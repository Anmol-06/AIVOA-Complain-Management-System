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

---

## ADR-012: Separation of Pydantic API Schemas and SQLAlchemy Database Models
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  When designing RESTful APIs with FastAPI and SQLAlchemy, a common design question is whether to use the same classes for data serialization/validation and database persistence, or decouple them.
- **Decision:**
  Decouple the data structures into two distinct layers:
  - **Pydantic Schemas (`backend/app/schemas/`):** Define the external API contract (`ComplaintCreate`, `ComplaintUpdate`, `ComplaintResponse`). Handle HTTP input validation, parsing, date coercion, and response shape.
  - **SQLAlchemy Models (`backend/app/db/models.py`):** Define table structures, database column constraints, primary keys, and transaction mapping in PostgreSQL.
- **Consequences:**
  - Clear separation of concerns between public API shape and internal database schema.
  - Prevents mass-assignment vulnerabilities: clients cannot manipulate internal columns (like `id` or `created_at`) on creation.
  - Flexibility to vary input vs output payloads independently (e.g., all fields optional on update, required fields on creation, read-only audit timestamps on response).

---

## ADR-013: Authoritative Database Record & Partial Updates via PATCH
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  When updating an existing pharmaceutical complaint, the client might only modify a single field (e.g. `quantity_affected` from 5 to 8). We must decide where the source of truth resides during an update, and how unsupplied fields are treated.
- **Decision:**
  - The PostgreSQL database record is strictly authoritative for existing complaints. The server loads the persistent record from the database before applying modifications.
  - `PATCH /api/complaints/{id}` uses Pydantic's `model_dump(exclude_unset=True)`. Only fields explicitly included in the request body are modified.
  - Unspecified fields are **never** overwritten with `None` or `NULL`.
- **Consequences:**
  - Completely eliminates accidental data erasure of existing complaint fields during updates.
  - Prevents race conditions or state desynchronization from client-side caches (such as Redux) assuming they own the authoritative complaint record.

---

## ADR-014: Redux Toolkit as Single Source of Truth for Complex Complaint Form State
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  The pharmaceutical complaint form has 13 domain fields organized across four sections, plus asynchronous submission state (saving, error, success message, saved ID). We had to choose between managing form inputs with local React state (`useState`) vs. centralized Redux Toolkit state (`complaintSlice`).
- **Decision:**
  Manage the complaint form state centrally inside Redux Toolkit via `complaintSlice.ts`:
  - `formData`: object with all 13 complaint fields.
  - `updateComplaintField`: single generic reducer updating one field at a time (`{ field, value }`).
  - `resetComplaintForm`: resets all form fields to initial empty state.
  - `isSaving`, `error`, `successMessage`, `savedComplaintId`: discrete UI workflow state.
- **Consequences:**
  - Form state is easily shareable across components (e.g., when the AI assistant in Unit 5 needs to auto-populate or review form fields).
  - Clean separation of UI rendering from state mutation logic.
  - Retains typed Redux hooks (`useAppDispatch`, `useAppSelector`) without prop-drilling.

---

## ADR-015: Client-Side Empty String Sanitization to SQL NULL
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  In HTML5 forms, empty or cleared inputs naturally evaluate to empty strings (`""`). Passing empty strings for optional dates (`manufacturing_date: ""`) causes PostgreSQL date parsing failures (`invalid input syntax for type date`). Passing empty strings for text fields pollutes the database with `""` instead of `NULL`.
- **Decision:**
  In `frontend/src/services/api.ts`, automatically sanitize all empty strings and whitespace-only strings to `null` before sending HTTP JSON payloads to FastAPI.
- **Consequences:**
  - Database maintains pristine data hygiene: missing data is stored strictly as SQL `NULL`.
  - Avoids false data validation errors on optional date and number fields.
  - Prevents subtle bugs in analytical queries filtering by `IS NULL`.

---

