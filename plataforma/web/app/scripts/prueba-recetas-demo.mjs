#!/usr/bin/env node
// *** LAS DIEZ RECETAS Y SUS CALORÍAS, EN LA DEMO PUBLICADA. *** *
//
// Usa la sonda de navegador que ya existe: no vuelve a montar CDP. Comprueba que el
// recetario dice «10 recetas», que las tarjetas llevan «kcal/ración» y que la ficha de la
// primera receta dice la cifra calculada (287 kcal por ración, 575 en total).
//
// Uso: node scripts/prueba-recetas-demo.mjs --base https://erdeivih.github.io/cesta-demo

import { spawnSync } from 'node:child_process'
import { readFileSync, mkdtempSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import os from 'node:os'

const i = process.argv.indexOf('--base')
const BASE = (i >= 0 ? process.argv[i + 1] : 'http://localhost:4173/cesta-demo').replace(/\/$/, '')
const tmp = mkdtempSync(join(os.tmpdir(), 'recetas-demo-'))
const salida = join(tmp, 'sonda.json')

const r = spawnSync(
  process.execPath,
  ['scripts/sonda-demo.mjs', '--url', `${BASE}/#/recetas`, '--espera', '3000', '--salida', salida],
  { encoding: 'utf8', timeout: 120000 },
)
if (r.status !== 0) {
  console.error(r.stderr || r.stdout)
  process.exit(1)
}
const recetario = JSON.parse(readFileSync(salida, 'utf8'))
const texto = recetario.textoPrimeraPantalla ?? ''
const fallos = []
if (!texto.includes('10 recetas')) fallos.push('el recetario no dice «10 recetas»')
if (!texto.includes('kcal/ración')) fallos.push('las tarjetas no enseñan kcal/ración')

const detalleSalida = join(tmp, 'detalle.json')
const d = spawnSync(
  process.execPath,
  ['scripts/sonda-demo.mjs', '--url', `${BASE}/#/recetas/1`, '--espera', '3000', '--salida', detalleSalida],
  { encoding: 'utf8', timeout: 120000 },
)
if (d.status !== 0) fallos.push('la ficha de la receta no cargó')
const detalle = JSON.parse(readFileSync(detalleSalida, 'utf8')).textoPrimeraPantalla ?? ''
if (!detalle.includes('287 kcal por ración')) fallos.push('la ficha no dice 287 kcal por ración')
if (!detalle.includes('575 kcal en total')) fallos.push('la ficha no dice 575 kcal en total')

rmSync(tmp, { recursive: true, force: true })
console.log(JSON.stringify({
  base: BASE,
  recetario: { diez: texto.includes('10 recetas'), kcal: texto.includes('kcal/ración') },
  detalle: { porRacion: detalle.includes('287 kcal por ración'), total: detalle.includes('575 kcal en total') },
  fallos,
  ok: fallos.length === 0,
}, null, 2))
process.exit(fallos.length === 0 ? 0 : 1)
