# Architectural Decision Records (ADRs)

This document records the key architectural choices, rationales, and trade-offs made during the design and development of the **AIVOA Customer Complaint Management System**. 
Historical entries are preserved permanently.

---

## ADR-001: Technology Stack Selection
- **Date:** 2026-09-14
- **Status:** Accepted
- **Context:**
  The assignment requires building an AI-powered customer complaint management system for pharmaceutical manufacturing that can be demonstrated and explained cleanly during technical interviews.
- **Decision:**
  - **Frontend:** React 19 + TypeScript + Vite.
  - **State Management:** Redux Toolkit + React-Redux.
  - **Backend:** Python 3.14 + FastAPI + Uvicorn.
  - **AI Workflow:** LangGraph.
  - **LLM Provider:** Groq.
  - **Database:** PostgreSQL.
  - **Typography:** Google Inter font.
- **Consequences:**
  - Provides a modern, fast, type-safe development environment.
  - Fast feedback loop with Vite's instant Hot Module Replacement (HMR) and FastAPI's interactive OpenAPI documentation.
  - Clear architectural boundaries between UI, business logic, workflow orchestration, and persistence.

---

## ADR-002: Monorepo Project Structure with Independent Client and Server
- **Date:** 2026-09-14
- **Status:** Accepted
- **Context:**
  We need a manageable repository structure that cleanly separates frontend code from backend code without introducing complex monorepo tooling like Nx or Turborepo.
- **Decision:**
  Adopt a simple, clean root folder structure:
  - `frontend/`: Standalone Vite project for all client-side UI and state.
  - `backend/`: Standalone Python FastAPI application for APIs and orchestration.
  - `docs/`: Centralized living documentation for architecture, database, decisions, logs, and interview prep.
- **Consequences:**
  - Independent dependency manifests (`frontend/package.json` vs `backend/requirements.txt`).
  - No risk of leaking server packages or private environment variables into the frontend.
  - Easy to run and test either subsystem independently.

---

## ADR-003: Server-Side AI Credentials and Model-Agnostic Configuration
- **Date:** 2026-09-14
- **Status:** Accepted
- **Context:**
  AI operations require Groq API credentials. Hard-coding model identifiers or leaking keys to the frontend poses severe security risks and architectural rigidity.
- **Decision:**
  - React client never communicates directly with Groq. All AI interactions are proxied through FastAPI.
  - `GROQ_API_KEY` is maintained strictly in server-side environment variables (`backend/.env`).
  - `GROQ_MODEL` is parameterized via environment variables, defaulting to `llama-3.3-70b-versatile`, so models can be upgraded or swapped without modifying code.
- **Consequences:**
  - Zero exposure of private credentials in browser network inspectors or client bundles.
  - Flexible model experimentation without code refactoring.

---

## ADR-004: Strict Phasing and Dependency Discipline (Anti-Over-Engineering)
- **Date:** 2026-09-14
- **Status:** Accepted
- **Context:**
  A common failure mode in AI engineering projects is introducing speculative infrastructure (Celery, Redis, Docker, vector DBs, LangChain) before the core foundation is proven and understood.
- **Decision:**
  - Implement the system in small, verified units.
  - Unit 1 strictly sets up the foundational skeleton: frontend scaffolding, Redux Toolkit integration test, minimal FastAPI health endpoint, and environment templates.
  - Do NOT create placeholder/fake complaint APIs, AI routes, database models, or LangGraph files until their respective phases.
- **Consequences:**
  - The project remains explainable for beginners and interviewers.
  - Every added dependency has an immediate, verifiable justification.

---

## ADR-005: Client Application State vs. Persistent Records
- **Date:** 2026-09-14
- **Status:** Accepted
- **Context:**
  Clear definitions are required for where state resides to avoid confusing frontend in-memory data with persistent pharmaceutical compliance records.
- **Decision:**
  - **Redux Toolkit** manages the current client-side application state (active form entries, UI toggles, loading spinners, and transient QA edits).
  - **PostgreSQL** provides persistent storage for saved complaint records, ensuring durability and audit compliance across browser sessions.
