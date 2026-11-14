import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, HashRouter } from 'react-router-dom'

import { App } from './App'
import { instalaApiDemo } from './demo/api'
import { VigilaCuenta } from './api/cuenta'
import { ErrorApi } from './api/cliente'
// *** Las fuentes van PRIMERO, y el orden importa. *** *
//
// *Este fichero lo genera `scripts/bajar_fuentes_locales.py` y lleva los
// `@font-face` con los `.woff2` servidos **desde la propia app** *-- *no desde
// `fonts.googleapis.com` --.* *Va **antes** que `estilos.css` para que la fuente
// este pedida **en la primera pintada** y no se vea el respaldo primero.* *
//
// *Y el porque de servirla en casa esta medido: *hasta el 15/10/2026 **no se
// servia**, *y los titulos salian en **Georgia** *(-- lo confirma
// `docs/ui/capturas/01-inicio.png` --).* *
import './fuentes.css'
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

/** *** LA DEMO PUBLICA: DATOS EN LA PROPIA PÁGINA. *** *
 *
 *  *La demo de GitHub Pages no tiene servidor: se instala la API de mentira con la muestra
 *  incrustada (`src/demo/api.ts`) y las rutas van en el hash, para que Pages no tenga que
 *  resolver rutas profundas. Si no hay hash, se entra por la pantalla que enseña el producto.*
 */
const DEMO = import.meta.env.VITE_DEMO === '1'
if (DEMO) {
  instalaApiDemo()
  if (!window.location.hash) window.location.replace('#/compra/listas')
}

const Enrutador = DEMO ? HashRouter : BrowserRouter

// *** EL SERVICE WORKER: LA APP ABRE SIN RED. ***
// *Se registra **solo en produccion**: en desarrollo cachearia el armazon y los cambios no se verian,
// que es el error clasico de los service workers.*
// *Y no se espera a que este listo: registrar tarda y no hace falta para pintar.*
if (!DEMO && import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('/sw.js').catch(() => {
      // *No poder cachear no puede romper la app: sin SW funciona igual, solo que con red.*
    })
  })
}


createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <Enrutador>
        {/* **Vaciar la cache cuando cambia la cuenta.** Va antes que la aplicacion
            para que no haya ni un render con datos de la sesion anterior. */}
        <VigilaCuenta />
        <App />
      </Enrutador>
    </QueryClientProvider>
  </StrictMode>,
)
