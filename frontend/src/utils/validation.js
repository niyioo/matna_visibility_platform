/*
 * Client-side mirrors of the API's input rules, for instant feedback. The
 * limits are passed in from the live platform config (GET /api/analytics/config/);
 * the API remains the authority.
 */

const isNumber = (value) => value !== "" && value !== null && value !== undefined && Number.isFinite(Number(value));

export function validateProductionEntry(form, { today, maxDowntimeMinutes }) {
  const errors = {};
  const inflow = Number(form.cassava_inflow_tons);
  const output = Number(form.starch_output_tons);
  const downtime = Number(form.downtime_minutes);

  if (!form.production_date) errors.production_date = "Production date is required.";
  else if (today && form.production_date > today) errors.production_date = "Production date cannot be in the future.";

  if (!isNumber(form.cassava_inflow_tons)) errors.cassava_inflow_tons = "Enter the cassava inflow in tons.";
  else if (inflow <= 0) errors.cassava_inflow_tons = "Cassava inflow must be greater than zero.";

  if (!isNumber(form.starch_output_tons)) errors.starch_output_tons = "Enter the starch output in tons (0 if none).";
  else if (output < 0) errors.starch_output_tons = "Starch output cannot be negative.";
  else if (isNumber(form.cassava_inflow_tons) && output > inflow)
    errors.starch_output_tons = "Starch output cannot exceed cassava inflow.";

  if (form.downtime_minutes !== "" && form.downtime_minutes !== undefined) {
    if (!Number.isInteger(downtime) || downtime < 0) errors.downtime_minutes = "Downtime must be a whole number of minutes.";
    else if (maxDowntimeMinutes != null && downtime > maxDowntimeMinutes)
      errors.downtime_minutes = `Downtime cannot exceed ${maxDowntimeMinutes} minutes in one day.`;
  }

  return errors;
}

/** Yield preview, or null when it can't be computed yet. */
export function previewYield(inflowValue, outputValue) {
  const inflow = Number(inflowValue);
  const output = Number(outputValue);
  if (!isNumber(inflowValue) || !isNumber(outputValue) || inflow <= 0) return null;
  return (output / inflow) * 100;
}

export function toProductionPayload(form) {
  return {
    production_date: form.production_date,
    cassava_inflow_tons: form.cassava_inflow_tons,
    starch_output_tons: form.starch_output_tons,
    downtime_minutes: form.downtime_minutes === "" ? 0 : Number(form.downtime_minutes),
    notes: form.notes?.trim() ?? "",
  };
}

export function validateDelivery(form, { today }) {
  const errors = {};
  if (!form.supplier) errors.supplier = "Select a supplier.";
  if (!form.delivery_date) errors.delivery_date = "Delivery date is required.";
  else if (today && form.delivery_date > today) errors.delivery_date = "Delivery date cannot be in the future.";
  if (!isNumber(form.quantity_tons) || Number(form.quantity_tons) <= 0)
    errors.quantity_tons = "Quantity must be greater than zero.";
  return errors;
}
