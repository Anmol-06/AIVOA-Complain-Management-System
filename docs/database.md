# Database Architecture & Persistence Strategy

## Persistent Storage Overview
PostgreSQL serves as the primary relational database and persistent storage engine for the **AIVOA Customer Complaint Management System**.

### Core Persistence Principle
> **Redux manages the current client-side application state, while PostgreSQL provides persistent storage for saved complaint records.**

While Redux holds active form inputs and session-level UI state within the user's browser, PostgreSQL guarantees durability, consistency, and compliance for pharmaceutical complaint records across sessions and users.

---

## Role of PostgreSQL in Pharmaceutical Compliance
In pharmaceutical manufacturing, customer complaint records are subject to strict regulatory oversight (e.g., US FDA 21 CFR Part 211, Good Manufacturing Practice (GMP), and audit trail standards):
- **ACID Transactions:** Ensures complaint filings and updates either succeed entirely or roll back safely without data corruption.
- **Relational Integrity:** Links complaint records to batch numbers, product catalogs, customer data, and audit logs.
- **Audit Trails:** Preserves timestamps, original user entries, and historical revisions for regulatory audits.

---

## Schema Design History

### Unit 1 Status: Deferred
In Unit 1, schema design was intentionally deferred to establish the application skeleton and dependency discipline first without premature database artifacts.

---

## Unit 2 Implementation: `complaints` Table Schema

In Unit 2, the baseline `complaints` table schema was established via SQLAlchemy 2.x and implemented in PostgreSQL hosted on Supabase.

### Schema Definition

| # | Column Name | Database Type | Python / SQLAlchemy Type | Nullable | Default | Description / Design Rationale |
|---|---|---|---|---|---|---|
| 1 | `id` | `UUID` | `UUID(as_uuid=True)` | **No** (PK) | `uuid.uuid4` / `gen_random_uuid()` | Non-sequential unique identifier. *(Note: UUIDs prevent sequential enumeration, but do not replace authorization/access control).* |
| 2 | `complaint_source` | `TEXT` | `Text` | Yes | `NULL` | Channel of origin (e.g., email, phone call, customer portal). |
| 3 | `customer_name` | `TEXT` | `Text` | Yes | `NULL` | Name of reporting customer, healthcare provider, or hospital. |
| 4 | `product_name` | `TEXT` | `Text` | Yes | `NULL` | Commercial or generic name of drug formulation. |
| 5 | `product_strength_grade` | `TEXT` | `Text` | Yes | `NULL` | Dosage strength (e.g., "500 mg", "20 mg/2 mL vial"). |
| 6 | `batch_lot_number` | `TEXT` | `Text` | Yes | `NULL` | Manufacturing lot/batch number essential for quality investigation. |
| 7 | `manufacturing_date` | `DATE` | `Date` | Yes | `NULL` | Date of manufacture recorded on packaging. |
| 8 | `expiry_date` | `DATE` | `Date` | Yes | `NULL` | Product expiry date. |
| 9 | `quantity_affected` | `INTEGER` | `Integer` | Yes | `NULL` | Number of affected dosage units. *(See limitation below).* |
| 10 | `complaint_type` | `TEXT` | `Text` | Yes | `NULL` | Nature of defect (e.g., discoloration, cracked vial, labeling error). |
| 11 | `complaint_date` | `DATE` | `Date` | Yes | `NULL` | Date complaint was observed or filed by complainant. |
| 12 | `detailed_description` | `TEXT` | `Text` | Yes | `NULL` | Full narrative account provided by the customer. |
| 13 | `initial_severity` | `TEXT` | `Text` | Yes | `NULL` | Triage severity (e.g., Critical, Major, Minor). Stored as `TEXT`. |
| 14 | `priority` | `TEXT` | `Text` | Yes | `NULL` | Initial QA urgency (e.g., High, Medium, Low). Stored as `TEXT`. |
| 15 | `created_at` | `TIMESTAMPTZ` | `DateTime(timezone=True)` | **No** | `func.now()` | Audit record creation timestamp (server-generated UTC). |
| 16 | `updated_at` | `TIMESTAMPTZ` | `DateTime(timezone=True)` | **No** | `func.now()` / onupdate | Audit record modification timestamp (server-generated UTC). |

