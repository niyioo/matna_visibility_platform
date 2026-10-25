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
import DeliveryForm from "./DeliveryForm";
import SupplierForm from "./SupplierForm";
import { clearFormStatus, clearVoidError } from "./suppliersSlice";
import { fetchSuppliersData, voidDelivery } from "./suppliersThunks";

export default function SuppliersPage() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const { suppliers, deliveries, deliveriesCount, loading, loadError, voidingId, voidError } = useAppSelector((s) => s.suppliers);
  const [voidTarget, setVoidTarget] = useState(null);
  const canVoid = canVoidRecords(user);
  const { refreshMs } = usePlatformConfig();
  useLiveInterval(() => dispatch(fetchSuppliersData()), refreshMs);

  useEffect(() => {
    dispatch(fetchSuppliersData());
    return () => {
      dispatch(clearFormStatus("supplier"));
      dispatch(clearFormStatus("delivery"));
    };
  }, [dispatch]);

  const confirmVoid = async (reason) => {
    const result = await dispatch(voidDelivery({ id: voidTarget.id, reason }));
    if (voidDelivery.fulfilled.match(result)) setVoidTarget(null);
  };

  const activeCount = suppliers.filter((s) => s.is_active).length;

  return (
    <div>
      <PageHeader title="Suppliers & deliveries" subtitle="Manage suppliers and log incoming cassava. Deliveries add to raw stock automatically." />

      {loadError && <div className="alert error" role="alert" style={{ marginBottom: "var(--space-5)" }}>{loadError}</div>}

      <div className="page-grid">
        <SupplierForm />
        <DeliveryForm />
      </div>

      <div className="page-grid">
        <section className="card" aria-labelledby="suppliers-title">
          <div className="card-header">
            <h3 id="suppliers-title">Registered suppliers</h3>
            <span className="muted-small">{activeCount} active</span>
          </div>
          <div className="card-body no-pad">
            {loading && !suppliers.length ? <Loader /> : suppliers.length === 0 ? (
              <EmptyState title="No suppliers yet" message="Add your first supplier to start logging deliveries." />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr><th scope="col">Name</th><th scope="col">Contact</th><th scope="col">Phone</th><th scope="col">Status</th></tr>
                  </thead>
                  <tbody>
                    {suppliers.map((s) => (
                      <tr key={s.id}>
                        <td className="strong">{s.name}</td>
                        <td className="muted">{s.contact_person || "—"}</td>
                        <td className="muted nowrap">{s.phone || "—"}</td>
                        <td><span className={`badge ${s.is_active ? "badge-green" : "badge-neutral"}`}>{s.is_active ? "Active" : "Inactive"}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <section className="card" aria-labelledby="deliveries-title">
          <div className="card-header">
            <h3 id="deliveries-title">Recent deliveries</h3>
            <span className="muted-small">
              {deliveriesCount > deliveries.length ? `Latest ${deliveries.length} of ${deliveriesCount}` : `${deliveriesCount} records`}
            </span>
          </div>
          <div className="card-body no-pad">
            {loading && !deliveries.length ? <Loader /> : deliveries.length === 0 ? (
              <EmptyState title="No deliveries recorded" />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th><th scope="col">Supplier</th><th scope="col" className="num">Quantity (t)</th><th scope="col">Vehicle</th>
                      {canVoid && <th scope="col"><span className="sr-only">Actions</span></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {deliveries.map((d) => (
                      <tr key={d.id}>
                        <td className="nowrap">{formatDate(d.delivery_date)}</td>
                        <td className="strong" title={d.quality_notes || undefined}>{d.supplier_name}</td>
                        <td className="num strong">{formatNumber(d.quantity_tons)}</td>
                        <td className="muted">{d.vehicle_number || "—"}</td>
                        {canVoid && (
                          <td className="num">
                            <button className="btn btn-ghost btn-sm" onClick={() => setVoidTarget(d)} disabled={voidingId === d.id}
                              aria-label={`Void delivery from ${d.supplier_name} on ${formatDate(d.delivery_date)}`}>
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
        title="Void this delivery?"
        description={voidTarget
          ? `${formatNumber(voidTarget.quantity_tons)} t from ${voidTarget.supplier_name} (${formatDate(voidTarget.delivery_date)}) will be removed from raw cassava stock. If that cassava has already been used in production, void those production entries first.`
          : ""}
        busy={Boolean(voidingId)}
        error={voidError}
        onConfirm={confirmVoid}
        onCancel={() => { setVoidTarget(null); dispatch(clearVoidError()); }}
      />
    </div>
  );
}
