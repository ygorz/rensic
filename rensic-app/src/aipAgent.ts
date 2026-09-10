import type { Client } from "@osdk/client";
import { symbolClientContext } from "@osdk/shared.client2";
import {
  aipAgentUserPrompt,
  paraphraseBrief,
  type AipBrief,
  type AipNarrative,
} from "./aipBrief";

/** Optional AIP Agent RID from env (AIP Chatbox / Agent Studio). */
export function configuredAipAgentRid(): string | null {
  const raw = (import.meta.env.VITE_AIP_AGENT_RID as string | undefined)?.trim();
  return raw ? raw : null;
}

/** Encode a RID for a URL path without letting ".." become path traversal. */
function encodeRidPathSegment(rid: string): string {
  return encodeURIComponent(rid).replace(/\./g, "%2E");
}

function narrativeFromMarkdown(md: string): AipNarrative {
  const cleaned = md.replace(/\r\n/g, "\n").trim();
  const parts = cleaned
    .split(/\n{2,}/)
    .map((p) => p.replace(/\n/g, " ").trim())
    .filter(Boolean)
    .filter((p) => !/^sources?\s*:?\s*$/i.test(p));
  const sourceUrls: string[] = [];
  for (const m of cleaned.matchAll(/https?:\/\/\S+/g)) {
    const url = m[0].replace(/[.,);]+$/, "");
    if (!sourceUrls.includes(url)) {
      sourceUrls.push(url);
    }
  }
  return {
    paragraphs: parts.slice(0, 3),
    sourceUrls,
    usedFields: ["aip-agent-response"],
    engine: "aip-agent",
  };
}

function formatApiError(err: unknown): string {
  if (err && typeof err === "object") {
    const e = err as {
      message?: string;
      errorName?: string;
      errorCode?: string;
      errorDescription?: string;
      parameters?: unknown;
    };
    const bits = [
      e.errorName,
      e.errorCode,
      e.errorDescription,
      e.message,
    ].filter(Boolean);
    if (e.parameters != null) {
      try {
        bits.push(JSON.stringify(e.parameters));
      } catch {
        /* ignore */
      }
    }
    if (bits.length) {
      return bits.join(" - ");
    }
  }
  return err instanceof Error ? err.message : String(err);
}

type ClientCtx = {
  baseUrl: string;
  fetch: typeof fetch;
};

function clientCtx(client: Client): ClientCtx {
  const ctx = (client as unknown as { [symbolClientContext]: ClientCtx })[
    symbolClientContext
  ];
  if (!ctx?.baseUrl || !ctx.fetch) {
    throw new Error("Foundry client is missing base URL or fetch.");
  }
  return ctx;
}

async function aipJson<T>(
  client: Client,
  method: string,
  pathAfterAgents: string,
  body?: unknown,
): Promise<T> {
  const ctx = clientCtx(client);
  const base = ctx.baseUrl.replace(/\/$/, "");
  const url = `${base}/api/v2/aipAgents/agents/${pathAfterAgents}?preview=true`;
  const response = await ctx.fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let payload: Record<string, unknown> = {};
    try {
      payload = (await response.json()) as Record<string, unknown>;
    } catch {
      /* ignore */
    }
    const err = new Error(
      String(payload.message ?? `Failed to fetch ${response.status}`),
    ) as Error & {
      errorName?: string;
      errorCode?: string;
      errorDescription?: string;
      statusCode?: number;
      parameters?: unknown;
    };
    err.errorName = payload.errorName as string | undefined;
    err.errorCode = payload.errorCode as string | undefined;
    err.errorDescription = payload.errorDescription as string | undefined;
    err.statusCode = response.status;
    err.parameters = payload.parameters;
    throw err;
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/**
 * Prefer AIP Agent when configured; fall back to local grounded paraphrase.
 * On this Dev enrollment the Agents API may return AgentNotFound even for a
 * Published Studio agent — the desk still ships a real summary from ontology facts.
 */
export async function runAipParaphrase(
  client: Client,
  brief: AipBrief,
): Promise<AipNarrative & { aipWarning?: string }> {
  const agentRid = configuredAipAgentRid();
  if (!agentRid) {
    return paraphraseBrief(brief);
  }

  try {
    const ridSeg = encodeRidPathSegment(agentRid);
    await aipJson<unknown>(client, "GET", ridSeg);
    const session = await aipJson<{ rid: string }>(
      client,
      "POST",
      `${ridSeg}/sessions`,
      { agentVersion: "1.0" },
    );
    const result = await aipJson<{ agentMarkdownResponse?: string }>(
      client,
      "POST",
      `${ridSeg}/sessions/${encodeRidPathSegment(session.rid)}/blockingContinue`,
      {
        userInput: { text: aipAgentUserPrompt(brief) },
        parameterInputs: {},
      },
    );
    const md = String(result.agentMarkdownResponse ?? "").trim();
    if (!md) {
      throw new Error("AIP returned an empty summary.");
    }
    const narrative = narrativeFromMarkdown(md);
    if (narrative.sourceUrls.length === 0) {
      narrative.sourceUrls = paraphraseBrief(brief).sourceUrls;
    }
    return narrative;
  } catch (err) {
    const detail = formatApiError(err);
    return {
      ...paraphraseBrief(brief),
      aipWarning: detail,
    };
  }
}
