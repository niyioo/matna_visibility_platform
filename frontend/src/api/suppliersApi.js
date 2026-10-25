import api from "./axios";

export const suppliersApi = {
  // Suppliers are few; fetch up to the API maximum so dropdowns see them all.
  listSuppliers: (params) => api.get("/suppliers/", { params: { page_size: 100, ...params } }).then((r) => r.data),
  createSupplier: (payload) => api.post("/suppliers/", payload).then((r) => r.data),
  listDeliveries: (params) => api.get("/suppliers/deliveries/", { params }).then((r) => r.data),
  createDelivery: (payload) => api.post("/suppliers/deliveries/", payload).then((r) => r.data),
  voidDelivery: (id, reason) => api.post(`/suppliers/deliveries/${id}/void/`, { reason }).then((r) => r.data),
};
