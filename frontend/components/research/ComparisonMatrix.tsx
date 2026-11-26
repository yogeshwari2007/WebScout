"use client";

import * as React from "react";
import { Table, Check, X, ExternalLink, HelpCircle } from "lucide-react";
import { ResearchResult } from "@/lib/types";

interface ComparisonMatrixProps {
  result: ResearchResult;
}

export function ComparisonMatrix({ result }: ComparisonMatrixProps) {
  const criteria = result.criteria || [];
  const items = result.items || [];

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <Table className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-foreground">
              Comparative Evaluation Matrix
            </h2>
            <span className="text-xs text-muted-foreground">
              Dynamic multi-attribute analysis across {items.length} candidate options
            </span>
          </div>
        </div>

        <span className="text-xs font-medium text-primary bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20 self-start sm:self-auto">
          {criteria.length} Comparison Dimensions
        </span>
      </div>

      {/* Responsive Table Scroll Container */}
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm border-collapse min-w-[600px] sm:min-w-[650px]">
          <thead>
            <tr className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <th className="py-3.5 px-3 sm:px-4 sticky left-0 bg-muted/90 backdrop-blur-sm z-10 w-40 sm:w-56">
                Compared Option
              </th>
              {criteria.map((criterion, idx) => (
                <th key={idx} className="py-3.5 px-3 sm:px-4 font-semibold text-foreground min-w-[150px]">
                  {criterion}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-foreground">
            {items.map((item, idx) => {
              const isWinner =
                result.recommendation.winner &&
                result.recommendation.winner
                  .toLowerCase()
                  .includes(item.name.toLowerCase());

              return (
                <tr
                  key={item.id || idx}
                  className="hover:bg-surface-hover/60 transition-colors"
                >
                  <td className="py-4 px-3 sm:px-4 sticky left-0 bg-surface z-10 font-medium w-40 sm:w-56">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-foreground text-xs sm:text-sm">
                        <span className="truncate max-w-[120px] sm:max-w-none">{item.name}</span>
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-muted-foreground hover:text-primary transition-colors shrink-0"
                            title="Open external source"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        )}
                      </div>
                      {isWinner && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded-md border border-primary/20">
                          Top Choice
                        </span>
                      )}
                    </div>
                  </td>

                  {criteria.map((criterion, cIdx) => {
                    const val = item.criteriaValues?.[criterion];
                    return (
                      <td
                        key={cIdx}
                        className="py-4 px-3 sm:px-4 text-xs sm:text-sm text-foreground/80 leading-relaxed align-top min-w-[150px] max-w-xs break-words"
                      >
                        {val ? (
                          <span>{val}</span>
                        ) : (
                          <span className="text-muted-foreground italic flex items-center gap-1">
                            <HelpCircle className="h-3 w-3" />
                            Not available
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Granular Pros and Cons Grid */}
      <div className="pt-2 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
          Detailed Pros &amp; Trade-Offs by Option
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-border bg-surface-hover/30 p-4 space-y-3"
            >
              <h4 className="text-sm font-bold text-foreground border-b border-border pb-2">
                {item.name}
              </h4>

              {/* Pros */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold uppercase text-emerald-500 flex items-center gap-1">
                  <Check className="h-3 w-3" />
                  Key Strengths
                </span>
                <ul className="text-xs space-y-1 text-foreground/80">
                  {item.pros && item.pros.length > 0 ? (
                    item.pros.map((p, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{p}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-muted-foreground italic">None listed</li>
                  )}
                </ul>
              </div>

              {/* Cons */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-bold uppercase text-rose-500 flex items-center gap-1">
                  <X className="h-3 w-3" />
                  Trade-Offs &amp; Caveats
                </span>
                <ul className="text-xs space-y-1 text-foreground/80">
                  {item.cons && item.cons.length > 0 ? (
                    item.cons.map((c, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-rose-500 font-bold">•</span>
                        <span>{c}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-muted-foreground italic">None noted</li>
                  )}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
