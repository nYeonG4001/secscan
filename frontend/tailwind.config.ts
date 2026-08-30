import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        secscan: {
          canvas: "#080808",
          surface: "#121214",
          "surface-2": "#17171A",
          border: "#2A2A2F",
          foreground: "#F5F5F5",
          muted: "#A0A0AA",
          violet: "#B45CFF",
          magenta: "#F05CFF",
          cyan: "#39D9CE",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
