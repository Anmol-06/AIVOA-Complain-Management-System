# Interview Notes & Architectural Concepts

This document provides beginner-friendly explanations, key concepts, and interview questions with model answers for the technologies and architectural patterns introduced in each development unit.
Historical records in this document are strictly preserved.

---

## Unit 1: Foundation Concepts & Interview Preparation

### Question 1: What is the purpose of this application in pharmaceutical manufacturing?
**Answer:**
In pharmaceutical manufacturing, patient safety and regulatory compliance (like US FDA 21 CFR regulations and GMP standards) are paramount. When a defect, adverse event, packaging error, or product malfunction occurs, customer complaints must be documented, triaged by severity, investigated, and archived with a complete audit trail. 
This system provides an AI-assisted workflow for Quality Assurance (QA) professionals to capture complaints, extract structured data from unstructured reports, and standardize classifications—while ensuring humans retain final review and decision-making authority.

---

### Question 2: Why are the frontend and backend physically separated?
**Answer:**
We separate the React frontend from the FastAPI backend for three critical reasons:
1. **Security:** Browser code is public. Anyone can open DevTools and inspect JavaScript bundles or network requests. Keeping sensitive API keys (e.g., Groq API keys) and database credentials exclusively on the server guarantees they cannot be leaked to end-users.
2. **Specialization:** Python is the premier language for AI workflows (LangGraph, LLM integration, data manipulation), whereas React + TypeScript is the industry standard for rich, dynamic user interfaces.
3. **Independent Scalability & Maintenance:** The frontend static assets can be hosted on a CDN (e.g., Vercel, Cloudflare, S3), while the backend API runs independently on scalable compute servers.

---

### Question 3: Why choose Vite + TypeScript over Create React App (CRA) or plain JavaScript?
**Answer:**
- **Vite:** Modern build tool leveraging native ES Modules (ESM) and esbuild written in Go. Unlike legacy bundlers like Webpack (used by Create React App), Vite starts the development server in milliseconds and provides near-instantaneous Hot Module Replacement (HMR).
- **TypeScript:** Adds static type checking to JavaScript. In enterprise pharmaceutical systems, strong typing prevents runtime bugs (e.g., mismatched complaint IDs, missing required batch numbers, or incorrect API payloads) before code ever runs.

---

### Question 4: What is Redux Toolkit, and how does its role differ from PostgreSQL?
**Answer:**
- **Key Principle:** *Redux manages the current client-side application state, while PostgreSQL provides persistent storage for saved complaint records.*
- **Redux Toolkit (RTK):** Modern, opinionated Redux that simplifies state management by eliminating boilerplate. In the browser, Redux stores active user state: what the user is currently typing in the complaint form, which tab is active, whether an API request is loading, or draft QA suggestions. However, Redux data lives only in the browser's memory and is lost on a full page reload.
- **PostgreSQL:** An ACID-compliant relational database running on the server. It permanently stores validated, submitted complaint records, audit logs, and status transitions so they can be retrieved by any authorized user anytime.

---

### Question 5: Why did we build a minimal `appSlice` in Unit 1 instead of starting the complaint state immediately?
**Answer:**
Software engineering emphasizes **incremental verification**. Before building complex domain models (complaint forms, severity classifications, AI revisions), we must verify that the foundational plumbing (Redux store configuration, TypeScript hooks `useAppDispatch`/`useAppSelector`, and React context provider) functions flawlessly. 
Creating a small integration slice proves the infrastructure is sound without coupling future complaint models to premature assumptions.

---

### Question 6: Why FastAPI and Uvicorn for the backend?
**Answer:**
- **FastAPI:** A modern, high-performance Python web framework based on Starlette and Pydantic. It automatically validates incoming HTTP request bodies and produces interactive OpenAPI/Swagger documentation (`/docs`) out of the box.
- **Uvicorn:** A lightning-fast ASGI (Asynchronous Server Gateway Interface) web server implementation that runs asynchronous Python code using an event loop (`uvloop`), making it ideal for handling concurrent network requests and streaming AI responses.

---

### Question 7: What is Cross-Origin Resource Sharing (CORS), and why did we configure it?
**Answer:**
- By default, web browsers block web pages from making HTTP requests to a different origin (domain, protocol, or port) to prevent malicious cross-site scripting attacks.
- During development, our React frontend runs at `http://localhost:5173`, and our FastAPI backend runs at `http://localhost:8000`. Because the ports differ, the browser views them as different origins.
- We configured FastAPI's `CORSMiddleware` to explicitly permit requests from `http://localhost:5173`, allowing the frontend to call `/api/health` and future endpoints without browser security blocks.

---

