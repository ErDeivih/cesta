#!/usr/bin/env node
// *** EL PESO DEL BUNDLE, CON UN TOPE. *** *
//
// Lee el `index.html` compilado, saca el bundle de entrada y comprueba que no pase de 500 KB.
// El catálogo y la API de demo van en un trozo aparte que solo carga la demo; lo que se mide
// aquí es lo que tiene que descargar cualquier primera pantalla.
//
// Uso: node scripts/comprobar-peso-bundle.mjs
//      node scripts/comprobar-peso-bundle.mjs --max 512000

import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { gzipSync } from 'node:zlib'

const i = process.argv.indexOf('--max')
const MAX = i >= 0 ? Number(process.argv[i + 1]) : 500 * 1024
const dist = join(process.cwd(), '..', 'demo-dist')
const html = readFileSync(join(dist, 'index.html'), 'utf8')
const entrada = html.match(/assets\/index-[A-Za-z0-9_-]+\.js/)?.[0]
if (!entrada) {
  console.error('No encuentro el bundle de entrada en demo-dist/index.html')
  process.exit(1)
}
const ruta = join(dist, entrada)
const bytes = statSync(ruta).size
const gzip = gzipSync(readFileSync(ruta)).length
const kb = Math.round((bytes / 1024) * 10) / 10
const gzipKb = Math.round((gzip / 1024) * 10) / 10

console.log(JSON.stringify({
  entrada,
  bytes,
  kb,
  gzip,
  gzipKb,
  max: MAX,
  pasa: bytes <= MAX,
  nota: 'El catálogo/API/recetas de la demo van en un trozo aparte (api-*.js) que no carga la app de casa.',
}, null, 2))
process.exit(bytes <= MAX ? 0 : 1)
