import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-primary)",
        "bg-primary": "var(--bg-primary)",
        "bg-surface": "var(--bg-surface)",
        "bg-elevated": "var(--bg-elevated)",
        "bg-hover": "var(--bg-hover)",
        "bg-card": "var(--bg-surface)",

        "border-default": "var(--border-default)",
        "border-muted": "var(--border-muted)",

        "accent-blue": "var(--accent-blue)",
        "accent-purple": "var(--accent-purple)",
        "accent-green": "var(--accent-green)",
        "accent-amber": "var(--accent-amber)",
        "accent-red": "var(--accent-red)",
        "accent-grey": "var(--accent-grey)",

        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-muted": "var(--text-muted)",
      },
      fontFamily: {
        headline: ["JetBrains Mono", "monospace"],
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
      animation: {
        "pulse-blue": "pulse-blue 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards",
      },
      keyframes: {
        "pulse-blue": {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 5px var(--accent-blue)" },
          "50%": { opacity: ".8", boxShadow: "0 0 15px var(--accent-blue)" },
        },
        "slide-in": {
          "0%": { transform: "translateX(-10px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
export default config;
