import api from "./axios";

export const authApi = {
  login: async (payload) => {
    const response = await api.post("/auth/login/", payload);
    return response.data;
  },

  getMe: async (token = null) => {
    const config = token
      ? {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      : undefined;

    const response = await api.get("/auth/me/", config);
    return response.data;
  }
};