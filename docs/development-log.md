# Development Log

A chronological record of milestones, architectural implementations, deferred items, and verification results for the **AIVOA Customer Complaint Management System**.
Historical records in this log are strictly preserved.

---

## [2026-09-14] - Unit 1: Establishing Project Foundation

### 1. Objective
Establish a clean, robust, and minimal architectural foundation for the AIVOA Customer Complaint Management System. 
Verify end-to-end frontend scaffolding, Redux Toolkit integration, minimal FastAPI health endpoint, security boundaries, and project documentation with zero speculative bloat.

### 2. What Was Implemented
- **Repository Hygiene & Security:**
  - Created root `.gitignore` to prevent committing Python virtual environments (`.venv/`, `venv/`), Node modules (`node_modules/`), build outputs (`dist/`), and environment secret files (`.env`).
  - Allowed tracking of `.env.example` templates via explicit un-ignore rule.
- **Frontend Foundation (`frontend/`):**
  - Initialized React 19 + TypeScript + Vite project in `frontend/`.
  - Configured Google Inter font in `frontend/index.html` and applied professional, responsive styling in `frontend/src/index.css`.
  - Installed `@reduxjs/toolkit` and `react-redux`.
  - Established central Redux store (`src/store/index.ts`) with typed hooks (`useAppDispatch`, `useAppSelector` in `src/store/hooks.ts`).
  - Implemented `src/store/slices/appSlice.ts` to perform an isolated integration test of state dispatch and selector retrieval.
  - Implemented interactive verification card in `src/App.tsx` and mounted Redux Provider in `src/main.tsx`.
  - Created `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000` and clear client security warnings.
- **Backend Foundation (`backend/`):**
  - Created minimal Python dependency specification in `backend/requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic`, `python-dotenv`).
  - Implemented minimal FastAPI application in `backend/app/main.py`.
  - Added Cross-Origin Resource Sharing (CORS) middleware to allow browser communication from `http://localhost:5173`.
  - Added `GET /api/health` and `GET /` endpoints for connectivity verification.
  - Created `backend/.env.example` containing server-side placeholders for `PORT`, `HOST`, `CORS_ORIGINS`, `GROQ_API_KEY`, `GROQ_MODEL`, and `DATABASE_URL`.
- **Project Documentation (`docs/`):**
  - Created baseline documentation suite:
    - `docs/architecture.md`: System architecture diagram, component roles, and security principles.
    - `docs/database.md`: Persistent storage strategy using PostgreSQL (schema design deferred).
    - `docs/decisions.md`: Architectural Decision Records (ADR-001 through ADR-005).
    - `docs/interview-notes.md`: Conceptual interview questions and beginner-friendly answers.
    - `docs/development-log.md`: Chronological implementation and verification record.

### 3. What Was Intentionally NOT Implemented
In strict adherence to dependency discipline and anti-over-engineering principles:
- **No Groq LLM integration:** No Groq SDK, no API calls, no AI prompts. (Deferred to Phase 3).
- **No LangGraph workflows:** No graph definitions, state nodes, or decision trees. (Deferred to Phase 3).
- **No PostgreSQL database connections:** No ORM models, no SQL tables, no migration tools, no fake DB connections. (Deferred to Phase 2).
- **No Complaint UI or Forms:** No intake forms, validation logic, or complaint domain slices.
- **No Document Parsing:** No PDF/OCR processing libraries.
- **No Heavy Infrastructure:** No Docker, Kubernetes, Celery, Redis, or Vector Databases.

### 4. Verification & Testing Performed
- **Frontend Type-Check & Production Build:**
  - Command: `npm run build` inside `frontend/`.
  - Result: Passed with zero errors. Transformed 27 modules into production assets in 146ms.
- **Frontend Linter:**
  - Command: `npm run lint` inside `frontend/`.
  - Result: Passed with 0 errors and 0 warnings across all files.
- **Backend Server Startup & Endpoints:**
  - Command: `uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
  - Health check verification: `curl -s http://127.0.0.1:8000/api/health`
  - Result: Returned HTTP 200 with payload:
    ```json
    {"status":"ok","service":"AIVOA Complaint Management System API","unit":"Unit 1: Foundation"}
    ```
  - Root endpoint verification: `curl -s http://127.0.0.1:8000/`
  - Result: Returned HTTP 200 with payload:
    ```json
    {"service":"AIVOA Complaint Management System API","status":"online","docs_url":"/docs"}
    ```
- **Git & Security Verification:**
  - Command: `git status --ignored --short`
  - Result: Confirmed `.venv/`, `frontend/node_modules/`, `frontend/dist/`, and Python caches are strictly ignored by Git. No credentials or secrets exist in tracked files.

### 5. Next Steps (Pending User Approval)
- Unit 2: Complaint Data Modeling & Database Foundation (PostgreSQL schema design and complaint intake data structures).

---

## [2026-09-15] - Unit 2: Database Foundation & Complaint Schema

### 1. Objective
Establish the PostgreSQL / Supabase database foundation and create the initial `complaints` database schema via SQLAlchemy 2.x, strictly following the assignment's complaint form specification. 
Ensure database access is mediated exclusively through FastAPI with strict credential isolation and safe connectivity checks.

### 2. What Was Implemented
- **Dependencies (`backend/requirements.txt`):**
  - Added `sqlalchemy>=2.0.0` and `psycopg2-binary>=2.9.0`.
  - Installed and verified in local virtual environment.
