# System Architecture

## Overview
The **AIVOA Customer Complaint Management System** is an AI-powered enterprise application designed for the pharmaceutical manufacturing industry. Its primary objective is to assist Quality Assurance (QA) personnel and compliance teams in capturing, standardizing, and reviewing customer complaints regarding drug products, packaging, and adverse events.

---

## High-Level Architecture Diagram

```
+-------------------------------------------------------------------------+
|                              Client Browser                             |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                       React + TypeScript                        |   |
|   |   (Presentation, User Input, Visual Verification, Inter Font)   |   |
|   +-------------------------------+---------------------------------+   |
|                                   |                                     |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |                         Redux Toolkit                           |   |
|   |      (Manages the current client-side application state)        |   |
|   +-------------------------------+---------------------------------+   |
+-----------------------------------|-------------------------------------+
                                    |
                                    | HTTP / JSON (REST API via CORS)
                                    v
+-------------------------------------------------------------------------+
|                               Server Side                               |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                       FastAPI Application                       |   |
|   |   (API Routing, Request Validation, Authentication & Gateway)   |   |
|   +-------------------------------+---------------------------------+   |
|                                   |                                     |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |                  LangGraph Orchestration Layer                  |   |
|   |    (Multi-step Workflow, State Validation & Decision Trees)     |   |
|   +-------------------------------+---------------------------------+   |
|                                   |                                     |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |                        Groq LLM Engine                          |   |
|   |   (Fast Inference, Structured Extraction & Formulation Checks)  |   |
|   +-----------------------------------------------------------------+   |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                   PostgreSQL Database Storage                   |   |
|   |      (Provides persistent storage for saved complaint records)  |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

---

## Component Responsibilities

### 1. React (Frontend UI)
- **Role:** Interactive presentation layer running in the user's web browser.
- **Responsibilities:**
  - Render complaint submission forms, QA review dashboards, and validation statuses.
  - Apply clean pharmaceutical UI design standards with Google Inter typography.
  - Collect user input and dispatch actions to the Redux store.
  - Never directly communicate with Groq or third-party AI APIs.

### 2. Redux Toolkit (Client State Management)
- **Role:** Centralized client-side state container.
- **Responsibilities:**
  - Redux manages the current client-side application state, while PostgreSQL provides persistent storage for saved complaint records.
  - Holds active form inputs, UI interaction status, asynchronous request statuses (idle, pending, succeeded, failed), and temporary QA review state.
  - Ensures a single source of truth within the browser session.

### 3. FastAPI (Backend Orchestration & API Layer)
- **Role:** High-performance, asynchronous Python web API.
- **Responsibilities:**
  - Expose validated REST endpoints for the client (e.g., `GET /api/health`, and future complaint endpoints).
  - Enforce Cross-Origin Resource Sharing (CORS) rules.
  - Guard private server secrets (such as `GROQ_API_KEY` and database credentials).
  - Serve as the controller that invokes the LangGraph workflow and commits data to PostgreSQL.

### 4. LangGraph (AI Workflow Engine)
- **Role:** State machine and cyclic workflow orchestrator for AI operations.
- **Responsibilities:**
  - Coordinate multi-step AI tasks: text extraction, field categorization, severity assessment, and regulatory compliance checks.
  - Provide deterministic guarantees and fallback mechanisms around probabilistic LLM responses.
  - Enforce that AI updates are partial updates (existing fields must be preserved unless explicitly altered).
  - Position AI strictly as an assistant for human QA operators, never the final pharmaceutical decision-maker.

### 5. Groq LLM (Inference Provider)
- **Role:** High-throughput, low-latency Language Model inference.
- **Responsibilities:**
  - Extract structured entities from unstructured complaint narratives.
  - Propose standardized complaint categorizations and initial severity ratings.
  - Operates model-agnostically via environment configuration (`GROQ_MODEL`).

### 6. PostgreSQL (Persistent Storage)
- **Role:** Relational database for long-term data persistence.
- **Responsibilities:**
  - Provides persistent storage for saved complaint records, audit logs, and version history.
  - Enforces ACID compliance, supporting reliable audit trails inspired by pharmaceutical Quality Management System (QMS) principles. (Note: this is an MVP inspired by pharma QMS requirements, not a certified 21 CFR Part 11 system).

---

## Unit 2 Update: Database Architecture & Integration Layer

```
+-------------------------------------------------------------------------+
|                              Client Browser                             |
|                           React + Redux Toolkit                         |
+------------------------------------+------------------------------------+
                                     |
                                     | HTTP / JSON (REST API)
                                     v
