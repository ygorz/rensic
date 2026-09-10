import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { Client, Osdk } from "@osdk/client";
import { useOsdkClient } from "@osdk/react";
import {
  Address,
  CaseAddress,
  InvestigationCase,
  TokenTransfer,
  Transaction,
  labelAddress,
  saveInvestigationNarrative,
} from "@rensic/sdk";
import css from "./CaseView.module.css";
import {
  DESK_LIST_FETCH_CAP,
  DESK_PAGE_SIZE,
  PAGE_CAP_TX_COUNT,
  addressMatchKey,
  deskPageCount,
  deskPageRangeLabel,
  deskPageSlice,
  investigatorNote,
  isSeedMembership,
  num,
  PAIR_FLOW_PAGE_SIZE,
  PAIR_FLOW_TX_CAP,
  pairEthFlow,
  rankAddresses,
  windowDays,
  windowFact,
  windowLabel,
} from "./desk";
import {
  type EntityCategory,
  entityCategories,
  isCommunityEntity,
  isOfficialEntity,
  lookupKnownEntity,
  seedExposureLine,
} from "./knownEntities";
import {
  buildAipBrief,
  type AipNarrative,
} from "./aipBrief";
import { runAipParaphrase } from "./aipAgent";
import {
  explorerAddressHref,
  explorerName,
  explorerTxHref,
  getDeskChain,
} from "./chains";

/** Minimal OSDK action stub until @rensic/sdk regenerates with deleteInvestigation. */
const deleteInvestigation = {
  apiName: "deleteInvestigation",
  type: "action" as const,
  unsanitizedApiName: "delete-investigation",
};




const CASE_ADDR_SELECT = [
  "caseAddressId",
  "addressId",
  "membershipRole",
  "hopDistance",
  "transactionCountInCase",
  "totalValueInEth",
  "totalValueOutEth",
  "netFlowEth",
] as const;

const TX_SELECT = [
  "transactionId",
  "transactionHash",
  "fromAddressId",
  "toAddressId",
  "valueEth",
  "blockTimestamp",
  "transactionCategory",
] as const;

const PAIR_TX_SELECT = [...TX_SELECT, "transactionStatus"] as const;

const TOKEN_SELECT = [
  "transferId",
  "tokenSymbol",
  "fromAddressId",
  "toAddressId",
  "amount",
  "blockTimestamp",
  "transactionId",
] as const;

type Tab = "graph" | "addresses" | "transactions" | "tokens" | "analyst";

type CaseAddr = Osdk.Instance<CaseAddress>;
type DeskAddr = CaseAddr & { addressLabel?: string };
type AddrOverlay = {
  addressLabel?: string;
  transactionCount?: number;
  totalValueInEth?: number;
  totalValueOutEth?: number;
};
type TxSort = "newest" | "eth";
type AddrSortKey = "transfers";
type AddrSort = { key: AddrSortKey; dir: "asc" | "desc" };
type TxRow = Osdk.Instance<Transaction>;
type TokenRow = Osdk.Instance<TokenTransfer>;
type AddrObj = Osdk.Instance<Address> & { $rid?: string };
type CaseObj = Osdk.Instance<InvestigationCase> & { $rid?: string };
type TxDir = "In" | "Out" | "Internal" | "Other";

function asRows<T>(data: readonly unknown[]): T[] {
  return data as T[];
}

function asObj<T>(value: unknown): T {
  return value as T;
}

function fmtEth(n: number | undefined | null): string {
  if (n == null || Number.isNaN(Number(n))) {
    return "-";
  }
  const v = Number(n);
  if (v === 0) {
    return "0";
  }
  const abs = Math.abs(v);
  let digits = 4;
  if (abs < 1) {
    digits = Math.min(12, Math.max(4, Math.ceil(-Math.log10(abs)) + 2));
  }
  return v.toLocaleString("en-US", {
    maximumFractionDigits: digits,
    useGrouping: abs >= 1000,
  });
}

function fmtAmt(n: number | undefined | null): string {
  if (n == null || Number.isNaN(Number(n))) {
    return "-";
  }
  const v = Number(n);
  if (v === 0) {
    return "0";
  }
  const abs = Math.abs(v);
  if (abs >= 1e6) {
    return v.toLocaleString("en-US", {
      maximumFractionDigits: 2,
      useGrouping: true,
    });
  }
  let digits = 6;
  if (abs < 1) {
    // Same idea as fmtEth: enough decimals to show the value, never scientific.
    digits = Math.min(12, Math.max(6, Math.ceil(-Math.log10(abs)) + 2));
  }
  return v.toLocaleString("en-US", {
    maximumFractionDigits: digits,
    useGrouping: abs >= 1000,
  });
}

function fmtCount(n: number | undefined | null): string {
  if (n == null || Number.isNaN(Number(n))) {
    return "-";
  }
  return String(n);
}

function shortAddr(id: string | undefined): string {
  if (!id) {
    return "-";
  }
  const parts = id.split(":");
  const addr = parts[parts.length - 1] ?? id;
  if (addr.length <= 14) {
    return addr;
  }
  return `${addr.slice(0, 8)}...${addr.slice(-6)}`;
}

function clipboardAddress(id: string | undefined): string {
  if (!id) {
    return "";
  }
  const i = id.lastIndexOf(":");
  return (i >= 0 ? id.slice(i + 1) : id).trim();
}

function displayAddr(id: string | undefined, label?: string): string {
  const ent = lookupKnownEntity(id);
  const pack = (ent?.name ?? "").trim();
  const t = (label ?? "").trim();
  // Official pack name always wins for ledger title.
  if (isOfficialEntity(ent) && pack) {
    return pack;
  }
  // Community: investigator Flag wins for display; pack stays secondary on hover.
  if (isCommunityEntity(ent)) {
    return t || pack || shortAddr(id);
  }
  return t || pack || shortAddr(id);
}

function categoryChipClass(cat: EntityCategory, community = false): string {
  if (community) {
    return `${css.pill} ${css.catCommunity}`;
  }
  if (cat === "sanctions" || cat === "mixer") {
    return `${css.pill} ${css.catRisk}`;
  }
  return `${css.pill} ${css.catPack}`;
}

function CategoryChips(props: { id?: string; row?: DeskAddr }): React.ReactElement | null {
  const ent = lookupKnownEntity(props.id);
  const cats = entityCategories(ent);
  const community = isCommunityEntity(ent);
  const note = props.row ? investigatorNote(props.row) : null;
  if (!cats.length && !note) {
    return null;
  }
  return (
    <span className={css.chipRow}>
      {cats.map((c) => (
        <span
          key={c}
          className={categoryChipClass(c, community)}
          title={community ? "Community label (unofficial)" : "Official pack label"}
        >
          {c}
        </span>
      ))}
      {note ? <span className={`${css.pill} ${css.catNote}`}>my note: {note}</span> : null}
    </span>
  );
}

function fmtShortDate(value: unknown): string {
  if (value == null) {
    return "-";
  }
  try {
    const d = new Date(String(value));
    if (Number.isNaN(d.getTime())) {
      return String(value);
    }
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
  } catch {
    return String(value);
  }
}

function candidateAddressIds(id: string | undefined): string[] {
  if (!id) {
    return [];
  }
  const out: string[] = [];
  const add = (v: string) => {
    if (v && !out.includes(v)) {
      out.push(v);
    }
  };
  add(id);
  const lower = id.toLowerCase();
  add(lower);
  const parts = lower.split(":");
  const hex = parts[parts.length - 1] ?? "";
  const chain = parts[0] ?? "";
  if (chain && hex && hex !== chain) {
    add(`${chain}:${hex}`);
  }
  return out;
}

function txCounterparty(tx: TxRow, dir: TxDir): string | undefined {
  if (dir === "In") {
    return tx.fromAddressId;
  }
  if (dir === "Out") {
    return tx.toAddressId;
  }
  return tx.toAddressId || tx.fromAddressId;
}

function chainOf(id: string | undefined, fallback?: string): string {
  if (id) {
    const i = id.indexOf(":");
    if (i > 0) {
      return id.slice(0, i);
    }
  }
  return fallback || "ethereum";
}


function txDirection(tx: TxRow, selected: string | null): TxDir {
  if (!selected) {
    return "Other";
  }
  const from = addressMatchKey(tx.fromAddressId) === addressMatchKey(selected);
  const to = addressMatchKey(tx.toAddressId) === addressMatchKey(selected);
  if (from && to) {
    return "Internal";
  }
  if (to) {
    return "In";
  }
  if (from) {
    return "Out";
  }
  return "Other";
}

function dirClass(d: TxDir): string {
  if (d === "In") {
    return css.dirIn;
  }
  if (d === "Out") {
    return css.dirOut;
  }
  if (d === "Internal") {
    return css.dirInternal;
  }
  return css.dirOther;
}

function formatOsdkError(e: unknown): string {
  if (e && typeof e === "object") {
    const err = e as {
      message?: string;
      errorName?: string;
      errorType?: string;
      statusCode?: number;
      parameters?: unknown;
    };
    const bits = [
      err.errorName,
      err.errorType,
      err.statusCode != null ? String(err.statusCode) : undefined,
      err.message,
    ].filter(Boolean);
    if (err.parameters != null) {
      bits.push(JSON.stringify(err.parameters));
    }
    if (bits.length) {
      return bits.join(" - ");
    }
  }
  return e instanceof Error ? e.message : String(e);
}

