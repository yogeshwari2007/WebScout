"use client";

import * as React from "react";
import Link from "next/link";
import {
  Calendar,
  Globe,
  Trophy,
  Trash2,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import { HistoryEntry } from "@/lib/types";

interface HistoryCardProps {
  entry: HistoryEntry;
  onDelete: (id: string) => void;
}

/**
 * Formats timestamps into readable relative or absolute strings
 */
function formatTimeAgo(timestamp: number): string {
  const diffSec = Math.floor((Date.now() - timestamp) / 1000);
  if (diffSec < 60) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function HistoryCard({ entry, onDelete }: HistoryCardProps) {
  const { id, query, timestamp, result, isSample } = entry;
  const timeLabel = formatTimeAgo(timestamp);
  const sourceCount = result.sources?.length || 0;
  const winner = result.recommendation?.winner;

  const [confirmDelete, setConfirmDelete] = React.useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirmDelete) {
      onDelete(id);
    } else {
      setConfirmDelete(true);
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  return (
    <div className="group rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card hover:border-primary/40 hover:shadow-lg transition-all duration-200 flex flex-col justify-between gap-4">
      <div className="space-y-3">
        {/* Top Badges & Time */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
              <Calendar className="h-3 w-3 text-primary" />
              <span>{timeLabel}</span>
            </span>

            {isSample && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                <Sparkles className="h-3 w-3" />
                Sample
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {sourceCount > 0 && (
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-muted-foreground bg-surface-hover px-2 py-0.5 rounded-md border border-border">
                <Globe className="h-3 w-3 text-primary" />
                <span>{sourceCount} {sourceCount === 1 ? "source" : "sources"}</span>
              </span>
            )}
          </div>
        </div>

        {/* Query Title */}
        <h3 className="text-base sm:text-lg font-bold text-foreground leading-snug group-hover:text-primary transition-colors line-clamp-2">
          &ldquo;{query}&rdquo;
        </h3>

        {/* Winner Highlight */}
        {winner && (
          <div className="flex items-start gap-1.5 text-xs text-foreground/80 bg-primary/5 p-2.5 rounded-xl border border-primary/15">
            <Trophy className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
            <div className="line-clamp-1">
              <span className="font-semibold text-primary mr-1">Winner:</span>
              <span>{winner}</span>
            </div>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-border flex items-center justify-between gap-3">
        <Link
          href={`/research/results?historyId=${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-hover py-1.5 px-3 rounded-xl border border-primary/20 bg-primary/5 hover:bg-primary/10 transition-colors"
        >
          <span>Reopen Dossier</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>

        <button
          type="button"
          onClick={handleDelete}
          title={confirmDelete ? "Click again to confirm deletion" : "Delete session"}
          className={`inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1.5 rounded-xl border transition-colors ${
            confirmDelete
              ? "border-rose-500/40 bg-rose-500/10 text-rose-500 font-bold"
              : "border-transparent text-muted-foreground hover:text-rose-500 hover:bg-rose-500/5"
          }`}
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>{confirmDelete ? "Confirm?" : "Delete"}</span>
        </button>
      </div>
    </div>
  );
}
