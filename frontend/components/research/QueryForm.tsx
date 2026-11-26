"use client";

import * as React from "react";
import { X, Sparkles, AlertCircle } from "lucide-react";
import { validateQuery } from "@/lib/validation";

interface QueryFormProps {
  query: string;
  onChange: (newQuery: string) => void;
  onClear: () => void;
}

export function QueryForm({ query, onChange, onClear }: QueryFormProps) {
  const [touched, setTouched] = React.useState(false);

  const validation = validateQuery(query);
  const isTooShort = touched && query.length > 0 && query.trim().length < 10;
  const isTooLong = query.length > 500;
  const hasError = isTooShort || isTooLong;

  return (
    <div className="space-y-3">
      {/* Label & Character Counter */}
      <div className="flex items-center justify-between">
        <label
          htmlFor="research-query-textarea"
          className="text-sm font-semibold text-foreground flex items-center gap-2"
        >
          <span>Research question</span>
          <span className="text-xs font-normal text-muted-foreground">
            (natural language)
          </span>
        </label>
        <span
          className={`text-xs font-mono transition-colors ${
            query.length > 500
              ? "text-red-500 font-bold"
              : query.length > 450
              ? "text-amber-500"
              : "text-muted-foreground"
          }`}
          aria-live="polite"
        >
          {query.length}/500
        </span>
      </div>

      {/* Textarea Wrapper */}
      <div className="relative group">
        <textarea
          id="research-query-textarea"
          rows={4}
          value={query}
          onChange={(e) => {
            if (!touched) setTouched(true);
            onChange(e.target.value);
          }}
          onBlur={() => setTouched(true)}
          placeholder="e.g. Find the best laptop under ₹70,000 for programming, with good battery life and at least 16GB RAM..."
          className={`w-full rounded-2xl border bg-surface p-4 text-sm text-foreground placeholder:text-muted-foreground/60 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background resize-none shadow-subtle ${
            hasError
              ? "border-red-400 focus-visible:ring-red-400"
              : "border-border hover:border-border/80 focus-visible:ring-primary focus-visible:border-primary"
          }`}
          aria-invalid={hasError}
          aria-describedby={hasError ? "query-error-msg" : "query-helper-msg"}
        />

        {/* Clear Button */}
        {query.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Clear research query"
            className="absolute top-3.5 right-3.5 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Error Message */}
      {hasError && (
        <div
          id="query-error-msg"
          role="alert"
          aria-live="assertive"
          className="flex items-center gap-1.5 text-xs text-red-500 font-medium"
        >
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{validation.error}</span>
        </div>
      )}

      {/* Contextual Helper */}
      <div
        id="query-helper-msg"
        className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed pt-0.5"
      >
        <Sparkles className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
        <span>
          Be specific about what matters to you. WebScout uses your requirements
          to decide what information to compare.
        </span>
      </div>
    </div>
  );
}
