"use client";

import * as React from "react";
import { Globe, CheckCircle2, AlertTriangle, Clock, ExternalLink } from "lucide-react";
import { SourceReference } from "@/lib/types";

interface SourceDossierListProps {
  sources: SourceReference[];
}

export function SourceDossierList({ sources }: SourceDossierListProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-4">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <Globe className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-foreground">
              Sources Consulted ({sources.length})
            </h3>
            <span className="text-xs text-muted-foreground">
              Authoritative websites analysed for this synthesis
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {sources.map((src, idx) => {
          const isSuccess = src.status === "success";
          const isFailed = src.status === "failed";

          return (
            <div
              key={idx}
              className="rounded-xl border border-border bg-surface-hover/30 p-3.5 space-y-2 flex flex-col justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-mono font-semibold text-foreground truncate">
                    {src.hostname}
                  </span>
                  {isSuccess ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <CheckCircle2 className="h-3 w-3" />
                      Verified
                    </span>
                  ) : isFailed ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-500 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                      <AlertTriangle className="h-3 w-3" />
                      Failed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                      <Clock className="h-3 w-3" />
                      {src.status}
                    </span>
                  )}
                </div>

                {src.title && (
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {src.title}
                  </p>
                )}
              </div>

              <div className="pt-2 border-t border-border/60">
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:text-primary-hover transition-colors"
                >
                  <span>Visit source</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
