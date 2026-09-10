/** Pure helpers for ontology edit validation (offline-testable). */

export function caseAddressKey(caseId: string, addressId: string): string {
  return caseId + ":" + addressId;
}

export function normalizeSeed(seed: string): string {
  return (seed ?? "").trim().toLowerCase();
}

export function clampLookbackDays(lookbackDays: number): number {
  const days = Number(lookbackDays) || 90;
  return Math.max(1, days);
}

export function canOpenInvestigation(
  caseTitle: string,
  seedWalletAddress: string,
  targetChains: string[],
): boolean {
  const title = (caseTitle ?? "").trim();
  const seed = (seedWalletAddress ?? "").trim();
  const chains = (targetChains ?? []).map(c => String(c).trim()).filter(Boolean);
  return Boolean(title && seed && chains.length > 0);
}

export type PackTier = "official" | "community" | "unlabeled";

export function labelAddressPayload(
  tier: PackTier,
  proposedLabel: string,
  note: string,
  packName?: string,
): { ok: boolean; label: string; error?: string } {
  const name = (proposedLabel ?? "").trim();
  const n = (note ?? "").trim();
  if (tier === "official") {
    if (!n) return { ok: false, label: "", error: "Official pack: note required" };
    return { ok: true, label: n };
  }
  if (!name) return { ok: false, label: "", error: "Empty label" };
  if (tier === "community" || tier === "unlabeled") {
    return { ok: true, label: n ? name + " — " + n : name };
  }
  return { ok: false, label: "", error: "Unknown tier" };
}

/** Documented cascade for deleteInvestigation (pure; for tests/docs). */
export const DELETE_INVESTIGATION_CASCADE = [
  "CaseAddress memberships via caseAddresses MultiLink",
  "InvestigationNarrative rows via narratives MultiLink",
  "InvestigationCase itself",
] as const;

export const DELETE_INVESTIGATION_KEEPS = [
  "global Address objects",
  "known_entities pack",
  "shared Foundry ingest pipeline datasets",
] as const;