## ADR-016: Two-Column Pharma QMS Layout with Visual Placeholder for Future AI Assistant
- **Date:** 2026-09-15
- **Status:** Accepted
- **Context:**
  The target pharmaceutical UI requires a two-column workspace: a complaint entry form on the left and an AI Complaint Intake Assistant on the right. However, Unit 4 strictly excludes AI implementation.
- **Decision:**
  Build a responsive two-column grid layout where:
  - Left column: The complete, functional pharmaceutical complaint form (`ComplaintForm`).
  - Right column: A clean, minimal visual placeholder card explicitly stating that AI document extraction and natural-language intake will be implemented in Unit 5.
  - On smaller screens / viewports, the grid responsively stacks columns vertically.
- **Consequences:**
  - Establishes the final visual layout expected in pharmaceutical Quality Management Systems without introducing premature AI dependencies.
  - Clear UX boundaries between manual complaint intake and future automated AI capabilities.

---

## ADR-017: LangGraph Directed StateGraph for Multi-Node AI Intake Pipeline
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  Unstructured pharmaceutical complaints require multiple processing steps: extracting structured domain fields, validating and normalizing formats, performing preliminary risk triage, and building a structured response. We evaluated using a single monolithic prompt vs an autonomous ReAct agent vs a deterministic LangGraph StateGraph.
- **Decision:**
  Use LangGraph's `StateGraph` with explicit sequential nodes:
  `START -> extract_fields -> validate_normalize -> risk_assessment -> build_result -> END`.
- **Consequences:**
  - Decouples extraction from risk triage, improving model accuracy on both tasks.
  - Intermediate state is typed (`ComplaintGraphState`) and easily inspectable/testable.
  - Avoids unpredictable loops and tool-calling drift inherent in autonomous ReAct agents.

---

## ADR-018: Strict Anti-Hallucination and Null-Safety Policy
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  In pharmaceutical manufacturing, fabricating batch numbers, dates, customer names, or quantities can mislead quality investigations and violate regulatory audit standards.
- **Decision:**
  Enforce a strict anti-hallucination policy via system prompts and normalization:
  - The model is explicitly instructed to extract only facts directly stated in the text.
  - Unmentioned fields MUST be returned as `null` (None).
  - Normalization verifies string cleanliness, enforces integer typing for quantities, and prevents negative values.
- **Consequences:**
  - Incomplete complaints remain accurately incomplete without artificial placeholders.
  - Protects pharmaceutical data integrity.

---

## ADR-019: Human-in-the-Loop Review Boundary (No Direct Database Writes by AI)
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  We must decide whether the AI workflow should automatically save extracted complaints directly to PostgreSQL.
- **Decision:**
  The AI intake pipeline NEVER writes directly to PostgreSQL. It returns structured suggestions to the React frontend. The QA operator reviews the data, clicks "Apply to Complaint Form", edits any fields if needed, and explicitly submits the form to persist the record.
- **Consequences:**
  - Ensures compliance with pharmaceutical QMS standards (human accountability).
  - Eliminates the risk of prompt injections or hallucinations corrupting the database.

---

## ADR-020: Environment-Configured Groq Model Selection (Model Agnosticism)
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  AI model availability, versions, and performance evolve rapidly. Hard-coding a model name in Python files causes deprecation breakage.
- **Decision:**
  Configure the Groq model name exclusively through the server-side environment variable `GROQ_MODEL` in `backend/.env`. Do not hardcode defaults to any single model.
- **Consequences:**
  - Operations team can switch or upgrade models instantaneously without code redeployment.
  - Prevents breaking changes when providers retire model checkpoints.

---

