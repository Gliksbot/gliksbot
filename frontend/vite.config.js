import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { 
    port: 3000, 
    proxy: { 
      '/api': { 
        target: 'http://localhost:8080', 
        changeOrigin: true, 
        rewrite: p => p.replace(/^\/api/, '') 
      } 
    },
    watch: {
      // Ignore collaboration files to prevent hot reload cycles
      ignored: [
        '**/collaboration/**',
        '**/*.jsonl',
        '**/backend/collaboration/**',
        '**/vm_shared/**',
        '**/logs/**'
      ]
    }
  }
})
