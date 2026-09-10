/**
 * Rensic Intelligence Layer — AIP Functions
 * ============================================
 *
 * LLM-powered investigation analysis functions:
 * 1. Investigation Narrative Generator — professional case summary
 * 2. Risk & Anomaly Detector — red flags, risk scoring, explanations
 * 3. Multi-Hop Tracer — path discovery and summarization
 *
 * All functions are grounded in ontology data — no hallucinations.
 * They gather structured data from the ontology, then ask the LLM to
 * synthesize it into human-readable analysis.
 */
import { Function, Integer } from "@foundry/functions-api";
import {
    InvestigationCase,
    Address,
    Transaction,
    TokenTransfer,
    ContractInteraction,
} from "@foundry/ontology-api";
import { AnthropicClaude_4_7_Opus } from "@foundry/models-api/language-models";

// ────────────────────────────────────────────────────────────────────────────
// System Prompts
// ────────────────────────────────────────────────────────────────────────────

const NARRATIVE_SYSTEM_PROMPT = `You are Rensic, a professional on-chain forensics analyst producing investigation reports.

Your role:
- Write clear, professional, factual summaries of on-chain wallet activity
- Structure reports with: Executive Summary, Key Findings, Fund Flow Summary, Notable Counterparties, and Recommendations
- Use precise language suitable for compliance officers, law enforcement, and AML analysts
- Always cite specific data: addresses (truncated), values, timestamps, token symbols
- Never speculate beyond what the data shows — if something is uncertain, say "possibly" or "indicates"
- Use bullet points and headers for readability
- Express monetary values in ETH and note token transfers separately

Format: Markdown with headers (##), bullet points, and bold for key terms.`;

const RISK_SYSTEM_PROMPT = `You are Rensic Risk Analyzer, a specialized on-chain risk assessment engine.

Your role:
- Analyze wallet activity data for red flags and suspicious patterns
- Assign a numeric risk score (0-100) with clear justification
- Categories of risk signals to check:
  * Mixer/privacy tool interaction (Tornado Cash, Railgun, etc.)
  * Rapid layering (many small transfers in short time to obfuscate source)
  * Sanctioned entity proximity (known OFAC-listed addresses)
  * Unusual DeFi patterns (flash loans, sandwich attacks, MEV)
  * Bridge usage to obscure cross-chain flows
  * Round-number transfers (common in laundering)
  * Dormant address reactivation
  * High-value transfers to newly created addresses
- For each detected signal, provide: signal name, severity (low/medium/high/critical), evidence, and explanation
- Be conservative — only flag genuine anomalies, not normal DeFi usage

Output format:
## Risk Score: [0-100]
## Risk Level: [low/medium/high/critical]
## Detected Signals:
- [Signal 1]: [severity] — [evidence and explanation]
## Recommendations:
- [Action items for investigator]`;

const TRACER_SYSTEM_PROMPT = `You are Rensic Tracer, a multi-hop fund flow analyst.

Your role:
- Analyze outgoing fund flows from a seed address across multiple hops
- Identify the most significant paths (by value, by risk, by endpoint type)
- Summarize where funds ultimately ended up
- Flag paths that pass through mixers, bridges, or high-risk intermediaries
- Note patterns: splitting (1 address → many), consolidation (many → 1), layering

Output format:
## Seed Address: [address]
## Tracing Summary:
- Total outflow: [X ETH + token transfers]
- Hops traced: [N]
- Significant endpoints: [list]

## Notable Paths:
### Path 1: [description]
- [hop-by-hop breakdown with values]
- Risk assessment: [why this path is notable]

## Conclusions:
- [Key takeaways for investigator]`;

// ────────────────────────────────────────────────────────────────────────────
// Intelligence Functions
// ────────────────────────────────────────────────────────────────────────────

export class RensicIntelligence {

