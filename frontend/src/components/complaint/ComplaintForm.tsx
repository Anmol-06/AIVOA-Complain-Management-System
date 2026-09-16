import React from "react";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import {
  updateComplaintField,
  resetComplaintForm,
  setSaving,
  setComplaintError,
  setComplaintSuccess,
  setSavedComplaintId,
  type ComplaintFormData,
} from "../../store/slices/complaintSlice";
import { createComplaint, updateComplaint } from "../../services/api";

export const ComplaintForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const { formData, isSaving, error, successMessage, savedComplaintId } =
    useAppSelector((state) => state.complaint);

  const handleTextChange = (
    field: keyof ComplaintFormData,
    value: string
  ) => {
    dispatch(updateComplaintField({ field, value }));
  };

  const handleNumberChange = (
    field: keyof ComplaintFormData,
    value: string
  ) => {
    if (value === "") {
      dispatch(updateComplaintField({ field, value: null }));
    } else {
      const parsed = parseInt(value, 10);
      dispatch(
        updateComplaintField({
          field,
          value: isNaN(parsed) ? null : parsed,
        })
      );
    }
  };

  const handleReset = () => {
    dispatch(resetComplaintForm());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(setSaving(true));
    dispatch(setComplaintError(null));
    dispatch(setComplaintSuccess(null));

    try {
      if (savedComplaintId) {
        const response = await updateComplaint(savedComplaintId, formData);
        dispatch(
          setComplaintSuccess(
            `Complaint successfully updated in PostgreSQL (ID: ${response.id})`
          )
        );
      } else {
        const response = await createComplaint(formData);
        dispatch(setSavedComplaintId(response.id));
        dispatch(
          setComplaintSuccess(
            `Complaint successfully registered with ID: ${response.id}`
          )
        );
      }
    } catch (err: any) {
      dispatch(
        setComplaintError(
          err.message || "An unexpected error occurred while saving the complaint."
        )
      );
    } finally {
      dispatch(setSaving(false));
    }
  };

  return (
    <form className="complaint-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <div className="form-title-group">
          <h2>Log Customer Complaint</h2>
          <p className="form-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <div className="form-header-badge">
          <span className={`status-badge-pill ${savedComplaintId ? "badge-saved" : "badge-pending"}`}>
            {savedComplaintId ? "Registered" : "Pending Triage"}
          </span>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <span className="alert-icon">⚠️</span>
          <div className="alert-content">
            <strong>Submission Error:</strong> {error}
          </div>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success" role="status">
          <span className="alert-icon">✅</span>
          <div className="alert-content">
            <strong>Success:</strong> {successMessage}
            {savedComplaintId && (
              <div className="record-badge">
                Record UUID: <code>{savedComplaintId}</code>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 1: Origin & Customer Details */}
      <fieldset className="form-section">
        <legend>1. ORIGIN &amp; CUSTOMER DETAILS</legend>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="complaint_source">Complaint Source</label>
            <select
              id="complaint_source"
              name="complaint_source"
              value={formData.complaint_source}
              onChange={(e) => handleTextChange("complaint_source", e.target.value)}
            >
              <option value="">Awaiting AI extraction...</option>
              <option value="Email">Email</option>
              <option value="Phone Call">Phone Call</option>
              <option value="Web Portal">Web Portal</option>
              <option value="Healthcare Professional">Healthcare Professional Report</option>
              <option value="Distributor">Wholesaler / Distributor</option>
              <option value="Regulatory Authority">Regulatory Authority Notice</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="customer_name">Customer Name</label>
            <input
              type="text"
              id="customer_name"
              name="customer_name"
              placeholder="Awaiting AI extraction..."
              value={formData.customer_name}
              onChange={(e) => handleTextChange("customer_name", e.target.value)}
            />
          </div>
        </div>
      </fieldset>

      {/* SECTION 2: Product & Batch Identification */}
      <fieldset className="form-section">
        <legend>2. PRODUCT &amp; BATCH IDENTIFICATION</legend>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="product_name">Product Name</label>
            <input
              type="text"
              id="product_name"
              name="product_name"
              placeholder="Awaiting AI extraction..."
              value={formData.product_name}
              onChange={(e) => handleTextChange("product_name", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="product_strength_grade">Product Strength/Grade</label>
            <input
              type="text"
              id="product_strength_grade"
              name="product_strength_grade"
              placeholder="Awaiting AI extraction..."
              value={formData.product_strength_grade}
              onChange={(e) => handleTextChange("product_strength_grade", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="batch_lot_number">Batch/Lot Number</label>
            <input
              type="text"
              id="batch_lot_number"
              name="batch_lot_number"
              placeholder="Awaiting AI extraction..."
              value={formData.batch_lot_number}
              onChange={(e) => handleTextChange("batch_lot_number", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="manufacturing_date">Manufacturing Date</label>
            <input
              type="date"
              id="manufacturing_date"
              name="manufacturing_date"
              placeholder="Awaiting AI extraction..."
              value={formData.manufacturing_date}
              onChange={(e) => handleTextChange("manufacturing_date", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="expiry_date">Expiry Date</label>
            <input
              type="date"
              id="expiry_date"
              name="expiry_date"
              placeholder="Awaiting AI extraction..."
              value={formData.expiry_date}
              onChange={(e) => handleTextChange("expiry_date", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="quantity_affected">Quantity Affected</label>
            <div className="input-with-unit">
              <input
                type="number"
                id="quantity_affected"
                name="quantity_affected"
                min="1"
                placeholder="Awaiting AI extraction..."
                value={formData.quantity_affected ?? ""}
                onChange={(e) => handleNumberChange("quantity_affected", e.target.value)}
              />
              <span className="unit-tag">kg / units</span>
            </div>
          </div>
        </div>
      </fieldset>

      {/* SECTION 3: Complaint Details */}
      <fieldset className="form-section">
        <legend>3. COMPLAINT DETAILS</legend>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="complaint_type">Complaint Type</label>
            <select
              id="complaint_type"
              name="complaint_type"
              value={formData.complaint_type}
              onChange={(e) => handleTextChange("complaint_type", e.target.value)}
            >
              <option value="">Awaiting AI extraction...</option>
              <option value="Product damage">Product damage / Packaging Defect</option>
              <option value="Contamination">Foreign Matter / Contamination</option>
              <option value="Discoloration">Discoloration / Appearance</option>
              <option value="Labeling issue">Labeling / Packaging Error</option>
              <option value="Efficacy failure">Suspected Inefficacy</option>
              <option value="Adverse event">Adverse Event / Reaction</option>
              <option value="Device malfunction">Delivery Device Malfunction</option>
              <option value="Other">Other Quality Issue</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="complaint_date">Complaint Date</label>
            <input
              type="date"
              id="complaint_date"
              name="complaint_date"
              placeholder="Awaiting AI extraction..."
              value={formData.complaint_date}
              onChange={(e) => handleTextChange("complaint_date", e.target.value)}
            />
          </div>

          <div className="form-group full-width">
            <label htmlFor="detailed_description">Detailed Complaint Description</label>
            <textarea
              id="detailed_description"
              name="detailed_description"
              rows={4}
              placeholder="Awaiting AI extraction..."
              value={formData.detailed_description}
              onChange={(e) => handleTextChange("detailed_description", e.target.value)}
            />
          </div>
        </div>
      </fieldset>

      {/* SECTION 4: Initial Assessment & Priority */}
      <fieldset className="form-section">
        <legend>4. INITIAL ASSESSMENT &amp; PRIORITY</legend>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="initial_severity">Initial Severity</label>
            <select
              id="initial_severity"
              name="initial_severity"
              value={formData.initial_severity}
              onChange={(e) => handleTextChange("initial_severity", e.target.value)}
            >
              <option value="">Awaiting AI extraction...</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={(e) => handleTextChange("priority", e.target.value)}
            >
              <option value="">Awaiting AI extraction...</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Urgent">Urgent</option>
            </select>
          </div>
        </div>
      </fieldset>

      {/* BUTTON ACTIONS */}
      <div className="form-actions">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleReset}
          disabled={isSaving}
        >
          <span className="btn-icon">↺</span>
          Reset Form
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isSaving}
          id="save-complaint-btn"
        >
          {isSaving ? (
            <>
              <span className="spinner" aria-hidden="true"></span>
              {savedComplaintId ? "Updating Complaint..." : "Saving Complaint..."}
            </>
          ) : (
            <>
              <span className="btn-icon">💾</span>
              {savedComplaintId ? "Update Complaint (PATCH)" : "Save Complaint"}
            </>
          )}
        </button>
      </div>
    </form>
  );
};
