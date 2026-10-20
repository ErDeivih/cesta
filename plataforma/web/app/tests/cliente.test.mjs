/**
 * *** LA UNICA PUERTA AL SERVIDOR, Y EL UNICO SITIO QUE TRADUCE UN FALLO. ***
 *
 * *`cliente.ts` dice de si mismo: «El unico sitio del frontend que habla con el servidor».*
 * *Y tiene cuatro decisiones que se notan en pantalla:*
 *
 *   1. **Los parametros vacios se omiten.** *«Un `?sellos=` no es un filtro a medias: el backend lo lee
 *      como "sin filtro" y contesta otra cosa de la que parece.»*
 *   2. **Un `TypeError` es «sin red»**, y se dice sin alarma: *«esto es lo ultimo que hay en pantalla»*.
 *   3. **Un 404 no es un fallo**: es una respuesta.
 *   4. **Un 502 de Caddy no es JSON**, y sin el `try` el `SyntaxError` no diria nada util.
 *
 * *** Y no tenia pruebas. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  ErrorApi,
  esErrorApi,
  esSinRed,
  pide,
  textoDeError,
} from '../src/api/cliente.ts'

/** *`window.location.origin` hace falta para construir la URL.* */
globalThis.window = { location: { origin: 'http://localhost:8080' } }

/** *Un `fetch` de mentira que apunta lo que le piden y contesta lo que se le diga.* */
function conFetch(respuesta, { lanza = null } = {}) {
  const llamadas = []
  globalThis.fetch = async (url, opciones) => {
    llamadas.push({ url: String(url), opciones })
    if (lanza) throw lanza
    return respuesta
  }
  return llamadas
}

const ok = (cuerpo) => ({ ok: true, status: 200, json: async () => cuerpo })
const malo = (status, cuerpo) => ({ ok: false, status, json: async () => cuerpo })

// --------------------------------------------------------------- la URL ---

test('*** pide a `/api` y no a `http://localhost:8000` ***', async () => {
  // *«Con dos origenes el navegador mete CORS por medio y, el dia que haya cookies de sesion, se
  // pierden por el camino.»*
  const llamadas = conFetch(ok({ a: 1 }))
  await pide('/listas')
  assert.equal(llamadas[0].url, 'http://localhost:8080/api/listas')
})

test('*** y los parametros vacios NO se mandan ***', async () => {
  // *«Un `?sellos=` no es un filtro a medias: el backend lo lee como "sin filtro" y contesta otra cosa.»*
  const llamadas = conFetch(ok({}))
  await pide('/buscar', { q: 'arroz', sellos: '', cadenas: null, limite: undefined, ofertas: false })
  const url = new URL(llamadas[0].url)
  assert.equal(url.searchParams.get('q'), 'arroz')
  assert.equal(url.searchParams.has('sellos'), false, 'vacio no viaja')
  assert.equal(url.searchParams.has('cadenas'), false, 'null no viaja')
  assert.equal(url.searchParams.has('limite'), false, 'undefined no viaja')
  // *Pero `false` SI viaja: es un dato, no un hueco.*
  assert.equal(url.searchParams.get('ofertas'), 'false')
})

// ------------------------------------------------------- los fallos ---

test('*** un 404 es una respuesta, y se dice como tal ***', () => {
  // *«El 404 del escaner no es un fallo: es una respuesta.»*
  assert.equal(textoDeError(new ErrorApi(404, null)), 'No existe.')
})

test('*** y si el servidor explica el fallo, manda su explicacion ***', () => {
  assert.equal(textoDeError(new ErrorApi(409, 'La lista cambió mientras mirabas.')), 'La lista cambió mientras mirabas.')
})

test('un 5xx manda a mirar los registros', () => {
  assert.match(textoDeError(new ErrorApi(502, null)), /registros/i)
})

test('y cualquier otro estado se dice con su numero', () => {
  assert.match(textoDeError(new ErrorApi(418, null)), /418/)
})

test('*** un `TypeError` es «sin red», y se dice sin alarma ***', () => {
  // *«En el pasillo esto pasa.»*
  assert.equal(esSinRed(new TypeError('fetch failed')), true)
  assert.match(textoDeError(new TypeError('fetch failed')), /sin conexion/i)
  // *Y no es un error de la API: es otra cosa.*
  assert.equal(esSinRed(new ErrorApi(500, null)), false)
})

test('*** `textoDeError` nunca devuelve «undefined» ***', () => {
  for (const raro of [null, undefined, 42, 'texto', {}, []]) {
    const t = textoDeError(raro)
    assert.ok(typeof t === 'string' && t.length > 0 && !/undefined/.test(t), String(raro) + ' -> ' + t)
  }
})

// ------------------------------------------------------ lo que llega de vuelta ---

test('lo que contesta el servidor se devuelve tal cual', async () => {
  conFetch(ok({ listas: [1, 2] }))
  assert.deepEqual(await pide('/listas'), { listas: [1, 2] })
})

test('*** un 409 lanza `ErrorApi` con su estado y su detalle ***', async () => {
  conFetch(malo(409, { detail: 'El sello no cuadra.' }))
  await assert.rejects(
    () => pide('/cerrar'),
    (e) => {
      assert.ok(esErrorApi(e))
      assert.equal(e.estado, 409)
      assert.equal(e.detalle, 'El sello no cuadra.')
      return true
    },
  )
})

test('*** y un 502 de Caddy, que no es JSON, no rompe con un SyntaxError ***', async () => {
  // *«Sin esto, el `await respuesta.json()` tira un SyntaxError que no dice nada util.»*
  globalThis.fetch = async () => ({
    ok: false,
    status: 502,
    json: async () => {
      throw new SyntaxError('Unexpected token <')
    },
  })
  await assert.rejects(
    () => pide('/listas'),
    (e) => {
      assert.ok(esErrorApi(e), 'tiene que ser un ErrorApi, no un SyntaxError')
      assert.equal(e.estado, 502)
      return true
    },
  )
})

test('*** y un 422 de FastAPI con la lista de errores se lee ***', async () => {
  conFetch(malo(422, { detail: [{ msg: 'campo requerido' }, { msg: 'valor invalido' }] }))
  await assert.rejects(
    () => pide('/listas', {}),
    (e) => {
      assert.equal(e.estado, 422)
      assert.match(e.detalle, /campo requerido/)
      assert.match(e.detalle, /valor invalido/)
      return true
    },
  )
})
