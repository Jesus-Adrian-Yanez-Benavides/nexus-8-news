/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'nexus-bg': '#0f172a', // zinc-900 / slate-900 base
        'nexus-cyan': '#22d3ee', // neon cyan
        'nexus-emerald': '#10b981', // emerald
        'nexus-card': '#1e293b', // slate-800
      },
    },
  },
  plugins: [],
}
