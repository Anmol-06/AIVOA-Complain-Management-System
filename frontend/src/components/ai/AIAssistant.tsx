import React, { useState, useRef } from "react";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import {
  setActiveTab,
  setInputText,
  setAnalyzing,
  setAnalysisError,
  setAnalysisResult,
  clearAnalysis,
  setSelectedFile,
  setDocumentStatus,
  setDocumentProcessingStep,
  setDocumentError,
  setDocumentResult,
  clearDocument,
  setEditInstruction,
  setEditing,
  setEditError,
  setEditProposal,
  clearEdit,
} from "../../store/slices/aiSlice";
import { populateComplaintFields } from "../../store/slices/complaintSlice";
import {
  runComplaintIntake,
  runComplaintEdit,
  runDocumentExtraction,
} from "../../services/api";

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

const SAMPLE_DOCUMENTS = [
  {
    label: "Paracetamol (.txt)",
    filename: "paracetamol_report.txt",
    type: "text/plain",
    content:
      "ABC Pharma reported that 25 tablets of Paracetamol 500 mg from batch B1234 were found broken. The complaint was received on 12 September 2026.",
  },
  {
    label: "Metformin Notice (.eml)",
    filename: "hospital_complaint.eml",
    type: "message/rfc822",
    content:
      "From: dr_alan@bletchley.org\nTo: quality@aivoa-pharma.com\nSubject: Defective Batch MET-2026\nDate: Mon, 15 Sep 2026 10:00:00 +0000\n\nDr. Alan Turing at Bletchley Hospital reported 30 tablets of Metformin 850 mg batch MET-2026 had foreign particles.",
  },
  {
    label: "Scanned / Blank PDF (Simulate Error)",
    filename: "scanned_doc.pdf",
    type: "application/pdf",
    content:
      "%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >> endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer << /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF",
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
    selectedFileName,
    selectedFileSize,
    documentStatus,
    documentProcessingStep,
    documentError,
    documentResult,
    editInstruction,
    isEditing,
    editError,
    editProposal,
  } = useAppSelector((state) => state.ai);

  const { formData, savedComplaintId } = useAppSelector(
    (state) => state.complaint
  );

  const [appliedNotice, setAppliedNotice] = useState<string | null>(null);
  const [selectedFileObj, setSelectedFileObj] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  // DOCUMENT EXTRACTION HANDLERS
  // -------------------------------------------------------------------
  const handleFileSelect = (file: File) => {
    setSelectedFileObj(file);
    dispatch(setSelectedFile({ name: file.name, size: file.size }));
    setAppliedNotice(null);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSampleDocument = (sample: (typeof SAMPLE_DOCUMENTS)[0]) => {
    const blob = new Blob([sample.content], { type: sample.type });
    const file = new File([blob], sample.filename, { type: sample.type });
    handleFileSelect(file);
  };

  const handleExtractDocument = async () => {
    if (!selectedFileObj) {
      dispatch(
        setDocumentError(
          "Please select or drop a complaint document (.pdf, .docx, .txt, .eml) first."
        )
      );
      return;
    }

    setAppliedNotice(null);
    dispatch(setDocumentStatus("uploading"));
    dispatch(setDocumentProcessingStep("Uploading document (multipart/form-data)..."));

    // Meaningful pipeline step transitions
    const stepTimer1 = setTimeout(() => {
      dispatch(setDocumentStatus("extracting_text"));
      dispatch(setDocumentProcessingStep("Extracting document text streams..."));
    }, 400);

    const stepTimer2 = setTimeout(() => {
      dispatch(setDocumentStatus("analyzing"));
      dispatch(setDocumentProcessingStep("Analyzing complaint via LangGraph & Groq..."));
    }, 1200);

    const stepTimer3 = setTimeout(() => {
      dispatch(setDocumentStatus("assessing_risk"));
      dispatch(setDocumentProcessingStep("Assessing preliminary QA risk & triage..."));
    }, 2000);

    try {
      const result = await runDocumentExtraction(selectedFileObj);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      dispatch(setDocumentResult(result));
    } catch (err: unknown) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to extract document.";
      dispatch(setDocumentError(msg));
    }
  };

  const handleApplyDocumentToForm = () => {
    if (!documentResult) return;

    const { complaint, risk_assessment } = documentResult;

    // Adjustment 4: populateComplaintFields skips null/missing values,
    // so existing form fields are never overwritten with null.
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
      "Document extraction applied to complaint form! Existing fields were preserved and the form remains fully editable. Click 'Save Complaint' when you are ready to persist to PostgreSQL."
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
      const result = await runComplaintEdit({
        complaint_id: savedComplaintId || undefined,
        current_complaint: formData as unknown as Record<string, unknown>,
        edit_instruction: editInstruction.trim(),
      });
      dispatch(setEditProposal(result));
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during AI edit.";
      dispatch(setEditError(msg));
    }
  };

  const handleApplyEditToForm = () => {
    if (!editProposal || !editProposal.requested_changes) return;

    const changes = editProposal.requested_changes;
    const partialForm: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(changes)) {
      if (value !== undefined && value !== null) {
        partialForm[key] = value;
      }
    }

    if (editProposal.risk_assessment?.initial_severity) {
      partialForm.initial_severity = editProposal.risk_assessment.initial_severity;
    }
    if (editProposal.risk_assessment?.priority) {
      partialForm.priority = editProposal.risk_assessment.priority;
    }

    dispatch(populateComplaintFields(partialForm));

    setAppliedNotice(
      "Proposed changes applied to the complaint form! The form on the left has been updated and remains fully editable. Click 'Save Complaint' when you are ready to persist to PostgreSQL."
    );
  };

  // Format file size helper
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Active context summary for Edit tab
  const hasActiveComplaint =
    formData.product_name ||
    formData.batch_lot_number ||
    formData.customer_name ||
    formData.quantity_affected !== null;

  const isDocumentProcessing =
    documentStatus === "uploading" ||
    documentStatus === "extracting_text" ||
    documentStatus === "analyzing" ||
    documentStatus === "assessing_risk";

  return (
    <div className="ai-assistant-card" aria-label="AI Complaint Intake Assistant">
      {/* Header */}
      <div className="assistant-header">
        <div className="ai-header-title-group">
          <span className="ai-sparkle-icon" aria-hidden="true">✨</span>
          <div className="ai-title-wrapper">
            <h3 className="assistant-title">AI Complaint Intake Assistant</h3>
            <span className="badge-ai-model">LangGraph + Groq LPU</span>
          </div>
        </div>
        <span className="badge-beta">BETA</span>
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
          ⚡ Text Intake
        </button>
        <button
          type="button"
          role="tab"
          id="tab-document"
          aria-selected={activeTab === "document"}
          className={`tab-btn ${activeTab === "document" ? "active" : ""}`}
          onClick={() => {
            dispatch(setActiveTab("document"));
            setAppliedNotice(null);
          }}
        >
          📄 Document Upload
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
          ✏️ Edit / Correct
        </button>
      </div>

      <div className="assistant-body">
        {/* Hidden native file input shared for document triggers */}
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept=".pdf,.docx,.txt,.eml"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelect(e.target.files[0]);
              dispatch(setActiveTab("document"));
            }
          }}
        />

        {/* ============================================================= */}
        {/* TAB 1: NEW COMPLAINT TEXT INTAKE                              */}
        {/* ============================================================= */}
        {activeTab === "intake" && (
          <div className="tab-pane">
            {/* Top Quick Document Ingestion Trigger Box */}
            <div
              className={`intake-dropzone ${isDragOver ? "drag-over" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => {
                handleDrop(e);
                dispatch(setActiveTab("document"));
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="dropzone-cloud-icon">☁️</div>
              <div className="dropzone-prompt">
                <strong>Drag &amp; drop complaint document here</strong>
                <span> or <span className="inline-browse-link">click to browse</span></span>
              </div>
            </div>

            {/* OR Separator */}
            <div className="or-divider">
              <span>OR</span>
            </div>

            {/* Paste Complaint Text / Email Section */}
            <form onSubmit={handleAnalyze} className="ai-input-form">
              <div className="paste-text-section">
                <div className="section-label-row">
                  <span className="doc-icon">📄</span>
                  <label htmlFor="ai-narrative-input" className="paste-text-title">
                    Paste Complaint Text / Email
                  </label>
                </div>

                {/* Quick Sample Prompts */}
                <div className="sample-prompts-container">
                  <span className="sample-prompts-label">Quick samples:</span>
                  <div className="sample-chips">
                    {SAMPLE_COMPLAINTS.map((sample, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="chip-btn"
                        onClick={() => {
                          dispatch(setInputText(sample.text));
                          setAppliedNotice(null);
                        }}
                        title="Click to populate sample narrative"
                      >
                        {sample.label}
                      </button>
                    ))}
                  </div>
                </div>

                <textarea
                  id="ai-narrative-input"
                  rows={4}
                  className="ai-textarea"
                  placeholder="Paste complaint email, clinical report, or phone transcript here..."
                  value={inputText}
                  onChange={(e) => dispatch(setInputText(e.target.value))}
                  disabled={isAnalyzing}
                />
              </div>

              <div className="ai-actions-bar">
                <button
                  type="submit"
                  id="btn-analyze-complaint"
                  className="btn-ai-primary"
                  disabled={isAnalyzing || !inputText.trim()}
                >
                  {isAnalyzing ? (
                    <>
                      <span className="spinner-ai" aria-hidden="true" />
                      Extracting &amp; Triaging with Groq...
                    </>
                  ) : (
                    "⚡ Extract & Assess Risk"
                  )}
                </button>
                <button
                  type="button"
                  className="btn-ai-secondary"
                  onClick={() => dispatch(clearAnalysis())}
                  disabled={isAnalyzing || !inputText}
                >
                  Clear
                </button>
              </div>
            </form>

            {/* Supported Formats Green Notice Card */}
            <div className="supported-formats-card">
              <span className="info-circle-icon">ⓘ</span>
              <div className="formats-content">
                <strong>Supported formats: PDF, DOCX, TXT, EML</strong>
                <span>Max file size: 10MB</span>
              </div>
            </div>

            {/* Extraction Progress Box */}
            {isAnalyzing && (
              <div className="extraction-progress-box" role="status">
                <div className="progress-header-row">
                  <span className="progress-title-label">EXTRACTION PROGRESS</span>
                  <span className="progress-pct-badge">Analyzing...</span>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill progress-animated"></div>
                </div>
                <p className="progress-subtext">
                  Analyzing document content and extracting key details... Please wait, this may take a few moments.
                </p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="ai-error-alert" role="alert">
                <strong>⚠️ Analysis Error:</strong> {error}
              </div>
            )}

            {/* Applied Confirmation Banner */}
            {appliedNotice && (
              <div className="ai-applied-banner" role="alert">
                <span className="banner-check">✓</span>
                <span>{appliedNotice}</span>
              </div>
            )}

            {/* AI Assistant Intro Card (When Idle) */}
            {!analysisResult && !isAnalyzing && (
              <div className="ai-intro-section">
                <div className="assistant-section-header">
                  <span className="section-small-title">AI ASSISTANT</span>
                </div>
                <div className="assistant-callout-card">
                  <div className="bot-icon-badge">🤖</div>
                  <p className="callout-text">
                    Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you.
                  </p>
                </div>
              </div>
            )}

            {/* Extraction Results */}
            {analysisResult && (
              <div className="ai-results-panel">
                <div className="results-header">
                  <h4>Extracted Complaint Information</h4>
                  <span className="badge-review">Human Review Required</span>
                </div>

                <div className="extracted-fields-grid">
                  <div className="field-card">
                    <span className="field-card-label">Product Name</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.product_name || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Dosage Strength</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.product_strength_grade || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Batch / Lot Number</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.batch_lot_number ? (
                        <code>{analysisResult.complaint.batch_lot_number}</code>
                      ) : (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Quantity Affected</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.quantity_affected !== null &&
                      analysisResult.complaint.quantity_affected !== undefined ? (
                        <strong>{analysisResult.complaint.quantity_affected}</strong>
                      ) : (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Customer / Reporter</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.customer_name || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Defect Category</span>
                    <span className="field-card-value">
                      {analysisResult.complaint.complaint_type || (
                        <em className="missing-val">Not categorized</em>
                      )}
                    </span>
                  </div>
                </div>

                {/* Risk Assessment Box */}
                <div className="risk-assessment-card">
                  <div className="risk-header">
                    <h5>Preliminary Risk Assessment & Triage</h5>
                    <div className="risk-badges">
                      <span
                        className={`badge-severity badge-${analysisResult.risk_assessment.initial_severity?.toLowerCase() || "medium"}`}
                      >
                        Severity: {analysisResult.risk_assessment.initial_severity || "Medium"}
                      </span>
                      <span
                        className={`badge-priority badge-${analysisResult.risk_assessment.priority?.toLowerCase() || "medium"}`}
                      >
                        Priority: {analysisResult.risk_assessment.priority || "Medium"}
                      </span>
                    </div>
                  </div>

                  <div className="risk-content">
                    <strong>Risk Rationale:</strong>
                    <p>{analysisResult.risk_assessment.risk_reasoning}</p>

                    {analysisResult.risk_assessment.recommended_next_actions?.length > 0 && (
                      <>
                        <strong>Recommended QA Actions:</strong>
                        <ul className="qa-action-list">
                          {analysisResult.risk_assessment.recommended_next_actions.map(
                            (action, idx) => (
                              <li key={idx}>{action}</li>
                            )
                          )}
                        </ul>
                      </>
                    )}
                  </div>
                </div>

                {/* Apply Button */}
                <div className="apply-actions">
                  <button
                    type="button"
                    id="btn-apply-to-form"
                    className="btn-apply-changes"
                    onClick={handleApplyIntakeToForm}
                  >
                    📋 Apply to Complaint Form (Review on Left)
                  </button>
                  <p className="apply-disclaimer">
                    Applying suggestions updates the local form for review. Data will NOT be saved to PostgreSQL until you click "Save Complaint".
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================= */}
        {/* TAB 2: DOCUMENT EXTRACTION (UNIT 7)                           */}
        {/* ============================================================= */}
        {activeTab === "document" && (
          <div className="tab-pane">
            <p className="assistant-info">
              Upload a customer complaint document (PDF, DOCX, TXT, or EML). 
              Deterministic Python parsers extract text streams, then LangGraph + Groq extract structured fields and perform preliminary QA risk triage.
            </p>

            {/* Quick Sample Document Buttons */}
            <div className="sample-prompts-container">
              <span className="sample-prompts-label">Quick sample documents:</span>
              <div className="sample-chips">
                {SAMPLE_DOCUMENTS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="chip-btn"
                    onClick={() => handleLoadSampleDocument(sample)}
                    title={`Click to stage ${sample.filename}`}
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Hidden native file input */}
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: "none" }}
              accept=".pdf,.docx,.txt,.eml"
              onChange={handleFileInputChange}
            />

            {/* Drag and Drop Zone */}
            <div
              className={`document-dropzone ${isDragOver ? "drag-over" : ""} ${selectedFileName ? "has-file" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="dropzone-icon">📄</div>
              <div className="dropzone-text">
                <strong>Drag & drop complaint document here</strong>
                <span>or click to browse files</span>
              </div>
              <div className="dropzone-formats">
                <span className="format-badge">.PDF</span>
                <span className="format-badge">.DOCX</span>
                <span className="format-badge">.TXT</span>
                <span className="format-badge">.EML</span>
                <span className="size-badge">Max 10 MB</span>
              </div>
            </div>

            {/* Selected File Pill */}
            {selectedFileName && (
              <div className="selected-file-pill">
                <div className="file-info-group">
                  <span className="file-icon">📎</span>
                  <div className="file-name-size">
                    <span className="file-name">{selectedFileName}</span>
                    <span className="file-size">
                      {selectedFileSize !== null ? formatFileSize(selectedFileSize) : ""}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-remove-file"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFileObj(null);
                    dispatch(clearDocument());
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  title="Remove selected file"
                  aria-label="Remove file"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Action Buttons */}
            <div className="ai-actions-bar" style={{ marginTop: "1rem" }}>
              <button
                type="button"
                id="btn-extract-document"
                className="btn-ai-primary"
                onClick={handleExtractDocument}
                disabled={isDocumentProcessing || !selectedFileName}
              >
                {isDocumentProcessing ? (
                  <>
                    <span className="spinner-ai" aria-hidden="true" />
                    Processing Document...
                  </>
                ) : (
                  "⚡ Extract Complaint Data"
                )}
              </button>
              <button
                type="button"
                className="btn-ai-secondary"
                onClick={() => {
                  setSelectedFileObj(null);
                  dispatch(clearDocument());
                  if (fileInputRef.current) fileInputRef.current.value = "";
                  setAppliedNotice(null);
                }}
                disabled={isDocumentProcessing || (!selectedFileName && !documentResult)}
              >
                Clear
              </button>
            </div>

            {/* Processing Timeline Indicator */}
            {isDocumentProcessing && (
              <div className="pipeline-progress-box" role="status">
                <div className="pipeline-spinner-row">
                  <span className="spinner-ai" />
                  <strong>{documentProcessingStep || "Processing..."}</strong>
                </div>
                <div className="pipeline-steps">
                  <div className={`step-item ${documentStatus === "uploading" ? "active" : "done"}`}>
                    1. Uploading
                  </div>
                  <div
                    className={`step-item ${
                      documentStatus === "extracting_text"
                        ? "active"
                        : documentStatus === "uploading"
                        ? "pending"
                        : "done"
                    }`}
                  >
                    2. Parsing Text
                  </div>
                  <div
                    className={`step-item ${
                      documentStatus === "analyzing"
                        ? "active"
                        : documentStatus === "assessing_risk"
                        ? "done"
                        : "pending"
                    }`}
                  >
                    3. AI Extraction
                  </div>
                  <div
                    className={`step-item ${
                      documentStatus === "assessing_risk"
                        ? "active"
                        : "pending"
                    }`}
                  >
                    4. Risk Triage
                  </div>
                </div>
              </div>
            )}

            {/* Document Error Alert */}
            {documentError && (
              <div className="ai-error-alert" role="alert" style={{ marginTop: "1rem" }}>
                <strong>⚠️ Document Extraction Error:</strong> {documentError}
              </div>
            )}

            {/* Applied Confirmation Banner */}
            {appliedNotice && (
              <div className="ai-applied-banner" role="alert" style={{ marginTop: "1rem" }}>
                <span className="banner-check">✓</span>
                <span>{appliedNotice}</span>
              </div>
            )}

            {/* Document Extraction Results */}
            {documentResult && (
              <div className="ai-results-panel" style={{ marginTop: "1rem" }}>
                {/* Document Metadata Banner */}
                <div className="doc-metadata-banner">
                  <div className="meta-item">
                    <span className="meta-label">File Name:</span>
                    <strong className="meta-val">{documentResult.document_metadata.filename}</strong>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Format:</span>
                    <span className="meta-badge">{documentResult.document_metadata.file_type}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Size:</span>
                    <span className="meta-val">
                      {formatFileSize(documentResult.document_metadata.file_size_bytes)}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Extracted Text:</span>
                    <span className="meta-val">
                      {documentResult.document_metadata.char_count} chars
                    </span>
                  </div>
                </div>

                <div className="results-header" style={{ marginTop: "0.75rem" }}>
                  <h4>Extracted Complaint Information</h4>
                  <span className="badge-review">Human Review Required</span>
                </div>

                <div className="extracted-fields-grid">
                  <div className="field-card">
                    <span className="field-card-label">Product Name</span>
                    <span className="field-card-value">
                      {documentResult.complaint.product_name || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Dosage Strength</span>
                    <span className="field-card-value">
                      {documentResult.complaint.product_strength_grade || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Batch / Lot Number</span>
                    <span className="field-card-value">
                      {documentResult.complaint.batch_lot_number ? (
                        <code>{documentResult.complaint.batch_lot_number}</code>
                      ) : (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Quantity Affected</span>
                    <span className="field-card-value">
                      {documentResult.complaint.quantity_affected !== null &&
                      documentResult.complaint.quantity_affected !== undefined ? (
                        <strong>{documentResult.complaint.quantity_affected}</strong>
                      ) : (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Customer / Reporter</span>
                    <span className="field-card-value">
                      {documentResult.complaint.customer_name || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Source Channel</span>
                    <span className="field-card-value">
                      {documentResult.complaint.complaint_source || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Complaint Date</span>
                    <span className="field-card-value">
                      {documentResult.complaint.complaint_date || (
                        <em className="missing-val">Not mentioned</em>
                      )}
                    </span>
                  </div>
                  <div className="field-card">
                    <span className="field-card-label">Defect Category</span>
                    <span className="field-card-value">
                      {documentResult.complaint.complaint_type || (
                        <em className="missing-val">Not categorized</em>
                      )}
                    </span>
                  </div>
                </div>

                {/* Risk Assessment Box */}
                <div className="risk-assessment-card">
                  <div className="risk-header">
                    <h5>Preliminary Risk Assessment & Triage</h5>
                    <div className="risk-badges">
                      <span
                        className={`badge-severity badge-${
                          documentResult.risk_assessment.initial_severity?.toLowerCase() || "medium"
                        }`}
                      >
                        Severity: {documentResult.risk_assessment.initial_severity || "Medium"}
                      </span>
                      <span
                        className={`badge-priority badge-${
                          documentResult.risk_assessment.priority?.toLowerCase() || "medium"
                        }`}
                      >
                        Priority: {documentResult.risk_assessment.priority || "Medium"}
                      </span>
                    </div>
                  </div>

                  <div className="risk-content">
                    <strong>Risk Rationale:</strong>
                    <p>{documentResult.risk_assessment.risk_reasoning}</p>

                    {documentResult.risk_assessment.recommended_next_actions?.length > 0 && (
                      <>
                        <strong>Recommended QA Actions:</strong>
                        <ul className="qa-action-list">
                          {documentResult.risk_assessment.recommended_next_actions.map(
                            (action, idx) => (
                              <li key={idx}>{action}</li>
                            )
                          )}
                        </ul>
                      </>
                    )}
                  </div>
                </div>

                {/* Apply Button */}
                <div className="apply-actions">
                  <button
                    type="button"
                    id="btn-apply-document-to-form"
                    className="btn-apply-changes"
                    onClick={handleApplyDocumentToForm}
                  >
                    📋 Apply to Complaint Form (Review on Left)
                  </button>
                  <p className="apply-disclaimer">
                    Applying suggestions updates the local form for review. Data will NOT be saved to PostgreSQL until you click "Save Complaint".
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================= */}
        {/* TAB 3: CONVERSATIONAL COMPLAINT EDIT                          */}
        {/* ============================================================= */}
        {activeTab === "edit" && (
          <div className="tab-pane">
            <p className="assistant-info">
              Provide natural-language corrections to the active complaint (e.g.,{" "}
              <em>"Actually, 50 tablets were affected."</em>). The AI extracts{" "}
              <strong>only</strong> requested changes, recalculates risk, and lets you review the diff before applying.
            </p>

            {/* Active Complaint Context Summary */}
            <div className="active-context-banner">
              <span className="context-icon">ℹ️</span>
              <div className="context-details">
                <strong>Active Context:</strong>{" "}
                {hasActiveComplaint ? (
                  <span>
                    {formData.product_name || "Untitled Product"} • Batch:{" "}
                    <code>{formData.batch_lot_number || "None"}</code> • Qty:{" "}
                    <strong>{formData.quantity_affected ?? "Unknown"}</strong> • Customer:{" "}
                    {formData.customer_name || "Unknown"}
                  </span>
                ) : (
                  <em>No complaint loaded yet. Fill the form on the left or extract a document first.</em>
                )}
              </div>
            </div>

            {/* Quick Sample Edit Prompts */}
            <div className="sample-prompts-container">
              <span className="sample-prompts-label">Quick edit samples:</span>
              <div className="sample-chips">
                {SAMPLE_EDITS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      dispatch(setEditInstruction(sample.text));
                      setAppliedNotice(null);
                    }}
                    title="Click to populate edit instruction"
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Edit Instruction Form */}
            <form onSubmit={handleProposeEdit} className="ai-input-form">
              <div className="ai-form-group">
                <label htmlFor="ai-edit-input" className="ai-label">
                  Correction / Edit Instruction:
                </label>
                <textarea
                  id="ai-edit-input"
                  rows={3}
                  className="ai-textarea"
                  placeholder="e.g. Actually, 50 tablets were affected. Or: Change customer name to XYZ Pharma."
                  value={editInstruction}
                  onChange={(e) => dispatch(setEditInstruction(e.target.value))}
                  disabled={isEditing}
                />
              </div>

              <div className="ai-actions-bar">
                <button
                  type="submit"
                  id="btn-propose-edit"
                  className="btn-ai-primary"
                  disabled={isEditing || !editInstruction.trim()}
                >
                  {isEditing ? (
                    <>
                      <span className="spinner-ai" aria-hidden="true" />
                      Proposing Changes...
                    </>
                  ) : (
                    "⚡ Propose Changes"
                  )}
                </button>
                <button
                  type="button"
                  className="btn-ai-secondary"
                  onClick={() => dispatch(clearEdit())}
                  disabled={isEditing || !editInstruction}
                >
                  Clear
                </button>
              </div>
            </form>

            {/* Edit Error State */}
            {editError && (
              <div className="ai-error-alert" role="alert">
                <strong>⚠️ Edit Error:</strong> {editError}
              </div>
            )}

            {/* Applied Confirmation Banner */}
            {appliedNotice && (
              <div className="ai-applied-banner" role="alert">
                <span className="banner-check">✓</span>
                <span>{appliedNotice}</span>
              </div>
            )}

            {/* Clarification Alert */}
            {editProposal && editProposal.needs_clarification && (
              <div className="ai-clarification-card" role="alert">
                <div className="clarification-header">
                  <span className="clarification-icon">❓</span>
                  <strong>Clarification Required</strong>
                </div>
                <p>{editProposal.clarification_message}</p>
                <span className="clarification-hint">
                  Please clarify which specific values you would like to update.
                </span>
              </div>
            )}

            {/* Proposed Change Set (Diff Table) */}
            {editProposal &&
              !editProposal.needs_clarification &&
              editProposal.requested_changes && (
                <div className="ai-results-panel">
                  <div className="results-header">
                    <h4>Proposed Change Set (Diff)</h4>
                    <span className="badge-review">Human Review Required</span>
                  </div>

                  <div className="diff-table-container">
                    <table className="diff-table">
                      <thead>
                        <tr>
                          <th>Field</th>
                          <th>Current Value</th>
                          <th>Proposed Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(editProposal.requested_changes).map(
                          ([field, proposedVal]) => {
                            const currentVal =
                              (editProposal.original_complaint as Record<string, unknown>)[
                                field
                              ] ?? "(empty)";
                            const fieldDisplay = field
                              .split("_")
                              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                              .join(" ");

                            return (
                              <tr key={field} className="diff-row-changed">
                                <td className="diff-field-name">{fieldDisplay}</td>
                                <td className="diff-current-val">
                                  {String(currentVal)}
                                </td>
                                <td className="diff-proposed-val">
                                  <span className="diff-arrow">➔</span>
                                  <strong>{String(proposedVal)}</strong>
                                </td>
                              </tr>
                            );
                          }
                        )}
                      </tbody>
                    </table>
                    <div className="preservation-note">
                      🛡️ <strong>Preservation Guarantee:</strong> All unmentioned complaint fields remain 100% unchanged.
                    </div>
                  </div>

                  {/* Recalculated Risk Card */}
                  {editProposal.risk_assessment && (
                    <div className="risk-assessment-card">
                      <div className="risk-header">
                        <h5>Recalculated Risk Assessment & Triage</h5>
                        <div className="risk-badges">
                          <span
                            className={`badge-severity badge-${
                              editProposal.risk_assessment.initial_severity?.toLowerCase() || "medium"
                            }`}
                          >
                            Severity: {editProposal.risk_assessment.initial_severity || "Medium"}
                          </span>
                          <span
                            className={`badge-priority badge-${
                              editProposal.risk_assessment.priority?.toLowerCase() || "medium"
                            }`}
                          >
                            Priority: {editProposal.risk_assessment.priority || "Medium"}
                          </span>
                        </div>
                      </div>

                      <div className="risk-content">
                        <strong>Updated Risk Rationale:</strong>
                        <p>{editProposal.risk_assessment.risk_reasoning}</p>

                        {editProposal.risk_assessment.recommended_next_actions?.length > 0 && (
                          <>
                            <strong>Recommended QA Next Steps:</strong>
                            <ul className="qa-action-list">
                              {editProposal.risk_assessment.recommended_next_actions.map(
                                (action, idx) => (
                                  <li key={idx}>{action}</li>
                                )
                              )}
                            </ul>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Apply Changes Action */}
                  <div className="apply-actions">
                    <button
                      type="button"
                      id="btn-apply-changes"
                      className="btn-apply-changes"
                      onClick={handleApplyEditToForm}
                    >
                      📋 Apply Changes to Form (Review on Left)
                    </button>
                    <p className="apply-disclaimer">
                      Clicking this will update the editable form on the left. The changes will NOT be written to PostgreSQL until you click "Save Complaint".
                    </p>
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Bottom Interaction / Action Area */}
        <div className="ai-bottom-interaction-area">
          <div className="chat-input-row">
            <input
              type="text"
              id="ai-quick-query-input"
              className="chat-prompt-input"
              placeholder="Ask me anything about this complaint..."
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.target as HTMLInputElement).value.trim()) {
                  const val = (e.target as HTMLInputElement).value.trim();
                  dispatch(setEditInstruction(val));
                  dispatch(setActiveTab("edit"));
                  (e.target as HTMLInputElement).value = "";
                }
              }}
            />
            <button
              type="button"
              id="btn-send-quick-query"
              className="btn-chat-send"
              title="Send to AI Assistant"
              onClick={(e) => {
                const input = e.currentTarget.parentElement?.querySelector("input") as HTMLInputElement;
                if (input && input.value.trim()) {
                  dispatch(setEditInstruction(input.value.trim()));
                  dispatch(setActiveTab("edit"));
                  input.value = "";
                }
              }}
            >
              <span className="send-icon" aria-hidden="true">➤</span>
            </button>
          </div>
          <p className="chat-disclaimer">
            AI responses may contain errors. Please verify information.
          </p>
        </div>

        {/* Footer Governance Disclaimer */}
        <div className="ai-governance-footer">
          <span className="gov-icon">🛡️</span>
          <small>
            <strong>Pharma QMS Safety Rule:</strong> AI proposals never write directly to PostgreSQL. Applying changes updates the local form for human review; explicit saving commits to the database.
          </small>
        </div>
      </div>
    </div>
  );
};
