"use client";

import * as React from "react";
import { Plus, Trash2, Globe, AlertCircle, X, CheckCircle2 } from "lucide-react";
import { UrlItem } from "@/lib/types";
import { validateUrlEntry, normalizeUrl } from "@/lib/validation";

interface UrlListInputProps {
  items: UrlItem[];
  onChange: (updatedItems: UrlItem[]) => void;
}

export function UrlListInput({ items, onChange }: UrlListInputProps) {
  const maxUrls = 5;
  const canAddMore = items.length < maxUrls;
  const validCount = items.filter((item) => item.isValid).length;

  const handleUrlChange = (id: string, rawVal: string) => {
    // Other items normalized URLs for duplicate check
    const otherNormalized = items
      .filter((i) => i.id !== id && i.value.trim().length > 0)
      .map((i) => (i.normalized ? i.normalized : normalizeUrl(i.value)));

    const validation = validateUrlEntry(rawVal, otherNormalized);

    const updated = items.map((item) => {
      if (item.id === id) {
        return {
          ...item,
          value: rawVal,
          normalized: validation.normalized,
          hostname: validation.hostname,
          isValid: validation.isValid,
          error: rawVal.trim().length > 0 ? validation.error : undefined,
          touched: true,
        };
      }
      return item;
    });

    onChange(updated);
  };

  const handleBlur = (id: string) => {
    const target = items.find((i) => i.id === id);
    if (!target || !target.value.trim()) return;

    // Auto-prepend https:// if missing on blur to enhance user experience
    const rawVal = target.value.trim();
    const normalizedVal = normalizeUrl(rawVal);
    if (normalizedVal !== rawVal && !rawVal.includes("://")) {
      handleUrlChange(id, normalizedVal);
    }
  };

  const handleAddUrl = () => {
    if (!canAddMore) return;
    const newItem: UrlItem = {
      id: `url-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      value: "",
      normalized: "",
      hostname: "",
      isValid: false,
    };
    onChange([...items, newItem]);
  };

  const handleRemoveUrl = (id: string) => {
    if (items.length <= 1) return;
    const remaining = items.filter((i) => i.id !== id);

    // Re-validate remaining items to clear any resolved duplicate errors
    const revalidated = remaining.map((item, idx) => {
      if (!item.value.trim()) return item;
      const otherNormalized = remaining
        .filter((_, otherIdx) => otherIdx !== idx && remaining[otherIdx].value.trim().length > 0)
        .map((i) => i.normalized || normalizeUrl(i.value));

      const validation = validateUrlEntry(item.value, otherNormalized);
      return {
        ...item,
        normalized: validation.normalized,
        hostname: validation.hostname,
        isValid: validation.isValid,
        error: validation.error,
      };
    });

    onChange(revalidated);
  };

  const handleClearUrl = (id: string) => {
    handleUrlChange(id, "");
  };

  return (
    <div className="space-y-4">
      {/* Header & Source Counter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground tracking-tight">
            Where should we look?
          </h3>
          <p className="text-xs text-muted-foreground">
            Add the websites you want WebScout to research.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className="text-xs font-mono px-2.5 py-1 rounded-full bg-muted text-muted-foreground border border-border"
            aria-live="polite"
          >
            {validCount} of {maxUrls} sources valid
          </span>
        </div>
      </div>

      {/* URL Inputs List */}
      <div className="space-y-3">
        {items.map((item, index) => {
          const hasError = item.touched && item.value.trim().length > 0 && !item.isValid;
          const isSuccess = item.isValid && item.value.trim().length > 0;

          return (
            <div key={item.id} className="space-y-1.5">
              <div className="flex items-center gap-2">
                {/* Input Container */}
                <div className="relative flex-1 group">
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
                    <Globe className="h-4 w-4" />
                  </div>

                  <input
                    type="text"
                    value={item.value}
                    onChange={(e) => handleUrlChange(item.id, e.target.value)}
                    onBlur={() => handleBlur(item.id)}
                    placeholder="e.g. amazon.in or https://www.flipkart.com"
                    aria-label={`Website URL source ${index + 1}`}
                    className={`w-full rounded-xl border bg-surface pl-10 pr-20 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background shadow-subtle ${
                      hasError
                        ? "border-red-400 focus-visible:ring-red-400"
                        : isSuccess
                        ? "border-primary/50 focus-visible:ring-primary"
                        : "border-border hover:border-border/80 focus-visible:ring-primary"
                    }`}
                  />

                  {/* Actions inside input: Clear button & Hostname badge */}
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
                    {item.hostname && isSuccess && (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                        <CheckCircle2 className="h-3 w-3" />
                        {item.hostname}
                      </span>
                    )}

                    {item.value.length > 0 && (
                      <button
                        type="button"
                        onClick={() => handleClearUrl(item.id)}
                        aria-label={`Clear URL field ${index + 1}`}
                        className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Remove button */}
                <button
                  type="button"
                  onClick={() => handleRemoveUrl(item.id)}
                  disabled={items.length <= 1}
                  aria-label={`Remove source ${index + 1}`}
                  className={`flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-surface transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    items.length <= 1
                      ? "opacity-30 cursor-not-allowed text-muted-foreground"
                      : "text-muted-foreground hover:text-red-500 hover:border-red-300 dark:hover:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-950/20"
                  }`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Inline Error Message */}
              {hasError && (
                <div
                  role="alert"
                  aria-live="assertive"
                  className="flex items-center gap-1.5 text-xs text-red-500 font-medium pl-2"
                >
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{item.error}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add Website Button */}
      <div className="pt-1 flex items-center justify-between">
        <button
          type="button"
          onClick={handleAddUrl}
          disabled={!canAddMore}
          aria-label="Add another website URL"
          className={`inline-flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-xl border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
            canAddMore
              ? "border-dashed border-border bg-surface text-primary hover:bg-surface-hover hover:border-primary/50"
              : "border-border bg-muted text-muted-foreground opacity-50 cursor-not-allowed"
          }`}
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Add website ({items.length}/5)</span>
        </button>

        <span className="text-[11px] text-muted-foreground">
          Supports paste • HTTP &amp; HTTPS
        </span>
      </div>
    </div>
  );
}
