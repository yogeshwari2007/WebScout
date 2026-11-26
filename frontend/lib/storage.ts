import { HistoryEntry, ResearchResult } from "./types";

const STORAGE_KEY = "webscout_history_v1";
const MAX_ENTRIES = 20;

/**
 * Checks if window and localStorage are available.
 */
function isStorageAvailable(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const testKey = "__ws_storage_test__";
    window.localStorage.setItem(testKey, "1");
    window.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validates whether an item matches the HistoryEntry contract.
 */
function isValidHistoryEntry(item: unknown): item is HistoryEntry {
  if (!item || typeof item !== "object") return false;
  const candidate = item as Partial<HistoryEntry>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.timestamp === "number" &&
    typeof candidate.query === "string" &&
    Boolean(candidate.result) &&
    typeof candidate.result?.query === "string" &&
    Array.isArray(candidate.result?.criteria) &&
    Array.isArray(candidate.result?.items) &&
    Boolean(candidate.result?.recommendation)
  );
}

/**
 * Retrieves all valid saved research sessions, sorted newest first.
 * Catches parse errors and ignores corrupted entries.
 */
export function getHistory(): HistoryEntry[] {
  if (!isStorageAvailable()) return [];

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      // Data was corrupted or in wrong format; reset safely
      window.localStorage.removeItem(STORAGE_KEY);
      return [];
    }

    const validEntries: HistoryEntry[] = [];
    for (const item of parsed) {
      if (isValidHistoryEntry(item)) {
        validEntries.push(item);
      }
    }

    // Sort newest first
    return validEntries.sort((a, b) => b.timestamp - a.timestamp);
  } catch {
    // If parse completely fails, return safe empty list without crashing
    return [];
  }
}

/**
 * Safely persists entries to localStorage, handling quota errors by pruning oldest entries.
 */
function persistEntries(entries: HistoryEntry[]): boolean {
  if (!isStorageAvailable()) return false;

  let currentList = entries.slice(0, MAX_ENTRIES);

  while (currentList.length > 0) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(currentList));
      return true;
    } catch (e: unknown) {
      // Check if QuotaExceededError
      const isQuotaError =
        e instanceof DOMException &&
        (e.name === "QuotaExceededError" ||
          e.name === "NS_ERROR_DOM_QUOTA_REACHED" ||
          e.code === 22 ||
          e.code === 1014);

      if (isQuotaError && currentList.length > 1) {
        // Prune the oldest entry and retry
        currentList.pop();
      } else {
        // Unrecoverable storage error
        console.warn("Failed to write to localStorage:", e);
        return false;
      }
    }
  }

  return false;
}

/**
 * Saves a new research result to localStorage.
 * Deduplicates identical queries submitted within a short window.
 * Enforces maximum limit of 20 entries.
 */
export function saveHistoryEntry(data: {
  query: string;
  result: ResearchResult;
  isSample?: boolean;
}): HistoryEntry {
  const existing = getHistory();

  // Deduplication check: Avoid duplicating identical query if saved within the last 5 seconds
  const now = Date.now();
  const duplicate = existing.find(
    (e) =>
      e.query.trim().toLowerCase() === data.query.trim().toLowerCase() &&
      Math.abs(e.timestamp - now) < 5000
  );

  if (duplicate) {
    return duplicate;
  }

  const id =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `ws_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

  const newEntry: HistoryEntry = {
    id,
    timestamp: now,
    query: data.query.trim(),
    result: data.result,
    isSample: Boolean(data.isSample),
  };

  const updated = [newEntry, ...existing];
  persistEntries(updated);

  return newEntry;
}

/**
 * Retrieves a single history entry by ID.
 */
export function getHistoryEntry(id: string): HistoryEntry | null {
  if (!id) return null;
  const entries = getHistory();
  return entries.find((e) => e.id === id) || null;
}

/**
 * Removes a single history entry by ID.
 */
export function deleteHistoryEntry(id: string): void {
  if (!id) return;
  const existing = getHistory();
  const updated = existing.filter((e) => e.id !== id);
  persistEntries(updated);
}

/**
 * Clears all research history from localStorage.
 */
export function clearHistory(): void {
  if (!isStorageAvailable()) return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore removal failure
  }
}
