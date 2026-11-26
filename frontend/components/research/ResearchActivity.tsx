"use client";

import * as React from "react";
import { Compass, FileSearch, Filter, Sparkles } from "lucide-react";

export function ResearchActivity() {
  const activities = [
    {
      title: "Understanding Research Requirements",
      description:
        "Parsing your natural-language query to isolate the primary comparative factors, constraints, and decision priorities.",
      icon: FileSearch,
    },
    {
      title: "Visiting Target Websites",
      description:
        "Launching headless browser navigation to load live rendered DOM trees, bypass client hydration delays, and collect source pages.",
      icon: Compass,
    },
    {
      title: "Extracting Relevant Page Evidence",
      description:
        "Stripping boilerplate noise, cookie modals, and navigation menus to isolate factual product specifications and technical details.",
      icon: Filter,
    },
    {
      title: "Preparing Structured Comparisons",
      description:
        "Cross-referencing findings across all accessible sources, detecting conflicting claims, and compiling evidence-backed recommendations.",
      icon: Sparkles,
    },
  ];

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-5">
      {/* Header */}
      <div className="space-y-1 pb-3 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground tracking-tight">
          Behind the research
        </h3>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Here&apos;s how WebScout approaches your request.
        </p>
      </div>

      {/* 4 Informational Activity Explanations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {activities.map((item, index) => {
          const Icon = item.icon;
          return (
            <div
              key={index}
              className="p-4 rounded-xl border border-border bg-background/50 space-y-2 hover:border-primary/30 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20 shrink-0">
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <h4 className="text-xs font-semibold text-foreground">
                  {item.title}
                </h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {item.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
