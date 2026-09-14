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
