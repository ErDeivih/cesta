/**
 * *** UNA FICHA CONCRETA NO AUTORIZA UNA SUSTITUCION POR OTRO MIEMBRO DEL GRUPO. ***
 *
 * *Eso dice el docstring de `referenciaLinea`, y es una regla de dinero: si añades «este yogur
 * concreto», el servidor no puede cambiartelo por otro del grupo aunque sea mas barato.*
 *
 * *La funcion devuelve **una de las dos referencias**, nunca las dos: o el grupo o el producto.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { referenciaLinea } from '../src/estado/referenciaLinea.ts'

test('*** con un producto concreto, se ancla al PRODUCTO y no al grupo ***', () => {
  const r = referenciaLinea(7, 'ensayo:arroz-a')
  assert.deepEqual(r, { grupo_id: null, producto_id: 'ensayo:arroz-a' })
  // *`grupo_id: null` es lo que impide que el servidor elija otro miembro del grupo.*
  assert.equal(r.grupo_id, null)
})

test('sin producto, se ancla al grupo', () => {
  assert.deepEqual(referenciaLinea(7), { grupo_id: 7, producto_id: null })
})

test('*** y el producto GANA al grupo si vienen los dos ***', () => {
  // *Añadir una ficha concreta es una decision mas fuerte que «algo de este grupo».*
  assert.equal(referenciaLinea(7, 'ensayo:arroz-a').producto_id, 'ensayo:arroz-a')
})

test('*** sin ninguna de las dos cosas, no se inventa una referencia: se dice ***', () => {
  assert.throws(() => referenciaLinea(), /producto/i, 'no hay nada que añadir')
  assert.throws(() => referenciaLinea(undefined, undefined), /producto/i)
})
