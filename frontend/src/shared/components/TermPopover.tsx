import { useEffect, useRef, type CSSProperties } from "react";

import { useTermPopover } from "../context/TermPopoverContext";
import { GLOSSARY } from "../glossary";

const MARGIN = 8;

// Positions off the clicked term's own viewport rect (position: fixed), not a chart coordinate —
// unlike ChartMovementPopover this has no chart/container to track, so it doesn't need a
// ResizeObserver. Flips to the opposite side near either viewport edge, same idea as
// ChartMovementPopover's left/right flip.
export function TermPopover() {
  const { active, close } = useTermPopover();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active) return;

    function handlePointerDown(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) close();
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [active, close]);

  if (!active) return null;

  const definition = GLOSSARY.find((entry) => entry.term === active.term)?.definition;
  if (!definition) return null;

  const { rect } = active;
  const anchorFromRight = rect.left > window.innerWidth / 2;
  const anchorFromBottom = rect.top > window.innerHeight / 2;

  const style: CSSProperties = {
    ...(anchorFromBottom
      ? { bottom: Math.max(MARGIN, window.innerHeight - rect.top + MARGIN) }
      : { top: Math.min(window.innerHeight - MARGIN, rect.bottom + MARGIN) }),
    ...(anchorFromRight
      ? { right: Math.max(MARGIN, window.innerWidth - rect.right) }
      : { left: Math.max(MARGIN, rect.left) }),
  };

  return (
    <div className="term-popover" style={style} ref={ref} role="tooltip">
      <button type="button" className="term-popover__close" onClick={close} aria-label="닫기">
        ✕
      </button>
      <p className="term-popover__term">{active.term}</p>
      <p className="term-popover__definition">{definition}</p>
    </div>
  );
}
