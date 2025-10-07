import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          ink: '#16355B',
          teal: '#20C997',
          red: '#E63946',
          paper: '#FAF7F2',
          charcoal: '#2B2B2F',
          slate: '#6B7280'
        }
      }
    }
  },
  darkMode: 'class',
  plugins: []
} satisfies Config