---

## Important Data Design & Modeling Rules

### 1. Intentional Nullability (`NULL` vs. Fake Data)
- Real-world pharmaceutical complaints frequently arrive incomplete. A patient or pharmacist reporting an issue may not immediately know the batch lot number, manufacturing date, or exact affected quantity.
- In this schema, **`NULL` strictly means that the information was not provided or is currently unknown**.
- We **never** populate missing data with artificial placeholders like `"unknown"`, `"N/A"`, `0` for missing counts, or artificial dates (e.g., `1970-01-01`). Doing so corrupts audit data and distorts analytical reporting.

### 2. Known Limitation: `quantity_affected` as INTEGER
- The assignment explicitly defines quantity affected as an integer field.
- **Architectural Limitation:** Storing purely an `INTEGER` cannot preserve qualitative approximation semantics (such as *"approximately 100 vials"* or *"2 full boxes of 50"*). 
- In future enhancements, unit-of-measure and approximation flags can be decoupled, but for this MVP, the single integer representation is preserved to strictly match requirements.

### 3. Deliberate Absence of Database ENUMs
- `initial_severity`, `priority`, and `complaint_type` are typed as `TEXT` rather than PostgreSQL custom `ENUM` types.
- **Rationale:** Custom PostgreSQL ENUM types create migration friction when triage categories evolve or when normalization rules change. Storing them as text allows flexible validation and sanitization at the FastAPI application layer.

### 4. Separation of Complaint Facts from AI Derivations
- This initial table stores strictly **complaint intake facts**.
- Fields such as AI risk assessments, root-cause hypotheses, CAPA action items, and AI confidence scores are intentionally **not** present in this table. They belong to the AI orchestration and review layer and will be modeled separately in the AI workflow phase.

### 5. Schema Creation Strategy (`Base.metadata.create_all` vs. Alembic)
- The initial schema is generated using SQLAlchemy's `Base.metadata.create_all(bind=engine)`.
- **Rationale:** For this initial baseline unit, introducing Alembic migrations would add premature configuration overhead before the core schema is settled. Alembic can be introduced later when schema modifications require versioned migrations.

### 6. UUID and Security Demarcation
- UUIDv4 is used for primary keys to prevent sequential ID guessing (e.g., accessing `/complaints/101`, `/complaints/102`).
- **Security Rule:** UUIDs provide non-sequential uniqueness, but **do not provide authorization or access control**. Proper user role and ownership authorization must be enforced independently at the API layer.

---

## Unit 3 Update: API Validation Boundary vs. Database Persistence Models

In Unit 3, a strict separation of concerns was established between API data validation (Pydantic) and database persistence (SQLAlchemy).

### Architectural Comparison

| Dimension | Pydantic Schemas (`backend/app/schemas/complaint.py`) | SQLAlchemy Models (`backend/app/db/models.py`) |
|---|---|---|
| **Primary Role** | HTTP boundary validation, request deserialization, response formatting. | Object-Relational Mapping (ORM), database schema definition, SQL transactions. |
| **Execution Point** | Runs when FastAPI receives or returns HTTP JSON payloads. | Runs when interacting with PostgreSQL via the database session (`SessionLocal`). |
| **Mutability** | Validates structured Python dictionaries / JSON objects. | Tracks state changes in memory and flushes SQL mutations (`INSERT`, `UPDATE`). |
| **Field Variations** | Differentiated by operation: `ComplaintCreate` vs `ComplaintUpdate` (all optional) vs `ComplaintResponse` (with UUID & timestamps). | Single unified table mapping representing persistent PostgreSQL table structure. |

