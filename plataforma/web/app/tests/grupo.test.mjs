/**
 * *** LA COMPARACION: CUANDO DOS COSAS SE PUEDEN COMPARAR, Y CUANDO NO. ***
 *
 * *`grupo.ts` es el modulo que decide tres cosas, y las tres se han equivocado alguna vez en esta
 * aplicacion:*
 *
 *   1. **si dos fichas son el mismo articulo** (`identidad`) -- *por EAN*
 *   2. **si sus precios se pueden comparar** (`precioComparable`) -- *por unidad*
 *   3. **y si la diferencia es un ahorro del elegido** (`esAhorroDelElegido`)
 *
 * *De la 2 salio el fallo del azafran: «te ahorras 6872,01 EUR/kg» en un producto de 0,4 g.* *De la 1,
 * que un producto sin EAN se fusionara con otro.*
 *
 * *Estas pruebas fijan las tres, con los casos que ya han fallado.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  construyeComparacion,
  esAhorroDelElegido,
  identidad,
  precioComparable,
} from '../src/logica/grupo.ts'

const ficha = (extra = {}) => ({
  fuente: 'ensayo',
  id_fuente: 'a',
  nombre: 'Leche entera 1 l',
  marca: 'Marca A',
  unidad: 'l',
  precio_unidad_cent: 100,
  ...extra,
})

// ------------------------------------------------------------------ identidad ---

test('mismo EAN y misma marca es el mismo articulo', () => {
  assert.equal(identidad(ficha({ ean: '8412345678905' }), ficha({ ean: '8412345678905' })), 'mismo')
})

test('EAN distinto es distinto, aunque el nombre sea el mismo', () => {
  // *El nombre no identifica: dos fabricantes pueden llamarlo igual.*
  assert.equal(identidad(ficha({ ean: '8412345678905' }), ficha({ ean: '8412345678912' })), 'distinto')
})

test('*** SIN EAN no se puede verificar, y NO se da por el mismo ***', () => {
  // *Es el fallo que se corrigio: un producto sin EAN se fusionaba con otro por parecerse.*
  // *`no-verificada` no es `mismo` ni es `distinto`: es «no lo se», y se dice.*
  assert.equal(identidad(ficha({ ean: null }), ficha({ ean: null })), 'no-verificada')
  assert.equal(identidad(ficha({ ean: null }), ficha({ ean: '8412345678905' })), 'no-verificada')
})

// ------------------------------------------------------- comparabilidad de precio ---

test('dos precios con la misma unidad y sin escurrido se comparan', () => {
  assert.equal(precioComparable(ficha(), ficha({ id_fuente: 'b' })), true)
})

test('*** SIN UNIDAD no se comparan: `null` no es una unidad ***', () => {
  // *Es el fondo del fallo del azafran: si la unidad es `null`, no hay con que normalizar.*
  assert.equal(precioComparable(ficha({ unidad: null }), ficha({ unidad: null })), false)
  assert.equal(precioComparable(ficha({ unidad: null }), ficha()), false)
})

test('unidades distintas no se comparan', () => {
  assert.equal(precioComparable(ficha({ unidad: 'l' }), ficha({ unidad: 'kg' })), false)
})

test('la unidad se normaliza antes de comparar', () => {
  // *Dos cadenas que la escriban distinto -- con espacios -- son la misma unidad.*
  assert.equal(precioComparable(ficha({ unidad: ' l ' }), ficha({ unidad: 'l' })), true)
})

test('*** precio por escurrido y precio normal NO se comparan ***', () => {
  // *Un precio «por escurrido» y uno normal no se miden igual, aunque la unidad coincida.*
  assert.equal(
    precioComparable(ficha({ precio_por_escurrido: true }), ficha({ precio_por_escurrido: false })),
    false,
  )
  assert.equal(
    precioComparable(ficha({ precio_por_escurrido: true }), ficha({ precio_por_escurrido: true })),
    true,
  )
})

// ------------------------------------------------------------ el ahorro del elegido ---

test('el ahorro del elegido exige ser el mismo Y comparable', () => {
  const elegido = ficha({ ean: '8412345678905', precio_unidad_cent: 100 })
  const otro = ficha({ ean: '8412345678905', id_fuente: 'b', precio_unidad_cent: 90 })
  assert.equal(esAhorroDelElegido(elegido, otro), true)
})

test('*** si es otro articulo, la diferencia NO es un ahorro del elegido ***', () => {
  // *Es el defecto de la horquilla del grupo, contado en una funcion: la diferencia entre dos articulos
  // distintos no es «lo que te ahorras comprando este».*
  const elegido = ficha({ ean: '8412345678905', precio_unidad_cent: 100 })
  const otro = ficha({ ean: '8412345678912', id_fuente: 'b', precio_unidad_cent: 90 })
  assert.equal(esAhorroDelElegido(elegido, otro), false)
})

test('sin unidad, aunque sea el mismo articulo, no hay ahorro que dar', () => {
  const elegido = ficha({ ean: '8412345678905', unidad: null, precio_unidad_cent: 100 })
  const otro = ficha({ ean: '8412345678905', id_fuente: 'b', unidad: null, precio_unidad_cent: 90 })
  assert.equal(esAhorroDelElegido(elegido, otro), false)
})

// ------------------------------------------------------------------- el resumen ---

test('la comparacion separa el mismo articulo de los demas', () => {
  const elegido = ficha({ ean: '8412345678905', precio_unidad_cent: 100 })
  const r = construyeComparacion(elegido, [
    ficha({ fuente: 'dia', id_fuente: 'x', ean: '8412345678905', precio_unidad_cent: 90 }),
    ficha({ fuente: 'aldi', id_fuente: 'y', ean: '8412345678912', precio_unidad_cent: 80 }),
  ])
  // *Solo la primera es el mismo articulo; la segunda es otro, y su precio no se usa para el ahorro.*
  assert.equal(r.comparables.length, 1, 'solo la del mismo EAN es comparable')
  assert.equal(r.comparables[0].fuente, 'dia')
})

test('*** y una ficha sin EAN no entra en los comparables ***', () => {
  const elegido = ficha({ ean: '8412345678905' })
  const r = construyeComparacion(elegido, [
    ficha({ fuente: 'dia', id_fuente: 'x', ean: null, precio_unidad_cent: 50 }),
  ])
  assert.equal(r.comparables.length, 0, 'sin EAN no se puede afirmar que sea el mismo')
})