    /**
     * INVESTIGATION NARRATIVE GENERATOR
     *
     * Produces a comprehensive, professional narrative summary of a case's
     * 90-day on-chain activity. Grounded entirely in ontology data.
     *
     * @param caseObject - The InvestigationCase to summarize
     * @returns Markdown-formatted investigation narrative
     */
    @Function()
    public async generateNarrative(caseObject: InvestigationCase): Promise<string> {
        // --- Gather grounded data from the ontology ---
        const transactions = await caseObject.caseTransactions.allAsync();
        const txCount = transactions.length;

        // Get unique addresses from transactions
        const addressIds = new Set<string>();
        let totalEthMoved = 0;
        const categoryBreakdown: { [key: string]: number } = {};

        for (const tx of transactions) {
            if (tx.fromAddressId) { addressIds.add(tx.fromAddressId); }
            if (tx.toAddressId) { addressIds.add(tx.toAddressId); }
            totalEthMoved += tx.valueEth ?? 0;
            const cat = tx.transactionCategory ?? "unknown";
            categoryBreakdown[cat] = (categoryBreakdown[cat] ?? 0) + 1;
        }

        // Get token transfers
        const tokenTransfers: TokenTransfer[] = [];
        for (const tx of transactions.slice(0, 50)) {
            const tfs = await tx.tokenTransfers.allAsync();
            tokenTransfers.push(...tfs);
        }

        // Build token summary
        const tokenSummary: { [symbol: string]: number } = {};
        for (const tf of tokenTransfers) {
            const sym = tf.tokenSymbol ?? "UNKNOWN";
            tokenSummary[sym] = (tokenSummary[sym] ?? 0) + (tf.amount ?? 0);
        }

        // Build the context for the LLM
        const context = `
## Investigation Case Data (GROUNDED — use ONLY this data)

**Case Title**: ${caseObject.caseTitle ?? "Untitled"}
**Seed Address**: ${caseObject.seedAddress ?? "Unknown"}
**Chains**: ${(caseObject.chainIds ?? []).join(", ")}
**Time Window**: ${caseObject.timeWindowStart ?? "N/A"} to ${caseObject.timeWindowEnd ?? "now"}
**Status**: ${caseObject.investigationStatus ?? "unknown"}

## Statistics
- Total transactions: ${txCount}
- Unique addresses involved: ${addressIds.size}
- Total native ETH moved: ${totalEthMoved.toFixed(4)} ETH
- Transaction categories: ${JSON.stringify(categoryBreakdown)}

## Token Transfer Summary
${Object.entries(tokenSummary).map(([sym, amt]) => `- ${sym}: ${amt.toFixed(2)}`).join("\n") || "- No token transfers detected"}

## Top Transactions (by value, first 10)
${[...transactions]
    .sort((a: Transaction, b: Transaction) => (b.valueEth ?? 0) - (a.valueEth ?? 0))
    .slice(0, 10)
    .map((tx: Transaction) => `- ${tx.transactionHash?.substring(0, 10)}... | ${tx.valueEth?.toFixed(4)} ETH | ${tx.fromAddressId?.split(":")[1]?.substring(0, 8)}... → ${tx.toAddressId?.split(":")[1]?.substring(0, 8)}... | ${tx.transactionCategory}`)
    .join("\n")}
`;

        const response = await AnthropicClaude_4_7_Opus.createGenericChatCompletion({
            params: { temperature: 0.2, maxTokens: 3000 },
            messages: [
                { role: "SYSTEM", contents: [{ text: NARRATIVE_SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: `Generate a professional investigation narrative based on the following case data. Use ONLY the data provided — do not invent or assume any information not present.\n\n${context}` }] },
            ],
        });

        return response.completion ?? "Unable to generate narrative. Please try again.";
    }

