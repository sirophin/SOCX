/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        // Base surfaces — deep navy-black, not pure #000, per the SOC
        // "modern dark theme, professional" brief.
        base: {
          950: '#0A0E17',
          900: '#0B0F19',
          800: '#111827',
          700: '#161E2E',
          600: '#1E293B',
          500: '#2A374D',
        },
        ink: {
          // Text colors
          100: '#E7ECF3',
          300: '#C3CCDB',
          500: '#94A3B8',
          600: '#748097',
          700: '#5B6B84',
        },
        accent: {
          // Primary blue — action color
          400: '#5B9CF6',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        // Severity scale — used consistently for alert/rule/log severity
        severity: {
          critical: '#E0435C',
          high: '#F0834A',
          medium: '#E8B93F',
          low: '#5B9CF6',
          info: '#748097',
        },
        // Alert/incident status scale
        statuscolor: {
          open: '#5B9CF6',
          investigating: '#E8B93F',
          contained: '#B07CE8',
          resolved: '#3FCB7E',
          closed: '#748097',
          pending: '#748097',
          parsing: '#5B9CF6',
          completed: '#3FCB7E',
          partial: '#E8B93F',
          failed: '#E0435C',
        },
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.5)',
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '8px',
        lg: '10px',
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
    },
  },
  plugins: [],
}