- **Database Architecture Layer (`backend/app/db/`):**
  - Created `backend/app/db/__init__.py`: Package entry point exporting database session, engine, and models.
  - Created `backend/app/db/database.py`:
    - Loads `DATABASE_URL` securely from `backend/.env`.
    - Normalizes `postgres://` to `postgresql://`.
    - Validates scheme and detects placeholder configurations.
    - Configures SQLAlchemy engine with connection pool resiliency (`pool_pre_ping=True`, `pool_recycle=300`).
    - Provides `SessionLocal` sessionmaker and FastAPI `get_db()` dependency.
    - Implements `init_db()` using `Base.metadata.create_all(bind=engine)`.
    - Implements `check_db_connection()` executing `SELECT 1` without exposing passwords or credentials.
  - Created `backend/app/db/models.py`:
    - Defined `Complaint` SQLAlchemy model matching all 16 specification columns:
      `id` (UUID, PK), `complaint_source`, `customer_name`, `product_name`, `product_strength_grade`, `batch_lot_number`, `manufacturing_date`, `expiry_date`, `quantity_affected`, `complaint_type`, `complaint_date`, `detailed_description`, `initial_severity`, `priority`, `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
    - Preserved intentional nullability across all domain fields (`NULL` represents missing data; no fake placeholders).
    - Preserved `quantity_affected` as `INTEGER` while documenting the limitation regarding approximation semantics.
    - Kept `initial_severity`, `priority`, and `complaint_type` as `TEXT` (no database ENUMs in this MVP).
    - Omitted AI risk scores, CAPA actions, and root-cause fields from this complaint facts table.
- **FastAPI Integration (`backend/app/main.py`):**
  - Added async `lifespan` context manager that calls `init_db()` on server startup.
  - Updated `GET /api/health` to report safe database status (`connected`, `not_configured`, or generic `error`).
- **Living Documentation (`docs/`):**
  - Updated `docs/architecture.md`: Documented React → FastAPI → SQLAlchemy → Supabase PostgreSQL and QMS-inspired MVP scope.
  - Updated `docs/database.md`: Documented complete 16-column table specification, data rules, and schema decisions.
  - Updated `docs/decisions.md`: Added ADR-006 through ADR-011.
  - Updated `docs/interview-notes.md`: Added Questions 9–14 covering PostgreSQL, UUIDs, NULL semantics, ORM, connection pools, and AI data separation.
  - Updated `docs/development-log.md`: Appended Unit 2 chronological changelog.

### 3. What Was Intentionally NOT Implemented
- **No Complaint CRUD Endpoints:** Deferred to Unit 3.
- **No Groq / LangGraph / AI workflow code:** Deferred to AI phase.
- **No Frontend Redux Complaint State or Forms:** Client-side complaint state deferred.
- **No Alembic Migration Tooling:** Initial schema created via `Base.metadata.create_all()` to avoid premature tooling churn.
- **No Fake Complaint Data:** No fake rows inserted into Supabase.

### 4. Verification & Testing Performed
- **Live Supabase PostgreSQL Connectivity & Schema Introspection:**
  - Command: `PYTHONPATH=. ./.venv/bin/python backend/test_db_verification.py`
  - Result: **PASSED (ALL 16 COLUMNS VERIFIED)**:
    - Connection Status: `connected` (PostgreSQL hosted on Supabase).
    - Table Existence: Confirmed `'complaints'` table successfully initialized via `Base.metadata.create_all()`.
    - Total Columns: Exactly 16 columns detected and verified against schema.
    - Column Types:
      - `id`: `UUID`, non-null, primary key.
      - `complaint_source`: `TEXT`, nullable.
      - `customer_name`: `TEXT`, nullable.
      - `product_name`: `TEXT`, nullable.
      - `product_strength_grade`: `TEXT`, nullable.
      - `batch_lot_number`: `TEXT`, nullable.
      - `manufacturing_date`: `DATE`, nullable.
      - `expiry_date`: `DATE`, nullable.
      - `quantity_affected`: `INTEGER`, nullable.
      - `complaint_type`: `TEXT`, nullable.
      - `complaint_date`: `DATE`, nullable.
      - `detailed_description`: `TEXT`, nullable.
      - `initial_severity`: `TEXT`, nullable.
      - `priority`: `TEXT`, nullable.
      - `created_at`: `TIMESTAMP`, non-null (UTC).
      - `updated_at`: `TIMESTAMP`, non-null (UTC).
    - Primary Key: Validated `complaints_pkey` on `['id']`.
    - Record Cleanliness: Validated row count is exactly `0` (no fake/dirty test rows inserted).
- **Backend Server Startup & Live Health Check:**
  - Command: `uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
  - Health check endpoint verification: `curl http://127.0.0.1:8000/api/health`
  - Result: Returned HTTP 200:
    ```json
    {
      "status": "ok",
      "service": "AIVOA Complaint Management System API",
      "unit": "Unit 2: Database Foundation",
      "database": {
        "status": "connected",
        "provider": "PostgreSQL (Supabase)"
      }
    }
    ```
- **Robust URL Normalization & Secret Isolation:**
  - Verified that passwords containing special characters (such as `@`) are safely URL-encoded in-memory without breaking URI parsing.
  - Verified that credentials, passwords, and connection strings are never exposed in JSON responses, terminal outputs, or log streams.
- **Frontend Regression Check:**
  - Ran `npm run build` and `npm run lint` in `frontend/`: Passed with 0 errors.
- **Git Security Verification:**
  - Ran `git status`: Confirmed `backend/.env` remains strictly untracked.

### 5. Next Steps (Pending User Approval)
- Unit 3: Complaint API endpoints and data ingestion (FastAPI endpoints to create and retrieve complaints).

---

## [2026-09-15] - Unit 3: Complaint CRUD API Implementation

### 1. Objective
Implement a clean, robust, and type-safe Complaint CRUD API using FastAPI, Pydantic v2, and SQLAlchemy 2.x connected to PostgreSQL on Supabase.
Enforce the authoritative database record rule for partial updates (`PATCH`) and keep the public API boundary decoupled from database storage models.

### 2. What Was Implemented
- **Pydantic Schemas (`backend/app/schemas/`):**
  - Created `backend/app/schemas/__init__.py` and `backend/app/schemas/complaint.py`.
  - `ComplaintBase`: Base schema containing all 13 complaint domain fields with optional/nullable typing.
  - `ComplaintCreate`: Schema for submitting new complaints via `POST /api/complaints`.
  - `ComplaintUpdate`: Schema for partial updates via `PATCH /api/complaints/{id}`.
  - `ComplaintResponse`: Schema for API responses including UUID `id`, domain fields, and `created_at`/`updated_at` audit timestamps (`from_attributes=True`).
- **RESTful Routes (`backend/app/api/routes/complaints.py`):**
  - `POST /api/complaints`: Validates payload, persists `Complaint` model to PostgreSQL, commits, and returns HTTP 201 with generated UUID.
  - `GET /api/complaints`: Queries and returns all complaints ordered newest first (`created_at.desc()`).
  - `GET /api/complaints/{complaint_id}`: Retrieves a single complaint by UUID; returns HTTP 404 if not found.
  - `PATCH /api/complaints/{complaint_id}`: Retrieves existing record from PostgreSQL, applies only explicitly supplied fields (`exclude_unset=True`), commits, and returns HTTP 200. Returns HTTP 404 if nonexistent.
- **Application Integration (`backend/app/main.py`):**
  - Mounted `complaints_router` under prefix `/api/complaints`.
  - Bumped API version to `0.3.0`.
- **Living Documentation (`docs/`):**
  - Updated `docs/architecture.md`: Documented end-to-end data flow (React → HTTP/JSON → FastAPI → Pydantic → SQLAlchemy → PostgreSQL).
  - Updated `docs/database.md`: Documented Pydantic validation boundary vs. SQLAlchemy persistence layer.
  - Updated `docs/decisions.md`: Added ADR-012 (Schema/Model separation) and ADR-013 (Authoritative DB for PATCH).
  - Updated `docs/interview-notes.md`: Added Questions 15–20 explaining Pydantic vs SQLAlchemy, POST vs PATCH, dependency injection, and partial update mechanics.
  - Updated `docs/development-log.md`: Appended Unit 3 changelog.

### 3. What Was Intentionally NOT Implemented
- **No Groq / LangGraph / AI workflow code:** Deferred to AI phase.
- **No Document Upload / OCR / PDF extraction:** Deferred to document ingestion phase.
- **No Frontend Complaint Form / Redux Complaint Slice:** Kept frontend foundation clean and focused.
- **No Authentication / RBAC:** Deferred to security phase.
- **No Alembic Migration Tooling:** Deferred until schema modifications require versioned migrations.

