#!/usr/bin/env node
// *** SELLA EL SERVICE WORKER CON LA VERSIÓN DEL BUILD. *** *
//
// Sin esto, el service worker de la demo se queda con `avio-demo-v1` para siempre: el
// navegador no ve cambiar el fichero, no instala el nuevo y sigue sirviendo la caché vieja.
// El sello es el hash del `index.html` compilado, que cambia cuando cambia el bundle de
// entrada (y con él el trozo de API/recetas).
//
// Uso: node scripts/sella-sw-demo.mjs

import { createHash } from 'node:crypto'
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const dist = join(process.cwd(), '..', 'demo-dist')
const index = readFileSync(join(dist, 'index.html'), 'utf8')
const version = createHash('sha256').update(index).digest('hex').slice(0, 8)
const sw = join(dist, 'sw-demo.js')
const original = readFileSync(sw, 'utf8')
if (!original.includes('__VERSION__')) {
  console.error('sw-demo.js no tiene el marcador __VERSION__')
  process.exit(1)
}
writeFileSync(sw, original.replaceAll('__VERSION__', version))
console.log('service worker sellado:', version)
