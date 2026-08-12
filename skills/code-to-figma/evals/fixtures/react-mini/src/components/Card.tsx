import type { ReactNode } from "react";

export function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section
      style={{
        padding: "var(--spacing-16)",
        borderRadius: "var(--radius-8)",
        background: "var(--color-surface-primary)",
        // Second inline shadow. There is no shadow token layer in this
        // project — these two call sites are the whole of it.
        boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
      }}
    >
      <h2 style={{ fontSize: "var(--font-size-title)", color: "var(--color-text-primary)" }}>
        {title}
      </h2>
      {children}
    </section>
  );
}