+-------------------------------------------------------------------------+
|                              Server Side                                |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                       FastAPI Application                       |   |
|   |          (Request Validation, Endpoints, Dependencies)          |   |
|   +-------------------------------+---------------------------------+   |
|                                   |                                     |
|                                   | Session Injection (get_db)          |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |                   SQLAlchemy 2.x ORM Engine                     |   |
|   |           (Connection Pooling, Mapping, Transactions)           |   |
|   +-------------------------------+---------------------------------+   |
|                                   |                                     |
|                                   | PostgreSQL Protocol (psycopg2)      |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |                  PostgreSQL Database (Supabase)                 |   |
|   |            (Hosted ACID Relational Storage: complaints)         |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

### Database Security & Privilege Demarcation
1. **No Direct Client Access:** The React browser client NEVER connects directly to PostgreSQL/Supabase. All database access is mediated by FastAPI.
2. **Credential Isolation:** Privileged database credentials (`DATABASE_URL`) exist solely in `backend/.env` on the server and are never exposed via network responses, API routes, or client bundles.
3. **Connection Pooling:** SQLAlchemy manages connection pooling (`pool_pre_ping=True`, `pool_recycle=300`) to ensure resilient connectivity with Supabase's connection poolers.

## Unit 3 Update: Complaint CRUD API Layer & End-to-End Data Flow

```
+---------------------------------------------------------------------------------------+
|                                    Client Browser                                     |
|                                React + Redux Toolkit                                  |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | HTTP Request (JSON Payload)
                                            v
+---------------------------------------------------------------------------------------+
|                                  FastAPI Routing Layer                                |
|             (POST, GET, PATCH endpoints in api/routes/complaints.py)                  |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Request Validation / Deserialization
                                            v
+---------------------------------------------------------------------------------------+
|                                  Pydantic Validation                                  |
|         (ComplaintCreate, ComplaintUpdate: type coercion, optionality checks)         |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Dependency Injection (Depends(get_db))
                                            v
+---------------------------------------------------------------------------------------+
|                                  SQLAlchemy 2.x ORM                                   |
|      (Session management: db.add(), db.commit(), db.refresh(), db.query(Complaint))    |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | SQL Queries & Mutations via psycopg2
                                            v
+---------------------------------------------------------------------------------------+
|                               PostgreSQL (Supabase)                                   |
|                     (Authoritative persistent complaints table)                       |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Persisted ORM Entity
                                            v
+---------------------------------------------------------------------------------------+
|                              Pydantic Response Model                                  |
|           (ComplaintResponse with from_attributes=True: UUID & timestamps)            |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Serialized JSON Response (200 / 201)
                                            v
+---------------------------------------------------------------------------------------+
|                                    Client Browser                                     |
+---------------------------------------------------------------------------------------+
```

### Architectural Responsibilities across the Boundary
1. **Pydantic Schemas:** Represent the **public API contract**. They enforce input validation, parse dates, cast integers, and sanitize responses without exposing internal database structures or private fields.
2. **SQLAlchemy Models:** Represent **persistence and database storage**. They define table structures, SQL column types, constraints, and relational mappings in PostgreSQL.
3. **Database Authoritative Principle for PATCH:** The existing row in PostgreSQL is the single source of truth. When applying updates via `PATCH`, only fields explicitly provided in the request payload (`exclude_unset=True`) are updated. Unspecified fields retain their existing values and are never overwritten with `NULL`.