function seedAddressId(
  rows: CaseAddr[],
  caseObj: { seedAddress?: string; chainIds?: string[] },
): string | null {
  const seedRow = rows.find(isSeedMembership);
  if (seedRow?.addressId) {
    return seedRow.addressId;
  }
  const raw = caseObj.seedAddress;
  if (!raw) {
    return null;
  }
  if (raw.includes(":")) {
    return raw;
  }
  const chain = caseObj.chainIds?.[0] ?? "ethereum";
  return `${chain}:${raw}`;
}

function rowKeyDown(
  e: React.KeyboardEvent,
  addressId: string | undefined,
  toggle: (id: string | undefined) => void,
): void {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    toggle(addressId);
  }
}

function IconClipboard(props: { className?: string }): React.ReactElement {
  return (
    <svg className={props.className} viewBox="0 0 14 14" aria-hidden="true">
      <rect x="3" y="3.4" width="8" height="8.8" rx="1.1" />
      <rect x="5" y="1.7" width="4" height="2.6" rx="0.55" />
    </svg>
  );
}

function IconCheck(props: { className?: string }): React.ReactElement {
  return (
    <svg className={props.className} viewBox="0 0 14 14" aria-hidden="true">
      <path d="M2.8 7.2l2.9 2.9 5.5-6.2" />
    </svg>
  );
}

