/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: { ink: '#0f172a', edge: { 50: '#eef6ff', 100: '#d9eaff', 500: '#2563eb', 600: '#1d4ed8', 700: '#1e40af' } },
    },
  },
  plugins: [],
}
