import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1200px" },
    },
    extend: {
      fontFamily: {
        sans: [
          "Space Grotesk",
          "Be Vietnam Pro",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        /* SearchMirror palette — DESIGN.md */
        ink: {
          DEFAULT: "hsl(var(--ink))",
          2: "hsl(var(--ink-2))",
          3: "hsl(var(--ink-3))",
          4: "hsl(var(--ink-4))",
        },
        paper: "hsl(var(--paper))",
        surface: {
          DEFAULT: "hsl(var(--surface))",
          2: "hsl(var(--surface-2))",
        },
        line: {
          DEFAULT: "var(--line)",
          2: "var(--line-2)",
        },
        up: "hsl(var(--up))",
        down: "hsl(var(--down))",
        flat: "hsl(var(--flat))",
      },
      borderRadius: {
        sm: "var(--r-sm)",
        md: "var(--r-md)",
        lg: "var(--r-lg)",
        pill: "var(--r-pill)",
      },
      /* Named, so nothing has to write `duration-[var(--dur)]` — that arbitrary
         value is ambiguous between transition- and animation-duration. */
      transitionDuration: { fast: "var(--dur)" },
      transitionTimingFunction: { brand: "var(--ease)" },
      letterSpacing: {
        tightest: "-0.045em",
        display: "-0.035em",
        micro: "0.09em",
      },
      fontSize: {
        micro: ["0.6875rem", { lineHeight: "1", letterSpacing: "0.09em" }],
      },
      keyframes: {
        /* Required by @magicui/typing-animation. The shadcn CLI emits this as a
           Tailwind v4 `@theme inline` block in index.css; this project is v3, so
           it lives here instead. */
        "blink-cursor": {
          "0%, 49%": { opacity: "1" },
          "50%, 100%": { opacity: "0" },
        },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "blink-cursor": "blink-cursor 1s step-end infinite",
        "fade-up": "fade-up 320ms cubic-bezier(0.2,0,0,1) both",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
