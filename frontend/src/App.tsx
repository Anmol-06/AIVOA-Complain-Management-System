import React, { useState } from "react";
import { useAppDispatch, useAppSelector } from "./store/hooks";
import { setStatusMessage } from "./store/slices/appSlice";

export const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const { systemName, statusMessage, isInitialized } = useAppSelector(
    (state) => state.app
  );

  const [testCounter, setTestCounter] = useState(0);

  const handleTestDispatch = () => {
    const nextCount = testCounter + 1;
    setTestCounter(nextCount);
    dispatch(
      setStatusMessage(
        `Redux state verified at ${new Date().toLocaleTimeString()} (Dispatch Test #${nextCount})`
      )
    );
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="badge">Unit 1 • Architectural Foundation</div>
        <h1>{systemName}</h1>
        <p className="subtitle">
          AI-Powered Complaint Management for Pharmaceutical Manufacturing
        </p>
      </header>

      <main className="main-content">
        <div className="card">
          <h2>Foundation Status</h2>
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Frontend Layer</span>
              <span className="value success">React + TypeScript + Vite Active</span>
            </div>
            <div className="status-item">
              <span className="label">State Management</span>
              <span className="value success">
                {isInitialized ? "Redux Toolkit Connected" : "Disconnected"}
              </span>
            </div>
            <div className="status-item">
              <span className="label">Backend Layer</span>
              <span className="value neutral">
                FastAPI (Health Check: GET /api/health)
              </span>
            </div>
            <div className="status-item">
              <span className="label">AI & Workflow</span>
              <span className="value pending">
                LangGraph + Groq (Deferred to Future Units)
              </span>
            </div>
          </div>

          <div className="redux-verification">
            <h3>Redux Integration Test</h3>
            <p className="redux-message">{statusMessage}</p>
            <button
              id="test-redux-btn"
              className="primary-button"
              onClick={handleTestDispatch}
            >
              Test Redux Dispatch Action
            </button>
          </div>
        </div>

        <div className="card info-card">
          <h3>Architectural Boundaries (Unit 1 Scope)</h3>
          <ul className="info-list">
            <li>
              <strong>Redux Role:</strong> Manages the current client-side
              application state. PostgreSQL will provide persistent storage for saved
              complaint records.
            </li>
            <li>
              <strong>Security Rule:</strong> Groq API keys and database
              credentials remain strictly server-side in FastAPI.
            </li>
            <li>
              <strong>Minimalism:</strong> Complaint intake form, LangGraph workflow,
              and PostgreSQL schema are deliberately deferred to ensure focused,
              step-by-step verification.
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
};

export default App;
