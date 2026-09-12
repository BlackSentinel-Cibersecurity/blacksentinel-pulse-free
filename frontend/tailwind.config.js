/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // BlackSentinel brand colors
        sentinel: {
          black: '#0A0A0A',
          dark: '#111111',
          gray: {
            900: '#1A1A1A',
            800: '#222222',
            700: '#2D2D2D',
            600: '#3D3D3D',
            500: '#555555',
            400: '#777777',
            300: '#999999',
            200: '#BBBBBB',
            100: '#DDDDDD',
          },
          white: '#F5F5F5',
          orange: {
            50: '#FFF7ED',
            100: '#FFEDD5',
            200: '#FED7AA',
            300: '#FDBA74',
            400: '#FB923C',
            500: '#FF6B2C',  // Primary orange
            600: '#EA580C',
            700: '#C2410C',
            800: '#9A3412',
            900: '#7C2D12',
          },
          // Risk colors
          risk: {
            critical: '#FF3B3B',
            high: '#FF6B2C',
            medium: '#FFB020',
            low: '#34D399',
            info: '#60A5FA',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'grid-pattern': `
          linear-gradient(rgba(255, 107, 44, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 107, 44, 0.03) 1px, transparent 1px)
        `,
        'glow-gradient': 'radial-gradient(ellipse at center, rgba(255, 107, 44, 0.15) 0%, transparent 70%)',
        'pulse-gradient': 'radial-gradient(circle at 50% 50%, rgba(255, 107, 44, 0.1) 0%, rgba(10, 10, 10, 0) 70%)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan-line': 'scanLine 3s linear infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-right': 'slideRight 0.3s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(255, 107, 44, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(255, 107, 44, 0.4)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
