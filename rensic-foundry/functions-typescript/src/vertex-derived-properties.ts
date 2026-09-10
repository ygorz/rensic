/**
 * Rensic — Vertex Derived Property Functions
 * ============================================
 *
 * These functions compute derived values used for Vertex node/edge styling.
 * Vertex calls each function ONCE with the full array of objects on the graph.
 *
 * Usage in Vertex:
 *   - Node Fill Color → Select derived property → "Risk Color" or "Chain Color"
 *   - Node Size → Select derived property → "Address Value Size"
 *   - Edge Label → Select derived property → "Transfer Amount Label"
 */
import { Function, Double, FunctionsMap, Integer } from "@foundry/functions-api";
import { Address, Transaction, TokenTransfer } from "@foundry/ontology-api";

// ────────────────────────────────────────────────────────────────────────────
// Custom types for derived properties (all fields must be primitives)
// ────────────────────────────────────────────────────────────────────────────

/** Node styling metadata for Address objects */
interface AddressNodeStyle {
    riskColor: string;       // Hex color based on risk score
    riskCategory: string;    // "critical" | "high" | "medium" | "low" | "unknown"
    chainColor: string;      // Hex color based on chain ID
    sizeWeight: Double;      // 0-1 scale for node sizing (based on total value)
    displayLabel: string;    // Best available label for the node
}

/** Edge styling metadata for Transaction objects */
interface TransactionEdgeStyle {
    valueLabel: string;      // "1.50 ETH" or "0 ETH"
    chainColor: string;      // Hex color for the chain
    weightNormalized: Double; // 0-1 scale for edge thickness
}

/** Edge styling metadata for Token Transfer objects */
interface TokenTransferEdgeStyle {
    amountLabel: string;     // "5,000 USDC" or "1 NFT #1234"
    chainColor: string;      // Hex color for the chain
    tokenStandard: string;   // "erc20" | "erc721" | "erc1155"
}

// ────────────────────────────────────────────────────────────────────────────
// Color mappings
// ────────────────────────────────────────────────────────────────────────────

const RISK_COLORS: { [key: string]: string } = {
    critical: "#D13438",    // Red
    high:     "#FF8C00",    // Orange
    medium:   "#0078D4",    // Blue
    low:      "#107C10",    // Green
    unknown:  "#8A8886",    // Gray
};

const CHAIN_COLORS: { [key: string]: string } = {
    ethereum:  "#627EEA",   // ETH purple
    base:      "#0052FF",   // Coinbase blue
    arbitrum:  "#28A0F0",   // Arbitrum blue
    optimism:  "#FF0420",   // Optimism red
    polygon:   "#8247E5",   // Polygon purple
    zksync:    "#4E529A",   // zkSync indigo
};

const DEFAULT_CHAIN_COLOR = "#8A8886";

// ────────────────────────────────────────────────────────────────────────────
// Functions
// ────────────────────────────────────────────────────────────────────────────

export class RensicVertexDerivedProperties {

    /**
     * ADDRESS NODE STYLING
     * Returns a composite style object for each Address on the graph.
     * Use individual fields for Fill Color, Size, and Label in Vertex.
     */
    @Function()
    public addressNodeStyle(addresses: Address[]): FunctionsMap<Address, AddressNodeStyle> {
        const map = new FunctionsMap<Address, AddressNodeStyle>();

        // Find max total value across all addresses for normalization
        let maxValue = 0;
        for (const addr of addresses) {
            const totalIn = addr.totalValueInEth ?? 0;
            const totalOut = addr.totalValueOutEth ?? 0;
            const total = totalIn + totalOut;
            if (total > maxValue) {
                maxValue = total;
            }
        }

        for (const addr of addresses) {
            const riskScore = addr.riskScore ?? -1;
            const riskCategory = riskScore >= 75 ? "critical"
                : riskScore >= 50 ? "high"
                : riskScore >= 25 ? "medium"
                : riskScore >= 0 ? "low"
                : "unknown";

            const chainId = addr.chainId ?? "unknown";
            const chainColor = CHAIN_COLORS[chainId] ?? DEFAULT_CHAIN_COLOR;

            const totalIn = addr.totalValueInEth ?? 0;
            const totalOut = addr.totalValueOutEth ?? 0;
            const totalValue = totalIn + totalOut;
            const sizeWeight = maxValue > 0 ? totalValue / maxValue : 0.5;

            // Best available label: addressLabel > "0xABCD...EFGH" truncated
            const wallet = addr.walletAddress ?? "unknown";
            const displayLabel = addr.addressLabel
                ?? (wallet.length > 10
                    ? wallet.substring(0, 6) + "..." + wallet.substring(wallet.length - 4)
                    : wallet);

            map.set(addr, {
                riskColor: RISK_COLORS[riskCategory] ?? RISK_COLORS.unknown,
                riskCategory,
                chainColor,
                sizeWeight,
                displayLabel,
            });
        }

        return map;
    }

