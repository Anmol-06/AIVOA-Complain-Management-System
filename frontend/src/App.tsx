import React from "react";
import { ComplaintForm } from "./components/complaint/ComplaintForm";
import { AIAssistant } from "./components/ai/AIAssistant";

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
            <span className="status-pill status-unit">AI-Assisted QMS • Groq + LangGraph</span>
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

          {/* RIGHT COLUMN: AI Complaint Intake Assistant */}
          <aside
            className="column-right"
            aria-label="AI Complaint Intake Assistant"
          >
            <AIAssistant />
          </aside>
        </div>
      </main>
    </div>
  );
};


export default App;
