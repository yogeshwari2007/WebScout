"use client";

import * as React from "react";
import { Trophy, Sparkles, ExternalLink, ArrowRight } from "lucide-react";
import { ResearchResult } from "@/lib/types";

interface RecommendationCardProps {
  result: ResearchResult;
}

export function RecommendationCard({ result }: RecommendationCardProps) {
  const { recommendation } = result;

  return (
    <div className="rounded-2xl border-2 border-primary/30 bg-primary/5 p-6 sm:p-7 shadow-card space-y-5 relative overflow-hidden">
      {/* Decorative subtle ambient glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-primary/15 pb-4 relative z-10">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-primary text-white flex items-center justify-center shadow-sm">
            <Trophy className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-foreground">
                Synthesized Recommendation
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-primary bg-primary/15 px-2 py-0.5 rounded-md border border-primary/20">
                <Sparkles className="h-3 w-3" />
                Verified Winner
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              Cross-source authoritative verdict
            </span>
          </div>
        </div>

        <div className="text-sm font-bold text-primary sm:text-right">
          {recommendation.winner}
        </div>
      </div>

      {/* Winner Details */}
      <div className="space-y-3 relative z-10">
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          {recommendation.winner}
        </h3>
        <p className="text-sm sm:text-base text-foreground/90 leading-relaxed">
          {recommendation.reasoning}
        </p>
      </div>

      {/* Core Justifications */}
      {recommendation.keyStrengths && recommendation.keyStrengths.length > 0 && (
        <div className="space-y-2 pt-2 relative z-10">
          <span className="text-xs font-bold uppercase tracking-wider text-primary">
            Key Decision Factors:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {recommendation.keyStrengths.map((str, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-primary/20 bg-surface/80 p-3 text-xs text-foreground/90 flex items-start gap-2 shadow-xs"
              >
                <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                <span>{str}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supporting Citations */}
      {recommendation.sourceLinks && recommendation.sourceLinks.length > 0 && (
        <div className="pt-3 border-t border-primary/15 flex flex-wrap items-center gap-2 relative z-10">
          <span className="text-xs font-semibold text-muted-foreground mr-1">
            Primary Citations:
          </span>
          {recommendation.sourceLinks.map((link, idx) => (
            <a
              key={idx}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-hover px-2.5 py-1 rounded-lg border border-primary/20 bg-surface/60 hover:bg-surface transition-colors"
            >
              <span>{link.title}</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
