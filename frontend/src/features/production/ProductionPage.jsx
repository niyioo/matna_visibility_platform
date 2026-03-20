import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { fetchProductionEntries } from "./productionThunks";
import PageHeader from "../../components/common/PageHeader";
import ProductionForm from "./ProductionForm";
import Loader from "../../components/common/Loader";
import Card from "../../components/common/Card";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function ProductionPage() {
  const dispatch = useAppDispatch();
  const { entries, loading } = useAppSelector((state) => state.production);

  useEffect(() => {
    dispatch(fetchProductionEntries());
  }, [dispatch]);

  return (
    <div>
      <PageHeader
        title="Production Tracking"
        subtitle="Capture daily production activity and computed yield."
      />

      <div className="page-grid">
        <ProductionForm />

        <Card title="Production Entries">
          {loading ? (
            <Loader />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Inflow</th>
                    <th>Output</th>
                    <th>Yield</th>
                    <th>Downtime</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id}>
                      <td>{formatDate(entry.production_date)}</td>
                      <td>{formatNumber(entry.cassava_inflow_tons)} tons</td>
                      <td>{formatNumber(entry.starch_output_tons)} tons</td>
                      <td>{formatNumber(entry.yield_percent)}%</td>
                      <td>{formatNumber(entry.downtime_minutes)} min</td>
                    </tr>
                  ))}
                  {entries.length === 0 && (
                    <tr>
                      <td colSpan="5" className="empty-cell">No production entries found.</td>
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