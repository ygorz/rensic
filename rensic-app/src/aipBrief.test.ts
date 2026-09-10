import { expect, test } from "vitest";
import { buildAipBrief, paraphraseBrief } from "./aipBrief";

const tornado = "ethereum:0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc";
const seed = "ethereum:0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532";
const dust = "ethereum:0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

test("buildAipBrief includes pack name and source for hop-1", () => {
  const brief = buildAipBrief({
    caseObj: {
      caseId: "c1",
      caseTitle: "Demo",
      seedAddress: seed,
      chainIds: ["ethereum"],
      timeWindowStart: "2026-08-11T00:00:00Z",
      timeWindowEnd: "2026-09-10T00:00:00Z",
      transactionCount: 12,
    },
    addresses: [
      {
        caseAddressId: "s",
        addressId: seed,
        membershipRole: "seed",
        hopDistance: 0,
      },
      {
        caseAddressId: "t",
        addressId: tornado,
        membershipRole: "discovered",
        hopDistance: 1,
        totalValueInEth: 0,
        totalValueOutEth: 0.013,
        transactionCountInCase: 1,
      },
      {
        caseAddressId: "d",
        addressId: dust,
        membershipRole: "discovered",
        hopDistance: 1,
        totalValueInEth: 1,
        totalValueOutEth: 0,
        transactionCountInCase: 2,
      },
    ],
  });
  expect(brief.schema).toBe("rensic.aipBrief.v1");
  expect(brief.windowLabel).toBe("30d");
  expect(brief.hop1AddressCount).toBe(2);
  const torn = brief.counterparties.find((c) => c.addressId === tornado);
  expect(torn?.packName?.toLowerCase()).toContain("tornado");
  expect(torn?.sourceUrl).toBeTruthy();
  expect(brief.counterparties.some((c) => c.addressId === dust && !c.displayName)).toBe(
    true,
  );
});

test("paraphraseBrief stays within brief facts", () => {
  const brief = buildAipBrief({
    caseObj: {
      caseId: "c1",
      caseTitle: "Quiet",
      seedAddress: seed,
      chainIds: ["ethereum"],
      timeWindowStart: "2026-08-11T00:00:00Z",
      timeWindowEnd: "2026-09-10T00:00:00Z",
    },
    addresses: [
      {
        caseAddressId: "s",
        addressId: seed,
        membershipRole: "seed",
        hopDistance: 0,
      },
      {
        caseAddressId: "t",
        addressId: tornado,
        membershipRole: "discovered",
        hopDistance: 1,
        totalValueInEth: 0.013,
        totalValueOutEth: 0,
      },
    ],
  });
  const narrative = paraphraseBrief(brief);
  expect(narrative.paragraphs.length).toBeGreaterThanOrEqual(2);
  const text = narrative.paragraphs.join("\n").toLowerCase();
  expect(text).toContain("30d");
  expect(text).toContain("biggest by eth moved");
  expect(text).not.toContain("counterpart");
  expect(text).not.toContain("risk score");
  expect(text).not.toContain("mule");
  expect(text).not.toContain("hop-1");
  expect(narrative.engine).toBe("deterministic");
  expect(narrative.sourceUrls.length).toBeGreaterThan(0);
});
