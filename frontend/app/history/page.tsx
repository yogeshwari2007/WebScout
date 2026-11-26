"use client";

import * as React from "react";
import Link from "next/link";
import {
  Layers,
  Trash2,
  Plus,
  Sparkles,
  Archive,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useHistory } from "@/hooks/useHistory";
import { HistoryList } from "@/components/history/HistoryList";
import { HistoryEmptyState } from "@/components/history/HistoryEmptyState";
import { ClearHistoryDialog } from "@/components/history/ClearHistoryDialog";
import { SAMPLE_RESEARCH_RESULT } from "@/lib/sampleData";

export default function HistoryPage() {
  const { entries, isLoading, deleteEntry, clearAll, saveEntry } = useHistory();
  const [isClearDialogOpen, setIsClearDialogOpen] = React.useState(false);

  const handleLoadSample = () => {
    saveEntry({
      query: SAMPLE_RESEARCH_RESULT.query,
      result: SAMPLE_RESEARCH_RESULT,
      isSample: true,
    });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* 1. Breadcrumbs & Status Tag */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <span>/</span>
          <span className="text-foreground font-medium">History</span>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[11px] font-mono uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20 flex items-center gap-1.5">
            <Archive className="w-3.5 h-3.5" />
            LOCAL BROWSER ARCHIVE
          </span>
        </div>
      </div>

      {/* 2. Page Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border pb-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
            <Layers className="h-4 w-4" />
            <span>Saved Intelligence Dossiers</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
            Research History
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
            Review, reopen, and export previous multi-website research reports
            stored privately in your browser.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {entries.length > 0 && (
            <button
              type="button"
              onClick={() => setIsClearDialogOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl border border-border bg-surface hover:bg-rose-500/10 hover:border-rose-500/30 text-muted-foreground hover:text-rose-500 transition-colors shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear History</span>
            </button>
          )}

          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleLoadSample}
            title="Load realistic sample dossier to evaluate features"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Load Sample Session</span>
          </Button>

          <Link href="/research">
            <Button variant="primary" size="sm">
              <Plus className="h-3.5 w-3.5" />
              <span>New Research</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* 3. Main Content List or Empty State */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-44 rounded-2xl border border-border bg-surface/50 p-6 animate-pulse space-y-3"
            >
              <div className="h-4 w-28 bg-muted rounded" />
              <div className="h-5 w-3/4 bg-muted rounded" />
              <div className="h-4 w-1/2 bg-muted rounded" />
            </div>
          ))}
        </div>
      ) : entries.length === 0 ? (
        <HistoryEmptyState onLoadSample={handleLoadSample} />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span>
              Showing {entries.length} saved session{entries.length === 1 ? "" : "s"}
            </span>
            <span className="text-[11px] font-mono">Max capacity: 20</span>
          </div>

          <HistoryList entries={entries} onDelete={deleteEntry} />
        </div>
      )}

      {/* 4. Clear Confirmation Dialog */}
      <ClearHistoryDialog
        isOpen={isClearDialogOpen}
        onClose={() => setIsClearDialogOpen(false)}
        onConfirm={clearAll}
        entryCount={entries.length}
      />
    </div>
  );
}
