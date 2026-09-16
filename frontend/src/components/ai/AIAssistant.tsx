import React, { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import {
  setInputText,
  setAnalyzing,
  setAnalysisError,
  setAnalysisResult,
  clearAnalysis,
} from "../../store/slices/aiSlice";
import { populateComplaintFields } from "../../store/slices/complaintSlice";
import { runComplaintIntake } from "../../services/api";

const SAMPLE_COMPLAINTS = [
  {
    label: "Paracetamol (Full Details)",
    text: "ABC Pharma reported that Paracetamol 500 mg batch B1234 had broken tablets. 25 tablets were affected.",
  },
  {
    label: "Amoxicillin (Vial Discoloration)",
    text: "Dr. Evans at Mercy Hospital emailed on 2026-08-10 stating Amoxicillin 250 mg batch LOT-9981 has severe liquid discoloration and sediment. 10 vials affected.",
  },
  {
    label: "Missing Details (Null Safety)",
    text: "Customer reported broken tablets.",
  },
];

export const AIAssistant: React.FC = () => {
  const dispatch = useAppDispatch();
  const { inputText, isAnalyzing, error, analysisResult } = useAppSelector(
    (state) => state.ai
  );
  const [appliedNotice, setAppliedNotice] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) {
      dispatch(setAnalysisError("Please enter complaint text to analyze."));
      return;
    }

    setAppliedNotice(null);
    dispatch(setAnalyzing(true));

    try {
      const result = await runComplaintIntake(inputText);
      dispatch(setAnalysisResult(result));
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during AI analysis.";
      dispatch(setAnalysisError(msg));
    }
  };

  const handleApplyToForm = () => {
    if (!analysisResult) return;

    const { complaint, risk_assessment } = analysisResult;

    dispatch(
      populateComplaintFields({
        complaint_source: complaint.complaint_source ?? undefined,
        customer_name: complaint.customer_name ?? undefined,
        product_name: complaint.product_name ?? undefined,
        product_strength_grade: complaint.product_strength_grade ?? undefined,
        batch_lot_number: complaint.batch_lot_number ?? undefined,
        manufacturing_date: complaint.manufacturing_date ?? undefined,
        expiry_date: complaint.expiry_date ?? undefined,
        quantity_affected:
          complaint.quantity_affected !== null &&
          complaint.quantity_affected !== undefined
            ? complaint.quantity_affected
            : undefined,
        complaint_type: complaint.complaint_type ?? undefined,
        complaint_date: complaint.complaint_date ?? undefined,
        detailed_description: complaint.detailed_description ?? undefined,
        initial_severity: risk_assessment.initial_severity ?? undefined,
        priority: risk_assessment.priority ?? undefined,
      })
    );

    setAppliedNotice(
      "Extracted fields applied to the complaint form! Review the values on the left, make any necessary adjustments, and click 'Save Complaint' to persist to PostgreSQL."
    );
  };

  return (
    <div className="ai-assistant-card" aria-label="AI Complaint Intake Assistant">
      {/* Header */}
      <div className="assistant-header">
        <div className="ai-icon-bubble">⚡</div>
        <div>
          <h3>AI Complaint Intake Assistant</h3>
          <span className="badge-ai-active">LangGraph + Groq LPU</span>
        </div>
      </div>

      <div className="assistant-body">
        <p className="assistant-info">
          Paste an unstructured complaint email, phone transcript, or clinical note. 
          The LangGraph workflow will extract factual fields and propose initial QA risk triage.
        </p>

        {/* Quick Sample Prompts */}
        <div className="sample-prompts-container">
          <span className="sample-prompts-label">Quick test samples:</span>
          <div className="sample-chips">
            {SAMPLE_COMPLAINTS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                className="sample-chip-btn"
                onClick={() => {
                  dispatch(setInputText(sample.text));
                  setAppliedNotice(null);
                }}
                disabled={isAnalyzing}
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleAnalyze} className="ai-input-form">
          <div className="form-group">
            <label htmlFor="ai-narrative-input" className="form-label">
              Customer Complaint Narrative:
            </label>
            <textarea
              id="ai-narrative-input"
              className="ai-textarea"
              rows={4}
              placeholder="e.g. ABC Pharma reported that Paracetamol 500 mg batch B1234 had broken tablets. 25 tablets were affected."
              value={inputText}
              onChange={(e) => dispatch(setInputText(e.target.value))}
              disabled={isAnalyzing}
            />
          </div>

          <div className="ai-button-row">
            <button
              type="submit"
              className="btn btn-primary btn-ai"
              disabled={isAnalyzing || !inputText.trim()}
            >
              {isAnalyzing ? (
                <>
                  <span className="spinner" aria-hidden="true"></span>
                  Analyzing with Groq...
                </>
              ) : (
                <>⚡ Analyze Complaint</>
              )}
            </button>

            {(inputText || analysisResult || error) && (
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => {
                  dispatch(clearAnalysis());
                  setAppliedNotice(null);
                }}
                disabled={isAnalyzing}
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* Error Banner */}
        {error && (
          <div className="alert alert-error" role="alert">
            <span className="alert-icon">⚠️</span>
            <div>
              <strong>Analysis Error:</strong> {error}
            </div>
          </div>
        )}

        {/* Applied to Form Success Notice */}
        {appliedNotice && (
          <div className="alert alert-success" role="alert">
            <span className="alert-icon">✓</span>
            <div>{appliedNotice}</div>
          </div>
        )}

        {/* Analysis Results Display */}
        {analysisResult && (
          <div className="ai-results-container">
            <div className="results-header">
              <h4>Structured AI Extraction</h4>
              <span className="badge-preliminary">Human Review Required</span>
            </div>

            {/* Extracted Fields Summary Grid */}
            <div className="extracted-fields-grid">
              <div className="extracted-field-item">
                <span className="field-title">Product Name:</span>
                <span className="field-value">
                  {analysisResult.complaint.product_name || (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>

              <div className="extracted-field-item">
                <span className="field-title">Strength / Grade:</span>
                <span className="field-value">
                  {analysisResult.complaint.product_strength_grade || (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>

              <div className="extracted-field-item">
                <span className="field-title">Batch / Lot #:</span>
                <span className="field-value">
                  {analysisResult.complaint.batch_lot_number ? (
                    <code className="batch-code">
                      {analysisResult.complaint.batch_lot_number}
                    </code>
                  ) : (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>

              <div className="extracted-field-item">
                <span className="field-title">Quantity Affected:</span>
                <span className="field-value">
                  {analysisResult.complaint.quantity_affected !== null &&
                  analysisResult.complaint.quantity_affected !== undefined ? (
                    <strong>{analysisResult.complaint.quantity_affected}</strong>
                  ) : (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>

              <div className="extracted-field-item">
                <span className="field-title">Customer / Reporter:</span>
                <span className="field-value">
                  {analysisResult.complaint.customer_name || (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>

              <div className="extracted-field-item">
                <span className="field-title">Complaint Type:</span>
                <span className="field-value">
                  {analysisResult.complaint.complaint_type || (
                    <em className="text-muted">Not mentioned</em>
                  )}
                </span>
              </div>
            </div>

            {/* Risk Assessment Section */}
            <div className="risk-assessment-card">
              <div className="risk-header">
                <h5>Initial Risk Assessment & Triage</h5>
                <div className="risk-badges">
                  <span
                    className={`severity-badge severity-${(
                      analysisResult.risk_assessment.initial_severity || "medium"
                    ).toLowerCase()}`}
                  >
                    Severity: {analysisResult.risk_assessment.initial_severity || "Medium"}
                  </span>
                  <span
                    className={`priority-badge priority-${(
                      analysisResult.risk_assessment.priority || "medium"
                    ).toLowerCase()}`}
                  >
                    Priority: {analysisResult.risk_assessment.priority || "Medium"}
                  </span>
                </div>
              </div>

              <div className="risk-body">
                <div className="risk-reasoning">
                  <strong>Risk Rationale:</strong>
                  <p>{analysisResult.risk_assessment.risk_reasoning}</p>
                </div>

                {analysisResult.risk_assessment.recommended_next_actions.length >
                  0 && (
                  <div className="recommended-actions">
                    <strong>Recommended QA Next Steps:</strong>
                    <ul className="actions-list">
                      {analysisResult.risk_assessment.recommended_next_actions.map(
                        (action, i) => (
                          <li key={i}>{action}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Action to Apply Data to Left Form */}
            <div className="ai-apply-section">
              <button
                type="button"
                className="btn btn-success btn-apply"
                onClick={handleApplyToForm}
              >
                📋 Apply to Complaint Form (Review on Left)
              </button>
              <span className="apply-disclaimer">
                Clicking this will populate the editable form on the left. The complaint
                will NOT be saved to PostgreSQL until you click "Save Complaint".
              </span>
            </div>
          </div>
        )}

        {/* Governance Notice */}
        <div className="assistant-notice">
          <span className="notice-icon">🛡️</span>
          <span>
            <strong>Pharma QMS Safety Rule:</strong> AI recommendations do not write
            directly to the database. Human QA review and explicit form submission is required.
          </span>
        </div>
      </div>
    </div>
  );
};
