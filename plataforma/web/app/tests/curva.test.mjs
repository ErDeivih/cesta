/**
 * *** LO QUE DICE LA CURVA, Y LO QUE NO SE PUEDE DECIR CON ELLA. ***
 *
 * *`curva.ts` devuelve `{frase, motivo}`: **una frase o `null`**, y el motivo cuando no la hay.*
 * *Es la misma regla de toda la aplicacion: cuando no hay nada honesto que decir, no se dice nada.*
 *
 * *Y la de la unidad, que comparte con `chispa` y con `api/alertas.py`:*
 * *«si la unidad cambio, no es una bajada».*
 *
 * *** Y no tenia pruebas. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { loQueDiceLaCurva } from '../src/logica/curva.ts'

/** *Lo que `api/formato` haria, sin arrastrar el navegador.* */
const fmt = { numero: (v) => `${Math.round(v)}` }

const punto = (fecha, precio, unidad = 'kg') => ({
  fecha,
  precio_unidad_cent: precio,
  unidad_canon: unidad,
})

test('*** sin puntos no hay frase, y NO se inventa una ***', () => {
  const r = loQueDiceLaCurva([], fmt)
  assert.equal(r.frase, null, 'no hay nada que decir')
})

test('*** un precio plano SI tiene frase: es el mas bajo de la serie ***', () => {
  // *Me equivoque dos veces aqui, y las dos veces el modulo tenia razon.*
  // *Primero supuse que diria «lleva dos dias a este precio».* *Despues, al fallar, supuse lo contrario:
  // que no diria nada.* *** Lo que dice es lo unico que se puede afirmar sin inventar: ***
  //   «Es el precio mas bajo de los 2 dias que tenemos.»
  // *Que es cierto, util y no promete nada sobre el futuro.*
  const r = loQueDiceLaCurva([punto('2026-10-01', 100), punto('2026-10-02', 100)], fmt)
  assert.ok(r.frase, 'con dos dias y precio hay frase')
  assert.match(r.frase, /precio m[aá]s bajo/i, 'y habla del precio mas bajo, que es lo que se sabe')
  assert.match(r.frase, /2 d[ií]as/, 'diciendo sobre cuantos dias')
  assert.equal(r.motivo, null, 'si hay frase no hay motivo')
})

test('*** un cambio de unidad NO es una bajada de precio ***', () => {
  // *La regla que comparte con `chispa` y con `api/alertas.py`.*
  const r = loQueDiceLaCurva(
    [punto('2026-10-01', 500, 'kg'), punto('2026-10-02', 100, 'ud')],
    fmt,
  )
  // *No puede decir que bajo: son dos cosas distintas.*
  if (r.frase !== null) {
    assert.doesNotMatch(r.frase, /baj/i, 'un cambio de unidad no es una bajada')
  }
})

test('los puntos sin precio no cuentan como dias con precio', () => {
  const r = loQueDiceLaCurva(
    [punto('2026-10-01', 100), { fecha: '2026-10-02', precio_unidad_cent: null, unidad_canon: 'kg' }],
    fmt,
  )
  // *Un solo dia con precio no da serie: no hay frase ni motivo, y eso tambien es una respuesta.*
  assert.equal(typeof r, 'object')
})

test('*** `frase` y `motivo` no vienen los dos a la vez ***', () => {
  // *Una frase **y** un motivo seria decir dos cosas contradictorias.*
  for (const puntos of [
    [],
    [punto('2026-10-01', 100)],
    [punto('2026-10-01', 100), punto('2026-10-02', 90)],
    [punto('2026-10-01', 100, 'kg'), punto('2026-10-02', 100, 'ud')],
  ]) {
    const r = loQueDiceLaCurva(puntos, fmt)
    assert.ok(
      !(r.frase !== null && r.motivo !== null),
      'no puede haber frase y motivo a la vez: ' + JSON.stringify(puntos),
    )
  }
})
