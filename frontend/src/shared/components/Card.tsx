import type { PropsWithChildren, ReactNode } from "react";

interface CardProps extends PropsWithChildren {
  title?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function Card({ title, actions, className, children }: CardProps) {
  return (
    <section className={`card ${className ?? ""}`.trim()}>
      {(title || actions) && (
        <div className="card__header">
          {title && <h3 className="card__title">{title}</h3>}
          {actions && <div className="card__actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