    /**
     * RISK & ANOMALY DETECTOR
     *
     * Analyzes an address's activity for red flags, assigns a risk score,
     * and provides explanations for each detected signal.
     *
     * @param address - The Address to analyze
     * @returns Markdown-formatted risk assessment
     */
    @Function()
    public async analyzeRisk(address: Address): Promise<string> {
        // --- Gather grounded data ---
        const sentTxs = await address.sentTransactions.allAsync();
        const receivedTxs = await address.receivedTransactions.allAsync();
        const outgoingTransfers = await address.outgoingTokenTransfers.allAsync();
        const incomingTransfers = await address.incomingTokenTransfers.allAsync();

        // Compute behavioral signals from data
        const totalTxs = sentTxs.length + receivedTxs.length;
        const totalSent = sentTxs.reduce((sum, tx) => sum + (tx.valueEth ?? 0), 0);
        const totalReceived = receivedTxs.reduce((sum, tx) => sum + (tx.valueEth ?? 0), 0);

        // Check for rapid transactions (multiple txs in same block or very close)
        const sentTimestamps = sentTxs
            .map(tx => tx.blockTimestamp)
            .filter(t => t !== undefined)
            .sort();

        // Unique counterparties
        const counterparties = new Set<string>();
        for (const tx of sentTxs) { if (tx.toAddressId) counterparties.add(tx.toAddressId); }
        for (const tx of receivedTxs) { if (tx.fromAddressId) counterparties.add(tx.fromAddressId); }

        // Token diversity
        const tokenSymbols = new Set<string>();
        for (const tf of [...outgoingTransfers, ...incomingTransfers]) {
            if (tf.tokenSymbol) tokenSymbols.add(tf.tokenSymbol);
        }

        // Contract interactions via sent transactions
        const contractInteractions: ContractInteraction[] = [];
        for (const tx of sentTxs.slice(0, 30)) {
            const cis = await tx.contractInteractions.allAsync();
            contractInteractions.push(...cis);
        }

        const interactionCategories: { [key: string]: number } = {};
        for (const ci of contractInteractions) {
            const cat = ci.interactionCategory ?? "unknown";
            interactionCategories[cat] = (interactionCategories[cat] ?? 0) + 1;
        }

        // Known high-risk patterns (data-based, not assumed)
        const knownMixerContracts = [
            "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b", // tornado cash
            "0x722122df12d4e14e13ac3b6895a86e84145b6967",
        ];
        const mixerInteractions = contractInteractions.filter(
            ci => knownMixerContracts.includes((ci.contractAddress ?? "").toLowerCase())
        );

        const context = `
## Address Activity Data (GROUNDED — analyze ONLY this data)

**Address**: ${address.walletAddress ?? "Unknown"}
**Chain**: ${address.chainId ?? "Unknown"}
**Type**: ${address.addressType ?? "Unknown"}
**Label**: ${address.addressLabel ?? "None"}
**Current Risk Score**: ${address.riskScore ?? "Not set"}

## Activity Summary
- Total transactions: ${totalTxs} (${sentTxs.length} sent, ${receivedTxs.length} received)
- Total ETH sent: ${totalSent.toFixed(4)} ETH
- Total ETH received: ${totalReceived.toFixed(4)} ETH
- Net flow: ${(totalReceived - totalSent).toFixed(4)} ETH
- Unique counterparties: ${counterparties.size}
- Token types interacted with: ${[...tokenSymbols].join(", ") || "none"}

## Contract Interaction Breakdown
${Object.entries(interactionCategories).map(([cat, count]) => `- ${cat}: ${count}`).join("\n") || "- No contract interactions"}

## Known Risk Indicators Found
- Mixer interactions detected: ${mixerInteractions.length > 0 ? `YES (${mixerInteractions.length} interactions)` : "None"}
- Bridge usage: ${interactionCategories["bridge"] ? `YES (${interactionCategories["bridge"]} times)` : "None detected"}
- Rapid transaction frequency: ${sentTxs.length > 20 ? "HIGH" : sentTxs.length > 10 ? "MODERATE" : "LOW"}

## Transaction Pattern (sent, first 15)
${sentTxs.slice(0, 15).map(tx =>
    `- ${tx.blockTimestamp?.toString().substring(0, 10)} | ${tx.valueEth?.toFixed(4)} ETH → ${tx.toAddressId?.split(":")[1]?.substring(0, 10)}... | ${tx.transactionCategory}`
).join("\n")}
`;

        const response = await AnthropicClaude_4_7_Opus.createGenericChatCompletion({
            params: { temperature: 0.1, maxTokens: 2000 },
            messages: [
                { role: "SYSTEM", contents: [{ text: RISK_SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: `Analyze the following address for risk and anomalies. Base your assessment SOLELY on the provided data. Do not assume information not present.\n\n${context}` }] },
            ],
        });

        return response.completion ?? "Unable to complete risk analysis. Please try again.";
    }