### Question 8: Why configure `GROQ_MODEL` via environment variables instead of hardcoding it?
**Answer:**
Large Language Models evolve rapidly. If an LLM name like `llama-3.3-70b-versatile` were hardcoded in multiple Python files, upgrading to a newer or specialized model would require search-and-replace edits, regression testing, and code commits. 
By placing `GROQ_MODEL` in `.env`, we maintain **model agnosticism**; changing the model across the entire application takes only a single configuration update without modifying a line of code.

---

## Unit 2: Database Foundation & Schema Design Concepts

### Question 9: What is PostgreSQL, and why use it for pharmaceutical complaints?
**Answer:**
- **PostgreSQL** is an enterprise-grade, open-source object-relational database management system (ORDBMS).
- In pharmaceutical Quality Management Systems (QMS), complaints are formal records. PostgreSQL provides **ACID guarantees** (Atomicity, Consistency, Isolation, Durability). If a system crashes mid-transaction, records are never half-written or corrupted.
- It enforces strict data types, relations between products, batches, and complaint events, and dependable timestamps needed for quality investigation audit trails.

---

### Question 10: What are tables, rows, and primary keys? Why choose UUIDs?
**Answer:**
- **Table:** A structured collection of data organized into rows and columns (e.g., `complaints`).
- **Column:** A specific attribute or field with a defined data type (e.g., `product_name` is `TEXT`, `manufacturing_date` is `DATE`).
- **Row (Record):** A single distinct instance in the table representing one complaint event.
- **Primary Key:** A column (or set of columns) that uniquely identifies each individual row. No two rows can share the same primary key.
- **Why UUIDs over sequential integers (1, 2, 3...)?** Sequential IDs reveal business metrics (how many complaints are filed) and allow enumeration attacks (a user changing `/complaints/5` to `/complaints/6` in the URL). UUIDv4 generates a 128-bit cryptographically random identifier that cannot be predicted.
- **Crucial Security Note:** UUIDs provide non-sequential uniqueness, but they do **not** replace authentication or authorization. You still need proper API permission checks to ensure a user is allowed to view that UUID.

---

### Question 11: What does `NULL` mean in SQL, and why avoid placeholder values like "unknown" or 0?
**Answer:**
- In relational databases, **`NULL` represents the absence of a value**—meaning the data is unknown, unprovided, or not applicable.
- In pharmaceutical complaints, complainants frequently report an issue without knowing the lot number, manufacturing date, or exact affected quantity.
- If we put `"unknown"` in text columns, `0` in integer columns, or fake dates (`1970-01-01`), we pollute the dataset:
  - An affected quantity of `0` falsely suggests that zero units were impacted.
  - A fake date could distort shelf-life calculations and compliance deadlines.
- By using `NULL`, downstream systems and analytics can accurately identify missing data without ambiguity.

---

### Question 12: What is an ORM (SQLAlchemy), and why use it over raw SQL strings?
**Answer:**
- **ORM (Object-Relational Mapping):** A programming technique that allows developers to interact with relational databases using object-oriented code. In SQLAlchemy, Python classes map to database tables (`Complaint` class -> `complaints` table), and class instances represent rows.
- **Benefits:**
  - **Type Safety & Maintainability:** Schema changes are made in clean Python code rather than scattered across raw SQL queries.
  - **SQL Injection Prevention:** SQLAlchemy uses parameterized queries under the hood, protecting the application from malicious SQL injections.
  - **Developer Productivity:** Simplifies transactions, relationships, and session lifecycle management.

---

### Question 13: What is a database connection pool, and why is it important with Supabase?
**Answer:**
- Establishing a new TCP/TLS connection to a remote database server takes significant time (often 50–150ms).
- A **connection pool** keeps a set of active connections open in memory and reuses them across incoming HTTP requests.
- In `database.py`, we configure `pool_pre_ping=True` (which tests whether a connection is still alive before using it) and `pool_recycle=300` (which recycles idle connections every 5 minutes). This prevents stale connection errors commonly caused by cloud proxies or Supabase's transaction poolers closing inactive connections.

---

### Question 14: Why keep AI-derived fields (like risk assessment or CAPA) separate from the initial complaint table?
**Answer:**
- **Separation of Concerns:** A customer complaint is an external statement of fact (e.g., *"the pill bottle seal was broken"*). This evidence should remain clean and immutable.
- An AI-generated risk assessment or recommended Corrective and Preventive Action (CAPA) is an **analytical interpretation** produced by an LLM workflow.
- Keeping these in separate tables/structures allows AI recommendations to be versioned, re-evaluated with newer models, or revised by human QA operators without altering the historical customer report.

