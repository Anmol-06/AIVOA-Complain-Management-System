import { configureStore } from "@reduxjs/toolkit";
import appReducer from "./slices/appSlice";
import complaintReducer from "./slices/complaintSlice";
import aiReducer from "./slices/aiSlice";

export const store = configureStore({
  reducer: {
    app: appReducer,
    complaint: complaintReducer,
    ai: aiReducer,
  },
});


// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
