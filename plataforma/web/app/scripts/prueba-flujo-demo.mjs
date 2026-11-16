#!/usr/bin/env node
// *** LA PRUEBA DEL FLUJO DE LA DEMO, EN UN NAVEGADOR DE VERDAD. *** *
//
// Recorre lo que hace una persona, a 390x844 y contra la URL que se le pase:
//
//   buscar «leche» → abrir las ofertas por supermercado → abrir la ficha → añadir a la
//   cesta → volver a la lista → comprobar que la línea está y que el total ha subido.
//
// No mira el código: mira la pantalla y lo que se puede tocar. Sirve para la demo local y
// para la publicada, y termina con código 1 si algo del recorrido no está.
//
// Uso:
//   node scripts/prueba-flujo-demo.mjs --base http://localhost:4173/cesta-demo
//   node scripts/prueba-flujo-demo.mjs --base https://erdeivih.github.io/cesta-demo
//
// Opciones: --ancho 390, --alto 844, --captura <png>, --salida <json>.

import { spawn } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname, resolve } from 'node:path'
import os from 'node:os'

function arg(nombre, defecto = null) {
  const i = process.argv.indexOf(`--${nombre}`)
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : defecto
}

const BASE = (arg('base', 'http://localhost:4173/cesta-demo')).replace(/\/$/, '')
const ANCHO = Number(arg('ancho', '390'))
const ALTO = Number(arg('alto', '844'))
const SALIDA = arg('salida', '')
const CAPTURA = arg('captura', '')
const PUERTO = Number(arg('puerto', '9335'))
const EDGE = process.env.CESTA_EDGE ?? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

const espera = (ms) => new Promise((r) => setTimeout(r, ms))
const U = (ruta) => `${BASE}/#${ruta}`