---

## Unit 4 Update: Frontend Complaint Form & Redux State Architecture

In Unit 4, the pharmaceutical complaint intake form was implemented on the React client, wired to Redux Toolkit for unified form state management, and integrated with the FastAPI `POST /api/complaints` endpoint.

```
+---------------------------------------------------------------------------------------+
|                                    Client Browser                                     |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                        ComplaintForm Component (React)                        |   |
|   |   Controlled inputs across 4 sections: Origin, Product, Complaint, Priority   |   |
|   +-----------------------+-------------------------------+-----------------------+   |
|                           |                               ^                           |
|             User Types /  |                               | Reads State               |
|             Selects Field |                               | (useAppSelector)          |
|                           v                               |                           |
|   +-------------------------------------------------------+-----------------------+   |
|   |                       complaintSlice (Redux Toolkit)                          |   |
|   |   State: formData (13 fields), isSaving, error, successMessage, savedId       |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                             User Clicks   | Dispatch setSaving(true)                  |
|                           Save Complaint  | Calls createComplaint()                   |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                        frontend/src/services/api.ts                           |   |
|   |   - Sanitizes empty strings to null                                           |   |
|   |   - Reads VITE_API_BASE_URL (fallback: http://localhost:8000)                 |   |
|   |   - Issues fetch(POST /api/complaints, { headers, body: JSON })               |   |
|   +---------------------------------------+---------------------------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            |
                                            | HTTP POST /api/complaints (JSON)
                                            v
+---------------------------------------------------------------------------------------+
|                               FastAPI Application Gateway                             |
|   - CORS validation (allows http://localhost:5173)                                    |
|   - Pydantic ComplaintCreate schema validation & type coercion                        |
|   - Dependency injection (db: Session = Depends(get_db))                              |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | SQLAlchemy ORM Operations
                                            v
+---------------------------------------------------------------------------------------+
|                                 SQLAlchemy 2.x ORM                                    |
|   - Instantiates Complaint model with validated attributes                            |
|   - db.add(new_complaint) -> db.commit() -> db.refresh(new_complaint)                 |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | SQL INSERT via psycopg2
                                            v
+---------------------------------------------------------------------------------------+
|                             PostgreSQL Storage (Supabase)                             |
|   - Generates persistent UUIDv4 primary key and UTC audit timestamps                  |
|   - Stores clean complaint record (NULL for unsupplied fields)                        |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | HTTP 201 Created (JSON with UUID)
                                            v
+---------------------------------------------------------------------------------------+
|                                    Client Browser                                     |
|   - api.ts parses JSON response                                                       |
|   - Dispatches setSavedComplaintId(id), setComplaintSuccess("..."), setSaving(false)  |
|   - ComplaintForm displays prominent green success alert with persistent UUID         |
|   - Form data remains preserved (never accidentally discarded)                        |
+---------------------------------------------------------------------------------------+
```

### Core Architectural Principles & Security Rules

1. **Redux vs. PostgreSQL (Client State vs. Persistent Storage):**
   - **Redux** manages transient, client-side application state (what the user is currently typing, whether a network request is pending, error messages, and the returned confirmation ID). Redux state lives purely in browser memory and ceases to exist if the tab is closed or reloaded.
   - **PostgreSQL** provides authoritative, durable, ACID-compliant storage for finalized pharmaceutical records. Once committed to PostgreSQL, the complaint is permanent, auditable, and accessible across the enterprise.

2. **Backend Authoritative Validation:**
   - The React frontend performs only lightweight, non-blocking validation (e.g., verifying that non-empty quantities are valid numbers and dates follow `YYYY-MM-DD`).
   - The FastAPI/Pydantic layer remains the **sole authoritative validator**. Because real-world pharmaceutical complaints frequently arrive incomplete, the frontend does not prematurely block submission of partial data that the database schema intentionally permits.
   - If backend validation fails, FastAPI returns standard HTTP 422 with actionable error details, which the frontend displays without losing user input.

