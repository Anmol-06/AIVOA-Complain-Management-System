import React, { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import {
  setActiveTab,
  setInputText,
  setAnalyzing,
  setAnalysisError,
  setAnalysisResult,
  clearAnalysis,
  setEditInstruction,
  setEditing,
  setEditError,
  setEditProposal,
  clearEdit,
} from "../../store/slices/aiSlice";
import { populateComplaintFields } from "../../store/slices/complaintSlice";
import { runComplaintIntake, runComplaintEdit } from "../../services/api";

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

const SAMPLE_EDITS = [
  {
    label: "Update Quantity (50 units)",
    text: "Actually, 50 tablets were affected.",
  },
  {
    label: "Update Customer & Quantity",
    text: "Change the customer name to XYZ Pharma and the affected quantity to 100.",
  },
  {
    label: "Ambiguity Test (Missing value)",
    text: "Change the quantity.",
  },
  {
    label: "Clinical Classification & Severity",
    text: "Update complaint classification to Adverse Event and detailed description: Patient experienced severe anaphylactic shock requiring emergency hospitalization.",
  },
];

export const AIAssistant: React.FC = () => {
  const dispatch = useAppDispatch();
  const {
    activeTab,
    inputText,
    isAnalyzing,
    error,
    analysisResult,
    editInstruction,
    isEditing,
    editError,
    editProposal,
  } = useAppSelector((state) => state.ai);

  const { formData, savedComplaintId } = useAppSelector(
    (state) => state.complaint
  );

  const [appliedNotice, setAppliedNotice] = useState<string | null>(null);

  // -------------------------------------------------------------------
  // INTAKE HANDLERS
  // -------------------------------------------------------------------
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

  const handleApplyIntakeToForm = () => {
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

  // -------------------------------------------------------------------
  // EDIT HANDLERS
  // -------------------------------------------------------------------
  const handleProposeEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editInstruction.trim()) {
      dispatch(setEditError("Please enter an edit instruction."));
      return;
    }

    setAppliedNotice(null);
    dispatch(setEditing(true));

    try {
      const proposal = await runComplaintEdit({
        complaint_id: savedComplaintId ?? undefined,
        current_complaint: formData,
        edit_instruction: editInstruction,
      });
      dispatch(setEditProposal(proposal));
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during AI complaint edit.";
      dispatch(setEditError(msg));
    }
  };

  const handleApplyEditChanges = () => {
    if (!editProposal || !editProposal.requested_changes) return;

    dispatch(populateComplaintFields(editProposal.requested_changes));

    if (editProposal.risk_assessment) {
      dispatch(
        populateComplaintFields({
          initial_severity:
            editProposal.risk_assessment.initial_severity ?? undefined,
          priority: editProposal.risk_assessment.priority ?? undefined,
        })
      );
    }

    setAppliedNotice(
      "Proposed changes applied to the complaint form! The form on the left has been updated and remains fully editable. Click 'Save Complaint' when you are ready to persist to PostgreSQL."
    );
  };

  const formatFieldName = (key: string): string => {
    return key
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const hasActiveContext =
    Boolean(formData.product_name) ||
    Boolean(formData.customer_name) ||
    Boolean(formData.batch_lot_number) ||
    formData.quantity_affected !== null;

  return (
    <div className="ai-assistant-card" aria-label="AI Complaint Assistant">
      {/* Header */}
      <div className="assistant-header">
        <div className="ai-icon-bubble">⚡</div>
        <div>
          <h3>AI Complaint Assistant</h3>
          <span className="badge-ai-active">LangGraph + Groq LPU</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="assistant-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          id="tab-intake"
          aria-selected={activeTab === "intake"}
          className={`tab-btn ${activeTab === "intake" ? "active" : ""}`}
          onClick={() => {
            dispatch(setActiveTab("intake"));
            setAppliedNotice(null);
          }}
        >
          ⚡ New Complaint Intake
        </button>
        <button
          type="button"
          role="tab"
          id="tab-edit"
          aria-selected={activeTab === "edit"}
          className={`tab-btn ${activeTab === "edit" ? "active" : ""}`}
          onClick={() => {
            dispatch(setActiveTab("edit"));
            setAppliedNotice(null);
          }}
        >
          ✏️ Edit / Correct Complaint
        </button>
      </div>

      <div className="assistant-body">
        {/* ============================================================= */}
        {/* TAB 1: NEW COMPLAINT INTAKE                                   */}
        {/* ============================================================= */}
        {activeTab === "intake" && (
          <div className="tab-pane">
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
                  id="btn-analyze-complaint"
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

            {/* Applied Notice */}
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

                {/* Risk Assessment Card */}
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

                {/* Apply Button */}
                <div className="ai-apply-section">
                  <button
                    type="button"
                    className="btn btn-success btn-apply"
                    id="btn-apply-to-form"
                    onClick={handleApplyIntakeToForm}
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
          </div>
        )}

        {/* ============================================================= */}
        {/* TAB 2: EDIT / CORRECT COMPLAINT                               */}
        {/* ============================================================= */}
        {activeTab === "edit" && (
          <div className="tab-pane">
            <p className="assistant-info">
              Provide natural-language corrections to the active complaint (e.g., <em>"Actually, 50 tablets were affected."</em>).
              The AI extracts <strong>only</strong> requested changes, recalculates risk, and lets you review the diff before applying.
            </p>

            {/* Active Complaint Context Banner */}
            <div className="active-context-banner">
              <span className="context-icon">ℹ️</span>
              <div className="context-details">
                <strong>Active Context:</strong>{" "}
                {hasActiveContext ? (
                  <span>
                    {formData.product_name || "Unspecified Product"} • Batch:{" "}
                    <code>{formData.batch_lot_number || "None"}</code> • Qty:{" "}
                    <strong>{formData.quantity_affected ?? "None"}</strong> • Customer:{" "}
                    {formData.customer_name || "None"}
                    {savedComplaintId && (
                      <span className="saved-id-tag"> (DB Record: {savedComplaintId.slice(0, 8)}...)</span>
                    )}
                  </span>
                ) : (
                  <span className="text-muted">
                    Intake form on left is currently empty. You can still propose edits, or fill the form first.
                  </span>
                )}
              </div>
            </div>

            {/* Quick Sample Edit Chips */}
            <div className="sample-prompts-container">
              <span className="sample-prompts-label">Quick edit samples:</span>
              <div className="sample-chips">
                {SAMPLE_EDITS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="sample-chip-btn"
                    onClick={() => {
                      dispatch(setEditInstruction(sample.text));
                      setAppliedNotice(null);
                    }}
                    disabled={isEditing}
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Edit Instruction Form */}
            <form onSubmit={handleProposeEdit} className="ai-input-form">
              <div className="form-group">
                <label htmlFor="ai-edit-input" className="form-label">
                  Correction / Edit Instruction:
                </label>
                <textarea
                  id="ai-edit-input"
                  className="ai-textarea"
                  rows={3}
                  placeholder="e.g. Actually, 50 tablets were affected. Or: Change customer name to XYZ Pharma."
                  value={editInstruction}
                  onChange={(e) => dispatch(setEditInstruction(e.target.value))}
                  disabled={isEditing}
                />
              </div>

              <div className="ai-button-row">
                <button
                  type="submit"
                  className="btn btn-primary btn-ai"
                  disabled={isEditing || !editInstruction.trim()}
                  id="btn-propose-changes"
                >
                  {isEditing ? (
                    <>
                      <span className="spinner" aria-hidden="true"></span>
                      Proposing Changes...
                    </>
                  ) : (
                    <>⚡ Propose Changes</>
                  )}
                </button>

                {(editInstruction || editProposal || editError) && (
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => {
                      dispatch(clearEdit());
                      setAppliedNotice(null);
                    }}
                    disabled={isEditing}
                  >
                    Clear
                  </button>
                )}
              </div>
            </form>

            {/* Error Banner */}
            {editError && (
              <div className="alert alert-error" role="alert">
                <span className="alert-icon">⚠️</span>
                <div>
                  <strong>Edit Error:</strong> {editError}
                </div>
              </div>
            )}

            {/* Clarification Needed Notice */}
            {editProposal?.needs_clarification && (
              <div className="alert alert-warning alert-clarification" role="alert" id="clarification-banner">
                <span className="alert-icon">⚠️</span>
                <div>
                  <strong>Clarification Needed:</strong>
                  <p>{editProposal.clarification_message || "The instruction is ambiguous or missing required parameters. Please specify exact values to update."}</p>
                  <small className="text-muted">
                    Safety Rule: The system did NOT modify or invent any values.
                  </small>
                </div>
              </div>
            )}

            {/* Applied Notice */}
            {appliedNotice && (
              <div className="alert alert-success" role="alert">
                <span className="alert-icon">✓</span>
                <div>{appliedNotice}</div>
              </div>
            )}

            {/* Proposed Edit Changes Diff */}
            {editProposal && !editProposal.needs_clarification && (
              <div className="ai-results-container" id="edit-proposal-container">
                <div className="results-header">
                  <h4>Proposed Change Set (Diff)</h4>
                  <span className="badge-preliminary">Human Review Required</span>
                </div>

                {/* Field Diffs Table */}
                <div className="changes-diff-card">
                  <div className="diff-header-row">
                    <span>Field</span>
                    <span>Current Value</span>
                    <span></span>
                    <span>Proposed Value</span>
                  </div>

                  {Object.entries(editProposal.requested_changes).length === 0 ? (
                    <div className="no-changes-note">No fields were modified.</div>
                  ) : (
                    Object.entries(editProposal.requested_changes).map(([field, newVal]) => {
                      const oldVal = editProposal.original_complaint[field];
                      return (
                        <div key={field} className="diff-item-row" id={`diff-row-${field}`}>
                          <span className="diff-field-name">{formatFieldName(field)}</span>
                          <span className="diff-old-val">
                            {oldVal !== null && oldVal !== undefined && oldVal !== "" ? (
                              String(oldVal)
                            ) : (
                              <em className="text-muted">Empty / Unset</em>
                            )}
                          </span>
                          <span className="diff-arrow">➔</span>
                          <span className="diff-new-val">
                            <strong>{String(newVal)}</strong>
                          </span>
                        </div>
                      );
                    })
                  )}

                  <div className="diff-preservation-note">
                    🛡️ <strong>Preservation Guarantee:</strong> All unmentioned complaint fields remain 100% unchanged.
                  </div>
                </div>

                {/* Recalculated Risk Assessment Section */}
                {editProposal.risk_assessment && (
                  <div className="risk-assessment-card">
                    <div className="risk-header">
                      <h5>Recalculated Risk Assessment & Triage</h5>
                      <div className="risk-badges">
                        <span
                          className={`severity-badge severity-${(
                            editProposal.risk_assessment.initial_severity || "medium"
                          ).toLowerCase()}`}
                        >
                          Severity: {editProposal.risk_assessment.initial_severity || "Medium"}
                        </span>
                        <span
                          className={`priority-badge priority-${(
                            editProposal.risk_assessment.priority || "medium"
                          ).toLowerCase()}`}
                        >
                          Priority: {editProposal.risk_assessment.priority || "Medium"}
                        </span>
                      </div>
                    </div>

                    <div className="risk-body">
                      <div className="risk-reasoning">
                        <strong>Updated Risk Rationale:</strong>
                        <p>{editProposal.risk_assessment.risk_reasoning}</p>
                      </div>

                      {editProposal.risk_assessment.recommended_next_actions.length > 0 && (
                        <div className="recommended-actions">
                          <strong>Recommended QA Next Steps:</strong>
                          <ul className="actions-list">
                            {editProposal.risk_assessment.recommended_next_actions.map(
                              (action, i) => (
                                <li key={i}>{action}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Apply Button */}
                <div className="ai-apply-section">
                  <button
                    type="button"
                    className="btn btn-success btn-apply"
                    id="btn-apply-changes"
                    onClick={handleApplyEditChanges}
                  >
                    📋 Apply Changes to Form (Review on Left)
                  </button>
                  <span className="apply-disclaimer">
                    Clicking this will update the editable form on the left. The changes
                    will NOT be written to PostgreSQL until you click "Save Complaint".
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Governance Notice */}
        <div className="assistant-notice">
          <span className="notice-icon">🛡️</span>
          <span>
            <strong>Pharma QMS Safety Rule:</strong> AI proposals never write directly to PostgreSQL.
            Applying changes updates the local form for human review; explicit saving commits to the database.
          </span>
        </div>
      </div>
    </div>
  );
};
