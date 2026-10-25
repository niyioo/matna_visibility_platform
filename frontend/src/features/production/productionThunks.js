import { createAsyncThunk } from "@reduxjs/toolkit";
import { productionApi } from "../../api/productionApi";
import { getErrorMessage, getFieldErrors } from "../../utils/errors";

export const fetchProductionEntries = createAsyncThunk(
  "production/fetchEntries",
  async (params, { rejectWithValue }) => {
    try {
      return await productionApi.list(params);
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Failed to load production entries."));
    }
  }
);

export const createProductionEntry = createAsyncThunk(
  "production/createEntry",
  async (payload, { rejectWithValue }) => {
    try {
      return await productionApi.create(payload);
    } catch (error) {
      return rejectWithValue({
        message: getErrorMessage(error, "Failed to save production entry."),
        fieldErrors: getFieldErrors(error),
      });
    }
  }
);

export const voidProductionEntry = createAsyncThunk(
  "production/voidEntry",
  async ({ id, reason }, { rejectWithValue }) => {
    try {
      return await productionApi.void(id, reason);
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Failed to void entry."));
    }
  }
);
