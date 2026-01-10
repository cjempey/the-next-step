import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    // Force single-process execution to avoid worker pool issues in CI
    // In vitest 4.x, poolOptions are now top-level
    pool: 'forks',
    maxForks: 1,
    minForks: 1,
    watch: false,
    passWithNoTests: false,
  },
  server: {
    hmr: false,
  },
})
