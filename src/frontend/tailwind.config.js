/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Fredoka', 'Nunito', 'system-ui', 'sans-serif'],
        sans: ['Nunito', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: '#1F2A44',
        muted: '#66708A',
        line: '#E3E6EF',
        canvas: '#F6F7FB',
        violet: { 50: '#F1EDFF', 100: '#E3DBFF', 300: '#B3A1FA', 500: '#6C4CF1', 600: '#5A3BE0', 700: '#4529B8' },
        sprout: { 50: '#E9F8F0', 100: '#CDEFDC', 500: '#2BB673', 600: '#1F9A5E', 700: '#167A49' },
        sun: { 50: '#FFF6E0', 100: '#FFE9B0', 400: '#FFC53D', 500: '#FFB020', 600: '#E0961A' },
        coral: { 50: '#FFEEEE', 100: '#FFD6D6', 500: '#FF6B6B', 600: '#E5534F' },
        sky: { 50: '#EAF4FF', 500: '#3D9BFF', 600: '#2483EA' },
      },
    },
  },
  plugins: [],
}
