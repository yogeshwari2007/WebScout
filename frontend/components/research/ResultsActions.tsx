"use client";

import * as React from "react";
import { Check, Copy, Download, BookmarkPlus, BookmarkCheck } from "lucide-react";
import { ResearchResult } from "@/lib/types";
import { copyMarkdownToClipboard, downloadComparisonCsv } from "@/lib/export";

interface ResultsActionsProps {
  result: ResearchResult;
  isSaved?: boolean;
  onSave?: () => void;
  showSaveButton?: boolean;
}

export function ResultsActions({
  result,
  isSaved = false,
  onSave,
  showSaveButton = false,
}: ResultsActionsProps) {
  const [copied, setCopied] = React.useState(false);
  const [downloading, setDownloading] = React.useState(false);
  const [copyFeedback, setCopyFeedback] = React.useState<string>("");

  const handleCopyMarkdown = async () => {
    try {
      const success = await copyMarkdownToClipboard(result);
      if (success) {
        setCopied(true);
        setCopyFeedback("Research results copied to clipboard as Markdown.");
        setTimeout(() => {
          setCopied(false);
          setCopyFeedback("");
        }, 2000);
      } else {
        setCopyFeedback("Unable to copy to clipboard automatically.");
      }
    } catch {
      setCopyFeedback("Error copying to clipboard.");
    }
  };

  const handleDownloadCsv = () => {
    try {
      setDownloading(true);
      downloadComparisonCsv(result, result.query);
      setTimeout(() => setDownloading(false), 1200);
    } catch (e) {
      console.error("Failed to generate CSV:", e);
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
      {/* Accessible live status announcement */}
      <span className="sr-only" aria-live="polite">
        {copyFeedback}
      </span>

      {/* Copy as Markdown Button */}
      <button
        type="button"
        onClick={handleCopyMarkdown}
        disabled={copied}
        title="Copy structured research dossier as clean Markdown"
        className={`inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-xl border transition-all duration-200 shadow-sm ${
          copied
            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-500"
            : "border-border bg-surface hover:bg-surface-hover text-foreground hover:border-primary/40"
        }`}
      >
        {copied ? (
          <>
            <Check className="h-4 w-4 text-emerald-500 animate-in zoom-in-50 duration-200" />
            <span>Copied Markdown!</span>
          </>
        ) : (
          <>
            <Copy className="h-4 w-4 text-primary" />
            <span>Copy as Markdown</span>
          </>
        )}
      </button>

      {/* Download CSV Button */}
      <button
        type="button"
        onClick={handleDownloadCsv}
        disabled={downloading}
        title="Download evaluation matrix and criteria as CSV"
        className={`inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-xl border transition-all duration-200 shadow-sm ${
          downloading
            ? "border-primary/40 bg-primary/10 text-primary"
            : "border-border bg-surface hover:bg-surface-hover text-foreground hover:border-primary/40"
        }`}
      >
        <Download
          className={`h-4 w-4 text-primary ${
            downloading ? "animate-bounce" : ""
          }`}
        />
        <span>{downloading ? "Preparing CSV..." : "Download CSV"}</span>
      </button>

      {/* Optional Save to History Button */}
      {showSaveButton && onSave && (
        <button
          type="button"
          onClick={onSave}
          disabled={isSaved}
          title={isSaved ? "Session saved to history" : "Save this session to local history"}
          className={`inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-xl border transition-all duration-200 shadow-sm ${
            isSaved
              ? "border-primary/30 bg-primary/10 text-primary cursor-default"
              : "border-primary/40 bg-primary text-white hover:bg-primary-hover"
          }`}
        >
          {isSaved ? (
            <>
              <BookmarkCheck className="h-4 w-4" />
              <span>Saved in History</span>
            </>
          ) : (
            <>
              <BookmarkPlus className="h-4 w-4" />
              <span>Save to History</span>
            </>
          )}
        </button>
      )}
    </div>
  );
}
