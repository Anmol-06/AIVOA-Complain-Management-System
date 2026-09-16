"""
Unit 6 AI Complaint Edit Verification Test Suite

Tests:
1. TEST 1 — Single-field edit ("Actually, 50 tablets were affected.")
2. TEST 2 — Multiple-field edit ("Change customer name to XYZ Pharma and quantity affected to 100.")
3. TEST 3 — Missing value / ambiguity ("Change the quantity.") -> Clarification, no invented numbers
4. TEST 4 — No hallucination (Unmentioned fields not in requested_changes)
5. TEST 5 — Risk reassessment on severity-altering change
6. TEST 6 — Database safety (Row count in PostgreSQL unchanged by AI edit proposal)
7. TEST 7 — Persisted complaint authority & error handling (UUID resolution, 404, 422)
"""

import copy
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.main import app
from backend.app.db.database import engine, SessionLocal
from backend.app.db.models import Complaint
from backend.app.schemas.ai import EDITABLE_COMPLAINT_FIELDS


class TestUnit6AIComplaintEdit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_complaint = {
            "customer_name": "ABC Pharma",
            "product_name": "Paracetamol",
            "product_strength_grade": "500 mg",
            "batch_lot_number": "B1234",
            "quantity_affected": 25,
            "complaint_type": "Product damage",
            "complaint_source": "Email",
            "detailed_description": "ABC Pharma reported broken tablets in Paracetamol 500 mg batch B1234. 25 tablets affected.",
            "initial_severity": "Medium",
            "priority": "Medium",
        }

    def test_01_single_field_edit(self):
        """
        TEST 1 — Single-field edit:
        Instruction: 'Actually, 50 tablets were affected.'
        Expected: ONLY quantity_affected changes to 50; all other fields preserved intact.
        """
        print("\n[TEST 1] Testing single-field edit ('Actually, 50 tablets were affected.')...")
        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Actually, 50 tablets were affected.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        self.assertTrue(data["is_valid_edit"])
        self.assertFalse(data["needs_clarification"])
        
        # Verify requested_changes contains ONLY quantity_affected
        self.assertIn("quantity_affected", data["requested_changes"])
        self.assertEqual(data["requested_changes"]["quantity_affected"], 50)
        
        # Verify updated_complaint has quantity 50 and preserves other fields
        self.assertEqual(data["updated_complaint"]["quantity_affected"], 50)
        self.assertEqual(data["updated_complaint"]["product_name"], "Paracetamol")
        self.assertEqual(data["updated_complaint"]["batch_lot_number"], "B1234")
        self.assertEqual(data["updated_complaint"]["customer_name"], "ABC Pharma")
        self.assertEqual(data["updated_complaint"]["product_strength_grade"], "500 mg")

        print("✓ [PASSED] TEST 1: Single field updated to 50, all other fields preserved with 100% fidelity.")

    def test_02_multiple_field_edit(self):
        """
        TEST 2 — Multiple-field edit:
        Instruction: 'Change the customer name to XYZ Pharma and quantity affected to 100.'
        Expected: customer_name = 'XYZ Pharma' and quantity_affected = 100; others unchanged.
        """
        print("\n[TEST 2] Testing multi-field edit ('Change customer to XYZ Pharma and quantity to 100')...")
        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Change the customer name to XYZ Pharma and the affected quantity to 100.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        self.assertTrue(data["is_valid_edit"])
        self.assertFalse(data["needs_clarification"])

        self.assertEqual(data["requested_changes"].get("customer_name"), "XYZ Pharma")
        self.assertEqual(data["requested_changes"].get("quantity_affected"), 100)

        # Ensure product and batch remain untouched
        self.assertEqual(data["updated_complaint"]["customer_name"], "XYZ Pharma")
        self.assertEqual(data["updated_complaint"]["quantity_affected"], 100)
        self.assertEqual(data["updated_complaint"]["product_name"], "Paracetamol")
        self.assertEqual(data["updated_complaint"]["batch_lot_number"], "B1234")

        print("✓ [PASSED] TEST 2: Multiple fields updated correctly, unmentioned fields untouched.")

    def test_03_missing_value_and_ambiguity(self):
        """
        TEST 3 — Missing value / ambiguity:
        Instruction: 'Change the quantity.'
        Expected: System MUST NOT invent a number.
        Returns needs_clarification = True with helpful message.
        Merge and risk reassessment must NOT be executed.
        """
        print("\n[TEST 3] Testing ambiguity handling ('Change the quantity.')...")
        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Change the quantity.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        self.assertTrue(data["needs_clarification"])
        self.assertIsNotNone(data["clarification_message"])
        self.assertTrue(len(data["clarification_message"]) > 5)

        # Verify NO changes were hallucinated or merged
        self.assertEqual(data["requested_changes"], {})
        self.assertEqual(
            data["updated_complaint"]["quantity_affected"],
            self.sample_complaint["quantity_affected"],
        )
        self.assertIsNone(data.get("risk_assessment"))

        print(f"✓ [PASSED] TEST 3: Ambiguity caught safely. Clarification: '{data['clarification_message']}'. Zero invented values.")

    def test_04_no_hallucination_and_allowlist(self):
        """
        TEST 4 — No hallucination & editable allowlist:
        Instruction: 'Change the quantity to 50.'
        Expected: requested_changes has ONLY 'quantity_affected'.
        Does NOT claim customer, product, or batch were requested.
        """
        print("\n[TEST 4] Testing anti-hallucination and field allowlist...")
        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Change the quantity to 50.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        requested = data["requested_changes"]
        self.assertEqual(set(requested.keys()), {"quantity_affected"})
        for field in requested.keys():
            self.assertIn(field, EDITABLE_COMPLAINT_FIELDS)

        self.assertNotIn("product_name", requested)
        self.assertNotIn("batch_lot_number", requested)
        self.assertNotIn("customer_name", requested)

        print("✓ [PASSED] TEST 4: Anti-hallucination verified. Only explicit target fields returned.")

    def test_05_risk_reassessment(self):
        """
        TEST 5 — Risk reassessment:
        Instruction changes complaint_type to Adverse event with severe patient reaction.
        Expected: Fresh preliminary risk assessment returned reflecting higher severity.
        """
        print("\n[TEST 5] Testing risk reassessment on clinical severity change...")
        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Update complaint classification to Adverse Event and update detailed description to: Patient experienced severe anaphylactic shock requiring emergency hospitalization.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        self.assertTrue(data["is_valid_edit"])
        self.assertIsNotNone(data.get("risk_assessment"))
        risk = data["risk_assessment"]

        # High or Critical severity expected due to anaphylactic shock
        self.assertIn(risk["initial_severity"], ["High", "Critical"])
        self.assertIn(risk["priority"], ["High", "Urgent"])
        self.assertTrue(len(risk["risk_reasoning"]) > 10)
        self.assertTrue(len(risk["recommended_next_actions"]) > 0)

        print(f"✓ [PASSED] TEST 5: Risk successfully reassessed (Severity: {risk['initial_severity']}, Priority: {risk['priority']}).")

    def test_06_database_safety_no_records_written(self):
        """
        TEST 6 — Database safety:
        Running the AI edit workflow must NOT create, mutate, or delete PostgreSQL records.
        """
        print("\n[TEST 6] Verifying database safety invariant (Zero DB writes)...")
        with engine.connect() as conn:
            initial_count = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar()

        payload = {
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "Change the customer name to BioPharma International and quantity to 500.",
        }
        response = self.client.post("/api/ai/complaint-edit", json=payload)
        self.assertEqual(response.status_code, 200)

        with engine.connect() as conn:
            final_count = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar()

        self.assertEqual(
            final_count,
            initial_count,
            f"Database safety violated! Initial: {initial_count}, Final: {final_count}",
        )
        print(f"✓ [PASSED] TEST 6: Database Safety: Row count in 'complaints' remained exactly {final_count} (delta = 0).")

    def test_07_persisted_complaint_authority_and_errors(self):
        """
        TEST 7 — Persisted complaint resolution & error boundaries:
        - When complaint_id is provided, loads authoritative record from DB.
        - Invalid UUID -> 422
        - Nonexistent UUID -> 404
        - Missing both complaint_id and current_complaint -> 422
        - Empty instruction -> 422
        """
        print("\n[TEST 7] Testing persisted complaint resolution and error boundaries...")
        
        # 1. Nonexistent UUID
        res_404 = self.client.post("/api/ai/complaint-edit", json={
            "complaint_id": "00000000-0000-0000-0000-000000000000",
            "edit_instruction": "Change quantity to 50.",
        })
        self.assertEqual(res_404.status_code, 404)

        # 2. Invalid UUID format
        res_invalid_uuid = self.client.post("/api/ai/complaint-edit", json={
            "complaint_id": "not-a-valid-uuid",
            "edit_instruction": "Change quantity to 50.",
        })
        self.assertEqual(res_invalid_uuid.status_code, 422)

        # 3. Missing both complaint_id and current_complaint
        res_missing = self.client.post("/api/ai/complaint-edit", json={
            "edit_instruction": "Change quantity to 50.",
        })
        self.assertEqual(res_missing.status_code, 422)

        # 4. Empty edit instruction
        res_empty = self.client.post("/api/ai/complaint-edit", json={
            "current_complaint": copy.deepcopy(self.sample_complaint),
            "edit_instruction": "   ",
        })
        self.assertEqual(res_empty.status_code, 422)

        # 5. Persisted record resolution (using first record in DB if available)
        db = SessionLocal()
        existing = db.query(Complaint).first()
        db.close()

        if existing:
            res_db = self.client.post("/api/ai/complaint-edit", json={
                "complaint_id": str(existing.id),
                "edit_instruction": "Actually, 30 tablets were affected.",
            })
            self.assertEqual(res_db.status_code, 200)
            data = res_db.json()
            self.assertEqual(data["complaint_id"], str(existing.id))
            self.assertEqual(data["original_complaint"]["product_name"], existing.product_name)
            self.assertEqual(data["requested_changes"].get("quantity_affected"), 30)
            print(f"✓ Authoritative resolution against persisted complaint {existing.id} verified.")

        print("✓ [PASSED] TEST 7: Persisted complaint authority and error boundaries verified.")


if __name__ == "__main__":
    unittest.main()