### 4. Verification & Testing Performed
- **End-to-End API Test Suite (`backend/test_crud_verification.py`):**
  - Executed test suite against live Uvicorn server and Supabase PostgreSQL.
  - **Step 1 (Health Check):** `GET /api/health` returned HTTP 200 with database status `connected`.
  - **Step 2 (POST Complaint):** `POST /api/complaints` with realistic Paracetamol 500mg batch `BATCH-2026-001` test data returned HTTP 201 Created with generated UUID (`f505cbb8-7b76-4b0b-82ad-291e39ed7c7f`).
  - **Step 3 (GET List):** `GET /api/complaints` returned HTTP 200 with list containing the newly created complaint.
  - **Step 4 (GET Single):** `GET /api/complaints/{id}` returned HTTP 200 with exact matching data.
  - **Step 5 (PATCH Partial Update):** Sent payload changing only `quantity_affected` from 5 to 8. Confirmed:
    - `quantity_affected` was updated to 8.
    - `customer_name`, `product_name`, `batch_lot_number`, and all other fields remained completely unchanged.
  - **Step 6 (404 Error Handling):** Verified that nonexistent UUID (`00000000-0000-0000-0000-000000000000`) returns HTTP 404 on both GET and PATCH.
  - **Step 7 (422 Validation Error):** Verified that invalid payload (`quantity_affected: "not-an-integer"`) is rejected by Pydantic with HTTP 422 Unprocessable Entity.
  - **Step 8 (Direct DB Inspection):** Queried PostgreSQL directly via SQLAlchemy and confirmed the complaint was updated to quantity 8.
  - **Step 9 (Database Cleanup):** Deleted the test record from PostgreSQL and confirmed row count in `complaints` table is back to `0`.
- **Frontend Regression Check:**
  - Ran `npm run build` and `npm run lint` in `frontend/`: Passed with 0 errors.
- **Git Security Verification:**
  - Ran `git status`: Confirmed `backend/.env` remains strictly untracked.

### 5. Next Steps (Pending User Approval)
- Unit 4: Frontend Complaint State & Intake Form UI (wiring Redux Toolkit complaint slice and interactive intake form to the backend CRUD API).

---

## [2026-09-15] - Unit 4: Pharmaceutical Complaint Intake Form & Redux State Integration

### 1. Objective
Build the actual pharmaceutical customer complaint intake form on the React frontend, connect it to Redux Toolkit for unified form state management, and integrate it with the existing FastAPI `POST /api/complaints` endpoint and Supabase PostgreSQL persistence.
Provide a clean two-column QMS layout featuring a placeholder for the future AI assistant while strictly preserving all existing Unit 1–3 architecture and historical documentation.

### 2. What Was Implemented
- **Redux State Management (`frontend/src/store/`):**
  - Created `frontend/src/store/slices/complaintSlice.ts`:
    - Defined typed `ComplaintFormData` matching the 13 backend domain fields.
    - Defined `ComplaintState` tracking `formData`, `isSaving` (boolean), `error` (string | null), `successMessage` (string | null), and `savedComplaintId` (string | null).
    - Created clean reducers and actions: `updateComplaintField`, `resetComplaintForm`, `setSaving`, `setComplaintError`, `setComplaintSuccess`, `setSavedComplaintId`.
  - Registered `complaintReducer` in `frontend/src/store/index.ts` alongside existing `appReducer`.
- **Frontend API Service (`frontend/src/services/api.ts`):**
  - Created typed `createComplaint(complaint: ComplaintFormData): Promise<ComplaintResponse>`.
  - Configured dynamic base URL from `import.meta.env.VITE_API_BASE_URL` with fallback to `http://localhost:8000`.
  - Implemented client-side empty string sanitization (`""` → `null`) to maintain SQL nullability and prevent date parsing errors in PostgreSQL.
  - Implemented numeric casting for `quantity_affected` (converts non-empty strings to numbers).
  - Handled non-2xx HTTP responses with descriptive error messages.
- **Controlled Complaint Form Component (`frontend/src/components/complaint/ComplaintForm.tsx`):**
  - Built full pharma intake form grouped into 4 accessible fieldsets:
    1. *Origin & Customer Details*: Complaint Source, Customer Name.
    2. *Product & Batch Identification*: Product Name, Product Strength/Grade, Batch/Lot Number, Manufacturing Date, Expiry Date, Quantity Affected.
    3. *Complaint Details*: Complaint Type, Complaint Date, Detailed Complaint Description.
    4. *Initial Assessment & QA Priority*: Initial Severity (Low, Medium, High, Critical), Priority (Low, Medium, High, Urgent).
  - Wired all inputs as controlled components dispatching `updateComplaintField` on change.
  - Built Reset Form button (dispatches `resetComplaintForm` and clears status alerts).
  - Built Save Complaint button with loading spinner, submit prevention, and button disabling during requests.
  - Added clear success notification displaying the generated PostgreSQL UUID upon success.
  - Added error alert banner preserving all entered data upon network or validation failures.
- **Two-Column QMS Workspace Layout (`frontend/src/App.tsx` & `frontend/src/index.css`):**
  - Implemented responsive two-column grid layout in `App.tsx`:
    - Left column: Full `ComplaintForm` component.
    - Right column: AI Complaint Intake Assistant placeholder card.
  - Styled with Google Inter typography, accessible focus indicators, clean fieldset borders, and badge chips.
  - Configured responsive media queries to stack columns on mobile/tablet screens.
  - Updated `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000`.

### 3. What Was Intentionally NOT Implemented
- **No Groq / LangGraph / AI workflow code:** Right assistant panel is strictly a visual placeholder.
- **No Document Upload / OCR / PDF parsing:** Deferred to Unit 5.
- **No Authentication / RBAC:** Deferred to security phase.
- **No CAPA / Root Cause / Investigation tables:** Fact intake only.

### 4. Verification & Testing Performed
- **Frontend Type-Check & Production Build:**
  - Command: `npm run build` inside `frontend/`.
  - Result: Passed with zero errors. Transformed 31 modules into production assets in 153ms.
- **Frontend Linter:**
  - Command: `npm run lint` inside `frontend/`.
  - Result: Passed with 0 errors and 0 warnings.
- **End-to-End Browser Automation Verification (Playwright MCP):**
  - Automated full browser session running against live FastAPI backend (`http://localhost:8000`) and Vite dev server (`http://localhost:5173`).
  - Tested:
    1. Form field entry across all 4 fieldsets (Customer Name, Product Name, Batch Number, Dates, Quantity, Description, Severity, Priority).
    2. Reset Form button: verified complete clearance of inputs and status messages.
    3. Complaint submission: submitted realistic pharmaceutical complaint (`Paracetamol 500 mg`, batch `BATCH-2026-001`, quantity `5`, severity `High`, priority `Urgent`).
    4. Network response: verified HTTP 201 Created from `POST /api/complaints`.
    5. Success alert: verified green banner appeared displaying the returned UUID: `96406bba-cc2a-4f6b-bb3f-44eda2ba25ac`.
    6. Preserved inputs: confirmed entered data was not lost after saving.
    7. Layout & responsiveness: captured visual artifacts on desktop and verified responsive layout.
