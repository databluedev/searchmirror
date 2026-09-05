/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],

  // Only the files that can contain Tailwind classes. Deliberately excludes
  // src/assets/styles/**, so the JIT scanner never sees MUI or legacy class
  // names and never emits or purges against them.
  content: [
    './index.html',
    './src/components/ui/**/*.{js,jsx,ts,tsx}',
    './src/pages/**/*.{js,jsx,ts,tsx}',
    './src/lib/**/*.{js,jsx,ts,tsx}',
  ],

  // MUI ships its own CSS baseline. Tailwind's preflight resets margins, list
  // styles, heading sizes and, critically, `button`/`input` appearance -- it
  // would repaint the whole existing UI. Utilities only; no reset.
  corePlugins: {
    preflight: false,
  },

  theme: {
    extend: {
      // Mirrors src/assets/styles/modules/_tokens.scss so a shadcn component
      // and a legacy SCSS page render the same greys and the same blue.
      colors: {
        ink: '#0f0f10',
        'ink-2': '#3d3f45',
        'ink-3': '#6b6e76',
        'ink-4': '#9aa0a8',
        paper: '#ffffff',
        surface: '#ffffff',
        'surface-2': '#f5f5f6',
        line: 'rgba(15, 15, 16, 0.12)',
        'line-2': 'rgba(15, 15, 16, 0.06)',
        accent: '#1a3cff',
        'accent-weak': '#e8ecff',
        // _tokens.scss --ink-hover, mirrored in App.js as t.inkHover. The
        // primary button's hover fill was the only hex literal left in the
        // shadcn layer (docs/DESIGN.md, Non-negotiable #1).
        'ink-hover': '#26262a',
        'nav-accent': '#791fba',
        up: '#12b76a',
        down: '#d92d20',
        flat: '#98a2b3',
        warn: '#dc6803',
        border: '#e2e2e2',
      },
      fontFamily: {
        sans: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        // The landing page uses these; they resolve to the same self-hosted
        // Space Grotesk the rest of the app loads, and a mono stack.
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.045em',
        display: '-0.035em',
        micro: '0.09em',
      },
      fontSize: {
        micro: ['0.6875rem', { lineHeight: '1', letterSpacing: '0.09em' }],
      },
      transitionDuration: { fast: 'var(--dur)' },
      transitionTimingFunction: { brand: 'var(--ease)' },
      keyframes: {
        'blink-cursor': { '0%, 49%': { opacity: '1' }, '50%, 100%': { opacity: '0' } },
        'fade-up': { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        'blink-cursor': 'blink-cursor 1s step-end infinite',
        'fade-up': 'fade-up 320ms cubic-bezier(0.2,0,0,1) both',
      },
      borderRadius: {
        lg: '12px',
        md: '10px',
        sm: '8px',
        pill: '999px',
      },
    },
  },

  plugins: [require('tailwindcss-animate')],
};