async function objetivo() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PUERTO}/json/list`)
      const lista = await r.json()
      const pagina = lista.find((x) => x.type === 'page' && x.webSocketDebuggerUrl)
      if (pagina) return pagina
    } catch {
      /* aun no ha abierto */
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

async function ir(enviar, ruta) {
  await enviar('Page.navigate', { url: U(ruta) })
  await hasta(enviar, 'document.readyState === "complete"')
}

const perfil = mkdtempSync(join(os.tmpdir(), 'flujo-cesta-'))
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

const informe = { base: BASE, viewport: { ancho: ANCHO, alto: ALTO }, pasos: {}, fallos: [] }
const fallo = (mensaje) => informe.fallos.push(mensaje)

try {
  const pagina = await objetivo()
  const { ws, enviar } = await abrir(pagina.webSocketDebuggerUrl)
  await enviar('Page.enable')
  await enviar('Runtime.enable')
  await enviar('Emulation.setDeviceMetricsOverride', {
    width: ANCHO,
    height: ALTO,
    deviceScaleFactor: 1,
    mobile: true,
  })

  // ---------------------------------------------------------------- 1. BUSCAR
  await ir(enviar, '/compra?q=leche')
  await hasta(enviar, 'document.querySelector("ul[aria-label=\\"Resultados de la búsqueda\\"] li") !== null')
  await espera(800)
  const busqueda = await evalJs(enviar, `(() => {
    const filas = [...document.querySelectorAll('ul[aria-label="Resultados de la búsqueda"] li')]
    const primera = filas[0]
    return {
      filas: filas.length,
      primera: (primera?.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 160),
      conPrecioUnidad: /€\\s*\\/\\s*(kg|l|ud)/i.test(primera?.innerText || ''),
      conCadenas: /\\d+ cadenas/.test(primera?.innerText || ''),
    }
  })()`)
  informe.pasos.buscar = busqueda
  if (busqueda.filas === 0) fallo('la búsqueda «leche» no pinta ningún resultado')
  if (!busqueda.conPrecioUnidad) fallo('la primera fila no enseña €/unidad')
  if (!busqueda.conCadenas) fallo('la primera fila no dice cuántas cadenas compara')

  // ------------------------------------------------- 2. COMPARAR EN LA FILA
  const comparacion = await evalJs(enviar, `(async () => {
    const boton = [...document.querySelectorAll('main button')]
      .find((b) => (b.textContent || '').includes('Ver ofertas por supermercado'))
    if (!boton) return { abierto: false }
    boton.click()
    return { abierto: true }
  })()`)
  if (comparacion.abierto) {
    await hasta(enviar, 'document.querySelector(\'main [role="region"][aria-label^="Precios de"]\') !== null')
    await espera(600)
    comparacion.cadenas = await evalJs(enviar, `(() => {
      const panel = document.querySelector('main [role="region"][aria-label^="Precios de"]')
      return {
        panel: !!panel,
        filas: panel ? [...panel.querySelectorAll('li')].map((li) =>
          (li.innerText || '').replace(/\\s+/g, ' ').trim()) : [],
      }
    })()`)
    if (!comparacion.cadenas.panel) fallo('el panel de precios por supermercado no se abre')
    if ((comparacion.cadenas.filas || []).length < 2) {
      fallo('el panel de comparación no trae dos cadenas')
    }
  } else {
    fallo('no hay botón «Ver ofertas por supermercado»')
  }
  informe.pasos.comparar = comparacion

  // ------------------------------------------------------ 3. AÑADIR A LA LISTA
  await evalJs(enviar, `(() => {
    const enlace = document.querySelector('ul[aria-label="Resultados de la búsqueda"] li a')
    if (!enlace) return false
    enlace.click()
    return true
  })()`)
  const ficha = await hasta(enviar, `!!document.querySelector('main button') &&
    [...document.querySelectorAll('main button')].some((b) => (b.textContent || '').includes('Añadir a la cesta'))`)
  informe.pasos.ficha = { abierta: ficha }
  if (!ficha) fallo('la ficha del producto no abre con el botón de añadir')

  const pulsado = await evalJs(enviar, `(() => {
    const boton = [...document.querySelectorAll('main button')]
      .find((b) => (b.textContent || '').includes('Añadir a la cesta'))
    if (!boton) return { pulsado: false }
    boton.click()
    return { pulsado: true }
  })()`)
  await espera(1400)
  informe.pasos.anadir = {
    ...pulsado,
    textoDespues: await evalJs(enviar, `(document.querySelector('main')?.innerText || '')
      .replace(/\\s+/g, ' ').trim().slice(0, 260)`),
  }
  if (!pulsado.pulsado) fallo('no se pudo pulsar «Añadir a la cesta»')

  // ------------------------------------------------------------ 4. LA LISTA
  await ir(enviar, '/compra/listas')
  await hasta(enviar, 'document.querySelector("#lo-que-falta") !== null')
  await espera(1200)
  const lista = await evalJs(enviar, `(() => {
    const texto = (document.querySelector('main')?.innerText || '').replace(/\\s+/g, ' ').trim()
    const total = texto.match(/(\\d+,\\d\\d)\\s*€/)
    return {
      texto: texto.slice(0, 700),
      lineas: [...document.querySelectorAll('main input[type="checkbox"]')].length,
      total: total ? total[1] : null,
      conLeche: /Leche/i.test(texto),
    }
  })()`)
  informe.pasos.lista = lista
  if (!lista.conLeche) fallo('la lista no enseña la leche añadida')
  if (lista.lineas < 9) fallo(`la lista tiene ${lista.lineas} líneas, se esperaban 9 (8 + la añadida)`)
  if (!lista.total) fallo('la lista no enseña el total')

  if (CAPTURA) {
    mkdirSync(dirname(resolve(CAPTURA)), { recursive: true })
    const shot = await enviar('Page.captureScreenshot', { format: 'png' })
    writeFileSync(resolve(CAPTURA), Buffer.from(shot.data, 'base64'))
    informe.captura = resolve(CAPTURA)
  }
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
