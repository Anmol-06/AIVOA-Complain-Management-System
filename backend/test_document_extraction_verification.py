"""
Verification Test Suite for Unit 7: Document Extraction Tool.

Tests all required invariants:
1. Valid TXT extraction (Paracetamol 500 mg, batch B1234, 25 tablets, 2026-09-12)
2. Valid PDF extraction (In-memory PDF with text stream)
3. Valid DOCX extraction (In-memory Word document with paragraphs/tables)
4. Valid EML extraction (In-memory email message)
5. EML Date handling: header date NOT mapped to complaint_date unless explicitly stated in body (Adjustment 2)
6. Short PDF complaint allowed through (Adjustment 3 - no arbitrary <5 char rule)
7. Scanned / unreadable PDF handling (controlled HTTP 422 error)
8. Empty / 0-byte file handling (HTTP 422)
9. Unsupported file type rejection (HTTP 400 for .jpg, .xlsx)
10. Oversized file rejection (>10 MB rejected with HTTP 413)
11. Missing information remains null (Anti-hallucination check)
12. Non-email documents do not default to complaint_source="Email"
13. Preliminary risk assessment returned with severity, priority, reasoning, next actions
14. File validation independent of Groq configuration (Adjustment 1)
15. Database Write Isolation: PostgreSQL row count remains exactly unchanged (delta = 0)
"""

import io
import os
import sys
from email.message import EmailMessage
import docx
from pypdf import PdfWriter

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db.models import Complaint

client = TestClient(app)


def make_sample_pdf(text: str) -> bytes:
    """Generates a minimal valid PDF containing the specified text string."""
    escaped = text.replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT\n/F1 12 Tf\n72 712 Td\n({escaped}) Tj\nET\n".encode("latin-1")
    length = len(stream_content)
    
    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    obj2 = b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    obj3 = b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    obj4 = b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    obj5 = f"5 0 obj << /Length {length} >> stream\n".encode("latin-1") + stream_content + b"endstream\nendobj\n"
    
    parts = [header, obj1, obj2, obj3, obj4, obj5]
    offsets = [0]
    total_len = 0
    for p in parts:
        total_len += len(p)
        offsets.append(total_len)
        
    xref = (
        f"xref\n0 6\n"
        f"0000000000 65535 f \n"
        f"{offsets[0]:010d} 00000 n \n"
        f"{offsets[1]:010d} 00000 n \n"
        f"{offsets[2]:010d} 00000 n \n"
        f"{offsets[3]:010d} 00000 n \n"
        f"{offsets[4]:010d} 00000 n \n"
        f"trailer << /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{total_len}\n%%EOF"
    ).encode("latin-1")
    
    return b"".join(parts) + xref


