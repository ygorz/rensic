/** Shared EVM chain registry for the desk (mirrors ingest CHAINS). */
export type DeskChain = {
  id: string;
  displayName: string;
  nativeSymbol: string;
  alchemySubdomain: string;
  /** Alchemy HTTPS base ending in /v2/ (key appended by Foundry config). */
  rpcBaseUrl: string;
  explorerUrl: string;
  explorerName: string;
};

/**
 * Chains the desk offers for new investigations / RPC keys.
 * Must stay aligned with rensic-ingestion transforms-python config.CHAINS.
 * Ingest only works when Alchemy is configured for that network in Foundry
 * Chain Configuration (RPC popover or Ontology).
 */
export const DESK_CHAINS: readonly DeskChain[] = [
  {
    id: "ethereum",
    displayName: "Ethereum Mainnet",
    nativeSymbol: "ETH",
    alchemySubdomain: "eth-mainnet",
    rpcBaseUrl: "https://eth-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://etherscan.io",
    explorerName: "Etherscan",
  },
  {
    id: "base",
    displayName: "Base",
    nativeSymbol: "ETH",
    alchemySubdomain: "base-mainnet",
    rpcBaseUrl: "https://base-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://basescan.org",
    explorerName: "Basescan",
  },
  {
    id: "arbitrum",
    displayName: "Arbitrum One",
    nativeSymbol: "ETH",
    alchemySubdomain: "arb-mainnet",
    rpcBaseUrl: "https://arb-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://arbiscan.io",
    explorerName: "Arbiscan",
  },
  {
    id: "polygon",
    displayName: "Polygon PoS",
    nativeSymbol: "MATIC",
    alchemySubdomain: "polygon-mainnet",
    rpcBaseUrl: "https://polygon-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://polygonscan.com",
    explorerName: "Polygonscan",
  },
  {
    id: "optimism",
    displayName: "Optimism",
    nativeSymbol: "ETH",
    alchemySubdomain: "opt-mainnet",
    rpcBaseUrl: "https://opt-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://optimistic.etherscan.io",
    explorerName: "Optimistic Etherscan",
  },
  {
    id: "bsc",
    displayName: "BNB Smart Chain",
    nativeSymbol: "BNB",
    alchemySubdomain: "bnb-mainnet",
    rpcBaseUrl: "https://bnb-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://bscscan.com",
    explorerName: "BscScan",
  },
  {
    id: "robinhood",
    displayName: "Robinhood Chain",
    nativeSymbol: "ETH",
    alchemySubdomain: "robinhood-mainnet",
    rpcBaseUrl: "https://robinhood-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://robinhoodchain.blockscout.com",
    explorerName: "Robinhood Blockscout",
  },
  {
    id: "avalanche",
    displayName: "Avalanche C-Chain",
    nativeSymbol: "AVAX",
    alchemySubdomain: "avax-mainnet",
    rpcBaseUrl: "https://avax-mainnet.g.alchemy.com/v2/",
    explorerUrl: "https://snowtrace.io",
    explorerName: "Snowtrace",
  },
] as const;

export const DEFAULT_CHAIN_ID = "ethereum";

export const CHAIN_RPC_NOTE =
  "Chains only work if an Alchemy key/network is configured in Foundry Chain Configuration for that network.";

const byId = new Map(DESK_CHAINS.map((c) => [c.id, c]));

export function getDeskChain(chainId: string | undefined | null): DeskChain {
  const id = (chainId ?? "").trim().toLowerCase();
  return byId.get(id) ?? byId.get(DEFAULT_CHAIN_ID)!;
}

export function deskChainIds(): string[] {
  return DESK_CHAINS.map((c) => c.id);
}

export function explorerOrigin(chainId: string | undefined | null): string {
  return getDeskChain(chainId).explorerUrl;
}

export function explorerName(chainId: string | undefined | null): string {
  return getDeskChain(chainId).explorerName;
}

export function explorerAddressHref(
  addressOrComposite: string | undefined,
  fallbackChain?: string,
): string | null {
  if (!addressOrComposite) {
    return null;
  }
  const i = addressOrComposite.indexOf(":");
  const chain =
    i > 0 ? addressOrComposite.slice(0, i) : fallbackChain || DEFAULT_CHAIN_ID;
  const hex = i > 0 ? addressOrComposite.slice(i + 1) : addressOrComposite;
  if (!hex) {
    return null;
  }
  return `${explorerOrigin(chain)}/address/${hex}`;
}

export function explorerTxHref(
  txOrComposite: string | undefined,
  fallbackChain?: string,
): string | null {
  if (!txOrComposite) {
    return null;
  }
  const i = txOrComposite.indexOf(":");
  const chain = i > 0 ? txOrComposite.slice(0, i) : fallbackChain || DEFAULT_CHAIN_ID;
  const hex = i > 0 ? txOrComposite.slice(i + 1) : txOrComposite;
  if (!hex || !/^0x[0-9a-fA-F]+$/i.test(hex)) {
    return null;
  }
  return `${explorerOrigin(chain)}/tx/${hex}`;
}
