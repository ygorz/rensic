/**
 * Closed AIP brief + grounded paraphrase.
 * The model (or local paraphraser) may only speak from this JSON.
 */
import {
  ethFlow,
  investigatorNote,
  isSeedMembership,
  labeledCount,
  num,
  rankAddresses,
  windowDays,
  windowLabel,
  type Rankable,
} from "./desk";
import {
  entityCategories,
  isCommunityEntity,
  isOfficialEntity,
  lookupKnownEntity,
  seedExposureLine,
} from "./knownEntities";

export const AIP_BRIEF_COUNTERPARTY_CAP = 12;

export type AipCounterparty = {
  addressId: string;
  displayName: string | null;
  packName: string | null;
  investigatorLabel: string | null;
  categories: string[];
  tier: "official" | "community" | null;
  source: string | null;
  sourceUrl: string | null;
  ethIn: number;
  ethOut: number;
  ethFlow: number;
  txCount: number;
};

export type AipBrief = {
  schema: "rensic.aipBrief.v1";
  caseId: string | null;
  caseTitle: string | null;
  seedAddressId: string | null;
  chains: string[];
  windowDays: number | null;
  windowLabel: string;
  truncated: boolean;
  hop1AddressCount: number;
  labeledHop1Count: number;
  exposureLine: string | null;
  counterparties: AipCounterparty[];
  notes: string[];
};

export type AipNarrative = {
  paragraphs: string[];
  sourceUrls: string[];
  usedFields: string[];
  engine: "deterministic" | "aip-agent";
};

type CaseLike = {
  caseId?: string;
  caseTitle?: string;
  seedAddress?: string;
  chainIds?: string[];
  timeWindowStart?: string;
  timeWindowEnd?: string;
  addressCount?: number;
  transactionCount?: number;
};

function fmtEth(n: number): string {
  if (!Number.isFinite(n) || n === 0) {
    return "0";
  }
  const abs = Math.abs(n);
  let digits = 4;
  if (abs < 1) {
    digits = Math.min(12, Math.max(4, Math.ceil(-Math.log10(abs)) + 2));
  }
  const s = n.toFixed(digits).replace(/\.?0+$/, "");
  return s;
}

function counterpartyName(row: Rankable): {
  displayName: string | null;
  packName: string | null;
  investigatorLabel: string | null;
  categories: string[];
  tier: "official" | "community" | null;
  source: string | null;
  sourceUrl: string | null;
} {
  const ent = lookupKnownEntity(row.addressId);
  const packName = (ent?.name ?? "").trim() || null;
  const note = investigatorNote(row);
  const cats = ent ? entityCategories(ent).map(String) : [];
  let tier: "official" | "community" | null = null;
  if (isOfficialEntity(ent)) {
    tier = "official";
  } else if (isCommunityEntity(ent)) {
    tier = "community";
  }
  let displayName: string | null = null;
  if (tier === "official" && packName) {
    displayName = packName;
  } else if (note) {
    displayName = note;
  } else if (packName) {
    displayName = packName;
  }
  return {
    displayName,
    packName,
    investigatorLabel: note,
    categories: cats,
    tier,
    source: ent?.source ?? null,
    sourceUrl: ent?.sourceUrl ?? null,
  };
}

export function buildAipBrief(args: {
  caseObj: CaseLike | null;
  addresses: Rankable[];
  truncated?: boolean;
  counterpartyCap?: number;
}): AipBrief {
  const cap = args.counterpartyCap ?? AIP_BRIEF_COUNTERPARTY_CAP;
  const ranked = rankAddresses(args.addresses);
  const seed = ranked.find(isSeedMembership);
  const hop1 = ranked.filter((r) => !isSeedMembership(r));
  const days = windowDays(
    args.caseObj?.timeWindowStart,
    args.caseObj?.timeWindowEnd,
  );
  const truncated =
    args.truncated ??
    num(args.caseObj?.transactionCount) >= 200000;

  const counterparties: AipCounterparty[] = hop1.slice(0, cap).map((row) => {
    const names = counterpartyName(row);
    return {
      addressId: row.addressId ?? "",
      ...names,
      ethIn: num(row.totalValueInEth),
      ethOut: num(row.totalValueOutEth),
      ethFlow: ethFlow(row),
      txCount: num(row.transactionCountInCase),
    };
  });

  const notes: string[] = [];
  if (truncated) {
    notes.push(
      "Ingest hit Alchemy's page cap; treat counts as a stress test, not complete history.",
    );
  }
  const unlabeled = hop1.length - labeledCount(args.addresses);
  if (unlabeled > 0) {
    notes.push(
      `${unlabeled} of those addresses have no public name yet.`,
    );
  }

  return {
    schema: "rensic.aipBrief.v1",
    caseId: args.caseObj?.caseId ?? null,
    caseTitle: args.caseObj?.caseTitle ?? null,
    seedAddressId:
      seed?.addressId ?? args.caseObj?.seedAddress ?? null,
    chains: [...(args.caseObj?.chainIds ?? [])],
    windowDays: days,
    windowLabel: windowLabel(days),
    truncated,
    hop1AddressCount: hop1.length,
    labeledHop1Count: labeledCount(args.addresses),
    exposureLine: seedExposureLine(args.addresses) || null,
    counterparties,
    notes,
  };
}

