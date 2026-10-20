/**
 * *** LA COLA OFFLINE, DEL LADO DEL CLIENTE: QUE SE SUBA ENTERA Y CON SU HORA. ***
 *
 * *`sincronizar` es el otro extremo de `estado/cola.ts`: lo que se guardo sin cobertura se manda de golpe
 * al volver la red.* *Su docstring dice lo que la API tiene que hacer:*
 *
 *   «La API contesta cuantos aplico y cuales fallaron -- un cambio puede referirse a una linea que la otra
 *    persona ya borro --, **y no se para por uno malo**.»
 *
 * *Aqui se comprueba lo que manda **el cliente**, que es la mitad que se puede probar sin servidor.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { sincronizar } from '../src/api/cesta.ts'

const BASE = 'http://localhost:8080'
globalThis.window = { location: { origin: BASE } }

function conFetch(cuerpo = { aplicados: 0, fallidos: [] }) {
  const llamadas = []
  globalThis.fetch = async (url, opciones) => {
    llamadas.push({ url: String(url), opciones })
    return { ok: true, status: 200, json: async () => cuerpo }
  }
  return llamadas
}

const cambio = (id, extra = {}) => ({
  id,
  momento: '2026-10-20T18:04:00.000Z',
  tachado: true,
  ...extra,
})

test('*** la cola ENTERA va en un solo POST ***', async () => {
  // *«Al volver la cobertura se sube entero»: una peticion, no una por cambio.*
  const llamadas = conFetch()
  await sincronizar('lista-1', [cambio('l-1'), cambio('l-2'), cambio('l-3')])
  assert.equal(llamadas.length, 1, 'una sola peticion')
  const cuerpo = JSON.parse(llamadas[0].opciones.body)
  assert.equal(cuerpo.length, 3, 'con los tres cambios')
})

test('*** y cada cambio lleva SU hora, la del movil ***', async () => {
  // *«Tachar a las 18:04 sin cobertura y subirlo a las 18:20 tiene que contar como las 18:04; si no, el
  // servidor se inventa el orden de los hechos.»*
  const llamadas = conFetch()
  await sincronizar('lista-1', [
    cambio('l-1', { momento: '2026-10-20T18:04:00.000Z' }),
    cambio('l-2', { momento: '2026-10-20T18:07:00.000Z' }),
  ])
  const cuerpo = JSON.parse(llamadas[0].opciones.body)
  assert.equal(cuerpo[0].momento, '2026-10-20T18:04:00.000Z')
  assert.equal(cuerpo[1].momento, '2026-10-20T18:07:00.000Z')
})

test('*** y el identificador de linea, que lo genera el cliente ***', async () => {
  const llamadas = conFetch()
  await sincronizar('lista-1', [cambio('linea-generada-en-el-movil')])
  const cuerpo = JSON.parse(llamadas[0].opciones.body)
  assert.equal(cuerpo[0].id, 'linea-generada-en-el-movil', 'la clave la pone el cliente')
})

test('*** los campos opcionales NO se rellenan con ceros ni falsos ***', async () => {
  // *Un cambio que solo tacha no puede llevar `cantidad: 0`: el servidor lo leeria como «cantidad cero».*
  const llamadas = conFetch()
  await sincronizar('lista-1', [cambio('l-1')])
  const cuerpo = JSON.parse(llamadas[0].opciones.body)
  assert.equal('cantidad' in cuerpo[0], false, 'no se inventa la cantidad')
  assert.equal('nota' in cuerpo[0], false, 'ni la nota')
  assert.equal(cuerpo[0].tachado, true)
})

test('*** una cola vacia se puede subir: no es un error ***', async () => {
  const llamadas = conFetch({ aplicados: 0, fallidos: [] })
  const r = await sincronizar('lista-1', [])
  assert.equal(JSON.parse(llamadas[0].opciones.body).length, 0)
  assert.deepEqual(r, { aplicados: 0, fallidos: [] })
})

test('*** y si el servidor dice que uno fallo, se devuelve tal cual ***', async () => {
  // *«No se para por uno malo»: los demas se aplicaron, y la pantalla tiene que poder contarlo.*
  conFetch({
    aplicados: 2,
    fallidos: [{ id: 'l-3', motivo: 'la linea ya no existe' }],
  })
  const r = await sincronizar('lista-1', [cambio('l-1'), cambio('l-2'), cambio('l-3')])
  assert.equal(r.aplicados, 2)
  assert.equal(r.fallidos.length, 1)
  assert.equal(r.fallidos[0].id, 'l-3')
  assert.match(r.fallidos[0].motivo, /ya no existe/)
})

test('*** el identificador de la lista se codifica en la ruta ***', async () => {
  const llamadas = conFetch()
  await sincronizar('lista/1', [])
  assert.match(llamadas[0].url, /listas\/lista%2F1\/sincronizar/)
})

test('y manda JSON, no un formulario', async () => {
  const llamadas = conFetch()
  await sincronizar('lista-1', [cambio('l-1')])
  assert.match(llamadas[0].opciones.headers['Content-Type'], /application\/json/)
  assert.equal(llamadas[0].opciones.method, 'POST')
})
