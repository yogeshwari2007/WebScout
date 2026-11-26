"use client";

import * as React from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ClearHistoryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  entryCount: number;
}

export function ClearHistoryDialog({
  isOpen,
  onClose,
  onConfirm,
  entryCount,
}: ClearHistoryDialogProps) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="clear-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in-0 duration-200"
    >
      <div
        className="fixed inset-0"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-xl space-y-5 z-10 animate-in zoom-in-95 duration-200">
        <div className="flex items-start gap-3">
          <div className="h-10 w-10 rounded-xl bg-rose-500/10 text-rose-500 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <h3
              id="clear-dialog-title"
              className="text-lg font-bold text-foreground"
            >
              Clear All Research History?
            </h3>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              This will permanently delete all {entryCount} saved research session
              {entryCount === 1 ? "" : "s"} from your browser&apos;s local storage. This action cannot be undone.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-border bg-surface hover:bg-surface-hover text-foreground transition-colors"
          >
            Cancel
          </button>
          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            Yes, Clear All History
          </Button>
        </div>
      </div>
    </div>
  );
}
