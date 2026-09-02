import { ReactNode, useEffect } from "react";

interface ActionDrawerProps {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
  hideDividers?: boolean;
}

export function ActionDrawer({ title, children, footer, onClose, hideDividers = false }: ActionDrawerProps) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [onClose]);

  return (
    <div className="fixed inset-x-0 top-[72px] bottom-0 z-50" aria-hidden="false">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-black/70"
        onClick={(event) => event.preventDefault()}
        onTouchMove={(event) => event.preventDefault()}
        onWheel={(event) => event.preventDefault()}
      />
      <aside
        aria-label={title}
        aria-modal="true"
        role="dialog"
        className="absolute top-0 right-0 bottom-5 flex w-[400px] max-w-full min-w-0 flex-col overflow-hidden rounded-l-xl border border-secscan-border bg-secscan-surface shadow-2xl shadow-black/50"
      >
        <header className={`flex h-20 shrink-0 items-center justify-between px-6 ${hideDividers ? "" : "border-b border-secscan-border"}`}>
          <h2 className="text-xl font-semibold">{title}</h2>
          <button type="button" onClick={onClose} aria-label={`${title} 닫기`} className="shrink-0 rounded-lg border-0 px-2 py-1 text-lg text-secscan-muted">
            ×
          </button>
        </header>
        <div className="min-h-0 min-w-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-contain p-5">{children}</div>
        {footer && <footer className={`shrink-0 bg-secscan-surface p-4 ${hideDividers ? "" : "border-t border-secscan-border"}`}>{footer}</footer>}
      </aside>
    </div>
  );
}
