export const GEMINI_KEY_STORAGE_KEY = "webscout_gemini_api_key_v1";
const GEMINI_KEY_CHANGE_EVENT = "webscout-gemini-key-change";
const PLACEHOLDER_KEYS = new Set(["", "your_gemini_api_key_here"]);

/**
 * Trims a candidate Gemini API key and rejects blank or placeholder strings.
 */
export function sanitizeGeminiApiKey(rawKey: string | null | undefined): string {
  const trimmed = (rawKey || "").trim();
  return PLACEHOLDER_KEYS.has(trimmed) ? "" : trimmed;
}

/**
 * Reads the tab-scoped Gemini API key from sessionStorage.
 */
export function getStoredGeminiApiKey(): string {
  if (typeof window === "undefined") return "";
  try {
    return sanitizeGeminiApiKey(
      window.sessionStorage.getItem(GEMINI_KEY_STORAGE_KEY)
    );
  } catch {
    return "";
  }
}

/**
 * Stores or clears the Gemini API key in tab-scoped sessionStorage and notifies subscribers.
 */
export function setStoredGeminiApiKey(rawKey: string): string {
  const cleaned = sanitizeGeminiApiKey(rawKey);
  if (typeof window === "undefined") return cleaned;

  try {
    if (cleaned) {
      window.sessionStorage.setItem(GEMINI_KEY_STORAGE_KEY, cleaned);
    } else {
      window.sessionStorage.removeItem(GEMINI_KEY_STORAGE_KEY);
    }
    window.dispatchEvent(new Event(GEMINI_KEY_CHANGE_EVENT));
  } catch {
    // Ignore storage unavailability
  }

  return cleaned;
}

/**
 * Removes any stored Gemini API key from sessionStorage.
 */
export function clearStoredGeminiApiKey(): void {
  setStoredGeminiApiKey("");
}

/**
 * Subscribes to in-tab Gemini API key changes.
 */
export function subscribeGeminiKeyChange(onChange: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(GEMINI_KEY_CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(GEMINI_KEY_CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}
