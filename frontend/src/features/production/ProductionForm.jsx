import { useMemo, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { createProductionEntry, fetchProductionEntries } from "./productionThunks";
import { clearProductionMessage } from "./productionSlice";
import Card from "../../components/common/Card";
import FormInput from "../../components/common/FormInput";

export default function ProductionForm() {
  const dispatch = useAppDispatch();
  const { loading, error, successMessage } = useAppSelector((state) => state.production);

  const [form, setForm] = useState({
    production_date: "",
    cassava_inflow_tons: "",
    starch_output_tons: "",
    downtime_minutes: "",
    notes: ""
  });

  const yieldPreview = useMemo(() => {
    const inflow = Number(form.cassava_inflow_tons || 0);
    const output = Number(form.starch_output_tons || 0);
    if (!inflow) return "0.00";
    return ((output / inflow) * 100).toFixed(2);
  }, [form.cassava_inflow_tons, form.starch_output_tons]);

  const handleChange = (e) => {
    dispatch(clearProductionMessage());
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const resultAction = await dispatch(createProductionEntry(form));
    if (createProductionEntry.fulfilled.match(resultAction)) {
      setForm({
        production_date: "",
        cassava_inflow_tons: "",
        starch_output_tons: "",
        downtime_minutes: "",
        notes: ""
      });
      dispatch(fetchProductionEntries());
    }
  };

  return (
    <Card title="New Production Entry">
      <form className="grid-form" onSubmit={handleSubmit}>
        <FormInput
          label="Production Date"
          type="date"
          name="production_date"
          value={form.production_date}
          onChange={handleChange}
          required
        />
        <FormInput
          label="Cassava Inflow (tons)"
          type="number"
          step="0.01"
          name="cassava_inflow_tons"
          value={form.cassava_inflow_tons}
          onChange={handleChange}
          required
        />
        <FormInput
          label="Starch Output (tons)"
          type="number"
          step="0.01"
          name="starch_output_tons"
          value={form.starch_output_tons}
          onChange={handleChange}
          required
        />
        <FormInput
          label="Downtime (minutes)"
          type="number"
          name="downtime_minutes"
          value={form.downtime_minutes}
          onChange={handleChange}
          required
        />

        <div className="form-group full-width">
          <label>Yield Preview</label>
          <div className="preview-box">{yieldPreview}%</div>
        </div>

        <div className="form-group full-width">
          <label>Notes</label>
          <textarea
            name="notes"
            rows="4"
            value={form.notes}
            onChange={handleChange}
            placeholder="Optional operational notes"
          />
        </div>

        {error && <div className="alert error full-width">{error}</div>}
        {successMessage && <div className="alert success full-width">{successMessage}</div>}

        <div className="full-width">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Saving..." : "Save Production Entry"}
          </button>
        </div>
      </form>
    </Card>
  );
}