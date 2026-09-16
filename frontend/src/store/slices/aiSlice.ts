import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { AIComplaintIntakeResponse } from "../../services/api";

export interface AIState {
  inputText: string;
  isAnalyzing: boolean;
  error: string | null;
  analysisResult: AIComplaintIntakeResponse | null;
}

const initialState: AIState = {
  inputText: "",
  isAnalyzing: false,
  error: null,
  analysisResult: null,
};

export const aiSlice = createSlice({
  name: "ai",
  initialState,
  reducers: {
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
  },
});

export const {
  setInputText,
  setAnalyzing,
  setAnalysisError,
  setAnalysisResult,
  clearAnalysis,
} = aiSlice.actions;

export default aiSlice.reducer;
