import type { ComplaintFormData } from "../store/slices/complaintSlice";

export interface ComplaintResponse extends ComplaintFormData {
  id: string;
  created_at: string;
  updated_at: string;
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
