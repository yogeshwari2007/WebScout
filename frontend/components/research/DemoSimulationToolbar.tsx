"use client";

import * as React from "react";
import { Play, RotateCcw, AlertTriangle, Sparkles, Sliders, ChevronDown, ChevronUp } from "lucide-react";
import { StageId, StageInfo, SourceStatusItem, SourceStatusType, ErrorScenarioType } from "@/lib/types";

interface DemoSimulationToolbarProps {
  isSimulating: boolean;
  onToggleSimulating: (active: boolean) => void;
  onSetStage: (stageId: StageId) => void;
  onSetSourceStatus: (statusPreset: "all_fetching" | "all_success" | "partial_fail" | "timeout") => void;
  onSetError: (errorType: ErrorScenarioType | null) => void;
  onRunDemoSequence: () => void;
  onReset: () => void;
}

export function DemoSimulationToolbar({
  isSimulating,
  onToggleSimulating,
  onSetStage,
  onSetSourceStatus,
  onSetError,
  onRunDemoSequence,
  onReset,
}: DemoSimulationToolbarProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="rounded-2xl border border-primary/30 bg-surface/95 backdrop-blur-md p-4 shadow-card text-xs space-y-3">
      {/* Header & Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="p-1 rounded-md bg-primary/10 text-primary">
            <Sliders className="h-3.5 w-3.5" />
          </span>
          <div>
            <span className="font-semibold text-foreground">
              Hackathon Demo Simulation Mode
            </span>
            <span className="ml-2 text-[10px] uppercase font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
              Dev Only
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 cursor-pointer font-medium text-foreground select-none">
            <input
              type="checkbox"
              checked={isSimulating}
              onChange={(e) => onToggleSimulating(e.target.checked)}
              className="rounded border-border text-primary focus:ring-primary h-4 w-4"
            />
            <span>Enable Simulation</span>
          </label>

          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            aria-label="Toggle simulation panel"
            className="p-1 rounded-md hover:bg-muted text-muted-foreground transition-colors"
          >
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Controls when Simulation is Active */}
      {isSimulating && (
        <div className="pt-2 border-t border-border space-y-3">
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            Preview the 4 workflow stages, individual source status states, and failure alerts without waiting for live backend crawling.
          </p>

          <div className="flex flex-wrap items-center gap-2">
            {/* Auto Sequence Play */}
            <button
              type="button"
              onClick={onRunDemoSequence}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-primary-foreground font-semibold shadow-subtle hover:bg-primary-hover transition-colors"
            >
              <Play className="h-3 w-3" />
              <span>Simulate Full Workflow</span>
            </button>

            {/* Reset */}
            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border bg-background hover:bg-muted text-muted-foreground transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset to Live Default</span>
            </button>
          </div>

          {/* Quick Stage Selectors */}
          <div className="space-y-1.5">
            <span className="font-semibold text-muted-foreground">Jump to Stage:</span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => onSetStage("navigating")}
                className="px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted font-medium"
              >
                01. Navigating
              </button>
              <button
                type="button"
                onClick={() => onSetStage("extracting")}
                className="px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted font-medium"
              >
                02. Extracting
              </button>
              <button
                type="button"
                onClick={() => onSetStage("analysing")}
                className="px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted font-medium"
              >
                03. Analysing
              </button>
              <button
                type="button"
                onClick={() => onSetStage("compiling")}
                className="px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted font-medium"
              >
                04. Compiling
              </button>
            </div>
          </div>

          {/* Source Status & Error State Simulation */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="space-y-1">
              <span className="font-semibold text-muted-foreground">Source States:</span>
              <div className="flex flex-wrap gap-1">
                <button
                  type="button"
                  onClick={() => onSetSourceStatus("all_fetching")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  All Fetching
                </button>
                <button
                  type="button"
                  onClick={() => onSetSourceStatus("all_success")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  All Success
                </button>
                <button
                  type="button"
                  onClick={() => onSetSourceStatus("partial_fail")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  Partial Fail
                </button>
                <button
                  type="button"
                  onClick={() => onSetSourceStatus("timeout")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  Timeout
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <span className="font-semibold text-muted-foreground">Error Scenarios:</span>
              <div className="flex flex-wrap gap-1">
                <button
                  type="button"
                  onClick={() => onSetError(null)}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  No Error
                </button>
                <button
                  type="button"
                  onClick={() => onSetError("backend_unreachable")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  Backend Off
                </button>
                <button
                  type="button"
                  onClick={() => onSetError("all_failed")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  Sources Fail
                </button>
                <button
                  type="button"
                  onClick={() => onSetError("partial_failure")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  Partial Warn
                </button>
                <button
                  type="button"
                  onClick={() => onSetError("analysis_failed")}
                  className="px-2 py-0.5 rounded border border-border bg-background text-[11px]"
                >
                  AI Error
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
