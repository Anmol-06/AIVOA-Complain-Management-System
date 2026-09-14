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
