#!/usr/bin/env node
// Mide las tres pantallas del encargo de UI de Cesta, a 390x844 (movil) y a
// 1440x900 (escritorio), con Chrome DevTools Protocol crudo contra msedge
// headless. Deja medicion.json y las capturas, con el prefijo de CESTA_PREFIJO
// (`ui-antes` por defecto, `ui-despues` para la tanda de despues).
//
// Adaptado de F:\Inforepositorios\scripts\medir-ui-movil.js, que media un sitio
// estatico por file://. Aqui el sitio es una SPA con sesion, asi que cambia:
//
//   - la URL base es el servidor de Vite (http://127.0.0.1:5173),
//   - el login se hace DENTRO de la pagina con `fetch('/api/entrar')` (Vite
//     manda /api a Caddy :8080), asi la cookie `cesta_sesion` queda en el mismo
//     origen que la app, que es como la pone la app de verdad,
//   - se miden las tres rutas del encargo y dos viewports,
//   - y se esperan los datos de cada pantalla antes de medir (si se mide el
//     esqueleto de carga, lo que se apunta no es la pantalla).
//
// NO toca src/. Escribe solo en scripts/ (este fichero), capturas/ y
// medicion.json.
//
// Uso:
//   node scripts/medir-ui-cesta.mjs
//
// Variables de entorno (todas opcionales):
//   CESTA_WEB        URL base de la app           (por defecto http://127.0.0.1:5173)
//   CESTA_USUARIO    usuario de prueba            (por defecto medicion)
//   CESTA_CLAVE      clave de prueba              (por defecto medicion2026)
//   CESTA_LISTA      id de la lista a comparar    (por defecto, la de casa)
//   CESTA_SALIDA     carpeta de medicion.json     (por defecto F:\Proyectos\cesta)
//   CESTA_CDP        puerto de depuracion         (por defecto 9333)

import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import os from 'node:os'

const BASE = process.env.CESTA_WEB ?? 'http://127.0.0.1:5173'
const USUARIO = process.env.CESTA_USUARIO ?? 'medicion'
const CLAVE = process.env.CESTA_CLAVE ?? 'medicion2026'
const LISTA_FORZADA = process.env.CESTA_LISTA ?? ''
const SALIDA = process.env.CESTA_SALIDA ?? 'F:\\Proyectos\\cesta'
const CAPTURAS = join(SALIDA, 'capturas')
// Prefijo de las capturas: `ui-antes` o `ui-despues`, para no pisar las de la
// medici.n anterior. Tambi.n sirve para el nombre de cada fichero del informe.
const PREFIJO = process.env.CESTA_PREFIJO ?? 'ui-antes'
// Y el fichero del informe, para no pisar la medida de la ronda anterior.
const SALIDA_JSON = process.env.CESTA_JSON ?? 'medicion.json'
const PUERTO = Number(process.env.CESTA_CDP ?? 9333)
const EDGE =
  process.env.CESTA_EDGE ??
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

// Los dos viewports. `mobile` cambia lo que el navegador dice de si mismo
// (matchMedia de puntero y de ancho), no solo el tamano de la ventana.
const VIEWPORTS = [
  { nombre: 'movil', ancho: 390, alto: 844, mobile: true },
  { nombre: 'escritorio', ancho: 1440, alto: 900, mobile: false },
]

// Las tres pantallas del encargo. `espera` es el selector que dice que los
// datos han llegado: sin el se mide el esqueleto, y el esqueleto no es la
// pantalla.
const RUTAS = [
  {
    clave: 'compra',
    nombre: '/compra (buscar, con el listado)',
    url: '/compra?q=leche%20entera',
    espera: [
      'ul[aria-label="Resultados de la búsqueda"] li',
      '.tabla-scroll table tbody tr',
      'main .vacio',
    ],
  },
  {
    clave: 'compra_filtros',
    nombre: '/compra con un filtro puesto (chips y cabecera compacta)',
    url: '/compra?q=leche%20entera&cadenas=dia',
    espera: ['ul[aria-label="Resultados de la búsqueda"] li', 'main .vacio'],
  },
  {
    clave: 'listas',
    nombre: '/compra/listas (la entrada de la cesta)',
    url: '/compra/listas',
    espera: ['#lo-que-falta', '#en-el-carro', 'main select[aria-label="Lista"]'],
  },
  {
    clave: 'comparar',
    nombre: '/compra/listas/:listaId/comparar (comparativa por cadena)',
    url: null, // se rellena con el id real
    espera: [
      'section[aria-label="Resumen de la comparación"]',
      '#totales-de-la-cesta',
      'main .vacio',
    ],
  },
]

