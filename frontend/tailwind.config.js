/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: "#070A0F",
        secondary: "#0D131C",
        surface: {
          DEFAULT: "#0D131C",
          card: "rgba(16, 24, 38, 0.75)",
          light: "rgba(24, 36, 54, 0.65)",
          glass: "rgba(10, 15, 23, 0.88)",
          border: "rgba(56, 189, 248, 0.16)",
        },
        text: {
          primary: "#FFFFFF",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
        electric: {
          DEFAULT: "#00F0FF",
          glow: "rgba(0, 240, 255, 0.28)",
          cyan: "#00F0FF",
          lime: "#00F0FF",
          mint: "#10E760",
          purple: "#A855F7",
          dim: "#0284C7",
          dark: "#041C2C"
        },
        signal: {
          cyan: "#00F0FF",
          green: "#10E760",
          yellow: "#FBBF24",
          red: "#FF3366",
          purple: "#C084FC",
          blue: "#38BDF8"
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'electric-sm': '0 0 14px rgba(0, 240, 255, 0.20)',
        'electric-md': '0 0 28px rgba(0, 240, 255, 0.30)',
        'electric-lg': '0 0 45px rgba(0, 240, 255, 0.40)',
        'glass-card': '0 8px 32px 0 rgba(0, 0, 0, 0.70)',
      },
      animation: {
        'radar-sweep': 'sweep 4s linear infinite',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        sweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.03)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-3px)' },
        }
      }
    },
  },
  plugins: [],
}
