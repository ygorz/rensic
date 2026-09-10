import { expect, test } from "vitest";
import {
  CHAIN_RPC_NOTE,
  DESK_CHAINS,
  DEFAULT_CHAIN_ID,
  deskChainIds,
  explorerAddressHref,
  explorerName,
  explorerOrigin,
  explorerTxHref,
  getDeskChain,
} from "./chains";

test("desk chains match curated eight-mainnet ingest registry", () => {
  expect(deskChainIds()).toEqual([
    "ethereum",
    "base",
    "arbitrum",
    "polygon",
    "optimism",
    "bsc",
    "robinhood",
    "avalanche",
  ]);
  expect(DEFAULT_CHAIN_ID).toBe("ethereum");
  expect(getDeskChain("optimism").nativeSymbol).toBe("ETH");
  expect(getDeskChain("polygon").nativeSymbol).toBe("MATIC");
  expect(getDeskChain("bsc").alchemySubdomain).toBe("bnb-mainnet");
  expect(getDeskChain("robinhood").alchemySubdomain).toBe("robinhood-mainnet");
  expect(getDeskChain("avalanche").alchemySubdomain).toBe("avax-mainnet");
  expect(getDeskChain("avalanche").nativeSymbol).toBe("AVAX");
  expect(CHAIN_RPC_NOTE.toLowerCase()).toContain("alchemy");
});

test("explorer helpers use chain-specific origins", () => {
  expect(explorerOrigin("base")).toBe("https://basescan.org");
  expect(explorerOrigin("arbitrum")).toBe("https://arbiscan.io");
  expect(explorerOrigin("optimism")).toBe("https://optimistic.etherscan.io");
  expect(explorerOrigin("polygon")).toBe("https://polygonscan.com");
  expect(explorerOrigin("bsc")).toBe("https://bscscan.com");
  expect(explorerOrigin("robinhood")).toBe("https://robinhoodchain.blockscout.com");
  expect(explorerOrigin("avalanche")).toBe("https://snowtrace.io");
  expect(explorerName("base")).toBe("Basescan");
  expect(explorerName("robinhood")).toBe("Robinhood Blockscout");
  expect(explorerAddressHref("optimism:0xabc")).toBe(
    "https://optimistic.etherscan.io/address/0xabc",
  );
  expect(explorerTxHref("bsc:0xdeadbeef")).toBe("https://bscscan.com/tx/0xdeadbeef");
  expect(explorerTxHref("not-a-hash", "ethereum")).toBeNull();
  for (const c of DESK_CHAINS) {
    expect(c.rpcBaseUrl.endsWith("/v2/")).toBe(true);
  }
});
