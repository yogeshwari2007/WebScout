"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";

interface NavItem {
  label: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Research", href: "/research" },
  { label: "History", href: "/history" },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Close mobile drawer on route change
  React.useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo & Name */}
        <Link
          href="/"
          className="group flex items-center gap-2.5 transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg p-1"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-subtle transition-transform group-hover:scale-105">
            <Compass className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-base tracking-tight text-foreground flex items-center gap-1.5">
              WebScout
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                MVP
              </span>
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "px-3.5 py-1.5 text-sm font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive
                    ? "bg-surface text-foreground shadow-subtle border border-border"
                    : "text-muted-foreground hover:text-foreground hover:bg-surface-hover"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Section: Theme Toggle & Mobile Trigger */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />

          {/* Mobile Menu Hamburger Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
            className="md:hidden flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-surface text-foreground transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {mobileMenuOpen ? (
              <X className="h-4 w-4" />
            ) : (
              <Menu className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="md:hidden border-b border-border bg-background px-4 py-4 overflow-hidden"
          >
            <nav className="flex flex-col space-y-1">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "px-3.5 py-2 text-sm font-medium rounded-xl transition-colors",
                      isActive
                        ? "bg-surface text-foreground border border-border"
                        : "text-muted-foreground hover:text-foreground hover:bg-surface-hover"
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
