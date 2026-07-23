import { useMemo } from "react";

import { useTermPopover } from "../context/TermPopoverContext";
import { GLOSSARY } from "../glossary";

interface HighlightedTextProps {
  text: string;
}

// Longest term first so overlapping entries match the more specific one first (e.g. a future
// "자기주식" entry would otherwise swallow "자기주식처분" instead of the other way around).
const SORTED_TERMS = [...GLOSSARY].sort((a, b) => b.term.length - a.term.length);
const TERM_SET = new Set(SORTED_TERMS.map((entry) => entry.term));
const PATTERN =
  SORTED_TERMS.length > 0
    ? new RegExp(`(${SORTED_TERMS.map((entry) => entry.term).join("|")})`, "g")
    : null;

export function HighlightedText({ text }: HighlightedTextProps) {
  const { openTerm } = useTermPopover();

  const parts = useMemo(() => (PATTERN ? text.split(PATTERN) : [text]), [text]);

  return (
    <>
      {parts.map((part, index) => {
        if (!TERM_SET.has(part)) return part;

        return (
          <mark
            key={index}
            className="glossary-term"
            role="button"
            tabIndex={0}
            onClick={(event) => openTerm(part, event.currentTarget.getBoundingClientRect())}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openTerm(part, event.currentTarget.getBoundingClientRect());
              }
            }}
          >
            {part}
          </mark>
        );
      })}
    </>
  );
}
