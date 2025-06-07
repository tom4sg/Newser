/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'navy': '#001F3F',
        'navy-dark': '#001830',
        'navy-darker': '#001021',
        'navy-light': '#002B59',
        'navy-lighter': '#003773',
      },
    },
  },
  plugins: [],
} 