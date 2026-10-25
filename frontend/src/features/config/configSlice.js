import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { analyticsApi } from "../../api/analyticsApi";

/**
 * Platform configuration served by the backend (GET /api/analytics/config/):
 * KPI thresholds, analysis windows, input limits, period definitions, the
 * server's current date and the live-refresh cadence. The UI reads these
 * instead of hardcoding them, so a change to backend/.env shows up everywhere.
 */
export const fetchPlatformConfig = createAsyncThunk("config/fetch", async (_, { rejectWithValue }) => {
  try {
    return await analyticsApi.getConfig();
  } catch {
    return rejectWithValue("Could not load platform settings.");
  }
});

const configSlice = createSlice({
  name: "config",
  initialState: { data: null, loadedAt: null, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPlatformConfig.fulfilled, (state, action) => {
        state.data = action.payload;
        state.loadedAt = Date.now();
        state.error = null;
      })
      .addCase(fetchPlatformConfig.rejected, (state, action) => {
        state.error = action.payload; // keep the last good config
      });
  },
});

export default configSlice.reducer;
