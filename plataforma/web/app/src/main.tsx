import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { App } from './App'
import { ErrorApi } from './api/cliente'
import './estilos.css'

/** Ajustes de Query, y por que.
 *
 *  - `retry` no reintenta un 4xx: si la API ha dicho "eso no existe", repetirlo
 *    tres veces solo hace esperar mas para ver el mismo 404.
 *  - `refetchOnWindowFocus: false` porque gold cambia una vez al dia. Volver a
 *    la pestana no cambia los precios, y con el movil en el bolsillo el
 *    navegador dispara ese evento cada vez que se saca.
 */
const cliente = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (intento, error) => {
        if (error instanceof ErrorApi && error.estado < 500) return false
        return intento < 1
      },
      refetchOnWindowFocus: false,
      staleTime: 60 * 1000,
      gcTime: 30 * 60 * 1000,
    },
  },
})

const raiz = document.getElementById('raiz')
if (!raiz) throw new Error('Falta el <div id="raiz"> en index.html.')

createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