- **PostgreSQL / Supabase Verification & Cleanup:**
  - Queried Supabase directly via SQLAlchemy script: confirmed record `96406bba-cc2a-4f6b-bb3f-44eda2ba25ac` was successfully stored with all 13 fields.
  - Cleaned up test record: executed `DELETE FROM complaints WHERE id = '96406bba-cc2a-4f6b-bb3f-44eda2ba25ac'`.
  - Confirmed database row count is back to `0` (zero dirty or fake records remaining).

### 5. Next Steps (Pending User Approval)
- Unit 5: AI Document Extraction & Natural Language Complaint Intake (LangGraph + Groq LLM workflow).

---

## [2026-09-16] - Unit 5: Groq + LangGraph AI Complaint Intake

### 1. Objective
Implement the first AI vertical slice for the AIVOA Customer Complaint Management System:
Natural-language complaint text → FastAPI → LangGraph → Groq → structured extraction → normalization → initial risk triage → FastAPI response → React/Redux.
Ensure strict anti-hallucination, null safety, human-in-the-loop review, and complete server-side secret isolation.

### 2. What Was Implemented
- **Dependencies (`backend/requirements.txt`):**
  - Added `groq>=0.37.0`, `langgraph>=1.2.0`, `langchain-groq>=1.1.0`.
  - Verified installation in Python 3.14 virtual environment without dependency conflicts.
- **Server-Side Environment & Groq Client (`backend/app/ai/`):**
  - Updated `backend/.env.example` with `GROQ_API_KEY=your_groq_api_key_here` and `GROQ_MODEL=your_supported_model_here`.
  - Created `backend/app/ai/groq_client.py`:
    - Loads `GROQ_API_KEY` and `GROQ_MODEL` from `backend/.env`.
    - Avoids hardcoding any default model; raises `GroqConfigurationError` with a clear message if unconfigured.
    - Provides `get_chat_groq()` with temperature `0.0` for deterministic extraction.
    - Provides `is_groq_configured()` check.
- **AI Pydantic Schemas (`backend/app/schemas/ai.py`):**
  - `AIComplaintExtraction`: All 11 domain fields typed with optional/null fallback.
  - `AIRiskAssessment`: `initial_severity`, `priority`, `risk_reasoning`, `recommended_next_actions`.
  - `AIComplaintIntakeRequest`: Validates narrative input (rejects empty/whitespace).
  - `AIComplaintIntakeResponse`: Structured container for extraction and risk assessment.
- **Prompts (`backend/app/ai/prompts.py`):**
  - `EXTRACTION_SYSTEM_PROMPT`: Strict anti-hallucination instructions. Sets unstated fields to `null`. Never fabricates lot numbers, dates, or quantities.
  - `RISK_ASSESSMENT_SYSTEM_PROMPT`: Preliminary triage instructions. Acknowledges uncertainty if data is missing. Proposes actionable QA next steps.
- **LangGraph StateGraph Workflow (`backend/app/ai/complaint_graph.py`):**
  - Directed workflow: `START -> extract_fields -> validate_normalize -> risk_assessment -> build_result -> END`.
  - Compiles into deterministic, auditable `CompiledStateGraph`.
  - Does NOT persist or commit to PostgreSQL.
- **FastAPI AI Route (`backend/app/api/routes/ai.py` & `backend/app/main.py`):**
  - `POST /api/ai/complaint-intake`: Validates input, checks AI configuration (returns HTTP 503 if unconfigured), executes graph, and returns structured response.
  - Enhanced `GET /api/health` to report safe AI service status (`configured` vs `not_configured`) without exposing keys.
- **Frontend API Service & Redux Slices:**
  - `frontend/src/services/api.ts`: Added `runComplaintIntake(text: string)`.
  - `frontend/src/store/slices/aiSlice.ts`: Created `aiSlice` managing `inputText`, `isAnalyzing`, `error`, `analysisResult`.
  - `frontend/src/store/slices/complaintSlice.ts`: Added `populateComplaintFields` reducer to copy AI suggestions into manual form inputs without losing existing user inputs.
  - `frontend/src/store/index.ts`: Registered `aiReducer` under `state.ai`.
- **Frontend AI Assistant Component (`frontend/src/components/ai/AIAssistant.tsx`):**
  - Mounted active assistant in `App.tsx` replacing the placeholder card.
  - Features quick-test sample chips, natural language textarea, analyze button with loading spinner, extracted entity chips, risk assessment card (severity, priority, reasoning, next steps), and "Apply to Complaint Form" button.
  - Enhanced `frontend/src/index.css` with responsive styling and color-coded risk badges.

### 3. What Was Intentionally NOT Implemented
- **No Document / Image OCR / PDF / DOCX parsing:** Deferred to Unit 6.
- **No Direct Database Writes by AI:** Human QA must review and click "Save Complaint".
- **No Autonomous Agent Loops / ReAct Tools:** Deterministic LangGraph StateGraph only.
- **No Edit Complaint Feature:** Fact intake only.
- **No Authentication / RBAC:** Deferred to security phase.
- **No RAG or Vector Databases:** Deferred to knowledge base phase.

### 4. Verification & Testing Performed
- **Backend Test Suite (`backend/test_ai_verification.py`):**
  - Ran 7 comprehensive tests:
    - Test 1 (Valid extraction): Verified structured extraction and risk triage.
    - Test 2 (Null safety): Verified unstated fields remain `None` without hallucinations.
    - Test 3 (Validation): Verified empty/whitespace input rejected with HTTP 422.
    - Test 4 (Missing API key): Verified clean HTTP 503 returned without crash.
    - Test 5 (LangGraph pipeline): Verified 4 sequential nodes execute properly.
    - Test 6 (Health endpoint): Verified AI service status reported safely.
    - Test 7 (Database Safety): Confirmed row count in PostgreSQL remained exactly unchanged (delta = 0).
- **CRUD Regression Test Suite (`backend/test_crud_verification.py`):**
  - All 9 CRUD steps passed (POST, GET list, GET by ID, PATCH partial update, 404, 422, direct SQL query, and cleanup).
- **Frontend Build & Linter:**
  - `npm run build`: Passed cleanly in 158ms.
  - `npm run lint`: Passed with 0 errors and 0 warnings.
- **Playwright MCP Browser Automation:**
  - Loaded `http://localhost:5173`.
  - Verified two-column desktop layout with active AI Assistant on the right.
  - Tested unconfigured API key error state: verified clean red alert `⚠️ Analysis Error: Groq AI service is not configured...`.
  - Tested sample prompt fill: populated Paracetamol 500mg narrative.
  - Tested AI extraction result display: verified entities grid, risk triage badges, risk reasoning, and recommended QA actions.
  - Tested "Apply to Complaint Form": verified left form was populated with extracted data and risk values while remaining fully editable.
  - Verified no automated database write occurred.
- **Security Check:**
  - Ran ripgrep search across `frontend/`: Confirmed 0 Groq API keys, 0 Authorization headers, and 0 secret tokens in client code.
- **Live Groq Inference & Factual Accuracy Verification:**
  - Executed live API requests against the configured model (`openai/gpt-oss-120b` via `backend/.env`).
  - Confirmed 100% extraction accuracy on valid complaints (customer, product, strength, batch, quantity).
  - Confirmed strict null-safety (unstated manufacturing/expiry/complaint dates remain `null`).
  - Confirmed source inference accuracy (only marks `complaint_source: Email` if explicitly stated in text; does not infer email from general reports).
  - Confirmed preliminary risk triage (preliminary severity/priority, fact-based reasoning acknowledging missing facts, and actionable QA next steps).
  - Confirmed in-browser human-in-the-loop workflow: "Apply to Complaint Form" populated the left form while keeping it fully editable, with zero automated database mutations.

