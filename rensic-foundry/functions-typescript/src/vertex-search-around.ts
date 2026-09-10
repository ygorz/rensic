/**
 * Rensic — Vertex Search Around Functions (Graph Generation)
 * ============================================================
 *
 * These functions generate graph structures for Vertex visualization.
 * They start from one or more objects and discover connected entities.
 *
 * Usage:
 *   - Right-click an Address in Vertex → Search Around → "Fund Flow"
 *   - Graph Template: Start from InvestigationCase → expand to addresses → fund flow
 *   - Workshop Vertex widget with object set variables
 */
import { Function, Integer } from "@foundry/functions-api";
import {
    Address,
    InvestigationCase,
    Transaction,
    TokenTransfer,
    ContractInteraction,
} from "@foundry/ontology-api";

// ────────────────────────────────────────────────────────────────────────────
// Vertex Search Around result interface
// Name MUST be exactly "IGraphSearchAroundResultV1" for Vertex to discover it
// ────────────────────────────────────────────────────────────────────────────

interface IGraphSearchAroundResultDirectEdgeV1 {
    sourceObjectRid: string;
    targetObjectRid: string;
    linkTypeRid?: string;
    label?: string;
    direction?: string;
}

interface IGraphSearchAroundResultIntermediateEdgeV1 {
    sourceObjectRid: string;
    sourceToIntermediateLinkTypeRid?: string;
    intermediateObjectRid: string;
    intermediateToTargetLinkTypeRid?: string;
    targetObjectRid: string;
    label?: string;
    direction?: string;
}

interface IGraphSearchAroundResultV1 {
    directEdges?: IGraphSearchAroundResultDirectEdgeV1[];
    intermediateEdges?: IGraphSearchAroundResultIntermediateEdgeV1[];
    orphanObjectRids?: string[];
}

// ────────────────────────────────────────────────────────────────────────────
// Link Type RIDs (for showing link display names on edges)
// ────────────────────────────────────────────────────────────────────────────

const LINK_RIDS = {
    txFromAddress:    "ri.ontology.main.relation.fcedeb1c-8e9f-4425-82ef-65c3851957a6",
    txToAddress:      "ri.ontology.main.relation.8b7627ab-cfbe-4643-8d31-0d34de6b3274",
    txCase:           "ri.ontology.main.relation.c1e24dae-f04a-430b-b283-1db0ce2aab61",
    transferTx:       "ri.ontology.main.relation.8e1a4425-a8e1-4d82-ae53-23c91e8a63cd",
    transferFrom:     "ri.ontology.main.relation.63b4dea3-2311-4e80-b53b-1cfa50a62e62",
    transferTo:       "ri.ontology.main.relation.1ea7595f-50bb-4fa3-b6f6-17f526e59987",
    interactionTx:    "ri.ontology.main.relation.c2de0f1c-b83c-4317-a5ea-c40736c8add6",
    interactionAddr:  "ri.ontology.main.relation.17ddb7e8-1d16-4ca4-96c7-86473af92d04",
};

export class RensicVertexSearchAround {

    /**
     * FUND FLOW — Native ETH Transfers
     *
     * Starting from one or more Addresses, shows all Transactions between them
     * as intermediate edges (Address → [Transaction] → Address).
     *
     * The Transaction objects appear as grouped intermediate objects on the edge,
     * allowing users to click the edge to inspect individual transactions.
     */
    @Function()
    public async fundFlowTransactions(
        addresses: Address[]
    ): Promise<IGraphSearchAroundResultV1> {
        // Batch load all sent + received transactions for all addresses
        const [sentTxPromises, receivedTxPromises] = await Promise.all([
            Promise.all(addresses.map(a => a.sentTransactions.allAsync())),
            Promise.all(addresses.map(a => a.receivedTransactions.allAsync())),
        ]);

        // Collect all unique transactions
        const txSet = new Map<string, Transaction>();
        for (const txList of [...sentTxPromises, ...receivedTxPromises]) {
            for (const tx of txList) {
                if (tx.rid) {
                    txSet.set(tx.rid, tx);
                }
            }
        }

        // Build address RID lookup
        const addressRidMap = new Map<string, string>();
        for (const addr of addresses) {
            if (addr.rid && addr.addressId) {
                addressRidMap.set(addr.addressId, addr.rid);
            }
        }

        // Build intermediate edges: Sender Address → [Transaction] → Receiver Address
        const intermediateEdges: IGraphSearchAroundResultIntermediateEdgeV1[] = [];

        for (const tx of txSet.values()) {
            if (!tx.rid) { continue; }

            const fromRid = tx.fromAddressId ? addressRidMap.get(tx.fromAddressId) : undefined;
            const toRid = tx.toAddressId ? addressRidMap.get(tx.toAddressId) : undefined;

            // Only add edge if both ends are known addresses on the graph
            if (fromRid && toRid) {
                const valueLabel = tx.valueEth
                    ? `${tx.valueEth.toFixed(4)} ETH`
                    : "0 ETH";

                intermediateEdges.push({
                    sourceObjectRid: fromRid,
                    sourceToIntermediateLinkTypeRid: LINK_RIDS.txFromAddress,
                    intermediateObjectRid: tx.rid,
                    intermediateToTargetLinkTypeRid: LINK_RIDS.txToAddress,
                    targetObjectRid: toRid,
                    label: valueLabel,
                    direction: "FORWARD",
                });
            }
        }

        return { intermediateEdges };
    }

