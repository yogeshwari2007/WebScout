import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      type = "button",
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 select-none";

    const variantStyles = {
      primary:
        "bg-primary text-primary-foreground hover:bg-primary-hover shadow-subtle",
      secondary:
        "bg-surface text-foreground hover:bg-surface-hover border border-border shadow-subtle",
      outline:
        "border border-border bg-transparent text-foreground hover:bg-surface hover:text-foreground",
      ghost:
        "bg-transparent text-muted-foreground hover:bg-surface-hover hover:text-foreground",
      danger:
        "bg-rose-600 text-white hover:bg-rose-700 shadow-subtle focus-visible:ring-rose-500",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-xs rounded-lg gap-1.5",
      md: "h-9 px-4 text-sm rounded-xl gap-2",
      lg: "h-11 px-6 text-base rounded-2xl gap-2.5",
    };

    return (
      <button
        ref={ref}
        type={type}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
