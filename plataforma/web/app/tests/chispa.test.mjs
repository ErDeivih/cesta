/**
 * *** LA CHISPA: UN HUECO CUENTA COMO HUECO, Y TRES DIAS NO SON UNA SERIE. ***
 *
 * *`chispa.ts` dibuja la mini-serie de un producto y tiene dos decisiones que no se ven:*
 *
 *   - *«Un hueco cuenta como hueco»: un dia sin observacion **se coloca en el eje con `null`**, no se
 *     salta. Saltarlo junta dos dias que no son seguidos y la linea miente.*
 *   - *«Tres dias en `kg` y uno en `ud` son dos series pegadas, y el minimo de las dos juntas no es el
 *     minimo de nada»*: con mas de una unidad **no se dibuja**, y se dice por que.*
 *
 * *** Y no tenia pruebas. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { aMs, filasDeChispa, serieDeChispa } from '../src/logica/chispa.ts'

// -------------------------------------------------------------- las fechas ---

test('una fecha sin hora se lee como ese dia, no como otra cosa', () => {
  assert.equal(aMs('2026-10-01'), aMs('2026-10-01T00:00:00'))
})

test('*** una fecha vacia o rota no es una fecha ***', () => {
  assert.equal(aMs(''), null)
  assert.equal(aMs('no es una fecha'), null)
})

// ------------------------------------------------------------- la serie ---

test('*** un dia sin valor se coloca como HUECO, no se salta ***', () => {
  // *Saltarlo juntaria dos dias que no son seguidos, y la linea mentiria.*
  const s = serieDeChispa([
    { fecha: '2026-10-01', valor: 100 },
    { fecha: '2026-10-02', valor: null },
    { fecha: '2026-10-03', valor: 120 },
  ])
  assert.equal(s.dibujados, 3, 'los tres dias estan en el eje')
  assert.equal(s.ys.length, 3)
  assert.equal(s.ys[1], null, 'el hueco va como null')
  assert.equal(s.dibujable, true)
})

test('*** una fecha ilegible se DESCARTA y no se coloca en el eje ***', () => {
  const s = serieDeChispa([
    { fecha: '2026-10-01', valor: 100 },
    { fecha: 'no es una fecha', valor: 120 },
  ])
  assert.equal(s.sinFecha, 1, 'se cuenta aparte')
  assert.equal(s.dibujados, 1, 'y no se coloca')
})

test('sin ningun punto, no hay nada que dibujar', () => {
  const s = serieDeChispa([])
  assert.equal(s.dibujable, false)
  assert.equal(s.dibujados, 0)
})

// ------------------------------------------------- la unidad que no se mezcla ---

test('*** con DOS unidades no se dibuja, y se dice por que ***', () => {
  // *«Tres dias en kg y uno en ud son dos series pegadas, y el minimo de las dos juntas no es el
  // minimo de nada.»* *Y `api/alertas.py` dice lo mismo: «si la unidad cambio, no es una bajada».*
  const s = serieDeChispa([
    { fecha: '2026-10-01', valor: 100, unidad: 'kg' },
    { fecha: '2026-10-02', valor: 200, unidad: 'ud' },
  ])
  assert.equal(s.dibujable, false, 'dos unidades no son una serie')
  assert.deepEqual(s.unidades.sort(), ['kg', 'ud'])
  assert.ok(s.motivoUnidad, 'y hay un motivo que dar')
})

test('con UNA sola unidad si se dibuja', () => {
  const s = serieDeChispa([
    { fecha: '2026-10-01', valor: 100, unidad: 'kg' },
    { fecha: '2026-10-02', valor: 110, unidad: 'kg' },
  ])
  assert.equal(s.dibujable, true)
  assert.equal(s.motivoUnidad, null)
})

// ----------------------------------------------------------------- las filas ---

test('las filas llevan fecha legible y el valor, tambien los huecos', () => {
  const filas = filasDeChispa([
    { fecha: '2026-10-01', valor: 100 },
    { fecha: '2026-10-02', valor: null },
  ])
  assert.equal(filas.length, 2, 'el hueco tambien es una fila')
  assert.equal(filas[1].valor, null)
})
