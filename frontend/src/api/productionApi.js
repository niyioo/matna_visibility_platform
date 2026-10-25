import api from "./axios";

export const productionApi = {
  list: (params) => api.get("/production/entries/", { params }).then((r) => r.data),
  create: (payload) => api.post("/production/entries/", payload).then((r) => r.data),
  void: (id, reason) => api.post(`/production/entries/${id}/void/`, { reason }).then((r) => r.data),
};
