/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#3B82F6',
        'primary-dark': '#2563EB',
        'primary-light': '#60A5FA',
        'gray-light': '#F8FAFC',
        'gray-lighter': '#F1F5F9',
        'gray-border': '#E2E8F0',
        'text-primary': '#1E293B',
        'text-secondary': '#64748B',
      },
    },
  },
  plugins: [],
} 