const espera = (ms) => new Promise((r) => setTimeout(r, ms))

// ------------------------------------------------------------------ navegador ---

async function objetivo() {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PUERTO}/json/list`)
      const lista = await r.json()
      const pagina = lista.find((x) => x.type === 'page' && x.webSocketDebuggerUrl)
      if (pagina) return pagina
    } catch {
      /* el navegador aun no ha abierto el puerto */
    }
    await espera(250)
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
  if (r.exceptionDetails) {
    throw new Error('JS: ' + JSON.stringify(r.exceptionDetails).slice(0, 400))
  }
  return r.result.value
}

/** Reintenta una condicion en la pagina hasta que se cumpla. */
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

// ------------------------------------------------------------------- medida ---

/** La medida, entera, dentro de la pagina.
 *
 *  Se pasa la configuracion como JSON y se devuelve todo lo que el informe
 *  necesita. Nada de esto inventa: si algo no esta, vale `null` y se dice.
 */
const MEDIR = (cfg) => {
  const dentro = (r, alto) => r.top < alto && r.bottom > 0 && r.width > 0 && r.height > 0
  const recorte = (el) => {
    const r = el.getBoundingClientRect()
    return {
      top: Math.round(r.top),
      bottom: Math.round(r.bottom),
      alto: Math.round(r.height),
      ancho: Math.round(r.width),
    }
  }
  const clase = (el) =>
    (typeof el.className === 'string' ? el.className : '').split(/\s+/).slice(0, 4).join(' ')

  const raiz = document.scrollingElement || document.documentElement
  const main = document.querySelector('main#contenido') || document.querySelector('main')
  const cabeceraEl = document.querySelector('header.sticky') || document.querySelector('header')
  const cabecera = cabeceraEl ? recorte(cabeceraEl) : null

  // --- scroll horizontal: la pregunta del encargo, sin interpretaciones
  const scrollHorizontal =
    raiz.scrollWidth > document.documentElement.clientWidth + 1

  // --- barra de abajo (solo movil): lo que tapa contenido
  const barraEl = [...document.querySelectorAll('nav[aria-label="Aplicaciones"]')].find((n) =>
    getComputedStyle(n).position === 'fixed',
  )
  const barraAbajo = barraEl ? recorte(barraEl) : null

  // --- primer contenido visible: el primer trozo con texto y caja que se ve
  let primerContenido = null
  const candidatos = main ? [...main.querySelectorAll('*')] : []
  for (const el of candidatos) {
    if (el.closest('[aria-hidden="true"]')) continue
    const alto = el.getBoundingClientRect().height
    if (alto < 8) continue
    const texto = (el.innerText || '').trim()
    if (!texto) continue
    // Solo el primero de cada rama: si el padre ya cuenta, el hijo no aporta.
    if (primerContenido) break
    const r = el.getBoundingClientRect()
    primerContenido = {
      etiqueta: el.tagName.toLowerCase(),
      clase: clase(el),
      texto: texto.replace(/\s+/g, ' ').slice(0, 160),
      ...recorte(el),
      visible: dentro(r, innerHeight) && r.top >= 0,
      pegadoALaCabecera: cabecera ? r.top - cabecera.bottom : null,
    }
  }

  // --- euro por unidad (€/kg, €/l...): en el DOM y en la pantalla
  const reUnidad = /(\d+[.,]\d+)\s*€\s*\/\s*(kg|g|100\s*g|l|ml|ud|unidad|docena|m)\b/i
  const conUnidad = [...document.querySelectorAll('main *')].filter(
    (el) => el.children.length === 0 && reUnidad.test(el.textContent || ''),
  )
  const euroKg = {
    enDom: conUnidad.length,
    enPantalla: conUnidad.filter((el) => dentro(el.getBoundingClientRect(), innerHeight)).length,
    ejemplos: conUnidad.slice(0, 4).map((el) => (el.textContent || '').trim().slice(0, 40)),
    columnaVisible: [...document.querySelectorAll('main th, main span, main p')]
      .map((el) => (el.textContent || '').trim())
      .filter((t) => /^(por unidad|€\/kg|precio por unidad)$/i.test(t))
      .length,
  }

  // --- el buscador de producto de la propia lista: existe, donde y si se ve
  const cajaTypeahead = (() => {
    const campo = document.querySelector('main input[role="combobox"], main [role="combobox"]')
    if (!campo) return { existe: false }
    const r = campo.getBoundingClientRect()
    const etiqueta = campo.getAttribute('aria-label')
      || document.querySelector('label[for="' + campo.id + '"]')?.textContent?.trim()
      || ''
    return {
      existe: true,
      etiqueta: etiqueta.replace(/\s+/g, ' ').slice(0, 40),
      top: Math.round(r.top),
      enPantalla: dentro(r, innerHeight),
      deSoloLectura: campo.getAttribute('aria-disabled') === 'true' || campo.hasAttribute('readonly'),
    }
  })()

  // --- texto cortado: cajas que esconden lo que no cabe
  const cortados = []
  for (const el of [...document.querySelectorAll('main *')]) {
    const cs = getComputedStyle(el)
    if (!/hidden|clip/.test(cs.overflowX) && cs.textOverflow !== 'ellipsis') continue
    if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
      const texto = (el.textContent || '').trim().replace(/\s+/g, ' ')
      if (!texto) continue
      cortados.push({
        etiqueta: el.tagName.toLowerCase(),
        clase: clase(el),
        texto: texto.slice(0, 80),
        ocultoPx: Math.round(el.scrollWidth - el.clientWidth),
      })
      if (cortados.length >= 12) break
    }
  }

  // --- filas y tarjetas visibles
  const filasEl =
    document.querySelector('ul[aria-label="Resultados de la búsqueda"]') ||
    document.querySelector('.tabla-scroll tbody')
  const filasTotal = filasEl
    ? filasEl.querySelectorAll('li, tr').length
    : 0
  const filasVisibles = filasEl
    ? [...filasEl.querySelectorAll('li, tr')].filter((f) =>
        dentro(f.getBoundingClientRect(), innerHeight),
      ).length
    : 0
  const tarjetas = main ? [...main.querySelectorAll('section')] : []
  const tarjetasVisibles = tarjetas.filter((t) =>
    dentro(t.getBoundingClientRect(), innerHeight),
  ).length

  // --- los controles: cuantos, cuanto ocupan antes del primer producto y si alguno queda tapado
  //
  // *«Tapado» no es un adorno: es un control que se ve pero no se puede pulsar porque hay otro
  // elemento encima en el punto donde se toca. Se pregunta por el punto central con
  // `elementFromPoint`, que es lo que recibiria el dedo. Ni el propio elemento, ni un hijo ni un
  // padre cuentan como tapar.*
  const interactivos = [...document.querySelectorAll(
    'main a[href], main button, main input, main select, main textarea, main summary, main [role="button"]',
  )].filter((el) => {
    const r = el.getBoundingClientRect()
    return r.width > 1 && r.height > 1 && r.top < innerHeight && r.bottom > 0
  })
  /** Si algo es parte del chrome fijo: cabecera pegada o barra de abajo. */
  const esFija = (el) => {
    let n = el
    while (n && n !== document.body) {
      const posicion = getComputedStyle(n).position
      if (posicion === 'fixed' || posicion === 'sticky') return true
      n = n.parentElement
    }
    return false
  }
  const tapados = interactivos.filter((el) => {
    const r = el.getBoundingClientRect()
    const x = Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2))
    const y = Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2))
    const encima = document.elementFromPoint(x, y)
    if (!encima) return true
    if (encima === el || el.contains(encima) || encima.contains(el)) return false
    // *La cabecera y la barra de abajo tapan lo que queda por debajo del pliegue mientras se
    // desplaza: eso no es un control tapado por un fallo de maquetación. Solo cuenta el solape
    // dentro del contenido, que es el que deja un control visible e impulsable.*
    return !esFija(encima)
  })
  const primerProducto = document.querySelector('main ul[aria-label="Resultados de la búsqueda"] > li')
  const chips = [...document.querySelectorAll('main [role="group"][aria-label="Filtros puestos"] button')]
    .map((b) => (b.textContent || '').trim().replace(/\s+/g, ' '))

  const controles = {
    chips: { total: chips.length, textos: chips.slice(0, 8) },
    total: interactivos.length,
    tapados: tapados.length,
    tapadosDetalle: tapados.slice(0, 8).map((el) => {
      const r = el.getBoundingClientRect()
      const encima = document.elementFromPoint(
        Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2)),
        Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2)),
      )
      return {
        etiqueta: el.tagName.toLowerCase(),
        texto: (el.textContent || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '')
          .trim().replace(/\s+/g, ' ').slice(0, 40),
        por: encima ? `${encima.tagName.toLowerCase()}.${clase(encima).replace(/\s+/g, '.')}` : 'nada',
        rect: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
        scrollY: Math.round(window.scrollY),
        pila: document.elementsFromPoint(
          Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2)),
          Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2)),
        ).slice(0, 3).map((e) => `${e.tagName.toLowerCase()}.${clase(e).replace(/\s+/g, '.')}`),
      }
    }),
    primerProductoTop: primerProducto ? Math.round(primerProducto.getBoundingClientRect().top) : null,
    altoHastaPrimerProducto: primerProducto && cabecera
      ? Math.round(primerProducto.getBoundingClientRect().top - cabecera.bottom)
      : null,
  }

  // --- las lineas de la lista de la compra
  const lineasEl = document.querySelector('#lo-que-falta')
    ? [...document.querySelectorAll('#lo-que-falta ~ *, #lo-que-falta')]
    : []
  const lineas = document.querySelectorAll(
    'section[aria-labelledby="lo-que-falta"] li, section[aria-labelledby="en-el-carro"] li',
  )

  return {
    url: location.href,
    titulo: document.title,
    viewport: { ancho: innerWidth, alto: innerHeight },
    scrollHorizontal,
    scrollWidth: raiz.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    documentoAlto: raiz.scrollHeight,
    cabecera: cabecera
      ? { ...cabecera, sticky: getComputedStyle(cabeceraEl).position === 'sticky' }
      : null,
    barraAbajo,
    primerContenido,
    euroKg,
    typeahead: cajaTypeahead,
    textosCortados: cortados,
    filas: { total: filasTotal, visibles: filasVisibles, hay: !!filasEl },
    controles,
    diagnostico: {
      details: [...document.querySelectorAll('main details')].map((d) => ({
        abierto: d.open,
        texto: (d.querySelector('summary')?.textContent || '').trim().slice(0, 30),
        rect: recorte(d),
      })),
      selects: [...document.querySelectorAll('main select')].map((s) => ({
        texto: (s.textContent || '').trim().slice(0, 20),
        rect: recorte(s),
        display: getComputedStyle(s).display,
        padre: (s.parentElement?.className || '').slice(0, 60),
      })),
    },
    tarjetas: { total: tarjetas.length, visibles: tarjetasVisibles },
    lineasDeLaLista: lineas.length,
    lineas: lineasEl.length,
    carga: {
      esqueletos: document.querySelectorAll('[role="status"]').length,
      vacios: document.querySelectorAll('main .vacio, main [class*="border-dashed"]').length,
      textosDeEspera: [...document.querySelectorAll('main *')]
        .filter((e) => e.children.length === 0 && /cargando|abriendo/i.test(e.textContent || ''))
        .length,
    },
    // Lo que la propia app dice que esta pasando, en la cabecera.
    titular: (document.querySelector('main h1, header h1, h1')?.textContent || '').trim(),
    textoPrimeraPantalla: (main?.innerText || '')
      .replace(/\s+/g, ' ')
      .slice(0, 400),
  }
}

// ------------------------------------------------------------------- principal ---

async function principal() {
  mkdirSync(CAPTURAS, { recursive: true })
  const perfil = join(os.tmpdir(), 'cesta-medir-' + Date.now())
  const nav = spawn(
    EDGE,
    [
      '--headless=new',
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--hide-scrollbars',
      `--remote-debugging-port=${PUERTO}`,
      `--user-data-dir=${perfil}`,
      '--window-size=390,844',
      'about:blank',
    ],
    { stdio: 'ignore' },
  )

  const informe = {
    fecha: new Date().toISOString(),
    base: BASE,
    usuario: { usuario: USUARIO, clave: CLAVE },
    navegador: 'msedge --headless=new (CDP crudo)',
    viewports: VIEWPORTS.map((v) => ({ nombre: v.nombre, ancho: v.ancho, alto: v.alto })),
    rutas: {},
    resumen: {},
    bloqueos: [],
  }

  try {
    const p = await objetivo()
    const { ws, enviar, eventos } = await abrir(p.webSocketDebuggerUrl)
    await enviar('Page.enable')
    await enviar('Runtime.enable')
    await enviar('Network.enable')

    // ---- sesion: entrar por la API, desde la pagina, como lo hace la app
    await enviar('Page.navigate', { url: BASE + '/' })
    await hasta(enviar, 'document.readyState === "complete"')
    await espera(800)

    const entrar = await evalJs(
      enviar,
      `(async () => {
        const cuerpo = JSON.stringify({ usuario: ${JSON.stringify(USUARIO)}, clave: ${JSON.stringify(CLAVE)} })
        let r = await fetch('/api/entrar', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: cuerpo, credentials: 'same-origin',
        })
        if (!r.ok) {
          r = await fetch('/api/registrarse', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: ${JSON.stringify(USUARIO)}, nombre: 'Medicion', clave: ${JSON.stringify(CLAVE)} }),
            credentials: 'same-origin',
          })
        }
        const yo = await fetch('/api/yo', { credentials: 'same-origin' }).then((x) => x.json())
        return { estadoEntrar: r.status, yo }
      })()`,
    )
    informe.sesion = entrar
    if (!entrar?.yo?.usuario) {
      throw new Error('No hay sesion despues de entrar (mira /api/entrar y /api/registrarse)')
    }

    // ---- la lista a comparar: la de casa, o la primera
    const listas = await evalJs(
      enviar,
      `fetch('/api/listas', { credentials: 'same-origin' }).then(r => r.json())`,
    )
    const lista =
      (LISTA_FORZADA && (listas.listas ?? []).find((l) => l.id === LISTA_FORZADA)) ||
      (listas.listas ?? []).find((l) => l.es_de_casa) ||
      (listas.listas ?? [])[0] ||
      null
    if (!lista) throw new Error('La cuenta de prueba no tiene ninguna lista; crea una antes.')
    informe.lista = { id: lista.id, nombre: lista.nombre, es_de_casa: !!lista.es_de_casa, lineas: lista.lineas }
    for (const r of RUTAS) {
      if (r.clave === 'comparar') r.url = `/compra/listas/${lista.id}/comparar`
    }

    // ---- por cada viewport, las tres rutas
    for (const vp of VIEWPORTS) {
      await enviar('Emulation.setDeviceMetricsOverride', {
        width: vp.ancho,
        height: vp.alto,
        deviceScaleFactor: 1,
        mobile: vp.mobile,
      })
      informe.rutas[vp.nombre] = {}

      for (const ruta of RUTAS) {
        const antes = eventos.length
        await enviar('Page.navigate', { url: BASE + ruta.url })
        await hasta(enviar, 'document.readyState === "complete"')
        // Esperar a que la pantalla tenga datos, no el esqueleto.
        const listo = await hasta(
          enviar,
          `(() => { const s = ${JSON.stringify(ruta.espera)}; return s.some(x => document.querySelector(x)); })()`,
          80,
          250,
        )
        // Y un respiro para las peticiones que llegan despues del primer pintado
        // (el precio por unidad, el reparto por tiendas).
        await espera(listo ? 1400 : 800)

        const medida = await evalJs(enviar, `(${MEDIR.toString()})(${JSON.stringify({})})`)

        // *Y la acción nueva: desplegar las ofertas del primer producto.* Se pulsa de verdad y
        // se lee el panel: es la única forma de probar que abre, que pide el grupo y que ordena.
        let interaccion = null
        if (ruta.clave === 'compra') {
          interaccion = await evalJs(enviar, `(() => {
            const boton = [...document.querySelectorAll('main button')]
              .find((b) => /Ver ofertas por supermercado/.test(b.textContent || ''))
            if (!boton) return { hayBoton: false }
            boton.click()
            return { hayBoton: true }
          })()`)
          // *El grupo se pide al abrir: se espera a que el panel exista (la primera llamada
          // puede tardar más de un segundo con la API recién levantada).*
          await hasta(
            enviar,
            'document.querySelector(\'main [role="region"][aria-label^="Precios de"]\') !== null',
            24,
            250,
          )
          const ofertas = await evalJs(enviar, `(() => {
            const panel = document.querySelector('main [role="region"][aria-label^="Precios de"]')
            if (!panel) return { hayPanel: false }
            const filas = [...panel.querySelectorAll('li')].map((li) =>
              (li.textContent || '').trim().replace(/\\s+/g, ' '))
            return { hayPanel: true, filas: filas.slice(0, 8) }
          })()`)
          interaccion = { ...interaccion, ...ofertas }
          // *Y se vuelve a plegar antes de la captura: la foto es de la pantalla de compra, no
          // del panel abierto; y de paso se comprueba que el botón también cierra.*
          await evalJs(enviar, `(() => {
            const boton = [...document.querySelectorAll('main button')]
              .find((b) => /Ocultar ofertas por supermercado/.test(b.textContent || ''))
            boton?.click()
            return true
          })()`)
          await espera(200)
        }

        // Respuestas de API de esta ruta: las que no son 2xx se apuntan.
        const api = eventos
          .slice(antes)
          .filter((e) => e.method === 'Network.responseReceived')
          .map((e) => e.params.response)
          .filter((r) => /\/api\//.test(r.url))
          .map((r) => ({ url: r.url.replace(BASE, ''), estado: r.status }))
        const apiNoOk = api.filter((r) => r.estado >= 400)
        const erroresConsola = eventos
          .slice(antes)
          .filter((e) => e.method === 'Runtime.exceptionThrown')
          .map((e) => e.params.exceptionDetails.text)

        const nombreFichero = `${PREFIJO}-${ruta.clave}-${vp.ancho}x${vp.alto}.png`
        const shot = await enviar('Page.captureScreenshot', { format: 'png' })
        writeFileSync(join(CAPTURAS, nombreFichero), Buffer.from(shot.data, 'base64'))

        // Y una captura de la pagina entera, para ver la pantalla completa en el
        // informe. Solo en movil: es donde el scroll importa.
        let ficheroCompleto = null
        if (vp.mobile) {
          const metricas = await enviar('Page.getLayoutMetrics')
          const alto = Math.ceil(metricas.cssContentSize.height)
          const shotCompleto = await enviar('Page.captureScreenshot', {
            format: 'png',
            captureBeyondViewport: true,
            clip: { x: 0, y: 0, width: vp.ancho, height: alto, scale: 1 },
          })
          ficheroCompleto = `${PREFIJO}-${ruta.clave}-${vp.ancho}x${vp.alto}-completa.png`
          writeFileSync(join(CAPTURAS, ficheroCompleto), Buffer.from(shotCompleto.data, 'base64'))
        }

        informe.rutas[vp.nombre][ruta.clave] = {
          ruta: ruta.url,
          nombre: ruta.nombre,
          datosListos: listo,
          titulo: medida.titular,
          captura: nombreFichero,
          capturaCompleta: ficheroCompleto,
          api: { llamadas: api.length, noOk: apiNoOk },
          erroresConsola,
          interaccion,
          ...medida,
        }
        console.log(
          `${vp.nombre} ${ruta.clave}: scrollH=${medida.scrollHorizontal} ` +
            `cabecera=${medida.cabecera?.alto ?? '-'} ` +
            `primerContenido=${medida.primerContenido?.top ?? '-'} ` +
            `€/ud=${medida.euroKg.enPantalla}/${medida.euroKg.enDom} ` +
            `filas=${medida.filas.visibles}/${medida.filas.total}`,
        )
      }
    }

    // ---- el resumen que se lee de un vistazo
    for (const vp of VIEWPORTS) {
      const deViewport = informe.rutas[vp.nombre]
      informe.resumen[vp.nombre] = {
        scrollHorizontal: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [k, v.scrollHorizontal]),
        ),
        altoDeCabecera: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [k, v.cabecera?.alto ?? null]),
        ),
        primerContenidoVisible: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [
            k,
            v.primerContenido
              ? { texto: v.primerContenido.texto.slice(0, 60), top: v.primerContenido.top }
              : null,
          ]),
        ),
        euroPorUnidadEnPantalla: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [k, v.euroKg.enPantalla]),
        ),
        filasVisibles: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [k, v.filas.visibles]),
        ),
        textosCortados: Object.fromEntries(
          Object.entries(deViewport).map(([k, v]) => [k, v.textosCortados.length]),
        ),
      }
    }

    writeFileSync(join(SALIDA, SALIDA_JSON), JSON.stringify(informe, null, 2) + '\n', 'utf8')
    console.log('\nEscrito ' + join(SALIDA, SALIDA_JSON))
    console.log('Capturas en ' + CAPTURAS)
    ws.close()
  } finally {
    nav.kill()
    await espera(600)
    try {
      rmSync(perfil, { recursive: true, force: true })
    } catch {
      /* el perfil temporal se queda; no es un fallo de la medida */
    }
  }
}

principal().catch((e) => {
  console.error('Fallo la medicion:', e.message)
  process.exit(1)
})
