import { useAppSelector } from "../app/hooks";
import { todayISO } from "../utils/formatters";

/**
 * Live platform settings from the backend. `ready` is false until the first
 * load; callers should render a loader (or disable inputs) until then rather
 * than fall back to made-up numbers.
 */
export default function usePlatformConfig() {
  const config = useAppSelector((s) => s.config.data);
  const error = useAppSelector((s) => s.config.error);

  return {
    ready: Boolean(config),
    error,
    config,
    thresholds: config?.thresholds,
    limits: config?.limits,
    windows: config?.windows,
    periods: config?.periods ?? [],
    refreshMs: config ? config.live_refresh_seconds * 1000 : null,
    // The plant's date (server timezone), falling back to the device date only
    // until the config has loaded.
    today: config?.server_date ?? todayISO(),
  };
}
