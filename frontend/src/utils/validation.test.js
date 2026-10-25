import { describe, expect, it } from "vitest";
import { previewYield, toProductionPayload, validateDelivery, validateProductionEntry } from "./validation";

const TODAY = "2026-05-20";
const LIMITS = { today: TODAY, maxDowntimeMinutes: 1440 };
const valid = {
  production_date: "2026-05-19",
  cassava_inflow_tons: "100",
  starch_output_tons: "28",
  downtime_minutes: "15",
  notes: "",
};

describe("validateProductionEntry", () => {
  it("accepts a valid entry", () => {
    expect(validateProductionEntry(valid, LIMITS)).toEqual({});
  });

  it("requires every mandatory field", () => {
    const errors = validateProductionEntry({ production_date: "", cassava_inflow_tons: "", starch_output_tons: "", downtime_minutes: "" }, LIMITS);
    expect(Object.keys(errors).sort()).toEqual(["cassava_inflow_tons", "production_date", "starch_output_tons"]);
  });

  it("rejects future dates but allows today", () => {
    expect(validateProductionEntry({ ...valid, production_date: "2026-05-21" }, LIMITS).production_date).toMatch(/future/);
    expect(validateProductionEntry({ ...valid, production_date: TODAY }, LIMITS)).toEqual({});
  });

  it.each([
    ["zero inflow", { cassava_inflow_tons: "0", starch_output_tons: "0" }, "cassava_inflow_tons"],
    ["negative inflow", { cassava_inflow_tons: "-5" }, "cassava_inflow_tons"],
    ["non-numeric inflow", { cassava_inflow_tons: "abc" }, "cassava_inflow_tons"],
    ["output above inflow", { starch_output_tons: "101" }, "starch_output_tons"],
    ["negative output", { starch_output_tons: "-1" }, "starch_output_tons"],
    ["fractional downtime", { downtime_minutes: "2.5" }, "downtime_minutes"],
    ["downtime above 24h", { downtime_minutes: "1441" }, "downtime_minutes"],
  ])("rejects %s", (_, overrides, field) => {
    expect(validateProductionEntry({ ...valid, ...overrides }, LIMITS)).toHaveProperty(field);
  });

  it("treats blank downtime as allowed (defaults to 0)", () => {
    expect(validateProductionEntry({ ...valid, downtime_minutes: "" }, LIMITS)).toEqual({});
    expect(toProductionPayload({ ...valid, downtime_minutes: "" }).downtime_minutes).toBe(0);
  });

  it("allows a zero-output day", () => {
    expect(validateProductionEntry({ ...valid, starch_output_tons: "0" }, LIMITS)).toEqual({});
  });

  it("uses the limit supplied by the server config", () => {
    expect(validateProductionEntry({ ...valid, downtime_minutes: "500" }, { today: TODAY, maxDowntimeMinutes: 480 }).downtime_minutes)
      .toMatch(/480 minutes/);
  });
});

describe("previewYield", () => {
  it("computes percentage yield", () => {
    expect(previewYield("100", "28")).toBeCloseTo(28);
  });

  it.each([["", "10"], ["0", "10"], ["abc", "5"], ["100", ""]])("returns null for (%s, %s)", (inflow, output) => {
    expect(previewYield(inflow, output)).toBeNull();
  });
});

describe("toProductionPayload", () => {
  it("trims notes and converts downtime to a number", () => {
    expect(toProductionPayload({ ...valid, notes: "  shift B  ", downtime_minutes: "20" })).toMatchObject({ notes: "shift B", downtime_minutes: 20 });
  });
});

describe("validateDelivery", () => {
  const delivery = { supplier: "abc", delivery_date: "2026-05-18", quantity_tons: "40" };

  it("accepts a valid delivery", () => {
    expect(validateDelivery(delivery, LIMITS)).toEqual({});
  });

  it("rejects missing supplier, future date and non-positive quantity", () => {
    expect(validateDelivery({ supplier: "", delivery_date: "2026-06-01", quantity_tons: "0" }, LIMITS)).toEqual({
      supplier: expect.any(String),
      delivery_date: expect.stringMatching(/future/),
      quantity_tons: expect.any(String),
    });
  });
});
