import { createSlice } from "@reduxjs/toolkit";
import { createProductionEntry, fetchProductionEntries } from "./productionThunks";

const initialState = {
  entries: [],
  loading: false,
  error: null,
  successMessage: null
};

const productionSlice = createSlice({
  name: "production",
  initialState,
  reducers: {
    clearProductionMessage(state) {
      state.error = null;
      state.successMessage = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductionEntries.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProductionEntries.fulfilled, (state, action) => {
        state.loading = false;
        state.entries = action.payload.results || action.payload;
      })
      .addCase(fetchProductionEntries.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(createProductionEntry.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.successMessage = null;
      })
      .addCase(createProductionEntry.fulfilled, (state) => {
        state.loading = false;
        state.successMessage = "Production entry created successfully.";
      })
      .addCase(createProductionEntry.rejected, (state, action) => {
        state.loading = false;
        state.error = typeof action.payload === "string"
          ? action.payload
          : JSON.stringify(action.payload);
      });
  }
});

export const { clearProductionMessage } = productionSlice.actions;
export default productionSlice.reducer;