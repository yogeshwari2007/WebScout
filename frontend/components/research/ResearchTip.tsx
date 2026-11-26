"use client";

import * as React from "react";
import { Lightbulb } from "lucide-react";

interface ResearchTipProps {
  tip?: string;
}

export function ResearchTip({ tip }: ResearchTipProps) {
  const displayTip =
    tip ||
    "Better questions lead to better comparisons. Include the factors that matter most to your decision.";

  return (
    <div className="rounded-2xl border border-border bg-surface p-4 shadow-subtle flex items-start gap-3">
      <div className="p-1.5 rounded-lg bg-primary/10 text-primary shrink-0 mt-0.5">
        <Lightbulb className="h-4 w-4" />
      </div>
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-primary">
          Research Tip
        </span>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {displayTip}
        </p>
      </div>
    </div>
  );
}
