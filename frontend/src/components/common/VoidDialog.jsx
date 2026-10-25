import { useEffect, useRef, useState } from "react";
import usePlatformConfig from "../../hooks/usePlatformConfig";

/**
 * Confirmation dialog for voiding a record. Voiding reverses stock, so a
 * written reason is required and becomes part of the audit trail.
 */
export default function VoidDialog({ open, title, description, busy, error, onConfirm, onCancel }) {
  const [reason, setReason] = useState("");
  const dialogRef = useRef(null);
  const { limits } = usePlatformConfig();
  const minLength = limits?.reason_min_length ?? 1;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setReason("");
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  const valid = Boolean(limits) && reason.trim().length >= minLength;

  return (
    <dialog ref={dialogRef} className="dialog" onCancel={(e) => { e.preventDefault(); if (!busy) onCancel(); }}>
      <form
        method="dialog"
        onSubmit={(e) => {
          e.preventDefault();
          if (valid && !busy) onConfirm(reason.trim());
        }}
      >
        <h3 className="dialog-title">{title}</h3>
        <p className="dialog-text">{description}</p>

        <div className="form-group">
          <label htmlFor="void-reason">Reason (required{limits ? `, at least ${minLength} characters` : ""})</label>
          <textarea
            id="void-reason"
            rows={3}
            value={reason}
            maxLength={limits?.reason_max_length}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Weighbridge ticket entered twice"
            autoFocus
          />
        </div>

        {error && <div className="alert error" role="alert" style={{ marginTop: "var(--space-3)" }}>{error}</div>}

        <div className="dialog-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={busy}>Cancel</button>
          <button type="submit" className="btn btn-danger" disabled={!valid || busy}>
            {busy ? "Voiding…" : "Void and reverse stock"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
