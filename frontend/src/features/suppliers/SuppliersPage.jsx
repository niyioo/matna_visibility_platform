import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { fetchSuppliersData } from "./suppliersThunks";
import PageHeader from "../../components/common/PageHeader";
import SupplierForm from "./SupplierForm";
import DeliveryForm from "./DeliveryForm";
import Card from "../../components/common/Card";
import Loader from "../../components/common/Loader";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function SuppliersPage() {
  const dispatch = useAppDispatch();
  const { suppliers, deliveries, loading } = useAppSelector((state) => state.suppliers);

  useEffect(() => {
    dispatch(fetchSuppliersData());
  }, [dispatch]);

  return (
    <div>
      <PageHeader
        title="Suppliers & Deliveries"
        subtitle="Manage supplier records and incoming cassava deliveries."
      />

      <div className="page-grid">
        <SupplierForm />
        <DeliveryForm />
      </div>

      <div className="page-grid">
        <Card title="Suppliers">
          {loading ? (
            <Loader />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Contact Person</th>
                    <th>Phone</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers.map((supplier) => (
                    <tr key={supplier.id}>
                      <td>{supplier.name}</td>
                      <td>{supplier.contact_person || "-"}</td>
                      <td>{supplier.phone || "-"}</td>
                      <td>{supplier.is_active ? "Active" : "Inactive"}</td>
                    </tr>
                  ))}
                  {suppliers.length === 0 && (
                    <tr>
                      <td colSpan="4" className="empty-cell">No suppliers found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card title="Recent Deliveries">
          {loading ? (
            <Loader />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Supplier</th>
                    <th>Quantity</th>
                    <th>Vehicle</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map((delivery) => (
                    <tr key={delivery.id}>
                      <td>{formatDate(delivery.delivery_date)}</td>
                      <td>{delivery.supplier_name}</td>
                      <td>{formatNumber(delivery.quantity_tons)} tons</td>
                      <td>{delivery.vehicle_number || "-"}</td>
                    </tr>
                  ))}
                  {deliveries.length === 0 && (
                    <tr>
                      <td colSpan="4" className="empty-cell">No deliveries found.</td>
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