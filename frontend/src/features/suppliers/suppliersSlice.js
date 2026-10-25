import { createSlice } from "@reduxjs/toolkit";
import { createDelivery, createSupplier, fetchSuppliersData, voidDelivery } from "./suppliersThunks";

const emptyForm = { submitting: false, error: null, fieldErrors: {}, success: null };

const initialState = {
  suppliers: [],
  deliveries: [],
  deliveriesCount: 0,
  loading: false,
  loadError: null,
  // Each form owns its status so one form's messages never appear on the other.
  forms: { supplier: { ...emptyForm }, delivery: { ...emptyForm } },
  voidingId: null,
  voidError: null,
};

const trackForm = (builder, thunk, key, successMessage) =>
  builder
    .addCase(thunk.pending, (state) => {
      state.forms[key] = { ...emptyForm, submitting: true };
    })
    .addCase(thunk.fulfilled, (state, action) => {
      state.forms[key] = { ...emptyForm, success: successMessage(action.payload) };
    })
    .addCase(thunk.rejected, (state, action) => {
      state.forms[key] = {
        ...emptyForm,
        error: action.payload?.message ?? "Request failed.",
        fieldErrors: action.payload?.fieldErrors ?? {},
      };
    });

const suppliersSlice = createSlice({
  name: "suppliers",
  initialState,
  reducers: {
    clearFormStatus(state, action) {
      state.forms[action.payload] = { ...emptyForm };
    },
    clearVoidError(state) {
      state.voidError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSuppliersData.pending, (state) => {
        state.loading = true;
        state.loadError = null;
      })
      .addCase(fetchSuppliersData.fulfilled, (state, action) => {
        state.loading = false;
        Object.assign(state, action.payload);
      })
      .addCase(fetchSuppliersData.rejected, (state, action) => {
        state.loading = false;
        state.loadError = action.payload;
      })
      .addCase(voidDelivery.pending, (state, action) => {
        state.voidingId = action.meta.arg.id;
        state.voidError = null;
      })
      .addCase(voidDelivery.fulfilled, (state, action) => {
        state.voidingId = null;
        state.deliveries = state.deliveries.filter((d) => d.id !== action.payload.id);
        state.deliveriesCount = Math.max(0, state.deliveriesCount - 1);
      })
      .addCase(voidDelivery.rejected, (state, action) => {
        state.voidingId = null;
        state.voidError = action.payload;
      });

    trackForm(builder, createSupplier, "supplier", (s) => `Supplier "${s.name}" added.`);
    trackForm(builder, createDelivery, "delivery", (d) => `Delivery of ${d.quantity_tons} t from ${d.supplier_name} logged.`);
  },
});

export const { clearFormStatus, clearVoidError } = suppliersSlice.actions;
export default suppliersSlice.reducer;
