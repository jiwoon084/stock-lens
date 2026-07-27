interface LogoProps {
  className?: string;
}

export function Logo({ className }: LogoProps) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <circle cx="17" cy="17" r="11" stroke="var(--color-text)" strokeWidth="2.4" />
      <line x1="25.2" y1="25.2" x2="34" y2="34" stroke="var(--color-text)" strokeWidth="3.2" strokeLinecap="round" />
      <polyline
        points="10,21 15,15.5 19,18.5 24,10"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="24" cy="10" r="2.1" fill="var(--color-accent)" />
    </svg>
  );
}
