import { expect, test } from "vitest";
import {
  isCommunityEntity,
  isOfficialEntity,
  lookupKnownEntity,
  seedExposureLine,
} from "./knownEntities";

test("pack labels Vitalik and WETH", () => {
  const v = lookupKnownEntity("ethereum:0xd8da6bf26964af9d7eed9e03e53415d37aa96045");
  expect(v?.category).toBe("person");
  expect(v?.name).toBe("Vitalik Buterin");
  const w = lookupKnownEntity("0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2");
  expect(w?.category).toBe("protocol");
  expect(w?.name).toBe("WETH");
});

test("Tornado Cash is mixer not current SDN", () => {
  const t = lookupKnownEntity("0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc");
  expect(t?.name).toBe("Tornado Cash");
  expect(t?.category).toBe("mixer");
});

test("FBI IC3 Bybit wallets are sanctions with an IC3 cite", () => {
  const b = lookupKnownEntity("0x51E9d833Ecae4E8D9D8Be17300AEE6D3398C135D");
  expect(b?.category).toBe("sanctions");
  expect(b?.name).toBe("TraderTraitor (Bybit)");
  expect(b?.sourceUrl).toContain("ic3.gov");
});

test("official protocol contracts from deployment docs", () => {
  const v2 = lookupKnownEntity("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D");
  expect(v2?.category).toBe("protocol");
  expect(v2?.name).toBe("Uniswap V2 Router02");
  const permit2 = lookupKnownEntity("0x000000000022D473030F116dDEE9F6B43aC78BA3");
  expect(permit2?.category).toBe("protocol");
  expect(permit2?.name).toBe("Uniswap Permit2");
  const steth = lookupKnownEntity("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84");
  expect(steth?.name).toBe("Lido stETH");
});

test("seed exposure prefers mixer then SDN then other labels", () => {
  expect(seedExposureLine([])).toBe("No public names on the addresses touched.");
  expect(
    seedExposureLine([
      {
        addressId: "ethereum:0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        membershipRole: "seed",
        hopDistance: 0,
      },
      {
        addressId: "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        membershipRole: "discovered",
        hopDistance: 1,
      },
    ]),
  ).toBe("Touched a protocol (WETH)");
  expect(
    seedExposureLine([
      { addressId: "ethereum:0xabc", membershipRole: "seed", hopDistance: 0 },
      {
        addressId: "ethereum:0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
        membershipRole: "discovered",
        hopDistance: 1,
      },
    ]),
  ).toBe("Touched a mixer (Tornado Cash)");
});

test("exchange pack includes Bitfinex and Binance from official cites", () => {
  const bf = lookupKnownEntity("0x742d35Cc6634C0532925a3b844Bc454e4438f44e");
  expect(bf?.category).toBe("exchange");
  expect(bf?.name.toLowerCase()).toContain("bitfinex");
  expect(bf?.sourceUrl).toContain("bitfinexcom");
  const bn = lookupKnownEntity("0x28c6c06298d514db089934071355e5743bf21d60");
  expect(bn?.category).toBe("exchange");
  expect(bn?.name.toLowerCase()).toContain("binance");
  expect(bn?.sourceUrl).toContain("binance.com");
});

test("Compound and DAI protocol rows are present", () => {
  const c = lookupKnownEntity("0xc3d688B66703497DAA19211EEdff47f25384cdc3");
  expect(c?.category).toBe("protocol");
  expect(c?.name).toContain("Compound");
  const dai = lookupKnownEntity("0x6B175474E89094C44Da98b954EedeAC495271d0F");
  expect(dai?.name).toBe("DAI");
  expect(dai?.category).toBe("protocol");
});

test("existing curated rows are official tier", () => {
  const bn = lookupKnownEntity("0x28c6c06298d514db089934071355e5743bf21d60");
  expect(bn?.tier).toBe("official");
  expect(isOfficialEntity(bn)).toBe(true);
  const v = lookupKnownEntity("0xd8da6bf26964af9d7eed9e03e53415d37aa96045");
  expect(v?.tier).toBe("official");
});

test("Coinbase community nametags are community not official", () => {
  const c1 = lookupKnownEntity("0x71660c4005ba85c37ccec55d0c4493e66fe775d3");
  expect(c1?.name).toBe("Coinbase 1");
  expect(c1?.category).toBe("exchange");
  expect(c1?.tier).toBe("community");
  expect(isCommunityEntity(c1)).toBe(true);
  expect(c1?.sourceUrl).toContain("etherscan.io/accounts/label/coinbase");
  const c11 = lookupKnownEntity("0x77696bb39917c91a0c3908d577d5e322095425ca");
  expect(c11?.name).toBe("Coinbase 11");
  expect(c11?.tier).toBe("community");
});

test("Binance 15 community counterparty from live Etherscan", () => {
  const b15 = lookupKnownEntity("0xc013426d7cef8be3ef3b366151ed85e4fe33688c");
  expect(b15?.name).toBe("Binance 15");
  expect(b15?.category).toBe("exchange");
  expect(b15?.tier).toBe("community");
  expect(isCommunityEntity(b15)).toBe(true);
  expect(b15?.sourceUrl.toLowerCase()).toContain("0xc013426d7cef8be3ef3b366151ed85e4fe33688c");
});

test("official Coinbase protocol tokens stay official", () => {
  const cbeth = lookupKnownEntity("0xbe9895146f7af43049ca1c1ae358b0541ea49704");
  expect(cbeth?.name).toBe("Coinbase cbETH");
  expect(cbeth?.tier).toBe("official");
  expect(cbeth?.category).toBe("protocol");
});
