import { expect, test } from "vitest";
import {
  DEFAULT_LOOKBACK_DAYS,
  LOOKBACK_CHOICES,
  PAGE_CAP_TX_COUNT,
  WORKING_SET_CAP,
  DESK_PAGE_SIZE,
  deskPageCount,
  deskPageRangeLabel,
  deskPageSlice,
  caseOptionLabel,
  clampLookback,
  investigatorNote,
  pairEthFlow,
  rankAddresses,
  vertexCast,
  windowDays,
  windowFact,
  windowLabel,
  workingSetCopy,
} from "./desk";

const tornado = "ethereum:0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc";
const weth = "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2";
const seed = "ethereum:0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532";
const whale = "ethereum:0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const dust = "ethereum:0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

test("lookback choices cover quiet wallets and default 30", () => {
  expect([...LOOKBACK_CHOICES]).toEqual([7, 30, 90, 365]);
  expect(DEFAULT_LOOKBACK_DAYS).toBe(30);
  expect(clampLookback("30")).toBe(30);
  expect(clampLookback(365)).toBe(365);
  expect(122).toBeLessThan(365);
});

test("window label is Nd, never complete history", () => {
  expect(windowDays("2026-08-04T00:00:00Z", "2026-09-03T00:00:00Z")).toBe(30);
  expect(windowLabel(30)).toBe("30d");
  expect(windowFact(30, false)).toBe("Fetched 30d of transfers in this case window.");
  expect(windowFact(30, false)?.toLowerCase()).not.toContain("complete");
  expect(windowFact(30, true)).toContain("page cap");
  expect(PAGE_CAP_TX_COUNT).toBe(200000);
});

test("case picker shows window so two cases are not identical", () => {
  const label = caseOptionLabel({
    caseTitle: "Quiet wallet",
    seedAddress: seed,
    transactionCount: 1,
    timeWindowStart: "2026-05-04T00:00:00Z",
    timeWindowEnd: "2026-09-03T00:00:00Z",
    shortAddr: (id) => (id ? id.slice(-6) : "-"),
  });
  expect(label).toContain("122d");
  expect(label).toContain("1 tx");
});

test("rankAddresses pins seed, then labeled, then ETH flow", () => {
  const ranked = rankAddresses([
    {
      caseAddressId: "dust",
      addressId: dust,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 50,
      totalValueOutEth: 0,
    },
    {
      caseAddressId: "tornado",
      addressId: tornado,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 0.013,
      totalValueOutEth: 0,
    },
    {
      caseAddressId: "seed",
      addressId: seed,
      membershipRole: "seed",
      hopDistance: 0,
      totalValueInEth: 0.013,
      totalValueOutEth: 0,
    },
    {
      caseAddressId: "whale",
      addressId: whale,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 80,
      totalValueOutEth: 0,
    },
    {
      caseAddressId: "flagged",
      addressId: "ethereum:0xcccccccccccccccccccccccccccccccccccccccc",
      addressLabel: "gas station",
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 0.001,
      totalValueOutEth: 0,
    },
  ]);
  expect(ranked.map((r) => r.caseAddressId)).toEqual([
    "seed",
    "tornado",
    "flagged",
    "whale",
    "dust",
  ]);
});

test("vertex cast keeps every labeled hop-1 then fills by flow", () => {
  const rows = [
    { caseAddressId: "seed", addressId: seed, membershipRole: "seed", hopDistance: 0 },
    {
      caseAddressId: "tc",
      addressId: tornado,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 0.013,
    },
    {
      caseAddressId: "weth",
      addressId: weth,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 1,
    },
    {
      caseAddressId: "whale",
      addressId: whale,
      membershipRole: "discovered",
      hopDistance: 1,
      totalValueInEth: 900,
    },
  ];
  const cast = vertexCast(rows, 3);
  expect(cast.map((r) => r.caseAddressId)).toEqual(["seed", "weth", "tc"]);
  const filled = vertexCast(rows, 4);
  expect(filled.map((r) => r.caseAddressId)).toEqual(["seed", "weth", "tc", "whale"]);
});

test("working set copy uses the fetch cap", () => {
  expect(workingSetCopy(WORKING_SET_CAP, 3)).toBe(
    "Wallet plus top 100 by native flow in this window (3 named).",
  );
});

test("investigator note is not the pack name", () => {
  expect(
    investigatorNote({
      addressId: tornado,
      addressLabel: "Tornado Cash",
    }),
  ).toBeNull();
  expect(
    investigatorNote({
      addressId: tornado,
      addressLabel: "gas station",
    }),
  ).toBe("gas station");
});

test("pairEthFlow sums sent and received between file wallet and counterparty", () => {
  const other = "ethereum:0xdddddddddddddddddddddddddddddddddddddddd";
  const rows = pairEthFlow(seed, [
    {
      transactionId: "ethereum:0x1",
      fromAddressId: seed,
      toAddressId: whale,
      valueEth: 1.2,
    },
    {
      transactionId: "ethereum:0x2",
      fromAddressId: whale,
      toAddressId: seed,
      valueEth: 0.4,
    },
    {
      transactionId: "ethereum:0x3",
      fromAddressId: "ETHEREUM:0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532",
      toAddressId: other,
      valueEth: "2",
    },
    {
      transactionId: "ethereum:0x1",
      fromAddressId: seed,
      toAddressId: whale,
      valueEth: 9,
    },
    {
      transactionId: "ethereum:0xself",
      fromAddressId: seed,
      toAddressId: seed,
      valueEth: 8,
    },
    {
      transactionId: "ethereum:0xselfhex",
      fromAddressId: seed,
      toAddressId: "0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532",
      valueEth: 3,
    },
    {
      transactionId: "ethereum:0xzero",
      fromAddressId: seed,
      toAddressId: dust,
      valueEth: 0,
    },
    {
      transactionId: "ethereum:0xfail",
      fromAddressId: seed,
      toAddressId: other,
      valueEth: 5,
      transactionStatus: "reverted",
    },
    {
      transactionId: "ethereum:0xother",
      fromAddressId: whale,
      toAddressId: dust,
      valueEth: 50,
    },
  ]);
  expect(rows.map((r) => r.addressId)).toEqual([other, whale]);
  expect(rows.find((r) => r.addressId === whale)).toEqual({
    addressId: whale,
    sentEth: 1.2,
    receivedEth: 0.4,
    transferCount: 2,
  });
  expect(rows.find((r) => r.addressId === other)).toMatchObject({
    sentEth: 2,
    receivedEth: 0,
    transferCount: 1,
  });
  expect(rows.some((r) => r.addressId === seed || r.addressId === dust)).toBe(false);
  expect(rows.some((r) => r.addressId.toLowerCase().includes("6d77695feba33e2e2fdd435997dc4f9ba8bfd532"))).toBe(
    false,
  );
});

test("deskPageSlice pages at DESK_PAGE_SIZE", () => {
  const rows = Array.from({ length: 120 }, (_, i) => i);
  expect(deskPageCount(120)).toBe(3);
  expect(deskPageSlice(rows, 1)).toEqual(rows.slice(0, DESK_PAGE_SIZE));
  expect(deskPageSlice(rows, 3)).toEqual(rows.slice(100, 120));
  expect(deskPageRangeLabel(120, 2)).toBe("51–100 of 120");
  expect(deskPageRangeLabel(0, 1)).toBe("0");
});
