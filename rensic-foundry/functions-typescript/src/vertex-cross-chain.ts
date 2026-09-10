/**
 * Rensic — Cross-Chain Vertex Functions
 * =======================================
 *
 * Functions for visualizing cross-chain relationships in Vertex graphs.
 * Enables investigators to see when the same wallet operates across
 * multiple EVM chains within an investigation.
 */
import { Function, FunctionsMap } from "@foundry/functions-api";
import { Address } from "@foundry/ontology-api";

// Chain colors (must match vertex-derived-properties.ts)
const CHAIN_COLORS: { [key: string]: string } = {
    ethereum:  "#627EEA",
    base:      "#0052FF",
    arbitrum:  "#28A0F0",
    optimism:  "#FF0420",
    polygon:   "#8247E5",
    zksync:    "#4E529A",
};

const DEFAULT_COLOR = "#8A8886";

export class RensicCrossChain {

    /**
     * CROSS-CHAIN BADGE
     *
     * Returns a label showing which chains an address is active on.
     * e.g., "ETH + BASE + ARB" for an address active on 3 chains.
     *
     * Usage: Node secondary label in Vertex to immediately see multi-chain presence.
     */
    @Function()
    public crossChainBadge(addresses: Address[]): FunctionsMap<Address, string> {
        // Group by hex address (strip chain prefix)
        const hexToChains = new Map<string, Set<string>>();
        const hexToAddresses = new Map<string, Address[]>();

        for (const addr of addresses) {
            const id = addr.addressId ?? "";
            const parts = id.split(":");
            if (parts.length < 2) { continue; }
            const hexAddr = parts.slice(1).join(":");
            const chain = parts[0];

            if (!hexToChains.has(hexAddr)) {
                hexToChains.set(hexAddr, new Set());
                hexToAddresses.set(hexAddr, []);
            }
            hexToChains.get(hexAddr)!.add(chain);
            hexToAddresses.get(hexAddr)!.push(addr);
        }

        const map = new FunctionsMap<Address, string>();

        for (const addr of addresses) {
            const id = addr.addressId ?? "";
            const parts = id.split(":");
            const hexAddr = parts.length >= 2 ? parts.slice(1).join(":") : id;
            const chains = hexToChains.get(hexAddr);

            if (chains && chains.size > 1) {
                const chainLabels = [...chains].map(c => c.substring(0, 3).toUpperCase()).join(" + ");
                map.set(addr, `🔗 ${chainLabels}`);
            } else {
                map.set(addr, addr.chainId?.substring(0, 3).toUpperCase() ?? "?");
            }
        }

        return map;
    }

    /**
     * MULTI-CHAIN INDICATOR COLOR
     *
     * Returns a special color for addresses that appear on multiple chains.
     * Single-chain addresses get their chain color; multi-chain get gold.
     */
    @Function()
    public multiChainColor(addresses: Address[]): FunctionsMap<Address, string> {
        const hexToChainCount = new Map<string, number>();

        for (const addr of addresses) {
            const id = addr.addressId ?? "";
            const parts = id.split(":");
            const hexAddr = parts.length >= 2 ? parts.slice(1).join(":") : id;

            hexToChainCount.set(hexAddr, (hexToChainCount.get(hexAddr) ?? 0) + 1);
        }

        const map = new FunctionsMap<Address, string>();
        const MULTI_CHAIN_COLOR = "#FFD700"; // Gold for multi-chain

        for (const addr of addresses) {
            const id = addr.addressId ?? "";
            const parts = id.split(":");
            const hexAddr = parts.length >= 2 ? parts.slice(1).join(":") : id;
            const chainCount = hexToChainCount.get(hexAddr) ?? 1;

            if (chainCount > 1) {
                map.set(addr, MULTI_CHAIN_COLOR);
            } else {
                const chainId = addr.chainId ?? "unknown";
                map.set(addr, CHAIN_COLORS[chainId] ?? DEFAULT_COLOR);
            }
        }

        return map;
    }
}
