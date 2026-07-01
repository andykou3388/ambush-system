import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  root: path.resolve(__dirname),
  resolve: {
    alias: [{ find: '@', replacement: path.resolve(__dirname, 'src') }]
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/**/*.{test,spec}.{js,ts}'],
  },
})