#!/usr/bin/env node
// Sonda de la demo publicada: abre una URL en Edge headless (CDP crudo), a un
// tamano de movil concreto, y devuelve lo que se ve y lo que falla.
//
// Nace para el informe INFORMES/FALLO-DEMO.md: hacia falta una forma repetible
// de decir «en la URL publicada, esta pantalla pinta N productos, pide estas
// rutas y le responden 404». No sustituye a `medir-ui-cesta.mjs` (que mide la
// app de casa con sesion); esto solo mira la demo estatica.
//
// Uso:
//   node scripts/sonda-demo.mjs --url "https://.../#/compra?q=leche" \
//     --salida ../sonda.json --captura ../capturas/sonda.png
//
// Opciones: --ancho (390), --alto (844), --espera (1200 ms), --espera-selector,
// --perfil (carpeta temporal), --puerto (9334).

import { spawn } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname, resolve } from 'node:path'
import os from 'node:os'

function arg(nombre, defecto = null) {
  const i = process.argv.indexOf(`--${nombre}`)
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : defecto
}

const URL_DESTINO = arg('url')
if (!URL_DESTINO) {
  console.error('Falta --url')
  process.exit(2)
}
const ANCHO = Number(arg('ancho', '390'))
const ALTO = Number(arg('alto', '844'))
const ESPERA = Number(arg('espera', '1200'))
const SELECTOR = arg('espera-selector', '')
const CLIC = arg('clic', '')
const PANEL = arg('panel', '')
const TECLEAR = arg('teclear', '')
const ELEGIR = process.argv.includes('--elegir')
const PERFIL = arg('perfil', '')
const SALIDA = arg('salida', '')
const CAPTURA = arg('captura', '')
const PUERTO = Number(arg('puerto', '9334'))
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
      /* aun no ha abierto el puerto */
    }
    await espera(200)
  }
  throw new Error('El navegador no abrio el puerto de depuracion')
}

