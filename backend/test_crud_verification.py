import json
import sys
import urllib.request
import urllib.error
from sqlalchemy import text

from app.db.database import engine

BASE_URL = "http://127.0.0.1:8000"


def http_req(path: str, method: str = "GET", data: dict = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else None
            return response.status, res_json
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = err_body
        return e.code, err_json


def run_crud_tests():
    print("=== Step 1: Health Check Verification ===")
    status, health_data = http_req("/api/health")
    print(f"GET /api/health status: {status}")
    assert status == 200, f"Expected 200, got {status}"
    print(f"Health response: {health_data}")
    assert health_data["database"]["status"] == "connected", "Database is not connected!"

    print("\n=== Step 2: POST /api/complaints (Create Realistic Test Complaint) ===")
    payload = {
        "complaint_source": "Email",
        "customer_name": "ABC Pharma",
        "product_name": "Paracetamol",
        "product_strength_grade": "500 mg",
        "batch_lot_number": "BATCH-2026-001",
        "manufacturing_date": "2026-01-15",
        "expiry_date": "2028-01-14",
        "quantity_affected": 5,
        "complaint_type": "Product damage",
        "complaint_date": "2026-09-14",
        "detailed_description": "Five boxes were received damaged during transportation.",
        "initial_severity": "Medium",
        "priority": "Medium",
    }
    status, created_data = http_req("/api/complaints", method="POST", data=payload)
    print(f"POST /api/complaints status: {status}")
    assert status == 201, f"Expected 201, got {status}: {created_data}"
    complaint_id = created_data["id"]
    print(f"Created complaint ID: {complaint_id}")
    assert created_data["customer_name"] == "ABC Pharma"
    assert created_data["quantity_affected"] == 5
    assert "created_at" in created_data
    assert "updated_at" in created_data

    try:
        print("\n=== Step 3: GET /api/complaints (List All Complaints) ===")
        status, complaints_list = http_req("/api/complaints")
        print(f"GET /api/complaints status: {status}")
        assert status == 200
        print(f"Retrieved {len(complaints_list)} complaints")
        found = any(c["id"] == complaint_id for c in complaints_list)
        assert found, f"Created complaint {complaint_id} not found in list!"

        print(f"\n=== Step 4: GET /api/complaints/{complaint_id} (Get by ID) ===")
        status, single_data = http_req(f"/api/complaints/{complaint_id}")
        print(f"GET /api/complaints/{complaint_id} status: {status}")
        assert status == 200
        assert single_data["id"] == complaint_id
        assert single_data["batch_lot_number"] == "BATCH-2026-001"

        print(f"\n=== Step 5: PATCH /api/complaints/{complaint_id} (Partial Update) ===")
        patch_payload = {"quantity_affected": 8}
        status, patched_data = http_req(f"/api/complaints/{complaint_id}", method="PATCH", data=patch_payload)
        print(f"PATCH status: {status}")
        assert status == 200
        print(f"Patched data: quantity_affected={patched_data['quantity_affected']}")
        # Verify quantity updated
        assert patched_data["quantity_affected"] == 8, f"Expected 8, got {patched_data['quantity_affected']}"
        # Verify other fields remain intact
        assert patched_data["customer_name"] == "ABC Pharma", "customer_name was modified!"
        assert patched_data["product_name"] == "Paracetamol", "product_name was modified!"
        assert patched_data["batch_lot_number"] == "BATCH-2026-001", "batch_lot_number was modified!"
        assert patched_data["detailed_description"] == "Five boxes were received damaged during transportation."
        assert patched_data["initial_severity"] == "Medium"
        assert patched_data["priority"] == "Medium"
        print("SUCCESS: Partial update updated only quantity_affected; all other fields preserved!")

        print("\n=== Step 6: Verify 404 for Nonexistent UUID ===")
        dummy_uuid = "00000000-0000-0000-0000-000000000000"
        status, res_404_get = http_req(f"/api/complaints/{dummy_uuid}")
        print(f"GET nonexistent UUID status: {status}")
        assert status == 404

        status, res_404_patch = http_req(f"/api/complaints/{dummy_uuid}", method="PATCH", data={"quantity_affected": 10})
        print(f"PATCH nonexistent UUID status: {status}")
        assert status == 404

        print("\n=== Step 7: Verify 422 for Invalid Pydantic Data ===")
        status, res_422 = http_req("/api/complaints", method="POST", data={"quantity_affected": "not-an-integer"})
        print(f"POST invalid data status: {status}")
        assert status == 422

        print("\n=== Step 8: Direct PostgreSQL Verification via SQLAlchemy ===")
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, product_name, quantity_affected FROM complaints WHERE id = :id"),
                {"id": complaint_id}
            ).fetchone()
            print(f"Direct DB query result: {row}")
            assert row is not None
            assert row[1] == "Paracetamol"
            assert row[2] == 8

    finally:
        print("\n=== Step 9: Database Cleanup (Removing Test Complaint) ===")
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM complaints WHERE id = :id"),
                {"id": complaint_id}
            )
            conn.commit()
            count = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar()
            print(f"Complaints table row count after cleanup: {count}")
            assert count == 0, f"Table not clean! Remaining rows: {count}"
        print("SUCCESS: Database cleaned up completely. 0 records remaining.")

    print("\n=== ALL UNIT 3 TESTS PASSED SUCCESSFULLY ===")
    return True


if __name__ == "__main__":
    success = run_crud_tests()
    sys.exit(0 if success else 1)
