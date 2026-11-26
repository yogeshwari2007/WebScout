"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Compass, Globe } from "lucide-react";

interface ResultsHeaderProps {
  query: string;
  sourceCount: number;
  hostnames: string[];
  statusLabel?: string;
  title?: string;
  description?: string;
  breadcrumbCurrent?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  onEdit?: () => void;
}

export function ResultsHeader({
  query,
  sourceCount,
  hostnames,
  statusLabel = "RESEARCH SESSION",
  title = "WebScout is exploring the web.",
  description = "Gathering information, analysing sources and preparing your comparison.",
  breadcrumbCurrent = "Processing",
  badge,
  actions,
  onEdit,
}: ResultsHeaderProps) {
  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Status Label */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <span>/</span>
          <Link href="/research" className="hover:text-foreground transition-colors">
            Research
          </Link>
          <span>/</span>
          <span className="text-foreground font-medium">{breadcrumbCurrent}</span>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {badge ? (
            badge
          ) : (
            <span className="text-[11px] font-mono uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              {statusLabel}
            </span>
          )}
        </div>
      </div>

      {/* Main Title Banner & Actions */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2 max-w-3xl">
          <span className="text-[11px] font-bold uppercase tracking-widest text-primary flex items-center gap-1.5">
            <Compass className="h-3.5 w-3.5" />
            WebScout Multi-Website Agent
          </span>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-foreground">
            {title}
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            {description}
          </p>
        </div>

        {actions && <div className="shrink-0">{actions}</div>}
      </div>

      {/* Query Card */}
      <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="space-y-1.5 max-w-2xl">
            <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Research Objective
            </span>
            <p className="text-sm sm:text-base font-semibold text-foreground leading-relaxed break-words">
              &ldquo;{query}&rdquo;
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onEdit ? (
              <button
                type="button"
                onClick={onEdit}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-hover px-3 py-1.5 rounded-xl border border-primary/20 bg-primary/5 hover:bg-primary/10 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Edit Request</span>
              </button>
            ) : (
              <Link
                href="/research"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-hover px-3 py-1.5 rounded-xl border border-primary/20 bg-primary/5 hover:bg-primary/10 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Edit Request</span>
              </Link>
            )}
          </div>
        </div>

        {/* Source Pills */}
        <div className="pt-3 border-t border-border flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground font-medium">
            Target Sources ({sourceCount}):
          </span>
          {hostnames.map((host, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-muted text-foreground border border-border"
            >
              <Globe className="h-3 w-3 text-primary" />
              {host}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
