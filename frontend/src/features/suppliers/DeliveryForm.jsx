import { useMemo, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import Field from "../../components/common/Field";
import usePlatformConfig from "../../hooks/usePlatformConfig";
import { validateDelivery } from "../../utils/validation";
import { clearFormStatus } from "./suppliersSlice";
import { createDelivery, fetchSuppliersData } from "./suppliersThunks";

const EMPTY = { supplier: "", delivery_date: "", quantity_tons: "", vehicle_number: "", quality_notes: "" };

export default function DeliveryForm() {
  const dispatch = useAppDispatch();
  const suppliers = useAppSelector((s) => s.suppliers.suppliers);
  const { submitting, error, fieldErrors, success } = useAppSelector((s) => s.suppliers.forms.delivery);
  const [form, setForm] = useState(EMPTY);
  const [submitted, setSubmitted] = useState(false);
  const { today } = usePlatformConfig();

  const activeSuppliers = useMemo(() => suppliers.filter((s) => s.is_active), [suppliers]);
  const clientErrors = validateDelivery(form, { today });
  const errorFor = (name) => (submitted && clientErrors[name]) || fieldErrors[name];

  const handleChange = (e) => {
    if (error || success) dispatch(clearFormStatus("delivery"));
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitted(true);
    if (Object.keys(clientErrors).length) return;

    const result = await dispatch(createDelivery({
      ...form,
      vehicle_number: form.vehicle_number.trim().toUpperCase(),
      quality_notes: form.quality_notes.trim(),
    }));
    if (createDelivery.fulfilled.match(result)) {
      setForm(EMPTY);
      setSubmitted(false);
      dispatch(fetchSuppliersData());
    }
  };

  return (
    <section className="card" aria-labelledby="delivery-form-title">
      <div className="card-header"><h3 id="delivery-form-title">Log cassava delivery</h3></div>
      <div className="card-body">
        <form className="grid-form" onSubmit={handleSubmit} noValidate>
          <Field label="Supplier" error={errorFor("supplier")} hint={activeSuppliers.length ? undefined : "Add a supplier first"}>
            <select name="supplier" value={form.supplier} onChange={handleChange} disabled={submitting} required>
              <option value="">Select active supplier</option>
              {activeSuppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>

          <Field label="Delivery date" error={errorFor("delivery_date")}>
            <input type="date" name="delivery_date" value={form.delivery_date} onChange={handleChange} max={today} disabled={submitting} required />
          </Field>

          <Field label="Quantity (tons)" error={errorFor("quantity_tons")}>
            <input type="number" step="0.01" min="0.01" inputMode="decimal" name="quantity_tons" value={form.quantity_tons}
              onChange={handleChange} placeholder="e.g. 45.00" disabled={submitting} required />
          </Field>

          <Field label="Vehicle number" error={fieldErrors.vehicle_number}>
            <input name="vehicle_number" value={form.vehicle_number} onChange={handleChange} maxLength={50} placeholder="e.g. LND 451 AB" disabled={submitting} />
          </Field>

          <Field label="Quality notes" error={fieldErrors.quality_notes} className="full-width">
            <textarea name="quality_notes" rows={2} value={form.quality_notes} onChange={handleChange} disabled={submitting}
              placeholder="Moisture, freshness, foreign matter…" />
          </Field>

          {error && <div className="alert error full-width" role="alert">{error}</div>}
          {success && <div className="alert success full-width" role="status">{success}</div>}

          <div className="full-width">
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Log delivery"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
