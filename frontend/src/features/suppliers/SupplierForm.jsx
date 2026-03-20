import { useState } from "react";
import { useAppDispatch } from "../../app/hooks";
import { createSupplier, fetchSuppliersData } from "./suppliersThunks";
import Card from "../../components/common/Card";
import FormInput from "../../components/common/FormInput";

export default function SupplierForm() {
  const dispatch = useAppDispatch();

  const [form, setForm] = useState({
    name: "",
    contact_person: "",
    phone: "",
    address: "",
    notes: ""
  });

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(createSupplier(form));
    if (createSupplier.fulfilled.match(result)) {
      setForm({
        name: "",
        contact_person: "",
        phone: "",
        address: "",
        notes: ""
      });
      dispatch(fetchSuppliersData());
    }
  };

  return (
    <Card title="Add Supplier">
      <form className="grid-form" onSubmit={handleSubmit}>
        <FormInput label="Supplier Name" name="name" value={form.name} onChange={handleChange} required />
        <FormInput label="Contact Person" name="contact_person" value={form.contact_person} onChange={handleChange} />
        <FormInput label="Phone" name="phone" value={form.phone} onChange={handleChange} />

        <div className="form-group full-width">
          <label>Address</label>
          <textarea name="address" rows="3" value={form.address} onChange={handleChange} />
        </div>

        <div className="form-group full-width">
          <label>Notes</label>
          <textarea name="notes" rows="3" value={form.notes} onChange={handleChange} />
        </div>

        <div className="full-width">
          <button className="btn btn-primary" type="submit">Save Supplier</button>
        </div>
      </form>
    </Card>
  );
}