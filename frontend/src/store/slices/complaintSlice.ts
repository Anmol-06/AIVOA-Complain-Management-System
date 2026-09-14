import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

/**
 * ComplaintFormData Interface
 * Strictly aligns with the backend ComplaintCreate schema.
 * All domain fields are initially empty/null to allow for partial real-world complaints.
 */
export interface ComplaintFormData {
  complaint_source: string;
  customer_name: string;
  product_name: string;
  product_strength_grade: string;
  batch_lot_number: string;
  manufacturing_date: string;
  expiry_date: string;
  quantity_affected: number | null;
  complaint_type: string;
  complaint_date: string;
  detailed_description: string;
  initial_severity: string;
  priority: string;
}

export interface ComplaintState {
  formData: ComplaintFormData;
  isSaving: boolean;
  error: string | null;
  successMessage: string | null;
  savedComplaintId: string | null;
}

const initialFormData: ComplaintFormData = {
  complaint_source: "",
  customer_name: "",
  product_name: "",
  product_strength_grade: "",
  batch_lot_number: "",
  manufacturing_date: "",
  expiry_date: "",
  quantity_affected: null,
  complaint_type: "",
  complaint_date: "",
  detailed_description: "",
  initial_severity: "",
  priority: "",
};

const initialState: ComplaintState = {
  formData: initialFormData,
  isSaving: false,
  error: null,
  successMessage: null,
  savedComplaintId: null,
};

export const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    updateComplaintField: <K extends keyof ComplaintFormData>(
      state: ComplaintState,
      action: PayloadAction<{ field: K; value: ComplaintFormData[K] }>
    ) => {
      state.formData[action.payload.field] = action.payload.value;
    },
    resetComplaintForm: (state) => {
      state.formData = initialFormData;
      state.error = null;
      state.successMessage = null;
      state.savedComplaintId = null;
    },
    setSaving: (state, action: PayloadAction<boolean>) => {
      state.isSaving = action.payload;
    },
    setComplaintError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setComplaintSuccess: (state, action: PayloadAction<string | null>) => {
      state.successMessage = action.payload;
    },
    setSavedComplaintId: (state, action: PayloadAction<string | null>) => {
      state.savedComplaintId = action.payload;
    },
  },
});

export const {
  updateComplaintField,
  resetComplaintForm,
  setSaving,
  setComplaintError,
  setComplaintSuccess,
  setSavedComplaintId,
} = complaintSlice.actions;

export default complaintSlice.reducer;
