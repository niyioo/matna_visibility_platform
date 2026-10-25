import { createSlice } from "@reduxjs/toolkit";
import { loginUser, logoutUser, restoreSession } from "./authThunks";

const initialState = {
  user: null,
  // True until the boot-time session restore finishes. The refresh cookie is
  // httpOnly, so the app cannot know whether a session exists without asking.
  initializing: true,
  // True while the login form is submitting.
  loading: false,
  error: null,
  sessionExpired: false,
  // Set when the server could not be reached during restore.
  offline: false,
};

const signedOut = (state) => {
  state.user = null;
  state.loading = false;
  state.initializing = false;
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    sessionEnded(state, action) {
      signedOut(state);
      state.sessionExpired = Boolean(action.payload?.expired);
    },
    clearAuthError(state) {
      state.error = null;
      state.sessionExpired = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.sessionExpired = false;
        state.offline = false;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ?? "Sign-in failed.";
      })

      .addCase(restoreSession.fulfilled, (state, action) => {
        state.initializing = false;
        state.user = action.payload;
      })
      .addCase(restoreSession.rejected, (state, action) => {
        signedOut(state);
        state.sessionExpired = Boolean(action.payload?.expired);
        state.offline = Boolean(action.payload?.offline);
      })

      .addCase(logoutUser.pending, (state) => {
        signedOut(state);
        state.error = null;
        state.sessionExpired = false;
      });
  },
});

export const { sessionEnded, clearAuthError } = authSlice.actions;
export default authSlice.reducer;
