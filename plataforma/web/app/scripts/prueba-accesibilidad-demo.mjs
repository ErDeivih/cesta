#!/usr/bin/env node
// *** ACCESIBILIDAD DE LA DEMO: TECLADO Y FOCO. *** *
//
// Comprueba lo que se puede medir sin axe:
//   - el enlace «Saltar al contenido» es lo primero que recibe el foco;
//   - al pulsarlo, el foco va al `main` y la ruta no se rompe (HashRouter);
//   - hay anillo de foco visible;
//   - no hay `tabindex` positivos;
//   - todas las imágenes tienen `alt` (vacío si son decorativas);
//   - los controles tienen nombre accesible.
//
// Uso: node scripts/prueba-accesibilidad-demo.mjs --base https://erdeivih.github.io/cesta-demo

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
const PUERTO = Number(arg('puerto', '9339'))
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

const perfil = mkdtempSync(join(os.tmpdir(), 'a11y-cesta-'))
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
  await enviar('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  })
  await enviar('Page.navigate', { url: `${BASE}/#/compra/listas` })
  await hasta(enviar, 'document.readyState === "complete"')
  await espera(3000)

  const estructura = await evalJs(enviar, `(() => {
    const skip = document.querySelector('a[href="#contenido"]')
    const main = document.querySelector('main#contenido')
    const focusables = [...document.querySelectorAll('a[href], button, input, select, textarea, summary, [tabindex]')]
      .filter((el) => !el.disabled && el.tabIndex >= 0)
    const positivos = [...document.querySelectorAll('[tabindex]')]
      .map((el) => Number(el.getAttribute('tabindex')))
      .filter((n) => n > 0)
    const imgs = [...document.querySelectorAll('img')].map((img) => ({
      src: img.getAttribute('src')?.slice(0, 60) ?? '',
      alt: img.getAttribute('alt'),
    }))
    const sinNombre = focusables.filter((el) => {
      const nombre = el.getAttribute('aria-label')
        || el.getAttribute('title')
        || (el.textContent || '').trim()
        || (el.labels && [...el.labels].map((l) => l.textContent).join(' ').trim())
      return !nombre
    }).map((el) => el.tagName + ':' + (el.className || '').toString().slice(0, 40))
    return {
      haySkip: !!skip,
      primerElemento: focusables[0]?.textContent?.trim().slice(0, 40) ?? null,
      hayMain: !!main,
      mainTabIndex: main?.tabIndex ?? null,
      positivos,
      imagenesSinAlt: imgs.filter((i) => i.alt === null),
      sinNombre: sinNombre.slice(0, 10),
      cuantosFocusables: focusables.length,
    }
  })()`)
  informe.pasos.estructura = estructura
  if (!estructura.haySkip) fallo('no hay enlace «Saltar al contenido»')
  if (estructura.primerElemento !== 'Saltar al contenido') {
    fallo(`el primer focusable es «${estructura.primerElemento}», no el enlace de salto`)
  }
  if (!estructura.hayMain || estructura.mainTabIndex !== -1) {
    fallo('el main no se puede enfocar (tabIndex -1)')
  }
  if (estructura.positivos.length > 0) fallo('hay tabindex positivos: ' + estructura.positivos.join(','))
  if (estructura.imagenesSinAlt.length > 0) fallo('hay imágenes sin atributo alt')
  if (estructura.sinNombre.length > 0) fallo('controles sin nombre accesible: ' + estructura.sinNombre.join(' | '))

  // El enlace de salto se enfoca directamente: en headless, el primer Tab puede caer en el
  // cromo del navegador. Lo que se mide es que sea el primer focusable del documento (arriba)
  // y que al activarlo enfoque el main sin romper la ruta.
  await evalJs(enviar, `document.querySelector('a[href="#contenido"]').focus()`)
  await espera(300)
  const foco = await evalJs(enviar, `(() => {
    const el = document.activeElement
    const cs = el ? getComputedStyle(el) : null
    const r = el ? el.getBoundingClientRect() : null
    const reglas = [...document.styleSheets].flatMap((hoja) => {
      try { return [...hoja.cssRules].map((r) => r.cssText) } catch { return [] }
    }).join(' ')
    return {
      texto: (el?.textContent || '').trim().slice(0, 40),
      tag: el?.tagName ?? null,
      visible: r ? r.width > 0 && r.height > 0 : false,
      sombra: cs ? cs.boxShadow : null,
      outline: cs ? cs.outlineStyle + ' ' + cs.outlineWidth : null,
      hayReglaFocoVisible: /:focus-visible/.test(reglas) && /box-shadow|outline/.test(reglas),
    }
  })()`)
  informe.pasos.foco = foco
  if (foco.texto !== 'Saltar al contenido') fallo(`el foco no está en el salto: «${foco.texto}»`)
  if (!foco.visible) fallo('el enlace de salto no se hace visible al enfocarlo')
  if (!foco.hayReglaFocoVisible) fallo('no hay una regla :focus-visible en el CSS')

  // Enter en el salto: foco al main y la ruta no cambia.
  const hashAntes = await evalJs(enviar, 'location.hash')
  await enviar('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 })
  await enviar('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 })
  await espera(400)
  const salto = await evalJs(enviar, `({
    id: document.activeElement?.id ?? null,
    hash: location.hash,
  })`)
  informe.pasos.salto = { ...salto, hashAntes }
  if (salto.id !== 'contenido') fallo(`el salto no enfocó el main: ${salto.id}`)
  if (salto.hash !== hashAntes) fallo(`el salto cambió la ruta: ${hashAntes} -> ${salto.hash}`)

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