/** Local short desk read from the brief only — no invented facts. */
export function paraphraseBrief(brief: AipBrief): AipNarrative {
  const paragraphs: string[] = [];
  const usedFields: string[] = [
    "windowLabel",
    "seedAddressId",
    "hop1AddressCount",
    "labeledHop1Count",
    "counterparties",
  ];
  const sourceUrls = [
    ...new Set(
      brief.counterparties
        .map((c) => c.sourceUrl)
        .filter((u): u is string => Boolean(u)),
    ),
  ];

  const windowBit = brief.windowLabel
    ? `the last ${brief.windowLabel}`
    : "this file's time window";
  const seedBit = brief.seedAddressId
    ? brief.seedAddressId.includes(":")
      ? brief.seedAddressId.split(":").slice(1).join(":")
      : brief.seedAddressId
    : "this wallet";
  const titleBit = brief.caseTitle ? ` (“${brief.caseTitle}”)` : "";

  let p1 = `In ${windowBit}${titleBit}, this file looks at ${seedBit} and the addresses it traded with.`;
  p1 += ` ${brief.hop1AddressCount} addresses show up in that set`;
  if (brief.labeledHop1Count > 0) {
    p1 += `; ${brief.labeledHop1Count} already have a public name or a label you set`;
  }
  p1 += ".";
  if (brief.exposureLine) {
    p1 += ` ${brief.exposureLine}.`;
    usedFields.push("exposureLine");
  }
  paragraphs.push(p1);

  const named = brief.counterparties.filter((c) => c.displayName);
  const top = brief.counterparties.slice(0, 5);
  if (top.length > 0) {
    if (named.length === 0) {
      paragraphs.push(
        "None of the top addresses in this window have a public name or label yet.",
      );
    } else {
      paragraphs.push("Biggest by ETH moved in this window:");
      for (const c of top) {
        const who = c.displayName ?? "Unlabeled address";
        const cat =
          c.categories.length > 0 ? ` (${c.categories[0]})` : "";
        const flow =
          c.ethFlow > 0 ? ` — about ${fmtEth(c.ethFlow)} ETH` : "";
        paragraphs.push(`${who}${cat}${flow}`);
      }
      if (top.some((c) => c.tier === "community" && c.displayName)) {
        paragraphs.push(
          "Some of those names come from a community list, not an official filing.",
        );
      }
    }
  }

  if (brief.notes.length > 0 || brief.truncated) {
    paragraphs.push(...brief.notes);
    usedFields.push("notes", "truncated");
  } else if (paragraphs.length < 2) {
    paragraphs.push(
      "No mixer or sanctions hit from the public pack stands out on this set. A missing name is not clearance.",
    );
    usedFields.push("counterparties.categories");
  }

  return {
    paragraphs,
    sourceUrls,
    usedFields: [...new Set(usedFields)],
    engine: "deterministic",
  };
}

/** Prompt body sent to an AIP Agent — brief only, paraphrase contract. */
export function aipAgentUserPrompt(brief: AipBrief): string {
  return [
    "Turn the following Rensic investigation brief into a short desk read.",
    "Rules:",
    "- Use ONLY facts present in the JSON.",
    "- Plain language: say addresses, names, ETH moved — not counterparties, hop-1, or ontology jargon.",
    "- Open with 1 short paragraph on the wallet and window.",
    "- Then a lead line like \"Biggest by ETH moved in this window:\" and one short line per top address.",
    "- Do not invent names, categories, amounts, hops, or risk scores.",
    "- Unlabeled addresses stay unlabeled; missing label is not clearance.",
    "- If any name is community-tier, add one quiet caveat line.",
    "- End with a short Sources list of sourceUrl values from the JSON when present.",
    "",
    "```json",
    JSON.stringify(brief, null, 2),
    "```",
  ].join("\n");
}
