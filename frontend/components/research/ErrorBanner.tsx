"use client";

import * as React from "react";
import Link from "next/link";
import { AlertCircle, AlertTriangle, RefreshCw, ArrowLeft, WifiOff } from "lucide-react";
import { ErrorScenarioType } from "@/lib/types";

interface ErrorBannerProps {
  type: ErrorScenarioType;
  onRetry?: () => void;
  onEdit?: () => void;
}

export function ErrorBanner({ type, onRetry, onEdit }: ErrorBannerProps) {
  const getDetails = (errType: ErrorScenarioType) => {
    switch (errType) {
      case "backend_unreachable":
        return {
          title: "Service Connection Issue",
          message:
            "WebScout couldn't connect to the research service. Please check your connection and try again.",
          icon: WifiOff,
          isWarning: false,
          canRetry: true,
        };
      case "all_failed":
        return {
          title: "All Sources Inaccessible",
          message:
            "We couldn't retrieve information from any of your selected websites.",
          icon: AlertCircle,
          isWarning: false,
          canRetry: true,
        };
      case "partial_failure":
        return {
          title: "Partial Sources Retrieved",
          message:
            "Some websites couldn't be accessed. WebScout can still compare the available sources.",
          icon: AlertTriangle,
          isWarning: true,
          canRetry: false,
        };
      case "analysis_failed":
        return {
          title: "Analysis Processing Error",
          message:
            "We retrieved the website information, but AI analysis couldn't be completed.",
          icon: AlertCircle,
          isWarning: false,
          canRetry: true,
        };
      default:
        return {
          title: "Research Processing Issue",
          message: "An unexpected condition occurred while processing your request.",
          icon: AlertCircle,
          isWarning: false,
          canRetry: true,
        };
    }
  };

  const details = getDetails(type);
  const Icon = details.icon;

  return (
    <div
      role="alert"
      className={`rounded-2xl border p-5 shadow-card space-y-3 transition-colors ${
        details.isWarning
          ? "border-amber-500/30 bg-amber-500/5 text-amber-900 dark:text-amber-100"
          : "border-red-500/30 bg-red-500/5 text-red-900 dark:text-red-100"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={`p-2 rounded-xl border shrink-0 mt-0.5 ${
              details.isWarning
                ? "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400"
                : "bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400"
            }`}
          >
            <Icon className="h-4 w-4" />
          </div>

          <div className="space-y-1">
            <h4 className="text-sm font-semibold tracking-tight">
              {details.title}
            </h4>
            <p className="text-xs opacity-90 leading-relaxed">
              {details.message}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {details.canRetry && onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-current/20 bg-background/50 hover:bg-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Retry</span>
            </button>
          )}

          {onEdit ? (
            <button
              type="button"
              onClick={onEdit}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-current/20 bg-background/50 hover:bg-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Edit Setup</span>
            </button>
          ) : (
            <Link
              href="/research"
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-current/20 bg-background/50 hover:bg-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Edit Setup</span>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
