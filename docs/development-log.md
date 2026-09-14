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




