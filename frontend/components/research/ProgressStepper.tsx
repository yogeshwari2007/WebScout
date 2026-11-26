"use client";

import * as React from "react";
import { Compass, Filter, Sparkles, FileText, Check, AlertCircle, Loader2 } from "lucide-react";
import { StageInfo, StageStatus } from "@/lib/types";

export const DEFAULT_STAGES: StageInfo[] = [
  {
    id: "navigating",
    number: "01",
    title: "NAVIGATING",
    description: "Visiting your selected websites.",
    status: "active",
  },
  {
    id: "extracting",
    number: "02",
    title: "EXTRACTING",
    description: "Collecting relevant information from each source.",
    status: "pending",
  },
  {
    id: "analysing",
    number: "03",
    title: "ANALYSING",
    description: "Comparing extracted findings using AI.",
    status: "pending",
  },
  {
    id: "compiling",
    number: "04",
    title: "COMPILING",
    description: "Preparing your comparison and recommendation.",
    status: "pending",
  },
];

interface ProgressStepperProps {
  stages?: StageInfo[];
  isIndeterminate?: boolean;
}

export function ProgressStepper({
  stages = DEFAULT_STAGES,
  isIndeterminate = true,
}: ProgressStepperProps) {
  const getIcon = (id: string) => {
    switch (id) {
      case "navigating":
        return Compass;
      case "extracting":
        return Filter;
      case "analysing":
        return Sparkles;
      case "compiling":
        return FileText;
      default:
        return Compass;
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div className="space-y-0.5">
          <span className="text-xs font-bold uppercase tracking-widest text-primary">
            Autonomous Pipeline
          </span>
          <h2 className="text-base sm:text-lg font-semibold text-foreground">
            Research Workflow Progress
          </h2>
        </div>

        {/* Live Indeterminate Activity Badge */}
        {isIndeterminate && (
          <div className="flex items-center gap-2 self-start sm:self-auto px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
            </span>
            <span>Agent Active &bull; Processing Sources</span>
          </div>
        )}
      </div>

      {/* Stepper Container: Connected on Desktop, Vertical on Mobile */}
      <div className="relative">
        {/* Desktop Progress Line */}
        <div
          className="hidden lg:block absolute top-6 left-8 right-8 h-[2px] bg-border -z-0"
          aria-hidden="true"
        />

        <ol
          role="list"
          aria-label="Research progress stages"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 relative z-10"
        >
          {stages.map((stage) => {
            const Icon = getIcon(stage.id);
            const status = stage.status;
            const isCompleted = status === "completed";
            const isActive = status === "active";
            const isFailed = status === "failed";
            const isPending = status === "pending";

            return (
              <li
                key={stage.id}
                aria-current={isActive ? "step" : undefined}
                className={`relative flex flex-col p-4 sm:p-5 rounded-xl border transition-all duration-200 ${
                  isActive
                    ? "bg-primary/5 dark:bg-primary/10 border-primary ring-1 ring-primary/40 shadow-subtle"
                    : isCompleted
                    ? "bg-emerald-500/5 dark:bg-emerald-500/10 border-emerald-500/30"
                    : isFailed
                    ? "bg-amber-500/5 dark:bg-amber-500/10 border-amber-500/30"
                    : "bg-surface border-border text-muted-foreground opacity-75"
                }`}
              >
                {/* Stage Indicator & Icon */}
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${
                      isActive
                        ? "bg-primary text-primary-foreground border-primary shadow-subtle"
                        : isCompleted
                        ? "bg-emerald-500 text-white border-emerald-500"
                        : isFailed
                        ? "bg-amber-500 text-white border-amber-500"
                        : "bg-muted text-muted-foreground border-border"
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="h-4 w-4 stroke-[2.5]" />
                    ) : isFailed ? (
                      <AlertCircle className="h-4 w-4" />
                    ) : isActive ? (
                      <Icon className="h-4 w-4 animate-pulse" />
                    ) : (
                      <Icon className="h-4 w-4" />
                    )}
                  </div>

                  <span className="text-xs font-mono font-bold tracking-wider text-muted-foreground/60">
                    {stage.number}
                  </span>
                </div>

                {/* Stage Title & Status */}
                <div className="space-y-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-bold tracking-wider uppercase ${
                        isActive
                          ? "text-primary"
                          : isCompleted
                          ? "text-emerald-600 dark:text-emerald-400"
                          : isFailed
                          ? "text-amber-600 dark:text-amber-400"
                          : "text-muted-foreground"
                      }`}
                    >
                      {stage.title}
                    </span>

                    {isActive && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-primary/20 text-primary">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {stage.description}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      {/* Honest Transparency Note */}
      <div className="pt-2 text-center text-xs text-muted-foreground">
        <p>
          WebScout completes full multi-site extraction and verification before compiling your comparison.
        </p>
      </div>
    </div>
  );
}
