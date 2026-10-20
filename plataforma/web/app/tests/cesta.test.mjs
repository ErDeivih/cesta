/**
 * *** EL SELLO DEL CIERRE: QUE SALGA DE VERDAD ES MEDIA GARANTIA. ***
 *
 * *M06 pide que cerrar dos veces no cree dos compras, y la mitad del cliente de eso es una linea:*
 *
 *   const consulta = sello ? `?sello_esperado=${encodeURIComponent(sello)}` : ''
 *
 * *** Si esa linea no manda el sello, el 409 del servidor no se dispara nunca *** *y la proteccion
 * entera es decorativa.* *Aqui se comprueba que sale, y que sale codificado.*
 *
 * *Y de paso, que sin sello NO se manda: cerrar sin sello es una peticion distinta -- la que no comprueba
 * nada -- y tiene que seguir siendo posible, porque es como se cierra cuando el cliente no tenia la
 * cotizacion a mano.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { cerrarCompra } from '../src/api/cesta.ts'

const BASE = 'http://localhost:8080'
globalThis.window = { location: { origin: BASE } }

/** *Un `fetch` que apunta la URL y contesta lo que se le diga.* */
function conFetch(cuerpo = { confirmado: true }, status = 200) {
  const llamadas = []
  globalThis.fetch = async (url, opciones) => {
    llamadas.push({ url: String(url), metodo: opciones?.method })
    return { ok: status < 400, status, json: async () => cuerpo }
  }
  return llamadas
}

test('*** con sello, la peticion LLEVA el sello ***', async () => {
  const llamadas = conFetch()
  await cerrarCompra('lista-1', 'abc123def456')
  const url = new URL(llamadas[0].url, BASE)
  assert.equal(url.searchParams.get('sello_esperado'), 'abc123def456', 'el sello tiene que viajar')
})

test('*** y va CODIFICADO, porque un sello puede traer caracteres raros ***', async () => {
  // *Si se concatenara a mano, un `&` en el sello partiria la consulta y el servidor veria otro sello.*
  const llamadas = conFetch()
  await cerrarCompra('lista-1', 'a&b=c d')
  const url = new URL(llamadas[0].url, BASE)
  assert.equal(url.searchParams.get('sello_esperado'), 'a&b=c d', 'llega entero, no partido')
})

test('*** sin sello NO se manda el parametro ***', async () => {
  // *Cerrar sin sello es la peticion que no comprueba nada, y tiene que seguir existiendo.*
  const llamadas = conFetch()
  await cerrarCompra('lista-1')
  const url = new URL(llamadas[0].url, BASE)
  assert.equal(url.searchParams.has('sello_esperado'), false, 'sin sello, sin parametro')
  await cerrarCompra('lista-1', null)
  assert.equal(new URL(llamadas[1].url, BASE).searchParams.has('sello_esperado'), false, 'null tampoco')
})

test('*** y un sello vacio tampoco: es «no lo tengo», no «comparalo con nada» ***', async () => {
  const llamadas = conFetch()
  await cerrarCompra('lista-1', '')
  assert.equal(new URL(llamadas[0].url, BASE).searchParams.has('sello_esperado'), false)
})

test('el identificador de la lista tambien se codifica', async () => {
  const llamadas = conFetch()
  await cerrarCompra('lista/1', 'x')
  assert.match(llamadas[0].url, /listas\/lista%2F1\/cerrar/, 'una barra en el id no parte la ruta')
})

test('*** el cierre es un POST ***', async () => {
  const llamadas = conFetch()
  await cerrarCompra('lista-1', 'x')
  assert.equal(llamadas[0].metodo, 'POST')
})

test('*** y un 409 al cerrar llega como error con su detalle ***', async () => {
  // *Es lo que la pantalla tiene que enseñar: «la cotizacion cambio, mira la nueva y confirma otra vez».*
  conFetch({ detail: 'El sello no cuadra.' }, 409)
  await assert.rejects(
    () => cerrarCompra('lista-1', 'viejo'),
    (e) => {
      assert.equal(e.estado, 409)
      assert.equal(e.detalle, 'El sello no cuadra.')
      return true
    },
  )
})