3. **Frontend Secret Isolation (Why Secrets Never Belong in Frontend `.env`):**
   - Vite environment variables prefixed with `VITE_` (such as `VITE_API_BASE_URL`) are embedded directly into compiled JavaScript bundles during build time.
   - Any end-user can view these strings by opening browser DevTools or reading network bundles.
   - Sensitive credentials—such as `DATABASE_URL`, database passwords, or `GROQ_API_KEY`—must **never** be placed in frontend code or frontend environment variables. They reside exclusively in server-side configuration (`backend/.env`).

---

## Unit 5 Update: Groq + LangGraph AI Complaint Intake Architecture

In Unit 5, the first AI vertical slice was added: an AI-assisted intake pipeline using **LangGraph** as the workflow orchestrator and **Groq** as the high-throughput inference engine.

```
[User enters unstructured narrative in React AIAssistant]
                             │
                             ▼
[POST /api/ai/complaint-intake (JSON: {"text": "..."})]
                             │
                             ▼
[FastAPI AI Route (backend/app/api/routes/ai.py)]
  - Validates request using AIComplaintIntakeRequest
  - Checks if Groq is configured (returns 503 if missing)
                             │
                             ▼
[LangGraph StateGraph Workflow (backend/app/ai/complaint_graph.py)]
  │
  ├─► Node 1: extract_fields
  │     - Uses ChatGroq with structured output schema (AIComplaintExtraction)
  │     - Anti-hallucination prompt: unmentioned fields MUST be null
  │
  ├─► Node 2: validate_normalize
  │     - Normalizes strings (trims whitespace, converts empty strings to None)
  │     - Enforces non-negative integer for quantity_affected
  │     - Re-validates with Pydantic
  │
  ├─► Node 3: risk_assessment
  │     - Passes extracted facts to ChatGroq (AIRiskAssessment schema)
  │     - Produces preliminary initial_severity, priority, reasoning, and next actions
  │     - Enforces canonical casing and valid categories
  │
  └─► Node 4: build_result
        - Compiles final payload: {"complaint": {...}, "risk_assessment": {...}}
        - Does NOT persist to PostgreSQL
                             │
                             ▼
[HTTP 200 Response: AIComplaintIntakeResponse]
                             │
                             ▼
[React Frontend: Redux aiSlice receives analysisResult]
  - Renders extracted entities summary & risk triage card
  - User inspects AI recommendations
                             │
                             ▼ (User clicks "Apply to Complaint Form")
[Redux complaintSlice updated via populateComplaintFields action]
  - Populates editable form on the left
  - Form remains fully editable for human QA review
                             │
                             ▼ (User explicitly clicks "Save Complaint")
[POST /api/complaints -> PostgreSQL Persistence]
```

### Key Architectural Invariants for AI in Pharmaceutical QMS

1. **Human-in-the-Loop (Non-Autonomous Database Write):**
   - Under pharmaceutical Good Manufacturing Practice (GMP), an AI model must never be the final decision-maker or autonomously commit records to official systems of record.
   - The LangGraph workflow produces *advisory proposals* for human QA review. The user reviews and verifies the fields before explicitly clicking "Save Complaint".
2. **Deterministic Workflow via LangGraph vs. Autonomous Agents:**
   - Rather than an unpredictable autonomous agent loop, LangGraph coordinates a fixed, directed acyclic workflow:
     $$\text{START} \longrightarrow \text{extract\_fields} \longrightarrow \text{validate\_normalize} \longrightarrow \text{risk\_assessment} \longrightarrow \text{build\_result} \longrightarrow \text{END}$$
   - This ensures strict auditability, deterministic state transitions, and verifiable intermediate steps.
3. **Server-Side Groq Isolation & Model Agnosticism:**
   - `GROQ_API_KEY` exists strictly on the server (`backend/.env`).
   - `GROQ_MODEL` is configurable via environment variables, avoiding hard-coded deprecated models.

## Unit 6 Update: Edit Complaint Tool & Conditional LangGraph Workflow

