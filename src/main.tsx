// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' // <-- 1. Import
import App from './App.tsx'
import './index.css'
import { configureApi } from '@/lib/api'
import { supabaseTokenProvider } from '@/lib/supabase'

// Wire auth token provider into the API client (decoupled from Supabase)
configureApi(supabaseTokenProvider)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter> {/* <-- 2. Wrap App */}
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)