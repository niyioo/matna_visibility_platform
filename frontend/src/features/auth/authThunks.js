import { createAsyncThunk } from "@reduxjs/toolkit";
import { authApi } from "../../api/authApi";
import { storage } from "../../utils/storage";

export const loginUser = createAsyncThunk(
  "auth/loginUser",
  async (payload, thunkAPI) => {
    try {
      const tokens = await authApi.login(payload);

      storage.setAccessToken(tokens.access);
      storage.setRefreshToken(tokens.refresh);

      const user = await authApi.getMe(tokens.access);
      storage.setUser(user);

      return { tokens, user };
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error?.response?.data?.detail ||
          error?.response?.data ||
          "Login failed."
      );
    }
  }
);

export const loadCurrentUser = createAsyncThunk(
  "auth/loadCurrentUser",
  async (_, thunkAPI) => {
    try {
      const token = storage.getAccessToken();

      if (!token) {
        return thunkAPI.rejectWithValue("No token found.");
      }

      const user = await authApi.getMe(token);
      storage.setUser(user);
      return user;
    } catch (error) {
      storage.clearAuth();
      return thunkAPI.rejectWithValue("Session expired.");
    }
  }
);