## ADR-021: LangGraph Conditional StateGraph for Complaint Edits & Corrections
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  When a user supplies natural-language corrections (e.g. *"Actually, 50 tablets were affected."*), the AI workflow must extract only the changed fields, merge them with existing baseline facts, recalculate risk, and present a diff. However, if the user input is ambiguous (*"Change the quantity"* without a value), non-edit, or invalid, running merge and risk recalculation would produce corrupted or misleading proposals.
- **Decision:**
  Implement a dedicated conditional LangGraph `complaint_edit_graph`:
  - Nodes: `extract_edit_changes` -> `validate_normalize_changes` -> `merge_changes` -> `reassess_risk` -> `build_edit_proposal`.
  - Conditional Edge: `route_after_edit_validation` checks `should_proceed`. If the request is ambiguous, non-edit, or contains no valid changes, it bypasses `merge_changes` and `reassess_risk` entirely and routes directly to `build_edit_proposal` with `needs_clarification = True`.
- **Consequences:**
  - Prevents LLM hallucination of missing values.
  - Avoids wasteful risk inference on invalid or ambiguous prompts.
  - Provides deterministic, audit-friendly execution flows.

---

## ADR-022: Defense-in-Depth Backend Editable Field Allowlist (`EDITABLE_COMPLAINT_FIELDS`)
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  In LLM-driven editing workflows, prompt instructions alone cannot guarantee that an LLM will not hallucinate unexpected keys, attempt to mutate primary keys, or overwrite audit timestamps.
- **Decision:**
  Enforce a hardcoded, immutable allowlist in the backend validation layer:
  `EDITABLE_COMPLAINT_FIELDS = {'complaint_source', 'customer_name', 'product_name', 'product_strength', 'batch_lot_number', 'quantity_affected', 'manufacturing_date', 'expiry_date', 'complaint_type', 'complaint_date', 'detailed_description', 'initial_severity', 'priority'}`.
  Any key extracted by the LLM that is not in this set is silently discarded during validation.
- **Consequences:**
  - Complete protection against unexpected schema pollution or prompt injection attacks aiming to overwrite internal attributes (`id`, `created_at`, `updated_at`).
  - Strict type contracts between LLM output and internal domain models.

---

## ADR-023: Persisted Complaint Authority Over Client Cache
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  When editing an existing complaint with a `complaint_id`, the client sends its current form data, but client state could be stale due to network latency, concurrent edits by other QA personnel, or browser tab staleness.
- **Decision:**
  FastAPI queries PostgreSQL directly via SQLAlchemy to load the authoritative complaint record when `complaint_id` is supplied:
  - If found, the database row is converted to a dictionary and serves as the merge baseline.
  - If the UUID does not exist, an HTTP 404 is returned immediately.
  - Only for unsaved drafts (`complaint_id` is None/empty) does the server use the client's submitted form payload as the complaint context.
- **Consequences:**
  - Database integrity is prioritized: edits are always applied on top of ground-truth persisted facts.
  - Eliminates stale cache overwrites.

---

## ADR-024: Visual Diff Proposal Pattern & Redux-Only Application Boundary
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  When an AI tool suggests modifications to a pharmaceutical complaint, QA personnel must clearly understand what changed, what was preserved, and must maintain final control.
- **Decision:**
  - The AI edit endpoint returns an `AIComplaintEditProposal` containing a structured field-by-field diff (`field_name`, `current_value`, `proposed_value`, `is_changed`).
  - The UI displays an interactive comparison table highlighting modified values with arrow indicators (➔) and a Preservation Guarantee banner.
  - Clicking "Apply Changes to Form" dispatches an action to the client-side Redux store (`complaintSlice`) ONLY.
  - No database write occurs until the human operator explicitly clicks "Save Complaint" or invokes `PATCH /api/complaints/{id}`.
- **Consequences:**
  - Human QA specialists remain 100% in control of data persistence.
  - Absolute compliance with pharmaceutical GMP principles of accountability and auditability.

---

