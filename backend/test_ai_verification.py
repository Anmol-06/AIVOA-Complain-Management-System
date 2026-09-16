"""
Verification Test Suite for Unit 5: Groq + LangGraph AI Complaint Intake.

Tests:
1. Test 1: Valid complaint extraction (real Groq if configured, or mocked LLM verification).
2. Test 2: Incomplete complaint / null safety (verifies missing fields are null, no hallucinations).
3. Test 3: Invalid / empty request handling (HTTP 422).
4. Test 4: Missing GROQ_API_KEY handling (clear HTTP 503 configuration error, no crash).
5. Database Safety: Confirms row count in PostgreSQL 'complaints' table remains unchanged (0 rows).
"""

import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load server environment
load_dotenv("backend/.env")

from backend.app.main import app
from backend.app.schemas.ai import AIComplaintExtraction, AIRiskAssessment
from backend.app.ai.groq_client import is_groq_configured, get_groq_config, GroqConfigurationError
from backend.app.ai.complaint_graph import complaint_intake_graph
from backend.app.db.database import SessionLocal, check_db_connection
from backend.app.db.models import Complaint

client = TestClient(app)


class TestUnit5AIComplaintIntake(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_health_endpoint_reports_ai_service(self):
        """Verify GET /api/health includes safe AI service metadata."""
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ai_service", data)
        self.assertEqual(data["ai_service"]["provider"], "Groq")
        self.assertEqual(data["ai_service"]["orchestrator"], "LangGraph")
        self.assertIn(data["ai_service"]["status"], ["configured", "not_configured"])
        print("\n[PASSED] Health endpoint reports AI service metadata safely.")

    def test_02_empty_or_whitespace_request_returns_422(self):
        """Test 3: Verify empty or whitespace-only narrative is rejected with HTTP 422."""
        # Empty string
        res1 = client.post("/api/ai/complaint-intake", json={"text": ""})
        self.assertEqual(res1.status_code, 422)

        # Whitespace only
        res2 = client.post("/api/ai/complaint-intake", json={"text": "   \n\t  "})
        self.assertEqual(res2.status_code, 422)

        # Missing 'text' key
        res3 = client.post("/api/ai/complaint-intake", json={})
        self.assertEqual(res3.status_code, 422)
        print("[PASSED] Test 3: Invalid and empty requests correctly rejected with HTTP 422.")

    def test_03_missing_groq_api_key_returns_503(self):
        """Test 4: Verify application returns clean HTTP 503 when GROQ_API_KEY is absent."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "GROQ_MODEL": ""}):
            # Clear cached or active config
            res = client.post(
                "/api/ai/complaint-intake",
                json={"text": "ABC Pharma reported broken Paracetamol 500mg tablets."}
            )
            self.assertEqual(res.status_code, 503)
            data = res.json()
            self.assertIn("detail", data)
            self.assertTrue("not configured" in data["detail"].lower() or "groq" in data["detail"].lower())
        print("[PASSED] Test 4: Missing GROQ_API_KEY returns clean HTTP 503 without crashing.")

    def test_04_langgraph_nodes_and_null_safety_workflow(self):
        """
        Verify LangGraph workflow nodes:
        extract_fields -> validate_normalize -> risk_assessment -> build_result.
        Tests both full extraction and null safety.
        """
        mock_extraction = AIComplaintExtraction(
            complaint_source="Customer Portal",
            customer_name="ABC Pharma",
            product_name="Paracetamol",
            product_strength_grade="500 mg",
            batch_lot_number="B1234",
            manufacturing_date=None,
            expiry_date=None,
            quantity_affected=25,
            complaint_type="Packaging Defect",
            complaint_date=None,
            detailed_description="Broken tablets reported upon opening pack."
        )

        mock_risk = AIRiskAssessment(
            initial_severity="Medium",
            priority="High",
            risk_reasoning="25 tablets affected with physical damage. No patient harm reported.",
            recommended_next_actions=[
                "Quarantine affected batch B1234 inventory.",
                "Request sample return from ABC Pharma for visual inspection."
            ]
        )

        mock_llm = MagicMock()
        # First call is extract_fields, second call is risk_assessment
        mock_llm.with_structured_output.side_effect = [
            MagicMock(invoke=MagicMock(return_value=mock_extraction)),
            MagicMock(invoke=MagicMock(return_value=mock_risk)),
        ]

        with patch("backend.app.ai.complaint_graph.get_chat_groq", return_value=mock_llm):
            result = complaint_intake_graph.invoke({
                "input_text": "ABC Pharma reported that Paracetamol 500 mg batch B1234 had broken tablets. 25 tablets were affected."
            })

            self.assertIn("complaint", result)
            self.assertIn("risk_assessment", result)
            complaint = result["complaint"]
            risk = result["risk_assessment"]

            # Verify fields
            self.assertEqual(complaint.customer_name, "ABC Pharma")
            self.assertEqual(complaint.product_name, "Paracetamol")
            self.assertEqual(complaint.batch_lot_number, "B1234")
            self.assertEqual(complaint.quantity_affected, 25)
            self.assertIsNone(complaint.manufacturing_date)
            self.assertIsNone(complaint.expiry_date)

            # Verify risk assessment
            self.assertEqual(risk.initial_severity, "Medium")
            self.assertEqual(risk.priority, "High")
            self.assertGreater(len(risk.recommended_next_actions), 0)

        print("[PASSED] LangGraph 4-node pipeline and schema transformations verified.")

    def test_05_incomplete_complaint_preserves_nulls(self):
        """Test 2: Verify that missing information produces clean nulls and no hallucinations."""
        mock_partial_extraction = AIComplaintExtraction(
            complaint_source=None,
            customer_name=None,
            product_name=None,
            product_strength_grade=None,
            batch_lot_number=None,
            manufacturing_date=None,
            expiry_date=None,
            quantity_affected=None,
            complaint_type="Physical Defect",
            complaint_date=None,
            detailed_description="Customer reported broken tablets."
        )

        mock_partial_risk = AIRiskAssessment(
            initial_severity="Medium",
            priority="Medium",
            risk_reasoning="Broken tablets reported, but product name, batch number, and quantity are missing.",
            recommended_next_actions=[
                "Contact complainant to obtain product name, lot number, and photos."
            ]
        )

        mock_llm = MagicMock()
        mock_llm.with_structured_output.side_effect = [
            MagicMock(invoke=MagicMock(return_value=mock_partial_extraction)),
            MagicMock(invoke=MagicMock(return_value=mock_partial_risk)),
        ]

        with patch("backend.app.ai.complaint_graph.get_chat_groq", return_value=mock_llm):
            result = complaint_intake_graph.invoke({
                "input_text": "Customer reported broken tablets."
            })

            complaint = result["complaint"]
            self.assertIsNone(complaint.customer_name)
            self.assertIsNone(complaint.product_name)
            self.assertIsNone(complaint.batch_lot_number)
            self.assertIsNone(complaint.quantity_affected)
            self.assertIsNone(complaint.manufacturing_date)
            self.assertEqual(complaint.detailed_description, "Customer reported broken tablets.")

        print("[PASSED] Test 2: Incomplete complaints preserve nulls without hallucinating missing fields.")

    def test_06_database_safety_no_records_written(self):
        """
        Governance Invariant:
        Verify that executing AI complaint intake NEVER writes records to PostgreSQL.
        """
        initial_count = self.db.query(Complaint).count()

        # Run AI intake call
        res = client.post("/api/ai/complaint-intake", json={"text": "ABC Pharma reported broken tablets."})

        final_count = self.db.query(Complaint).count()
        self.assertEqual(
            final_count,
            initial_count,
            f"AI intake must NEVER write to PostgreSQL. Initial count: {initial_count}, final count: {final_count}"
        )
        print(f"[PASSED] Database Safety: Confirmed row count in PostgreSQL 'complaints' table remained exactly {final_count} (delta = 0).")


    def test_07_live_groq_if_configured(self):
        """
        If GROQ_API_KEY and GROQ_MODEL are configured in backend/.env,
        executes a live end-to-end integration test against the Groq LPU API.
        """
        if not is_groq_configured():
            print("\n[INFO] Live Groq integration skipped (GROQ_API_KEY not configured in backend/.env).")
            return

        api_key, model_name = get_groq_config()
        print(f"\n[LIVE TEST] Testing live with Groq model: {model_name}...")

        # Test 1 Live: Valid full complaint
        res = client.post(
            "/api/ai/complaint-intake",
            json={
                "text": "ABC Pharma reported that Paracetamol 500 mg batch B1234 had broken tablets. 25 tablets were affected."
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        complaint = data["complaint"]
        risk = data["risk_assessment"]

        # Validate extraction
        self.assertIsNotNone(complaint.get("product_name"))
        self.assertIn("paracetamol", complaint["product_name"].lower())
        self.assertEqual(complaint.get("quantity_affected"), 25)
        self.assertEqual(complaint.get("batch_lot_number"), "B1234")

        # Validate risk assessment
        self.assertIn(risk.get("initial_severity"), ["Low", "Medium", "High", "Critical"])
        self.assertIn(risk.get("priority"), ["Low", "Medium", "High", "Urgent"])
        self.assertTrue(len(risk.get("recommended_next_actions", [])) > 0)

        # Test 2 Live: Incomplete complaint
        res_incomplete = client.post(
            "/api/ai/complaint-intake",
            json={"text": "Customer reported broken tablets."}
        )
        self.assertEqual(res_incomplete.status_code, 200)
        inc_data = res_incomplete.json()["complaint"]
        self.assertIsNone(inc_data.get("customer_name"))
        self.assertIsNone(inc_data.get("batch_lot_number"))
        self.assertIsNone(inc_data.get("quantity_affected"))

        print(f"[PASSED] Live Groq test with model '{model_name}' succeeded for both Test 1 & Test 2!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
