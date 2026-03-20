import { configureStore } from "@reduxjs/toolkit";
import authReducer from "../features/auth/authSlice";
import productionReducer from "../features/production/productionSlice";
import suppliersReducer from "../features/suppliers/suppliersSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    production: productionReducer,
    suppliers: suppliersReducer
  }
});