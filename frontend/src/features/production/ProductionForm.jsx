import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import Field from "../../components/common/Field";
import usePlatformConfig from "../../hooks/usePlatformConfig";
import { previewYield, toProductionPayload, validateProductionEntry } from "../../utils/validation";
import { clearProductionMessage } from "./productionSlice";
import { createProductionEntry, fetchProductionEntries } from "./productionThunks";

const EMPTY_FORM = {
  production_date: "",
  cassava_inflow_tons: "",
  starch_output_tons: "",
  downtime_minutes: "",
  notes: "",
};

export default function ProductionForm() {
  const dispatch = useAppDispatch();
  const { ready, thresholds, limits, today } = usePlatformConfig();
  const { submitting, submitError, fieldErrors: serverErrors, successMessage } = useAppSelector((s) => s.production);

  const [form, setForm] = useState(EMPTY_FORM);
  const [touched, setTouched] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const clientErrors = validateProductionEntry(form, { today, maxDowntimeMinutes: limits?.max_downtime_minutes });
  const showError = (name) => (submitted || touched[name]) && clientErrors[name];
  const errorFor = (name) => showError(name) || serverErrors[name];

  const yieldValue = previewYield(form.cassava_inflow_tons, form.starch_output_tons);
  const yieldTarget = thresholds?.yield_target_percent;
  const yieldCritical = thresholds?.yield_critical_percent;
  const yieldMaxPlausible = thresholds?.yield_max_plausible_percent;
  const yieldTone =
    yieldValue == null || !thresholds ? ""
    : yieldValue > yieldMaxPlausible ? "implausible"
    : yieldValue >= yieldTarget ? "good"
    : yieldValue >= yieldCritical ? "warn"
    : "bad";

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (submitError || successMessage) dispatch(clearProductionMessage());
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleBlur = (e) => setTouched((t) => ({ ...t, [e.target.name]: true }));

  const reset = () => {
    setForm(EMPTY_FORM);
    setTouched({});
    setSubmitted(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting || !ready) return; // guard against double submission
    setSubmitted(true);
    if (Object.keys(clientErrors).length) return;

    const result = await dispatch(createProductionEntry(toProductionPayload(form)));
    if (createProductionEntry.fulfilled.match(result)) {
      reset();
      dispatch(fetchProductionEntries());
    }
  };

  const input = (name, props) => (
    <input name={name} value={form[name]} onChange={handleChange} onBlur={handleBlur} disabled={submitting} {...props} />
  );

  return (
    <section className="card" aria-labelledby="production-form-title">
      <div className="card-header"><h3 id="production-form-title">New production entry</h3></div>
      <div className="card-body">
        <form className="grid-form" onSubmit={handleSubmit} noValidate>
          <Field label="Production date" error={errorFor("production_date")}>
            {input("production_date", { type: "date", max: today, required: true })}
          </Field>

          <Field label="Downtime (minutes)" error={errorFor("downtime_minutes")} hint="Leave blank if none">
            {input("downtime_minutes", { type: "number", min: 0, max: limits?.max_downtime_minutes, step: 1, inputMode: "numeric", placeholder: "0" })}
          </Field>

          <Field label="Cassava inflow (tons)" error={errorFor("cassava_inflow_tons")}>
            {input("cassava_inflow_tons", { type: "number", min: 0, step: "0.01", inputMode: "decimal", placeholder: "e.g. 120.00", required: true })}
          </Field>

          <Field label="Starch output (tons)" error={errorFor("starch_output_tons")}>
            {input("starch_output_tons", { type: "number", min: 0, step: "0.01", inputMode: "decimal", placeholder: "e.g. 34.00", required: true })}
          </Field>

          <div className="form-group full-width">
            <span className="form-label">Estimated yield</span>
            <div className={`preview-box ${yieldTone === "implausible" ? "bad" : yieldTone}`} aria-live="polite">
              {yieldValue == null ? "—" : `${yieldValue.toFixed(2)}%`}
              {yieldTone === "bad" && <span className="preview-note">Below the {yieldCritical}% critical threshold — check the figures</span>}
              {yieldTone === "warn" && <span className="preview-note">Below the {yieldTarget}% target</span>}
              {yieldTone === "implausible" && (
                <span className="preview-note">Unusually high (above {yieldMaxPlausible}%) — double-check inflow and output</span>
              )}
            </div>
          </div>

          <Field label="Operational notes" error={errorFor("notes")} className="full-width">
            <textarea
              name="notes"
              rows={3}
              maxLength={2000}
              value={form.notes}
              onChange={handleChange}
              disabled={submitting}
              placeholder="Optional — stoppages, quality observations, shift remarks."
            />
          </Field>

          {submitError && <div className="alert error full-width" role="alert">{submitError}</div>}
          {successMessage && <div className="alert success full-width" role="status">{successMessage}</div>}

          <div className="full-width actions-row">
            <button type="submit" className="btn btn-primary" disabled={submitting || !ready}>
              {submitting ? "Saving…" : "Save production entry"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => { reset(); dispatch(clearProductionMessage()); }} disabled={submitting}>
              Clear
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
