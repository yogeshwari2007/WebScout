export interface UrlItem {
  id: string;
  value: string;
  normalized: string;
  hostname: string;
  isValid: boolean;
  error?: string;
  touched?: boolean;
}

export interface ExampleIdea {
  id: string;
  title: string;
  query: string;
  urls: string[];
  tip: string;
}

export interface ReadinessState {
  hasValidQuery: boolean;
  hasAtLeastOneSource: boolean;
  allUrlsValid: boolean;
  isReady: boolean;
}

export interface StoredResearchData {
  query: string;
  urls: string[];
  submittedAt: string;
  autoStart?: boolean;
}

// Stage & Progress Stepper Definitions
export type StageId = "navigating" | "extracting" | "analysing" | "compiling";
export type StageStatus = "pending" | "active" | "completed" | "failed";

export interface StageInfo {
  id: StageId;
  number: string;
  title: string;
  description: string;
  status: StageStatus;
}

// Source Fetching Statuses
export type SourceStatusType =
  | "waiting"
  | "fetching"
  | "success"
  | "failed"
  | "timeout";

export interface SourceStatusItem {
  url: string;
  hostname: string;
  status: SourceStatusType;
  message?: string;
  error?: string;
}

// Error Scenarios
export type ErrorScenarioType =
  | "backend_unreachable"
  | "all_failed"
  | "partial_failure"
  | "analysis_failed";

export interface ResearchError {
  type: ErrorScenarioType;
  title: string;
  message: string;
  canRetry: boolean;
}

// ---------------------------------------------------------------------------
// Step 6: Core Synthesized Research Result and Storage Types
// ---------------------------------------------------------------------------

export interface ComparisonItem {
  id: string;
  name: string;
  criteriaValues: Record<string, string>;
  pros: string[];
  cons: string[];
  url?: string;
}

export interface SourceReference {
  url: string;
  hostname: string;
  status: SourceStatusType;
  title?: string;
}

export interface RecommendationLink {
  title: string;
  url: string;
}

export interface Recommendation {
  winner: string;
  reasoning: string;
  keyStrengths?: string[];
  sourceLinks?: RecommendationLink[];
}

export interface ResearchResult {
  query: string;
  summary: string;
  criteria: string[];
  items: ComparisonItem[];
  recommendation: Recommendation;
  sources: SourceReference[];
  durationSeconds?: number;
  createdAt: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: number;
  query: string;
  result: ResearchResult;
  isSample?: boolean;
}

