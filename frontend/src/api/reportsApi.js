const API_BASE = import.meta.env.VITE_API_BASE_URL;

export const reportsApi = {
  csvUrl: (period = "daily") => `${API_BASE}/analytics/reports/export/csv/?period=${period}`,
  pdfUrl: (period = "daily") => `${API_BASE}/analytics/reports/export/pdf/?period=${period}`
};