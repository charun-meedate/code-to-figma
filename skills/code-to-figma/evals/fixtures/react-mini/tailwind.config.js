/** The decoy.
 *
 * Everything here re-exports the CSS custom properties in
 * src/styles/tokens.css. Nothing is defined here. Extracting from this file
 * produces a set of var() references instead of values, and misses the
 * primitives entirely.
 *
 * The question to ask is "which file does a developer edit when a colour
 * changes?" — the answer is tokens.css, and this is a view of it.
 */
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "text-primary": "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        "surface-brand": "var(--color-surface-brand)",
      },
      spacing: {
        4: "var(--spacing-4)",
        8: "var(--spacing-8)",
        16: "var(--spacing-16)",
      },
    },
  },
};
