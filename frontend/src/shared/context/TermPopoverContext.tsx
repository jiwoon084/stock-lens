import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface ActiveTerm {
  term: string;
  rect: DOMRect;
}

interface TermPopoverContextValue {
  active: ActiveTerm | null;
  openTerm: (term: string, rect: DOMRect) => void;
  close: () => void;
}

const TermPopoverContext = createContext<TermPopoverContextValue | null>(null);

export function TermPopoverProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<ActiveTerm | null>(null);

  const openTerm = useCallback((term: string, rect: DOMRect) => {
    setActive({ term, rect });
  }, []);
  const close = useCallback(() => setActive(null), []);

  const value = useMemo(() => ({ active, openTerm, close }), [active, openTerm, close]);

  return <TermPopoverContext.Provider value={value}>{children}</TermPopoverContext.Provider>;
}

export function useTermPopover(): TermPopoverContextValue {
  const ctx = useContext(TermPopoverContext);
  if (!ctx) throw new Error("useTermPopover must be used within a TermPopoverProvider");
  return ctx;
}
