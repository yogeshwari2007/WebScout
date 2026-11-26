"use client";

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Globe, Sparkles, Link2, Target } from "lucide-react";

interface Feature {
  title: string;
  description: string;
  icon: React.ElementType;
}

const FEATURES: Feature[] = [
  {
    title: "Automated Multi-site Browsing",
    description: "Automatically navigate multiple user-provided websites without manually switching between tabs.",
    icon: Globe,
  },
  {
    title: "Intelligent AI Analysis",
    description: "Use AI to understand the user's query and compare relevant information across extracted content.",
    icon: Sparkles,
  },
  {
    title: "Source-backed Findings",
    description: "Provide links to original websites so users can verify the information behind the results.",
    icon: Link2,
  },
  {
    title: "Personalised Recommendations",
    description: "Generate recommendations based on the user's research requirements and comparison criteria.",
    icon: Target,
  },
];

export function FeatureGrid() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section className="py-20 sm:py-28 border-t border-border bg-background transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16 sm:mb-20">
          <span className="text-xs font-bold uppercase tracking-widest text-primary">
            Core Capabilities
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
            Everything you need to research smarter.
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Purpose-built browser automation and verified evidence synthesis designed for deep comparison.
          </p>
        </div>

        {/* 4 Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 max-w-5xl mx-auto">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : index * 0.1 }}
                className="group relative rounded-2xl border border-border bg-surface p-7 sm:p-8 shadow-card hover:shadow-card-hover hover:border-primary/40 transition-all duration-200"
              >
                <div className="flex flex-col space-y-4">
                  {/* Icon */}
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-subtle transition-transform duration-200 group-hover:scale-105">
                    <Icon className="h-6 w-6" />
                  </div>

                  {/* Title & Description */}
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
