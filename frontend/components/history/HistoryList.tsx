"use client";

import * as React from "react";
import { HistoryEntry } from "@/lib/types";
import { HistoryCard } from "./HistoryCard";

interface HistoryListProps {
  entries: HistoryEntry[];
  onDelete: (id: string) => void;
}

export function HistoryList({ entries, onDelete }: HistoryListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {entries.map((entry) => (
        <HistoryCard key={entry.id} entry={entry} onDelete={onDelete} />
      ))}
    </div>
  );
}