In Unit 6, the **Edit / Correct Complaint Tool** was introduced. It enables Quality Assurance personnel to supply conversational corrections (e.g., *"Actually, 50 tablets were affected."* or *"Change customer to XYZ Hospital."*) against an existing complaint.

The system extracts **ONLY** the minimal requested changes, strictly preserves all unmentioned facts, dynamically recalculates preliminary risk, and presents an interactive before/after diff for human verification.

```
[User enters correction prompt in React AIAssistant (Edit Tab)]
                             │
                             ▼
[POST /api/ai/complaint-edit (JSON: {"edit_instruction": "...", "complaint_id": "...", "current_complaint": {...}})]
                             │
                             ▼
[FastAPI Route (backend/app/api/routes/ai.py)]
  - Validates request schema (AIComplaintEditRequest)
  - Resolves Authoritative Complaint:
      * If complaint_id provided -> Fetch directly from PostgreSQL (Supabase) via SQLAlchemy
      * If no complaint_id (unsaved draft) -> Use current_complaint from Redux form payload
                             │
                             ▼
[LangGraph Conditional StateGraph (backend/app/ai/complaint_graph.py)]
  │
  ├─► Node 1: extract_edit_changes
  │     - Prompts ChatGroq with EDIT_EXTRACTION_SYSTEM_PROMPT
  │     - Extracts ONLY explicitly requested changes into ComplaintChanges schema
  │     - Identifies ambiguity or non-edit queries (sets needs_clarification = True)
  │
  ├─► Node 2: validate_normalize_changes
  │     - Enforces backend EDITABLE_COMPLAINT_FIELDS allowlist (discards illegal/unexpected keys)
  │     - Normalizes types (casts non-negative integer quantity, trims whitespace)
  │     - Determines if workflow should proceed (valid changes present and not ambiguous)
  │
  ├─► Conditional Routing (route_after_edit_validation):
  │     │
  │     ├─► If Ambiguous / Invalid / No Changes:
  │     │     - Bypasses merge_changes and reassess_risk entirely
  │     │     - Routes directly to build_edit_proposal
  │     │     - Returns safe clarification message and guidance
  │     │
  │     └─► If Valid Edit Request:
  │           │
  │           ▼
  │   Node 3: merge_changes
  │     - Creates merged complaint snapshot (authoritative baseline + validated changes)
  │     - Guarantees 100% preservation of all unmentioned fields
  │           │
  │           ▼
  │   Node 4: reassess_risk
  │     - Passes merged facts to ChatGroq (AIRiskAssessment schema)
  │     - Dynamically recalculates preliminary severity, priority, reasoning, and QA next steps
  │           │
  │           ▼
  │   Node 5: build_edit_proposal
  │     - Generates structured diff table: [Field, Current Value, Proposed Value, Changed Status]
  │     - Assembles AIComplaintEditProposal payload
  │     - Zero database writes (100% read-only)
                             │
                             ▼
[HTTP 200 Response: AIComplaintEditProposal]
                             │
                             ▼
[React Frontend: Redux aiSlice receives editProposal]
  - Renders Proposed Change Set Diff Table & Recalculated Risk Card
  - Highlights exact fields modified (e.g. Quantity Affected: 25 -> 50)
  - Displays Preservation Guarantee banner
                             │
                             ▼ (User clicks "Apply Changes to Form")
[Redux complaintSlice updated via applyComplaintChanges action]
  - Updates only the modified fields in the active form
  - Unmodified fields remain completely intact
  - Left form remains 100% interactive and editable for QA review
                             │
                             ▼ (User clicks "Save Complaint" / PATCH)
[Authoritative Persistence to PostgreSQL via FastAPI CRUD]
```

### The Three Data Layers: Separation of Concerns

To prevent data loss, race conditions, and uncontrolled mutations, Unit 6 establishes strict demarcation across three distinct data layers:

