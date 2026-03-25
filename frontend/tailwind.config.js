/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#e8eef5',
          100: '#c5d3e3',
          200: '#9fb5cd',
          300: '#7897b7',
          400: '#5b80a6',
          500: '#3e6995',
          600: '#2d5580',
          700: '#1B3A5C',
          800: '#152d47',
          900: '#0e2033',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
