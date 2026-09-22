import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El destino del proxy de desarrollo. Por defecto, el puerto donde escucha
// uvicorn si se levanta a mano. Con el compose de hoy la API **no publica el
// 8000** (solo la ve Caddy por la red interna), asi que para desarrollar contra
// la plataforma ya levantada hay que apuntar al 8080 de Caddy:
//
//     $env:CESTA_API='http://127.0.0.1:8080'; npm run dev
//
// En produccion nada de esto se usa: es Caddy quien manda /api al backend.
const destinoApi = process.env.CESTA_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],

  // Dos decisiones que no son de gusto:
  //
  //   outDir '../dist'  Caddy sirve `plataforma/web` y el docker-compose monta
  //                     esa carpeta. La app se construye a `web/dist`, que es lo
  //                     que se montara en /srv. Si el outDir se quedara en
  //                     `app/dist`, habria que cambiar el montaje en dos sitios
  //                     a la vez.
  //   base '/'          El index.html cuelga de la raiz del sitio, no de /app/.
  //                     Con una base relativa, /grupo/4125 pediria los assets a
  //                     /grupo/assets/... y la ficha saldria en blanco.
  base: '/',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    // Sin mapas en produccion: son megabytes que nadie va a leer en el movil.
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: destinoApi,
        changeOrigin: true,
      },
    },
  },
})