- **Consequences:**
  - Eliminates ambiguity regarding the source of truth.
  - The frontend never pretends to be the database.

---

## ADR-006: PostgreSQL via Supabase as the Relational Database Engine
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  The pharmaceutical complaint management system requires a robust, ACID-compliant relational database. We need a modern, cloud-hosted PostgreSQL solution that is easy to provision and maintain for demonstrations without local database server overhead.
- **Decision:**
  Use PostgreSQL hosted via Supabase.
- **Consequences:**
  - Fully managed, high-performance PostgreSQL instance with connection pooling.
  - No direct client-side database access; all database access is mediated by FastAPI.
  - Compatible with standard PostgreSQL drivers (`psycopg2-binary`) and ORMs (`SQLAlchemy`).

---

## ADR-007: Database Access Exclusively through FastAPI via SQLAlchemy ORM
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  We must decide how data access is brokered between the React frontend and PostgreSQL.
- **Decision:**
  - React NEVER interacts with PostgreSQL or Supabase client libraries directly using privileged credentials.
  - All database interactions are routed through FastAPI using SQLAlchemy 2.x as the Object-Relational Mapper (ORM) and session manager (`get_db` dependency).
- **Consequences:**
  - Strict security boundary: database credentials remain hidden on the server.
  - Centralized data validation, access control, and transaction management in Python.

---

## ADR-008: Intentional Nullability and Realistic Data Hygiene
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  In real-world pharmaceutical manufacturing, complaints are often initially received with incomplete information (e.g., complainant does not know the batch lot number or manufacturing date). We must decide how to handle missing fields in the database schema.
- **Decision:**
  - All complaint intake fields are made nullable (`NULL`).
  - `NULL` strictly signifies that the data was unavailable or unprovided.
  - Never fabricate placeholder values like `"unknown"`, `"N/A"`, `0` for missing counts, or dummy dates.
- **Consequences:**
  - Preserves data integrity and prevents corrupting audit trails with fake data.
  - Downstream analytical queries can accurately distinguish between "zero defective units" and "quantity not reported".

---

## ADR-009: Non-Sequential UUID Primary Keys
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  Using sequential integer IDs (`1, 2, 3...`) exposes systems to enumeration attacks and conveys unnecessary information about intake volume.
- **Decision:**
  Use UUIDv4 as the primary key for the `complaints` table, generated automatically via `uuid.uuid4` in Python and `gen_random_uuid()` in PostgreSQL.
- **Important Invariant:**
  UUIDs provide non-sequential global uniqueness, but **do not provide authorization or access security**. Explicit user authorization checks must be enforced at the API layer.
- **Consequences:**
  - Eliminates predictable URL scanning.
  - Safe for distributed and concurrent record creation.

---

## ADR-010: Separation of Complaint Facts from AI-Derived Analytical Fields
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  We must decide whether to store AI risk assessments, root-cause hypotheses, and CAPA recommendations directly in the primary `complaints` table.
- **Decision:**
  Keep the initial `complaints` table strictly focused on **complaint facts** as submitted by the customer. AI-derived assessments will be stored in separate workflow/investigation structures in future units.
- **Consequences:**
  - Clean separation of concerns between raw intake evidence and AI-generated analytical suggestions.
  - Auditing is simplified: raw complaint data is immutable, while AI suggestions can be recalculated or refined by human QA operators.

---

## ADR-011: Initial Schema Generation via SQLAlchemy Metadata (Deferred Alembic Migrations)
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  Database schema management can be implemented using automated migration tools (Alembic) or programmatic creation (`Base.metadata.create_all`).
- **Decision:**
  Use `Base.metadata.create_all(bind=engine)` for this initial MVP schema. Defer Alembic migration scripts until subsequent units where schema alterations occur.
- **Consequences:**
  - Adheres strictly to the minimalism and anti-over-engineering principle.
  - Avoids introducing migration churn before the baseline schema is settled.