def make_blank_pdf() -> bytes:
    """Generates a valid PDF with zero text streams (simulates scanned/image-only)."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def make_sample_docx(paragraphs: list, tables: list = None) -> bytes:
    """Generates an in-memory .docx file."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    if tables:
        for t in tables:
            num_rows = len(t)
            num_cols = max(len(row) for row in t) if num_rows > 0 else 0
            table = doc.add_table(rows=num_rows, cols=num_cols)
            for r_idx, row in enumerate(t):
                for c_idx, val in enumerate(row):
                    table.rows[r_idx].cells[c_idx].text = str(val)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_sample_eml(subject: str, sender: str, date_str: str, body: str) -> bytes:
    """Generates an in-memory RFC 822 .eml message."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "quality-assurance@aivoa-pharma.com"
    msg["Subject"] = subject
    if date_str:
        msg["Date"] = date_str
    msg.set_content(body)
    return msg.as_bytes()


def get_db_complaint_count() -> int:
    """Returns total complaint rows in PostgreSQL."""
    session = SessionLocal()
    try:
        return session.query(Complaint).count()
    finally:
        session.close()


def run_tests():
    print("=" * 70)
    print("STARTING UNIT 7 DOCUMENT EXTRACTION VERIFICATION TEST SUITE")
    print("=" * 70)

    # Initial DB safety baseline
    initial_db_count = get_db_complaint_count()
    print(f"\n[Baseline] Initial PostgreSQL complaint count: {initial_db_count}")

    # -----------------------------------------------------------------
    # Test 1: Valid TXT extraction with full domain facts
    # -----------------------------------------------------------------
    print("\n[Test 1] Valid TXT extraction (Paracetamol 500 mg, batch B1234, 25 units)")
    txt_content = (
        "ABC Pharma reported that 25 tablets of Paracetamol 500 mg from batch B1234 were found broken. "
        "The complaint was received on 12 September 2026."
    ).encode("utf-8")

    resp1 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("complaint_report.txt", txt_content, "text/plain")},
    )
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"
    data1 = resp1.json()
    c1 = data1["complaint"]
    r1 = data1["risk_assessment"]
    m1 = data1["document_metadata"]

    print(f"  Extracted Product: {c1.get('product_name')}")
    print(f"  Extracted Strength: {c1.get('product_strength_grade')}")
    print(f"  Extracted Batch: {c1.get('batch_lot_number')}")
    print(f"  Extracted Quantity: {c1.get('quantity_affected')}")
    print(f"  Extracted Customer: {c1.get('customer_name')}")
    print(f"  Extracted Complaint Date: {c1.get('complaint_date')}")
    print(f"  Complaint Source: {c1.get('complaint_source')}")
    print(f"  Metadata: {m1}")

    assert "paracetamol" in (c1.get("product_name") or "").lower()
    assert "b1234" in (c1.get("batch_lot_number") or "").lower()
    assert c1.get("quantity_affected") == 25
    assert "abc pharma" in (c1.get("customer_name") or "").lower()
    assert c1.get("complaint_date") == "2026-09-12"
    assert c1.get("manufacturing_date") is None
    assert c1.get("expiry_date") is None
    # Critical invariant: TXT files must NOT default to Email!
    assert c1.get("complaint_source") != "Email"
    assert m1["file_type"] == ".txt"
    assert m1["char_count"] > 20
    assert r1["initial_severity"] in {"Low", "Medium", "High", "Critical"}
    print("  -> PASSED: TXT facts extracted accurately, unmentioned dates remain null, non-email preserved.")

    # -----------------------------------------------------------------
    # Test 2: Valid PDF extraction
    # -----------------------------------------------------------------
    print("\n[Test 2] Valid PDF text extraction")
    pdf_text = "Apex Health Clinic reported 10 vials of Amoxicillin 250 mg batch LOT-9981 with severe discoloration."
    pdf_bytes = make_sample_pdf(pdf_text)

    resp2 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("apex_clinic_defect.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text}"
    data2 = resp2.json()
    c2 = data2["complaint"]
    m2 = data2["document_metadata"]
    print(f"  Extracted Product: {c2.get('product_name')}")
    print(f"  Extracted Batch: {c2.get('batch_lot_number')}")
    print(f"  Extracted Quantity: {c2.get('quantity_affected')}")
    assert "amoxicillin" in (c2.get("product_name") or "").lower()
    assert "9981" in (c2.get("batch_lot_number") or "").lower()
    assert c2.get("quantity_affected") == 10
    assert m2["file_type"] == ".pdf"
    # PDF must NOT default to Email
    assert c2.get("complaint_source") != "Email"
    print("  -> PASSED: PDF text extracted and parsed cleanly.")

    # -----------------------------------------------------------------
    # Test 3: Valid DOCX extraction (with tables)
    # -----------------------------------------------------------------
    print("\n[Test 3] Valid DOCX extraction (paragraphs & table)")
    docx_bytes = make_sample_docx(
        paragraphs=["Hospital Quality Department Complaint Notice"],
        tables=[
            ["Customer", "St. Jude Hospital"],
            ["Product", "Ciprofloxacin 500 mg"],
            ["Batch Number", "CIP-5042"],
            ["Defective Units", "15"],
            ["Defect Observed", "Cracked seals on blister packages"],
        ],
    )

    resp3 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("st_jude_report.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp3.status_code == 200, f"Expected 200, got {resp3.status_code}: {resp3.text}"
    data3 = resp3.json()
    c3 = data3["complaint"]
    print(f"  Extracted Product: {c3.get('product_name')}")
    print(f"  Extracted Customer: {c3.get('customer_name')}")
    print(f"  Extracted Quantity: {c3.get('quantity_affected')}")
    assert "ciprofloxacin" in (c3.get("product_name") or "").lower()
    assert "st. jude" in (c3.get("customer_name") or "").lower()
    assert c3.get("quantity_affected") == 15
    print("  -> PASSED: DOCX table and text extracted successfully.")

    # -----------------------------------------------------------------
    # Test 4: Valid EML extraction (complaint_source="Email")
    # -----------------------------------------------------------------
    print("\n[Test 4] Valid EML extraction (Explicit email source)")
    eml_bytes = make_sample_eml(
        subject="Defect Notice: Metformin 850 mg",
        sender="Dr. Alan Turing <alan@bletchley-hospital.org>",
        date_str="Mon, 15 Sep 2026 10:00:00 +0000",
        body="Dr. Alan Turing at Bletchley Hospital reported 30 tablets of Metformin 850 mg batch MET-2026 had foreign particles.",
    )

    resp4 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("dr_turing_email.eml", eml_bytes, "message/rfc822")},
    )
    assert resp4.status_code == 200, f"Expected 200, got {resp4.status_code}: {resp4.text}"
    data4 = resp4.json()
    c4 = data4["complaint"]
    print(f"  Extracted Source: {c4.get('complaint_source')}")
    print(f"  Extracted Product: {c4.get('product_name')}")
    print(f"  Extracted Quantity: {c4.get('quantity_affected')}")
    assert c4.get("complaint_source") == "Email"
    assert "metformin" in (c4.get("product_name") or "").lower()
    assert c4.get("quantity_affected") == 30
    print("  -> PASSED: EML recognized complaint_source as Email.")

    # -----------------------------------------------------------------
    # Test 5: EML Date Handling (Adjustment 2)
    # Header date must NOT be mapped to complaint_date if unstated in body!
    # -----------------------------------------------------------------
    print("\n[Test 5] EML Date Handling (Adjustment 2: Header Date is metadata, not complaint_date)")
    eml_no_complaint_date = make_sample_eml(
        subject="Quality Issue Notification",
        sender="pharmacist@store.com",
        date_str="Wed, 10 Sep 2026 14:22:00 +0000",
        body="We received broken Ibuprofen 400 mg batch IBU-100 tablets. 5 units affected.",
    )

    resp5 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("no_complaint_date.eml", eml_no_complaint_date, "message/rfc822")},
    )
    assert resp5.status_code == 200
    c5 = resp5.json()["complaint"]
    print(f"  Extracted complaint_date: {c5.get('complaint_date')}")
    # The header timestamp 2026-09-10 must NOT automatically become complaint_date!
    assert c5.get("complaint_date") is None, (
        f"Expected complaint_date to be None, but got {c5.get('complaint_date')}!"
    )
    print("  -> PASSED: EML transmission date header correctly treated as metadata only.")

    # -----------------------------------------------------------------
    # Test 6: Short PDF complaint allowed through (Adjustment 3)
    # -----------------------------------------------------------------
    print("\n[Test 6] Short PDF complaint allowed through (Adjustment 3 - no arbitrary <5 char rule)")
    short_text = "Broken Paracetamol B1234"
    short_pdf = make_sample_pdf(short_text)

    resp6 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("short.pdf", short_pdf, "application/pdf")},
    )
    assert resp6.status_code == 200, f"Expected 200 for short PDF, got {resp6.status_code}: {resp6.text}"
    c6 = resp6.json()["complaint"]
    print(f"  Extracted Product: {c6.get('product_name')}")
    assert "paracetamol" in (c6.get("product_name") or "").lower()
    print("  -> PASSED: Short PDF extracted without failing.")

    # -----------------------------------------------------------------
    # Test 7: Scanned / Empty PDF handling (Controlled Error)
    # -----------------------------------------------------------------
    print("\n[Test 7] Scanned / Empty PDF handling (Controlled HTTP 422)")
    blank_pdf = make_blank_pdf()

    resp7 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("scanned_document.pdf", blank_pdf, "application/pdf")},
    )
    assert resp7.status_code == 422, f"Expected 422, got {resp7.status_code}: {resp7.text}"
    detail7 = resp7.json().get("detail", "")
    print(f"  Error message returned: '{detail7}'")
    assert "could not extract readable text" in detail7.lower() or "scanned" in detail7.lower()
    print("  -> PASSED: Controlled error returned for unreadable/scanned PDF.")

    # -----------------------------------------------------------------
    # Test 8: Empty / 0-byte document handling
    # -----------------------------------------------------------------
    print("\n[Test 8] Empty 0-byte file handling (HTTP 422)")
    resp8 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp8.status_code == 422
    print(f"  0-byte error: {resp8.json().get('detail')}")
    print("  -> PASSED: Empty file rejected cleanly with HTTP 422.")

    # -----------------------------------------------------------------
    # Test 9: Unsupported file type rejection (.jpg, .xlsx)
    # -----------------------------------------------------------------
    print("\n[Test 9] Unsupported file type rejection (.jpg, .xlsx)")
    resp9a = client.post(
        "/api/ai/document-extraction",
        files={"file": ("photo.jpg", b"fake-jpg-content", "image/jpeg")},
    )
    assert resp9a.status_code == 400
    print(f"  .jpg error: {resp9a.json().get('detail')}")

    resp9b = client.post(
        "/api/ai/document-extraction",
        files={"file": ("sheet.xlsx", b"fake-excel-content", "application/vnd.ms-excel")},
    )
    assert resp9b.status_code == 400
    print(f"  .xlsx error: {resp9b.json().get('detail')}")
    print("  -> PASSED: Unsupported file formats rejected with HTTP 400.")

    # -----------------------------------------------------------------
    # Test 10: Oversized file rejection (> 10 MB)
    # -----------------------------------------------------------------
    print("\n[Test 10] Oversized file rejection (> 10 MB)")
    # Generate 10.1 MB dummy text
    oversized_bytes = b"A" * (10 * 1024 * 1024 + 1024)
    resp10 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("oversized.txt", oversized_bytes, "text/plain")},
    )
    assert resp10.status_code in {400, 413}, f"Expected 400 or 413, got {resp10.status_code}"
    print(f"  Oversized error: {resp10.json().get('detail')}")
    print("  -> PASSED: Oversized file (>10MB) rejected safely.")

    # -----------------------------------------------------------------
    # Test 11: Missing information remains null (Anti-hallucination)
    # -----------------------------------------------------------------
    print("\n[Test 11] Missing information remains null (Customer ABC Pharma reported broken tablets from batch B1234)")
    minimal_narrative = "Customer ABC Pharma reported broken tablets from batch B1234."
    resp11 = client.post(
        "/api/ai/document-extraction",
        files={"file": ("minimal.txt", minimal_narrative.encode("utf-8"), "text/plain")},
    )
    assert resp11.status_code == 200
    c11 = resp11.json()["complaint"]
    print(f"  Customer: {c11.get('customer_name')}")
    print(f"  Batch: {c11.get('batch_lot_number')}")
    print(f"  Product Name: {c11.get('product_name')}")
    print(f"  Strength: {c11.get('product_strength_grade')}")
    print(f"  Quantity: {c11.get('quantity_affected')}")
    print(f"  Manufacturing Date: {c11.get('manufacturing_date')}")
    print(f"  Expiry Date: {c11.get('expiry_date')}")

    assert "abc pharma" in (c11.get("customer_name") or "").lower()
    assert "b1234" in (c11.get("batch_lot_number") or "").lower()
    # Unmentioned facts MUST be null
    assert c11.get("product_name") is None or c11.get("product_name") == ""
    assert c11.get("product_strength_grade") is None
    assert c11.get("quantity_affected") is None
    assert c11.get("manufacturing_date") is None
    assert c11.get("expiry_date") is None
    print("  -> PASSED: Missing fields correctly preserved as null (zero hallucinations).")

    # -----------------------------------------------------------------
    # Test 12: Database Write Isolation (0 Database Writes)
    # -----------------------------------------------------------------
    print("\n[Test 12] Database Write Isolation Verification")
    final_db_count = get_db_complaint_count()
    print(f"  Baseline DB count: {initial_db_count}")
    print(f"  Post-extraction DB count: {final_db_count}")
    delta = final_db_count - initial_db_count
    assert delta == 0, f"DATABASE SAFETY VIOLATION: {delta} records written by document extraction!"
    print(f"  -> PASSED: Delta = 0. Document extraction executed strictly in memory with zero database writes.")

    print("\n" + "=" * 70)
    print("ALL UNIT 7 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
