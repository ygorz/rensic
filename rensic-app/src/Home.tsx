import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import type { Osdk } from "@osdk/client";
import { useOsdkClient } from "@osdk/react";
import {
  ChainConfiguration,
  InvestigationCase,
  configureChainRpc,
  createInvestigation,
} from "@rensic/sdk";
import css from "./Home.module.css";
import {
  DEFAULT_LOOKBACK_DAYS,
  LOOKBACK_CHOICES,
  clampLookback,
  caseOptionLabel as formatCaseOption,
} from "./desk";
import {
  DEFAULT_CHAIN_ID,
  DESK_CHAINS,
  getDeskChain,
} from "./chains";

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
      const raw = JSON.stringify(err.parameters);
      bits.push(raw.replace(/("api-key"\s*:\s*")[^"]+/gi, "$1***"));
    }
    if (bits.length) {
      return bits.join(" - ");
    }
  }
  return e instanceof Error ? e.message : String(e);
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

function caseOptionLabel(c: Osdk.Instance<InvestigationCase>): string {
  return formatCaseOption({
    caseTitle: c.caseTitle,
    caseId: c.caseId,
    seedAddress: c.seedAddress,
    transactionCount: c.transactionCount,
    timeWindowStart: c.timeWindowStart,
    timeWindowEnd: c.timeWindowEnd,
    shortAddr,
  });
}

function maskKey(value: string | undefined): string {
  if (!value) {
    return "not set";
  }
  if (value === "auto" || value === "PASTE_YOUR_ALCHEMY_KEY_HERE") {
    return "placeholder";
  }
  return "set";
}

