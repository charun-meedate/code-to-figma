import type { ReactNode } from "react";

type Variant = "primary" | "secondary" | "danger";

export function Button({
  children,
  variant = "primary",
  disabled = false,
  onClick,
}: {
  children: ReactNode;
  variant?: Variant;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      className={`btn btn--${variant}`}
      disabled={disabled}
      onClick={onClick}
      style={{
        padding: "var(--spacing-12) var(--spacing-24)",
        borderRadius: "var(--radius-8)",
        fontSize: "var(--font-size-body)",
        // Inline shadow — there is no shadow token layer in this project.
        boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
      }}
    >
      {children}
    </button>
  );
}
