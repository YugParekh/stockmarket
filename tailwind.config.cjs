/** @type {import('tailwindcss').Config} */
// MarketSentinel AI - Premium Design System Config

module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b0b0b"
      },
      boxShadow: {
        "neon-cyan": "0 0 25px rgba(34,211,238,0.35)",
        "neon-green": "0 0 25px rgba(34,197,94,0.35)",
        "neon-orange": "0 0 25px rgba(249,115,22,0.45)",
        "neon-red": "0 0 25px rgba(248,113,113,0.45)"
      },
      backdropBlur: {
        xs: "2px",
      }
    }
  },
  plugins: []
};