    /**
     * TOKEN FLOW — ERC-20/721/1155 Transfers
     *
     * Starting from one or more Addresses, shows all Token Transfers between them.
     * Each transfer appears as an intermediate object on the edge.
     */
    @Function()
    public async tokenFlow(
        addresses: Address[]
    ): Promise<IGraphSearchAroundResultV1> {
        const [outPromises, inPromises] = await Promise.all([
            Promise.all(addresses.map(a => a.outgoingTokenTransfers.allAsync())),
            Promise.all(addresses.map(a => a.incomingTokenTransfers.allAsync())),
        ]);

        const transferSet = new Map<string, TokenTransfer>();
        for (const list of [...outPromises, ...inPromises]) {
            for (const tf of list) {
                if (tf.rid) {
                    transferSet.set(tf.rid, tf);
                }
            }
        }

        const addressRidMap = new Map<string, string>();
        for (const addr of addresses) {
            if (addr.rid && addr.addressId) {
                addressRidMap.set(addr.addressId, addr.rid);
            }
        }

        const intermediateEdges: IGraphSearchAroundResultIntermediateEdgeV1[] = [];

        for (const tf of transferSet.values()) {
            if (!tf.rid) { continue; }

            const fromRid = tf.fromAddressId ? addressRidMap.get(tf.fromAddressId) : undefined;
            const toRid = tf.toAddressId ? addressRidMap.get(tf.toAddressId) : undefined;

            if (fromRid && toRid) {
                const amount = tf.amount ?? 0;
                const symbol = tf.tokenSymbol ?? "???";
                const label = amount >= 1000
                    ? `${(amount / 1000).toFixed(1)}K ${symbol}`
                    : `${amount.toFixed(2)} ${symbol}`;

                intermediateEdges.push({
                    sourceObjectRid: fromRid,
                    sourceToIntermediateLinkTypeRid: LINK_RIDS.transferFrom,
                    intermediateObjectRid: tf.rid,
                    intermediateToTargetLinkTypeRid: LINK_RIDS.transferTo,
                    targetObjectRid: toRid,
                    label,
                    direction: "FORWARD",
                });
            }
        }

        return { intermediateEdges };
    }

    /**
     * MULTI-HOP FUND FLOW
     *
     * Starting from one Address, traces outgoing transactions N hops deep.
     * Discovers the extended fund flow network.
     *
     * Parameters:
     *   - address: Starting address
     *   - hops: Number of hops to trace (1-3, default 1)
     */
    @Function()
    public async multiHopFundFlow(
        address: Address,
        hops: Integer
    ): Promise<IGraphSearchAroundResultV1> {
        const maxHops = Math.min(Math.max(hops, 1), 3); // Clamp to 1-3
        const directEdges: IGraphSearchAroundResultDirectEdgeV1[] = [];
        const seenAddressRids = new Set<string>();

        let currentAddresses = [address];
        if (address.rid) {
            seenAddressRids.add(address.rid);
        }

        for (let hop = 0; hop < maxHops; hop++) {
            // Load all sent transactions for current hop's addresses
            const sentTxBatches = await Promise.all(
                currentAddresses.map(a => a.sentTransactions.allAsync())
            );

            const nextHopAddresses: Address[] = [];

            for (let i = 0; i < currentAddresses.length; i++) {
                const sourceAddr = currentAddresses[i];
                if (!sourceAddr.rid) { continue; }

                // For each transaction, find the receiver address
                const receiverPromises = sentTxBatches[i].map(tx =>
                    tx.receiverAddress.getAsync()
                );
                const receivers = await Promise.all(receiverPromises);

                for (const receiver of receivers) {
                    if (!receiver || !receiver.rid) { continue; }

                    // Add direct edge (address to address)
                    directEdges.push({
                        sourceObjectRid: sourceAddr.rid,
                        targetObjectRid: receiver.rid,
                        direction: "FORWARD",
                    });

                    // Queue for next hop if not yet seen
                    if (!seenAddressRids.has(receiver.rid)) {
                        seenAddressRids.add(receiver.rid);
                        nextHopAddresses.push(receiver);
                    }
                }
            }

            currentAddresses = nextHopAddresses;
            if (currentAddresses.length === 0) { break; }
        }

        return { directEdges };
    }

