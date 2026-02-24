export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        glass: "rgba(255,255,255,0.08)",
        borderGlass: "rgba(255,255,255,0.12)",
        accent: "#6366f1",   // Indigo-500
        accentSoft: "#818cf8"
      },
      boxShadow: {
        glass: "0 8px 30px rgba(0,0,0,0.25)",
      },
      backdropBlur: {
        xl: "20px",
      },
      borderRadius: {
        xl: "1.25rem",
        "2xl": "1.75rem",
      },
      animation: {
        "fade-up": "fadeUp 0.3s ease-out",
        "pulse-soft": "pulse 2s infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};