/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#0f172a',      // Dark navy background
          panel: '#1e293b',   // Dark slate panels
          panelLight: '#334155',
          accent: '#06b6d4',  // Cyan accent
          accentHover: '#0891b2',
          success: '#10b981', // Green
          warning: '#f59e0b', // Yellow
          danger: '#ef4444',  // Red
          critical: '#dc2626', // Dark red
          offline: '#6b7280', // Gray
        }
      }
    },
  },
  plugins: [],
}
