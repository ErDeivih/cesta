/**
 * *** QUE LISTA USA EL DIARIO, Y POR QUE NUNCA «LA PRIMERA QUE HAYA». ***
 *
 * *M03 pide «eleccion explicita de lista en Calorias».* *Lo que habia era:*
 *
 *     find(es_de_casa)?.id ?? listas.data?.[0]?.id
 *
 * *** Si no habia lista de casa, anotaba en la PRIMERA -- que puede ser la de otra persona del hogar o una de
 * ideas. *** *O sea: una compra apuntada en la lista de alguien sin que lo sepa.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { hayQueElegir, listaDelDiario } from '../src/logica/listaDelDiario.ts'

const lista = (id, casa = false) => ({ id, es_de_casa: casa })

// --------------------------------------------------------------- lo normal ---

test('sin elegir nada, manda la lista de casa', () => {
  assert.equal(listaDelDiario([lista('a'), lista('casa', true)], null), 'casa')
})

test('*** y una eleccion explicita manda sobre la de casa ***', () => {
  assert.equal(listaDelDiario([lista('a'), lista('casa', true)], 'a'), 'a')
})

// ------------------------------------------------ lo que antes estaba mal ---

test('*** SIN lista de casa, NO se coge la primera: se devuelve null ***', () => {
  // *Es el defecto de M03 contado en una asercion.* *Con tres listas sin casa, la pantalla anotaba en la
  // primera -- y esa puede ser de otra persona.*
  assert.equal(listaDelDiario([lista('a'), lista('b'), lista('c')], null), null)
})

test('*** y con dos personas en el mismo aparato, no se pisa la eleccion ***', () => {
  // *Lo que elige A no cambia lo que usa B: la eleccion se pasa como argumento, no se adivina.*
  const suyas = [lista('de-ana'), lista('de-bruno')]
  // *Sin elegir, no hay ninguna que sea de casa, asi que no se usa ninguna.*
  assert.equal(listaDelDiario(suyas, null), null)
  // *Y si Bruno elige la suya, se usa la suya.*
  assert.equal(listaDelDiario(suyas, 'de-bruno'), 'de-bruno')
})

test('*** una eleccion que ya no existe no se queda mandando ***', () => {
  // *Si borraron la lista, `elegida` sigue en el estado de la pantalla pero ya no esta en las suyas.*
  // *Usarla mandaria la compra a una lista que no existe.*
  assert.equal(listaDelDiario([lista('a'), lista('casa', true)], 'borrada'), 'casa')
})

test('sin listas, no hay lista', () => {
  assert.equal(listaDelDiario([], null), null)
  assert.equal(listaDelDiario(null, null), null)
  assert.equal(listaDelDiario(undefined, null), null)
})

// ------------------------------------------------------- ¿hay que preguntar? ---

test('*** si hay lista de casa, no se pregunta nada ***', () => {
  // *El comportamiento de siempre no cambia: quien tiene lista de casa no ve un selector nuevo.*
  assert.equal(hayQueElegir([lista('a'), lista('casa', true)]), false)
})

test('*** con una sola lista, tampoco ***', () => {
  assert.equal(hayQueElegir([lista('a')]), false)
})

test('*** y con varias sin casa, si: hay que elegir ***', () => {
  assert.equal(hayQueElegir([lista('a'), lista('b')]), true)
})

test('sin listas no hay que elegir nada: no hay donde', () => {
  assert.equal(hayQueElegir([]), false)
  assert.equal(hayQueElegir(null), false)
})
