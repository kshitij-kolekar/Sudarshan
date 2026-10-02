/** @type {import('tailwindcss').Config} */

// ============================================================
// LIGHT THEME
// ============================================================

const lightTheme = {
  canvas: "#F8F7F4",
  surface: "#FFFFFF",
  "surface-subtle": "#F3F2EE",

  border: {
    DEFAULT: "#E5E3DC",
    strong: "#D2CEC4",
  },

  charcoal: {
    900: "#141517",
    DEFAULT: "#1D1F22",
    700: "#2B2E33",
    600: "#444850",
    500: "#636873",
    400: "#868C98",
    300: "#B0B5BF",
  },

  terracotta: {
    DEFAULT: "#C4542E",
    hover: "#AD4421",
    light: "#FAECE6",
    border: "#E9B6A3",
  },

  forest: {
    DEFAULT: "#2B5840",
    hover: "#224733",
    light: "#EAF2ED",
    border: "#A5C5B2",
  },

  amber: {
    subtle: "#FDF6E2",
    border: "#EAD69E",
    text: "#8A6112",
  },
};


// ============================================================
// DARK THEME
// ============================================================

const darkTheme = {
  canvas: "#080909",
  surface: "#101112",
  "surface-subtle": "#181A1C",

  border: {
    DEFAULT: "#292C30",
    strong: "#3A3E43",
  },

  charcoal: {
    900: "#F2F3F3",
    DEFAULT: "#E5E7E8",
    700: "#C5C8CB",
    600: "#A2A6AB",
    500: "#858A90",
    400: "#686D73",
    300: "#4B5056",
  },

  terracotta: {
    DEFAULT: "#D65A32",
    hover: "#E06A42",
    light: "#321B14",
    border: "#713522",
  },

  forest: {
    DEFAULT: "#4F9A70",
    hover: "#62AD83",
    light: "#14251C",
    border: "#315C43",
  },

  amber: {
    subtle: "#292313",
    border: "#655322",
    text: "#D5A83A",
  },
};


// ============================================================
// ACTIVE THEME
// ============================================================

// LIGHT THEME
const activeTheme = lightTheme;

// DARK THEME
// const activeTheme = darkTheme;


// ============================================================
// TAILWIND CONFIG
// ============================================================

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: activeTheme,

      fontFamily: {
        sans: ['"DM Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },

      boxShadow: {
        subtle:
          "0 1px 2px rgba(20, 21, 23, 0.04), 0 1px 3px rgba(20, 21, 23, 0.03)",

        card:
          "0 1px 3px rgba(20, 21, 23, 0.05), 0 4px 12px rgba(20, 21, 23, 0.03)",

        elevated:
          "0 4px 16px rgba(20, 21, 23, 0.08), 0 1px 4px rgba(20, 21, 23, 0.04)",
      },
    },
  },

  plugins: [],
};