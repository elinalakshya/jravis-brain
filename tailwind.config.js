/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mission: {
          bg: "#0b0b0b", // matte black background
          card: "#141414", // darker card color
          accent: "#00ff88", // neon green accent
          text: "#f0f0f0", // light text
          subtext: "#9ca3af", // gray subtext
          border: "#1f1f1f", // subtle border
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        heading: ["Orbitron", "sans-serif"],
      },
      boxShadow: {
        neon: "0 0 10px #00ff88",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
