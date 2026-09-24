/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        rail: { 950: "#07182d", 900: "#0a2342", 800: "#12345a", 700: "#185080" },
        signal: { red: "#c73b33", amber: "#d88b24", green: "#238363" },
      },
      boxShadow: { panel: "0 8px 24px rgba(7,24,45,.08)" },
    },
  },
  plugins: [],
};
