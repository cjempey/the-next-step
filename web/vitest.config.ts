import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    watch: false,
    // CI-specific configuration to prevent hanging
    // In Vitest 4.x, pool options are now top-level
    // Use forks pool with limited workers for better stability in CI
    pool: process.env.CI ? 'forks' : 'threads',
    // Vitest 4.x: poolOptions moved to top-level
    minForks: process.env.CI ? 1 : undefined,
    maxForks: process.env.CI ? 2 : undefined,
  },
})