### 5. Next Steps (Pending User Approval)
- Unit 6: Edit Complaint Tool (conversational natural-language corrections, minimal diff proposals, and conditional LangGraph workflow).

---

## [2026-09-16] - Unit 6: Edit Complaint Tool & Conditional AI Workflow

### 1. Objective
Implement the conversational **Edit / Correct Complaint Tool** for the AIVOA Customer Complaint Management System:
Enable QA specialists to provide natural-language corrections (e.g. *"Actually, 50 tablets were affected."*) against an existing complaint.
The AI extracts **ONLY** the minimal requested changes, validates them against an explicit backend allowlist, merges them with existing facts, dynamically recalculates risk triage, and presents an interactive visual diff for human verification.
Enforce conditional routing to safely halt early on ambiguous queries, maintain persisted complaint authority from PostgreSQL when `complaint_id` is supplied, and guarantee zero direct database writes by the AI edit tool.

### 2. What Was Implemented
- **AI Schemas & Validation Allowlist (`backend/app/schemas/ai.py` & `backend/app/schemas/__init__.py`):**
  - Defined `EDITABLE_COMPLAINT_FIELDS` allowlist containing the 13 valid domain fields.
  - `ComplaintChanges`: Model containing all 13 fields as optional, representing strictly the delta.
  - `AIComplaintEditExtraction`: Schema for Groq structured output capturing `changes`, `needs_clarification`, `clarification_reason`, and `is_edit_request`.
  - `AIComplaintEditRequest`: Validates incoming edit requests (`edit_instruction`, optional `complaint_id`, optional `current_complaint`).
  - `ComplaintFieldDiff`: Represents a single field's diff (`field_name`, `current_value`, `proposed_value`, `is_changed`).
  - `AIComplaintEditProposal`: Comprehensive response schema with `complaint_id`, `original_complaint`, `merged_complaint`, `changes_summary`, `diff`, `recalculated_risk`, and `needs_clarification`.
- **System Prompts (`backend/app/ai/prompts.py`):**
  - Created `EDIT_EXTRACTION_SYSTEM_PROMPT`: Enforces strict minimal change extraction, anti-hallucination, mandatory omission of unmentioned fields, explicit flagging of ambiguous inputs without inventing values, and updating descriptions when clinical facts are provided.
- **LangGraph Conditional StateGraph (`backend/app/ai/complaint_graph.py`):**
  - Implemented `complaint_edit_graph` with 5 nodes:
    1. `extract_edit_changes`: Invokes Groq with `AIComplaintEditExtraction` structured schema.
    2. `validate_normalize_changes`: Filters keys against `EDITABLE_COMPLAINT_FIELDS`, normalizes numeric quantities, trims strings, and sets `should_proceed`.
    3. `merge_changes`: Overlays validated changes onto the authoritative baseline complaint.
    4. `reassess_risk`: Re-runs risk assessment using the merged complaint facts via `assess_complaint_risk`.
    5. `build_edit_proposal`: Constructs the field-by-field diff and response payload.
  - Implemented conditional router `route_after_edit_validation`: If `should_proceed` is False (ambiguous, non-edit, or no valid changes), it bypasses `merge_changes` and `reassess_risk` entirely, routing directly to `build_edit_proposal` with safe clarification feedback.
- **FastAPI AI Route (`backend/app/api/routes/ai.py`):**
  - Mounted `POST /api/ai/complaint-edit`.
  - Validates `complaint_id` UUID format if provided.
  - Enforces **Persisted Record Authority**: Queries PostgreSQL directly via SQLAlchemy to load the authoritative record if `complaint_id` is supplied. Falls back to client form payload for unsaved drafts.
  - Guarantees 0 database writes (100% read-only / advisory).
  - Handles missing API keys (503), unprocessable entities (422), and missing records (404).
- **Automated Test Suite (`backend/test_ai_edit_verification.py`):**
  - Implemented 7 automated verification tests:
    - Test 1 (Single field edit): Verified 25 -> 50 quantity update with all other fields preserved.
    - Test 2 (Multi-field edit): Verified simultaneous customer and quantity update.
    - Test 3 (Ambiguity handling): Verified "Change the quantity" halted at validation, skipped merge/risk, and returned clarification.
    - Test 4 (Anti-hallucination & allowlist): Verified unmentioned fields were not extracted and allowlist discarded illegal fields.
    - Test 5 (Risk reassessment): Verified severe clinical event triggered Critical severity and Urgent priority.
    - Test 6 (Database safety): Confirmed PostgreSQL row count remained exactly 2 (delta = 0).
    - Test 7 (Persisted record authority): Verified UUID lookup, 404 for nonexistent UUID, and 422 for bad UUID.
  - Result: 7/7 tests passed.
- **Frontend State Management (`frontend/src/store/` & `frontend/src/services/api.ts`):**
  - `frontend/src/services/api.ts`: Added `runComplaintEdit(request: AIComplaintEditRequest)`.
  - `frontend/src/store/slices/aiSlice.ts`: Added `activeTab` ('intake' | 'edit'), `editInstruction`, `isEditing`, `editProposal`, `editError`, and reducers.
  - `frontend/src/store/slices/complaintSlice.ts`: Added `applyComplaintChanges` reducer to merge AI proposed changes into active form fields without wiping untouched data.
- **Frontend AI Assistant UI (`frontend/src/components/ai/AIAssistant.tsx` & `index.css`):**
  - Added tab switcher (`⚡ New Complaint Intake` vs `✏️ Edit / Correct Complaint`).
  - Implemented Active Context banner displaying currently loaded product, batch, quantity, and customer.
  - Added 4 quick edit sample chips for rapid testing.
  - Built Proposed Change Set Diff Table showing Field, Current Value, and Proposed Value with arrow indicators (➔).
  - Added Preservation Guarantee banner.
  - Added Recalculated Risk Assessment card showing updated severity, priority, reasoning, and QA next steps.
  - Added "📋 Apply Changes to Form" button with visual confirmation banner.
  - Production build: `tsc -b && vite build` compiled cleanly in 210ms with 0 errors.
- **Browser Automation Verification (Playwright MCP):**
  - Tested live end-to-end flow on `http://localhost:5173/`.
  - Populated sample complaint (Paracetamol 500 mg, B1234, 25 tablets).
  - Switched to Edit tab; verified Active Context banner.
  - Submitted live Groq edit prompt: *"Actually, 50 tablets were affected."*.
  - Verified diff table displayed `Quantity Affected: 25 ➔ 50`.
  - Verified recalculated risk assessment displayed.
  - Clicked "Apply Changes to Form"; verified left form field updated to 50 while all other fields remained intact.
  - Confirmed left form remained fully editable (typed into customer field).
  - Verified database row count remained exactly 2 (0 DB writes).
  - Captured visual screenshot artifact: `unit6_applied_to_form.png`.

