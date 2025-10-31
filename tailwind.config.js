/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mission: {
          bg: "#0b0b0b", // Matte black background
          card: "#141414", // Slightly lighter card surface
          accent: "#00ff88", // Neon green accent
          text: "#f0f0f0", // Light text
          subtext: "#9ca3af", // Muted gray subtext
          border: "#1f1f1f", // Subtle border
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        heading: ["Orbitron", "sans-serif"], // Futuristic heading font
      },
      boxShadow: {
        neon: "0 0 12px #00ff88", // Glowing effect for cards and text
        glow: "0 0 20px #00ff88",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      animation: {
        pulseGlow: "pulseGlow 2s infinite",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { textShadow: "0 0 5px #00ff88, 0 0 15px #00ff88" },
          "50%": { textShadow: "0 0 10px #00ff88, 0 0 25px #00ff88" },
        },
      },
    },
  },
  plugins: [],
};