    /**
     * INVESTIGATION CASE GRAPH
     *
     * Workshop / Vertex entry point: start from one or more Investigation Cases
     * and expand to the addresses and native ETH flows in that case.
     *
     * Uses caseTransactions (always present). After the ontology-design-fixes
     * branch is merged, also include Case Address memberships when imported.
     *
     * Bind this Search Around on the Rensic Workshop Vertex widget with the
     * selected Investigation Case object set as the seed.
     */
    @Function()
    public async investigationCaseGraph(
        cases: InvestigationCase[]
    ): Promise<IGraphSearchAroundResultV1> {
        const txBatches = await Promise.all(
            cases.map(c => c.caseTransactions.allAsync())
        );

        const txSet = new Map<string, Transaction>();
        for (const list of txBatches) {
            for (const tx of list) {
                if (tx.rid) {
                    txSet.set(tx.rid, tx);
                }
            }
        }

        const senderPromises = [...txSet.values()].map(tx => tx.senderAddress.getAsync());
        const receiverPromises = [...txSet.values()].map(tx => tx.receiverAddress.getAsync());
        const senders = await Promise.all(senderPromises);
        const receivers = await Promise.all(receiverPromises);

        const addressRidById = new Map<string, string>();
        const orphanObjectRids: string[] = [];
        for (const addr of [...senders, ...receivers]) {
            if (!addr || !addr.rid || !addr.addressId) { continue; }
            addressRidById.set(addr.addressId, addr.rid);
            orphanObjectRids.push(addr.rid);
        }

        const intermediateEdges: IGraphSearchAroundResultIntermediateEdgeV1[] = [];
        const txs = [...txSet.values()];
        for (let i = 0; i < txs.length; i++) {
            const tx = txs[i];
            if (!tx.rid) { continue; }
            const fromRid = tx.fromAddressId ? addressRidById.get(tx.fromAddressId) : undefined;
            const toRid = tx.toAddressId ? addressRidById.get(tx.toAddressId) : undefined;
            if (!fromRid || !toRid) { continue; }

            const valueLabel = tx.valueEth
                ? `${tx.valueEth.toFixed(4)} ETH`
                : "0 ETH";

            intermediateEdges.push({
                sourceObjectRid: fromRid,
                sourceToIntermediateLinkTypeRid: LINK_RIDS.txFromAddress,
                intermediateObjectRid: tx.rid,
                intermediateToTargetLinkTypeRid: LINK_RIDS.txToAddress,
                targetObjectRid: toRid,
                label: valueLabel,
                direction: "FORWARD",
            });
        }

        return {
            intermediateEdges,
            orphanObjectRids: [...new Set(orphanObjectRids)],
        };
    }

    /**
     * CONTRACT INTERACTION MAP
     *
     * Starting from one or more Addresses, shows which contracts they interacted with.
     * Useful for identifying protocol usage patterns (DEX, bridges, mixers).
     */
    @Function()
    public async contractInteractionMap(
        addresses: Address[]
    ): Promise<IGraphSearchAroundResultV1> {
        // Load all sent transactions (which may contain contract interactions)
        const sentTxBatches = await Promise.all(
            addresses.map(a => a.sentTransactions.allAsync())
        );

        // For each transaction, load contract interactions
        const allTxs = sentTxBatches.flat();
        const interactionBatches = await Promise.all(
            allTxs.map(tx => tx.contractInteractions.allAsync())
        );

        // For each interaction, load the contract address
        const allInteractions = interactionBatches.flat();
        const contractPromises = allInteractions.map(ci => ci.contract.getAsync());
        const contracts = await Promise.all(contractPromises);

        // Build address RID lookup
        const addressRidMap = new Map<string, string>();
        for (const addr of addresses) {
            if (addr.rid && addr.addressId) {
                addressRidMap.set(addr.addressId, addr.rid);
            }
        }

        const directEdges: IGraphSearchAroundResultDirectEdgeV1[] = [];
        const seenEdges = new Set<string>();

        for (let i = 0; i < allInteractions.length; i++) {
            const ci = allInteractions[i];
            const contract = contracts[i];
            if (!contract || !contract.rid) { continue; }

            // Find which address sent this transaction
            const tx = allTxs.find(t => t.transactionId === ci.transactionId);
            if (!tx) { continue; }

            const senderRid = tx.fromAddressId ? addressRidMap.get(tx.fromAddressId) : undefined;
            if (!senderRid) { continue; }

            const edgeKey = `${senderRid}->${contract.rid}`;
            if (seenEdges.has(edgeKey)) { continue; }
            seenEdges.add(edgeKey);

            const category = ci.interactionCategory ?? "unknown";
            const label = ci.contractLabel ?? category;

            directEdges.push({
                sourceObjectRid: senderRid,
                targetObjectRid: contract.rid,
                label,
                direction: "FORWARD",
            });
        }

        return { directEdges };
    }
}
