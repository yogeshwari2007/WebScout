"use client";

import * as React from "react";
import { Laptop, Headphones, Smartphone, Cloud, ArrowUpRight } from "lucide-react";
import { ExampleIdea } from "@/lib/types";

export const EXAMPLES: ExampleIdea[] = [
  {
    id: "laptops",
    title: "Best laptops for coding",
    query:
      "Find the best laptop under ₹70,000 for programming, with at least 16GB RAM, good battery life and a reliable processor.",
    urls: [
      "https://www.amazon.in",
      "https://www.flipkart.com",
      "https://www.croma.com",
    ],
    tip: "When comparing laptops, highlight display resolution, keyboard travel, and RAM upgradeability in addition to battery runtime.",
  },
  {
    id: "headphones",
    title: "Noise-cancelling headphones",
    query:
      "Compare the best noise-cancelling headphones for students, considering sound quality, comfort, battery life and price.",
    urls: [
      "https://www.amazon.in",
      "https://www.flipkart.com",
      "https://www.reliancedigital.in",
    ],
    tip: "Audio research benefits from specifying ANC strength, weight for long study sessions, and microphone clarity for calls.",
  },
  {
    id: "smartphones",
    title: "Smartphones under ₹30,000",
    query:
      "Find the best smartphones under ₹30,000, comparing camera quality, performance, battery life and software support.",
    urls: [
      "https://www.amazon.in",
      "https://www.flipkart.com",
      "https://www.croma.com",
    ],
    tip: "In mid-range phone research, compare software update commitments (years of Android OS support) alongside hardware specs.",
  },
  {
    id: "cloud",
    title: "Cloud hosting platforms",
    query:
      "Compare cloud hosting options for a small startup based on pricing, scalability, reliability and ease of use.",
    urls: [
      "https://aws.amazon.com",
      "https://cloud.google.com",
      "https://azure.microsoft.com",
    ],
    tip: "For cloud infrastructure, evaluate free-tier credits, egress bandwidth fees, and managed database operational simplicity.",
  },
];

interface ExampleChipsProps {
  activeExampleId: string | null;
  onSelectExample: (example: ExampleIdea) => void;
}

export function ExampleChips({
  activeExampleId,
  onSelectExample,
}: ExampleChipsProps) {
  const getIcon = (id: string) => {
    switch (id) {
      case "laptops":
        return Laptop;
      case "headphones":
        return Headphones;
      case "smartphones":
        return Smartphone;
      case "cloud":
        return Cloud;
      default:
        return Laptop;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-foreground tracking-tight">
          Need a starting point?
        </h3>
        <p className="text-xs text-muted-foreground">
          Try one of these research ideas.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {EXAMPLES.map((item) => {
          const Icon = getIcon(item.id);
          const isSelected = activeExampleId === item.id;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectExample(item)}
              aria-pressed={isSelected}
              className={`group flex items-start justify-between gap-3 p-3.5 rounded-xl border text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                isSelected
                  ? "bg-primary/5 dark:bg-primary/10 border-primary text-foreground shadow-subtle ring-1 ring-primary/40"
                  : "bg-surface border-border hover:border-border/80 hover:bg-surface-hover text-muted-foreground hover:text-foreground"
              }`}
            >
              <div className="flex items-start gap-3 min-w-0">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-lg border transition-colors shrink-0 ${
                    isSelected
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-muted text-muted-foreground group-hover:text-foreground border-border"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 space-y-0.5">
                  <p
                    className={`text-xs font-semibold truncate ${
                      isSelected ? "text-primary" : "text-foreground"
                    }`}
                  >
                    {item.title}
                  </p>
                  <p className="text-[11px] text-muted-foreground line-clamp-1">
                    {item.query}
                  </p>
                </div>
              </div>

              <ArrowUpRight
                className={`h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 ${
                  isSelected ? "text-primary" : "text-muted-foreground/60"
                }`}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
