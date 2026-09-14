import React from "react";
import { ComplaintForm } from "./components/complaint/ComplaintForm";

export const App: React.FC = () => {
  return (
    <div className="app-shell">
      {/* TOP NAVIGATION / QMS BRANDING */}
      <header className="navbar">
        <div className="nav-container">
          <div className="brand-group">
            <div className="brand-badge">AIVOA QMS</div>
            <div className="brand-titles">
              <h1>Customer Complaint Management System</h1>
              <span className="brand-subtitle">
                Pharmaceutical Manufacturing • Good Manufacturing Practice (GMP)
              </span>
            </div>
          </div>
          <div className="nav-meta">
            <span className="status-pill status-online">
              <span className="pulse-dot"></span>
              FastAPI + Supabase Connected
            </span>
            <span className="status-pill status-unit">Unit 4 • Intake Form</span>
          </div>
        </div>
      </header>

      {/* MAIN TWO-COLUMN WORKSPACE */}
      <main className="workspace-container">
        <div className="two-column-layout">
          {/* LEFT COLUMN: Full Complaint Intake Form */}
          <section className="column-left" aria-label="Complaint Intake Form">
            <ComplaintForm />
          </section>

          {/* RIGHT COLUMN: AI Intake Assistant Placeholder */}
          <aside
            className="column-right"
            aria-label="AI Complaint Intake Assistant"
          >
            <div className="assistant-placeholder-card">
              <div className="assistant-header">
                <div className="ai-icon-bubble">🤖</div>
                <div>
                  <h3>AI Intake Assistant</h3>
                  <span className="badge-coming-soon">Scheduled for Next Unit</span>
                </div>
              </div>

              <div className="assistant-body">
                <p className="assistant-info">
                  Automated document extraction, voice/audio transcription, and
                  natural-language intake triage are scheduled for the AI workflow unit.
                </p>

                <div className="placeholder-feature-box">
                  <div className="feature-icon">📄</div>
                  <div className="feature-text">
                    <strong>Document & Image OCR</strong>
                    <span>Extract batch numbers and complaint details from attached photos & PDFs</span>
                  </div>
                </div>

                <div className="placeholder-feature-box">
                  <div className="feature-icon">⚡</div>
                  <div className="feature-text">
                    <strong>LangGraph + Groq Workflow</strong>
                    <span>Automated categorization, severity triage & QA review assistance</span>
                  </div>
                </div>

                <div className="assistant-notice">
                  <span className="notice-icon">ℹ️</span>
                  <span>
                    Form inputs on the left are fully interactive and persist directly
                    to PostgreSQL via the FastAPI backend.
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default App;