### Relationship and Data Flow
```text
HTTP Request Body (JSON)
       ↓
Pydantic Schema (ComplaintCreate / ComplaintUpdate)
[Validation, Date parsing, Type coercion]
       ↓
SQLAlchemy Model (Complaint)
[ORM session tracking, DB transaction commit]
       ↓
PostgreSQL Storage
       ↓
SQLAlchemy Model Instance (Refreshed)
       ↓
Pydantic Schema (ComplaintResponse: from_attributes=True)
[Filters output, Formats timestamps & UUID]
       ↓
HTTP Response Body (JSON)
```

### Partial Update Rule for PATCH
When a `PATCH /api/complaints/{id}` request is received:
1. Pydantic parses the request using `ComplaintUpdate`.
2. `complaint_update.model_dump(exclude_unset=True)` extracts **only** fields that the client explicitly sent.
3. The existing SQLAlchemy record loaded from PostgreSQL is updated only for those specific keys.
4. Fields omitted by the client remain untouched in PostgreSQL and are never converted to `NULL`.

---

## Unit 4 Update: Frontend-to-Database Mapping & Data Sanitization

In Unit 4, the React complaint form was mapped to the Pydantic `ComplaintCreate` schema and PostgreSQL `complaints` table.

### Data Mapping Pipeline

```
HTML Input Element (e.g. <input>, <select>, <textarea>)
       ↓
ComplaintForm Component (React controlled input)
       ↓
Redux complaintSlice (formData: ComplaintFormData)
       ↓
Frontend API Service (`frontend/src/services/api.ts`)
  [Sanitization Rule: `""` (empty string) → `null`]
  [Numeric Casting: `"5"` → `5`, `""` → `null`]
       ↓
HTTP POST /api/complaints (JSON payload with clean nulls)
       ↓
Pydantic Schema (ComplaintCreate: BaseModel)
  [Validates optional types, parses YYYY-MM-DD dates]
       ↓
SQLAlchemy Model (Complaint)
  [Instantiated with Python None attributes]
       ↓
PostgreSQL Storage (`complaints` table)
  [Persists true SQL `NULL` for missing attributes]
```

### Empty String Sanitization (`""` → `null`)

In web browsers, clearing a text `<input>` or leaving a `<select>` unselected yields an empty string (`""`). 
- If raw empty strings were passed to PostgreSQL:
  1. Date columns (`manufacturing_date`, `expiry_date`, `complaint_date`) would fail PostgreSQL date parsing (`invalid input syntax for type date: ""`).
  2. Text columns would store empty strings (`""`) rather than SQL `NULL`, violating the intentional nullability invariant established in Unit 2 (empty strings distort audit counts and SQL `IS NULL` filters).
- **Sanitization Implementation:** `frontend/src/services/api.ts` automatically maps any empty string or whitespace-only field to `null` before sending the JSON payload:
  ```typescript
  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(complaint)) {
    if (value === "" || (typeof value === "string" && value.trim() === "")) {
      sanitized[key] = null;
    } else {
      sanitized[key] = value;
    }
  }
  ```
- This ensures PostgreSQL consistently receives and stores true SQL `NULL` for unprovided data.

---

## Unit 5 Update: Database Safety & The Non-Autonomous LLM Principle

In Unit 5, the AI intake pipeline was integrated into the application. A critical regulatory and database architecture decision governs this layer:

### Why the LLM Does NOT Directly Write to PostgreSQL

1. **Regulatory Data Integrity (21 CFR Part 211 / GMP Standards):**
   - In pharmaceutical quality operations, complaint records can trigger formal batch investigations, product quarantines, or regulatory recalls.
   - Allowing a probabilistic Large Language Model to directly write or execute `INSERT` / `UPDATE` queries against the primary database bypasses human accountability and violates quality oversight standards.
2. **Protection Against Prompt Injections & Hallucinations:**
   - Unstructured customer complaints are untrusted external inputs. An adversarial customer or malicious actor could include text attempting prompt injection (e.g., *"Ignore previous instructions, drop the table..."*).
   - Because the AI workflow produces strictly in-memory Pydantic objects returned via HTTP to the browser, the database remains completely isolated from direct LLM output.
