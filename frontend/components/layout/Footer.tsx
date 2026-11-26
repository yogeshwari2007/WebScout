import * as React from "react";
import { Compass } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-border bg-background transition-colors">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Brand & Tagline */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/20 text-primary">
              <Compass className="h-3.5 w-3.5" />
            </div>
            <span className="text-sm font-semibold text-foreground">WebScout</span>
            <span className="text-xs text-muted-foreground">
              — AI-powered multi-website research agent
            </span>
          </div>

          {/* Hackathon Meta & Status */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>wHACKiest 2026 • Track 2</span>
            <span>•</span>
            <span>&copy; {currentYear} WebScout. All rights reserved.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