function Home(): React.ReactElement {
  const client = useOsdkClient();
  const navigate = useNavigate();
  const location = useLocation();
  const rpcWrapRef = useRef<HTMLDivElement>(null);
  const newWrapRef = useRef<HTMLDivElement>(null);
  const [cases, setCases] = useState<Osdk.Instance<InvestigationCase>[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [openNew, setOpenNew] = useState(false);
  const [title, setTitle] = useState("");
  const [seed, setSeed] = useState("");
  const [chain, setChain] = useState(DEFAULT_CHAIN_ID);
  const [lookback, setLookback] = useState(String(DEFAULT_LOOKBACK_DAYS));
  const [openRpc, setOpenRpc] = useState(false);
  const [rpcChain, setRpcChain] = useState(DEFAULT_CHAIN_ID);
  const [rpcKey, setRpcKey] = useState("");
  const [rpcBusy, setRpcBusy] = useState(false);
  const [rpcNote, setRpcNote] = useState<string | null>(null);
  const [rpcNoteBad, setRpcNoteBad] = useState(false);
  const [rpcMasks, setRpcMasks] = useState<Record<string, string>>({});

  async function reloadRpc(): Promise<void> {
    const page = await client(ChainConfiguration).fetchPage({
      $pageSize: 20,
      $select: ["chainId", "apiKey", "enabled"],
    });
    const next: Record<string, string> = {};
    for (const row of page.data) {
      next[row.chainId] = maskKey(row.apiKey);
    }
    setRpcMasks(next);
  }

  async function reload(): Promise<void> {
    const page = await client(InvestigationCase).fetchPage({
      $pageSize: 50,
      $select: [
        "caseId",
        "caseTitle",
        "investigationStatus",
        "seedAddress",
        "transactionCount",
        "addressCount",
        "chainIds",
        "createdAt",
        "timeWindowStart",
        "timeWindowEnd",
      ],
    });
    setCases(page.data as Osdk.Instance<InvestigationCase>[]);
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await reload();
        try {
          await reloadRpc();
        } catch (rpcErr) {
          if (!cancelled) {
            setRpcNote(formatOsdkError(rpcErr));
            setRpcNoteBad(true);
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError(formatOsdkError(e));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client]);

  useEffect(() => {
    if (!openRpc && !openNew) {
      return;
    }
    function onKey(e: KeyboardEvent): void {
      if (e.key === "Escape") {
        setOpenRpc(false);
        setOpenNew(false);
      }
    }
    function onDown(e: MouseEvent): void {
      const t = e.target;
      if (!(t instanceof Node)) {
        return;
      }
      if (rpcWrapRef.current?.contains(t) || newWrapRef.current?.contains(t)) {
        return;
      }
      setOpenRpc(false);
      setOpenNew(false);
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onDown);
    };
  }, [openRpc, openNew]);

  const activeId = useMemo(() => {
    const m = location.pathname.match(/^\/cases\/([^/]+)/);
    return m?.[1] ?? "";
  }, [location.pathname]);

  async function onCreate(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await client(createInvestigation).applyAction(
        {
          "case-title": title.trim(),
          "seed-address": seed.trim(),
          "chain-ids": [chain].filter(Boolean),
          "time-window-days": clampLookback(lookback),
        },
        { $returnEdits: true },
      );
      await reload();
      const page = await client(InvestigationCase).fetchPage({ $pageSize: 50 });
      const match = page.data.find((c) => c.caseTitle === title.trim());
      setTitle("");
      setSeed("");
      setOpenNew(false);
      if (match) {
        navigate(`/cases/${match.caseId}`);
      }
    } catch (err) {
      setError(formatOsdkError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onSaveRpc(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const key = rpcKey.trim();
    if (!key) {
      return;
    }
    setRpcBusy(true);
    setRpcNote(null);
    setRpcNoteBad(false);
    setError(null);
    const meta = getDeskChain(rpcChain);
    try {
      await client(configureChainRpc).applyAction({
        "chain-id": rpcChain,
        "api-key": key,
        "display-name": meta.displayName,
        "native-symbol": meta.nativeSymbol,
        "rpc-base-url": "auto",
      });
      setRpcKey("");
      setRpcNote("Saved.");
      setRpcNoteBad(false);
      await reloadRpc();
      setOpenRpc(false);
    } catch (err) {
      setRpcNote(formatOsdkError(err));
      setRpcNoteBad(true);
    } finally {
      setRpcBusy(false);
    }
  }

  return (
    <div className={css.shell}>
      <header className={css.top}>
        <Link className={css.brand} to="/">
          Rensic
        </Link>
        <div className={css.topGrow}>
          <select
            className={css.caseSelect}
            value={activeId}
            onChange={(ev) => {
              const id = ev.target.value;
              if (id) {
                navigate(`/cases/${id}`);
              } else {
                navigate("/");
              }
            }}
          >
            <option value="">Select file</option>
            {cases.map((c) => (
              <option key={c.caseId} value={c.caseId}>
                {caseOptionLabel(c)}
              </option>
            ))}
          </select>
        </div>
        <div className={css.headerActions}>
          <div className={css.menu} ref={rpcWrapRef}>
            <button
              type="button"
              className={`${css.ghost}${openRpc ? ` ${css.ghostOn}` : ""}`}
              aria-expanded={openRpc}
              onClick={() => {
                setOpenRpc((v) => !v);
                setOpenNew(false);
              }}
            >
              RPC
            </button>
            {openRpc ? (
              <form className={css.popover} onSubmit={onSaveRpc}>
                <div className={css.popoverHead}>
                  <span className={css.popoverHeadLead}>
                    <span>Alchemy RPC</span>
                    <span className={css.popoverDot} aria-hidden="true" />
                    <a
                      className={css.rpcLink}
                      href="https://dashboard.alchemy.com/apps"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Get a key
                    </a>
                  </span>
                  <button
                    type="button"
                    className={css.popoverClose}
                    aria-label="Close"
                    onClick={() => setOpenRpc(false)}
                  />
                </div>
                <p className={css.rpcBlurb}>
                  Reads{" "}
                  <a
                    className={css.rpcMethod}
                    href="https://www.alchemy.com/docs/data/transfers-api/transfers-endpoints/alchemy-get-asset-transfers"
                    target="_blank"
                    rel="noreferrer"
                  >
                    getAssetTransfers
                  </a>{" "}
                  for the wallet,{" "}
                  <span className={css.rpcBlurbEnd}>
                    on the chain you pick.
                    <span className={css.popoverDot} aria-hidden="true" />
                    <span><span className={css.rpcStatus}>{rpcMasks[rpcChain] === "set" ? "Key set" : "Key not set"}</span></span>
                  </span>
                </p>
                <select value={rpcChain} onChange={(ev) => setRpcChain(ev.target.value)}>
                  {DESK_CHAINS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.displayName}
                    </option>
                  ))}
                </select>
                <input
                  type="password"
                  autoComplete="off"
                  placeholder="Alchemy API key"
                  value={rpcKey}
                  onChange={(ev) => setRpcKey(ev.target.value)}
                  required
                />
                {rpcNote ? (
                  <div className={rpcNoteBad ? css.popoverError : css.popoverNote}>{rpcNote}</div>
                ) : null}
                <button className={`${css.popoverSubmit} ${css.popoverSubmitLast}`} type="submit" disabled={rpcBusy}>
                  {rpcBusy ? "Saving..." : "Save key"}
                </button>
              </form>
            ) : null}
          </div>
          <div className={css.menu} ref={newWrapRef}>
            <button
              type="button"
              className={`${css.ghost}${openNew ? ` ${css.ghostOn}` : ""}`}
              aria-expanded={openNew}
              onClick={() => {
                setOpenNew((v) => !v);
                setOpenRpc(false);
              }}
            >
              New file
            </button>
            {openNew ? (
              <form className={`${css.popover} ${css.popoverWide}`} onSubmit={onCreate}>
                <div className={css.popoverHead}>
                  <span>New file</span>
                  <button
                    type="button"
                    className={css.popoverClose}
                    aria-label="Close"
                    onClick={() => setOpenNew(false)}
                  />
                </div>
                <p className={css.rpcBlurb}>One wallet, one chain, and a stretch of time.</p>
                <input
                  placeholder="File title"
                  value={title}
                  onChange={(ev) => setTitle(ev.target.value)}
                  required
                />
                <input
                  className={css.seedInput}
                  placeholder="Wallet 0x..."
                  value={seed}
                  onChange={(ev) => setSeed(ev.target.value)}
                  required
                />
                <select value={chain} onChange={(ev) => setChain(ev.target.value)}>
                  {DESK_CHAINS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.displayName}
                    </option>
                  ))}
                </select>
                <label className={css.fieldLabel}>
                  Window
                  <select value={lookback} onChange={(ev) => setLookback(ev.target.value)}>
                    {LOOKBACK_CHOICES.map((d) => (
                      <option key={d} value={String(d)}>
                        {d} days
                      </option>
                    ))}
                  </select>
                </label>
                {error ? <div className={css.popoverError}>{error}</div> : null}
                <button className={`${css.popoverSubmit} ${css.popoverSubmitLast}`} type="submit" disabled={busy}>
                  {busy ? "Creating..." : "Create"}
                </button>
              </form>
            ) : null}
          </div>
        </div>
      </header>
      {error && !openNew ? <div className={css.error}>{error}</div> : null}
      <div className={css.body}>
        {location.pathname === "/" ? (
          <main className={css.blank}>
            <h1>Open a file</h1>
            <p>Look at one crypto wallet over a stretch of time. Some addresses are already named from public sources. You can label the rest.</p>
          </main>
        ) : (
          <Outlet />
        )}
      </div>
    </div>
  );
}

export default Home;
