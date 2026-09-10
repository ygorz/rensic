import { lookupKnownEntity } from "./knownEntities";

export const LOOKBACK_CHOICES = [7, 30, 90, 365] as const;
export const DEFAULT_LOOKBACK_DAYS = 30;
export const WORKING_SET_CAP = 100;
export const VERTEX_CAST_CAP = 16;
export const PAGE_CAP_TX_COUNT = 200000;
/** Native ETH Transaction rows read per file for Fund flow pair sums. */
export const PAIR_FLOW_PAGE_SIZE = 100;
export const PAIR_FLOW_TX_CAP = 1000;

/** Rows shown per desk table page (Fund flow, Addresses, Transactions, Token transfers). */
export const DESK_PAGE_SIZE = 50;
/** Soft ceiling when walking OSDK nextPageToken for list tabs. */
export const DESK_LIST_FETCH_CAP = 2000;

export function deskPageCount(total: number, pageSize = DESK_PAGE_SIZE): number {
  if (total <= 0) {
    return 1;
  }
  return Math.ceil(total / pageSize);
}

export function deskPageSlice<T>(rows: readonly T[], page: number, pageSize = DESK_PAGE_SIZE): T[] {
  const pages = deskPageCount(rows.length, pageSize);
  const p = Math.min(Math.max(1, page), pages);
  const start = (p - 1) * pageSize;
  return rows.slice(start, start + pageSize);
}

export function deskPageRangeLabel(total: number, page: number, pageSize = DESK_PAGE_SIZE): string {
  if (total <= 0) {
    return "0";
  }
  const pages = deskPageCount(total, pageSize);
  const p = Math.min(Math.max(1, page), pages);
  const start = (p - 1) * pageSize + 1;
  const end = Math.min(total, p * pageSize);
  return `${start}–${end} of ${total}`;
}

export type Rankable = {
  caseAddressId?: string;
  addressId?: string;
  addressLabel?: string;
  membershipRole?: string;
  hopDistance?: number;
  transactionCountInCase?: number;
  totalValueInEth?: number;
  totalValueOutEth?: number;
  netFlowEth?: number;
};

export function clampLookback(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return DEFAULT_LOOKBACK_DAYS;
  }
  const days = Math.round(n);
  if ((LOOKBACK_CHOICES as readonly number[]).includes(days)) {
    return days;
  }
  if (days <= 7) {
    return 7;
  }
  if (days <= 30) {
    return 30;
  }
  if (days <= 90) {
    return 90;
  }
  return 365;
}

export function windowDays(start: unknown, end: unknown): number | null {
  if (start == null || end == null) {
    return null;
  }
  const a = new Date(String(start)).getTime();
  const b = new Date(String(end)).getTime();
  if (!Number.isFinite(a) || !Number.isFinite(b) || b < a) {
    return null;
  }
  return Math.max(1, Math.round((b - a) / 86400000));
}

export function windowLabel(days: number | null): string {
  if (days == null) {
    return "";
  }
  return `${days}d`;
}

export function num(n: number | undefined | null): number {
  const v = Number(n ?? 0);
  return Number.isFinite(v) ? v : 0;
}

export function ethFlow(a: Rankable): number {
  return Math.abs(num(a.totalValueInEth)) + Math.abs(num(a.totalValueOutEth));
}

export function isSeedMembership(a: Rankable): boolean {
  return (a.membershipRole ?? "").toLowerCase() === "seed" || a.hopDistance === 0;
}

export function investigatorNote(a: Rankable): string | null {
  const packName = (lookupKnownEntity(a.addressId)?.name ?? "").trim();
  const label = (a.addressLabel ?? "").trim();
  if (!label) {
    return null;
  }
  if (packName && label.toLowerCase() === packName.toLowerCase()) {
    return null;
  }
  return label;
}

export function isPackLabeled(id: string | undefined): boolean {
  return Boolean(lookupKnownEntity(id));
}

export function isLabeled(a: Rankable): boolean {
  return isPackLabeled(a.addressId) || Boolean(investigatorNote(a));
}

export function labeledCount(rows: Rankable[]): number {
  return rows.filter((r) => isLabeled(r) && !isSeedMembership(r)).length;
}

export function rankAddresses<T extends Rankable>(rows: T[]): T[] {
  const seen = new Set<string>();
  const unique: T[] = [];
  for (const r of rows) {
    const k = r.caseAddressId || r.addressId || "";
    if (!k || seen.has(k)) {
      continue;
    }
    seen.add(k);
    unique.push(r);
  }
  const seeds = unique.filter(isSeedMembership);
  const rest = unique.filter((r) => !isSeedMembership(r));
  rest.sort((a, b) => {
    const la = isLabeled(a) ? 1 : 0;
    const lb = isLabeled(b) ? 1 : 0;
    if (la !== lb) {
      return lb - la;
    }
    const df = ethFlow(b) - ethFlow(a);
    if (df !== 0) {
      return df;
    }
    const dt = num(b.transactionCountInCase) - num(a.transactionCountInCase);
    if (dt !== 0) {
      return dt;
    }
    return num(b.netFlowEth) - num(a.netFlowEth);
  });
  return [...seeds, ...rest];
}

export function vertexCast<T extends Rankable>(rows: T[], cap = VERTEX_CAST_CAP): T[] {
  const ranked = rankAddresses(rows);
  const seeds = ranked.filter(isSeedMembership);
  const rest = ranked.filter((r) => !isSeedMembership(r));
  const labeled = rest.filter(isLabeled);
  const unlabeled = rest.filter((r) => !isLabeled(r));
  const remaining = Math.max(0, cap - seeds.length - labeled.length);
  return [...seeds, ...labeled, ...unlabeled.slice(0, remaining)];
}

