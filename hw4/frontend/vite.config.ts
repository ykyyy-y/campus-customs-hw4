import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The React dev server runs on 5173 and proxies data calls to the FastAPI backend on
// 8000, so the browser only ever talks to one origin and there are no CORS surprises.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
