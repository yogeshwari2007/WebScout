"use client";

import * as React from "react";

export function SummarySkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4 animate-pulse">
      <div className="h-4 w-32 bg-muted rounded-md" />
      <div className="space-y-2">
        <div className="h-3 w-full bg-muted/80 rounded" />
        <div className="h-3 w-5/6 bg-muted/80 rounded" />
        <div className="h-3 w-4/6 bg-muted/80 rounded" />
      </div>
    </div>
  );
}

export function ComparisonTableSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-40 bg-muted rounded-md" />
        <div className="h-4 w-20 bg-muted rounded-md" />
      </div>

      <div className="space-y-3 pt-2">
        <div className="h-10 w-full bg-muted/60 rounded-xl" />
        <div className="h-12 w-full bg-muted/40 rounded-xl" />
        <div className="h-12 w-full bg-muted/40 rounded-xl" />
        <div className="h-12 w-full bg-muted/40 rounded-xl" />
      </div>
    </div>
  );
}

export function RecommendationSkeleton() {
  return (
    <div className="rounded-2xl border border-primary/20 bg-primary/5 p-6 shadow-card space-y-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-36 bg-primary/20 rounded-md" />
        <div className="h-4 w-24 bg-primary/20 rounded-md" />
      </div>
      <div className="h-5 w-3/4 bg-primary/25 rounded" />
      <div className="space-y-2 pt-1">
        <div className="h-3 w-full bg-primary/15 rounded" />
        <div className="h-3 w-4/5 bg-primary/15 rounded" />
      </div>
    </div>
  );
}

export function SourceListSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3 animate-pulse">
      <div className="h-4 w-36 bg-muted rounded-md" />
      <div className="space-y-2 pt-2">
        <div className="h-12 w-full bg-muted/50 rounded-xl" />
        <div className="h-12 w-full bg-muted/50 rounded-xl" />
        <div className="h-12 w-full bg-muted/50 rounded-xl" />
      </div>
    </div>
  );
}
