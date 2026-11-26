"use client";

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { FileSearch, Compass, Filter, GitCompare } from "lucide-react";

interface Step {
  number: string;
  title: string;
  subtitle: string;
  description: string;
  icon: React.ElementType;
}

const STEPS: Step[] = [
  {
    number: "01",
    title: "INPUT",
    subtitle: "Define Research",
    description: "User enters a natural-language research query and the URLs they want analysed.",
    icon: FileSearch,
  },
  {
    number: "02",
    title: "NAVIGATE",
    subtitle: "Automated Browsing",
    description: "WebScout automatically visits the provided websites using browser automation.",
    icon: Compass,
  },
  {
    number: "03",
    title: "EXTRACT",
    subtitle: "Semantic Cleaning",
    description: "Relevant information is extracted and cleaned from each website.",
    icon: Filter,
  },
  {
    number: "04",
    title: "COMPARE",
    subtitle: "Structured Synthesis",
    description: "AI analyses the collected information and generates structured comparisons and recommendations with source links.",
    icon: GitCompare,
  },
];

export function HowItWorks() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="how-it-works" className="py-20 sm:py-28 border-t border-border bg-background transition-colors scroll-mt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16 sm:mb-20">
          <span className="text-xs font-bold uppercase tracking-widest text-primary">
            Workflow Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
            From scattered tabs to clear answers.
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            WebScout turns a time-consuming research process into four simple steps.
          </p>
        </div>

        {/* Connected 4-Step Grid */}
        <div className="relative">
          {/* Connecting Line across desktop steps */}
          <div
            className="hidden lg:block absolute top-12 left-12 right-12 h-[2px] bg-border -z-0"
            aria-hidden="true"
          >
            <div className="h-full bg-gradient-to-r from-primary/30 via-primary to-primary/30 w-full" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 relative z-10">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-40px" }}
                  transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : index * 0.1 }}
                  className="flex flex-col bg-surface border border-border rounded-2xl p-6 sm:p-7 shadow-card hover:border-primary/40 transition-all duration-200"
                >
                  {/* Step Header with Icon & Number */}
                  <div className="flex items-center justify-between mb-5">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-subtle">
                      <Icon className="h-6 w-6" />
                    </div>
                    <span className="text-2xl font-extrabold tracking-tight text-muted-foreground/40 font-mono">
                      {step.number}
                    </span>
                  </div>

                  {/* Title & Subtitle */}
                  <div className="space-y-1 mb-2.5">
                    <span className="text-xs font-bold tracking-wider uppercase text-primary">
                      {step.title}
                    </span>
                    <h3 className="text-lg font-semibold text-foreground">
                      {step.subtitle}
                    </h3>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
