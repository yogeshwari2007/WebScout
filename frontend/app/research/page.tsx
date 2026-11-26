"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Compass } from "lucide-react";
import { QueryForm } from "@/components/research/QueryForm";
import { UrlListInput } from "@/components/research/UrlListInput";
import { ExampleChips, EXAMPLES } from "@/components/research/ExampleChips";
import { ResearchReadiness } from "@/components/research/ResearchReadiness";
import { ResearchTip } from "@/components/research/ResearchTip";
import { Button } from "@/components/ui/Button";
import { UrlItem, ExampleIdea, StoredResearchData } from "@/lib/types";
import { calculateReadiness, validateUrlEntry } from "@/lib/validation";

export default function ResearchWorkspacePage() {
  const router = useRouter();

  // Controlled Form State
  const [query, setQuery] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [urlItems, setUrlItems] = React.useState<UrlItem[]>([
    {
      id: "url-init-1",
      value: "",
      normalized: "",
      hostname: "",
      isValid: false,
    },
  ]);
  const [activeExampleId, setActiveExampleId] = React.useState<string | null>(
    null
  );
  const [activeTip, setActiveTip] = React.useState<string | undefined>(undefined);

  // Restore previous session state if returning from processing/results to edit
  React.useEffect(() => {
    try {
      const stored = sessionStorage.getItem("webscout_current_research");
      if (stored) {
        const parsed: StoredResearchData = JSON.parse(stored);
        if (parsed.query) setQuery(parsed.query);
        if (parsed.urls && parsed.urls.length > 0) {
          const items: UrlItem[] = parsed.urls.map((u, idx) => {
            const others = parsed.urls.filter((_, i) => i !== idx);
            const val = validateUrlEntry(u, others);
            return {
              id: `restored-url-${idx}-${Date.now()}`,
              value: u,
              normalized: val.normalized,
              hostname: val.hostname,
              isValid: val.isValid,
              touched: true,
            };
          });
          setUrlItems(items);
        }
      }
    } catch {
      // Ignore parse issues
    }
  }, []);

  // Derived readiness check
  const readiness = calculateReadiness(query, urlItems);

  // Handle Example Selection
  const handleSelectExample = (example: ExampleIdea) => {
    setActiveExampleId(example.id);
    setQuery(example.query);
    setActiveTip(example.tip);

    // Populate URLs from example and validate each
    const populatedItems: UrlItem[] = example.urls.map((url, idx) => {
      const otherUrls = example.urls.filter((_, i) => i !== idx);
      const validation = validateUrlEntry(url, otherUrls);

      return {
        id: `example-url-${idx}-${Date.now()}`,
        value: url,
        normalized: validation.normalized,
        hostname: validation.hostname,
        isValid: validation.isValid,
        touched: true,
      };
    });

    setUrlItems(populatedItems);

    // Smoothly scroll to the form top
    const formEl = document.getElementById("research-workspace-form");
    if (formEl) {
      formEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Clear query handler
  const handleClearQuery = () => {
    setQuery("");
    setActiveExampleId(null);
  };

  // Form submission handler
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!readiness.isReady || isSubmitting) return;

    setIsSubmitting(true);

    const validUrls = urlItems
      .filter((item) => item.isValid && item.normalized)
      .map((item) => item.normalized);

    const payload: StoredResearchData & { autoStart?: boolean } = {
      query: query.trim(),
      urls: validUrls,
      submittedAt: new Date().toISOString(),
      autoStart: true,
    };

    try {
      sessionStorage.setItem(
        "webscout_current_research",
        JSON.stringify(payload)
      );
    } catch {
      // Fallback
    }

    router.push("/research/results");
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8 space-y-12">
      {/* 1. Header & Workspace Breadcrumbs */}
      <div className="space-y-4 max-w-3xl">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <span>/</span>
          <span className="text-foreground font-medium">Research</span>
        </div>

        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-widest text-primary flex items-center gap-1.5">
            <Compass className="h-3.5 w-3.5" />
            WebScout Research Workspace
          </span>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-foreground">
            What are we researching today?
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Describe what you&apos;re looking for, add your sources, and let
            WebScout do the digging.
          </p>
        </div>
      </div>

      {/* 2. Main Workspace Layout: Form & Interactive Sidebar */}
      <form
        id="research-workspace-form"
        onSubmit={handleSubmit}
        className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start"
      >
        {/* Left Column: Query Input & Website Manager */}
        <div className="lg:col-span-8 space-y-8">
          {/* Section A: Query Form */}
          <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-6">
            <QueryForm
              query={query}
              onChange={(newQ) => {
                setQuery(newQ);
                if (activeExampleId) setActiveExampleId(null);
              }}
              onClear={handleClearQuery}
            />
          </div>

          {/* Section B: Website Sources Manager */}
          <div className="rounded-2xl border border-border bg-surface p-6 sm:p-7 shadow-card space-y-6">
            <UrlListInput
              items={urlItems}
              onChange={(updated) => {
                setUrlItems(updated);
                if (activeExampleId) setActiveExampleId(null);
              }}
            />
          </div>
        </div>

        {/* Right Column: Readiness Panel, Assistant Tip, and CTA */}
        <div className="lg:col-span-4 space-y-6 sticky top-24">
          {/* Research Readiness Card */}
          <ResearchReadiness readiness={readiness} />

          {/* Contextual Assistant Tip */}
          <ResearchTip tip={activeTip} />

          {/* Primary Action Button */}
          <div className="space-y-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={!readiness.isReady || isSubmitting}
              className="w-full shadow-card text-base py-3"
            >
              {isSubmitting ? (
                <>
                  <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin mr-1" />
                  <span>Preparing research...</span>
                </>
              ) : (
                <>
                  <span>Start researching</span>
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </Button>

            {!readiness.isReady && (
              <p className="text-[11px] text-center text-muted-foreground">
                Complete query and add valid website URLs to proceed.
              </p>
            )}
          </div>
        </div>
      </form>

      {/* 3. Example Research Suggestions */}
      <div className="pt-8 border-t border-border">
        <ExampleChips
          activeExampleId={activeExampleId}
          onSelectExample={handleSelectExample}
        />
      </div>
    </div>
  );
}