function abrir(wsUrl) {
  return new Promise((cumplir, fallar) => {
    const ws = new WebSocket(wsUrl)
    let siguiente = 1
    const pendientes = new Map()
    const eventos = []
    ws.addEventListener('open', () => cumplir({ ws, enviar, eventos }))
    ws.addEventListener('error', () => fallar(new Error('WebSocket no disponible')))
    ws.addEventListener('message', (e) => {
      const d = JSON.parse(e.data)
      if (d.id && pendientes.has(d.id)) {
        const { ok, ko } = pendientes.get(d.id)
        pendientes.delete(d.id)
        d.error ? ko(new Error(d.error.message)) : ok(d.result)
      } else if (d.method) eventos.push(d)
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
  if (r.exceptionDetails) throw new Error('JS: ' + JSON.stringify(r.exceptionDetails).slice(0, 500))
  return r.result.value
}

async function hasta(enviar, expresion, intentos = 60, cada = 250) {
  for (let i = 0; i < intentos; i++) {
    try {
      if (await evalJs(enviar, expresion)) return true
    } catch {
      /* la pagina puede estar navegando */
    }
    await espera(cada)
  }
  return false
}

const MEDIR = () => {
  const main = document.querySelector('main') || document.body
  const filasEl =
    document.querySelector('ul[aria-label="Resultados de la búsqueda"]') ||
    document.querySelector('.tabla-scroll tbody')
  const filas = filasEl ? [...filasEl.querySelectorAll('li, tr')] : []
  const visibles = filas.filter((f) => {
    const r = f.getBoundingClientRect()
    return r.top < innerHeight && r.bottom > 0 && r.width > 0 && r.height > 0
  })
  const euroUnidad = /(\d+[.,]\d+)\s*€\s*\/\s*(kg|g|100\s*g|l|ml|ud|unidad|docena|m)\b/i
  const conUnidad = [...document.querySelectorAll('main *')].filter(
    (el) => el.children.length === 0 && euroUnidad.test(el.textContent || ''),
  )
  const texto = (main.innerText || '').replace(/\s+/g, ' ').trim()
  return {
    titulo: document.title,
    url: location.href,
    hash: location.hash,
    textoPrimeraPantalla: texto.slice(0, 700),
    filasResultados: filas.length,
    filasVisibles: visibles.length,
    primerosProductos: filas.slice(0, 6).map((f) => (f.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 90)),
    conPrecioPorUnidad: conUnidad.length,
    ejemplosPrecioUnidad: conUnidad.slice(0, 4).map((el) => (el.textContent || '').trim().slice(0, 30)),
    scrollHorizontal: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    altoContenido: Math.round((document.scrollingElement || document.documentElement).scrollHeight),
    hayBuscador: !!document.querySelector('main input[type="search"], main [role="combobox"]'),
    demoApiInstalada: !!window.__cestaDemoApi,
  }
}

const perfil = PERFIL ? resolve(PERFIL) : mkdtempSync(join(os.tmpdir(), 'sonda-cesta-'))
if (PERFIL) mkdirSync(perfil, { recursive: true })
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

let informe
try {
  const pagina = await objetivo()
  const { ws, enviar, eventos } = await abrir(pagina.webSocketDebuggerUrl)
  await enviar('Page.enable')
  await enviar('Runtime.enable')
  await enviar('Network.enable')
  await enviar('Emulation.setDeviceMetricsOverride', {
    width: ANCHO,
    height: ALTO,
    deviceScaleFactor: 1,
    mobile: true,
  })

  const inicio = Date.now()
  await enviar('Page.navigate', { url: URL_DESTINO })
  await hasta(enviar, 'document.readyState === "complete"')
  if (SELECTOR) {
    await hasta(
      enviar,
      `!!document.querySelector(${JSON.stringify(SELECTOR)})`,
      60,
      250,
    )
  }
  await espera(ESPERA)

  const medida = await evalJs(enviar, `(${MEDIR.toString()})()`)

  // *Una acción de verdad, si se pide: pulsar lo que contenga `--clic` y leer el panel
  // que abra. Es lo que convierte «la fila tiene un botón» en «el botón enseña los precios
  // de cada cadena».*
  let accion = null
  if (TECLEAR) {
    // *Teclear de verdad en el combobox de la lista: es la única forma de comprobar que el
    // typeahead pregunta al catálogo y que las sugerencias llegan sin backend.*
    accion = await evalJs(enviar, `(async () => {
      const campo = document.querySelector('main input[role="combobox"]')
      if (!campo) return { escribio: false }
      campo.focus()
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
      setter?.call(campo, ${JSON.stringify(TECLEAR)})
      campo.dispatchEvent(new Event('input', { bubbles: true }))
      return { escribio: true, texto: campo.value }
    })()`)
    await espera(1400)
    const opciones = await evalJs(enviar, `(() => {
      const lista = document.querySelector('[role="listbox"]')
      const items = [...(lista ? lista.querySelectorAll('[role="option"]') : [])]
      return {
        hayLista: !!lista,
        cuantas: items.length,
        textos: items.slice(0, 8).map((li) =>
          (li.innerText || '').replace(/\\s+/g, ' ').trim()),
      }
    })()`)
    accion = { ...accion, opciones }
    if (ELEGIR && opciones.cuantas > 0) {
      accion.elegido = await evalJs(enviar, `(() => {
        const item = document.querySelector('[role="listbox"] [role="option"]')
        if (!item) return { pulsado: false }
        item.click()
        return { pulsado: true, texto: (item.innerText || '').replace(/\\s+/g, ' ').trim() }
      })()`)
      await espera(1600)
      accion.despues = await evalJs(enviar, `(() => {
        const cajas = [...document.querySelectorAll('main input[type="checkbox"]')]
        const nombres = [...document.querySelectorAll('main li')]
          .map((li) => (li.innerText || '').replace(/\\s+/g, ' ').trim())
          .filter((t) => t && t.length < 120)
        return {
          casillas: cajas.length,
          lineas: nombres.slice(0, 20),
        }
      })()`)
    }
  }
  if (CLIC) {
    accion = await evalJs(enviar, `(() => {
      const boton = [...document.querySelectorAll('main button')]
        .find((b) => (b.textContent || '').includes(${JSON.stringify(CLIC)}))
      if (!boton) return { pulsado: false }
      boton.click()
      return { pulsado: true, texto: (boton.textContent || '').trim() }
    })()`)
    if (accion.pulsado && PANEL) {
      await hasta(enviar, `!!document.querySelector(${JSON.stringify(PANEL)})`, 20, 250)
      await espera(600)
      const panel = await evalJs(enviar, `(() => {
        const el = document.querySelector(${JSON.stringify(PANEL)})
        return el ? {
          existe: true,
          texto: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 900),
          filas: [...el.querySelectorAll('li')].map((li) =>
            (li.innerText || '').replace(/\\s+/g, ' ').trim()).slice(0, 12),
        } : { existe: false }
      })()`)
      accion = { ...accion, panel }
    } else if (accion.pulsado) {
      // *Un respiro y se lee lo que ha cambiado: un botón que dice «Guardado» o una línea
      // nueva. Sin esto solo se sabe que el clic llegó, no que hizo algo.*
      await espera(1200)
      accion = {
        ...accion,
        despuesTexto: await evalJs(enviar, `(() => ({
          texto: (document.querySelector('main')?.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 600),
          botones: [...document.querySelectorAll('main button')].map((b) =>
            (b.innerText || '').replace(/\\s+/g, ' ').trim()).filter(Boolean).slice(0, 12),
        }))()`),
      }
    }
  }

  const noOk = eventos
    .filter((e) => e.method === 'Network.responseReceived')
    .map((e) => e.params.response)
    .filter((r) => r.status >= 400)
    .map((r) => ({ url: r.url, estado: r.status, tipo: r.mimeType }))
  const api = eventos
    .filter((e) => e.method === 'Network.responseReceived')
    .map((e) => e.params.response)
    .filter((r) => /\/api\//.test(r.url))
    .map((r) => ({ url: r.url, estado: r.status }))
  const errores = eventos
    .filter((e) => e.method === 'Runtime.exceptionThrown')
    .map((e) => e.params.exceptionDetails.text)
    .slice(0, 10)

  informe = {
    cuando: new Date().toISOString(),
    urlPedida: URL_DESTINO,
    viewport: { ancho: ANCHO, alto: ALTO },
    milisegundos: Date.now() - inicio,
    ...medida,
    accion,
    api: { llamadas: api.length, rutas: api.slice(0, 20) },
    noOk,
    erroresConsola: errores,
  }

  if (CAPTURA) {
    mkdirSync(dirname(CAPTURA), { recursive: true })
    const shot = await enviar('Page.captureScreenshot', { format: 'png' })
    writeFileSync(CAPTURA, Buffer.from(shot.data, 'base64'))
    informe.captura = CAPTURA
  }
  ws.close()
} finally {
  nav.kill()
  if (!PERFIL) {
    try {
      rmSync(perfil, { recursive: true, force: true })
    } catch {
      /* el perfil es temporal; si queda, no rompe nada */
    }
  }
}

const texto = JSON.stringify(informe, null, 2)
if (SALIDA) {
  mkdirSync(dirname(SALIDA), { recursive: true })
  writeFileSync(SALIDA, texto + '\n')
}
console.log(texto)
