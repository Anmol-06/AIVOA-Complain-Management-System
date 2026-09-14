import sys
from sqlalchemy import inspect, text
from app.db.database import engine, init_db, check_db_connection

def run_checks():
    print("=== Checking Database Configuration ===")
    conn_status = check_db_connection()
    print(f"Connection status: {conn_status['status']}")
    if conn_status['status'] != 'connected':
        print(f"Status detail: {conn_status.get('message', 'Not connected')}")
        return False

    print("\n=== Initializing Database Schema (Base.metadata.create_all) ===")
    init_db()

    print("\n=== Introspecting 'complaints' Table ===")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Found tables: {tables}")
    if "complaints" not in tables:
        print("ERROR: 'complaints' table was not found!")
        return False
    print("SUCCESS: 'complaints' table exists.")

    print("\n=== Verifying Columns and Types ===")
    columns = inspector.get_columns("complaints")
    col_dict = {col["name"]: col for col in columns}
    
    expected_columns = [
        ("id", False),
        ("complaint_source", True),
        ("customer_name", True),
        ("product_name", True),
        ("product_strength_grade", True),
        ("batch_lot_number", True),
        ("manufacturing_date", True),
        ("expiry_date", True),
        ("quantity_affected", True),
        ("complaint_type", True),
        ("complaint_date", True),
        ("detailed_description", True),
        ("initial_severity", True),
        ("priority", True),
        ("created_at", False),
        ("updated_at", False),
    ]

    print(f"Total columns detected: {len(columns)} (Expected: 16)")
    if len(columns) != 16:
        print(f"ERROR: Expected 16 columns, got {len(columns)}")
        return False

    for col_name, expected_nullable in expected_columns:
        if col_name not in col_dict:
            print(f"ERROR: Missing column '{col_name}'")
            return False
        col = col_dict[col_name]
        actual_nullable = col["nullable"]
        type_str = str(col["type"])
        print(f" - {col_name:25} | Type: {type_str:30} | Nullable: {actual_nullable}")
        if actual_nullable != expected_nullable:
            print(f"   ERROR: Nullability mismatch for {col_name}! Expected {expected_nullable}, got {actual_nullable}")
            return False

    print("\n=== Verifying Primary Key ===")
    pk = inspector.get_pk_constraint("complaints")
    print(f"Primary key: {pk}")
    if pk.get("constrained_columns") != ["id"]:
        print(f"ERROR: Expected primary key ['id'], got {pk.get('constrained_columns')}")
        return False
    print("SUCCESS: Primary key is 'id'.")

    print("\n=== Verifying Table Record Count (Ensuring no fake/dirty records) ===")
    with engine.connect() as conn:
        count_res = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar()
        print(f"Current row count in complaints table: {count_res}")

    print("\n=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
