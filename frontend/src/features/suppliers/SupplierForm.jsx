import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import Field from "../../components/common/Field";
import { clearFormStatus } from "./suppliersSlice";
import { createSupplier, fetchSuppliersData } from "./suppliersThunks";

const EMPTY = { name: "", contact_person: "", phone: "", address: "", notes: "" };

export default function SupplierForm() {
  const dispatch = useAppDispatch();
  const { submitting, error, fieldErrors, success } = useAppSelector((s) => s.suppliers.forms.supplier);
  const [form, setForm] = useState(EMPTY);
  const [submitted, setSubmitted] = useState(false);

  const nameError = submitted && !form.name.trim() ? "Supplier name is required." : fieldErrors.name;

  const handleChange = (e) => {
    if (error || success) dispatch(clearFormStatus("supplier"));
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitted(true);
    if (!form.name.trim()) return;

    const payload = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v.trim()]));
    const result = await dispatch(createSupplier(payload));
    if (createSupplier.fulfilled.match(result)) {
      setForm(EMPTY);
      setSubmitted(false);
      dispatch(fetchSuppliersData());
    }
  };

  const input = (name, props = {}) => (
    <input name={name} value={form[name]} onChange={handleChange} disabled={submitting} {...props} />
  );

  return (
    <section className="card" aria-labelledby="supplier-form-title">
      <div className="card-header"><h3 id="supplier-form-title">Add supplier</h3></div>
      <div className="card-body">
        <form className="grid-form" onSubmit={handleSubmit} noValidate>
          <Field label="Supplier name" error={nameError}>{input("name", { maxLength: 150, placeholder: "e.g. Olusegun Farms", required: true })}</Field>
          <Field label="Contact person" error={fieldErrors.contact_person}>{input("contact_person", { maxLength: 150, placeholder: "Full name" })}</Field>
          <Field label="Phone number" error={fieldErrors.phone}>{input("phone", { type: "tel", maxLength: 30, placeholder: "+234 …" })}</Field>
          <Field label="Address" error={fieldErrors.address}>{input("address", { placeholder: "Town / LGA" })}</Field>
          <Field label="Notes" error={fieldErrors.notes} className="full-width">
            <textarea name="notes" rows={2} value={form.notes} onChange={handleChange} disabled={submitting} placeholder="Optional remarks" />
          </Field>

          {error && <div className="alert error full-width" role="alert">{error}</div>}
          {success && <div className="alert success full-width" role="status">{success}</div>}

          <div className="full-width">
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Save supplier"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
