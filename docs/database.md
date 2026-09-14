# Database Architecture & Persistence Strategy

## Persistent Storage Overview
PostgreSQL serves as the primary relational database and persistent storage engine for the **AIVOA Customer Complaint Management System**.

### Core Persistence Principle
> **Redux manages the current client-side application state, while PostgreSQL provides persistent storage for saved complaint records.**

While Redux holds active form inputs and session-level UI state within the user's browser, PostgreSQL guarantees durability, consistency, and compliance for pharmaceutical complaint records across sessions and users.

---

## Role of PostgreSQL in Pharmaceutical Compliance
In pharmaceutical manufacturing, customer complaint records are subject to strict regulatory oversight (e.g., US FDA 21 CFR Part 211, Good Manufacturing Practice (GMP), and audit trail standards):
- **ACID Transactions:** Ensures complaint filings and updates either succeed entirely or roll back safely without data corruption.
- **Relational Integrity:** Links complaint records to batch numbers, product catalogs, customer data, and audit logs.
- **Audit Trails:** Preserves timestamps, original user entries, and historical revisions for regulatory audits.

---

## Schema Design Status: Deferred to Later Phase

> [!IMPORTANT]
> **Status:** Schema design is **deliberately deferred** to a future implementation unit.
> In accordance with the project's phased development strategy and dependency discipline, no database tables, migrations, ORM models, or fake database connections are implemented in Unit 1.

### Planned Schema Areas for Future Units
When complaint modeling begins in subsequent phases, the PostgreSQL schema will be formally specified to handle:
1. **Complaint Core Records:** Unique complaint identifiers, product brand/generic name, lot/batch number, date of receipt, and complainant details.
2. **Classification & Categorization:** Quality defect classifications (e.g., packaging defect, contamination, labeling error, sub-potency) and adverse event indicators.
3. **Investigation & Resolution:** QA findings, corrective and preventive actions (CAPA), root cause analysis, and resolution statuses.
4. **Audit History & AI Revisions:** Tracking human QA edits alongside AI-proposed structured updates, preserving a complete audit trail.
