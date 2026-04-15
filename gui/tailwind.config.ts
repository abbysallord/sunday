import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sunday: {
          bg: "#0a0a0f",
          surface: "#12121a",
          "surface-hover": "#1a1a25",
          border: "#1e1e2e",
          "border-active": "#2d2d44",
          text: "#e4e4ef",
          "text-muted": "#6b6b80",
          accent: "#7c5bf5",
          "accent-hover": "#6a4be0",
          "accent-glow": "rgba(124, 91, 245, 0.15)",
          user: "#1e3a5f",
          assistant: "#1a1a25",
          success: "#34d399",
          error: "#f87171",
          warning: "#fbbf24",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
