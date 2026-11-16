#!/usr/bin/env node
// *** ¿SE PUEDE INSTALAR LA DEMO? *** *
//
// Pregunta al navegador por los errores de instalabilidad (CDP) y comprueba el manifiesto y
// sus iconos por HTTP. No prueba el diálogo nativo —no se puede en headless—, pero sí lo que
// el navegador exige para ofrecerlo: manifiesto, nombre, iconos 192/512, start_url, display y
// service worker.
//
// Uso: node scripts/prueba-instalable-demo.mjs --base https://erdeivih.github.io/cesta-demo

import { spawn } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname, resolve } from 'node:path'
import os from 'node:os'

function arg(nombre, defecto = null) {
  const i = process.argv.indexOf(`--${nombre}`)
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : defecto
}

const BASE = (arg('base', 'http://localhost:4173/cesta-demo')).replace(/\/$/, '')
const SALIDA = arg('salida', '')
const PUERTO = Number(arg('puerto', '9340'))
const EDGE = process.env.CESTA_EDGE ?? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const espera = (ms) => new Promise((r) => setTimeout(r, ms))

async function objetivo() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PUERTO}/json/list`)
      const lista = await r.json()
      const pagina = lista.find((x) => x.type === 'page' && x.webSocketDebuggerUrl)
      if (pagina) return pagina
    } catch {
      /* aún no ha abierto */
    }
    await espera(200)
  }
  throw new Error('El navegador no abrió el puerto de depuración')
}

function abrir(wsUrl) {
  return new Promise((cumplir, fallar) => {
    const ws = new WebSocket(wsUrl)
    let siguiente = 1
    const pendientes = new Map()
    ws.addEventListener('open', () => cumplir({ ws, enviar }))
    ws.addEventListener('error', () => fallar(new Error('WebSocket no disponible')))
    ws.addEventListener('message', (e) => {
      const d = JSON.parse(e.data)
      if (d.id && pendientes.has(d.id)) {
        const { ok, ko } = pendientes.get(d.id)
        pendientes.delete(d.id)
        d.error ? ko(new Error(d.error.message)) : ok(d.result)
      }
    })
    function enviar(method, params = {}) {
      const id = siguiente++
      return new Promise((ok, ko) => {
        pendientes.set(id, { ok, ko })
        ws.send(JSON.stringify({ id, method, params }))
      })
    }
  })
}

async function evalJs(enviar, expresion) {
  const r = await enviar('Runtime.evaluate', {
    expression: expresion,
    returnByValue: true,
    awaitPromise: true,
    userGesture: true,
  })
  if (r.exceptionDetails) throw new Error('JS: ' + JSON.stringify(r.exceptionDetails).slice(0, 400))
  return r.result.value
}

async function hasta(enviar, expresion, intentos = 80, cada = 250) {
  for (let i = 0; i < intentos; i++) {
    try {
      if (await evalJs(enviar, expresion)) return true
    } catch {
      /* navegando */
    }
    await espera(cada)
  }
  return false
}

const perfil = mkdtempSync(join(os.tmpdir(), 'instalable-cesta-'))
const nav = spawn(
  EDGE,
  [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    `--remote-debugging-port=${PUERTO}`,
    `--user-data-dir=${perfil}`,
    'about:blank',
  ],
  { stdio: 'ignore', windowsHide: true },
)

const informe = { base: BASE, pasos: {}, fallos: [] }
const fallo = (m) => informe.fallos.push(m)

try {
  const pagina = await objetivo()
  const { ws, enviar } = await abrir(pagina.webSocketDebuggerUrl)
  await enviar('Page.enable')
  await enviar('Runtime.enable')
  await enviar('Page.navigate', { url: `${BASE}/#/compra/listas` })
  await hasta(enviar, 'document.readyState === "complete"')
  await espera(3000)

  const manifiesto = await evalJs(enviar, `(async () => {
    const enlace = document.querySelector('link[rel="manifest"]')?.href
    if (!enlace) return { hay: false }
    const r = await fetch(enlace)
    const m = await r.json()
    const iconos = await Promise.all((m.icons ?? []).map(async (i) => {
      const u = new URL(i.src, enlace).href
      const resp = await fetch(u)
      return { src: i.src, sizes: i.sizes, estado: resp.status }
    }))
    return { hay: true, name: m.name, short_name: m.short_name, start_url: m.start_url, display: m.display, icons: iconos }
  })()`)
  informe.pasos.manifiesto = manifiesto
  if (!manifiesto.hay) fallo('la página no enlaza un manifiesto')
  if (!manifiesto.name || !manifiesto.short_name) fallo('el manifiesto no tiene name/short_name')
  if (!manifiesto.start_url) fallo('el manifiesto no tiene start_url')
  if (manifiesto.display !== 'standalone') fallo('display no es standalone')
  for (const icono of manifiesto.icons ?? []) {
    if (icono.estado !== 200) fallo(`icono ${icono.src} responde ${icono.estado}`)
  }
  if (!(manifiesto.icons ?? []).some((i) => /192x192/.test(i.sizes))) fallo('falta icono 192')
  if (!(manifiesto.icons ?? []).some((i) => /512x512/.test(i.sizes))) fallo('falta icono 512')

  const errores = await enviar('Page.getInstallabilityErrors')
  informe.pasos.installabilityErrors = errores.installabilityErrors ?? []
  if ((errores.installabilityErrors ?? []).length > 0) {
    fallo('el navegador da errores de instalabilidad: ' +
      JSON.stringify(errores.installabilityErrors))
  }

  informe.pasos.serviceWorker = await evalJs(enviar, `(async () => {
    try {
      const r = await navigator.serviceWorker.ready
      return { hay: !!r, controlador: !!navigator.serviceWorker.controller }
    } catch (e) { return { hay: false, error: String(e) } }
  })()`)
  if (!informe.pasos.serviceWorker.hay) fallo('no hay service worker listo')
  if (!informe.pasos.serviceWorker.controlador) fallo('el service worker no controla la página')

  ws.close()
} catch (e) {
  fallo(`la prueba se rompió: ${e instanceof Error ? e.message : String(e)}`)
} finally {
  nav.kill()
  try {
    rmSync(perfil, { recursive: true, force: true })
  } catch {
    /* temporal */
  }
}

informe.ok = informe.fallos.length === 0
const texto = JSON.stringify(informe, null, 2)
if (SALIDA) {
  mkdirSync(dirname(resolve(SALIDA)), { recursive: true })
  writeFileSync(resolve(SALIDA), texto + '\n')
}
console.log(texto)
process.exit(informe.ok ? 0 : 1)
