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
  - Enforces ACID compliance, essential for pharmaceutical regulatory audits (e.g., FDA 21 CFR Part 11).

---

## Core Security and Architecture Principles

1. **Strict Secret Isolation:** Private API keys (`GROQ_API_KEY`) and database credentials remain exclusively on the server. The browser client never touches or receives secret keys.
2. **Model Agnosticism:** The LLM model name is configured via server environment variables, enabling zero-code model upgrades.
3. **Separation of Concerns:** Client UI state is decoupled from persistent database records.
4. **Human-in-the-Loop:** In pharmaceutical quality control, AI recommendations must be human-reviewed and confirmed before final regulatory filing.
