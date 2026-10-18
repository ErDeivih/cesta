/** *** EL MISMO ARTICULO NO ES «EL MISMO GRUPO DE EQUIVALENCIAS». ***
 *
 *  *Caso real, `dia/147509`, azafran Pote de 0,4 g:*
 *
 *      elegido    dia:147509   EAN 8412206003235  Pote       kg
 *      carrefour  699603651    EAN 8412206003235  Pote       ud    <- mismo articulo, otra unidad
 *      mercadona  8370         EAN 8402001022050  Hacendado  kg    <- OTRO articulo
 *
 *  *Y la ficha decia «Cuesta un 41 % mas que en Mercadona».* *Ese 41 % es Pote contra Hacendado:
 *  **otro articulo**, otro EAN, otra marca.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { esMismoArticulo, mismosArticulos, alternativas } from '../src/logica/grupo.ts'

const POTE_DIA = { ean: '8412206003235', unidad: 'kg' }
const POTE_CARREFOUR = { ean: '8412206003235', unidad: 'ud' }
const HACENDADO = { ean: '8402001022050', unidad: 'kg' }

test('mismo EAN y misma unidad: es el mismo articulo', () => {
  assert.equal(esMismoArticulo(POTE_DIA, { ean: '8412206003235', unidad: 'kg' }), true)
})

test('el azafran Hacendado NO es el mismo articulo que el Pote, y no se resta', () => {
  assert.equal(esMismoArticulo(POTE_DIA, HACENDADO), false)
})

test('mismo EAN pero otra unidad tampoco se compara: kg frente a ud', () => {
  assert.equal(esMismoArticulo(POTE_DIA, POTE_CARREFOUR), false)
})

test('sin EAN no se afirma nada', () => {
  assert.equal(esMismoArticulo({ ean: null, unidad: 'kg' }, { ean: '8412206003235', unidad: 'kg' }), false)
  assert.equal(esMismoArticulo({ ean: '', unidad: 'kg' }, { ean: '', unidad: 'kg' }), false)
})

test('el grupo del azafran se parte como debe: cero mismos articulos comparables y dos alternativas', () => {
  const grupo = [POTE_CARREFOUR, HACENDADO, POTE_DIA]
  // *El elegido esta en la lista, y `esMismoArticulo` consigo mismo es `true`: por eso la funcion
  // devuelve el. Quien la llama tiene que quitarlo, y la ficha lo hace filtrando por fuente.*
  const mismos = mismosArticulos(POTE_DIA, grupo).filter((p) => p !== POTE_DIA)
  assert.deepEqual(mismos, [], 'ninguno se puede comparar en la misma unidad')
  // *Dos: el Hacendado (otro EAN) y Carrefour (mismo EAN, otra unidad). Ninguno de los dos
  // se puede restar, y los dos se enseñan aparte.*
  assert.equal(alternativas(POTE_DIA, grupo).length, 2, 'el Hacendado y Carrefour van aparte')
})

test('cuando hay un comparable de verdad, se encuentra', () => {
  const otro = { ean: '8412206003235', unidad: 'kg', fuente: 'carrefour' }
  assert.deepEqual(mismosArticulos(POTE_DIA, [otro, HACENDADO]), [otro])
})
