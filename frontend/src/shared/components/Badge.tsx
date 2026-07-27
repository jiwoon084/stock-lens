import type { PropsWithChildren } from "react";

export type BadgeTone = "accent" | "positive" | "negative" | "neutral";

interface BadgeProps extends PropsWithChildren {
  tone?: BadgeTone;
  className?: string;
}

export function Badge({ tone = "neutral", className, children }: BadgeProps) {
  return <span className={`badge badge--${tone} ${className ?? ""}`.trim()}>{children}</span>;
}
