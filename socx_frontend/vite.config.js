import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Lets the frontend call relative /api/... paths in dev without
      // fighting CORS — Vite forwards to the FastAPI backend directly.
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // recharts (+ its d3 internals) is the single heaviest
          // dependency and changes far less often than app code — its
          // own chunk means it's cached independently across deploys.
          charts: ['recharts'],
          vendor: ['react', 'react-dom', 'react-router-dom', 'axios'],
        },
      },
    },
  },
})
