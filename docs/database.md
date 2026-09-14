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



