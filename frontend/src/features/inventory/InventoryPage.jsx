import { useState } from "react";
import { inventoryApi } from "../../api/inventoryApi";
import { useAppSelector } from "../../app/hooks";
import EmptyState from "../../components/common/EmptyState";
import Loader from "../../components/common/Loader";
import PageHeader from "../../components/common/PageHeader";
import LiveStatus from "../../components/common/LiveStatus";
import useApiData from "../../hooks/useApiData";
import usePlatformConfig from "../../hooks/usePlatformConfig";
import { getErrorMessage } from "../../utils/errors";
import { formatDate, formatDateTime, formatNumber } from "../../utils/formatters";
import { isAdmin } from "../../utils/permissions";

const TX_BADGE = {
  IN: { cls: "badge-green", label: "IN" },
  OUT: { cls: "badge-red", label: "OUT" },
  ADJUSTMENT: { cls: "badge-amber", label: "ADJ" },
};

const REF_LABEL = {
  SUPPLIER_DELIVERY: "Supplier delivery",
  PRODUCTION_ENTRY: "Production entry",
  MANUAL_ADJUSTMENT: "Manual adjustment",
};

function IntegrityCheck() {
  const [state, setState] = useState({ loading: false, report: null, error: "" });

  const run = async () => {
    setState({ loading: true, report: null, error: "" });
    try {
      setState({ loading: false, report: await inventoryApi.getReconciliation(), error: "" });
    } catch (error) {
      setState({ loading: false, report: null, error: getErrorMessage(error, "Integrity check failed.") });
    }
  };

  const { report } = state;
  return (
    <section className="card" aria-labelledby="integrity-title" style={{ marginBottom: "var(--space-5)" }}>
      <div className="card-header">
        <h3 id="integrity-title">Stock integrity check</h3>
        <button className="btn btn-ghost btn-sm" onClick={run} disabled={state.loading}>
          {state.loading ? "Checking…" : "Run check"}
        </button>
      </div>
      <div className="card-body">
        {!report && !state.error && (
          <p className="muted-small">Verifies that stock balances, the movement ledger, and every delivery and production entry agree.</p>
        )}
        {state.error && <div className="alert error" role="alert">{state.error}</div>}
        {report?.is_consistent && <div className="alert success" role="status">All balances, ledger entries and source documents reconcile.</div>}
        {report && !report.is_consistent && (
          <>
            <div className="alert warning" role="alert">
              {report.issue_count} discrepanc{report.issue_count === 1 ? "y" : "ies"} found. Review with the system administrator
              (<code>manage.py reconcile_inventory</code>).
            </div>
            <ul className="issue-list">
              {report.issues.map((issue, i) => (
                <li key={i}>
                  <span className="badge badge-amber">{issue.type.replace(/_/g, " ")}</span>{" "}
                  {issue.document || issue.item_code || issue.reference_id}
                  {issue.detail && <span className="muted"> — {issue.detail}</span>}
                  {issue.differences && Object.entries(issue.differences).map(([code, d]) => (
                    <span key={code} className="muted"> — {code}: expected {d.expected}, ledger {d.ledger}</span>
                  ))}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}

export default function InventoryPage() {
  const user = useAppSelector((s) => s.auth.user);
  const { refreshMs } = usePlatformConfig();
  const { data, loading, error, updatedAt, reload } = useApiData(
    () => Promise.all([inventoryApi.getBalances(), inventoryApi.getTransactions()]),
    [],
    { fallbackError: "Failed to load inventory data.", refreshMs }
  );

  const [balancesData, txData] = data ?? [[], { results: [], count: 0 }];
  const balances = Array.isArray(balancesData) ? balancesData : balancesData.results ?? [];
  const transactions = Array.isArray(txData) ? txData : txData.results ?? [];
  const txCount = txData.count ?? transactions.length;

  return (
    <div>
      <div className="page-toolbar">
        <PageHeader title="Inventory" subtitle="Current stock and the complete, append-only movement ledger." />
        <LiveStatus updatedAt={updatedAt} refreshMs={refreshMs} loading={loading} error={error} onRefresh={reload} />
      </div>

      {error && <div className="alert error" role="alert" style={{ marginBottom: "var(--space-5)" }}>{error}</div>}

      {loading && !data ? <Loader text="Loading inventory…" /> : (
        <>
          <div className="kpi-grid">
            {balances.map((b) => (
              <div key={b.id} className="kpi-card">
                <p className="kpi-label">{b.item?.name}</p>
                <div className="kpi-value-row">
                  <span className="kpi-value">{formatNumber(b.quantity_on_hand)}</span>
                  <span className="kpi-suffix">{b.item?.unit}</span>
                </div>
                <span className="kpi-hint">Updated {formatDateTime(b.last_updated_at)}</span>
              </div>
            ))}
          </div>

          {isAdmin(user) && <IntegrityCheck />}

          <section className="card" aria-labelledby="ledger-title">
            <div className="card-header">
              <h3 id="ledger-title">Stock movement ledger</h3>
              <span className="muted-small">{txCount > transactions.length ? `Latest ${transactions.length} of ${txCount}` : `${txCount} records`}</span>
            </div>
            <div className="card-body no-pad">
              {transactions.length === 0 ? <EmptyState title="No stock movements yet" /> : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Date</th><th scope="col">Item</th><th scope="col">Type</th>
                        <th scope="col" className="num">Qty (t)</th><th scope="col" className="num">Balance after</th>
                        <th scope="col">Source</th><th scope="col">Notes</th><th scope="col">By</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx) => {
                        const badge = TX_BADGE[tx.transaction_type] ?? { cls: "badge-neutral", label: tx.transaction_type };
                        return (
                          <tr key={tx.id} className={tx.is_reversed ? "row-muted" : undefined}>
                            <td className="nowrap">{formatDate(tx.transaction_date)}</td>
                            <td className="strong">{tx.item_name}</td>
                            <td>
                              <span className={`badge ${badge.cls}`}>{badge.label}</span>
                              {tx.is_reversal && <span className="badge badge-neutral" style={{ marginLeft: 4 }}>reversal</span>}
                              {tx.is_reversed && <span className="badge badge-neutral" style={{ marginLeft: 4 }}>reversed</span>}
                            </td>
                            <td className="num strong">{formatNumber(tx.quantity)}</td>
                            <td className="num muted">{tx.balance_after != null ? formatNumber(tx.balance_after) : "—"}</td>
                            <td><span className="badge badge-neutral">{REF_LABEL[tx.reference_type] ?? tx.reference_type}</span></td>
                            <td className="muted small-text cell-notes">{tx.notes || "—"}</td>
                            <td className="muted small-text">{tx.created_by_name}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
