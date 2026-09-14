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


