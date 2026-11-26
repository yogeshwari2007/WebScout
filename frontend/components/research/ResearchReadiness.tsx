"use client";

import * as React from "react";
import { CheckCircle2, Circle, AlertCircle, Sparkles } from "lucide-react";
import { ReadinessState } from "@/lib/types";

interface ResearchReadinessProps {
  readiness: ReadinessState;
}

export function ResearchReadiness({ readiness }: ResearchReadinessProps) {
  const { hasValidQuery, hasAtLeastOneSource, allUrlsValid, isReady } = readiness;

  const checks = [
    {
      id: "query",
      label: "Research question entered",
      completed: hasValidQuery,
    },
    {
      id: "source-presence",
      label: "At least one source added",
      completed: hasAtLeastOneSource,
    },
    {
      id: "urls-valid",
      label: "All entered URLs validated",
      completed: allUrlsValid,
    },
    {
      id: "ready",
      label: "Ready to research",
      completed: isReady,
    },
  ];

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-4">
      {/* Header & Status Banner */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Research Readiness
          </span>
          <span
            className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
              isReady
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                : "bg-muted text-muted-foreground border border-border"
            }`}
          >
            {isReady ? "Ready" : "Incomplete"}
          </span>
        </div>

        <p
          className={`text-xs font-medium transition-colors ${
            isReady ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
          }`}
          aria-live="polite"
        >
          {isReady
            ? "Everything looks good. Ready to explore."
            : "Your research setup needs a little more information."}
        </p>
      </div>

      {/* 4 Check Items */}
      <div className="space-y-2.5 pt-1 border-t border-border">
        {checks.map((item) => (
          <div
            key={item.id}
            className={`flex items-center gap-2.5 text-xs transition-colors ${
              item.completed ? "text-foreground font-medium" : "text-muted-foreground"
            }`}
          >
            {item.completed ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
            ) : (
              <Circle className="h-4 w-4 text-muted-foreground/40 shrink-0" />
            )}
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