### 3. What Was Intentionally NOT Implemented
- **No Unit 7 / Future Features:** No document extraction, OCR, PDF/DOCX parsing, CAPA, duplicate detection, RAG, auth, or Docker.
- **No Automatic Database Mutations by AI:** AI proposals remain strictly advisory; persistence boundary remains explicit Save/PATCH actions.

### 4. Verification & Testing Performed
- **Automated Backend Suite:** `backend/test_ai_edit_verification.py` passed 7/7 tests.
- **Frontend TypeScript & Build:** `tsc -b && vite build` passed cleanly with zero errors.
- **Browser Automation:** Playwright MCP completed end-to-end verification and captured screenshots.
- **Database Count:** PostgreSQL row count verified unchanged at 2.

### 5. Next Steps (Pending User Approval)
- Stop and await user review for Unit 6.

---

## [2026-09-16] - Unit 7: Document Extraction Tool & Deterministic Ingestion Pipeline

### 1. Objective
Implement the mandatory **Document Extraction Tool** from the assignment, enabling QA specialists to upload complaint documents in **PDF, DOCX, TXT, or EML** formats (up to **10 MB**).
Extract raw text streams in memory using deterministic Python libraries (without external OCR dependencies), orchestrate structured entity extraction and preliminary QA risk triage through a dedicated **LangGraph** workflow with **Groq LPU** inference, and present structured complaint proposals to the React frontend for human review.
Incorporate four user adjustments:
1. Deterministic file validation before Groq configuration check.
2. EML transmission header date treated as metadata (not automatically mapped to `complaint_date`).
3. PDF readability determined by whitespace/empty checks rather than arbitrary character cutoffs; legitimate short complaints pass through.
4. Non-destructive form merging on Apply (extracted null/missing fields never overwrite existing form values).
Guarantee absolute database write isolation (0 writes during extraction).

### 2. What Was Implemented
- **Dependencies (`backend/requirements.txt`):**
  - Added and pinned: `pypdf>=5.0.0`, `python-docx>=1.1.0`, `python-multipart>=0.0.18`.
- **In-Memory Deterministic Document Parser (`backend/app/ai/document_extractor.py`):**
  - Implemented `extract_text_from_document(filename: str, file_bytes: bytes) -> tuple[str, str, int]`:
    - Enforces allowed extensions: `{".pdf", ".docx", ".txt", ".eml"}`.
    - Rejects files exceeding 10 MB limit (`MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024`).
    - Uses `io.BytesIO` streams in memory (zero temporary disk files).
    - **PDF:** Uses `pypdf.PdfReader` to extract text page-by-page. If extracted text is completely empty or whitespace-only, raises `ValueError` with clear guidance: *"Could not extract readable text from this PDF. The file may be scanned/image-only."* Allows concise short complaints.
    - **DOCX:** Uses `docx.Document` to extract paragraph text and table cell text.
    - **TXT:** Decodes text using UTF-8 with Latin-1 fallback.
    - **EML:** Uses standard library `email.parser.BytesParser` to extract email body. Identifies the RFC 822 `Date` header as `[Email Transmission Date (Header Metadata): ...]`, preventing automatic mapping to observation date.
- **Pydantic Schemas (`backend/app/schemas/ai.py` & `backend/app/schemas/__init__.py`):**
  - `DocumentMetadata`: Captures `filename`, `format`, `size_bytes`, `extracted_characters`, and optional `warning`.
  - `AIDocumentExtractionResponse`: Comprehensive response payload containing `metadata`, `complaint` (`AIComplaintExtraction`), and `risk_assessment` (`AIRiskAssessment`).
- **Prompt Engineering (`backend/app/ai/prompts.py`):**
  - Updated `EXTRACTION_SYSTEM_PROMPT` to enforce that EML header `Date` is transmission metadata and must not be mapped to `complaint_date` unless explicitly supported in narrative text. Also explicitly instructed to set `complaint_source` to `"Email"` when reading from an email document.
- **LangGraph Workflow (`backend/app/ai/complaint_graph.py`):**
  - Implemented and compiled `document_extraction_graph` with 5 sequential nodes:
    1. `extract_document_text`: Ingests and validates extracted text stream.
    2. `extract_complaint_fields`: Invokes ChatGroq with `EXTRACTION_SYSTEM_PROMPT` and `AIComplaintExtraction` structured schema.
    3. `validate_normalize`: Normalizes field strings, trims whitespace, converts empty strings to None, and enforces non-negative integer quantity.
    4. `risk_assessment`: Invokes ChatGroq with `RISK_ASSESSMENT_PROMPT` to calculate preliminary severity, priority, reasoning, and QA next actions.
    5. `build_result`: Compiles `AIDocumentExtractionResponse` payload.
- **FastAPI AI Endpoint (`backend/app/api/routes/ai.py`):**
  - Mounted `POST /api/ai/document-extraction` accepting `file: UploadFile = File(...)`.
  - **Stage 1:** Deterministic validation: checks file extension (HTTP 400), checks 10 MB size limit (HTTP 413), checks 0-byte file (HTTP 422).
  - **Stage 2:** Deterministic in-memory text parsing: catches scanned PDF / empty text (HTTP 422).
  - **Stage 3:** Checks Groq configuration (HTTP 503 if unconfigured).
  - **Stage 4:** Executes `document_extraction_graph`. Zero database queries or writes.
  - Used modern non-deprecated HTTP status codes (`HTTP_413_CONTENT_TOO_LARGE` and `HTTP_422_UNPROCESSABLE_CONTENT`).
- **Automated Test Suite (`backend/test_document_extraction_verification.py`):**
  - Created and executed a 12-test automated suite:
    - Test 1: Realistic TXT complaint extraction.
    - Test 2: Standard PDF text extraction.
    - Test 3: DOCX document with paragraphs and tables.
    - Test 4: EML email document extraction.
    - Test 5: EML Date header metadata isolation (`complaint_date` remains null when observation date unstated).
    - Test 6: Short legitimate PDF complaint accepted (no arbitrary <5 char rule).
    - Test 7: Scanned / image-only PDF cleanly caught with HTTP 422 error alert.
    - Test 8: Empty (0-byte) file rejected with HTTP 422.
    - Test 9: Unsupported file extension (.jpg, .xlsx) rejected with HTTP 400.
    - Test 10: Oversized file (>10 MB) rejected with HTTP 413.
    - Test 11: Incomplete complaint preserves nulls without hallucinating.
    - Test 12: Database Write Isolation verified (row count remained exactly 2, delta = 0).
  - Result: 12/12 tests passed with exit code 0.
- **Frontend API & Redux State (`frontend/src/store/` & `frontend/src/services/api.ts`):**
  - `frontend/src/services/api.ts`: Added `runDocumentExtraction(file: File): Promise<AIDocumentExtractionResponse>`.
  - `frontend/src/store/slices/aiSlice.ts`: Added `documentStatus`, `documentProcessingStep`, `documentError`, `documentResult`, `selectedFileName`, `selectedFileSize`, and reducers.
  - `frontend/src/store/slices/complaintSlice.ts`: Updated `populateComplaintFields` reducer to enforce Adjustment 4 (non-destructive merging: null or empty extracted fields never overwrite existing non-empty values in the form).
