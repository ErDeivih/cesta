/**
 * *** LA COTIZACION NUEVA QUE MANDA UN 409: SE COMPRUEBAN LOS DOS CAMPOS ANTES DE FIARSE. ***
 *
 * *El servidor contesta 409 con `{detalle, sello_visto, cotizacion_nueva}`, y `cotizacion_nueva` es el
 * resultado entero de `cotiza`.*
 *
 * *La pantalla necesita **dos** cosas de ahi: el `sello` para reintentar y el `total_cent` para enseñarlo.*
 * *** Si falta una, no hay nada que ofrecer -- y ofrecer un boton que reintenta con `undefined` seria peor
 * que no ofrecerlo. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { ErrorApi } from '../src/api/cliente.ts'
import { cotizacionDelConflicto } from '../src/logica/conflicto.ts'

const conflicto = (cotizacion_nueva) => new ErrorApi(409, 'ha cambiado', { sello_visto: 'v', cotizacion_nueva })

test('*** con sello y total, se devuelve la cotizacion ***', () => {
  const r = cotizacionDelConflicto(conflicto({ sello: 'nuevo', total_cent: 4500 }))
  assert.deepEqual(r, { sello: 'nuevo', total_cent: 4500 })
})

test('*** sin sello no se ofrece nada: no se podria reintentar ***', () => {
  for (const roto of [null, '', 42, undefined]) {
    assert.equal(cotizacionDelConflicto(conflicto({ sello: roto, total_cent: 4500 })), null, String(roto))
  }
})

test('*** y sin total tampoco: no habria nada que enseñar ***', () => {
  for (const roto of [null, undefined, '45', Number.NaN]) {
    assert.equal(cotizacionDelConflicto(conflicto({ sello: 'nuevo', total_cent: roto })), null, String(roto))
  }
})

test('*** un cero SI es un total valido ***', () => {
  // *La otra mitad de la regla de siempre: `0` es un dato, no un hueco.*
  assert.deepEqual(cotizacionDelConflicto(conflicto({ sello: 'n', total_cent: 0 })), { sello: 'n', total_cent: 0 })
})

test('*** y un error que no es 409 no trae cotizacion ***', () => {
  assert.equal(cotizacionDelConflicto(new ErrorApi(500, 'fallo')), null)
  assert.equal(cotizacionDelConflicto(new ErrorApi(404, null)), null)
})

test('*** ni un error que no es de la API ***', () => {
  assert.equal(cotizacionDelConflicto(new TypeError('sin red')), null)
  assert.equal(cotizacionDelConflicto(null), null)
  assert.equal(cotizacionDelConflicto(undefined), null)
})

test('un 409 sin cuerpo tampoco rompe', () => {
  assert.equal(cotizacionDelConflicto(new ErrorApi(409, 'ha cambiado')), null)
})
