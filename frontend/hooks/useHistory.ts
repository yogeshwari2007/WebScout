"use client";

import * as React from "react";
import { HistoryEntry, ResearchResult } from "@/lib/types";
import {
  getHistory,
  saveHistoryEntry as saveStorageEntry,
  deleteHistoryEntry as deleteStorageEntry,
  clearHistory as clearStorageHistory,
  getHistoryEntry as getStorageEntry,
} from "@/lib/storage";

export function useHistory() {
  const [entries, setEntries] = React.useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  // Load entries on mount
  const refresh = React.useCallback(() => {
    const data = getHistory();
    setEntries(data);
    setIsLoading(false);
  }, []);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const saveEntry = React.useCallback(
    (data: { query: string; result: ResearchResult; isSample?: boolean }) => {
      const saved = saveStorageEntry(data);
      refresh();
      return saved;
    },
    [refresh]
  );

  const deleteEntry = React.useCallback(
    (id: string) => {
      deleteStorageEntry(id);
      refresh();
    },
    [refresh]
  );

  const clearAll = React.useCallback(() => {
    clearStorageHistory();
    refresh();
  }, [refresh]);

  const getEntry = React.useCallback((id: string) => {
    return getStorageEntry(id);
  }, []);

  return {
    entries,
    isLoading,
    refresh,
    saveEntry,
    deleteEntry,
    clearAll,
    getEntry,
  };
}