export function workingSetCopy(cap: number, labeled: number): string {
  return `Wallet plus top ${cap} by native flow in this window (${labeled} named).`;
}

export function windowFact(days: number | null, truncated: boolean): string | null {
  if (truncated) {
    return "Ingest hit Alchemy's page cap; this is a stress test, not a complete history.";
  }
  if (days == null) {
    return null;
  }
  return `Fetched ${days}d of transfers in this case window.`;
}

export function caseOptionLabel(input: {
  caseTitle?: string;
  caseId?: string;
  seedAddress?: string;
  transactionCount?: number;
  timeWindowStart?: unknown;
  timeWindowEnd?: unknown;
  shortAddr: (id: string | undefined) => string;
}): string {
  const title = input.caseTitle || input.caseId || "untitled";
  const seed = input.shortAddr(input.seedAddress);
  const win = windowLabel(windowDays(input.timeWindowStart, input.timeWindowEnd));
  const n = input.transactionCount;
  const bits = [title, seed];
  if (win) {
    bits.push(win);
  }
  if (n != null && !Number.isNaN(Number(n))) {
    const count = Number(n);
    bits.push(count === 1 ? "1 tx" : `${count} tx`);
  }
  return bits.join("  ");
}

export type PairEthTransfer = {
  transactionId?: string;
  fromAddressId?: string;
  toAddressId?: string;
  valueEth?: number | string | null;
  transactionStatus?: string;
};

export type PairEthRow = {
  addressId: string;
  sentEth: number;
  receivedEth: number;
  transferCount: number;
};

/** Case-insensitive id match for file-wallet pair sums. */
export function addressMatchKey(id: string | undefined | null): string {
  return (id ?? "").trim().toLowerCase();
}

function addressTail(id: string): string {
  const i = id.lastIndexOf(":");
  return i >= 0 ? id.slice(i + 1) : id;
}

/** Same wallet even if one id is chain:hex and the other is hex-only. */
function sameAddress(a: string, b: string): boolean {
  if (!a || !b) {
    return false;
  }
  if (a === b) {
    return true;
  }
  const ta = addressTail(a);
  const tb = addressTail(b);
  if (!ta || ta !== tb) {
    return false;
  }
  const ca = a.includes(":") ? a.slice(0, a.indexOf(":")) : "";
  const cb = b.includes(":") ? b.slice(0, b.indexOf(":")) : "";
  return !ca || !cb || ca === cb;
}

function positiveEth(value: number | string | null | undefined): number {
  const v = Number(value ?? 0);
  if (!Number.isFinite(v) || v <= 0) {
    return 0;
  }
  return v;
}

function skippedTransferStatus(status: string | undefined): boolean {
  if (status == null) {
    return false;
  }
  const s = status.trim().toLowerCase();
  return s === "failed" || s === "reverted";
}

/**
 * Pair-level native ETH between the file wallet and each counterparty.
 *
 * Sent is valueEth on transfers from the file wallet to that address.
 * Received is valueEth on transfers from that address to the file wallet.
 * Only positive valueEth is summed. Zero and negative amounts are ignored
 * and do not create a row; a counterparty is omitted when sent + received is 0.
 * Self-transfers (both sides the file wallet, including chain:hex vs hex-only) are excluded and not counted.
 * Rows with transactionStatus failed or reverted are skipped when status is present.
 * Duplicate transactionId values are counted once. Transfers that do not
 * touch the file wallet are ignored. Order is sent + received, largest first.
 */
export function pairEthFlow(
  fileWalletId: string | undefined | null,
  transfers: readonly PairEthTransfer[],
): PairEthRow[] {
  const wallet = addressMatchKey(fileWalletId);
  if (!wallet) {
    return [];
  }
  const seen = new Set<string>();
  const acc = new Map<string, PairEthRow>();
  for (const tx of transfers) {
    const id = (tx.transactionId ?? "").trim();
    if (id) {
      if (seen.has(id)) {
        continue;
      }
      seen.add(id);
    }
    if (skippedTransferStatus(tx.transactionStatus)) {
      continue;
    }
    const value = positiveEth(tx.valueEth);
    if (value === 0) {
      continue;
    }
    const from = addressMatchKey(tx.fromAddressId);
    const to = addressMatchKey(tx.toAddressId);
    const fromWallet = sameAddress(from, wallet);
    const toWallet = sameAddress(to, wallet);
    if (fromWallet && toWallet) {
      continue;
    }
    let key = "";
    let sent = 0;
    let received = 0;
    let displayId = "";
    if (fromWallet && to) {
      key = to;
      sent = value;
      displayId = (tx.toAddressId ?? "").trim();
    } else if (toWallet && from) {
      key = from;
      received = value;
      displayId = (tx.fromAddressId ?? "").trim();
    } else {
      continue;
    }
    const cur = acc.get(key);
    if (cur) {
      cur.sentEth += sent;
      cur.receivedEth += received;
      cur.transferCount += 1;
    } else {
      acc.set(key, {
        addressId: displayId || key,
        sentEth: sent,
        receivedEth: received,
        transferCount: 1,
      });
    }
  }
  return [...acc.values()].sort((a, b) => {
    const moved = b.sentEth + b.receivedEth - (a.sentEth + a.receivedEth);
    if (moved !== 0) {
      return moved;
    }
    const dt = b.transferCount - a.transferCount;
    if (dt !== 0) {
      return dt;
    }
    return a.addressId.localeCompare(b.addressId);
  });
}
