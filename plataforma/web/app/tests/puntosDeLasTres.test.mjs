/**
 * **B08: los puntos de las tres series.** Y la regla que importa es una:
 *
 * > *Un dia con **varias comidas** se suma **solo si todas traen su energia**.*
 *
 * *Si a una le falta, el dia entero va a `null` -- **no a la suma de las que si**, porque **una suma parcial
 * no es «lo previsto»: es lo previsto menos algo**, y quien la leyera creeria que el dia esta cubierto.*
 * *Es la misma regla de `diario.py`: «lo que no se sabe sigue sin saberse».*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'

import { puntosObjetivo, puntosPrevistos, puntosRegistrados } from '../src/logica/puntosDeLasTres.ts'

test('lo registrado: un punto por dia, y null donde la API no sabe', () => {
  const p = puntosRegistrados([
    { fecha: '2026-10-12', kcal_conocida: 400 },
    { fecha: '2026-10-13', kcal_conocida: null },
  ])
  assert.deepEqual(p, [
    { fecha: '2026-10-12', valor: 400 },
    { fecha: '2026-10-13', valor: null },
  ])
})

test('lo previsto: dos comidas el mismo dia se suman', () => {
  const p = puntosPrevistos([
    { fecha: '2026-10-12', conocido: { kcal: 300 }, cobertura: {}, lineas: [], receta_id: 1, version: 1, comensales: 2, completo: true },
    { fecha: '2026-10-12', conocido: { kcal: 200 }, cobertura: {}, lineas: [], receta_id: 2, version: 1, comensales: 2, completo: true },
  ])
  assert.deepEqual(p, [{ fecha: '2026-10-12', valor: 500 }])
})

test('lo previsto: si a una comida le falta la energia, el dia va a null y NO a la suma parcial', () => {
  const p = puntosPrevistos([
    { fecha: '2026-10-12', conocido: { kcal: 300 }, cobertura: {}, lineas: [], receta_id: 1, version: 1, comensales: 2, completo: true },
    { fecha: '2026-10-12', conocido: { kcal: null }, cobertura: {}, lineas: [], receta_id: 2, version: 1, comensales: 2, completo: false },
  ])
  // ***Null, y no 300*** -- *que se leeria como el dia entero.*
  assert.deepEqual(p, [{ fecha: '2026-10-12', valor: null }])
})

test('lo previsto: el orden no cambia el resultado', () => {
  const sinDato = { fecha: '2026-10-12', conocido: { kcal: null }, cobertura: {}, lineas: [], receta_id: 2, version: 1, comensales: 2, completo: false }
  const conDato = { fecha: '2026-10-12', conocido: { kcal: 300 }, cobertura: {}, lineas: [], receta_id: 1, version: 1, comensales: 2, completo: true }
  assert.deepEqual(puntosPrevistos([sinDato, conDato]), puntosPrevistos([conDato, sinDato]))
})

test('el objetivo: un dia sin objetivo no es un dia de cero', () => {
  const p = puntosObjetivo({ 'objetivo:2026-10-12': { kcal: 2000 } }, ['2026-10-12', '2026-10-13'])
  // ***El 13 sale con `null`, y no con 0.***
  assert.deepEqual(p, [
    { fecha: '2026-10-12', valor: 2000 },
    { fecha: '2026-10-13', valor: null },
  ])
})

test('el objetivo: sin preferencias, todos null', () => {
  assert.deepEqual(puntosObjetivo(null, ['2026-10-12']), [{ fecha: '2026-10-12', valor: null }])
  assert.deepEqual(puntosObjetivo(undefined, ['2026-10-12']), [{ fecha: '2026-10-12', valor: null }])
})

test('el objetivo: una clave con forma rara no se toma por un numero', () => {
  // *Y si alguien guardara otra cosa bajo `objetivo:<fecha>`, **no se dibuja un numero inventado**.*
  const p = puntosObjetivo({ 'objetivo:2026-10-12': { kcal: 'dos mil' } }, ['2026-10-12'])
  assert.deepEqual(p, [{ fecha: '2026-10-12', valor: null }])
})
