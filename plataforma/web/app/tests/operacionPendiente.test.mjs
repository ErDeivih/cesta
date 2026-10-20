/**
 * *** REINTENTAR LO MISMO NO ES UNA OPERACION NUEVA. ***
 *
 * *`operacionPendiente.ts` es la primitiva de **idempotencia del cliente**:*
 *
 *   «Si es **lo mismo** que estaba pendiente: **la misma clave**, y un intento mas.
 *    Si es **distinto**: operacion nueva, con clave nueva. *Cambiar el formulario es cancelar lo
 *    anterior, y no hace falta un boton para eso.*»
 *
 * *Y el sello:*
 *
 *   «Dos envios con el mismo sello son **la misma operacion**. Se ordenan las claves para que el orden
 *    en que se escriban los campos no cambie la respuesta: un `JSON.stringify` a secas haria que el mismo
 *    formulario pareciera distinto segun como se construyera el objeto.»
 *
 * *** Y no tenia pruebas. ***
 *
 * *Es la mitad del cliente de lo que M06 pide con «un reintento no crea otra compra».*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { esReintento, resolver, sello } from '../src/logica/operacionPendiente.ts'

/** *Una clave nueva determinista, para no depender del azar -- el modulo la inyecta justo para eso.* */
const claves = () => {
  let n = 0
  return () => `clave-${++n}`
}

// ------------------------------------------------------------------- el sello ---

test('*** el orden de las claves no cambia el sello ***', () => {
  // *Es la regla que evita que el mismo formulario parezca distinto segun como se construya.*
  const uno = { nombre: 'Arroz', cantidad: 2 }
  const otro = { cantidad: 2, nombre: 'Arroz' }
  assert.equal(sello(uno), sello(otro), 'mismo contenido, mismo sello')
})

test('*** y un cambio de valor SI cambia el sello ***', () => {
  assert.notEqual(sello({ cantidad: 2 }), sello({ cantidad: 3 }))
  assert.notEqual(sello({ nombre: 'Arroz' }), sello({ nombre: 'Leche' }))
})

test('el sello de un objeto anidado tambien ordena', () => {
  const a = { linea: { nombre: 'Arroz', cantidad: 1 } }
  const b = { linea: { cantidad: 1, nombre: 'Arroz' } }
  assert.equal(sello(a), sello(b), 'la anidacion tambien se ordena')
})

// ------------------------------------------------------------- ¿es reintento? ---

test('lo mismo pendiente es un reintento', () => {
  const pendiente = { clave: 'k1', datos: { cantidad: 2 }, intentos: 1 }
  assert.equal(esReintento(pendiente, { cantidad: 2 }), true)
})

test('*** el mismo dato escrito en otro orden SIGUE siendo un reintento ***', () => {
  const pendiente = { clave: 'k1', datos: { nombre: 'Arroz', cantidad: 2 }, intentos: 1 }
  assert.equal(esReintento(pendiente, { cantidad: 2, nombre: 'Arroz' }), true)
})

test('*** un dato distinto NO es un reintento ***', () => {
  const pendiente = { clave: 'k1', datos: { cantidad: 2 }, intentos: 1 }
  assert.equal(esReintento(pendiente, { cantidad: 3 }), false)
})

test('sin nada pendiente, no hay reintento', () => {
  assert.equal(esReintento(null, { cantidad: 2 }), false)
})

// ------------------------------------------------------------------ resolver ---

test('*** reintentar lo mismo REUTILIZA la clave y suma un intento ***', () => {
  // *Es lo que permite que el servidor sepa que es la misma operacion y no cree otra.*
  const nueva = claves()
  const primero = resolver(null, { cantidad: 2 }, nueva)
  assert.equal(primero.intentos, 1)
  const segundo = resolver(primero, { cantidad: 2 }, nueva)
  assert.equal(segundo.clave, primero.clave, 'la misma clave: es la misma operacion')
  assert.equal(segundo.intentos, 2, 'y un intento mas')
})

test('*** cambiar el dato ES una operacion nueva, con clave nueva ***', () => {
  // *«Cambiar el formulario es cancelar lo anterior, y no hace falta un boton para eso.»*
  const nueva = claves()
  const primero = resolver(null, { cantidad: 2 }, nueva)
  const cambiado = resolver(primero, { cantidad: 5 }, nueva)
  assert.notEqual(cambiado.clave, primero.clave, 'dato distinto, clave distinta')
  assert.equal(cambiado.intentos, 1, 'operacion nueva: el contador empieza en uno')
})

test('*** y tres reintentos seguidos siguen siendo la MISMA operacion ***', () => {
  const nueva = claves()
  let p = resolver(null, { cantidad: 2 }, nueva)
  for (let i = 0; i < 3; i++) p = resolver(p, { cantidad: 2 }, nueva)
  assert.equal(p.intentos, 4, 'uno y tres reintentos')
  assert.equal(p.clave, 'clave-1', 'la clave no cambio en ningun reintento')
})

test('volver al dato anterior NO recupera la clave vieja', () => {
  // *Y es correcto: la operacion anterior ya se cerro al cambiarla. Recuperar su clave seria revivirla.*
  const nueva = claves()
  const a = resolver(null, { cantidad: 2 }, nueva)
  const b = resolver(a, { cantidad: 5 }, nueva)
  const c = resolver(b, { cantidad: 2 }, nueva)
  assert.notEqual(c.clave, a.clave, 'volver al dato anterior es una operacion nueva')
})

test('la clave nueva se genera de verdad y no se repite', () => {
  // *Sin inyectar nada: dos operaciones distintas tienen que tener dos claves distintas.*
  const a = resolver(null, { x: 1 })
  const b = resolver(null, { x: 2 })
  assert.notEqual(a.clave, b.clave)
  assert.ok(a.clave.length > 0)
})