| Layer | Technology | Role & Authority | Mutation Boundary |
| :--- | :--- | :--- | :--- |
| **1. Database Layer** | PostgreSQL (Supabase via SQLAlchemy) | **Authoritative System of Record** for all persisted complaints. When `complaint_id` is supplied, this layer supersedes any client state. | Modified **only** when user explicitly triggers `POST /api/complaints` or `PATCH /api/complaints/{id}`. The AI edit endpoint **never** writes to this layer. |
| **2. Client Application Layer** | Redux Toolkit (`complaintSlice`) | **Active Working State** for the form currently being viewed or edited in the user's browser. | Updated by user typing, resetting, or by clicking "Apply Changes to Form". Ceases to exist if browser tab is closed without saving. |
| **3. AI Proposal Layer** | Redux Toolkit (`aiSlice`) & LangGraph | **Advisory Change Proposal (Diff)** generated from conversational user requests. | Ephemeral. Contains proposed delta, field-by-field diff, and recalculated risk. Cannot alter form state or database state until explicitly approved by human user. |

### Critical Architectural Safeguards

1. **Explicit Backend Allowlist (`EDITABLE_COMPLAINT_FIELDS`):**
   Relying solely on LLM prompt instructions to restrict modifications is unsafe. The backend validation layer explicitly inspects the extracted dictionary against an immutable allowlist:
   `{'complaint_source', 'customer_name', 'product_name', 'product_strength', 'batch_lot_number', 'quantity_affected', 'manufacturing_date', 'expiry_date', 'complaint_type', 'complaint_date', 'detailed_description', 'initial_severity', 'priority'}`.
   Any extraneous, internal, or primary key fields (such as `id` or `created_at`) are automatically pruned.
2. **Authoritative Persisted Record Authority:**
   When editing an already-saved complaint (`complaint_id` present), the backend queries PostgreSQL directly. This ensures stale frontend data (e.g. from an out-of-date browser tab) cannot corrupt the authoritative complaint baseline. For unsaved drafts, the in-memory form payload provides the necessary context.
3. **Conditional Workflow Early Exit:**
   Ambiguous or non-edit inputs (e.g., *"What is the weather today?"* or *"Change the quantity"* without specifying a number) do not proceed to merge or risk recalculation. The conditional graph safely halts at validation and returns a clear explanation of what information is missing.

## Unit 7 Update: Document Extraction Tool & File Ingestion Architecture

In Unit 7, the **Document Extraction Tool** was introduced. It allows QA specialists to upload complaint documents in **PDF, DOCX, TXT, or EML** formats (up to **10 MB**), extract raw text streams in memory using deterministic Python libraries, process the extracted text through a dedicated **LangGraph** workflow with **Groq LPU** inference, and present structured complaint proposals and preliminary risk assessments to the React frontend for human review.

