import api from "./axios";

export const inventoryApi = {
  getBalances: async () => {
    const response = await api.get("/inventory/balances/");
    return response.data;
  },

  getTransactions: async () => {
    const response = await api.get("/inventory/transactions/");
    return response.data;
  }
};