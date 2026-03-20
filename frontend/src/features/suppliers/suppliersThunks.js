import { createAsyncThunk } from "@reduxjs/toolkit";
import { suppliersApi } from "../../api/suppliersApi";

export const fetchSuppliersData = createAsyncThunk(
  "suppliers/fetchData",
  async (_, thunkAPI) => {
    try {
      const [suppliers, deliveries] = await Promise.all([
        suppliersApi.listSuppliers(),
        suppliersApi.listDeliveries()
      ]);
      return {
        suppliers: suppliers.results || suppliers,
        deliveries: deliveries.results || deliveries
      };
    } catch (error) {
      return thunkAPI.rejectWithValue("Failed to load supplier data.");
    }
  }
);

export const createSupplier = createAsyncThunk(
  "suppliers/createSupplier",
  async (payload, thunkAPI) => {
    try {
      return await suppliersApi.createSupplier(payload);
    } catch {
      return thunkAPI.rejectWithValue("Failed to create supplier.");
    }
  }
);

export const createDelivery = createAsyncThunk(
  "suppliers/createDelivery",
  async (payload, thunkAPI) => {
    try {
      return await suppliersApi.createDelivery(payload);
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error?.response?.data || "Failed to create delivery."
      );
    }
  }
);