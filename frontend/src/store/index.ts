import { configureStore } from "@reduxjs/toolkit";
import appReducer from "./slices/appSlice";
import complaintReducer from "./slices/complaintSlice";

export const store = configureStore({
  reducer: {
    app: appReducer,
    complaint: complaintReducer,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
