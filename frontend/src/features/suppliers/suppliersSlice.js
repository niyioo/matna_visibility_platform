import { createSlice } from "@reduxjs/toolkit";
import { createDelivery, createSupplier, fetchSuppliersData } from "./suppliersThunks";

const initialState = {
  suppliers: [],
  deliveries: [],
  loading: false,
  error: null,
  successMessage: null
};

const suppliersSlice = createSlice({
  name: "suppliers",
  initialState,
  reducers: {
    clearSupplierMessages(state) {
      state.error = null;
      state.successMessage = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSuppliersData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSuppliersData.fulfilled, (state, action) => {
        state.loading = false;
        state.suppliers = action.payload.suppliers;
        state.deliveries = action.payload.deliveries;
      })
      .addCase(fetchSuppliersData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(createSupplier.fulfilled, (state) => {
        state.successMessage = "Supplier created successfully.";
      })
      .addCase(createSupplier.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(createDelivery.fulfilled, (state) => {
        state.successMessage = "Delivery logged successfully.";
      })
      .addCase(createDelivery.rejected, (state, action) => {
        state.error =
          typeof action.payload === "string"
            ? action.payload
            : JSON.stringify(action.payload);
      });
  }
});

export const { clearSupplierMessages } = suppliersSlice.actions;
export default suppliersSlice.reducer;