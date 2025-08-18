/**** @type {import('tailwindcss').Config} ****/
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#e9edf7',
          100: '#cfd7ee',
          200: '#a0b0de',
          300: '#7188cd',
          400: '#4765b7',
          500: '#2b4a98',
          600: '#223a78',
          700: '#192b59',
          800: '#111e3e',
          900: '#0b122a',
          950: '#05060a',
        },
        gold: {
          50: '#fff8e1',
          100: '#fee9a7',
          200: '#fdd76b',
          300: '#fcca3a',
          400: '#f7c948',
          500: '#d4af37',
          600: '#b68f2c',
          700: '#8f6e22',
          800: '#6b5119',
          900: '#4a3911',
        },
        onyx: '#0b0f16',
      },
    },
  },
  plugins: [],
}