```
[User drops or selects file in React AIAssistant (Document Upload Tab)]
                             │
                             ▼
[POST /api/ai/document-extraction (multipart/form-data: file=...)]
                             │
                             ▼
[FastAPI Routing Layer (backend/app/api/routes/ai.py)]
  │
  ├─► Stage 1: Deterministic File Validation (Zero Groq Dependency)
  │     - Enforces allowed extensions: .pdf, .docx, .txt, .eml (HTTP 400 if invalid)
  │     - Enforces 10 MB payload ceiling (HTTP 413 if oversized)
  │     - Rejects 0-byte files (HTTP 422)
  │
  ├─► Stage 2: In-Memory Deterministic Text Parsing (backend/app/ai/document_extractor.py)
  │     - In-memory parsing via BytesIO (zero temporary disk files created)
  │     - PDF: pypdf.PdfReader extracts page text; flags scanned/empty PDFs (HTTP 422)
  │     - DOCX: python-docx extracts paragraph text and structured table cell text
  │     - TXT: UTF-8 decoder with Latin-1 fallback
  │     - EML: email.parser.BytesParser extracts body text and isolates header Date as metadata
  │
  ├─► Stage 3: LLM Readiness Check
  │     - Only checks GROQ_API_KEY after deterministic extraction succeeds
  │     - Returns HTTP 503 if LLM is unconfigured
  │
  └─► Stage 4: LangGraph Workflow (backend/app/ai/complaint_graph.py: document_extraction_graph)
        │
        ├─► Node 1: extract_document_text
        │     - Validates and wraps extracted text in LangGraph state
        │
        ├─► Node 2: extract_complaint_fields
        │     - Prompts ChatGroq with EXTRACTION_SYSTEM_PROMPT
        │     - Enforces Anti-Hallucination & EML Date metadata rules
        │     - Populates AIComplaintExtraction schema
        │
        ├─► Node 3: validate_normalize
        │     - Sanitizes strings, strips whitespace, converts empty strings to None
        │     - Enforces non-negative integer for quantity_affected
        │
        ├─► Node 4: risk_assessment
        │     - Passes extracted facts to ChatGroq (AIRiskAssessment schema)
        │     - Proposes preliminary severity, priority, reasoning, and QA next actions
        │
        └─► Node 5: build_result
              - Compiles AIDocumentExtractionResponse (file metadata + complaint + risk)
              - Database safety: ZERO writes to PostgreSQL (delta = 0)
                             │
                             ▼
[HTTP 200 Response: AIDocumentExtractionResponse]
                             │
                             ▼
[React Frontend: Redux aiSlice receives documentResult]
  - Renders Document Metadata Banner (file name, format, size, extracted char count)
  - Displays Extracted Fields Summary Cards (with "Human Review Required" pill)
  - Displays Preliminary Risk Assessment & Actionable Next Steps
                             │
                             ▼ (User clicks "Apply to Complaint Form")
[Redux complaintSlice updated via populateComplaintFields action]
  - Non-destructive Apply: Only non-null extracted fields update the form
  - Existing non-empty form values are strictly preserved if extracted field is null
  - Left form remains 100% interactive and editable for QA review
                             │
                             ▼ (Optional conversational edits)
[AIAssistant Edit / Correct Tab inherits extracted complaint for seamless refinement]
                             │
                             ▼ (User explicitly clicks "Save Complaint")
[POST /api/complaints -> Authoritative PostgreSQL Persistence]
```

### Architectural Decisions & Technical Safeguards

1. **Deterministic File Validation Before Groq Check:**
   File validation (format support, 10MB size ceiling, empty payload checks) executes before evaluating Groq configuration. This ensures that client-side file upload errors are immediately identified and rejected with appropriate HTTP status codes (400, 413, 422) regardless of AI service availability.

2. **In-Memory Streaming vs. Disk Persistence:**
   Uploaded files are processed entirely in server memory using `io.BytesIO` streams and `UploadFile.read()`. Files are never written to temporary directories or local disk storage. This minimizes security risks, prevents disk exhaustion, and complies with pharmaceutical data containment principles.

3. **Scanned PDF vs. Short Legitimate Complaints:**
   A PDF is deemed unreadable only if its extracted text across all pages is completely empty or consists solely of whitespace, triggering a controlled HTTP 422 with a helpful message: *"Could not extract readable text from this PDF. The file may be scanned/image-only."* Arbitrary character thresholds are avoided, allowing legitimate concise complaint notices to pass through safely.

4. **EML Transmission Metadata vs. Complaint Observation Date:**
   In email complaints, the `Date` header indicates when the email was transmitted through mail servers—not necessarily when the defect occurred or was observed by the customer. The extractor explicitly separates email header date as metadata, and the LLM prompt instructs that `complaint_date` must remain `null` unless the email narrative explicitly provides the observation/received date.

5. **Non-Destructive Form Merging (Redux):**
   When the user clicks "Apply to Complaint Form", extracted fields that are `null` or empty do not overwrite existing values already present in the Redux form. Only fields with extracted values update the form, preventing accidental loss of user-entered data.

---

## Unit 8 Update: Final Product Readiness Audit and System Polish

In Unit 8, a comprehensive product-readiness audit across the entire system was executed. The core architecture proved sound and resilient; specific polish items were integrated to ensure seamless full-lifecycle CRUD operations and deprecation-free runtime environments:

