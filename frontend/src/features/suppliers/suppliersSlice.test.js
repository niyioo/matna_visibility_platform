import { describe, expect, it } from "vitest";
import reducer from "./suppliersSlice";
import { createDelivery, createSupplier } from "./suppliersThunks";

describe("suppliers slice", () => {
  it("keeps each form's feedback separate", () => {
    let state = reducer(undefined, { type: "init" });
    state = reducer(state, createSupplier.rejected(null, "req1", {}, { message: "A supplier with this name already exists.", fieldErrors: { name: "Duplicate" } }));
    state = reducer(state, createDelivery.fulfilled({ quantity_tons: "40.00", supplier_name: "Adeola" }, "req2", {}));

    expect(state.forms.supplier.error).toBe("A supplier with this name already exists.");
    expect(state.forms.supplier.fieldErrors).toEqual({ name: "Duplicate" });
    expect(state.forms.delivery.error).toBeNull();
    expect(state.forms.delivery.success).toMatch(/40.00 t from Adeola/);
  });

  it("tracks submitting per form", () => {
    const state = reducer(undefined, createDelivery.pending("req", {}));
    expect(state.forms.delivery.submitting).toBe(true);
    expect(state.forms.supplier.submitting).toBe(false);
  });
});
