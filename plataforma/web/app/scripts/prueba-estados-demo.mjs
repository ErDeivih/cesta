#!/usr/bin/env node
// *** LOS TRES ESTADOS DE LA LISTA Y DEL BUSCADOR, EN LA DEMO PUBLICADA. *** *
//
// `?demo=vacio`, `?demo=carga` y `?demo=error` existen para poder enseñar la pantalla
// sin backend. Este guion los recorre de verdad, a 390x844, y comprueba que cada uno dice
// lo que tiene que decir. Termina con código 1 si alguno no aparece.
//
// Uso:
//   node scripts/prueba-estados-demo.mjs --base https://erdeivih.github.io/cesta-demo

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
const PUERTO = Number(arg('puerto', '9337'))
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

const CASOS = [
  { nombre: 'lista normal', ruta: '/compra/listas', ms: 2200, espera: ['La semana', '8 productos'] },
  { nombre: 'lista vacia', ruta: '/compra/listas?demo=vacio', ms: 2200, espera: ['No tienes ninguna lista'] },
  { nombre: 'lista carga', ruta: '/compra/listas?demo=carga', ms: 900, espera: ['Cargando'] },
  { nombre: 'lista error', ruta: '/compra/listas?demo=error', ms: 2600, espera: ['No he podido traer tus listas'] },
  { nombre: 'buscar normal', ruta: '/compra?q=leche', ms: 2200, espera: ['resultados'] },
  { nombre: 'buscar vacio', ruta: '/compra?q=leche&demo=vacio', ms: 2200, espera: ['Nada con «leche»'] },
  { nombre: 'buscar carga', ruta: '/compra?q=leche&demo=carga', ms: 900, espera: ['Cargando'] },
  { nombre: 'buscar error', ruta: '/compra?q=leche&demo=error', ms: 2600, espera: ['No he podido buscar'] },
]

const perfil = mkdtempSync(join(os.tmpdir(), 'estados-cesta-'))
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

const informe = { base: BASE, viewport: { ancho: 390, alto: 844 }, casos: [], fallos: [] }

try {
  const pagina = await objetivo()
  const { ws, enviar } = await abrir(pagina.webSocketDebuggerUrl)
  await enviar('Page.enable')
  await enviar('Runtime.enable')
  await enviar('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  })

  for (const caso of CASOS) {
    await enviar('Page.navigate', { url: `${BASE}/#${caso.ruta}` })
    await hasta(enviar, 'document.readyState === "complete"')
    // *Cambiar solo el hash no recarga la página y React Query sirve lo que ya tenía: para
    // montar el estado forzado hay que recargar de verdad, como hace una persona al abrir
    // el enlace de `?demo=`.*
    await enviar('Page.reload', { ignoreCache: true })
    await hasta(enviar, 'document.readyState === "complete"')
    await espera(caso.ms)
    const texto = await evalJs(enviar, `(document.querySelector('main')?.textContent || '')
      .replace(/\\s+/g, ' ').trim().slice(0, 600)`)
    const faltan = caso.espera.filter((t) => !texto.includes(t))
    informe.casos.push({ ...caso, texto, faltan })
    if (faltan.length) informe.fallos.push(`${caso.nombre}: falta «${faltan.join('», «')}»`)
  }
  ws.close()
} catch (e) {
  informe.fallos.push(`la prueba se rompió: ${e instanceof Error ? e.message : String(e)}`)
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
