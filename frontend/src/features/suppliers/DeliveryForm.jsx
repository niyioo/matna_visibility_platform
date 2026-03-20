import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { createDelivery, fetchSuppliersData } from "./suppliersThunks";
import Card from "../../components/common/Card";
import FormInput from "../../components/common/FormInput";

export default function DeliveryForm() {
  const dispatch = useAppDispatch();
  const { suppliers } = useAppSelector((state) => state.suppliers);

  const [form, setForm] = useState({
    supplier: "",
    delivery_date: "",
    quantity_tons: "",
    quality_notes: "",
    vehicle_number: ""
  });

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(createDelivery(form));
    if (createDelivery.fulfilled.match(result)) {
      setForm({
        supplier: "",
        delivery_date: "",
        quantity_tons: "",
        quality_notes: "",
        vehicle_number: ""
      });
      dispatch(fetchSuppliersData());
    }
  };

  return (
    <Card title="Log Supplier Delivery">
      <form className="grid-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Supplier</label>
          <select name="supplier" value={form.supplier} onChange={handleChange} required>
            <option value="">Select supplier</option>
            {suppliers.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>
                {supplier.name}
              </option>
            ))}
          </select>
        </div>

        <FormInput
          label="Delivery Date"
          type="date"
          name="delivery_date"
          value={form.delivery_date}
          onChange={handleChange}
          required
        />

        <FormInput
          label="Quantity (tons)"
          type="number"
          step="0.01"
          name="quantity_tons"
          value={form.quantity_tons}
          onChange={handleChange}
          required
        />

        <FormInput
          label="Vehicle Number"
          name="vehicle_number"
          value={form.vehicle_number}
          onChange={handleChange}
        />

        <div className="form-group full-width">
          <label>Quality Notes</label>
          <textarea
            name="quality_notes"
            rows="3"
            value={form.quality_notes}
            onChange={handleChange}
          />
        </div>

        <div className="full-width">
          <button className="btn btn-primary" type="submit">Save Delivery</button>
        </div>
      </form>
    </Card>
  );
}