    /**
     * RISK COLOR ONLY
     * Simpler derived property — just the hex color string based on risk score.
     * Use for node Fill Color in Vertex.
     */
    @Function()
    public addressRiskColor(addresses: Address[]): FunctionsMap<Address, string> {
        const map = new FunctionsMap<Address, string>();
        for (const addr of addresses) {
            const score = addr.riskScore ?? -1;
            const color = score >= 75 ? RISK_COLORS.critical
                : score >= 50 ? RISK_COLORS.high
                : score >= 25 ? RISK_COLORS.medium
                : score >= 0 ? RISK_COLORS.low
                : RISK_COLORS.unknown;
            map.set(addr, color);
        }
        return map;
    }

    /**
     * CHAIN COLOR
     * Hex color based on chain ID — for multi-chain styling.
     */
    @Function()
    public addressChainColor(addresses: Address[]): FunctionsMap<Address, string> {
        const map = new FunctionsMap<Address, string>();
        for (const addr of addresses) {
            const chainId = addr.chainId ?? "unknown";
            map.set(addr, CHAIN_COLORS[chainId] ?? DEFAULT_CHAIN_COLOR);
        }
        return map;
    }

    /**
     * NET FLOW LABEL
     * Shows net ETH flow direction and magnitude on the node.
     */
    @Function()
    public addressNetFlowLabel(addresses: Address[]): FunctionsMap<Address, string> {
        const map = new FunctionsMap<Address, string>();
        for (const addr of addresses) {
            const netFlow = addr.netFlowEth ?? 0;
            const direction = netFlow > 0 ? "▲" : netFlow < 0 ? "▼" : "—";
            const absFlow = Math.abs(netFlow);
            const label = absFlow >= 1000
                ? `${direction} ${(absFlow / 1000).toFixed(1)}K ETH`
                : `${direction} ${absFlow.toFixed(4)} ETH`;
            map.set(addr, label);
        }
        return map;
    }

    /**
     * TRANSACTION EDGE STYLING
     * Returns value label and chain color for Transaction edges.
     */
    @Function()
    public transactionEdgeStyle(transactions: Transaction[]): FunctionsMap<Transaction, TransactionEdgeStyle> {
        const map = new FunctionsMap<Transaction, TransactionEdgeStyle>();

        let maxValue = 0;
        for (const tx of transactions) {
            const v = tx.valueEth ?? 0;
            if (v > maxValue) { maxValue = v; }
        }

        for (const tx of transactions) {
            const value = tx.valueEth ?? 0;
            const chainId = tx.chainId ?? "unknown";
            const valueLabel = value >= 1000
                ? `${(value / 1000).toFixed(1)}K ETH`
                : `${value.toFixed(4)} ETH`;

            map.set(tx, {
                valueLabel,
                chainColor: CHAIN_COLORS[chainId] ?? DEFAULT_CHAIN_COLOR,
                weightNormalized: maxValue > 0 ? value / maxValue : 0.1,
            });
        }

        return map;
    }

    /**
     * TOKEN TRANSFER EDGE STYLING
     * Returns amount label, chain color, and token standard for Token Transfer edges.
     */
    @Function()
    public tokenTransferEdgeStyle(transfers: TokenTransfer[]): FunctionsMap<TokenTransfer, TokenTransferEdgeStyle> {
        const map = new FunctionsMap<TokenTransfer, TokenTransferEdgeStyle>();

        for (const tf of transfers) {
            const amount = tf.amount ?? 0;
            const symbol = tf.tokenSymbol ?? "???";
            const standard = tf.tokenStandard ?? "erc20";
            const chainId = tf.chainId ?? "unknown";
            const tokenId = tf.tokenId;

            let amountLabel: string;
            if (standard === "erc721" && tokenId) {
                amountLabel = `NFT #${tokenId}`;
            } else if (amount >= 1_000_000) {
                amountLabel = `${(amount / 1_000_000).toFixed(1)}M ${symbol}`;
            } else if (amount >= 1_000) {
                amountLabel = `${(amount / 1_000).toFixed(1)}K ${symbol}`;
            } else {
                amountLabel = `${amount.toFixed(2)} ${symbol}`;
            }

            map.set(tf, {
                amountLabel,
                chainColor: CHAIN_COLORS[chainId] ?? DEFAULT_CHAIN_COLOR,
                tokenStandard: standard,
            });
        }

        return map;
    }
}
