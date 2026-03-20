import { createAsyncThunk } from "@reduxjs/toolkit";
import { productionApi } from "../../api/productionApi";

export const fetchProductionEntries = createAsyncThunk(
  "production/fetchEntries",
  async (_, thunkAPI) => {
    try {
      return await productionApi.list();
    } catch (error) {
      return thunkAPI.rejectWithValue("Failed to load production entries.");
    }
  }
);

export const createProductionEntry = createAsyncThunk(
  "production/createEntry",
  async (payload, thunkAPI) => {
    try {
      return await productionApi.create(payload);
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error?.response?.data || "Failed to create production entry."
      );
    }
  }
);