### 1. Dynamic Form Mode (POST vs. PATCH Lifecycle Integration)
Prior to Unit 8, the left complaint intake form submitted exclusively via `POST /api/complaints`. When a user loaded an existing complaint or saved a draft and subsequently issued an AI correction (Unit 6 conversational edit flow), submitting the form would inadvertently create a duplicate record in PostgreSQL.
- **Polish Fix:** In `frontend/src/services/api.ts` and `frontend/src/components/complaint/ComplaintForm.tsx`, the submission pipeline was upgraded:
  - If `savedComplaintId` is present in Redux (`complaintSlice.savedComplaintId`), the form dynamically switches to **Update Mode**.
  - The submit button label updates to `"Update Complaint (PATCH)"`.
  - The submit handler calls `updateComplaint(id, payload)` which issues `PATCH /api/complaints/{id}`.
  - The PostgreSQL record is updated in place, advancing its `updated_at` timestamp while preserving the row count and primary key UUID.
  - If `savedComplaintId` is null (initial submission), the form operates in **Creation Mode** via `POST /api/complaints`.

### 2. HTTP Status Code Modernization
In FastAPI route definitions (`backend/app/api/routes/ai.py`), references to deprecated `status.HTTP_422_UNPROCESSABLE_ENTITY` were updated to standard `status.HTTP_422_UNPROCESSABLE_CONTENT`. This eliminated Starlette runtime deprecation warnings in Python 3.14 without changing API contracts or client behavior.

### 3. UI Status Badging & Brand Consistency
The header status badge in `frontend/src/App.tsx` was updated from `"Unit 5 • Groq + LangGraph AI"` to `"AI-Assisted QMS • Groq + LangGraph"`, accurately reflecting the unified multi-modal intake system (Text, Document Upload, and Conversational Edit).


---

## Submission Polish Update: UI Visual Alignment & Pharmaceutical QMS Polish

Following the core feature completion (Units 1–8), a final visual alignment pass was performed to match the visual layout and design language of the enterprise pharmaceutical QMS reference:

### Visual Architecture & Styling Alignments
1. **Design System & Palette:** Modern enterprise light aesthetic with slate-50 background (`#f8fafc`), clean white card containers (`#ffffff`), subtle borders (`#e2e8f0`), and accessible blue primary actions (`#2563eb`).
2. **Typography:** Standardized globally on `Inter` with modern tabular font numerals, strict uppercase tracking on section legends, and consistent font scales.
3. **Left Form Structure:**
   - Header hierarchy: "Log Customer Complaint" with subtitle "API & FDF Quality Assurance Module".
   - Amber pill badge: "Pending Triage" (dynamic to "Registered" once saved).
   - 4 numbered uppercase section legends: `1. ORIGIN & CUSTOMER DETAILS`, `2. PRODUCT & BATCH IDENTIFICATION`, `3. COMPLAINT DETAILS`, `4. INITIAL ASSESSMENT & PRIORITY`.
   - Explicit "Awaiting AI extraction..." placeholders and unit adornment (`kg / units`).
4. **Right AI Assistant Panel:**
   - Panel title: "AI Complaint Intake Assistant" with "BETA" badge.
   - Unified intake zone: Document dropzone, visual "OR" divider, and paste complaint text/email area on the default tab.
   - Informative format notice: Green alert card highlighting supported formats (`PDF, DOCX, TXT, EML • Max 10MB`).
   - Animated extraction progress bar and idle AI assistant intro card.
   - Bottom interaction prompt bar: "Ask me anything about this complaint...".
5. **Architectural Invariants Strictly Preserved:**
   - Zero change to backend endpoints, API contracts, LangGraph workflows, AI prompts, or DB schema.
   - All 3 workflows (`Text Intake`, `Document Upload`, `Edit / Correct`) retained and fully accessible via tablist navigation.
   - Absolute database write isolation invariant preserved: AI operations remain 100% ephemeral and in-memory until explicit user save.


