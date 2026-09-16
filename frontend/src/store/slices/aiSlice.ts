import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type {
  AIComplaintIntakeResponse,
  AIComplaintEditProposal,
  AIDocumentExtractionResponse,
} from "../../services/api";

export interface AIState {
  activeTab: "intake" | "document" | "edit";
  // Intake state
  inputText: string;
  isAnalyzing: boolean;
  error: string | null;
  analysisResult: AIComplaintIntakeResponse | null;
  // Document extraction state
  selectedFileName: string | null;
  selectedFileSize: number | null;
  documentStatus:
    | "idle"
    | "uploading"
    | "extracting_text"
    | "analyzing"
    | "assessing_risk"
    | "complete"
    | "error";
  documentProcessingStep: string | null;
  documentError: string | null;
  documentResult: AIDocumentExtractionResponse | null;
  // Edit state
  editInstruction: string;
  isEditing: boolean;
  editError: string | null;
  editProposal: AIComplaintEditProposal | null;
}

const initialState: AIState = {
  activeTab: "intake",
  inputText: "",
  isAnalyzing: false,
  error: null,
  analysisResult: null,
  selectedFileName: null,
  selectedFileSize: null,
  documentStatus: "idle",
  documentProcessingStep: null,
  documentError: null,
  documentResult: null,
  editInstruction: "",
  isEditing: false,
  editError: null,
  editProposal: null,
};

export const aiSlice = createSlice({
  name: "ai",
  initialState,
  reducers: {
    setActiveTab: (
      state,
      action: PayloadAction<"intake" | "document" | "edit">
    ) => {
      state.activeTab = action.payload;
    },
    // Intake actions
    setInputText: (state, action: PayloadAction<string>) => {
      state.inputText = action.payload;
    },
    setAnalyzing: (state, action: PayloadAction<boolean>) => {
      state.isAnalyzing = action.payload;
      if (action.payload) {
        state.error = null;
      }
    },
    setAnalysisError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.isAnalyzing = false;
    },
    setAnalysisResult: (
      state,
      action: PayloadAction<AIComplaintIntakeResponse | null>
    ) => {
      state.analysisResult = action.payload;
      state.isAnalyzing = false;
      state.error = null;
    },
    clearAnalysis: (state) => {
      state.inputText = "";
      state.isAnalyzing = false;
      state.error = null;
      state.analysisResult = null;
    },
    // Document extraction actions
    setSelectedFile: (
      state,
      action: PayloadAction<{ name: string; size: number } | null>
    ) => {
      if (action.payload) {
        state.selectedFileName = action.payload.name;
        state.selectedFileSize = action.payload.size;
      } else {
        state.selectedFileName = null;
        state.selectedFileSize = null;
      }
      state.documentError = null;
    },
    setDocumentStatus: (
      state,
      action: PayloadAction<AIState["documentStatus"]>
    ) => {
      state.documentStatus = action.payload;
      if (action.payload === "uploading" || action.payload === "extracting_text") {
        state.documentError = null;
      }
    },
    setDocumentProcessingStep: (state, action: PayloadAction<string | null>) => {
      state.documentProcessingStep = action.payload;
    },
    setDocumentError: (state, action: PayloadAction<string | null>) => {
      state.documentError = action.payload;
      state.documentStatus = "error";
      state.documentProcessingStep = null;
    },
    setDocumentResult: (
      state,
      action: PayloadAction<AIDocumentExtractionResponse | null>
    ) => {
      state.documentResult = action.payload;
      state.documentStatus = action.payload ? "complete" : "idle";
      state.documentProcessingStep = null;
      state.documentError = null;
    },
    clearDocument: (state) => {
      state.selectedFileName = null;
      state.selectedFileSize = null;
      state.documentStatus = "idle";
      state.documentProcessingStep = null;
      state.documentError = null;
      state.documentResult = null;
    },
    // Edit actions
    setEditInstruction: (state, action: PayloadAction<string>) => {
      state.editInstruction = action.payload;
    },
    setEditing: (state, action: PayloadAction<boolean>) => {
      state.isEditing = action.payload;
      if (action.payload) {
        state.editError = null;
      }
    },
    setEditError: (state, action: PayloadAction<string | null>) => {
      state.editError = action.payload;
      state.isEditing = false;
    },
    setEditProposal: (
      state,
      action: PayloadAction<AIComplaintEditProposal | null>
    ) => {
      state.editProposal = action.payload;
      state.isEditing = false;
      state.editError = null;
    },
    clearEdit: (state) => {
      state.editInstruction = "";
      state.isEditing = false;
      state.editError = null;
      state.editProposal = null;
    },
  },
});

export const {
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
} = aiSlice.actions;

export default aiSlice.reducer;

