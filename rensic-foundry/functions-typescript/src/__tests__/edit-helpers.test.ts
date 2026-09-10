import {
  caseAddressKey,
  normalizeSeed,
  clampLookbackDays,
  canOpenInvestigation,
  labelAddressPayload,
  DELETE_INVESTIGATION_CASCADE,
  DELETE_INVESTIGATION_KEEPS,
} from "../edit-helpers";

describe("edit helpers", () => {
  test("caseAddressKey", () => {
    expect(caseAddressKey("c1", "ethereum:0xab")).toBe("c1:ethereum:0xab");
  });
  test("normalizeSeed lowercases", () => {
    expect(normalizeSeed(" 0xABC ")).toBe("0xabc");
  });
  test("clampLookbackDays", () => {
    expect(clampLookbackDays(30)).toBe(30);
    expect(clampLookbackDays(0)).toBe(90);
    expect(clampLookbackDays(-5)).toBe(1);
  });
  test("canOpenInvestigation rejects empties", () => {
    expect(canOpenInvestigation("", "0x1", ["ethereum"])).toBe(false);
    expect(canOpenInvestigation("t", "", ["ethereum"])).toBe(false);
    expect(canOpenInvestigation("t", "0x1", [])).toBe(false);
    expect(canOpenInvestigation("t", "0x1", ["ethereum"])).toBe(true);
  });
  test("official label requires note only", () => {
    const bad = labelAddressPayload("official", "rename", "", "OFAC");
    expect(bad.ok).toBe(false);
    const ok = labelAddressPayload("official", "rename", "seen on mixer", "OFAC");
    expect(ok.ok).toBe(true);
    expect(ok.label).toBe("seen on mixer");
  });
  test("community may override display; empty rejected", () => {
    expect(labelAddressPayload("community", "", "").ok).toBe(false);
    const r = labelAddressPayload("community", "Gas station", "note");
    expect(r.ok).toBe(true);
    expect(r.label).toContain("Gas station");
  });
});

describe("deleteInvestigation cascade contract", () => {
  test("deletes case-scoped rows only", () => {
    expect([...DELETE_INVESTIGATION_CASCADE]).toEqual([
      "CaseAddress memberships via caseAddresses MultiLink",
      "InvestigationNarrative rows via narratives MultiLink",
      "InvestigationCase itself",
    ]);
    expect(DELETE_INVESTIGATION_KEEPS).toContain("global Address objects");
    expect(DELETE_INVESTIGATION_KEEPS).toContain("known_entities pack");
    expect(DELETE_INVESTIGATION_KEEPS).toContain("shared Foundry ingest pipeline datasets");
  });
});
