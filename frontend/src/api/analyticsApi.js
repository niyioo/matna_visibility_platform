import api from "./axios";

const buildQuery = (params = {}) => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, value);
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
};

export const analyticsApi = {
  getDashboard: async () => {
    const response = await api.get("/analytics/dashboard/");
    return response.data;
  },

  getSummary: async (period = "daily", params = {}) => {
    const response = await api.get(
      `/analytics/summary/${buildQuery({ period, ...params })}`
    );
    return response.data;
  },

  getYieldTrend: async (params = {}) => {
    const response = await api.get(
      `/analytics/yield-trend/${buildQuery(params)}`
    );
    return response.data;
  },

  getInflowVsOutput: async (params = {}) => {
    const response = await api.get(
      `/analytics/inflow-vs-output/${buildQuery(params)}`
    );
    return response.data;
  },

  getDowntimeTrend: async (params = {}) => {
    const response = await api.get(
      `/analytics/downtime-trend/${buildQuery(params)}`
    );
    return response.data;
  }
};