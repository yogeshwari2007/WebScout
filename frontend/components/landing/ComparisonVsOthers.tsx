"use client";

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Check, Compass, Minus } from "lucide-react";

interface ComparisonRow {
  feature: string;
  searchEngines: string;
  chatbots: string;
  webscout: string;
}

const COMPARISON_DATA: ComparisonRow[] = [
  {
    feature: "Web navigation",
    searchEngines: "Manual",
    chatbots: "Limited",
    webscout: "Automated",
  },
  {
    feature: "Multi-site extraction",
    searchEngines: "Manual",
    chatbots: "Varies",
    webscout: "Yes",
  },
  {
    feature: "Structured comparison",
    searchEngines: "Manual",
    chatbots: "Yes",
    webscout: "Yes",
  },
  {
    feature: "Source-linked findings",
    searchEngines: "Links",
    chatbots: "Varies",
    webscout: "Yes",
  },
  {
    feature: "User-specific recommendations",
    searchEngines: "Limited",
    chatbots: "Yes",
    webscout: "Yes",
  },
];

export function ComparisonVsOthers() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section className="py-20 sm:py-28 border-t border-border bg-background transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-14 sm:mb-18">
          <span className="text-xs font-bold uppercase tracking-widest text-primary">
            Competitive Distinction
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
            Not another search engine.
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Search engines find information. Chatbots explain information.{" "}
            <span className="text-foreground font-semibold">WebScout researches it.</span>
          </p>
        </div>

        {/* Comparison Table Container */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.4 }}
          className="rounded-2xl border border-border bg-surface shadow-card overflow-hidden max-w-4xl mx-auto"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[620px]">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th scope="col" className="py-4 px-6 text-sm font-semibold text-foreground w-[34%]">
                    Feature
                  </th>
                  <th scope="col" className="py-4 px-5 text-sm font-medium text-muted-foreground w-[22%]">
                    Search Engines
                  </th>
                  <th scope="col" className="py-4 px-5 text-sm font-medium text-muted-foreground w-[22%]">
                    AI Chatbots
                  </th>
                  <th
                    scope="col"
                    className="py-4 px-6 text-sm font-bold text-primary bg-primary/5 dark:bg-primary/10 border-l border-primary/20 w-[22%]"
                  >
                    <div className="flex items-center gap-1.5">
                      <Compass className="h-4 w-4" />
                      <span>WebScout</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-sm">
                {COMPARISON_DATA.map((row) => (
                  <tr key={row.feature} className="hover:bg-muted/20 transition-colors">
                    <td className="py-4 px-6 font-medium text-foreground">
                      {row.feature}
                    </td>
                    <td className="py-4 px-5 text-muted-foreground">
                      <span className="inline-flex items-center gap-1.5">
                        {row.searchEngines === "Manual" ? (
                          <span className="text-xs text-muted-foreground font-mono">Manual</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">{row.searchEngines}</span>
                        )}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-muted-foreground">
                      <span className="inline-flex items-center gap-1.5">
                        {row.chatbots === "Yes" ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-foreground">
                            <Check className="h-3.5 w-3.5 text-muted-foreground" />
                            Yes
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">{row.chatbots}</span>
                        )}
                      </span>
                    </td>
                    <td className="py-4 px-6 bg-primary/5 dark:bg-primary/10 border-l border-primary/20">
                      <span className="inline-flex items-center gap-1.5 text-primary font-semibold text-sm">
                        <Check className="h-4 w-4 stroke-[2.5]" />
                        {row.webscout}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer Insight Banner */}
          <div className="p-4 bg-muted/30 border-t border-border flex items-center justify-between text-xs text-muted-foreground px-6">
            <span>Verified Hackathon Architecture Specification • Track 2</span>
            <span className="font-medium text-foreground">Continuous Source Traceability</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
