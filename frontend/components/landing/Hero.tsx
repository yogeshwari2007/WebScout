"use client";

import * as React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, ArrowDown, Compass, CheckCircle2, Globe, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function Hero() {
  const shouldReduceMotion = useReducedMotion();

  const fadeIn = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
  };

  return (
    <section className="relative overflow-hidden pt-12 pb-20 sm:pt-16 sm:pb-28 lg:pt-20 lg:pb-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto space-y-6">
          {/* Badge */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeIn}
            className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 shadow-subtle"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Autonomous Multi-Website Intelligence</span>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            initial="hidden"
            animate="visible"
            variants={fadeIn}
            transition={{ delay: 0.08 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-foreground leading-[1.12]"
          >
            The web is vast.{" "}
            <span className="text-primary block sm:inline">
              Research shouldn&apos;t be.
            </span>
          </motion.h1>

          {/* Supporting Description */}
          <motion.p
            initial="hidden"
            animate="visible"
            variants={fadeIn}
            transition={{ delay: 0.16 }}
            className="text-base sm:text-lg lg:text-xl text-muted-foreground leading-relaxed max-w-2xl"
          >
            Compare multiple websites, extract what matters, and get AI-powered
            recommendations backed by real sources. All in one place.
          </motion.p>

          {/* Action CTAs */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeIn}
            transition={{ delay: 0.24 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3.5 w-full sm:w-auto pt-2"
          >
            <Link href="/research" className="w-full sm:w-auto">
              <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-card">
                Start researching
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#how-it-works" className="w-full sm:w-auto">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                See how it works
                <ArrowDown className="h-4 w-4" />
              </Button>
            </a>
          </motion.div>
        </div>

        {/* Realistic Miniature Research Dashboard Preview */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          transition={{ delay: 0.32 }}
          className="mt-14 sm:mt-18 max-w-4xl mx-auto"
        >
          <div className="rounded-2xl border border-border bg-surface shadow-card overflow-hidden">
            {/* Window Top Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/40">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
                <div className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/80" />
                <span className="ml-2 text-xs font-mono text-muted-foreground flex items-center gap-1.5">
                  <Compass className="h-3.5 w-3.5 text-primary" />
                  webscout.session/0491
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" />
                  Synthesis Verified
                </span>
              </div>
            </div>

            {/* Dashboard Content */}
            <div className="p-5 sm:p-7 space-y-5">
              {/* Query Indicator */}
              <div className="p-3.5 rounded-xl border border-border bg-background flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                <div className="space-y-0.5">
                  <span className="text-[11px] uppercase font-bold tracking-wider text-muted-foreground">
                    Research Objective
                  </span>
                  <p className="text-sm font-semibold text-foreground">
                    &ldquo;Compare high-performance student ultrabooks on battery runtime, compile speed, and durability.&rdquo;
                  </p>
                </div>
                <span className="self-start sm:self-auto text-xs font-medium px-2.5 py-1 rounded-lg bg-primary/10 text-primary border border-primary/20 shrink-0">
                  3 Sources Active
                </span>
              </div>

              {/* Source Indicators */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                      <Globe className="h-3 w-3 text-primary" />
                      apple.com
                    </span>
                    <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                      Extracted
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-foreground truncate">
                    MacBook Air (M3)
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    18 hr runtime • 1.24 kg
                  </p>
                </div>

                <div className="p-3 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                      <Globe className="h-3 w-3 text-primary" />
                      dell.com
                    </span>
                    <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                      Extracted
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-foreground truncate">
                    Dell XPS 13 Plus
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    13 hr runtime • 1.26 kg
                  </p>
                </div>

                <div className="p-3 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                      <Globe className="h-3 w-3 text-primary" />
                      lenovo.com
                    </span>
                    <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                      Extracted
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-foreground truncate">
                    ThinkPad T14s Gen 5
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    15 hr runtime • 1.28 kg
                  </p>
                </div>
              </div>

              {/* Miniature Comparison Matrix Preview */}
              <div className="rounded-xl border border-border overflow-hidden text-xs">
                <div className="grid grid-cols-4 bg-muted/60 p-2.5 font-semibold text-muted-foreground border-b border-border">
                  <div>Criteria</div>
                  <div>MacBook Air</div>
                  <div>Dell XPS 13</div>
                  <div>ThinkPad T14s</div>
                </div>
                <div className="grid grid-cols-4 p-2.5 border-b border-border/60 bg-surface">
                  <div className="font-medium text-foreground">Battery Life</div>
                  <div className="text-emerald-600 dark:text-emerald-400 font-semibold">18 Hours (Class-Lead)</div>
                  <div className="text-muted-foreground">13 Hours</div>
                  <div className="text-muted-foreground">15 Hours</div>
                </div>
                <div className="grid grid-cols-4 p-2.5 bg-surface">
                  <div className="font-medium text-foreground">Linux Support</div>
                  <div className="text-muted-foreground">Asahi (Experimental)</div>
                  <div className="text-emerald-600 dark:text-emerald-400">Certified Developer</div>
                  <div className="text-emerald-600 dark:text-emerald-400 font-semibold">Official Tier-1</div>
                </div>
              </div>

              {/* Recommendation Indicator */}
              <div className="p-3 rounded-xl border border-primary/30 bg-primary/5 flex items-start gap-2.5">
                <div className="p-1 rounded-md bg-primary text-primary-foreground shrink-0 mt-0.5">
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
                <div className="text-xs leading-relaxed">
                  <span className="font-semibold text-foreground">AI Verdict: </span>
                  <span className="text-muted-foreground">
                    MacBook Air M3 delivers the best battery runtime and portability for general coursework, while ThinkPad T14s is recommended for modular Linux engineering workloads.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
