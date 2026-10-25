import { useEffect, useRef } from "react";

/**
 * Calls `callback` every `intervalMs` while the tab is visible, and once
 * immediately when a hidden tab becomes visible again. No-op without an interval.
 */
export default function useLiveInterval(callback, intervalMs) {
  const saved = useRef(callback);
  saved.current = callback;

  useEffect(() => {
    if (!intervalMs) return undefined;
    const visible = () => document.visibilityState !== "hidden";
    const tick = () => visible() && saved.current();
    const timer = setInterval(tick, intervalMs);
    document.addEventListener("visibilitychange", tick);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [intervalMs]);
}
