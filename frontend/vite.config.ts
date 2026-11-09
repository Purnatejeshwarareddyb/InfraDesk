/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backend = process.env.VITE_BACKEND_URL ?? 'http://localhost:8000'
const proxied = ['/api', '/health', '/ready', '/docs', '/openapi.json']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(proxied.map((path) => [path, { target: backend, changeOrigin: false }])),
  },
  preview: {
    port: 4173,
    proxy: Object.fromEntries(proxied.map((path) => [path, { target: backend, changeOrigin: false }])),
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/tests/setup.ts'],
    css: false,
  },
})
