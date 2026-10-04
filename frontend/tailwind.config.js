/** @type {import('tailwindcss').Config} */

// Colors are defined once, as CSS variables, in src/index.css
// (light in :root, dark inside @media (prefers-color-scheme: dark)).
// This helper keeps Tailwind opacity modifiers working: bg-terracotta/20 etc.
const c = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: {
        canvas: c("canvas"),
        surface: c("surface"),
        "surface-subtle": c("surface-subtle"),

        border: {
          DEFAULT: c("border"),
          strong: c("border-strong"),
        },

        charcoal: {
          900: c("charcoal-900"),
          DEFAULT: c("charcoal"),
          700: c("charcoal-700"),
          600: c("charcoal-600"),
          500: c("charcoal-500"),
          400: c("charcoal-400"),
          300: c("charcoal-300"),
        },

        terracotta: {
          DEFAULT: c("terracotta"),
          hover: c("terracotta-hover"),
          light: c("terracotta-light"),
          border: c("terracotta-border"),
        },

        forest: {
          DEFAULT: c("forest"),
          hover: c("forest-hover"),
          light: c("forest-light"),
          border: c("forest-border"),
        },

        amber: {
          subtle: c("amber-subtle"),
          border: c("amber-border"),
          text: c("amber-text"),
        },
      },

      fontFamily: {
        sans: ['"DM Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },

      boxShadow: {
        subtle:
          "0 1px 2px rgb(var(--shadow-rgb) / 0.04), 0 1px 3px rgb(var(--shadow-rgb) / 0.03)",

        card:
          "0 1px 3px rgb(var(--shadow-rgb) / 0.05), 0 4px 12px rgb(var(--shadow-rgb) / 0.03)",

        elevated:
          "0 4px 16px rgb(var(--shadow-rgb) / 0.08), 0 1px 4px rgb(var(--shadow-rgb) / 0.04)",
      },
    },
  },

  plugins: [],
};