import { createAsyncThunk } from "@reduxjs/toolkit";
import { suppliersApi } from "../../api/suppliersApi";
import { getErrorMessage, getFieldErrors } from "../../utils/errors";

const list = (data) => (Array.isArray(data) ? data : data.results ?? []);

export const fetchSuppliersData = createAsyncThunk("suppliers/fetchData", async (_, { rejectWithValue }) => {
  try {
    const [suppliers, deliveries] = await Promise.all([suppliersApi.listSuppliers(), suppliersApi.listDeliveries()]);
    return {
      suppliers: list(suppliers),
      deliveries: list(deliveries),
      deliveriesCount: deliveries.count ?? list(deliveries).length,
    };
  } catch (error) {
    return rejectWithValue(getErrorMessage(error, "Failed to load supplier data."));
  }
});

const submitThunk = (type, call, fallback) =>
  createAsyncThunk(type, async (payload, { rejectWithValue }) => {
    try {
      return await call(payload);
    } catch (error) {
      return rejectWithValue({ message: getErrorMessage(error, fallback), fieldErrors: getFieldErrors(error) });
    }
  });

export const createSupplier = submitThunk("suppliers/createSupplier", suppliersApi.createSupplier, "Failed to create supplier.");
export const createDelivery = submitThunk("suppliers/createDelivery", suppliersApi.createDelivery, "Failed to log delivery.");

export const voidDelivery = createAsyncThunk("suppliers/voidDelivery", async ({ id, reason }, { rejectWithValue }) => {
  try {
    return await suppliersApi.voidDelivery(id, reason);
  } catch (error) {
    return rejectWithValue(getErrorMessage(error, "Failed to void delivery."));
  }
});