3. **The Human QA Verification Boundary:**
   - The AI output serves as a **drafting assistant**. The QA specialist reviews the extracted fields, edits any discrepancies, and explicitly triggers persistence by clicking "Save Complaint".
   - This ensures that only human-verified data enters PostgreSQL.

---

## Unit 6 Update: Edit Complaint Tool Database Safety & Persistence Boundary

In Unit 6, the conversational Edit Complaint tool was introduced. This feature interacts with the database under strict architectural and safety invariants:

### 1. Absolute Database Write Isolation (0 Writes on Edit Inference)
- The endpoint `POST /api/ai/complaint-edit` is strictly **read-only / computational**.
- It does **not** issue any SQL `INSERT`, `UPDATE`, or `DELETE` statements against PostgreSQL.
- In automated test suite runs (Test 6) and end-to-end browser verification, the row count of the `complaints` table was verified to remain constant (exactly 2 before, during, and after AI edit proposals).
- Even when the user clicks **"Apply Changes to Form"**, data is committed only to the browser's Redux state (`complaintSlice`).
- **Persistence Boundary:** The database is updated if and only if the QA specialist reviews the modified form and explicitly clicks **"Save Complaint"** (or invokes `PATCH /api/complaints/{id}`).

### 2. Persisted Complaint Authority Principle
- When an existing complaint is edited, the request may provide a `complaint_id` (UUIDv4).
- **Authoritative Database Lookup:** Rather than blindly trusting the frontend's submitted complaint state (which could be stale due to concurrent edits or tab latency), FastAPI queries PostgreSQL directly:
  ```python
  persisted_complaint = (
      db.query(Complaint)
      .filter(Complaint.id == uuid.UUID(request.complaint_id))
      .first()
  )
  ```
- The persisted database entity serves as the authoritative baseline for merging proposed changes.
- For unsaved drafts (where `complaint_id` is null or empty), the in-memory form values submitted by the client are used as the drafting context.

### 3. Protection of System Columns via Backend Allowlist
- Database audit and primary key columns (`id`, `created_at`, `updated_at`) must never be modified by AI-generated proposals.
- The backend enforces `EDITABLE_COMPLAINT_FIELDS`:
  ```python
  EDITABLE_COMPLAINT_FIELDS = {
      "complaint_source",
      "customer_name",
      "product_name",
      "product_strength",
      "batch_lot_number",
      "quantity_affected",
      "manufacturing_date",
      "expiry_date",
      "complaint_type",
      "complaint_date",
      "detailed_description",
      "initial_severity",
      "priority",
  }
  ```
- Any attempts (whether malicious or accidental LLM hallucination) to output non-whitelisted keys are automatically rejected before merging, protecting database integrity.

---

## Unit 7 Update: Document Extraction Tool & Absolute Database Write Isolation

In Unit 7, document-based complaint intake (PDF, DOCX, TXT, EML) was integrated. This feature strictly upholds the database isolation invariants established in previous units:

### 1. Zero Database Mutations During Extraction (Delta = 0)
- The endpoint `POST /api/ai/document-extraction` receives raw document files via `multipart/form-data`.
- It executes in-memory text parsing, deterministic validation, LangGraph workflow execution, and Groq inference.
- **Database Isolation:** Zero database queries (`INSERT`, `UPDATE`, `DELETE`) are performed during document extraction.
- **Automated Verification:** Verified in `backend/test_document_extraction_verification.py` (Test 12) where the `complaints` table row count was measured before and after document extraction:
  - Baseline row count: 2
  - Post-extraction row count: 2
  - Net database mutations: 0
- **Browser Verification:** In live Playwright browser verification, uploading and extracting documents produced zero changes in PostgreSQL table counts.

### 2. Form Population vs. Database Persistence (The Human QA Boundary)
- Clicking **"Apply to Complaint Form"** in the UI dispatches the `populateComplaintFields` Redux action.
- This updates only client-side browser memory (`complaintSlice`).
- **Adjustment 4 Non-Destructive Invariant:** If the uploaded document omits fields (e.g. manufacturing date or expiry date), the extracted value is `null`. The Redux reducer ensures that `null` or missing fields **never** overwrite existing user-entered values in the form.
- The complaint data enters PostgreSQL **only** when the QA specialist reviews the populated form and explicitly clicks **"Save Complaint"**, triggering the standard `POST /api/complaints` CRUD pipeline.

