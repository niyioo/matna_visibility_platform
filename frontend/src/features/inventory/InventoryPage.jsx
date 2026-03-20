import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/common/Card";
import Loader from "../../components/common/Loader";
import { inventoryApi } from "../../api/inventoryApi";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function InventoryPage() {
  const [balances, setBalances] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadInventory = async () => {
      try {
        const [balancesData, transactionsData] = await Promise.all([
          inventoryApi.getBalances(),
          inventoryApi.getTransactions()
        ]);

        setBalances(balancesData.results || balancesData);
        setTransactions(transactionsData.results || transactionsData);
      } finally {
        setLoading(false);
      }
    };

    loadInventory();
  }, []);

  return (
    <div>
      <PageHeader
        title="Inventory"
        subtitle="Track current stock balances and audit stock movements."
      />

      <div className="page-grid">
        <Card title="Current Balances">
          {loading ? (
            <Loader />
          ) : (
            <div className="stats-grid">
              {balances.map((balance) => (
                <div key={balance.id} className="stat-card">
                  <span className="stat-label">{balance.item.name}</span>
                  <strong className="stat-value">{formatNumber(balance.quantity_on_hand)} {balance.item.unit}</strong>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Inventory Transactions">
          {loading ? (
            <Loader />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Item</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td>{formatDate(tx.transaction_date)}</td>
                      <td>{tx.item_name}</td>
                      <td>{tx.transaction_type}</td>
                      <td>{formatNumber(tx.quantity)}</td>
                      <td>{tx.reference_type}</td>
                    </tr>
                  ))}
                  {transactions.length === 0 && (
                    <tr>
                      <td colSpan="5" className="empty-cell">No inventory transactions found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}