#!/usr/bin/env node
// *** ¿LA DEMO ABRE SIN RED? *** *
//
// Carga la página, deja que el service worker cachee el armazón y los trozos, se pone en
// offline de verdad (CDP `Network.emulateNetworkConditions`) y recarga. Tiene que seguir
// viéndose la lista, que es lo que se consulta en el súper sin cobertura.
//
// Uso: node scripts/prueba-offline-demo.mjs --base https://erdeivih.github.io/cesta-demo

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
const PUERTO = Number(arg('puerto', '9338'))
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

const perfil = mkdtempSync(join(os.tmpdir(), 'offline-cesta-'))
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
  await enviar('Network.enable')
  await enviar('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  })

  // 1) Dos pasadas online: la primera instala el SW y la segunda deja los trozos en caché.
  await enviar('Page.navigate', { url: `${BASE}/#/compra/listas` })
  await hasta(enviar, 'document.readyState === "complete"')
  await espera(2500)
  const registrado = await evalJs(enviar, `(async () => {
    try {
      const reg = await navigator.serviceWorker.ready
      return { hay: !!reg, controlador: !!navigator.serviceWorker.controller }
    } catch (e) {
      return { hay: false, error: String(e) }
    }
  })()`)
  informe.pasos.serviceWorker = registrado
  if (!registrado.hay) fallo('el service worker no se registró')

  await enviar('Page.reload', { ignoreCache: false })
  await hasta(enviar, 'document.readyState === "complete"')
  await espera(2500)
  informe.pasos.controlador = await evalJs(enviar, `!!navigator.serviceWorker.controller`)

  // 2) Offline de verdad y recarga.
  await enviar('Network.emulateNetworkConditions', {
    offline: true,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: -1,
  })
  await enviar('Page.reload', { ignoreCache: false })
  await hasta(enviar, 'document.readyState === "complete"')
  await espera(3000)
  const texto = await evalJs(enviar, `(document.querySelector('main')?.innerText || '')
    .replace(/\\s+/g, ' ').trim().slice(0, 500)`)
  informe.pasos.offline = { texto, titulo: await evalJs(enviar, 'document.title') }
  if (!/La semana/i.test(texto)) fallo('sin red no se ve la lista')
  if (!/8 productos/i.test(texto)) fallo('sin red no se ve el total de la lista')

  await enviar('Network.emulateNetworkConditions', {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: -1,
  })
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
