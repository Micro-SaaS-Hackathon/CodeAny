export default defineAppConfig({
  ui: {
    // Map semantic colors to base palettes; overridden by CSS variables below for precise brand hex
    colors: {
      primary: 'indigo',
      secondary: 'green',
      neutral: 'slate',
      success: 'green',
      warning: 'amber',
      error: 'red'
    },
    // Other runtime UI config can be added here if needed
  }
})
