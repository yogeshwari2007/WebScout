import { UrlItem } from "./types";

/**
 * Normalizes user URL input by trimming and auto-prepending https:// if missing.
 */
export function normalizeUrl(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return "";

  // Check if starts with a known protocol or schema
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//i.test(trimmed)) {
    return trimmed;
  }

  // Auto-prepend https://
  return `https://${trimmed}`;
}

/**
 * Extracts and sanitizes hostname for display.
 */
export function extractHostname(urlStr: string): string {
  try {
    const parsed = new URL(urlStr);
    return parsed.hostname.replace(/^www\./i, "");
  } catch {
    return "";
  }
}

/**
 * Validates a single URL input against security rules, format requirements,
 * and duplicate detection within the current session list.
 */
export function validateUrlEntry(
  rawInput: string,
  existingNormalizedUrls: string[]
): {
  isValid: boolean;
  normalized: string;
  hostname: string;
  error?: string;
} {
  const trimmed = rawInput.trim();

  if (!trimmed) {
    return {
      isValid: false,
      normalized: "",
      hostname: "",
      error: "Website URL cannot be empty.",
    };
  }

  // Reject unsafe non-HTTP/HTTPS protocols
  const lower = trimmed.toLowerCase();
  if (
    lower.startsWith("javascript:") ||
    lower.startsWith("data:") ||
    lower.startsWith("file:") ||
    lower.startsWith("vbscript:") ||
    lower.startsWith("ftp:")
  ) {
    return {
      isValid: false,
      normalized: "",
      hostname: "",
      error: "Only HTTP and HTTPS website URLs are permitted.",
    };
  }

  const normalized = normalizeUrl(trimmed);

  try {
    const parsed = new URL(normalized);

    // Only allow http and https
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return {
        isValid: false,
        normalized: "",
        hostname: "",
        error: "Only HTTP and HTTPS protocols are supported.",
      };
    }

    const host = parsed.hostname;
    // Hostname must be valid and contain a domain separator (e.g., example.com)
    if (!host || !host.includes(".") || host.endsWith(".")) {
      return {
        isValid: false,
        normalized: "",
        hostname: "",
        error: "Please enter a valid domain (e.g. amazon.in, flipkart.com).",
      };
    }

    // Reject localhost and IP loopbacks for safe research scope
    if (
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "0.0.0.0" ||
      host.endsWith(".local")
    ) {
      return {
        isValid: false,
        normalized: "",
        hostname: "",
        error: "Localhost and loopback addresses cannot be researched.",
      };
    }

    // Clean display hostname
    const displayHostname = host.replace(/^www\./i, "");

    // Duplicate check: compare canonical forms (lowercase, no trailing slash)
    const canonicalCurrent = normalized.toLowerCase().replace(/\/+$/, "");
    const isDuplicate = existingNormalizedUrls.some((other) => {
      const canonicalOther = other.toLowerCase().replace(/\/+$/, "");
      return canonicalCurrent === canonicalOther;
    });

    if (isDuplicate) {
      return {
        isValid: false,
        normalized,
        hostname: displayHostname,
        error: "This website has already been added to your sources.",
      };
    }

    return {
      isValid: true,
      normalized,
      hostname: displayHostname,
    };
  } catch {
    return {
      isValid: false,
      normalized: "",
      hostname: "",
      error: "Invalid website URL format. Please check the address.",
    };
  }
}

/**
 * Validates the natural-language research query.
 */
export function validateQuery(query: string): {
  isValid: boolean;
  charCount: number;
  error?: string;
} {
  const charCount = query.length;
  const trimmed = query.trim();

  if (charCount === 0) {
    return {
      isValid: false,
      charCount: 0,
    };
  }

  if (trimmed.length < 10) {
    return {
      isValid: false,
      charCount,
      error: "Please enter at least 10 characters to formulate a clear research objective.",
    };
  }

  if (charCount > 500) {
    return {
      isValid: false,
      charCount,
      error: "Query exceeds the maximum limit of 500 characters.",
    };
  }

  return {
    isValid: true,
    charCount,
  };
}

/**
 * Computes overall research readiness state based on current query and URL items.
 */
export function calculateReadiness(
  query: string,
  urlItems: UrlItem[]
): {
  hasValidQuery: boolean;
  hasAtLeastOneSource: boolean;
  allUrlsValid: boolean;
  isReady: boolean;
} {
  const queryResult = validateQuery(query);
  const nonEmptyUrls = urlItems.filter((item) => item.value.trim().length > 0);

  const hasValidQuery = queryResult.isValid;
  const hasAtLeastOneSource = nonEmptyUrls.length > 0;
  const allUrlsValid =
    hasAtLeastOneSource && nonEmptyUrls.every((item) => item.isValid);

  const isReady = hasValidQuery && hasAtLeastOneSource && allUrlsValid;

  return {
    hasValidQuery,
    hasAtLeastOneSource,
    allUrlsValid,
    isReady,
  };
}
