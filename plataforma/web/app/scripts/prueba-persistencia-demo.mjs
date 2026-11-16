#!/usr/bin/env node
// *** LA LISTA Y LOS FAVORITOS SOBREVIVEN A RECARGAR. *** *
//
// Lo que se comprueba, en un navegador de verdad y contra la URL que se le pase:
//
//   1. La lista de la semana empieza con sus 8 líneas.
//   2. Se añade «arroz» desde el typeahead: la línea entra y el total sube.
//   3. Se recarga la página: la línea SIGUE ahí (IndexedDB, no memoria).
//   4. Se guarda un favorito en la ficha de un producto y se recarga: sigue guardado.
//   5. La pantalla de favoritos lo enseña.
//
// Termina con código 1 si cualquiera de los cinco pasos no se cumple.
//
// Uso:
//   node scripts/prueba-persistencia-demo.mjs --base https://erdeivih.github.io/cesta-demo

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
const SAIDA = arg('salida', '')
const PUERTO = Number(arg('puerto', '9336'))
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

async function ir(enviar, ruta) {
  await enviar('Page.navigate', { url: `${BASE}/#${ruta}` })
  await hasta(enviar, 'document.readyState === "complete"')
}

async function recargar(enviar) {
  await enviar('Page.reload', { ignoreCache: true })
  await hasta(enviar, 'document.readyState === "complete"')
}

/** *Lo que dice la lista: cuántas casillas (líneas), el total y el texto de la cabecera.* */
async function leerLista(enviar) {
  return evalJs(enviar, `(() => {
    const texto = (document.querySelector('main')?.innerText || '').replace(/\\s+/g, ' ').trim()
    const total = texto.match(/PRECIO ESTIMADO\\s*(\\d+,\\d\\d)\\s*€/)
    return {
      lineas: document.querySelectorAll('main input[type="checkbox"]').length,
      total: total ? total[1] : null,
      cabecera: texto.slice(0, 120),
    }
  })()`)
}

const perfil = mkdtempSync(join(os.tmpdir(), 'persistencia-cesta-'))
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

  // 1. La lista de la semana.
  await ir(enviar, '/compra/listas')
  await hasta(enviar, 'document.querySelector("main input[type=checkbox]") !== null')
  await espera(1200)
  const antes = await leerLista(enviar)
  informe.pasos.listaInicial = antes
  if (antes.lineas < 8) fallo(`la lista inicial tiene ${antes.lineas} líneas, se esperaban 8`)

  // 2. Añadir «arroz» desde el typeahead.
  await evalJs(enviar, `(() => {
    const campo = document.querySelector('main input[role="combobox"]')
    if (!campo) return false
    campo.focus()
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
    setter?.call(campo, 'arroz')
    campo.dispatchEvent(new Event('input', { bubbles: true }))
    return true
  })()`)
  await espera(1400)
  const opciones = await evalJs(enviar, `(() => {
    const items = [...document.querySelectorAll('[role="listbox"] [role="option"]')]
    return { cuantas: items.length, primera: (items[0]?.innerText || '').replace(/\\s+/g, ' ').trim() }
  })()`)
  informe.pasos.sugerencia = opciones
  if (opciones.cuantas === 0) fallo('el typeahead no encontró «arroz»')
  await evalJs(enviar, `(() => {
    const item = document.querySelector('[role="listbox"] [role="option"]')
    if (!item) return false
    item.click()
    return true
  })()`)
  await espera(1600)
  const despues = await leerLista(enviar)
  informe.pasos.listaTrasAnadir = despues
  if (despues.lineas !== antes.lineas + 1) {
    fallo(`tras añadir hay ${despues.lineas} líneas, se esperaban ${antes.lineas + 1}`)
  }
  if (!(Number(String(despues.total).replace(',', '.')) > Number(String(antes.total).replace(',', '.')))) {
    fallo(`el total no subió al añadir: ${antes.total} -> ${despues.total}`)
  }

  // 3. Recargar: la línea sigue.
  await recargar(enviar)
  await hasta(enviar, 'document.querySelector("main input[type=checkbox]") !== null')
  await espera(1400)
  const trasRecarga = await leerLista(enviar)
  informe.pasos.listaTrasRecarga = trasRecarga
  if (trasRecarga.lineas !== despues.lineas) {
    fallo(`tras recargar hay ${trasRecarga.lineas} líneas, se esperaban ${despues.lineas}`)
  }

  // 4. Guardar un favorito y recargar.
  await ir(enviar, '/compra/comparar/11627')
  await hasta(enviar, `[...document.querySelectorAll('main button')].some((b) => (b.textContent || '').includes('Guardar'))`)
  await espera(1000)
  const guardado = await evalJs(enviar, `(() => {
    const boton = [...document.querySelectorAll('main button')]
      .find((b) => (b.textContent || '').trim() === 'Guardar')
    if (!boton) return { pulsado: false }
    boton.click()
    return { pulsado: true }
  })()`)
  await espera(1400)
  informe.pasos.favorito = guardado
  if (!guardado.pulsado) fallo('no apareció el botón «Guardar» en la ficha')
  await recargar(enviar)
  await hasta(enviar, `[...document.querySelectorAll('main button')].some((b) => /Guardado|Guardar/.test(b.textContent || ''))`)
  await espera(1200)
  const trasRecargaFavorito = await evalJs(enviar, `(() => {
    const boton = [...document.querySelectorAll('main button')]
      .find((b) => /Guardado|Guardar/.test((b.textContent || '').trim()))
    return { texto: boton ? (boton.textContent || '').trim() : null }
  })()`)
  informe.pasos.favoritoTrasRecarga = trasRecargaFavorito
  if (trasRecargaFavorito.texto !== 'Guardado') {
    fallo(`el favorito no siguió guardado tras recargar: «${trasRecargaFavorito.texto}»`)
  }

  // 5. La pantalla de favoritos lo enseña.
  await ir(enviar, '/compra/favoritos')
  await hasta(enviar, 'document.querySelector("main") !== null')
  await espera(1600)
  const favoritos = await evalJs(enviar, `(() => {
    const texto = (document.querySelector('main')?.innerText || '').replace(/\\s+/g, ' ').trim()
    return { texto: texto.slice(0, 500), tieneElProducto: /Leche entera brik 1 l\\./i.test(texto) }
  })()`)
  informe.pasos.pantallaFavoritos = favoritos
  if (!favoritos.tieneElProducto) fallo('la pantalla de favoritos no enseña el producto guardado')

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
if (SAIDA) {
  mkdirSync(dirname(resolve(SAIDA)), { recursive: true })
  writeFileSync(resolve(SAIDA), texto + '\n')
}
console.log(texto)
process.exit(informe.ok ? 0 : 1)
