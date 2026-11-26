import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  rounded?: "xl" | "2xl";
  subtleHover?: boolean;
}

export function Card({
  className,
  rounded = "xl",
  subtleHover = false,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-card text-card-foreground border border-card-border shadow-card transition-all duration-200",
        rounded === "2xl" ? "rounded-2xl" : "rounded-xl",
        subtleHover && "hover:shadow-card-hover hover:border-primary/40",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-6 pb-3", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("font-semibold text-lg leading-none tracking-tight text-foreground", className)}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-muted-foreground leading-relaxed", className)}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-3", className)} {...props} />;
}
