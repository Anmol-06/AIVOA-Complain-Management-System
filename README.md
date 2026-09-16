# AIVOA Customer Complaint Management System
### API & FDF Quality Assurance Module • Pharmaceutical Manufacturing

A modern, regulatory-compliant pharmaceutical customer complaint management application designed for Good Manufacturing Practice (GMP) quality assurance workflows. The platform pairs a structured, human-in-the-loop manual complaint form with an advanced **AI Complaint Intake Assistant** powered by **Groq LPU** inference and **LangGraph** orchestration.

---

## Key Highlights

- **Human-in-the-Loop QA Oversight:** In compliance with FDA 21 CFR Part 11 / EU GMP guidelines, AI models never write directly or autonomously to the database ($\Delta \text{DB Rows}_{\text{AI}} = 0$). All AI extractions and edits generate ephemeral proposals for human review before explicit persistence.
- **Strict Anti-Hallucination & Null Safety:** Prompts and validation schemas enforce that missing or unmentioned attributes remain `null`. Fabricating lot numbers, expiry dates, or defect categories is strictly disallowed.
- **Multi-Format Ingestion:** In-memory text extraction from **PDF**, **DOCX**, **TXT**, and **EML** (up to 10 MB) without heavyweight external OCR dependencies or temporary disk persistence.
- **Conversational Corrections & Diff Proposals:** Natural-language iterative edits (e.g., *"Actually, 50 tablets were affected"*) produce minimal field diffs and dynamic risk recalculations without touching unmodified fields.
- **Enterprise Pharmaceutical Aesthetics:** Standardized on Google Inter typography, accessible numbered QA section groupings, clean tabular alignment, and an enterprise light design system matching pharmaceutical QMS standards.

---

## Core Capabilities

### 1. GMP Complaint Intake Form
- **13 Standardized Complaint Fields** organized into four numbered sections:
  1. `ORIGIN & CUSTOMER DETAILS`: Complaint Source, Customer Name.
  2. `PRODUCT & BATCH IDENTIFICATION`: Product Name, Strength/Grade, Batch/Lot Number, Manufacturing Date, Expiry Date, Quantity Affected (with unit indicators).
  3. `COMPLAINT DETAILS`: Complaint Type (Packaging, Contamination, Discoloration, Labeling, etc.), Complaint Date, Detailed Description.
  4. `INITIAL ASSESSMENT & PRIORITY`: Severity (Low, Medium, High, Critical) and Priority (Low, Medium, High, Urgent).
- **Dynamic Entity Lifecycle:** Seamlessly transitions from creation (`POST /api/complaints`) to in-place patch (`PATCH /api/complaints/{id}`) when updating existing records.
- **Interactive Form Controls:** Reset Form, field-level error preservation, and instant visual status indicators (*Pending Triage* $\rightarrow$ *Registered*).

### 2. AI Complaint Intake Assistant (Text Stream)
- Ingests raw customer complaint narratives, clinical reports, or call transcripts.
- Executes a 4-node **LangGraph StateGraph** pipeline:
  `START` $\rightarrow$ `extract_fields` $\rightarrow$ `validate_normalize` $\rightarrow$ `risk_assessment` $\rightarrow$ `build_result` $\rightarrow$ `END`.
- Performs preliminary QA risk triage: proposes severity, priority, clinical risk reasoning, and actionable regulatory next steps.
- **Non-Destructive Form Merging:** Extracted values populate the active form on operator approval while preserving existing manual entries.

### 3. Multi-Format Document Extraction Pipeline
- In-memory parsing of digital documents:
  - **PDF:** Extracts digital text streams via `pypdf`; detects scanned/image-only PDFs and returns actionable HTTP 422 feedback.
  - **DOCX:** Reads paragraphs and structured table cells via `python-docx`.
  - **TXT:** Multi-encoding text decoding (UTF-8 with Latin-1 fallback).
  - **EML:** RFC 822 email parser isolating transmission date headers as metadata to avoid corrupting defect observation dates.
- Enforces strict 10 MB payload ceiling and format validation prior to AI invocation.