## ADR-025: In-Memory Deterministic File Parsers Over Production OCR for Document Extraction MVP
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  Unit 7 requires extracting complaint data from PDF, DOCX, TXT, and EML documents up to 10 MB. In production, scanned images or flattened PDFs require optical character recognition (OCR). However, OCR engines (like Tesseract or cloud vision APIs) introduce significant binary dependencies, latency, and operational complexity.
- **Decision:**
  - Use lightweight, deterministic, pure-Python parsers: `pypdf` for PDFs, `python-docx` for Word documents, standard library `email.parser.BytesParser` for EML files, and standard UTF-8/Latin-1 decoding for TXT.
  - Process all file streams in memory using `io.BytesIO` (zero temporary disk files).
  - If a PDF yields no readable text streams (e.g. image-only or scanned), return a controlled HTTP 422 with an explicit error message explaining that the file may be scanned/image-only.
- **Consequences:**
  - Zero heavyweight C-bindings or external OCR services required for the MVP.
  - Extremely fast in-memory execution.
  - Transparent error messaging when a user uploads an image-only document.

---

## ADR-026: Deterministic Validation Prior to Groq Configuration Check
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  If a user uploads an unsupported file format (.jpg, .xlsx), an oversized file (>10 MB), or an empty file (0 bytes), the application should reject it immediately regardless of whether Groq AI credentials are configured.
- **Decision:**
  Validate file extension, file size, and payload content *before* checking `GROQ_API_KEY`. The AI configuration is evaluated only when extracted text is ready to be dispatched to the LLM workflow.
- **Consequences:**
  - Fast fail: Invalid uploads are rejected with HTTP 400, 413, or 422 before consuming any AI workflow resources.
  - Independent subsystem testing: Document extraction parsing logic can be verified even in offline or unconfigured environments.

---

## ADR-027: EML Transmission Header Date Isolation
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  In email complaints (.eml), the RFC 822 `Date` header indicates when the email message was generated by the mail user agent. This timestamp is message transmission metadata, not necessarily the pharmaceutical observation or complaint date (e.g. an email sent on Monday regarding an issue observed the previous Thursday).
- **Decision:**
  - The EML parser prefixes the extracted text with `[Email Transmission Date (Header Metadata): ...]`.
  - The extraction prompt explicitly instructs the LLM that email header date is transmission metadata and must NOT be mapped to `complaint_date`.
  - `complaint_date` is populated only if the document narrative explicitly states when the complaint occurred or was received; otherwise, it remains `null`.
- **Consequences:**
  - Prevents inaccurate audit dates in pharmaceutical records.
  - Preserves distinction between network transmission metadata and clinical/quality observation facts.

---

## ADR-028: PDF Empty Text Stream Detection vs. Arbitrary Character Thresholds
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  An early draft considered rejecting PDFs with fewer than 5 characters. However, an arbitrary character threshold could reject legitimate, ultra-concise complaint notices (e.g., *"Batch B1 recalled"*).
- **Decision:**
  Define an unreadable PDF strictly as one where extracted text across all pages is completely empty or consists solely of whitespace. Genuine short text is allowed to proceed to the LangGraph extraction pipeline.
- **Consequences:**
  - Eliminates arbitrary cutoffs.
  - Accurately targets scanned, image-only, or blank PDFs while accepting concise complaints.

---

## ADR-029: Non-Destructive Form Merging on Document Apply
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  When a QA operator extracts a document and clicks "Apply to Complaint Form", the extracted document may have omitted optional fields (e.g., manufacturing date, expiry date, or complaint source). If the user had already entered values for those fields in the form, overwriting them with `null` would erase user data.
- **Decision:**
  In `complaintSlice.ts` (`populateComplaintFields`), apply non-destructive merging:
  - Only extracted fields containing a non-null, non-empty value update the corresponding Redux form field.
  - Extracted fields with `null` or empty strings leave existing form values untouched.
- **Consequences:**
  - Prevents accidental data loss during multi-stage document ingestion.
  - Complements the human-in-the-loop review principle by retaining user corrections.

---

