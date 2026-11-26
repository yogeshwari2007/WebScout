"use client";

import * as React from "react";
import { Clock, FileText, CheckCircle2 } from "lucide-react";
import { ResearchResult } from "@/lib/types";

interface ExecutiveSummaryProps {
  result: ResearchResult;
}

export function ExecutiveSummary({ result }: ExecutiveSummaryProps) {
  const dateStr = result.createdAt
    ? new Date(result.createdAt).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Just now";

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-foreground">
              Executive Summary
            </h2>
            <span className="text-xs text-muted-foreground">
              Synthesized multi-source intelligence
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {result.durationSeconds !== undefined && (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3.5 w-3.5 text-primary" />
              <span>{result.durationSeconds}s research duration</span>
            </span>
          )}
          <span>•</span>
          <span className="inline-flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            <span>Completed {dateStr}</span>
          </span>
        </div>
      </div>

      <p className="text-sm sm:text-base text-foreground/90 leading-relaxed">
        {result.summary}
      </p>

      {result.criteria && result.criteria.length > 0 && (
        <div className="pt-2 flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold text-muted-foreground mr-1">
            Evaluation Dimensions:
          </span>
          {result.criteria.map((dim, idx) => (
            <span
              key={idx}
              className="text-[11px] font-medium px-2.5 py-1 rounded-lg bg-surface-hover text-foreground/80 border border-border"
            >
              {dim}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
