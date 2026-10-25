import { createSlice } from "@reduxjs/toolkit";
import { formatDate } from "../../utils/formatters";
import { createProductionEntry, fetchProductionEntries, voidProductionEntry } from "./productionThunks";

const initialState = {
  entries: [],
  count: 0,
  loading: false,
  loadError: null,
  submitting: false,
  submitError: null,
  fieldErrors: {},
  successMessage: null,
  voidingId: null,
  voidError: null,
};

const productionSlice = createSlice({
  name: "production",
  initialState,
  reducers: {
    clearProductionMessage(state) {
      state.submitError = null;
      state.fieldErrors = {};
      state.successMessage = null;
      state.voidError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductionEntries.pending, (state) => {
        state.loading = true;
        state.loadError = null;
      })
      .addCase(fetchProductionEntries.fulfilled, (state, action) => {
        state.loading = false;
        const data = action.payload;
        state.entries = Array.isArray(data) ? data : data.results ?? [];
        state.count = Array.isArray(data) ? data.length : data.count ?? state.entries.length;
      })
      .addCase(fetchProductionEntries.rejected, (state, action) => {
        state.loading = false;
        state.loadError = action.payload;
      })

      .addCase(createProductionEntry.pending, (state) => {
        state.submitting = true;
        state.submitError = null;
        state.fieldErrors = {};
        state.successMessage = null;
      })
      .addCase(createProductionEntry.fulfilled, (state, action) => {
        state.submitting = false;
        state.successMessage = `Entry for ${formatDate(action.payload.production_date)} saved — yield ${action.payload.yield_percent}%.`;
      })
      .addCase(createProductionEntry.rejected, (state, action) => {
        state.submitting = false;
        state.submitError = action.payload?.message ?? "Failed to save production entry.";
        state.fieldErrors = action.payload?.fieldErrors ?? {};
      })

      .addCase(voidProductionEntry.pending, (state, action) => {
        state.voidingId = action.meta.arg.id;
        state.voidError = null;
      })
      .addCase(voidProductionEntry.fulfilled, (state, action) => {
        state.voidingId = null;
        state.entries = state.entries.filter((e) => e.id !== action.payload.id);
        state.count = Math.max(0, state.count - 1);
        state.successMessage = `Entry for ${formatDate(action.payload.production_date)} voided and stock reversed.`;
      })
      .addCase(voidProductionEntry.rejected, (state, action) => {
        state.voidingId = null;
        state.voidError = action.payload;
      });
  },
});

export const { clearProductionMessage } = productionSlice.actions;
export default productionSlice.reducer;
