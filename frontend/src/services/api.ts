import type { ComplaintFormData } from "../store/slices/complaintSlice";

export interface ComplaintResponse extends ComplaintFormData {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface AIComplaintExtraction {
  complaint_source?: string | null;
  customer_name?: string | null;
  product_name?: string | null;
  product_strength_grade?: string | null;
  batch_lot_number?: string | null;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  quantity_affected?: number | null;
  complaint_type?: string | null;
  complaint_date?: string | null;
  detailed_description?: string | null;
}

export interface AIRiskAssessment {
  initial_severity?: string | null;
  priority?: string | null;
  risk_reasoning: string;
  recommended_next_actions: string[];
}

export interface AIComplaintIntakeResponse {
  complaint: AIComplaintExtraction;
  risk_assessment: AIRiskAssessment;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

/**
 * Submits a new customer complaint to the FastAPI backend.
 * 
 * Data Hygiene:
 * Converts empty strings ("") to null so the database receives true SQL NULL
 * values rather than empty strings, adhering strictly to pharmaceutical data hygiene.
 */
export async function createComplaint(
  data: ComplaintFormData
): Promise<ComplaintResponse> {
  const sanitizedPayload = Object.fromEntries(
    Object.entries(data).map(([key, value]) => [
      key,
      value === "" ? null : value,
    ])
  );

  const response = await fetch(`${API_BASE_URL}/api/complaints`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(sanitizedPayload),
  });

  if (!response.ok) {
    let errorMessage = `Failed to save complaint (HTTP ${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        if (typeof errorJson.detail === "string") {
          errorMessage = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          // Format Pydantic 422 validation errors cleanly
          errorMessage = errorJson.detail
            .map((err: any) => `${err.loc?.join(".") || "Field"}: ${err.msg}`)
            .join(" | ");
        }
      }
    } catch {
      // Fallback to generic message if response isn't JSON
    }
    throw new Error(errorMessage);
  }

  return (await response.json()) as ComplaintResponse;
}

/**
 * Submits natural language complaint text to the AI intake pipeline.
 * Executes LangGraph workflow on the server and returns structured suggestions.
 * Note: Never saves to PostgreSQL automatically.
 */
export async function runComplaintIntake(
  text: string
): Promise<AIComplaintIntakeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/complaint-intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    let errorMessage = `AI intake failed (HTTP ${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        if (typeof errorJson.detail === "string") {
          errorMessage = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorMessage = errorJson.detail
            .map((err: any) => `${err.loc?.join(".") || "Field"}: ${err.msg}`)
            .join(" | ");
        }
      }
    } catch {
      // Fallback to generic message
    }
    throw new Error(errorMessage);
  }

  return (await response.json()) as AIComplaintIntakeResponse;
}

export interface AIComplaintEditRequest {
  complaint_id?: string | null;
  current_complaint?: Partial<ComplaintFormData> | null;
  edit_instruction: string;
}

export interface AIComplaintEditProposal {
  complaint_id?: string | null;
  is_valid_edit: boolean;
  needs_clarification: boolean;
  clarification_message?: string | null;
  original_complaint: Record<string, any>;
  requested_changes: Record<string, any>;
  updated_complaint: Record<string, any>;
  risk_assessment?: AIRiskAssessment | null;
}

/**
 * Submits a natural language edit instruction against an existing complaint.
 * Executes LangGraph edit workflow on the server and returns structured proposed changes.
 * Note: Never saves to PostgreSQL automatically.
 */
export async function runComplaintEdit(
  request: AIComplaintEditRequest
): Promise<AIComplaintEditProposal> {
  const response = await fetch(`${API_BASE_URL}/api/ai/complaint-edit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorMessage = `AI edit failed (HTTP ${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        if (typeof errorJson.detail === "string") {
          errorMessage = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorMessage = errorJson.detail
            .map((err: any) => `${err.loc?.join(".") || "Field"}: ${err.msg}`)
            .join(" | ");
        }
      }
    } catch {
      // Fallback to generic message
    }
    throw new Error(errorMessage);
  }

  return (await response.json()) as AIComplaintEditProposal;
}


