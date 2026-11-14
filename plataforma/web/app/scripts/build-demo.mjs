#!/usr/bin/env node
// Compila la **demo estática** que se publica en GitHub Pages.
//
// No es el build de la app: ese sirve Caddy con su API. Este:
//   - compila en modo `demo` (base `/cesta-demo/`, salida `../demo-dist`),
//   - con `VITE_DEMO=1`, que monta la API de mentira con la muestra incrustada,
//   - y deja `.nojekyll` para que Pages no filtre ficheros que empiezan por `_`.
//
// Uso: `npm run build:demo` desde `plataforma/web/app`.

import { spawnSync } from 'node:child_process'
import { copyFileSync, existsSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const app = process.cwd()
const salida = join(app, '..', 'demo-dist')

function corre(args, opciones = {}) {
  const r = spawnSync('npx', args, { stdio: 'inherit', shell: true, cwd: app, ...opciones })
  if (r.status !== 0) process.exit(r.status ?? 1)
}

corre(['tsc', '--noEmit'])
corre(['vite', 'build', '--mode', 'demo'], { env: { ...process.env, VITE_DEMO: '1' } })

if (!existsSync(join(salida, 'index.html'))) {
  console.error('No se ha generado', join(salida, 'index.html'))
  process.exit(1)
}

writeFileSync(join(salida, '.nojekyll'), '')
// Con las rutas en el hash no hace falta el 404 de SPA, pero se deja igual: si algún día se
// enlaza una ruta sin hash, Pages devuelve la app en vez de una página de error.
copyFileSync(join(salida, 'index.html'), join(salida, '404.html'))
console.log('demo compilada en', salida)