- **Frontend AIAssistant UI (`frontend/src/components/ai/AIAssistant.tsx` & `index.css`):**
  - Implemented 3-tab layout: `⚡ Text Intake` | `📄 Document Upload` | `✏️ Edit / Correct`.
  - Built interactive Drag & Drop dropzone with format badges (.PDF, .DOCX, .TXT, .EML, Max 10 MB).
  - Added 3 quick sample document buttons (Paracetamol .txt, Metformin .eml, Scanned PDF error simulation).
  - Built Selected File Pill with file name, size, and remove button.
  - Built multi-step pipeline progress indicator (Uploading -> Extracting Text -> Analyzing -> Assessing Risk).
  - Built Document Metadata Banner showing file name, format, size, and character count.
  - Built Extracted Fields Cards with "Human Review Required" status pill.
  - Built Preliminary Risk Assessment card with severity, priority, reasoning, and QA next actions.
  - Built "📋 Apply to Complaint Form" button with visual feedback and non-destructive merge.
  - Production build: `tsc -b && vite build` compiled cleanly in 242ms with 0 errors.
- **Browser Automation Verification (Playwright MCP):**
  - Tested live end-to-end flow on `http://localhost:5173/`.
  - Verified 3-tab layout; switched to `📄 Document Upload`.
  - Pre-populated form fields (`complaint_source: Phone Call`, `manufacturing_date: 2026-01-15`, `batch_lot_number: BATCH-ORIGINAL-777`, `quantity_affected: 10`).
  - Extracted sample document (`paracetamol_report.txt`).
  - Verified extraction results and preliminary risk assessment (Medium/Medium).
  - Clicked "Apply to Complaint Form":
    - Verified `quantity_affected` updated to 25 and `product_name` updated to Paracetamol.
    - Verified `complaint_source` stayed "Phone Call" (preserved!).
    - Verified `manufacturing_date` stayed "2026-01-15" (preserved!).
  - Verified Scanned PDF error simulation: returned clean HTTP 422 with controlled alert banner.
  - Switched to `✏️ Edit / Correct` tab: verified Active Context seamlessly inherited the applied complaint.
  - Verified PostgreSQL row count remained exactly 2 (zero database writes).
  - Captured visual screenshot artifacts:
    - `unit7_document_extracted_results.png`
    - `unit7_applied_to_form.png`
    - `unit7_document_error_handling.png`

### 3. What Was Intentionally NOT Implemented
- **No Unit 8 / Future Features:** No production OCR (Tesseract / cloud vision), no CAPA, no duplicate detection, no RAG, no auth, no Docker.
- **No Automatic Database Mutations by AI:** AI extraction remains strictly advisory; human QA review required before persistence.

### 4. Verification & Testing Performed
- **Automated Backend Suite:** `backend/test_document_extraction_verification.py` passed 12/12 tests.
- **Regression Suites:**
  - `backend/test_crud_verification.py` passed 9/9 steps.
  - `backend/test_ai_verification.py` passed 7/7 tests.
  - `backend/test_ai_edit_verification.py` passed 7/7 tests.
- **Frontend TypeScript & Build:** `tsc -b && vite build` passed cleanly with 0 errors.
- **Browser Automation:** Playwright MCP completed full positive, negative, and non-destructive apply testing.
- **Database Safety:** PostgreSQL row count verified unchanged at 2 (delta = 0).

### 5. Next Steps (Pending User Approval)
- Unit 8: Final Product Readiness Audit and Polish.

---

## [2026-09-16] - Unit 8: Final Product Readiness Audit and Polish

### 1. Objective
Execute a rigorous 11-phase product-readiness audit across the entire AIVOA Customer Complaint Management System:
- Inspect all mandatory features (Manual Complaint Form, AI Text Complaint Intake, AI Complaint Edit, AI Document Extraction).
- Validate architecture, data layers, secret containment, error handling, and database write isolation.
- Preserve the 2 historical test records in Supabase PostgreSQL without deletion.
- Execute full regression testing across all 4 automated backend test suites and frontend build/lint pipelines.
- Conduct 3 complete end-to-end user workflows (Flow A: Text Intake, Flow B: Document Extraction, Flow C: Conversational AI Edit & In-Place PATCH) using Playwright MCP.
- Polish concrete UX/architecture gaps without rewriting working foundations or adding speculative features.

### 2. What Was Audited & Polished
- **Requirements Matrix (Phase 1):** Verified all 13 fields across Manual Form, AI Text Intake, AI Edit, and Document Extraction against the actual codebase. All requirements evaluated as **PASS**.
- **Architecture Audit (Phase 2):** Confirmed strict 3-tier boundary: Database Layer (PostgreSQL via SQLAlchemy) $\rightarrow$ Client Application Layer (Redux `complaintSlice`) $\rightarrow$ AI Proposal Layer (Redux `aiSlice` & LangGraph). Verified backend-only Groq execution.
- **AI Safety & Factuality Audit (Phase 3):** Verified `backend/app/ai/prompts.py` anti-hallucination rules, strict null preservation for unmentioned fields, EML header date metadata separation, and preliminary/advisory risk phrasing.
- **UI/UX Polish (Phase 4):**
  - Updated outdated header badge in `frontend/src/App.tsx` from `"Unit 5 • Groq + LangGraph AI"` to `"AI-Assisted QMS • Groq + LangGraph"`.
  - Implemented dynamic form submission switching in `frontend/src/components/complaint/ComplaintForm.tsx` and `frontend/src/services/api.ts`:
    - Added `updateComplaint(id, payload)` issuing `PATCH /api/complaints/{id}`.
    - Submit button dynamically displays `"Update Complaint (PATCH)"` when editing a saved complaint (`savedComplaintId` present) and updates record in place rather than creating accidental duplicates.
- **API & Error Handling Audit (Phase 5):**
  - Modernized Starlette status codes in `backend/app/api/routes/ai.py` from `status.HTTP_422_UNPROCESSABLE_ENTITY` to `status.HTTP_422_UNPROCESSABLE_CONTENT`.
- **Security Audit (Phase 6):** Confirmed `GROQ_API_KEY` is strictly server-side; zero mentions or leaks in `frontend/src/` or `dist/` bundles; `.env` git-ignored; in-memory document parsing via `io.BytesIO`.
- **Database Audit (Phase 7):**
  - Supabase PostgreSQL schema and UUID primary key generation verified.
  - Zero database writes verified across all AI endpoints (Delta = 0).
  - Preserved the two historical test records (`0c0ad145-37c5-496e-90fd-bcac619494a6` and `a1aea44b-bfe2-4085-b06a-b348f65d5a77`).
- **Regression Testing (Phase 8):**
  - `backend/test_crud_verification.py`: 9/9 passed.
  - `backend/test_ai_verification.py`: 7/7 passed.
  - `backend/test_ai_edit_verification.py`: 7/7 passed.
  - `backend/test_document_extraction_verification.py`: 12/12 passed.
  - Total automated test cases: 35/35 passed (100%).
  - `npm run build`: Compiled cleanly in 178ms with 0 errors.
  - `npm run lint`: Oxlint passed with 0 errors and 0 warnings.
