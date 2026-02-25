/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0a0a0f',
        'bg-secondary': '#12121a',
        'bg-elevated': '#1a1a25',
        'bg-hover': '#22222f',
        'text-primary': '#e4e4e7',
        'text-secondary': '#a1a1aa',
        'text-muted': '#71717a',
        'critical': '#ef4444',
        'warning': '#f59e0b',
        'success': '#22c55e',
        'info': '#3b82f6',
        'border': '#27272a',
        'border-focus': '#3b82f6',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
  safelist: [
    'bg-critical/10', 'bg-critical/20', 'bg-critical/30',
    'bg-warning/10', 'bg-warning/20', 'bg-warning-bg',
    'bg-success/10', 'bg-success/20', 'bg-success/30',
    'bg-info/10', 'bg-info/20', 'bg-info/30',
    'text-critical', 'text-warning', 'text-success', 'text-info',
    'border-critical/30', 'border-warning/20', 'border-success/30',
  ]
}
