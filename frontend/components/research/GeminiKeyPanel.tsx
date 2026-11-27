"use client";

import * as React from "react";
import {
  KeyRound,
  Eye,
  EyeOff,
  X,
  CheckCircle2,
  Sparkles,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { checkBackendHealth } from "@/lib/api";
import {
  clearStoredGeminiApiKey,
  getStoredGeminiApiKey,
  sanitizeGeminiApiKey,
  setStoredGeminiApiKey,
  subscribeGeminiKeyChange,
} from "@/lib/geminiKey";

interface GeminiKeyPanelProps {
  variant?: "sidebar" | "banner";
  onApplyAndRerun?: () => void;
  isRerunning?: boolean;
  fellBackToMock?: boolean;
}

export function GeminiKeyPanel({
  variant = "sidebar",
  onApplyAndRerun,
  isRerunning = false,
  fellBackToMock = false,
}: GeminiKeyPanelProps) {
  const [keyInput, setKeyInput] = React.useState("");
  const [showKey, setShowKey] = React.useState(false);
  const [serverAnalyzer, setServerAnalyzer] = React.useState<string | null>(null);
  const [showOverride, setShowOverride] = React.useState(false);

  const sanitizedKey = sanitizeGeminiApiKey(keyInput);
  const hasUserKey = Boolean(sanitizedKey);

  // Sync with sessionStorage and detect whether server already provides a Gemini key
  React.useEffect(() => {
    setKeyInput(getStoredGeminiApiKey());

    const unsubscribe = subscribeGeminiKeyChange(() => {
      const latest = getStoredGeminiApiKey();
      setKeyInput((prev) =>
        sanitizeGeminiApiKey(prev) === latest ? prev : latest
      );
    });

    let active = true;
    checkBackendHealth().then((health) => {
      if (active && health?.analyzer) {
        setServerAnalyzer(health.analyzer);
      }
    });

    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    setKeyInput(rawValue);
    setStoredGeminiApiKey(rawValue);
  };

  const handleClear = () => {
    setKeyInput("");
    setShowKey(false);
    clearStoredGeminiApiKey();
  };

  const handlePreventFormEnter = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (variant === "banner" && hasUserKey && onApplyAndRerun && !isRerunning) {
        onApplyAndRerun();
      }
    }
  };

  const renderMaskedInput = (id: string) => (
    <div className="relative flex-1">
      <input
        id={id}
        type={showKey ? "text" : "password"}
        value={keyInput}
        onChange={handleChange}
        onKeyDown={handlePreventFormEnter}
        placeholder="Paste Gemini API key (AIza...)"
        autoComplete="off"
        spellCheck={false}
        aria-label="Gemini API key"
        className={`w-full rounded-xl border bg-background pl-3 pr-16 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/60 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-offset-background shadow-subtle ${
          hasUserKey
            ? "border-emerald-500/40 focus-visible:ring-emerald-500"
            : "border-border hover:border-border/80 focus-visible:ring-primary"
        }`}
      />
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
        <button
          type="button"
          onClick={() => setShowKey((prev) => !prev)}
          aria-label={showKey ? "Hide Gemini API key" : "Show Gemini API key"}
          title={showKey ? "Hide key" : "Show key"}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          {showKey ? (
            <EyeOff className="h-3.5 w-3.5" />
          ) : (
            <Eye className="h-3.5 w-3.5" />
          )}
        </button>

        {keyInput.length > 0 && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Clear Gemini API key"
            title="Clear key"
            className="p-1 rounded-md text-muted-foreground hover:text-rose-500 hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );

  if (variant === "banner") {
    return (
      <div className="pt-2.5 space-y-2">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          {renderMaskedInput("results-gemini-api-key")}
          {onApplyAndRerun && (
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={!hasUserKey || isRerunning}
              onClick={onApplyAndRerun}
              className="shrink-0 h-9 px-3.5 rounded-xl"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Re-run with Gemini</span>
            </Button>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-primary shrink-0" />
            {fellBackToMock && hasUserKey
              ? "Verify your key or quota, then click Re-run with Gemini."
              : "Kept only in this browser tab session — never saved on our server."}
          </span>
          <a
            href="https://aistudio.google.com/apikey"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
          >
            <span>Get a key</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    );
  }

  const isServerActive = serverAnalyzer === "gemini";

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-3">
      <div className="flex items-center justify-between gap-2">
        <label
          htmlFor="workspace-gemini-api-key"
          className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5"
        >
          <KeyRound className="h-3.5 w-3.5 text-primary" />
          <span>Gemini AI Key</span>
        </label>

        {hasUserKey ? (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            Gemini Ready
          </span>
        ) : isServerActive ? (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            Server Active
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
            Demo Mode
          </span>
        )}
      </div>

      {isServerActive && !hasUserKey && !showOverride ? (
        <div className="space-y-2 pt-1 border-t border-border">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Live Gemini semantic analysis is enabled by the server configuration.
          </p>
          <button
            type="button"
            onClick={() => setShowOverride(true)}
            className="text-[11px] font-medium text-primary hover:underline"
          >
            Override with your own key
          </button>
        </div>
      ) : (
        <div className="space-y-2.5 pt-1 border-t border-border">
          <p className="text-xs text-muted-foreground leading-relaxed">
            {isServerActive
              ? "Optional: paste your own Gemini key to override the server default for this tab."
              : "Paste your Gemini API key below to enable real AI semantic analysis."}
          </p>

          {renderMaskedInput("workspace-gemini-api-key")}

          <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-primary shrink-0" />
              Tab-only • Never saved to server
            </span>
            <a
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline font-medium shrink-0"
            >
              <span>Get key</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
