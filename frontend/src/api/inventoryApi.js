import api from "./axios";

export const inventoryApi = {
  getBalances: () => api.get("/inventory/balances/").then((r) => r.data),
  getTransactions: (params) => api.get("/inventory/transactions/", { params }).then((r) => r.data),
  getReconciliation: () => api.get("/inventory/reconciliation/").then((r) => r.data),
};
