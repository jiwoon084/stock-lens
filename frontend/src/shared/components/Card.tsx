import type { PropsWithChildren } from "react";

interface CardProps extends PropsWithChildren {
  title?: string;
  className?: string;
}

export function Card({ title, className, children }: CardProps) {
  return (
    <section className={`card ${className ?? ""}`.trim()}>
      {title && <h3 className="card__title">{title}</h3>}
      {children}
    </section>
  );
}
