import api from "./axios";

export const productionApi = {
  list: async () => {
    const response = await api.get("/production/entries/");
    return response.data;
  },

  create: async (payload) => {
    const response = await api.post("/production/entries/", payload);
    return response.data;
  }
};