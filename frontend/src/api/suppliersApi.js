import api from "./axios";

export const suppliersApi = {
  listSuppliers: async () => {
    const response = await api.get("/suppliers/");
    return response.data;
  },

  createSupplier: async (payload) => {
    const response = await api.post("/suppliers/", payload);
    return response.data;
  },

  listDeliveries: async () => {
    const response = await api.get("/suppliers/deliveries/");
    return response.data;
  },

  createDelivery: async (payload) => {
    const response = await api.post("/suppliers/deliveries/", payload);
    return response.data;
  }
};