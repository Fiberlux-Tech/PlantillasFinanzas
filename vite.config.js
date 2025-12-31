import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path' // This is correct

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // This is correct
      include: "**/*.{js,jsx,ts,tsx}",
    }),
  ],
  
  // This is correct
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // --- THIS IS THE UPDATED BLOCK ---
  // Use the full object syntax to add 'changeOrigin: true'
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true, // <-- THIS IS THE CRITICAL FIX
        secure: false
      },
      '/auth': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true, // <-- AND THIS ONE
        secure: false
      }
    }
  }
})