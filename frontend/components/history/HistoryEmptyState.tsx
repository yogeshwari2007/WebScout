"use client";

import * as React from "react";
import Link from "next/link";
import { Layers, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface HistoryEmptyStateProps {
  onLoadSample?: () => void;
}

export function HistoryEmptyState({ onLoadSample }: HistoryEmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-10 sm:p-14 text-center space-y-6 max-w-2xl mx-auto shadow-sm">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
        <Layers className="h-8 w-8" />
      </div>

      <div className="space-y-2 max-w-md mx-auto">
        <h3 className="text-xl font-bold tracking-tight text-foreground">
          No Saved Research Sessions
        </h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Your synthesized research dossiers, comparative evaluation matrices, and
          source analyses will automatically be saved locally right here.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        <Link href="/research">
          <Button variant="primary" size="md">
            <span>Start New Research</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>

        {onLoadSample && (
          <Button variant="secondary" size="md" onClick={onLoadSample}>
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Load Sample Session</span>
          </Button>
        )}
      </div>
    </div>
  );
}
