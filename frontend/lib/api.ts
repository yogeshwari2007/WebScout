import { ResearchResult, SourceStatusType } from "./types";
import { extractHostname } from "./validation";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(
  /\/+$/,
  ""
);

// Backend API response schemas
interface BackendItem {
  name: string;
  source_url: string;
  values: Record<string, string>;
  pros: string[];
  cons: string[];
}

interface BackendRecommendation {
  winner: string;
  reasoning: string;
  source_urls: string[];
}

interface BackendSource {
  url: string;
  title: string;
  status: "ok" | "failed";
  error?: string | null;
}

interface BackendResearchResponse {
  query: string;
  summary: string;
  criteria: string[];
  items: BackendItem[];
  recommendation: BackendRecommendation;
  sources: BackendSource[];
  elapsed_ms: number;
}

export class ApiError extends Error {
  statusCode: number;
  isNetworkError: boolean;
  detail?: string;

  constructor(
    message: string,
    statusCode: number = 500,
    isNetworkError: boolean = false,
    detail?: string
  ) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.isNetworkError = isNetworkError;
    this.detail = detail;
  }
}

/**
 * Transforms the backend API response schema into the frontend ResearchResult format.
 */
export function adaptBackendResponse(
  data: BackendResearchResponse,
  fallbackQuery: string
): ResearchResult {
  const query = data.query || fallbackQuery;
  const criteria = Array.isArray(data.criteria) ? data.criteria : [];

  const items = (data.items || []).map((it, idx) => ({
    id: `item-${idx}-${(it.name || "option").toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
    name: it.name || `Option ${idx + 1}`,
    criteriaValues: it.values || {},
    pros: Array.isArray(it.pros) ? it.pros : [],
    cons: Array.isArray(it.cons) ? it.cons : [],
    url: it.source_url || undefined,
  }));

  const recommendation = {
    winner: data.recommendation?.winner || "No conclusive winner identified",
    reasoning:
      data.recommendation?.reasoning ||
      "Sufficient comparative data was not available to formulate a definitive recommendation.",
    sourceLinks: (data.recommendation?.source_urls || []).map((url) => ({
      title: extractHostname(url) || url,
      url,
    })),
  };

  const sources = (data.sources || []).map((src) => {
    let status: SourceStatusType = "failed";
    if (src.status === "ok") {
      status = "success";
    }

    return {
      url: src.url,
      hostname: extractHostname(src.url),
      status,
      title: src.title || undefined,
      error: src.error || undefined,
    };
  });

  const durationSeconds =
    typeof data.elapsed_ms === "number"
      ? Math.round(data.elapsed_ms / 100) / 10
      : undefined;

  return {
    query,
    summary: data.summary || "No synthesis summary available.",
    criteria,
    items,
    recommendation,
    sources,
    durationSeconds,
    createdAt: new Date().toISOString(),
  };
}

/**
 * Sends a research request to the FastAPI backend.
 * Configured with a sensible 90-second timeout for multi-website Playwright fetching.
 */
export async function research(
  query: string,
  urls: string[],
  options?: { signal?: AbortSignal; timeoutMs?: number }
): Promise<ResearchResult> {
  const timeoutMs = options?.timeoutMs || 90000; // 90s timeout
  const controller = new AbortController();

  // Combine caller signal and timeout
  const timeoutId = setTimeout(() => {
    controller.abort("REQUEST_TIMEOUT");
  }, timeoutMs);

  if (options?.signal) {
    options.signal.addEventListener("abort", () => {
      clearTimeout(timeoutId);
      controller.abort("USER_CANCELLED");
    });
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/research`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        query: query.trim(),
        urls,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail = "";
      try {
        const errorJson = await response.json();
        errorDetail =
          errorJson.detail ||
          (Array.isArray(errorJson.errors)
            ? errorJson.errors.map((e: any) => e.msg || e).join("; ")
            : "");
      } catch {
        errorDetail = response.statusText;
      }

      if (response.status === 400) {
        throw new ApiError(
          errorDetail || "Invalid request or duplicate URLs supplied.",
          400,
          false,
          errorDetail
        );
      } else if (response.status === 422) {
        throw new ApiError(
          errorDetail || "Validation error: Check query length and URL formats.",
          422,
          false,
          errorDetail
        );
      } else if (response.status === 503) {
        throw new ApiError(
          errorDetail ||
            "The WebScout research service is temporarily unavailable or still starting. Please try again in a moment.",
          503,
          true,
          errorDetail
        );
      } else if (response.status >= 500) {
        throw new ApiError(
          errorDetail ||
            "The backend encountered an error while exploring these websites. Please try again or check target URLs.",
          response.status,
          false,
          errorDetail
        );
      } else {
        throw new ApiError(
          `Research request failed with status ${response.status}: ${errorDetail}`,
          response.status,
          false,
          errorDetail
        );
      }
    }

    const json: BackendResearchResponse = await response.json();
    return adaptBackendResponse(json, query);
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === "AbortError") {
      if (controller.signal.reason === "REQUEST_TIMEOUT") {
        throw new ApiError(
          "Research request timed out after 90 seconds. Visiting multiple dynamic websites and synthesizing intelligence took longer than expected.",
          408,
          true
        );
      }
      throw new ApiError("Research request was cancelled.", 499, false);
    }

    // Network connection failure (e.g. backend server is stopped or port blocked)
    const isConnRefused =
      error.message?.includes("Failed to fetch") ||
      error.message?.includes("NetworkError") ||
      error.message?.includes("fetch failed");

    if (isConnRefused) {
      const targetHint = API_BASE_URL || "this application server";
      throw new ApiError(
        `Unable to reach the WebScout research service via ${targetHint}. Please confirm WebScout is running.`,
        503,
        true
      );
    }

    throw new ApiError(
      error.message || "An unexpected error occurred during research.",
      500,
      false
    );
  }
}

/**
 * Checks backend health status.
 */
export async function checkBackendHealth(): Promise<{
  status: string;
  fetcher: string;
  analyzer: string;
} | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
