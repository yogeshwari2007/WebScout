"use client";

import * as React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Compass } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function FinalCTA() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section className="py-20 sm:py-28 border-t border-border bg-background transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, scale: shouldReduceMotion ? 1 : 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.45 }}
          className="relative overflow-hidden rounded-3xl border border-border bg-surface p-8 sm:p-14 lg:p-16 shadow-card text-center max-w-4xl mx-auto"
        >
          {/* Subtle Accent Glow Backdrop */}
          <div
            className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/15 rounded-full blur-3xl pointer-events-none -z-0"
            aria-hidden="true"
          />

          <div className="relative z-10 flex flex-col items-center max-w-2xl mx-auto space-y-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-subtle">
              <Compass className="h-6 w-6" />
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
              Less browsing. More knowing.
            </h2>

            <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
              Let WebScout handle the research while you focus on making the decision.
            </p>

            <div className="pt-2">
              <Link href="/research">
                <Button variant="primary" size="lg" className="shadow-card text-base px-8 py-3">
                  Explore WebScout
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