### 4. Conversational AI Edit & Correction Tool
- Processes natural language feedback on existing complaints (e.g., *"Change customer name to XYZ Pharma and mark priority as Urgent"*).
- Enforces a defense-in-depth backend allowlist (`EDITABLE_COMPLAINT_FIELDS`) preventing modification of system audit columns (`id`, `created_at`).
- **Persisted Record Authority:** Queries PostgreSQL directly when a `complaint_id` is supplied to ensure proposals are grounded in the authoritative system of record.
- Displays an interactive field-by-field diff table (`Field`, `Current Value`, `Proposed Value`, `Status`) and recalculated risk card.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 19 + Redux Frontend                       │
│    ┌───────────────────────────┐    ┌─────────────────────────────┐   │
│    │   Complaint Form (Left)   │    │  AI Intake Assistant (Right) │   │
│    │  - 4 Numbered Sections    │    │  - Text Intake Tab          │   │
│    │  - Full Validation        │    │  - Document Upload Tab      │   │
│    │  - Human Review / Edit    │    │  - Edit / Correct Tab       │   │
│    └─────────────┬─────────────┘    └──────────────┬──────────────┘   │
└──────────────────┼─────────────────────────────────┼───────────────────┘
                   │ POST / PATCH                    │ POST /ai/*
                   │ (On Explicit User Save)         │ (Ephemeral Proposals)
                   ▼                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Server                      │
│                                                                        │
│   ┌──────────────────────────┐         ┌───────────────────────────┐   │
│   │   CRUD / Route Layer     │         │   Document Extractor      │   │
│   │   - POST /api/complaints │         │   - pypdf (In-Memory)     │   │
│   │   - GET  /api/complaints │         │   - python-docx           │   │
│   │   - PATCH /api/compl...  │         │   - email.parser          │   │
│   └─────────────┬────────────┘         └─────────────┬─────────────┘   │
│                 │                                    │                 │
│                 │                                    ▼                 │
│                 │                      ┌───────────────────────────┐   │
│                 │                      │    LangGraph Workflows    │   │
│                 │                      │    - Structured Extraction│   │
│                 │                      │    - Normalization        │   │
│                 │                      │    - Risk Triage          │   │
│                 │                      └─────────────┬─────────────┘   │
│                 │                                    │                 │
│                 │                                    ▼                 │
│                 │                      ┌───────────────────────────┐   │
│                 │                      │     Groq LPU Engine       │   │
│                 │                      │     - ChatGroq (temp=0.0) │   │
│                 │                      └───────────────────────────┘   │
│                 ▼                                                      │
│   ┌──────────────────────────┐                                         │
│   │   SQLAlchemy 2.0 ORM     │                                         │
│   └─────────────┬────────────┘                                         │
└─────────────────┼──────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database (Supabase)                       │
│                   - Table: complaints (UUIDv4 Primary Key)             │
│                   - Strict Write Boundary: Human Actions Only          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── complaint_graph.py      # LangGraph StateGraph pipelines (Intake, Document, Edit)
│   │   │   ├── document_extractor.py   # In-memory PDF, DOCX, TXT, EML parser
│   │   │   ├── groq_client.py          # Server-side ChatGroq initialization & safety checks
│   │   │   └── prompts.py              # Strict anti-hallucination & risk triage system prompts
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── ai.py               # /api/ai/complaint-intake, /document-extraction, /complaint-edit
│   │   │       └── complaints.py       # Standard RESTful CRUD (/api/complaints)
│   │   ├── db/
│   │   │   ├── database.py             # SQLAlchemy session and engine management
│   │   │   └── models.py               # Complaint ORM model (UUID, 13 domain fields, timestamps)
│   │   ├── schemas/
│   │   │   ├── ai.py                   # Pydantic schemas for AI proposals, diffs, and risk models
│   │   │   └── complaint.py            # Pydantic schemas for ComplaintCreate, Update, and Response
│   │   └── main.py                     # FastAPI application factory, CORS, and router registry
│   ├── requirements.txt                # Pinned backend dependencies
│   ├── .env.example                    # Template for database & Groq credentials
│   └── test_*.py                       # 4 automated test suites (35 test cases, 100% pass)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ai/
│   │   │   │   └── AIAssistant.tsx     # 3-workflow AI assistant (Text, Document, Edit)
│   │   │   └── complaint/
│   │   │       └── ComplaintForm.tsx   # 4-section controlled complaint intake form
│   │   ├── services/
│   │   │   └── api.ts                  # Axios/fetch service with data sanitization & null safety
│   │   ├── store/
│   │   │   ├── slices/
│   │   │   │   ├── aiSlice.ts          # State for active proposals, tabs, and extraction progress
│   │   │   │   └── complaintSlice.ts   # Working form state and non-destructive merging
│   │   │   └── index.ts                # Redux Toolkit store configuration
│   │   ├── index.css                   # Enterprise pharmaceutical light design system
│   │   └── App.tsx                     # Two-column layout and system status indicators
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore                          # Clean ignore rules (excludes secrets, local docs, caches)
└── README.md                           # System overview & setup guide
```

---

## Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19 + TypeScript | Type safety across domain entities, robust ecosystem. |
| **State Management** | Redux Toolkit | Predictable state isolation between working form and AI proposals. |
| **Build & Styling** | Vite + Vanilla CSS (Inter font) | Instant HMR, zero Tailwind bloat, precise enterprise typography. |
| **Backend Framework** | FastAPI (Python 3.12+) | Async performance, automated OpenAPI docs, native Pydantic v2 validation. |
| **AI Orchestration** | LangGraph (StateGraph) | Deterministic state transitions, auditable multi-node execution, conditional branching. |
| **LLM Inference** | Groq LPU (`ChatGroq`) | Ultra-low latency, deterministic inference (`temperature=0.0`), structured output. |
| **Document Parsers** | `pypdf`, `python-docx`, standard `email` | Pure-Python, in-memory stream processing with zero external OCR runtime binaries. |
| **Database & ORM** | PostgreSQL (Supabase) + SQLAlchemy 2.0 | Acid transactions, indexed UUIDv4 keys, timezone-aware audit timestamps. |
| **Code Quality** | Oxlint, Pytest / Unittest | High-speed linting and comprehensive regression verification. |

---

## Quickstart & Local Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** and **npm**
- **Supabase / PostgreSQL** connection URI
- **Groq API Key** ([console.groq.com](https://console.groq.com/))

### 1. Backend Setup

```bash
# Navigate to repository root
cd AIVOA-Complain-Management-System

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your DATABASE_URL, GROQ_API_KEY, and GROQ_MODEL
```

Start the backend server:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

In a separate terminal:
```bash
cd frontend

# Install frontend dependencies
npm install

# Start the Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```
Open your browser at: `http://127.0.0.1:5173/`.

---

## Running Verification Tests

The repository includes four comprehensive automated test suites covering CRUD operations, AI text extraction, conversational editing, and multi-format document extraction:

```bash
# Activate virtual environment
source .venv/bin/activate

# 1. Verify CRUD operations and PostgreSQL persistence (9 steps)
python backend/test_crud_verification.py

# 2. Verify AI Text Intake, null-safety, and LangGraph workflow (7 tests)
PYTHONPATH=. python backend/test_ai_verification.py

# 3. Verify Conversational AI Edit, allowlists, and diff engine (7 tests)
PYTHONPATH=. python backend/test_ai_edit_verification.py

# 4. Verify Document Extraction for PDF, DOCX, TXT, and EML (12 tests)
PYTHONPATH=. python backend/test_document_extraction_verification.py

# 5. Verify Frontend Linter & Production Build
cd frontend
npm run lint
npm run build
```

---

## Regulatory Compliance & Governance

- **Zero Autonomous Writes:** AI endpoints operate strictly in server RAM and return draft proposals. No SQL mutations (`INSERT`, `UPDATE`, `DELETE`) are ever triggered by AI endpoints.
- **Server-Side Secret Isolation:** `GROQ_API_KEY` is loaded exclusively inside `backend/app/ai/groq_client.py`. No API keys or tokens are ever exposed to client bundles.
- **Data Preservation Guarantee:** Applying AI proposals merges only validated fields; unmentioned existing user input is never overwritten with nulls.
- **Audit-Ready Timestamps:** All database records maintain immutable `created_at` and auto-advancing `updated_at` timezone-aware timestamps.
