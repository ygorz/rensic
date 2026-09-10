/**
 * Rensic — Ontology edit functions
 *
 * Function-backed actions for investigation lifecycle. These write Case Address
 * memberships so Address stays a global identity.
 *
 * Requires Ontology imports of CaseAddress and InvestigationNarrative after
 * the ontology-design-fixes global branch is merged.
 */
import { Integer, OntologyEditFunction, Timestamp } from "@foundry/functions-api";
import {
    Address,
    CaseAddress,
    InvestigationCase,
    InvestigationNarrative,
    Objects,
} from "@foundry/ontology-api";

function newId(): string {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        const v = c === "x" ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function caseAddressKey(caseId: string, addressId: string): string {
    return `${caseId}:${addressId}`;
}

export class RensicOntologyEdits {

    /**
     * Opens a case and registers the seed wallet as a Case Address (role=seed, hop=0).
     * Call from Workshop instead of the Create Investigation action when you need
     * both objects written in one submit.
     */
    @OntologyEditFunction()
    public openInvestigation(
        caseTitle: string,
        seedWalletAddress: string,
        targetChains: string[],
        lookbackDays: Integer,
    ): void {
        const title = (caseTitle ?? "").trim();
        const seed = (seedWalletAddress ?? "").trim();
        const chains = (targetChains ?? []).map(c => String(c).trim()).filter(Boolean);
        if (!title || !seed || chains.length === 0) {
            return;
        }
        const caseId = newId();
        const investigation = Objects.create().investigationCase(caseId);
        investigation.caseTitle = title;
        investigation.seedAddress = seed;
        investigation.chainIds = chains;
        investigation.investigationStatus = "draft";

        const now = Timestamp.now();
        investigation.createdAt = now;
        const days = Math.max(1, Number(lookbackDays) || 90);
        investigation.timeWindowEnd = now;
        investigation.timeWindowStart = Timestamp.fromJsDate(
            new Date(Date.now() - days * 24 * 60 * 60 * 1000),
        );

        const hex = seed.toLowerCase();
        for (const chain of chains) {
            const addressId = `${chain}:${hex}`;
            const membership = Objects.create().caseAddress(caseAddressKey(caseId, addressId));
            membership.caseId = caseId;
            membership.addressId = addressId;
            membership.membershipRole = "seed";
            membership.hopDistance = 0;
            membership.inclusionReason = "Seed wallet from Open Investigation";
        }
    }

    /**
     * Adds an existing Address to a case as an expanded counterparty.
     */
    @OntologyEditFunction()
    public expandInvestigation(
        investigationCase: InvestigationCase,
        address: Address,
        reason: string,
        hopDistance: Integer,
    ): void {
        const caseId = investigationCase.caseId;
        const addressId = address.addressId;
        if (!caseId || !addressId) {
            return;
        }
        const membership = Objects.create().caseAddress(caseAddressKey(caseId, addressId));
        membership.caseId = caseId;
        membership.addressId = addressId;
        membership.membershipRole = "expanded";
        membership.hopDistance = hopDistance;
        membership.inclusionReason = reason;
        investigationCase.investigationStatus = "active";
    }

    @OntologyEditFunction()
    public closeInvestigation(investigationCase: InvestigationCase): void {
        investigationCase.investigationStatus = "closed";
    }

    @OntologyEditFunction()
    public archiveInvestigation(investigationCase: InvestigationCase): void {
        investigationCase.investigationStatus = "archived";
    }

    /**
     * Persists a generated narrative onto Investigation Narrative and copies
     * the body onto caseSummary so existing Workshop text widgets still work.
     */
    @OntologyEditFunction()
    public saveInvestigationNarrative(
        investigationCase: InvestigationCase,
        body: string,
        narrativeType: string,
        focusAddressId?: string,
    ): void {
        const caseId = investigationCase.caseId;
        if (!caseId) {
            return;
        }
        investigationCase.caseSummary = body;

        const narrative = Objects.create().investigationNarrative(newId());
        narrative.caseId = caseId;
        narrative.body = body;
        narrative.narrativeType = narrativeType || "case_summary";
        narrative.focusAddressId = focusAddressId;
        narrative.sources = `Grounded in case ${caseId} ontology objects`;
        narrative.generatedAt = Timestamp.now();
    }

    /**
     * Hard-deletes an investigation case and its case-scoped rows.
     * Cascade via MultiLink on the InvestigationCase instance: caseAddresses,
     * narratives, then the InvestigationCase itself.
     * Does NOT delete global Address objects, known_entities, or shared ingest datasets.
     * (caseId is not searchable on ObjectSetFilter; do not Objects.search().filter by caseId.)
     */
    @OntologyEditFunction()
    public deleteInvestigation(investigationCase: InvestigationCase): void {
        for (const membership of investigationCase.caseAddresses.all()) {
            membership.delete();
        }
        for (const narrative of investigationCase.narratives.all()) {
            narrative.delete();
        }
        investigationCase.delete();
    }

}
