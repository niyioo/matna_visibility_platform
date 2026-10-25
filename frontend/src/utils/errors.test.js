import { describe, expect, it } from "vitest";
import { getErrorMessage, getFieldErrors, parseBlobError } from "./errors";

const apiError = (status, data) => ({ response: { status, data } });

describe("getErrorMessage", () => {
  it("uses the API envelope's detail", () => {
    expect(getErrorMessage(apiError(400, { error: true, code: "insufficient_stock", detail: "Insufficient stock for 'Raw Cassava'." })))
      .toBe("Insufficient stock for 'Raw Cassava'.");
  });

  it("falls back to the first field error", () => {
    expect(getErrorMessage(apiError(400, { errors: { quantity_tons: ["Must be positive."] } }))).toBe("Must be positive.");
  });

  it("never exposes raw server errors", () => {
    expect(getErrorMessage(apiError(500, "<html>Traceback…</html>"))).toMatch(/server encountered an error/);
  });

  it("explains throttling, timeouts and network failures", () => {
    expect(getErrorMessage(apiError(429, {}))).toMatch(/Too many requests/);
    expect(getErrorMessage({ code: "ECONNABORTED" })).toMatch(/too long/);
    expect(getErrorMessage({ message: "Network Error" })).toMatch(/Cannot reach the server/);
  });

  it("returns empty string for cancelled requests", () => {
    expect(getErrorMessage({ code: "ERR_CANCELED" })).toBe("");
  });

  it("uses the fallback when nothing better is available", () => {
    expect(getErrorMessage(apiError(400, {}), "Could not save.")).toBe("Could not save.");
  });
});

describe("getFieldErrors", () => {
  it("flattens DRF field errors to one message per field", () => {
    const error = apiError(400, { errors: { production_date: ["Already exists."], starch_output_tons: "Too high." } });
    expect(getFieldErrors(error)).toEqual({ production_date: "Already exists.", starch_output_tons: "Too high." });
  });

  it("returns an empty object when there are none", () => {
    expect(getFieldErrors({})).toEqual({});
  });
});

describe("parseBlobError", () => {
  it("decodes JSON error bodies from blob downloads", async () => {
    const blob = new Blob([JSON.stringify({ detail: "Date range cannot exceed 366 days." })], { type: "application/json" });
    const error = await parseBlobError(apiError(400, blob));
    expect(getErrorMessage(error)).toBe("Date range cannot exceed 366 days.");
  });
});
