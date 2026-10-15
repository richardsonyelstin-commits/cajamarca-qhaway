const palette = {
  50: 'var(--cal-50)', 100: 'var(--cal-100)', 200: 'var(--cal-200)', 300: 'var(--cal-300)',
  400: 'var(--piedra-400)', 500: 'var(--piedra-500)', 600: 'var(--piedra-600)',
  700: 'var(--piedra-700)', 800: 'var(--piedra-800)', 900: 'var(--anil-900)', 950: 'var(--anil-950)'
};
const colors = {
  transparent: 'transparent', current: 'currentColor', inherit: 'inherit',
  white: 'var(--c-superficie)', black: 'var(--anil-950)',
  slate: palette, gray: palette, zinc: palette, neutral: palette, stone: palette,
  primary: { DEFAULT: 'var(--color-primary)', light: 'var(--anil-700)', dark: 'var(--anil-950)' },
  secondary: { DEFAULT: 'var(--color-secondary)', hover: 'var(--c-accion-hover)', container: 'var(--c-realce)' },
  surface: { DEFAULT: 'var(--color-surface)', dim: 'var(--color-surface-dim)', bright: 'var(--color-surface-bright)',
    container: 'var(--color-surface-container)', 'container-lowest': 'var(--color-surface-container-lowest)',
    'container-low': 'var(--color-surface-container-low)', 'container-high': 'var(--color-surface-container-high)',
    'container-highest': 'var(--color-surface-container-highest)' },
  'on-surface': { DEFAULT: 'var(--c-texto)', variant: 'var(--c-texto-2)' },
  'on-primary': 'var(--c-accion-texto)', 'on-secondary': 'var(--c-accion-texto)',
  'secondary-container': 'var(--c-realce)', 'on-secondary-container': 'var(--c-texto)',
  outline: { DEFAULT: 'var(--c-texto-3)', variant: 'var(--c-borde)' },
  'civic-emerald': 'var(--c-accion)', 'civic-teal': 'var(--c-accion)',
  'alert-amber': 'var(--sev-media-suave-texto)', 'alert-rose': 'var(--sev-critica-suave-texto)',
  'slate-surface': 'var(--c-superficie)', 'slate-border': 'var(--c-borde)',
  'background-light': 'var(--c-fondo)', 'background-dark': 'var(--c-fondo)',
};
for (const [name, token] of Object.entries({ blue: 'anil', indigo: 'anil', cyan: 'jalca', teal: 'jalca',
  green: 'jalca', emerald: 'jalca', red: 'cochinilla', rose: 'cochinilla', amber: 'retama',
  yellow: 'retama', orange: 'achiote', purple: 'kiwicha', violet: 'kiwicha' })) {
  colors[name] = { 50: `var(--${token}-100)`, 100: `var(--${token}-100)`, 200: `var(--${token}-100)`,
    300: `var(--${token}-500)`, 400: `var(--${token}-500)`, 500: `var(--${token}-600, var(--${token}-500))`,
    600: `var(--${token}-600, var(--${token}-700))`, 700: `var(--${token}-700)`,
    800: `var(--${token}-700)`, 900: `var(--${token}-700)`, 950: 'var(--anil-950)' };
}
module.exports = {
  content: ['./web/*.html', './web/src/js/*.js'], darkMode: 'class',
  theme: { colors, extend: {
    fontFamily: { sans: ['Public Sans', 'system-ui', 'sans-serif'], serif: ['Fraunces', 'serif'],
      mono: ['JetBrains Mono', 'monospace'], 'headline-xl': ['Fraunces', 'serif'], 'headline-sm': ['Fraunces', 'serif'] },
    fontSize: { 'headline-xl': ['var(--fs-7)', '1.12'], 'headline-lg': ['var(--fs-6)', '1.12'],
      'headline-md': ['var(--fs-5)', '1.2'], 'headline-sm': ['var(--fs-4)', '1.3'],
      'body-lg': ['var(--fs-4)', '1.55'], 'body-md': ['var(--fs-3)', '1.55'], 'body-sm': ['var(--fs-2)', '1.5'],
      'label-md': ['var(--fs-2)', '1.4'], 'label-sm': ['var(--fs-1)', '1.4'], caption: ['var(--fs-1)', '1.4'] },
  } },
};
