import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Build configuration for Vercel deployment
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Optimize for production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.logs in production
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-core': ['react', 'react-dom', 'react-router-dom'],
          'vendor-supabase': ['@supabase/supabase-js'],
          'vendor-ui': ['@radix-ui/react-select', '@radix-ui/react-slot', 'lucide-react'],
        },
      },
    },
  },

  // Development server configuration
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to Flask backend during development
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  // Path aliases for cleaner imports
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
