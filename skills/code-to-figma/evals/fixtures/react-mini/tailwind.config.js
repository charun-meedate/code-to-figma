/** Tailwind theme.
 *
 * Exposes the design tokens to utility classes.
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
