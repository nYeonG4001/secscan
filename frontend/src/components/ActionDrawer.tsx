import { ReactNode, useEffect } from "react";

interface ActionDrawerProps {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
}

export function ActionDrawer({ title, children, footer, onClose }: ActionDrawerProps) {
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
    <div className="fixed inset-0 z-50" aria-hidden="false">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-black/40"
        onClick={(event) => event.preventDefault()}
        onTouchMove={(event) => event.preventDefault()}
        onWheel={(event) => event.preventDefault()}
      />
      <aside
        aria-label={title}
        aria-modal="true"
        role="dialog"
        className="absolute inset-y-0 right-0 flex w-[400px] max-w-full flex-col border-l border-gray-800 bg-white shadow-xl"
      >
        <header className="flex h-16 shrink-0 items-center justify-between border-b px-5">
          <h2 className="text-base font-semibold">{title}</h2>
          <button type="button" onClick={onClose} aria-label={`${title} 닫기`} className="rounded px-2 py-1 text-lg">
            ×
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-5">{children}</div>
        {footer && <footer className="shrink-0 border-t bg-white p-4">{footer}</footer>}
      </aside>
    </div>
  );
}