    /**
     * MULTI-HOP TRACER
     *
     * Traces outgoing fund flows from a seed address up to N hops,
     * then asks the LLM to summarize the most significant paths.
     *
     * @param seedAddress - Starting address to trace from
     * @param maxHops - Number of hops to trace (1-3)
     * @returns Markdown-formatted tracing summary
     */
    @Function()
    public async traceMultiHop(
        seedAddress: Address,
        maxHops: Integer,
    ): Promise<string> {
        const hops = Math.min(Math.max(maxHops, 1), 3);

        // --- Trace outgoing paths hop by hop ---
        interface HopRecord {
            hop: number;
            fromAddress: string;
            toAddress: string;
            valueEth: number;
            category: string;
            txHash: string;
        }

        const allHops: HopRecord[] = [];
        let currentAddresses = [seedAddress];
        const visitedIds = new Set<string>();
        if (seedAddress.addressId) { visitedIds.add(seedAddress.addressId); }

        for (let hop = 1; hop <= hops; hop++) {
            const nextAddresses: Address[] = [];

            for (const addr of currentAddresses) {
                const sentTxs = await addr.sentTransactions.allAsync();

                for (const tx of sentTxs.slice(0, 20)) {
                    const receiver = await tx.receiverAddress.getAsync();
                    if (!receiver || !receiver.addressId) { continue; }

                    allHops.push({
                        hop,
                        fromAddress: addr.walletAddress ?? addr.addressId ?? "?",
                        toAddress: receiver.walletAddress ?? receiver.addressId ?? "?",
                        valueEth: tx.valueEth ?? 0,
                        category: tx.transactionCategory ?? "unknown",
                        txHash: tx.transactionHash ?? "?",
                    });

                    if (!visitedIds.has(receiver.addressId)) {
                        visitedIds.add(receiver.addressId);
                        nextAddresses.push(receiver);
                    }
                }
            }

            currentAddresses = nextAddresses.slice(0, 10); // Limit breadth
            if (currentAddresses.length === 0) { break; }
        }

        // Build context for LLM
        const hopsByLevel: { [hop: number]: HopRecord[] } = {};
        for (const h of allHops) {
            if (!hopsByLevel[h.hop]) { hopsByLevel[h.hop] = []; }
            hopsByLevel[h.hop].push(h);
        }

        const context = `
## Multi-Hop Trace Data (GROUNDED — analyze ONLY this data)

**Seed Address**: ${seedAddress.walletAddress ?? "Unknown"}
**Chain**: ${seedAddress.chainId ?? "Unknown"}
**Label**: ${seedAddress.addressLabel ?? "None"}
**Hops Traced**: ${hops}
**Total Paths Found**: ${allHops.length}

## Hop-by-Hop Breakdown
${Object.entries(hopsByLevel).map(([hop, records]) => `
### Hop ${hop} (${records.length} transfers)
${records.sort((a, b) => b.valueEth - a.valueEth).slice(0, 15).map(r =>
    `- ${r.fromAddress.substring(0, 10)}... → ${r.toAddress.substring(0, 10)}... | ${r.valueEth.toFixed(4)} ETH | ${r.category}`
).join("\n")}`).join("\n")}

## Summary Statistics
- Total ETH traced: ${allHops.reduce((s, h) => s + h.valueEth, 0).toFixed(4)} ETH
- Unique intermediate addresses: ${visitedIds.size - 1}
- Addresses reached at final hop: ${currentAddresses.length}
`;

        const response = await AnthropicClaude_4_7_Opus.createGenericChatCompletion({
            params: { temperature: 0.2, maxTokens: 2500 },
            messages: [
                { role: "SYSTEM", contents: [{ text: TRACER_SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: `Trace and summarize the following multi-hop fund flow data. Identify the most significant paths and endpoints. Base analysis ONLY on provided data.\n\n${context}` }] },
            ],
        });

        return response.completion ?? "Unable to complete multi-hop trace. Please try again.";
    }
}