- **Complete End-to-End Demo Flows (Phase 9):**
  - **FLOW A (Text AI Intake):** Ceftriaxone narrative $\rightarrow$ Groq structured extraction $\rightarrow$ form population $\rightarrow$ manual edit (`complaint_source: Healthcare Professional`) $\rightarrow$ Save Complaint $\rightarrow$ Created UUID: `58492821-383b-4d9a-ac5e-abb571637e0f`. Direct SQL verified.
  - **FLOW B (Document Extraction):** Uploaded `hospital_complaint.eml` $\rightarrow$ parsed Metformin 850 mg facts $\rightarrow$ isolated EML header date $\rightarrow$ applied to form $\rightarrow$ AI Edit corrected quantity from 30 to 45 $\rightarrow$ applied correction $\rightarrow$ Save Complaint $\rightarrow$ Created UUID: `851896e4-68d8-43a5-9d56-513ea0e950b0`. Direct SQL verified.
  - **FLOW C (Conversational AI Edit & PATCH):** Loaded active context (`851896e4-68d8-43a5-9d56-513ea0e950b0`) $\rightarrow$ issued instruction: *"Actually, 50 tablets were affected."* $\rightarrow$ AI proposed `Quantity Affected: 45 ➔ 50` $\rightarrow$ verified DB still held 45 (write isolation confirmed!) $\rightarrow$ applied diff to form $\rightarrow$ clicked `"Update Complaint (PATCH)"` $\rightarrow$ direct SQL confirmed record `851896e4-68d8-43a5-9d56-513ea0e950b0` updated in place to quantity 50, updating `updated_at` without row count change.
- **Database Row Count Evolution (Phase 10):**
  - Initial baseline count: 2 records.
  - Flow A saved: +1 record (total: 3).
  - Flow B saved: +1 record (total: 4).
  - Flow C edited & PATCHed: updated existing record in place (total remained: 4).

### 3. What Was Intentionally NOT Implemented
- Strict adherence to scope boundaries:
  - NO commit, NO push.
  - NO RAG, NO OCR production pipeline, NO CAPA module, NO duplicate detection, NO root cause module, NO completeness checker, NO authentication, NO analytics dashboard, NO notifications, NO deployment infrastructure.

### 4. Verification & Testing Performed
- **Automated Backend Suites:** 35/35 tests passed across all 4 test files.
- **Frontend Quality:** TypeScript compilation, Vite production bundling, and Oxlint passed with zero errors.
- **Browser Automation (Playwright MCP):** Executed Flows A, B, and C with full screenshot and DOM verification.
- **Database Queries:** Verified all CRUD operations directly against Supabase PostgreSQL.

### 5. Next Steps
- Deliver the final 13-point comprehensive report to the user.
- Await user review and instructions.

---

## [2026-09-16] - Submission UI Polish & Enterprise QMS Alignment

### 1. Objective
Execute a visual alignment pass on the frontend interface to match the enterprise pharmaceutical QMS visual reference without changing backend behavior, API contracts, LangGraph workflows, AI prompts, or database schemas.
Preserve all three existing workflows (`Text Intake`, `Document Upload`, `Edit / Correct`) while polishing the default view, typography, form hierarchy, section headings, and status badging.

### 2. What Was Implemented
- **Frontend Form Alignment (`frontend/src/components/complaint/ComplaintForm.tsx`):**
  - Updated card header to display "Log Customer Complaint" with subtitle "API & FDF Quality Assurance Module".
  - Added "Pending Triage" amber pill badge (dynamically switching to "Registered" once saved).
  - Renamed all fieldset legends to uppercase numbered sections:
    - `1. ORIGIN & CUSTOMER DETAILS`
    - `2. PRODUCT & BATCH IDENTIFICATION`
    - `3. COMPLAINT DETAILS`
    - `4. INITIAL ASSESSMENT & PRIORITY`
  - Updated input placeholders to `"Awaiting AI extraction..."`.
  - Added unit indicators (`kg / units`) on quantity field.
  - Added clear icons to primary action buttons (`↺ Reset Form`, `💾 Save Complaint`).
- **AI Assistant Header & Default View (`frontend/src/components/ai/AIAssistant.tsx`):**
  - Renamed right-side header to `"AI Complaint Intake Assistant"` with a `BETA` pill badge.
  - Enhanced the default `Text Intake` tab to incorporate the primary ingestion dropzone:
    - Clean drag & drop document intake area (`Drag & drop complaint document here or click to browse`).
    - Obvious visual `"OR"` separator.
    - Paste Complaint Text / Email narrative input with quick sample chips.
    - Green alert notice highlighting supported formats: `PDF, DOCX, TXT, EML • Max file size: 10MB`.
    - Animated extraction progress bar during LLM inference.
    - AI assistant intro card with robot avatar.
    - Bottom interactive query bar: `"Ask me anything about this complaint..."`.
  - Maintained all 3 tabs (`⚡ Text Intake`, `📄 Document Upload`, `✏️ Edit / Correct`) via clean accessible navigation.
- **Enterprise Pharmaceutical Design System (`frontend/src/index.css`):**
  - Standardized globally on Google `Inter` font.
  - Established crisp enterprise light theme matching reference screenshot (`#f8fafc` background, `#ffffff` containers, `#2563eb` primary buttons, `#e2e8f0` borders).
  - Responsive two-column grid on desktop screens ($\ge 1024\text{px}$) with smooth wrapping for smaller viewports.

### 3. What Was Intentionally NOT Implemented
- Zero change to backend Python code, FastAPI endpoints, or database models.
- Zero change to LangGraph StateGraph nodes or Groq prompts.
- Zero removal of existing features or workflows.
- No auto-populated fake data on initial page load.

### 4. Verification & Testing Performed
- **Automated Backend Suites:**
  - `backend/test_crud_verification.py`: Passed (9/9 steps, exit code 0).
  - `backend/test_ai_verification.py`: Passed (7/7 tests, exit code 0).
  - `backend/test_ai_edit_verification.py`: Passed (7/7 tests, exit code 0).
  - `backend/test_document_extraction_verification.py`: Passed (12/12 tests, exit code 0).
- **Frontend Code Quality:**
  - `npm run lint` (Oxlint): Passed with 0 errors and 0 warnings.
  - `npm run build` (Vite production build): Built in 173ms with 0 errors.
- **Playwright MCP Browser Verification:**
  - Navigated to `http://127.0.0.1:5173/` at 1440x900 resolution.
  - Verified clean landing state visually matching `input_file_0.png` with "Pending Triage" and "BETA" badges.
  - Verified Text Intake workflow: populated Paracetamol sample, ran live Groq extraction, verified progress bar and risk triage results.
  - Verified "Apply to Complaint Form": populated left form fields non-destructively.
  - Verified "Save Complaint": successfully created record in PostgreSQL (`2c224f66-d642-4647-94f1-80c4c2fbd033`), switching submit button to `"Update Complaint (PATCH)"`.
  - Verified zero-write isolation: AI extraction itself produced 0 database writes. Cleaned up test record to restore baseline count to 4.
  - Verified Document Upload and Edit / Correct tabs rendered cleanly and functioned properly.
  - Captured verification screenshots in artifacts directory.

### 5. Next Steps
- Await user confirmation before committing or pushing.


