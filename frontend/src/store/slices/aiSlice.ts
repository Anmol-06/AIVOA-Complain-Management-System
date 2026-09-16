import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type {
  AIComplaintIntakeResponse,
  AIComplaintEditProposal,
} from "../../services/api";

export interface AIState {
  activeTab: "intake" | "edit";
  // Intake state
  inputText: string;
  isAnalyzing: boolean;
  error: string | null;
  analysisResult: AIComplaintIntakeResponse | null;
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
  editInstruction: "",
  isEditing: false,
  editError: null,
  editProposal: null,
};

export const aiSlice = createSlice({
  name: "ai",
  initialState,
  reducers: {
    setActiveTab: (state, action: PayloadAction<"intake" | "edit">) => {
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
  setEditInstruction,
  setEditing,
  setEditError,
  setEditProposal,
  clearEdit,
} = aiSlice.actions;

export default aiSlice.reducer;

