import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

/**
 * AppState Interface
 *
 * NOTE: This slice exists solely as a foundational integration test for Unit 1
 * to verify that Redux Toolkit and React-Redux are wired up properly.
 * Future complaint state will be modeled in its own dedicated slice (e.g., complaintSlice).
 */
export interface AppState {
  isInitialized: boolean;
  systemName: string;
  statusMessage: string;
}

const initialState: AppState = {
  isInitialized: true,
  systemName: "AIVOA Customer Complaint Management System",
  statusMessage: "Frontend Redux store initialized successfully (Unit 1 Foundation)",
};

export const appSlice = createSlice({
  name: "app",
  initialState,
  reducers: {
    setStatusMessage: (state, action: PayloadAction<string>) => {
      state.statusMessage = action.payload;
    },
  },
});

export const { setStatusMessage } = appSlice.actions;
export default appSlice.reducer;
