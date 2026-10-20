/**
 * *** UNA VISTA CON EL MISMO NOMBRE SE SUSTITUYE. ***
 *
 * *`vistasGuardadas.ts` guarda una combinacion de filtros con un nombre.* *Dos reglas:*
 *
 *   - *«Guardar dos veces "Sin lactosa" y acabar con dos chips identicos no ayuda a nadie»:
 *     **el nombre es la clave**, y se sustituye.*
 *   - *Se guardan como mucho 40, y se quedan las ultimas.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { borrarVista, guardarVista, leerVistas } from '../src/estado/vistasGuardadas.ts'

function almacen({ falla = false } = {}) {
  const datos = new Map()
  return {
    getItem: (k) => (datos.has(k) ? datos.get(k) : null),
    setItem: (k, v) => {
      if (falla) throw new Error('sin permiso')
      datos.set(k, v)
    },
    removeItem: (k) => datos.delete(k),
  }
}
const conAlmacen = (st) => {
  globalThis.window = { localStorage: st }
}

test('sin nada guardado no hay vistas', () => {
  conAlmacen(almacen())
  assert.deepEqual(leerVistas(), [])
})

test('una vista guardada se lee con su nombre y su consulta', () => {
  conAlmacen(almacen())
  const r = guardarVista('Sin lactosa', '?sellos=sin-lactosa&cadenas=dia')
  assert.deepEqual(r, [{ nombre: 'Sin lactosa', consulta: '?sellos=sin-lactosa&cadenas=dia' }])
})

test('*** el mismo nombre SUSTITUYE, no duplica ***', () => {
  conAlmacen(almacen())
  guardarVista('Sin lactosa', '?a=1')
  const r = guardarVista('Sin lactosa', '?a=2')
  assert.equal(r.length, 1, 'un solo chip, no dos')
  assert.equal(r[0].consulta, '?a=2', 'y vale la ultima')
})

test('*** un nombre vacio no guarda nada ***', () => {
  conAlmacen(almacen())
  assert.deepEqual(guardarVista('   ', '?a=1'), [])
})

test('el nombre se recorta', () => {
  conAlmacen(almacen())
  assert.equal(guardarVista('  Ofertas  ', '?ofertas=true')[0].nombre, 'Ofertas')
})

test('borrar quita solo la que se pide', () => {
  conAlmacen(almacen())
  guardarVista('A', '?a=1')
  guardarVista('B', '?b=1')
  const r = borrarVista('A')
  assert.deepEqual(r.map((v) => v.nombre), ['B'])
})

test('*** una vista con forma invalida se descarta al leer ***', () => {
  const st = almacen()
  st.setItem(
    'cesta.vistas.v1',
    JSON.stringify([{ nombre: 'Buena', consulta: '?a=1' }, { nombre: 'Sin consulta' }, { consulta: '?b=1' }]),
  )
  conAlmacen(st)
  const r = leerVistas()
  assert.equal(r.length, 1, 'solo la que tiene nombre y consulta')
  assert.equal(r[0].nombre, 'Buena')
})

// ------------------------------------------- si no se puede guardar, se dice ---

test('*** si el navegador no deja guardar, la lista dice la VERDAD: lo que hay ***', () => {
  // *Antes `escribir` devolvia la lista aunque el `setItem` hubiera lanzado, y el comentario del modulo decia
  // «la pantalla lo dice» -- pero la pantalla no podia saberlo.*
  // *Es el mismo defecto que tenia `busquedasRecientes`, arreglado igual.*
  conAlmacen(almacen({ falla: true }))
  assert.deepEqual(guardarVista('Sin lactosa', '?a=1'), [], 'devuelve el estado REAL, no la vista que quiso guardar')
})

test('*** y borrar tampoco finge ***', () => {
  conAlmacen(almacen({ falla: true }))
  assert.deepEqual(borrarVista('A'), [], 'no hay nada que borrar, porque no hay nada guardado')
})

test('*** con el almacen bien, guardar SI devuelve lo guardado ***', () => {
  // *La otra mitad: la correccion no puede convertir el caso bueno en uno vacio.*
  conAlmacen(almacen())
  const r = guardarVista('Ofertas', '?ofertas=true')
  assert.equal(r.length, 1)
  assert.equal(r[0].nombre, 'Ofertas')
})