## ADR-030: Dynamic Form Mode (POST vs. PATCH) for Persisted Complaints
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  In Units 4-7, the left complaint intake form exclusively submitted payloads via `POST /api/complaints`. When a QA specialist saved a complaint and subsequently performed conversational edits (Unit 6) or manual adjustments, re-clicking "Save Complaint" created an entirely new duplicate row in PostgreSQL with a new UUID. This broke the entity lifecycle and caused data duplication during conversational edit workflows.
- **Decision:**
  Wire the frontend form submission dynamically to `savedComplaintId` in `complaintSlice`:
  - If `savedComplaintId` is null, submit via `POST /api/complaints` and store the returned UUID in Redux.
  - If `savedComplaintId` is present, render the primary action button as `"Update Complaint (PATCH)"` and submit via `updateComplaint(id, payload)` issuing `PATCH /api/complaints/{id}`.
  - Update the status alert to indicate in-place PostgreSQL update confirmation.
- **Consequences:**
  - Full CRUD lifecycle integration: seamless transition from creation to in-place patch.
  - Eliminates accidental duplicate database records during iterative edit and refinement workflows.
  - Complies with REST semantics (POST for creation, PATCH for partial updates).

---

## ADR-031: Starlette HTTP 422 Status Code Modernization
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  FastAPI route handlers in `backend/app/api/routes/ai.py` used `status.HTTP_422_UNPROCESSABLE_ENTITY`. In newer Starlette and Python 3.14 environments, `HTTP_422_UNPROCESSABLE_ENTITY` triggers deprecation warnings in favor of RFC 9110 standard `status.HTTP_422_UNPROCESSABLE_CONTENT`.
- **Decision:**
  Update all occurrences of `status.HTTP_422_UNPROCESSABLE_ENTITY` across route handlers to `status.HTTP_422_UNPROCESSABLE_CONTENT`.
- **Consequences:**
  - Eliminates deprecation warnings during server startup and request handling.
  - Aligns with the latest HTTP standard specifications (RFC 9110).
  - Preserves exact numeric status code 422 for frontend and automated test clients.

---

## ADR-032: Submission UI Visual Polish & Enterprise QMS Alignment
- **Date:** 2026-09-16
- **Status:** Accepted
- **Context:**
  The project assignment specifies an enterprise two-column pharmaceutical QMS layout with specific section numbering, badge designations, and intake assistant layouts as illustrated in the reference UI. To maximize presentation quality for submission while preserving 100% of tested business logic and workflows, a visual alignment pass was required.
- **Decision:**
  1. Update visible right-side title from `"AI Complaint Assistant"` to `"AI Complaint Intake Assistant"` with a `BETA` pill badge.
  2. Maintain all 3 core workflows (`Text Intake`, `Document Upload`, `Edit / Correct`) via clean top tabs, while structuring the default `Text Intake` view to feature:
     - Top document drag-and-drop ingestion dropzone
     - Obvious visual `"OR"` divider
     - Clean text narrative/email input area with quick sample chips
     - Supported formats green notice card (`PDF, DOCX, TXT, EML • Max 10MB`)
     - Animated extraction progress bar and conversational assistant intro card
     - Bottom interactive query prompt (`"Ask me anything about this complaint..."`)
  3. Restructure left form headings to uppercase numbered sections (`1. ORIGIN & CUSTOMER DETAILS`, `2. PRODUCT & BATCH IDENTIFICATION`, `3. COMPLAINT DETAILS`, `4. INITIAL ASSESSMENT & PRIORITY`), add `"Awaiting AI extraction..."` placeholders, and add a `"Pending Triage"` pill badge.
  4. Transition global styling in `index.css` to an enterprise light pharmaceutical palette (`#f8fafc` canvas, `#ffffff` containers, `#2563eb` primary actions, `#e2e8f0` borders) using `Inter` typography.
  5. Strictly preserve all existing DOM element IDs, name attributes, Redux state shapes, and backend API contracts.
- **Consequences:**
  - Visuals closely match the target pharmaceutical QMS reference screenshot.
  - Zero disruption to existing Unit 1–8 functionality or automated test suites.
  - Clear and professional presentation for assignment submission and interview walkthroughs.