function IconFlow(props: { className?: string; dir: "left" | "right" }): React.ReactElement {
  const d =
    props.dir === "right"
      ? "M2.8 7h8.4M8.6 4.2 11.2 7l-2.6 2.8"
      : "M11.2 7H2.8M5.4 4.2 2.8 7l2.6 2.8";
  return (
    <svg className={props.className} viewBox="0 0 14 14" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

function IconExternal(props: { className?: string }): React.ReactElement {
  return (
    <svg className={props.className} viewBox="0 0 14 14" aria-hidden="true">
      <path d="M5.5 2.5H3.6A1.1 1.1 0 0 0 2.5 3.6v6.8A1.1 1.1 0 0 0 3.6 11.5h6.8A1.1 1.1 0 0 0 11.5 10.4V8.5" />
      <path d="M8.2 2.5h3.3V5.8" />
      <path d="M11.5 2.5L6.6 7.4" />
    </svg>
  );
}

type AddrHoverFacts = {
  membershipRole?: string;
  hopDistance?: number | string;
  totalValueInEth?: number | string;
  totalValueOutEth?: number | string;
  addressType?: string;
  investigatorLabel?: string;
};

function factsForAddress(
  id: string | undefined,
  rows: DeskAddr[],
  overlay?: { addressId?: string; addressLabel?: string; addressType?: string } | null,
): AddrHoverFacts | undefined {
  if (!id) {
    return undefined;
  }
  const row = rows.find((a) => a.addressId === id);
  const ov = overlay && overlay.addressId === id ? overlay : null;
  return {
    membershipRole: row?.membershipRole,
    hopDistance: row?.hopDistance,
    totalValueInEth: row?.totalValueInEth,
    totalValueOutEth: row?.totalValueOutEth,
    investigatorLabel: row?.addressLabel ?? ov?.addressLabel,
    addressType: ov?.addressType,
  };
}


function AddrBits(props: {
  id: string | undefined;
  kind?: "address" | "tx";
  chain?: string;
  copyKey: string;
  copiedKey: string | null;
  copyHoldKey?: string | null;
  onCopy: (text: string, key: string) => void;
  highlight?: boolean;
  display?: string;
  showText?: boolean;
  facts?: AddrHoverFacts;
  leadIcons?: boolean;
}): React.ReactElement {
  const {
    id,
    kind = "address",
    chain,
    copyKey,
    copiedKey,
    copyHoldKey = null,
    onCopy,
    highlight,
    display,
    showText = true,
    facts,
    leadIcons = false,
  } = props;
  const href = kind === "tx" ? explorerTxHref(id, chain) : explorerAddressHref(id, chain);
  const scan = explorerName(chainOf(id, chain));
  const copied = copiedKey === copyKey;
  const held = copied || copyHoldKey === copyKey;
  const pack = kind === "address" ? lookupKnownEntity(id) : undefined;
  const note = (facts?.investigatorLabel ?? "").trim();
  const role = (facts?.membershipRole ?? "").trim();
  const hop =
    facts?.hopDistance == null || facts.hopDistance === ""
      ? null
      : Number(facts.hopDistance);
  const addrType = (facts?.addressType ?? "").trim();
  const hasCaseFacts = Boolean(role) || (hop != null && !Number.isNaN(hop));
  const hasCard =
    kind === "address" && Boolean(pack || note || hasCaseFacts || addrType);
  const [open, setOpen] = React.useState(false);
  const showCard = hasCard && open;
  const actions = (
    <>
      {id ? (
        <button
          type="button"
          className={css.iconBtn}
          aria-label={copied ? "Copied" : "Copy"}
          title={copied ? "Copied" : "Copy"}
          onClick={(e) => {
            e.stopPropagation();
            onCopy(kind === "address" ? clipboardAddress(id) : id, copyKey);
          }}
        >
          <span className={css.iconSlot}>
            <IconClipboard className={copied ? undefined : css.iconOn} />
            <IconCheck className={copied ? css.iconOn : undefined} />
          </span>
        </button>
      ) : null}
      {href ? (
        <a
          className={css.iconLink}
          href={href}
          target="_blank"
          rel="noreferrer"
          title={scan}
          aria-label={scan}
          onClick={(e) => e.stopPropagation()}
        >
          <span className={css.iconSlot}>
            <IconExternal className={css.iconOn} />
          </span>
        </a>
      ) : null}
    </>
  );

  return (
    <span
      className={`${css.addrBits} ${highlight ? css.peer : ""} ${held ? css.addrBitsHold : ""} ${leadIcons ? css.addrLead : ""}`}
      onMouseEnter={() => hasCard && setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => hasCard && setOpen(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          setOpen(false);
        }
      }}
    >
      {leadIcons ? <span className={css.addrLeadIcons}>{actions}</span> : null}
      {showText ? (
        <span className={css.mono} title={id ?? ""}>
          {display || shortAddr(id)}
        </span>
      ) : null}
      {leadIcons ? null : actions}
      {showCard ? (
        <span className={css.hoverCard} role="tooltip">
          <span className={css.hoverTitle}>
            {isCommunityEntity(pack) && note && note.toLowerCase() !== (pack?.name ?? "").toLowerCase()
              ? note
              : pack?.name || note || display || shortAddr(id)}
            {isCommunityEntity(pack) ? (
              <span className={`${css.tierBadge} ${css.tierCommunity}`}>unofficial</span>
            ) : null}
          </span>
          {pack ? (
            <span className={css.chipRow}>
              {entityCategories(pack).map((c) => (
                <span key={c} className={categoryChipClass(c, isCommunityEntity(pack))}>
                  {c}
                </span>
              ))}
            </span>
          ) : null}
          {isCommunityEntity(pack) && note && note.toLowerCase() !== (pack?.name ?? "").toLowerCase() ? (
            <span className={css.hoverLine}>Public name: {pack?.name}</span>
          ) : null}
          {isOfficialEntity(pack) && note && note.toLowerCase() !== (pack?.name ?? "").toLowerCase() ? (
            <span className={css.hoverLine}>Note: {note}</span>
          ) : null}
          {!pack && note ? <span className={css.hoverLine}>Note: {note}</span> : null}
          {pack?.sourceUrl ? (
            <span className={css.hoverLine}>
              Source:{" "}
              <a
                href={pack.sourceUrl}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                {(() => {
                  try {
                    return new URL(pack.sourceUrl).host.replace(/^www\./, "");
                  } catch {
                    return pack.sourceUrl;
                  }
                })()}
              </a>
            </span>
          ) : pack?.source && pack.source.toLowerCase() !== "public" ? (
            <span className={css.hoverLine}>Source: {pack.source}</span>
          ) : null}
        </span>
      ) : null}
    </span>
  );
}

async function fetchWorkingSet(
  client: Client,
  caseId: string,
  caseObj: Osdk.Instance<InvestigationCase>,
): Promise<{ rows: CaseAddr[]; note: string | null }> {
  const seedP = client(CaseAddress)
    .where({
      $and: [{ caseId: { $eq: caseId } }, { membershipRole: { $eq: "seed" } }],
    })
    .fetchPage({
      $pageSize: 10,
      $includeRid: true,
      $select: [...CASE_ADDR_SELECT],
    })
    .then((p) => asRows<CaseAddr>(p.data))
    .catch(() => [] as CaseAddr[]);

  let pageRows: CaseAddr[] = [];
  let note: string | null = null;

  async function loadCaseAddresses(orderByOut: boolean): Promise<CaseAddr[]> {
    const rows: CaseAddr[] = [];
    let token: string | undefined;
    while (rows.length < DESK_LIST_FETCH_CAP) {
      const page = await client(CaseAddress)
        .where({ caseId: { $eq: caseId } })
        .fetchPage({
          $pageSize: Math.min(100, DESK_LIST_FETCH_CAP - rows.length),
          ...(orderByOut ? { $orderBy: { totalValueOutEth: "desc" as const } } : {}),
          ...(token ? { $nextPageToken: token } : {}),
          $includeRid: true,
          $select: [...CASE_ADDR_SELECT],
        });
      rows.push(...asRows<CaseAddr>(page.data));
      token = page.nextPageToken;
      if (!token) {
        break;
      }
    }
    return rows;
  }

  try {
    pageRows = await loadCaseAddresses(true);
  } catch (e1) {
    try {
      pageRows = await loadCaseAddresses(false);
      note =
        "CaseAddress $orderBy unavailable; unsorted pages. " + formatOsdkError(e1);
    } catch (e2) {
      try {
        const rows: CaseAddr[] = [];
        let token: string | undefined;
        while (rows.length < DESK_LIST_FETCH_CAP) {
          const page = await caseObj.$link.caseAddresses.fetchPage({
            $pageSize: Math.min(100, DESK_LIST_FETCH_CAP - rows.length),
            ...(token ? { $nextPageToken: token } : {}),
            $includeRid: true,
            $select: [...CASE_ADDR_SELECT],
          });
          rows.push(...asRows<CaseAddr>(page.data));
          token = page.nextPageToken;
          if (!token) {
            break;
          }
        }
        pageRows = rows;
        note =
          "CaseAddress.where failed; used link fetchPage, ranked client-side. " +
          formatOsdkError(e2);
      } catch (e3) {
        try {
          const seeds = await seedP;
          return {
            rows: rankAddresses(seeds),
            note: "addresses: " + formatOsdkError(e3),
          };
        } catch {
          throw e3;
        }
      }
    }
  }

  const seeds = await seedP;
  return { rows: rankAddresses([...seeds, ...pageRows]), note };
}

const ADDR_OVERLAY_SELECT = [
  "addressId",
  "addressLabel",
  "transactionCount",
  "totalValueInEth",
  "totalValueOutEth",
] as const;

function asMaybeNum(v: number | string | undefined | null): number | undefined {
  if (v == null || v === "") {
    return undefined;
  }
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
}

function overlayFromAddress(a: {
  addressId?: string;
  addressLabel?: string;
  transactionCount?: number | string;
  totalValueInEth?: number | string;
  totalValueOutEth?: number | string;
}): AddrOverlay {
  return {
    addressLabel: a.addressLabel,
    transactionCount: asMaybeNum(a.transactionCount),
    totalValueInEth: asMaybeNum(a.totalValueInEth),
    totalValueOutEth: asMaybeNum(a.totalValueOutEth),
  };
}

function applyAddressOverlay(rows: CaseAddr[], overlay: Record<string, AddrOverlay>): DeskAddr[] {
  return rows.map((row) => {
    let o: AddrOverlay | undefined;
    for (const k of candidateAddressIds(row.addressId)) {
      if (overlay[k]) {
        o = overlay[k];
        break;
      }
    }
    if (!o) {
      return row as DeskAddr;
    }
    return {
      ...row,
      addressLabel: o.addressLabel,
      transactionCountInCase: row.transactionCountInCase ?? o.transactionCount,
      totalValueInEth: row.totalValueInEth ?? o.totalValueInEth,
      totalValueOutEth: row.totalValueOutEth ?? o.totalValueOutEth,
    } as DeskAddr;
  });
}

async function fetchAddressOverlay(
  client: Client,
  rows: CaseAddr[],
): Promise<Record<string, AddrOverlay>> {
  const overlay: Record<string, AddrOverlay> = {};
  const ids: string[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    for (const id of candidateAddressIds(row.addressId)) {
      if (!seen.has(id)) {
        seen.add(id);
        ids.push(id);
      }
    }
  }
  if (!ids.length) {
    return overlay;
  }

  const put = (a: {
    addressId?: string;
    addressLabel?: string;
    transactionCount?: number | string;
    totalValueInEth?: number | string;
    totalValueOutEth?: number | string;
  }) => {
    if (!a.addressId) {
      return;
    }
    const rec = overlayFromAddress(a);
    overlay[a.addressId] = rec;
    overlay[a.addressId.toLowerCase()] = rec;
  };

  try {
    const page = await client(Address)
      .where({ addressId: { $in: ids } })
      .fetchPage({
        $pageSize: 100,
        $select: [...ADDR_OVERLAY_SELECT],
      });
    for (const a of page.data) {
      put(a);
    }
  } catch {
    // $in unavailable; fetchOne / link below
  }

  const missing = rows.filter((row) => {
    return !candidateAddressIds(row.addressId).some((id) => overlay[id]);
  });
  const cap = missing.slice(0, 40);
  await Promise.all(
    cap.map(async (row) => {
      try {
        const linked = row as CaseAddr & {
          $link?: {
            address?: {
              fetch: (opts?: { $select?: readonly string[] }) => Promise<{
                addressId?: string;
                addressLabel?: string;
                transactionCount?: number;
                totalValueInEth?: number;
                totalValueOutEth?: number;
              }>;
            };
          };
        };
        const a = await linked.$link?.address?.fetch({
          $select: [...ADDR_OVERLAY_SELECT],
        });
        if (a) {
          put(a);
          return;
        }
      } catch {
        // try fetchOne
      }
      for (const id of candidateAddressIds(row.addressId)) {
        try {
          const a = await client(Address).fetchOne(id, {
            $select: [...ADDR_OVERLAY_SELECT],
          });
          put(a);
          return;
        } catch {
          // next candidate
        }
      }
    }),
  );

  return overlay;
}

async function fetchFileWalletEthTransfers(
  client: Client,
  caseId: string,
  fileWalletId: string,
  caseObj: Osdk.Instance<InvestigationCase>,
): Promise<{ rows: TxRow[]; note: string | null }> {
  const ids = candidateAddressIds(fileWalletId);
  const where = {
    $and: [
      { caseId: { $eq: caseId } },
      {
        $or: ids.flatMap((id) => [
          { fromAddressId: { $eq: id } },
          { toAddressId: { $eq: id } },
        ]),
      },
    ],
  };

  async function pages(orderByValue: boolean): Promise<TxRow[]> {
    const rows: TxRow[] = [];
    let token: string | undefined;
    while (rows.length < PAIR_FLOW_TX_CAP) {
      const page = await client(Transaction)
        .where(where)
        .fetchPage({
          $pageSize: PAIR_FLOW_PAGE_SIZE,
          ...(orderByValue ? { $orderBy: { valueEth: "desc" as const } } : {}),
          ...(token ? { $nextPageToken: token } : {}),
          $select: [...PAIR_TX_SELECT],
        });
      rows.push(...asRows<TxRow>(page.data));
      token = page.nextPageToken;
      if (!token) {
        break;
      }
    }
    return rows.slice(0, PAIR_FLOW_TX_CAP);
  }

  try {
    return { rows: await pages(true), note: null };
  } catch {
    try {
      return {
        rows: await pages(false),
        note: null,
      };
    } catch (e2) {
      try {
        const page = await caseObj.$link.caseTransactions.fetchPage({
          $pageSize: PAIR_FLOW_PAGE_SIZE,
          $select: [...PAIR_TX_SELECT],
        });
        const keys = new Set(ids.map((id) => id.toLowerCase()));
        const filtered = asRows<TxRow>(page.data).filter(
          (tx) =>
            keys.has((tx.fromAddressId ?? "").toLowerCase()) ||
            keys.has((tx.toAddressId ?? "").toLowerCase()),
        );
        return {
          rows: filtered,
          note:
            filtered.length === 0
              ? "Transaction $where unavailable; filtered a linked page client-side. " +
                formatOsdkError(e2)
              : null,
        };
      } catch (e3) {
        return { rows: [], note: "transactions: " + formatOsdkError(e3) };
      }
    }
  }
}

function CaseView(): React.ReactElement {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const client = useOsdkClient();
  const [caseObj, setCaseObj] = useState<CaseObj | null>(null);
  const [addresses, setAddresses] = useState<DeskAddr[]>([]);
  const [txs, setTxs] = useState<TxRow[]>([]);
  const [tokens, setTokens] = useState<TokenRow[]>([]);
  const [selectedAddr, setSelectedAddr] = useState<AddrObj | null>(null);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [aipNarrative, setAipNarrative] = useState<AipNarrative | null>(null);
  const [aipBusy, setAipBusy] = useState(false);
  const [aipErr, setAipErr] = useState<string | null>(null);
  const [aipShowBrief, setAipShowBrief] = useState(false);
  const [aipSaveBusy, setAipSaveBusy] = useState(false);
  const [aipSaveNote, setAipSaveNote] = useState<string | null>(null);
  const [addrQuery, setAddrQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [linkNote, setLinkNote] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("addresses");
  const [txNote, setTxNote] = useState<string | null>(null);
  const [tokenNote, setTokenNote] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [copyHoldKey, setCopyHoldKey] = useState<string | null>(null);
  const [flowQuietKey, setFlowQuietKey] = useState<string | null>(null);
  const [txFor, setTxFor] = useState<string | null>(null);
  const [tokenFor, setTokenFor] = useState<string | null>(null);
  const [txSort, setTxSort] = useState<TxSort>("newest");
  const [addrSort, setAddrSort] = useState<AddrSort | null>(null);
  const [flowPage, setFlowPage] = useState(1);
  const [addrPage, setAddrPage] = useState(1);
  const [txPage, setTxPage] = useState(1);
  const [tokenPage, setTokenPage] = useState(1);
  const [flagOpen, setFlagOpen] = useState(false);
  const [flagName, setFlagName] = useState("");
  const [flagNote, setFlagNote] = useState("");
  const [flagBusy, setFlagBusy] = useState(false);
  const [flagErr, setFlagErr] = useState<string | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteErr, setDeleteErr] = useState<string | null>(null);
  const [seedFlowTxs, setSeedFlowTxs] = useState<TxRow[]>([]);
  const [seedFlowFor, setSeedFlowFor] = useState<string | null>(null);
  const [seedFlowErr, setSeedFlowErr] = useState<string | null>(null);

  function toggleSelect(addressId: string | undefined): void {
    if (!addressId) {
      return;
    }
    setSelectedAddressId((cur) => (cur === addressId ? null : addressId));
  }

  function selectOnly(addressId: string | undefined): void {
    if (!addressId) {
      return;
    }
    setSelectedAddressId(addressId);
  }

  async function onFlag(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    if (!selectedAddressId) {
      return;
    }
    const packEnt = lookupKnownEntity(selectedAddressId);
    const official = isOfficialEntity(packEnt);
    const name = flagName.trim();
    const note = flagNote.trim();
    // Official pack: do not overwrite pack name in ledger title; note-only allowed.
    if (official) {
      if (!note) {
        setFlagErr("Official pack label cannot be renamed. Add a note only.");
        return;
      }
    } else if (!name) {
      return;
    }
    const label = official ? note : note ? `${name} | ${note}` : name;
    // Quiet seed ethereum:0x6d77... often has CaseAddress from openInvestigation,
    // but Address only after clean_to_ontology — Flag needs the Address object.
    if (!selectedAddr) {
      setFlagErr(
        "Address object not in ontology yet. Run ingest so this wallet exists as an Address, then Flag.",
      );
      return;
    }
    setFlagBusy(true);
    setFlagErr(null);
    try {
      // Existing OSDK action "Label Address" writes Address.addressLabel.
      // Do not pass address-type: pack category and addressType stay as-is.
      // flagForReview is case-level and is the wrong object.
      // Official: displayAddr still shows pack name; note surfaces as investigator note.
      // Prefer fetched OSDK instance; bare string PK can serialize as primaryKey: {} / ObjectNotFound.
      await client(labelAddress).applyAction({
        address: selectedAddr,
        label,
      });
      setAddresses((rows) =>
        rankAddresses(
          rows.map((r) =>
            r.addressId === selectedAddressId ? ({ ...r, addressLabel: label } as DeskAddr) : r,
          ),
        ),
      );
      setSelectedAddr((cur) => (cur ? ({ ...cur, addressLabel: label } as AddrObj) : cur));
      setFlagOpen(false);
      setFlagName("");
      setFlagNote("");
    } catch (err) {
      const msg = formatOsdkError(err);
      if (/ObjectNotFound|not found|primaryKey/i.test(msg)) {
        setFlagErr(
          "Address object not in ontology yet. Run ingest so this wallet exists as an Address, then Flag.",
        );
      } else {
        setFlagErr(msg);
      }
    } finally {
      setFlagBusy(false);
    }
  }

  async function onDeleteInvestigation(): Promise<void> {
    if (!caseObj) {
      return;
    }
    setDeleteBusy(true);
    setDeleteErr(null);
    try {
      // Function-backed action: cascades CaseAddress + InvestigationNarrative, then case.
      // Does not delete global Address rows or ingest datasets.
      const action = client(
        deleteInvestigation as unknown as typeof labelAddress,
      );
      await action.applyAction({
        "investigation-case": caseObj,
      } as never);
      setDeleteOpen(false);
      navigate("/");
    } catch (err) {
      setDeleteErr(formatOsdkError(err));
    } finally {
      setDeleteBusy(false);
    }
  }

  function onCopy(text: string, key: string): void {
    void navigator.clipboard.writeText(text).then(
      () => {
        setCopiedKey(key);
        setCopyHoldKey(key);
        window.setTimeout(() => {
          setCopiedKey((cur) => (cur === key ? null : cur));
        }, 1600);
        window.setTimeout(() => {
          setCopyHoldKey((cur) => (cur === key ? null : cur));
          if (key.startsWith("flow:")) {
            setFlowQuietKey(key);
          }
          const active = document.activeElement;
          if (active instanceof HTMLElement) {
            active.blur();
          }
        }, 1900);
      },
      () => undefined,
    );
  }

  useEffect(() => {
    if (!caseId) {
      return;
    }
    setTab("addresses");
    setSelectedAddressId(null);
    setSelectedAddr(null);
    setAddresses([]);
    setTxs([]);
    setTokens([]);
    setCaseObj(null);
    setError(null);
    setLinkNote(null);
    setTxNote(null);
    setTokenNote(null);
    setAddrQuery("");
    setCopiedKey(null);
    setTxFor(null);
    setTokenFor(null);
    setTxSort("newest");
    setAddrSort(null);
    setFlowPage(1);
    setAddrPage(1);
    setTxPage(1);
    setTokenPage(1);
    setFlagOpen(false);
    setFlagName("");
    setFlagNote("");
    setFlagBusy(false);
    setDeleteOpen(false);
    setDeleteBusy(false);
    setDeleteErr(null);
    setFlagErr(null);

    let cancelled = false;
    (async () => {
      try {
        const obj = await client(InvestigationCase).fetchOne(caseId, {
          $includeRid: true,
          $select: [
            "caseId",
            "caseTitle",
            "investigationStatus",
            "seedAddress",
            "chainIds",
            "caseSummary",
            "transactionCount",
            "addressCount",
            "totalValueMovedEth",
            "timeWindowStart",
            "timeWindowEnd",
            "highRiskAddressCount",
            "uniqueTokenCount",
          ],
        });
        if (cancelled) {
          return;
        }
        let rows: CaseAddr[] = [];
        let note: string | null = null;
        try {
          const fetched = await fetchWorkingSet(
            client,
            caseId,
            asObj<Osdk.Instance<InvestigationCase>>(obj),
          );
          rows = fetched.rows;
          note = fetched.note;
        } catch (e) {
          note = "addresses: " + formatOsdkError(e);
        }
        if (cancelled) {
          return;
        }
        try {
          const over = await fetchAddressOverlay(client, rows);
          rows = rankAddresses(applyAddressOverlay(rows, over));
        } catch {
          // keep CaseAddress metrics; do not coerce remaining nulls to 0
        }
        if (cancelled) {
          return;
        }
        setCaseObj(asObj<CaseObj>(obj));
        setAddresses(rows);
        setLinkNote(note);
        setSelectedAddressId(seedAddressId(rows, obj));
      } catch (e) {
        if (!cancelled) {
          setError(formatOsdkError(e));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [caseId, client]);

  useEffect(() => {
    if (!selectedAddressId) {
      setSelectedAddr(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const addr = await client(Address).fetchOne(selectedAddressId, {
          $includeRid: true,
          $select: ["addressId", "walletAddress", "addressLabel", "addressType"],
        });
        if (!cancelled) {
          setSelectedAddr(asObj<AddrObj>(addr));
        }
      } catch {
        if (!cancelled) {
          setSelectedAddr(null);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedAddressId, client]);

  const seedId = caseObj ? seedAddressId(addresses, caseObj) : null;

  useEffect(() => {
    if (!caseId || !caseObj || !seedId) {
      setTxs([]);
      setTxNote(null);
      setTxFor(null);
      return;
    }
    let cancelled = false;
    (async () => {
      const apply = (rows: readonly unknown[], note: string | null) => {
        if (!cancelled) {
          setTxs(asRows<TxRow>(rows));
          setTxNote(note);
          setTxFor(seedId);
          setTxPage(1);
        }
      };
      const ids = candidateAddressIds(seedId);
      const where = {
        $and: [
          { caseId: { $eq: caseId } },
          {
            $or: ids.flatMap((id) => [
              { fromAddressId: { $eq: id } },
              { toAddressId: { $eq: id } },
            ]),
          },
        ],
      };

      async function load(orderByTime: boolean): Promise<TxRow[]> {
        const rows: TxRow[] = [];
        let token: string | undefined;
        while (rows.length < DESK_LIST_FETCH_CAP) {
          const page = await client(Transaction)
            .where(where)
            .fetchPage({
              $pageSize: Math.min(DESK_PAGE_SIZE, DESK_LIST_FETCH_CAP - rows.length),
              ...(orderByTime
                ? { $orderBy: { blockTimestamp: "desc" as const } }
                : {}),
              ...(token ? { $nextPageToken: token } : {}),
              $select: [...TX_SELECT],
            });
          rows.push(...asRows<TxRow>(page.data));
          token = page.nextPageToken;
          if (!token) {
            break;
          }
        }
        return rows;
      }

      try {
        apply(await load(true), null);
      } catch (e1) {
        try {
          apply(
            await load(false),
            "Transaction $orderBy unavailable; unsorted pages. " + formatOsdkError(e1),
          );
        } catch (e2) {
          try {
            const page = await caseObj.$link.caseTransactions.fetchPage({
              $pageSize: 100,
              $select: [...TX_SELECT],
            });
            const idSet = new Set(ids.map(addressMatchKey));
            const filtered = asRows<TxRow>(page.data).filter(
              (tx) =>
                idSet.has(addressMatchKey(tx.fromAddressId)) ||
                idSet.has(addressMatchKey(tx.toAddressId)),
            );
            apply(
              filtered,
              "Transaction $where unavailable; filtered a linked page client-side. " +
                formatOsdkError(e2),
            );
          } catch (e3) {
            apply([], "transactions: " + formatOsdkError(e3));
          }
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [caseId, caseObj, seedId, client]);


  useEffect(() => {
    if (!caseId || !caseObj || !seedId) {
      setSeedFlowTxs([]);
      setSeedFlowFor(null);
      setSeedFlowErr(null);
      return;
    }
    let cancelled = false;
    setSeedFlowFor(null);
    setSeedFlowErr(null);
    (async () => {
      const got = await fetchFileWalletEthTransfers(client, caseId, seedId, caseObj);
      if (cancelled) {
        return;
      }
      setSeedFlowTxs(got.rows);
      setSeedFlowFor(seedId);
      setSeedFlowErr(got.rows.length === 0 ? got.note : null);
    })();
    return () => {
      cancelled = true;
    };
  }, [caseId, caseObj, seedId, client]);


  useEffect(() => {
    if (!seedId) {
      setTokens([]);
      setTokenNote(null);
      setTokenFor(null);
      return;
    }
    let cancelled = false;
    (async () => {
      const apply = (rows: readonly unknown[], note: string | null) => {
        if (!cancelled) {
          setTokens(asRows<TokenRow>(rows));
          setTokenNote(note);
          setTokenFor(seedId);
          setTokenPage(1);
        }
      };
      const ids = candidateAddressIds(seedId);
      const where = {
        $or: ids.flatMap((id) => [
          { fromAddressId: { $eq: id } },
          { toAddressId: { $eq: id } },
        ]),
      };

      async function load(orderByTime: boolean): Promise<TokenRow[]> {
        const rows: TokenRow[] = [];
        let token: string | undefined;
        while (rows.length < DESK_LIST_FETCH_CAP) {
          const page = await client(TokenTransfer)
            .where(where)
            .fetchPage({
              $pageSize: Math.min(DESK_PAGE_SIZE, DESK_LIST_FETCH_CAP - rows.length),
              ...(orderByTime
                ? { $orderBy: { blockTimestamp: "desc" as const } }
                : {}),
              ...(token ? { $nextPageToken: token } : {}),
              $select: [...TOKEN_SELECT],
            });
          rows.push(...asRows<TokenRow>(page.data));
          token = page.nextPageToken;
          if (!token) {
            break;
          }
        }
        return rows;
      }

      try {
        apply(await load(true), null);
      } catch (e1) {
        try {
          apply(
            await load(false),
            "TokenTransfer $orderBy unavailable; unsorted pages. " + formatOsdkError(e1),
          );
        } catch (e2) {
          apply(
            [],
            "TokenTransfer.where failed (no caseId on this object). " + formatOsdkError(e2),
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [seedId, client]);


  const filteredAddresses = useMemo(() => {
    const q = addrQuery.trim().toLowerCase();
    if (!q) {
      return addresses;
    }
    return addresses.filter((a) => {
      const id = (a.addressId ?? "").toLowerCase();
      const label = (a.addressLabel ?? "").toLowerCase();
      const pack = lookupKnownEntity(a.addressId);
      const packName = (pack?.name ?? "").toLowerCase();
      const cats = entityCategories(pack).join(" ");
      return id.includes(q) || label.includes(q) || packName.includes(q) || cats.includes(q);
    });
  }, [addresses, addrQuery]);

  const addressesView = useMemo(() => {
    if (!addrSort) {
      return filteredAddresses;
    }
    const rows = filteredAddresses.slice();
    const dir = addrSort.dir === "asc" ? 1 : -1;
    rows.sort((a, b) => {
      const av = num(a.transactionCountInCase);
      const bv = num(b.transactionCountInCase);
      if (av === bv) {
        return (a.addressId ?? "").localeCompare(b.addressId ?? "");
      }
      return (av - bv) * dir;
    });
    return rows;
  }, [filteredAddresses, addrSort]);

  useEffect(() => {
    setAddrPage(1);
  }, [addrQuery, addrSort]);

  useEffect(() => {
    setFlowPage(1);
  }, [seedId, seedFlowFor]);

  useEffect(() => {
    setTxPage(1);
  }, [txSort, seedId]);

  function toggleAddrSort(key: AddrSortKey): void {
    setAddrSort((cur) => {
      if (!cur || cur.key !== key) {
        return { key, dir: "desc" };
      }
      if (cur.dir === "desc") {
        return { key, dir: "asc" };
      }
      return null;
    });
  }

  const showSelectedInRail = Boolean(selectedAddressId && seedId && selectedAddressId !== seedId);
  const aipBrief = useMemo(
    () =>
      buildAipBrief({
        caseObj,
        addresses,
        truncated: num(caseObj?.transactionCount) >= PAGE_CAP_TX_COUNT,
      }),
    [caseObj, addresses],
  );

  async function generateAipNarrative(): Promise<void> {
    if (aipBusy) {
      return;
    }
    setAipBusy(true);
    setAipErr(null);
    setAipSaveNote(null);
    try {
      const narrative = await runAipParaphrase(client, aipBrief);
      setAipNarrative(narrative);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Could not write summary.";
      setAipErr(msg);
    } finally {
      setAipBusy(false);
    }
  }

  async function saveAipNarrative(): Promise<void> {
    if (!caseObj || !aipNarrative || aipSaveBusy) {
      return;
    }
    setAipSaveBusy(true);
    setAipSaveNote(null);
    try {
      const body = [
        ...aipNarrative.paragraphs,
        aipNarrative.sourceUrls.length
          ? `Sources: ${aipNarrative.sourceUrls.join(", ")}`
          : "",
      ]
        .filter(Boolean)
        .join("\n\n");
      await client(saveInvestigationNarrative).applyAction({
        body,
        "investigation-case": caseObj,
        "narrative-type": "aip",
        "focus-address-id": seedId,
      });
      setAipSaveNote("Saved to this file.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Could not save narrative";
      setAipSaveNote(msg);
    } finally {
      setAipSaveBusy(false);
    }
  }

  const chainHint = caseObj?.chainIds?.[0];
  const txsShown = useMemo(
    () => (seedId && txFor === seedId ? txs : []),
    [txFor, seedId, txs],
  );
  const txsSorted = useMemo(() => {
    const rows = txsShown.slice();
    if (txSort === "eth") {
      rows.sort((a, b) => num(b.valueEth) - num(a.valueEth));
      return rows;
    }
    rows.sort((a, b) => {
      const tb = Date.parse(String(b.blockTimestamp ?? ""));
      const ta = Date.parse(String(a.blockTimestamp ?? ""));
      const nb = Number.isNaN(tb) ? 0 : tb;
      const na = Number.isNaN(ta) ? 0 : ta;
      return nb - na;
    });
    return rows;
  }, [txsShown, txSort]);
  const txsLoading = Boolean(seedId) && txFor !== seedId;
  const tokensShown = seedId && tokenFor === seedId ? tokens : [];
  const tokensLoading = Boolean(seedId) && tokenFor !== seedId;
  const truncated = (caseObj?.transactionCount ?? 0) >= PAGE_CAP_TX_COUNT;
  const lookbackDays = caseObj ? windowDays(caseObj.timeWindowStart, caseObj.timeWindowEnd) : null;
  const windowFactLine = windowFact(lookbackDays, truncated);

  if (error) {
    return (
      <div className={css.page}>
        <p className={css.note}>{error}</p>
      </div>
    );
  }
  if (!caseObj) {
    return (
      <div className={css.page}>
        <p className={css.loadingFile}>Loading file</p>
      </div>
    );
  }

  const seedMem = addresses.find(isSeedMembership);
  const discovered = addresses.filter((a) => !isSeedMembership(a));
  const emptySlice = discovered.length === 0 && num(seedMem?.transactionCountInCase) === 0;
  const railEth =
    seedMem != null ? num(seedMem.totalValueInEth) + num(seedMem.totalValueOutEth) : undefined;
  const nativeSymbol = getDeskChain(caseObj.chainIds?.[0]).nativeSymbol;
  const railTx = seedMem?.transactionCountInCase;
  const railAddr = discovered.length;
  const railLabeledRisk = addresses.filter((a) => {
    const cats = entityCategories(lookupKnownEntity(a.addressId));
    return cats.includes("sanctions") || cats.includes("mixer");
  }).length;

  const tabs: { id: Tab; label: string; blurb: string }[] = [
    {
      id: "graph",
      label: "Fund flow",
      blurb: `Who this wallet sent ${nativeSymbol} to, and who sent ${nativeSymbol} to this wallet.`,
    },
    {
      id: "addresses",
      label: "Addresses",
      blurb:
        "Addresses seen in this wallet's transfers.",
    },
    {
      id: "transactions",
      label: "Transactions",
      blurb: `Native ${nativeSymbol} transfers for this wallet.`,
    },
    {
      id: "tokens",
      label: "Token transfers",
      blurb: "Token transfers for this wallet.",
    },
    {
      id: "analyst",
      label: "Summary",
      blurb: "A short read of this wallet over the window.",
    },
  ];
  const tabBlurb = tabs.find((t) => t.id === tab)?.blurb;

  const pairFlow =
    seedId && seedFlowFor === seedId
      ? pairEthFlow(seedId, seedFlowTxs).filter(
          (row) => addressMatchKey(row.addressId) !== addressMatchKey(seedId),
        )
      : [];
  const pairFlowLoading = Boolean(seedId) && seedFlowFor !== seedId;
  const pairFlowPage = deskPageSlice(pairFlow, flowPage);
  const addressesPage = deskPageSlice(addressesView, addrPage);
  const txsPage = deskPageSlice(txsSorted, txPage);
  const tokensPage = deskPageSlice(tokensShown, tokenPage);
  const exposure = seedExposureLine(addresses);
  const selectedPack = lookupKnownEntity(selectedAddressId ?? undefined);
  const seedPack = lookupKnownEntity(seedId ?? caseObj.seedAddress);
  const seedDesk = seedId
    ? addresses.find((a) => addressMatchKey(a.addressId) === addressMatchKey(seedId))
    : undefined;
  const selectedDesk = addresses.find((a) => a.addressId === selectedAddressId);
  const selectedNote = investigatorNote(selectedDesk ?? {});

  return (
    <div className={css.page}>
      <aside className={css.rail}>
        <div className={css.railSection}>
        <div className={css.row}>
          <span>Wallet</span>
          <b>
            <AddrBits
              id={caseObj.seedAddress}
              chain={chainHint}
              leadIcons
              copyKey="rail-seed"
              copiedKey={copiedKey}
              copyHoldKey={copyHoldKey}
              onCopy={onCopy}
              display={displayAddr(caseObj.seedAddress, seedPack?.name)}
              facts={{
                membershipRole: seedMem?.membershipRole,
                hopDistance: seedMem?.hopDistance,
                totalValueInEth: seedMem?.totalValueInEth,
                totalValueOutEth: seedMem?.totalValueOutEth,
                addressType:
                  seedId && selectedAddressId === seedId
                    ? selectedAddr?.addressType
                    : undefined,
              }}
            />
          </b>
        </div>
        {showSelectedInRail ? (
          <div className={css.row}>
            <span>Selected</span>
            <b>
              <AddrBits
                id={selectedAddressId ?? undefined}
                chain={chainHint}
                copyKey="rail-selected"
                copiedKey={copiedKey}
              copyHoldKey={copyHoldKey}
                onCopy={onCopy}
                display={displayAddr(
                  selectedAddressId ?? undefined,
                  selectedAddr?.addressLabel ?? selectedPack?.name,
                )}
                facts={{
                  membershipRole: selectedDesk?.membershipRole,
                  hopDistance: selectedDesk?.hopDistance,
                  totalValueInEth: selectedDesk?.totalValueInEth,
                  totalValueOutEth: selectedDesk?.totalValueOutEth,
                  investigatorLabel: selectedAddr?.addressLabel,
                  addressType: selectedAddr?.addressType,
                }}
              />
            </b>
          </div>
        ) : null}
        {selectedPack || selectedNote ? (
          <div className={css.row}>
            <span>Listed as</span>
            <b>
              <CategoryChips id={selectedAddressId ?? undefined} row={selectedDesk} />
            </b>
          </div>
        ) : null}
        </div>
        <div className={css.railSection}>
        <p className={css.exposure}>{exposure}</p>
        <div className={css.row}>
          <span>Chain</span>
          <b>{caseObj.chainIds?.[0] ? getDeskChain(caseObj.chainIds[0]).displayName : "-"}</b>
        </div>
        <div className={css.row}>
          <span>Window</span>
          <b>
            {windowLabel(lookbackDays) || "-"} {fmtShortDate(caseObj.timeWindowStart)} -{" "}
            {fmtShortDate(caseObj.timeWindowEnd)}
          </b>
        </div>
        </div>
        <div className={css.railSection}>
        <div className={css.row}>
          <span className={css.rowLabel}>
            {nativeSymbol} moved
            <button type="button" className={css.infoMark} aria-label="About ETH moved">
              i
              <span className={css.infoCard} role="tooltip">
                In plus out for this wallet, in this window. Not a net.
              </span>
            </button>
          </span>
          <b className={css.num}>{fmtEth(railEth)}</b>
        </div>
        <div className={css.row}>
          <span>Addresses touched</span>
          <b className={css.num}>{fmtCount(railAddr)}</b>
        </div>
        <div className={css.row}>
          <span>Transfers</span>
          <b className={css.num}>{fmtCount(railTx)}</b>
        </div>
        <div className={css.row}>
          <span className={css.rowLabel}>
            Sanctions / mixers
            <button type="button" className={css.infoMark} aria-label="About sanctions and mixers">
              i
              <span className={css.infoCard} role="tooltip">
                Named from the public list. Not a risk score.
              </span>
            </button>
          </span>
          <b className={css.num}>{fmtCount(railLabeledRisk)}</b>
        </div>
        </div>
        <div className={css.railSection}>
        <div className={css.actions}>
          <div className={css.actionMenu}>
            <button
              type="button"
              className={flagOpen ? css.actionOn : undefined}
              disabled={!selectedAddressId}
              title={!selectedAddressId ? "Select an address" : "Name this address"}
              onClick={() => {
                setFlagOpen((v) => !v);
                setDeleteOpen(false);
                setFlagErr(null);
              }}
            >
              Flag
            </button>
            {flagOpen ? (
              <form className={css.actionPop} onSubmit={(e) => void onFlag(e)}>
                <div className={css.actionPopHead}>
                  <span>Flag</span>
                  <button
                    type="button"
                    className={css.actionClose}
                    aria-label="Close"
                    onClick={() => setFlagOpen(false)}
                  />
                </div>
                {isOfficialEntity(selectedPack) ? (
                  <p className={css.flagWarn}>
                    {selectedPack?.name} is a public name. You can add a note, not rename it.
                  </p>
                ) : null}
                {isCommunityEntity(selectedPack) ? (
                  <p className={css.flagWarn}>
                    Unofficial name. Your name replaces it on this file.
                  </p>
                ) : null}
                <label className={css.flagLabel}>
                  Name
                  <input
                    value={flagName}
                    onChange={(ev) => setFlagName(ev.target.value)}
                    placeholder="Name"
                    required={!isOfficialEntity(selectedPack)}
                    disabled={isOfficialEntity(selectedPack)}
                  />
                </label>
                <label className={css.flagLabel}>
                  {isOfficialEntity(selectedPack) ? "Note" : "Note (optional)"}
                  <input
                    value={flagNote}
                    onChange={(ev) => setFlagNote(ev.target.value)}
                    placeholder="Why"
                    required={isOfficialEntity(selectedPack)}
                  />
                </label>
                {flagErr ? <p className={css.flagWarn}>{flagErr}</p> : null}
                <button
                  type="submit"
                  className={css.actionSubmit}
                  disabled={
                    flagBusy ||
                    (isOfficialEntity(selectedPack) ? !flagNote.trim() : !flagName.trim())
                  }
                >
                  {flagBusy ? "Saving..." : isOfficialEntity(selectedPack) ? "Save note" : "Save name"}
                </button>
              </form>
            ) : null}
          </div>
          <div className={css.actionMenu}>
            <button
              type="button"
              className={`${css.danger}${deleteOpen ? ` ${css.actionOn}` : ""}`}
              disabled={!caseObj || deleteBusy}
              title="Delete this file"
              onClick={() => {
                setDeleteOpen((v) => !v);
                setFlagOpen(false);
                setDeleteErr(null);
              }}
            >
              Delete file
            </button>
            {deleteOpen ? (
              <div className={css.actionPop}>
                <div className={css.actionPopHead}>
                  <span>Delete file</span>
                  <button
                    type="button"
                    className={css.actionClose}
                    aria-label="Close"
                    onClick={() => setDeleteOpen(false)}
                  />
                </div>
                <p className={css.flagWarn}>Delete this file? This cannot be undone.</p>
                {deleteErr ? <p className={css.flagWarn}>{deleteErr}</p> : null}
                <button
                  type="button"
                  className={css.actionCancel}
                  disabled={deleteBusy}
                  onClick={() => {
                    setDeleteOpen(false);
                    setDeleteErr(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className={`${css.actionSubmit} ${css.danger}`}
                  disabled={deleteBusy}
                  onClick={() => void onDeleteInvestigation()}
                >
                  {deleteBusy ? "Deleting..." : "Delete file"}
                </button>
              </div>
            ) : null}
          </div>
        </div>
        </div>
        {emptySlice ? (
          <p className={css.note} style={{ marginTop: "1rem" }}>
            Nothing fetched for this file yet.
          </p>
        ) : null}
      </aside>

      <section className={css.main}>
        <div className={css.tabs} role="tablist" aria-label="Investigation views">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              className={`${css.tab} ${tab === t.id ? css.tabOn : ""}`}
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        {tabBlurb ? (
          <p className={`${css.tabMeta} ${css.tabBlurb}`} id="tab-blurb">
            {tabBlurb}
          </p>
        ) : null}
        {tab !== "graph" && windowFactLine ? (
          <p className={`${css.tabMeta} ${css.warnNote}`}>{windowFactLine}</p>
        ) : null}
        {linkNote ? <p className={`${css.tabMeta} ${css.note}`}>{linkNote}</p> : null}
        <div className={css.stage}>
          {tab === "graph" ? (
            pairFlowLoading ? (
              <p className={css.note}>Loading...</p>
            ) : seedFlowErr ? (
              <p className={css.note}>{seedFlowErr}</p>
            ) : pairFlow.length === 0 ? (
              <p className={css.note}>No addresses touched.</p>
            ) : (
              <>
              <div className={css.toolbar}>
                <span>{pairFlow.length} addresses</span>
                <span className={css.pageRange}>{deskPageRangeLabel(pairFlow.length, flowPage)}</span>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={flowPage <= 1}
                  onClick={() => setFlowPage((p) => Math.max(1, p - 1))}
                >
                  Prev
                </button>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={flowPage >= deskPageCount(pairFlow.length)}
                  onClick={() => setFlowPage((p) => Math.min(deskPageCount(pairFlow.length), p + 1))}
                >
                  Next
                </button>
              </div>
              <div className={css.flowTable}>
                <div className={css.flowHead}>
                  <span className={css.flowHeadName}>Address</span>
                  <span>
                    <IconFlow dir="left" className={css.flowArrow} />
                    Sent to
                  </span>
                  <span>
                    <IconFlow dir="right" className={css.flowArrow} />
                    Received from
                  </span>
                  <span>Transfers</span>
                </div>
                <ul className={css.flowList}>
                  {pairFlowPage.map((row) => {
                    const member = addresses.find(
                      (a) => addressMatchKey(a.addressId) === addressMatchKey(row.addressId),
                    );
                    const id = member?.addressId ?? row.addressId;
                    const on = addressMatchKey(id) === addressMatchKey(selectedAddressId);
                    const n = row.transferCount;
                    const copied = copiedKey === `flow:${id}`;
                    const held = copyHoldKey === `flow:${id}`;
                    const quiet = flowQuietKey === `flow:${id}`;
                    return (
                      <li
                        key={member?.caseAddressId ?? id}
                        className={quiet ? css.flowQuiet : undefined}
                        onMouseEnter={() => {
                          if (flowQuietKey === `flow:${id}`) {
                            setFlowQuietKey(null);
                          }
                        }}
                        onMouseLeave={() => {
                          if (flowQuietKey === `flow:${id}`) {
                            setFlowQuietKey(null);
                          }
                        }}
                      >
                        <div
                          role="button"
                          tabIndex={0}
                          className={`${css.flowRow} ${on ? css.flowOn : ""} ${held ? css.flowRowHold : ""}`}
                          onClick={() => selectOnly(id)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              selectOnly(id);
                            }
                          }}
                        >
                          <span className={css.flowMeta}>
                            <span className={css.mono} title={id}>
                              {displayAddr(id, member?.addressLabel)}
                            </span>
                            <span className={`${css.flowIcons} ${held ? css.flowIconsHold : ""}`}>
                              <button
                                type="button"
                                className={css.iconBtn}
                                aria-label={copied ? "Copied" : "Copy"}
                                title={copied ? "Copied" : "Copy"}
                                onMouseDown={(e) => e.preventDefault()}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onCopy(clipboardAddress(id), `flow:${id}`);
                                }}
                              >
                                <span className={css.iconSlot}>
                                  <IconClipboard className={copied ? undefined : css.iconOn} />
                                  <IconCheck className={copied ? css.iconOn : undefined} />
                                </span>
                              </button>
                              <a
                                className={css.iconLink}
                                href={explorerAddressHref(id) ?? undefined}
                                target="_blank"
                                rel="noreferrer"
                                title={explorerName(chainOf(id))}
                                aria-label={explorerName(chainOf(id))}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <span className={css.iconSlot}>
                                  <IconExternal className={css.iconOn} />
                                </span>
                              </a>
                            </span>
                            <CategoryChips id={id} row={member} />
                          </span>
                          <span className={css.flowAmt}>
                            <span className={css.num}>{fmtEth(row.sentEth)}</span> {nativeSymbol}
                          </span>
                          <span className={css.flowAmt}>
                            <span className={css.num}>{fmtEth(row.receivedEth)}</span> {nativeSymbol}
                          </span>
                          <span className={css.flowAmt}>
                            <span className={css.num}>{fmtCount(n)}</span>
                          </span>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
              </>
            )
          ) : null}

          {tab === "addresses" ? (
            <>
              <div className={css.toolbar}>
                <span>
                  {addresses.length}
                  {caseObj.addressCount != null ? ` of ${caseObj.addressCount}` : ""} addresses
                  {addrQuery.trim() ? ` · ${filteredAddresses.length} match` : ""}
                </span>
                <input
                  type="search"
                  placeholder="Filter addresses"
                  value={addrQuery}
                  onChange={(ev) => setAddrQuery(ev.target.value)}
                  aria-label="Filter addresses"
                />
                <span className={css.pageRange}>{deskPageRangeLabel(filteredAddresses.length, addrPage)}</span>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={addrPage <= 1}
                  onClick={() => setAddrPage((p) => Math.max(1, p - 1))}
                >
                  Prev
                </button>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={addrPage >= deskPageCount(filteredAddresses.length)}
                  onClick={() => setAddrPage((p) => Math.min(deskPageCount(filteredAddresses.length), p + 1))}
                >
                  Next
                </button>
                <button
                  type="button"
                  disabled={!selectedAddressId}
                  onClick={() => setSelectedAddressId(null)}
                >
                  Clear
                </button>
              </div>
              {filteredAddresses.length === 0 ? (
                <p className={css.note}>
                  {addresses.length === 0 ? "No addresses in this file" : "No matching addresses"}
                </p>
              ) : (
                <div className={css.tableWrap}>
                  <table>
                    <thead>
                      <tr>
                        <th>Address</th>
                        <th className={css.num}>
                          <span className={css.colHeadWithInfo}>
                            <button
                              type="button"
                              className={`${css.sortHead} ${addrSort?.key === "transfers" ? css.sortHeadOn : ""}`}
                              onClick={() => toggleAddrSort("transfers")}
                              aria-label="Sort by transactions"
                            >
                              Transactions
                              {addrSort?.key === "transfers" ? (
                                <span className={css.sortMark} aria-hidden="true">
                                  {addrSort.dir === "desc" ? "↓" : "↑"}
                                </span>
                              ) : null}
                            </button>
                            <button
                              type="button"
                              className={`${css.infoMark} ${css.infoMarkHead}`}
                              aria-label="About transactions count"
                              onClick={(e) => e.stopPropagation()}
                              onMouseDown={(e) => e.stopPropagation()}
                            >
                              i
                              <span className={css.infoCard} role="tooltip">
                                Unique transactions this address was in, in this
                                window. Not only with the file wallet.
                              </span>
                            </button>
                          </span>
                        </th>

                      </tr>
                    </thead>
                    <tbody>
                      {addressesPage.map((a) => {
                        const on = a.addressId === selectedAddressId;
                        return (
                          <tr
                            key={a.caseAddressId}
                            className={`${css.clickRow} ${on ? css.rowOn : ""}`}
                            onClick={() => toggleSelect(a.addressId)}
                            onKeyDown={(e) => rowKeyDown(e, a.addressId, toggleSelect)}
                            tabIndex={0}
                            aria-selected={on}
                          >
                            <td>
                              <span className={css.chipRow}>
                                <AddrBits
                                  id={a.addressId}
                                  chain={chainHint}
                                  copyKey={`addr-${a.caseAddressId}`}
                                  copiedKey={copiedKey}
                                  copyHoldKey={copyHoldKey}
                                  onCopy={onCopy}
                                  display={displayAddr(a.addressId, a.addressLabel)}
                                  facts={{
                                    membershipRole: a.membershipRole,
                                    hopDistance: a.hopDistance,
                                    totalValueInEth: a.totalValueInEth,
                                    totalValueOutEth: a.totalValueOutEth,
                                    investigatorLabel: a.addressLabel,
                                  }}
                                />
                                {isSeedMembership(a) ? (
                                  <span className={`${css.pill} ${css.roleSeed}`}>Wallet</span>
                                ) : null}
                                <CategoryChips id={a.addressId} row={a} />
                              </span>
                            </td>
                            <td className={css.num}>{fmtCount(a.transactionCountInCase)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : null}

          {tab === "transactions" ? (
            <>
              <div className={css.toolbar}>
                <span>
                  {seedId
                    ? `${deskPageRangeLabel(txsShown.length, txPage)} for ${displayAddr(seedId, seedDesk?.addressLabel ?? seedPack?.name)}`
                    : "Loading wallet…"}
                </span>
                <span className={css.pageRange}>{deskPageRangeLabel(txsShown.length, txPage)}</span>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={txPage <= 1}
                  onClick={() => setTxPage((p) => Math.max(1, p - 1))}
                >
                  Prev
                </button>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={txPage >= deskPageCount(txsShown.length)}
                  onClick={() => setTxPage((p) => Math.min(deskPageCount(txsShown.length), p + 1))}
                >
                  Next
                </button>
                <button
                  type="button"
                  className={`${css.sortHead} ${txSort === "newest" ? css.sortHeadOn : ""}`}
                  onClick={() => setTxSort("newest")}
                >
                  Newest
                </button>
                <button
                  type="button"
                  className={`${css.sortHead} ${txSort === "eth" ? css.sortHeadOn : ""}`}
                  onClick={() => setTxSort("eth")}
                >
                  Highest {nativeSymbol}
                </button>
              </div>
              {txNote ? <p className={css.note}>{txNote}</p> : null}
              {seedId && txsLoading ? (
                <p className={css.note}>Loading...</p>
              ) : null}
              {seedId &&
              !txsLoading &&
              txsShown.length === 0 &&
              !(txNote && txNote.startsWith("transactions:")) ? (
                <p className={css.note}>No {nativeSymbol} transfers in this window</p>
              ) : null}
              {txsSorted.length > 0 ? (
                <div className={css.tableWrap}>
                  <table>
                    <thead>
                      <tr>
                        <th>Direction</th>
                        <th>Address</th>
                        <th className={css.num}>Amount</th>
                        <th>When</th>
                        <th>Tx</th>
                      </tr>
                    </thead>
                    <tbody>
                      {txsPage.map((tx) => {
                        const dir = txDirection(tx, seedId);
                        const peer = txCounterparty(tx, dir);
                        const showPeer = dir === "In" || dir === "Out";
                        const peerRow = showPeer
                          ? addresses.find(
                              (a) => addressMatchKey(a.addressId) === addressMatchKey(peer),
                            )
                          : undefined;
                        return (
                          <tr key={tx.transactionId} className={css.txRow}>
                            <td>
                              <span className={`${css.pill} ${dirClass(dir)}`}>{dir}</span>
                            </td>
                            <td>
                              {showPeer && peer ? (
                                <span className={css.chipRow}>
                                  <AddrBits
                                    id={peer}
                                    chain={chainHint}
                                    copyKey={`tx-peer-${tx.transactionId}`}
                                    copiedKey={copiedKey}
                                    copyHoldKey={copyHoldKey}
                                    onCopy={onCopy}
                                    display={displayAddr(peer, peerRow?.addressLabel)}
                                    facts={factsForAddress(peer, addresses, selectedAddr)}
                                  />
                                  <CategoryChips id={peer} row={peerRow} />
                                </span>
                              ) : (
                                <span className={css.mutedCell}>—</span>
                              )}
                            </td>
                            <td className={css.num}>
                              <span className={css.mono}>
                                {fmtEth(tx.valueEth)} {nativeSymbol}
                              </span>
                            </td>
                            <td>
                              <span className={css.txWhen}>{fmtShortDate(tx.blockTimestamp)}</span>
                            </td>
                            <td>
                              <AddrBits
                                id={tx.transactionHash}
                                kind="tx"
                                chain={chainHint}
                                copyKey={`tx-hash-${tx.transactionId}`}
                                copiedKey={copiedKey}
                                copyHoldKey={copyHoldKey}
                                onCopy={onCopy}
                                display={shortAddr(tx.transactionHash)}
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </>
          ) : null}

          {tab === "tokens" ? (
            <>
              <div className={css.toolbar}>
                <span>
                  {seedId
                    ? `${deskPageRangeLabel(tokensShown.length, tokenPage)} for ${displayAddr(seedId, seedDesk?.addressLabel ?? seedPack?.name)}`
                    : "Loading wallet…"}
                </span>
                <span className={css.pageRange}>{deskPageRangeLabel(tokensShown.length, tokenPage)}</span>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={tokenPage <= 1}
                  onClick={() => setTokenPage((p) => Math.max(1, p - 1))}
                >
                  Prev
                </button>
                <button
                  type="button"
                  className={css.sortHead}
                  disabled={tokenPage >= deskPageCount(tokensShown.length)}
                  onClick={() => setTokenPage((p) => Math.min(deskPageCount(tokensShown.length), p + 1))}
                >
                  Next
                </button>
              </div>
              {tokenNote ? <p className={css.note}>{tokenNote}</p> : null}
              {seedId && tokensLoading ? (
                <p className={css.note}>Loading...</p>
              ) : null}
              {seedId &&
              !tokensLoading &&
              tokensShown.length === 0 &&
              !(tokenNote && tokenNote.includes("failed")) ? (
                <p className={css.note}>No token transfers in this window</p>
              ) : null}
              {tokensShown.length > 0 ? (
                <div className={css.tableWrap}>
                  <table>
                    <thead>
                      <tr>
                        <th>Token</th>
                        <th>From</th>
                        <th>To</th>
                        <th className={css.num}>Amount</th>
                        <th>When</th>
                        <th>Tx</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tokensPage.map((t) => {
                        const fromRow = addresses.find(
                          (a) => addressMatchKey(a.addressId) === addressMatchKey(t.fromAddressId),
                        );
                        const toRow = addresses.find(
                          (a) => addressMatchKey(a.addressId) === addressMatchKey(t.toAddressId),
                        );
                        return (
                          <tr key={t.transferId} className={css.txRow}>
                            <td>{t.tokenSymbol ?? "-"}</td>
                            <td>
                              <AddrBits
                                id={t.fromAddressId}
                                chain={chainHint}
                                copyKey={`tok-from-${t.transferId}`}
                                copiedKey={copiedKey}
                                copyHoldKey={copyHoldKey}
                                onCopy={onCopy}
                                display={displayAddr(t.fromAddressId, fromRow?.addressLabel)}
                                facts={factsForAddress(t.fromAddressId, addresses, selectedAddr)}
                              />
                            </td>
                            <td>
                              <AddrBits
                                id={t.toAddressId}
                                chain={chainHint}
                                copyKey={`tok-to-${t.transferId}`}
                                copiedKey={copiedKey}
                                copyHoldKey={copyHoldKey}
                                onCopy={onCopy}
                                display={displayAddr(t.toAddressId, toRow?.addressLabel)}
                                facts={factsForAddress(t.toAddressId, addresses, selectedAddr)}
                              />
                            </td>
                            <td className={css.num}>{fmtAmt(t.amount)}</td>
                            <td>
                              <span className={css.txWhen}>{fmtShortDate(t.blockTimestamp)}</span>
                            </td>
                            <td>
                              {t.transactionId ? (
                                <AddrBits
                                  id={t.transactionId}
                                  kind="tx"
                                  chain={chainHint}
                                  copyKey={`tok-tx-${t.transferId}`}
                                  copiedKey={copiedKey}
                                  copyHoldKey={copyHoldKey}
                                  onCopy={onCopy}
                                  display={shortAddr(t.transactionId)}
                                />
                              ) : (
                                <span className={css.mutedCell}>—</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </>
          ) : null}

          {tab === "analyst" ? (
            <div className={css.aipPanel}>
              <div className={css.toolbar}>
                <button
                  type="button"
                  className={css.ghostBtn}
                  disabled={aipBusy || !caseObj}
                  onClick={() => {
                    void generateAipNarrative();
                  }}
                >
                  {aipBusy ? "Writing…" : "Write summary"}
                </button>
                <button
                  type="button"
                  className={css.ghostBtn}
                  disabled={!aipNarrative || aipSaveBusy || !caseObj}
                  onClick={() => {
                    void saveAipNarrative();
                  }}
                >
                  {aipSaveBusy ? "Saving…" : "Save to file"}
                </button>
                <button
                  type="button"
                  className={css.ghostBtn}
                  onClick={() => setAipShowBrief((v) => !v)}
                >
                  {aipShowBrief ? "Hide facts used" : "Show facts used"}
                </button>
              </div>
              <p className={css.note}>
                Built from this file&apos;s transfers and public names — nothing invented.
              </p>
              {aipErr ? <p className={css.note}>{aipErr}</p> : null}
              {aipSaveNote ? <p className={css.note}>{aipSaveNote}</p> : null}
              {aipNarrative ? (
                <>
                  <div className={css.aipProse}>
                    {aipNarrative.paragraphs.map((p, i) => (
                      <p key={i}>{p}</p>
                    ))}
                  </div>
                  {aipNarrative.sourceUrls.length > 0 ? (
                    <div className={css.aipSources}>
                      <div className={css.sectionLabel}>Sources</div>
                      <ul className={css.briefSummary}>
                        {aipNarrative.sourceUrls.map((url) => (
                          <li key={url}>
                            <a href={url} target="_blank" rel="noreferrer">
                              {url}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className={css.note}>
                  Write a summary to get a short read of this wallet over the window.
                </p>
              )}
              {aipShowBrief ? (
                <pre className={css.briefPre}>{JSON.stringify(aipBrief, null, 2)}</pre>
              ) : null}
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

export default CaseView;
