"use client";

import * as React from "react";
import { Globe, CheckCircle2, Clock, AlertCircle, AlertTriangle, ExternalLink } from "lucide-react";
import { SourceStatusItem, SourceStatusType } from "@/lib/types";

interface SourceStatusListProps {
  sources: SourceStatusItem[];
}

export function SourceStatusList({ sources }: SourceStatusListProps) {
  const getStatusBadge = (status: SourceStatusType) => {
    switch (status) {
      case "waiting":
        return {
          label: "Waiting in queue",
          icon: Clock,
          className:
            "bg-muted text-muted-foreground border-border",
        };
      case "fetching":
        return {
          label: "Navigating & reading...",
          icon: Globe,
          className:
            "bg-primary/10 text-primary border-primary/20 animate-pulse",
        };
      case "success":
        return {
          label: "Fetched successfully",
          icon: CheckCircle2,
          className:
            "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
        };
      case "failed":
        return {
          label: "Navigation failed",
          icon: AlertCircle,
          className:
            "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
        };
      case "timeout":
        return {
          label: "Timed out",
          icon: AlertTriangle,
          className:
            "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
        };
      default:
        return {
          label: "Waiting",
          icon: Clock,
          className: "bg-muted text-muted-foreground border-border",
        };
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="space-y-0.5">
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Target Sources Status
          </span>
          <h3 className="text-sm font-semibold text-foreground">
            Configured Websites ({sources.length})
          </h3>
        </div>

        <span className="text-xs font-mono text-muted-foreground">
          {sources.filter((s) => s.status === "success").length}/{sources.length} Verified
        </span>
      </div>

      {/* Sources List */}
      <div className="space-y-2.5">
        {sources.map((item, index) => {
          const badge = getStatusBadge(item.status);
          const Icon = badge.icon;

          return (
            <div
              key={`${item.url}-${index}`}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl border border-border bg-background/50 hover:bg-background transition-colors"
            >
              {/* Hostname & URL */}
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface border border-border text-primary shrink-0">
                  <Globe className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-foreground truncate">
                      {item.hostname || item.url}
                    </span>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      title={item.url}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <span className="text-[11px] font-mono text-muted-foreground truncate block max-w-xs sm:max-w-md">
                    {item.url}
                  </span>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                <span
                  className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border ${badge.className}`}
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span>{badge.label}</span>
                </span>
              </div>

              {/* Error Detail if Failed */}
              {item.error && (
                <div className="w-full text-xs text-red-500 pt-1 font-mono">
                  {item.error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
