"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Compass,
  ArrowLeft,
  Sparkles,
  Archive,
  AlertCircle,
  AlertTriangle,
  Clock,
  RotateCcw,
  CheckCircle2,
  BookmarkCheck,
  RefreshCw,
  XCircle,
  ServerOff,
} from "lucide-react";
import { ResultsHeader } from "@/components/research/ResultsHeader";
import { ProgressStepper, DEFAULT_STAGES } from "@/components/research/ProgressStepper";
import { SourceStatusList } from "@/components/research/SourceStatusList";
import { ResearchActivity } from "@/components/research/ResearchActivity";
import {
  SummarySkeleton,
  ComparisonTableSkeleton,
  RecommendationSkeleton,
} from "@/components/research/ResearchSkeletons";
import { DemoSimulationToolbar } from "@/components/research/DemoSimulationToolbar";
import { ResultsActions } from "@/components/research/ResultsActions";
import { ExecutiveSummary } from "@/components/research/ExecutiveSummary";
import { ComparisonMatrix } from "@/components/research/ComparisonMatrix";
import { RecommendationCard } from "@/components/research/RecommendationCard";
import { SourceDossierList } from "@/components/research/SourceDossierList";
import { Button } from "@/components/ui/Button";
import {
  StoredResearchData,
  StageId,
  StageInfo,
  SourceStatusItem,
  ErrorScenarioType,
  HistoryEntry,
  ResearchResult,
} from "@/lib/types";
import { extractHostname } from "@/lib/validation";
import { getHistoryEntry, saveHistoryEntry } from "@/lib/storage";
import { SAMPLE_RESEARCH_RESULT } from "@/lib/sampleData";
import { research as executeResearchApi, ApiError } from "@/lib/api";

function ResearchResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get("historyId");
  const isSampleQuery = searchParams.get("sample") === "true";

  // Reopened Saved History State
  const [historyEntry, setHistoryEntry] = React.useState<HistoryEntry | null>(null);
  const [historyNotFound, setHistoryNotFound] = React.useState(false);

  // Live Session Data (from sessionStorage)
  const [data, setData] = React.useState<StoredResearchData | null>(null);
  const [loaded, setLoaded] = React.useState(false);

  // Primary Lifecycle View State: 'loading' | 'completed' | 'error'
  const [viewState, setViewState] = React.useState<"loading" | "completed" | "error">(
    "loading"
  );
  const [activeResult, setActiveResult] = React.useState<ResearchResult | null>(null);
  const [isSavedToHistory, setIsSavedToHistory] = React.useState(false);

  // Error State
  const [errorTitle, setErrorTitle] = React.useState<string | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [isNetworkError, setIsNetworkError] = React.useState(false);

  // Live Timer for honest request duration
  const [elapsedSeconds, setElapsedSeconds] = React.useState(0);

  // Progress Stepper & Source Statuses
  const [stages, setStages] = React.useState<StageInfo[]>(DEFAULT_STAGES);
  const [sources, setSources] = React.useState<SourceStatusItem[]>([]);

  // Simulation controls (optional developer preview)
  const [isSimulating, setIsSimulating] = React.useState(false);
  const [showSkeletonPreview, setShowSkeletonPreview] = React.useState(false);

  // Request cancellation & in-flight tracking
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const hasInitiatedRef = React.useRef(false);

  // Real API research execution handler
  const startRealResearch = React.useCallback(
    async (queryStr: string, urlList: string[]) => {
      setViewState("loading");
      setErrorTitle(null);
      setErrorMessage(null);
      setIsNetworkError(false);
      setElapsedSeconds(0);
      setIsSavedToHistory(false);

      // Initialize source list with queued/fetching states
      setSources(
        urlList.map((url) => ({
          url,
          hostname: extractHostname(url),
          status: "fetching",
          message: "Navigating and extracting content with Playwright...",
        }))
      );

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const result = await executeResearchApi(queryStr, urlList, {
          signal: controller.signal,
          timeoutMs: 90000,
        });

        // Check if all sources failed
        const allFailed =
          result.sources.length > 0 &&
          result.sources.every((s) => s.status === "failed");

        if (allFailed) {
          setViewState("error");
          setErrorTitle("All Target Websites Failed");
          setErrorMessage(
            result.summary ||
              "None of the target websites returned readable content. They may have encountered network timeouts, paywalls, or bot verification."
          );
          return;
        }

        // Successfully received research result
        setActiveResult(result);
        setViewState("completed");

        // Automatically save successful real research to local history exactly once
        saveHistoryEntry({
          query: result.query,
          result,
          isSample: false,
        });
        setIsSavedToHistory(true);
      } catch (err: any) {
        if (err.name === "AbortError" || err.statusCode === 499) {
          // Request was cancelled by the user
          return;
        }

        setViewState("error");
        if (err instanceof ApiError) {
          setErrorTitle(
            err.isNetworkError
              ? "Backend Server Unreachable"
              : err.statusCode === 408
              ? "Research Request Timed Out"
              : err.statusCode === 422
              ? "Validation Error"
              : "Research Request Failed"
          );
          setErrorMessage(err.message);
          setIsNetworkError(err.isNetworkError);
        } else {
          setErrorTitle("Unexpected Error");
          setErrorMessage(
            err.message || "An unexpected error occurred while conducting research."
          );
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    []
  );

  // Load session or history on mount
  React.useEffect(() => {
    // 1. Reopening from saved history
    if (historyId) {
      const entry = getHistoryEntry(historyId);
      if (entry) {
        setHistoryEntry(entry);
        setActiveResult(entry.result);
        setViewState("completed");
        setIsSavedToHistory(true);
      } else {
        setHistoryNotFound(true);
      }
      setLoaded(true);
      return;
    }

    // 2. Direct sample preview mode
    if (isSampleQuery) {
      setActiveResult(SAMPLE_RESEARCH_RESULT);
      setViewState("completed");
      setLoaded(true);
      return;
    }

    // 3. Live session from /research form
    try {
      const stored = sessionStorage.getItem("webscout_current_research");
      if (stored) {
        const parsed: StoredResearchData = JSON.parse(stored);
        setData(parsed);

        // Auto-start real backend request if not initiated yet
        if (!hasInitiatedRef.current && parsed.query && parsed.urls?.length > 0) {
          hasInitiatedRef.current = true;
          startRealResearch(parsed.query, parsed.urls);
        }
      }
    } catch {
      // Storage error
    } finally {
      setLoaded(true);
    }

    // Clean up in-flight requests when component unmounts
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [historyId, isSampleQuery, startRealResearch]);

  // Elapsed seconds timer during honest loading
  React.useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (viewState === "loading") {
      timer = setInterval(() => {
        setElapsedSeconds((sec) => sec + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [viewState]);

  // Return to edit query
  const handleEdit = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    router.push("/research");
  };

  // Retry research request with original parameters
  const handleRetry = () => {
    if (data && data.query && data.urls) {
      startRealResearch(data.query, data.urls);
    }
  };

  // Handle explicit manual save for sample previews
  const handleSaveToHistory = () => {
    if (!activeResult) return;
    saveHistoryEntry({
      query: activeResult.query,
      result: activeResult,
      isSample: Boolean(historyEntry?.isSample || isSampleQuery || !data),
    });
    setIsSavedToHistory(true);
  };

  // -------------------------------------------------------------
  // SIMULATION CONTROLS (For Developer Demo Toolbar)
  // -------------------------------------------------------------
  const handleToggleSimulation = (active: boolean) => {
    setIsSimulating(active);
    if (!active && data) {
      setStages(DEFAULT_STAGES);
      setSources(
        data.urls.map((url, idx) => ({
          url,
          hostname: extractHostname(url),
          status: idx === 0 ? "fetching" : "waiting",
        }))
      );
    }
  };

  const handleSetStage = (targetStageId: StageId) => {
    const stageOrder: StageId[] = [
      "navigating",
      "extracting",
      "analysing",
      "compiling",
    ];
    const targetIdx = stageOrder.indexOf(targetStageId);

    const updated = stages.map((s, idx) => {
      if (idx < targetIdx) {
        return { ...s, status: "completed" as const };
      } else if (idx === targetIdx) {
        return { ...s, status: "active" as const };
      } else {
        return { ...s, status: "pending" as const };
      }
    });

    setStages(updated);
  };

  const handleSetSourceStatus = (
    preset: "all_fetching" | "all_success" | "partial_fail" | "timeout"
  ) => {
    if (!data) return;

    let updated: SourceStatusItem[] = [];
    if (preset === "all_fetching") {
      updated = data.urls.map((url) => ({
        url,
        hostname: extractHostname(url),
        status: "fetching",
        message: "Active browser navigation",
      }));
    } else if (preset === "all_success") {
      updated = data.urls.map((url) => ({
        url,
        hostname: extractHostname(url),
        status: "success",
        message: "Clean semantic content extracted",
      }));
    } else if (preset === "partial_fail") {
      updated = data.urls.map((url, idx) => ({
        url,
        hostname: extractHostname(url),
        status: idx === 0 ? "failed" : "success",
        error: idx === 0 ? "HTTP 403 Forbidden (Blocked by destination)" : undefined,
      }));
    } else if (preset === "timeout") {
      updated = data.urls.map((url, idx) => ({
        url,
        hostname: extractHostname(url),
        status: idx === 1 ? "timeout" : "success",
        error: idx === 1 ? "Navigation timed out after 25 seconds" : undefined,
      }));
    }
    setSources(updated);
  };

  const handleRunDemoSequence = () => {
    handleSetStage("navigating");
    handleSetSourceStatus("all_fetching");

    setTimeout(() => {
      handleSetStage("extracting");
    }, 1200);

    setTimeout(() => {
      handleSetStage("analysing");
      handleSetSourceStatus("all_success");
    }, 2400);

    setTimeout(() => {
      handleSetStage("compiling");
      const synthesized: ResearchResult = data
        ? {
            ...SAMPLE_RESEARCH_RESULT,
            query: data.query,
            sources: data.urls.map((u) => ({
              url: u,
              hostname: extractHostname(u),
              status: "success",
            })),
          }
        : SAMPLE_RESEARCH_RESULT;

      setActiveResult(synthesized);
      setViewState("completed");
    }, 3600);
  };

  const handleReset = () => {
    setStages(DEFAULT_STAGES);
    setShowSkeletonPreview(false);
    if (data) {
      startRealResearch(data.query, data.urls);
    }
  };

  // -------------------------------------------------------------
  // 1. NOT FOUND STATE FOR INVALID HISTORY ID
  // -------------------------------------------------------------
  if (loaded && historyNotFound) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8 text-center space-y-6">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-500 border border-rose-500/20">
          <AlertCircle className="h-8 w-8" />
        </div>
        <div className="space-y-2 max-w-md mx-auto">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Research Session Not Found
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            The requested research dossier could not be found in your local browser
            history. It may have been cleared or the link is invalid.
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link href="/history">
            <Button variant="secondary" size="md">
              <Archive className="h-4 w-4" />
              <span>Back to History</span>
            </Button>
          </Link>
          <Link href="/research">
            <Button variant="primary" size="md">
              <Compass className="h-4 w-4" />
              <span>Start New Research</span>
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 2. EMPTY STATE (Direct access without session or query)
  // -------------------------------------------------------------
  if (loaded && !historyEntry && !data && !activeResult && viewState !== "loading") {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8 text-center space-y-6">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
          <Compass className="h-8 w-8" />
        </div>
        <div className="space-y-2 max-w-md mx-auto">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            No Active Research Session
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Formulate a research question and add your target websites to start an
            automated research session, or view our interactive demo report.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/research">
            <Button variant="primary" size="md">
              <ArrowLeft className="h-4 w-4" />
              <span>Go to Research Setup</span>
            </Button>
          </Link>
          <Button
            variant="secondary"
            size="md"
            onClick={() => {
              setActiveResult(SAMPLE_RESEARCH_RESULT);
              setViewState("completed");
            }}
          >
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Preview Sample Results</span>
          </Button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 3. ERROR STATE (Backend failure, timeout, or all sources failed)
  // -------------------------------------------------------------
  if (viewState === "error") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8 space-y-8 animate-in fade-in-0 duration-300">
        <div className="rounded-2xl border border-rose-500/30 bg-surface p-7 sm:p-9 shadow-card space-y-6">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-2xl bg-rose-500/10 text-rose-500 flex items-center justify-center shrink-0 border border-rose-500/20">
              {isNetworkError ? (
                <ServerOff className="h-6 w-6" />
              ) : (
                <XCircle className="h-6 w-6" />
              )}
            </div>
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-rose-500">
                Research Interrupted
              </span>
              <h2 className="text-xl sm:text-2xl font-bold text-foreground">
                {errorTitle || "Research Execution Failed"}
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {errorMessage ||
                  "An error prevented the research request from completing successfully."}
              </p>
            </div>
          </div>

          {/* Submitted Query Reference */}
          {data && (
            <div className="p-4 rounded-xl bg-surface-hover/50 border border-border space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase">
                Attempted Query:
              </span>
              <p className="text-xs sm:text-sm font-medium text-foreground">
                &ldquo;{data.query}&rdquo;
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-2 border-t border-border flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleEdit}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-foreground transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Edit Query &amp; URLs</span>
            </button>

            {data && (
              <Button
                type="button"
                variant="primary"
                size="md"
                onClick={handleRetry}
              >
                <RefreshCw className="h-4 w-4" />
                <span>Retry Research</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 4. HONEST INDETERMINATE LOADING VIEW (Active API Request)
  // -------------------------------------------------------------
  if (viewState === "loading") {
    const hostnames = data ? data.urls.map(extractHostname) : [];

    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8 space-y-10 animate-in fade-in-0 duration-300">
        {/* Research Header */}
        {data && (
          <ResultsHeader
            query={data.query}
            sourceCount={data.urls.length}
            hostnames={hostnames}
            title="WebScout is exploring the web."
            description="Visiting target websites concurrently using Playwright, extracting structured content, and synthesizing intelligence."
            statusLabel="RESEARCH IN PROGRESS"
            badge={
              <span className="text-[11px] font-mono uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                ACTIVE ENGINE • {elapsedSeconds}s
              </span>
            }
            onEdit={handleEdit}
          />
        )}

        {/* Live Status Card with Honest Indeterminate Indicator */}
        <div className="rounded-2xl border border-primary/30 bg-primary/5 p-6 sm:p-7 shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-primary/15 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-primary text-white flex items-center justify-center shadow-xs">
                <Compass className="h-5 w-5 animate-spin" />
              </div>
              <div className="space-y-0.5">
                <h3 className="text-sm sm:text-base font-bold text-foreground">
                  Asynchronous Research Engine Active
                </h3>
                <p className="text-xs text-muted-foreground">
                  Running concurrent Playwright browser sessions and anti-SSRF guards
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-lg border border-primary/20">
                Elapsed: {elapsedSeconds}s
              </span>
              <button
                type="button"
                onClick={handleEdit}
                className="text-xs font-medium text-muted-foreground hover:text-foreground px-2.5 py-1 rounded-lg border border-border hover:bg-surface transition-colors"
                title="Cancel the in-flight request and return to setup"
              >
                Cancel
              </button>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-foreground/85 leading-relaxed">
            WebScout is visiting {data?.urls.length || 0} candidate website
            {data?.urls.length === 1 ? "" : "s"} concurrently. The backend strips
            ads, navigations, and tracker code, caps text at 12,000 characters, and
            passes verified DOM extracts to the synthesis pipeline.
          </p>

          {elapsedSeconds > 15 && (
            <div className="pt-2 text-xs text-muted-foreground flex items-center gap-1.5 animate-in fade-in-0 duration-300">
              <Clock className="h-3.5 w-3.5 text-primary shrink-0" />
              <span>
                Extracting large dynamic pages and compiling insights... almost ready.
              </span>
            </div>
          )}
        </div>

        {/* Four-Stage Research Workflow Stepper (Honest Indeterminate) */}
        <ProgressStepper stages={stages} isIndeterminate={true} />

        {/* Target Sources Status List */}
        <SourceStatusList sources={sources} />

        {/* Behind the Research Activity Panel */}
        <ResearchActivity />
      </div>
    );
  }

  // -------------------------------------------------------------
  // 5. COMPLETED SYNTHESIS RESULTS VIEW
  // -------------------------------------------------------------
  if (viewState === "completed" && activeResult) {
    const formattedDate = historyEntry
      ? new Date(historyEntry.timestamp).toLocaleString("en-US", {
          dateStyle: "medium",
          timeStyle: "short",
        })
      : activeResult.createdAt
      ? new Date(activeResult.createdAt).toLocaleString("en-US", {
          dateStyle: "medium",
          timeStyle: "short",
        })
      : "Just now";

    const hostnames =
      activeResult.sources?.map((s) => s.hostname) ||
      (data ? data.urls.map(extractHostname) : []);

    const failedSources = activeResult.sources.filter(
      (s) => s.status === "failed"
    );
    const hasPartialFailure =
      failedSources.length > 0 &&
      failedSources.length < activeResult.sources.length;

    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8 space-y-8 animate-in fade-in-0 duration-300">
        {/* Saved Session Notification Banner */}
        {historyEntry && (
          <div className="rounded-2xl border border-primary/30 bg-primary/10 p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-xl bg-primary text-white flex items-center justify-center shadow-xs">
                <BookmarkCheck className="h-4 w-4" />
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-primary">
                    Saved Session from History
                  </span>
                  {historyEntry.isSample && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/20 px-2 py-0.5 rounded-full">
                      Sample
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>Archived on {formattedDate}</span>
                </p>
              </div>
            </div>

            <Link href="/history">
              <Button variant="secondary" size="sm">
                <Archive className="h-3.5 w-3.5" />
                <span>All History</span>
              </Button>
            </Link>
          </div>
        )}

        {/* Partial Failure Warning Banner */}
        {hasPartialFailure && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 sm:p-5 flex items-start gap-3 shadow-xs animate-in fade-in-0 duration-200">
            <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-foreground">
                Partial Research Synthesis
              </h4>
              <p className="text-xs sm:text-sm text-foreground/85 leading-relaxed">
                {failedSources.length} of {activeResult.sources.length} target
                websites could not be accessed (e.g. timeout or bot protection).
                Findings below are synthesized strictly from the{" "}
                {activeResult.sources.length - failedSources.length} accessible
                sources.
              </p>
            </div>
          </div>
        )}

        {/* Demo Mode / Mock Engine Transparency Banner */}
        {activeResult.summary.includes("[DEMO / MOCK ANALYSIS]") && (
          <div className="rounded-2xl border border-primary/40 bg-primary/10 p-4 sm:p-5 flex items-start gap-3 shadow-xs animate-in fade-in-0 duration-200">
            <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">
                  Predictable Demo Mode Active
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary/20 text-primary font-bold">
                  MOCK ANALYZER
                </span>
              </div>
              <p className="text-xs sm:text-sm text-foreground/85 leading-relaxed">
                This research session was evaluated using the Hackathon Demo Engine. Websites were fetched and cleaned via Playwright, and comparative findings are structured for presentation reliability. Configure <code className="text-primary font-mono text-[11px]">GEMINI_API_KEY</code> and <code className="text-primary font-mono text-[11px]">ANALYZER=gemini</code> in the backend for live Gemini AI reasoning.
              </p>
            </div>
          </div>
        )}

        {/* Results Header with Export Controls */}
        <ResultsHeader
          query={activeResult.query}
          sourceCount={hostnames.length}
          hostnames={hostnames}
          title="Multi-Source Synthesis & Report"
          description="Authoritative comparative evaluation and AI recommendation backed by real sources."
          breadcrumbCurrent={historyEntry ? "Saved Dossier" : "Results"}
          badge={
            historyEntry ? (
              <span className="text-[11px] font-mono uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20 flex items-center gap-1.5">
                <Archive className="w-3.5 h-3.5" />
                FROM HISTORY
              </span>
            ) : isSampleQuery || !data ? (
              <span className="text-[11px] font-mono uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                SAMPLE DOSSIER
              </span>
            ) : (
              <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-500 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                SYNTHESIS COMPLETED
              </span>
            )
          }
          actions={
            <ResultsActions
              result={activeResult}
              isSaved={isSavedToHistory}
              onSave={handleSaveToHistory}
              showSaveButton={!historyEntry}
            />
          }
          onEdit={data ? handleEdit : undefined}
        />

        {/* 1. Executive Summary */}
        <ExecutiveSummary result={activeResult} />

        {/* 2. Synthesized Recommendation */}
        <RecommendationCard result={activeResult} />

        {/* 3. Dynamic Comparison Matrix & Pros/Cons */}
        <ComparisonMatrix result={activeResult} />

        {/* 4. Consulted Sources Dossier with Real Statuses */}
        <SourceDossierList sources={activeResult.sources} />

        {/* Bottom Switch / Reset if came from live session */}
        {data && (
          <div className="pt-4 border-t border-border flex items-center justify-between">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Re-run research exploration</span>
            </button>

            <Link
              href="/research"
              className="text-xs font-semibold text-primary hover:text-primary-hover"
            >
              Start New Research Query &rarr;
            </Link>
          </div>
        )}
      </div>
    );
  }

  return null;
}

export default function ResearchProcessingPage() {
  return (
    <React.Suspense
      fallback={
        <div className="mx-auto max-w-5xl px-4 py-20 text-center space-y-4">
          <div className="h-8 w-8 mx-auto rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-muted-foreground font-mono">
            Loading research workspace...
          </p>
        </div>
      }
    >
      <ResearchResultsContent />
    </React.Suspense>
  );
}
