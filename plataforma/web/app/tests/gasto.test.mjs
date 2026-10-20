/**
 * *** «NULL NO ES CERO», EN EL DINERO. ***
 *
 * *`gasto.ts` lo dice en su propia cabecera:*
 *
 *   «Un periodo del que no se sabe el total **no se pinta como cero**: «0,00 €» se lee “ese mes no
 *    gaste nada”, y lo que pasa es que **no se sabe** -- y el ademas mas bajo de lo real, redondo y
 *    creible. Es la forma mas silenciosa de mentir en esta aplicacion, **y por eso la decision vive
 *    aqui, fuera de la pantalla, con sus pruebas**.»*
 *
 * *** Y no tenia ninguna. ***
 *
 * *Este fichero las pone. Y lo hace en el orden en que el error aparece: primero «¿se sabe?», luego
 * «si no se sabe, ¿que se dice?», y al final «¿como se llama el periodo?».*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  importeEnCentimos,
  textoDeLoQueFalta,
  textoDePeriodo,
  totalConocido,
} from '../src/logica/gasto.ts'

const fila = (extra = {}) => ({
  periodo: '2026-10',
  total_cent: 15000,
  compras: 3,
  con_importe: 3,
  sin_importe: 0,
  lineas_sin_precio: 0,
  completo: true,
  ...extra,
})

// ------------------------------------------- ¿se sabe el total, o no se sabe? ---

test('total conocido es total conocido', () => {
  assert.equal(totalConocido(fila()), true)
  assert.equal(importeEnCentimos(fila()), 15000)
})

test('*** un total desconocido NO es un cero: es un desconocido ***', () => {
  // *Es la regla del modulo, y la que mas se ha roto en esta aplicacion.*
  const sin = fila({ total_cent: null, completo: false })
  assert.equal(totalConocido(sin), false)
  assert.equal(importeEnCentimos(sin), null)
  // *Y lo que **no** puede pasar: que alguien lo lea como 0.*
  assert.notEqual(importeEnCentimos(sin), 0, 'desconocer no es deber cero')
})

test('*** y un total de cero SI es cero: son dos cosas distintas ***', () => {
  // *La trampa del otro lado: si de verdad se gastaron 0, hay que poder decirlo.*
  const cero = fila({ total_cent: 0, compras: 0, con_importe: 0 })
  assert.equal(totalConocido(cero), true, 'cero es un dato')
  assert.equal(importeEnCentimos(cero), 0)
})

// ------------------------------------------------------- lo que falta, y se dice ---

test('si esta completo no falta nada', () => {
  assert.equal(textoDeLoQueFalta(fila()), null)
})

test('*** lo que falta se cuenta en LINEAS, no solo en compras ***', () => {
  // *Una compra puede tener tres lineas sin precio y contar como una sola cosa.*
  const parcial = fila({ completo: false, lineas_sin_precio: 3 })
  const texto = textoDeLoQueFalta(parcial)
  assert.match(texto, /3 lineas sin precio/)
})

test('y en singular cuando es una sola linea', () => {
  const una = fila({ completo: false, lineas_sin_precio: 1 })
  assert.match(textoDeLoQueFalta(una), /^falta 1 linea sin precio$/)
})

test('sin lineas sin precio, pero con compras sin importe, se dice eso', () => {
  const sin = fila({ completo: false, lineas_sin_precio: 0, sin_importe: 2 })
  assert.match(textoDeLoQueFalta(sin), /2 compras sin importe/)
})

test('*** un periodo incompleto sin motivo que dar no se calla: no dice nada, y eso es correcto ***', () => {
  // *`completo: false` pero sin lineas ni compras pendientes es un estado raro; el modulo devuelve
  // `null` en vez de inventar un motivo.* *Se fija para que nadie lo lea como «esta completo».*
  const raro = fila({ completo: false, lineas_sin_precio: 0, sin_importe: 0 })
  assert.equal(textoDeLoQueFalta(raro), null)
  // *Y aun asi `completo` sigue siendo false: el aviso no lo cambia.*
  assert.equal(raro.completo, false)
})

// ----------------------------------------------------------- el nombre del periodo ---

test('por mes, con el nombre en castellano', () => {
  assert.equal(textoDePeriodo(fila({ periodo: '2026-10' }), false), 'octubre de 2026')
  assert.equal(textoDePeriodo(fila({ periodo: '2026-01' }), false), 'enero de 2026')
})

test('por semana, con la semana dicha', () => {
  assert.equal(textoDePeriodo(fila({ periodo: '2026-W42' }), true), '2026 · semana 42')
})

test('*** una fila sin periodo lo dice: «Sin fecha», no una fecha inventada ***', () => {
  assert.equal(textoDePeriodo(fila({ periodo: null }), false), 'Sin fecha')
  assert.equal(textoDePeriodo(fila({ periodo: null }), true), 'Sin fecha')
})
