import { useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import EmptyState from "../../components/common/EmptyState";
import Loader from "../../components/common/Loader";
import PageHeader from "../../components/common/PageHeader";
import VoidDialog from "../../components/common/VoidDialog";
import useLiveInterval from "../../hooks/useLiveInterval";
import usePlatformConfig from "../../hooks/usePlatformConfig";
import { formatDate, formatNumber } from "../../utils/formatters";
import { canVoidRecords } from "../../utils/permissions";
import ProductionForm from "./ProductionForm";
import { clearProductionMessage } from "./productionSlice";
import { fetchProductionEntries, voidProductionEntry } from "./productionThunks";

function YieldBadge({ value, thresholds }) {
  const n = Number(value);
  const tone = !thresholds ? "badge-neutral"
    : n > thresholds.yield_max_plausible_percent ? "badge-red"
    : n >= thresholds.yield_target_percent ? "badge-green"
    : n >= thresholds.yield_critical_percent ? "badge-amber"
    : "badge-red";
  const title = thresholds && n > thresholds.yield_max_plausible_percent ? "Implausibly high — check the figures" : undefined;
  return <span className={`badge ${tone}`} title={title}>{formatNumber(value)}%</span>;
}

function DowntimeBadge({ minutes, thresholds }) {
  if (!minutes) return <span className="badge badge-green">None</span>;
  const tone = !thresholds ? "badge-neutral"
    : minutes >= thresholds.downtime_critical_minutes ? "badge-red"
    : minutes >= thresholds.downtime_warning_minutes ? "badge-amber"
    : "badge-neutral";
  return <span className={`badge ${tone}`}>{minutes} min</span>;
}

export default function ProductionPage() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const { entries, count, loading, loadError, voidingId, voidError } = useAppSelector((s) => s.production);
  const [voidTarget, setVoidTarget] = useState(null);
  const canVoid = canVoidRecords(user);
  const { thresholds, refreshMs } = usePlatformConfig();
  useLiveInterval(() => dispatch(fetchProductionEntries()), refreshMs);

  useEffect(() => {
    dispatch(fetchProductionEntries());
    return () => dispatch(clearProductionMessage());
  }, [dispatch]);

  const confirmVoid = async (reason) => {
    const result = await dispatch(voidProductionEntry({ id: voidTarget.id, reason }));
    if (voidProductionEntry.fulfilled.match(result)) setVoidTarget(null);
  };

  return (
    <div>
      <PageHeader title="Production tracking" subtitle="Record daily production. Stock is updated automatically." />

      <div className="page-grid form-and-table">
        <ProductionForm />

        <section className="card" aria-labelledby="production-log-title">
          <div className="card-header">
            <h3 id="production-log-title">Production log</h3>
            <span className="muted-small">
              {count > entries.length ? `Latest ${entries.length} of ${count}` : `${count} entries`}
            </span>
          </div>
          <div className="card-body no-pad">
            {loadError && <div className="alert error" role="alert" style={{ margin: "var(--space-4)" }}>{loadError}</div>}
            {loading && !entries.length ? (
              <Loader text="Loading entries…" />
            ) : entries.length === 0 && !loadError ? (
              <EmptyState title="No production entries yet" message="Use the form to record the first production day." />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col" className="num">Inflow (t)</th>
                      <th scope="col" className="num">Output (t)</th>
                      <th scope="col">Yield</th>
                      <th scope="col">Downtime</th>
                      {canVoid && <th scope="col"><span className="sr-only">Actions</span></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e) => (
                      <tr key={e.id}>
                        <td className="nowrap strong" title={e.notes || undefined}>{formatDate(e.production_date)}</td>
                        <td className="num">{formatNumber(e.cassava_inflow_tons)}</td>
                        <td className="num">{formatNumber(e.starch_output_tons)}</td>
                        <td><YieldBadge value={e.yield_percent} thresholds={thresholds} /></td>
                        <td><DowntimeBadge minutes={e.downtime_minutes} thresholds={thresholds} /></td>
                        {canVoid && (
                          <td className="num">
                            <button
                              className="btn btn-ghost btn-sm"
                              onClick={() => setVoidTarget(e)}
                              disabled={voidingId === e.id}
                              aria-label={`Void entry for ${formatDate(e.production_date)}`}
                            >
                              Void
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </div>

      <VoidDialog
        open={Boolean(voidTarget)}
        title={`Void production entry for ${voidTarget ? formatDate(voidTarget.production_date) : ""}?`}
        description={voidTarget
          ? `This reverses ${formatNumber(voidTarget.cassava_inflow_tons)} t of cassava consumption and ${formatNumber(voidTarget.starch_output_tons)} t of starch output. The entry stays in the audit log and a corrected entry can then be recorded for the same date.`
          : ""}
        busy={Boolean(voidingId)}
        error={voidError}
        onConfirm={confirmVoid}
        onCancel={() => { setVoidTarget(null); dispatch(clearProductionMessage()); }}
      />
    </div>
  );
}