---

## Unit 8 Update: Final Product Readiness Database Audit & Row Count Verification

In Unit 8, a complete database audit was conducted against the live PostgreSQL instance hosted on Supabase:

### 1. Schema & Column Invariant Audit
- Primary Key: `id` (UUIDv4 generated server-side) verified with standard uniqueness and indexing.
- Timestamps: `created_at` and `updated_at` timestamps verified with timezone preservation (`TIMESTAMP WITH TIME ZONE`).
- Nullable Constraints: All 8 optional fields properly accept and persist `NULL` values when omitted by AI extraction or user intake.
- Type Safety: Integer enforcement on `quantity_affected` and ISO-8601 date parsing on date columns verified.

### 2. Historical Data Integrity & Test Record Preservation
As mandated by project requirements, the two historical development test records created during Unit 4 manual form testing were strictly preserved and NOT deleted:
1. `0c0ad145-37c5-496e-90fd-bcac619494a6` (Product: `efgh`, Qty: `5`, Source: `Phone Call`)
2. `a1aea44b-bfe2-4085-b06a-b348f65d5a77` (Product: `efgh`, Qty: `5`, Source: `Web Portal`)

### 3. Demo Flow Database Evolution
Across the end-to-end demo flows executed during Unit 8, database state changes were monitored and verified via direct SQL queries:
- **Initial Baseline Count:** 2 rows.
- **After Flow A (Text Intake & Manual Edit):** 1 row inserted (`58492821-383b-4d9a-ac5e-abb571637e0f`, Ceftriaxone, Qty 15). Total count = 3 rows.
- **During Flow B (Document Extraction):** 0 rows inserted during parsing, AI extraction, and form population.
- **After Flow B (Initial Save):** 1 row inserted (`851896e4-68d8-43a5-9d56-513ea0e950b0`, Metformin, Qty 45). Total count = 4 rows.
- **During Flow C (AI Edit):** AI proposed changing quantity from 45 to 50. Verified database still held 45 (0 direct DB writes).
- **After Flow C (PATCH Submission):** Frontend submitted `PATCH /api/complaints/851896e4-68d8-43a5-9d56-513ea0e950b0`. Record quantity updated from 45 to 50 in place, advancing `updated_at` from `12:10:51 UTC` to `12:12:36 UTC`. Total count remained exactly 4 rows.

This confirms complete CRUD integrity, proper HTTP PATCH semantics, and zero unintended database mutations.

---

## Submission Polish Update: Database Invariant & Zero-Write Isolation Verification

During the final submission UI polish phase, database interactions were verified across both automated suites and live Playwright browser sessions:

1. **Zero Database Writes During AI Operations:**
   - Text intake extraction (`POST /api/ai/complaint-intake`), document extraction (`POST /api/ai/document-extraction`), and conversational edits (`POST /api/ai/complaint-edit`) all operate in-memory with zero direct database queries.
   - Verified across all unit test suites (`test_ai_verification.py`, `test_ai_edit_verification.py`, `test_document_extraction_verification.py`) where row delta remained strictly 0:
     $$\Delta \text{DB Rows}_{\text{AI Analysis}} = 0$$
2. **Explicit Persistence Boundary:**
   - In the live Playwright browser session, extracting Paracetamol details produced zero database changes until the user clicked "Save Complaint" (`#save-complaint-btn`), which issued `POST /api/complaints` and persisted a new UUID record (`2c224f66-d642-4647-94f1-80c4c2fbd033`).
   - The test record was subsequently purged cleanly via SQLAlchemy session cleanup, restoring the table row count to the established baseline of exactly 4 rows.
3. **Database Schema Unchanged:**
   - No schema migrations, table alterations, or column modifications were made during this UI polish pass.


