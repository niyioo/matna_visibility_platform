import api from "./axios";

/** Drop empty values so the backend applies its defaults. */
const clean = (params = {}) =>
  Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""));

export const analyticsApi = {
  /** Thresholds, windows, limits, periods and refresh cadence. */
  getConfig: () => api.get("/analytics/config/").then((r) => r.data),

  getDashboard: (config) => api.get("/analytics/dashboard/", config).then((r) => r.data),

  getSummary: (params, config) =>
    api.get("/analytics/summary/", { ...config, params: clean(params) }).then((r) => r.data),

  /** All daily series + anomaly flags in one request (defaults to the configured trend window). */
  getTrends: (params, config) =>
    api.get("/analytics/trends/", { ...config, params: clean(params) }).then((r) => r.data),

  downloadReport: (type, params) =>
    api.get(`/analytics/reports/export/${type}/`, { params: clean(params), responseType: "blob", timeout: 60000 }),
};
