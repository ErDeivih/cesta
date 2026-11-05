/**
 * *** «¿ESTO ESTA CARO?», CONTESTADO CON LA SERIE DE VERDAD. ***
 *
 * *La ficha del producto lleva un chip que dice **está caro** o **está bien** con su motivo
 * («el máximo de los últimos 60 días»).* *Y ese texto es una afirmación sobre el histórico, así que
 * la decisión **no se puede tomar en el JSX**:* *se prueba aquí.*
 *
 * Las cuatro reglas que fija esta prueba:
 *
 *   1. **La ventana es la que hay, no la que suena bien.** *`dias` sale de las fechas de la serie
 *      (del primer día al último, contando los dos), no de un «60» escrito a mano.*
 *   2. **Con un solo día con precio no se juzga nada.** *«El máximo de un día» no es una respuesta.*
 *   3. **Con dos unidades no se juzga.** *Es la misma regla que `curva.ts` y `api/alertas.py`: si la
 *      unidad cambió, el mínimo mezclado no significa nada.*
 *   4. **Un precio que no se movió no es «el mínimo»: es que no se movió.** *Decir «el mínimo de los
 *      últimos 3 días» con tres días al mismo precio es cierto y no informa de nada.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { veredictoDelPrecio } from '../src/logica/juicio.ts'

const punto = (fecha, precio, unidad = 'kg') => ({
  fecha,
  precio_unidad_cent: precio,
  unidad_canon: unidad,
})

test('*** el precio más alto de la serie es «está caro», y dice la ventana real ***', () => {
  const v = veredictoDelPrecio([
    punto('2026-09-07', 300),
    punto('2026-09-08', 300),
    punto('2026-09-09', 335),
  ])
  assert.ok(v, 'con tres días y precio hay veredicto')
  assert.equal(v.juicio, 'caro')
  assert.match(v.texto, /está caro/)
  assert.match(v.texto, /el máximo de los últimos 3 días/)
  assert.equal(v.minimo, 300)
  assert.equal(v.maximo, 335)
  assert.equal(v.conPrecio, 3)
})

test('*** el precio más bajo es «está bien», con su mínimo ***', () => {
  const v = veredictoDelPrecio([
    punto('2026-09-07', 335),
    punto('2026-09-08', 335),
    punto('2026-09-09', 300),
  ])
  assert.equal(v.juicio, 'barato')
  assert.match(v.texto, /está bien/)
  assert.match(v.texto, /el mínimo de los últimos 3 días/)
})

test('*** ni máximo ni mínimo: se dice eso, y no se inventa un «normal» ***', () => {
  const v = veredictoDelPrecio([
    punto('2026-09-07', 300),
    punto('2026-09-08', 335),
    punto('2026-09-09', 320),
  ])
  assert.equal(v.juicio, 'medio')
  assert.match(v.texto, /ni máximo ni mínimo de los últimos 3 días/)
})

test('*** un precio que no se ha movido no es «el mínimo» ***', () => {
  const v = veredictoDelPrecio([
    punto('2026-09-07', 300),
    punto('2026-09-08', 300),
    punto('2026-09-09', 300),
  ])
  assert.equal(v.juicio, 'medio')
  assert.match(v.texto, /sin cambios en los últimos 3 días/)
})

test('*** la ventana sale de las fechas, y los huecos se cuentan aparte ***', () => {
  // *Un día sin dato (null) es un hueco: no cuenta como día con precio, pero sí está en la ventana.*
  const v = veredictoDelPrecio([
    punto('2026-09-07', 300),
    punto('2026-09-08', null),
    punto('2026-09-10', 300),
    punto('2026-09-12', 335),
  ])
  assert.equal(v.dias, 6, 'del 7 al 12 son seis días de calendario')
  assert.equal(v.conPrecio, 3, 'tres días con precio')
  assert.equal(v.huecos, 1, 'un día sin precio')
  assert.equal(v.hasta, '2026-09-12')
})

test('*** con un solo día con precio no hay veredicto ***', () => {
  assert.equal(veredictoDelPrecio([punto('2026-09-07', 300)]), null)
  assert.equal(
    veredictoDelPrecio([punto('2026-09-07', 300), punto('2026-09-08', null)]),
    null,
    'un día con precio y un hueco siguen siendo un día con precio',
  )
})

test('*** con dos unidades no se juzga: el mínimo mezclado no es el mínimo de nada ***', () => {
  const v = veredictoDelPrecio([
    punto('2026-09-07', 500, 'kg'),
    punto('2026-09-08', 100, 'ud'),
  ])
  assert.equal(v, null)
})

test('*** una fecha ilegible no se coloca en el eje ***', () => {
  const v = veredictoDelPrecio([
    punto('', 300),
    punto('2026-09-07', 300),
    punto('2026-09-08', 335),
  ])
  assert.equal(v.dias, 2, 'la fecha vacía no estira la ventana')
  assert.equal(v.conPrecio, 2)
})
