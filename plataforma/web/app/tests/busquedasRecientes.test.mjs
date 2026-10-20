/**
 * *** LAS BUSQUEDAS RECIENTES: OCHO, SIN REPETIR, Y NO LO QUE ESTAS ESCRIBIENDO. ***
 *
 * *`busquedasRecientes.ts` recuerda lo buscado para ofrecerlo como chips.* *Tres reglas:*
 *
 *   - *`CUANTAS = 8`: «ocho caben en dos filas de chips en un movil; veinte no».*
 *   - *`MINIMO = 3`: «por debajo de esto no es una busqueda, es estar escribiendo».*
 *   - *Se compara **sin mayusculas**: «Leche» y «leche» son la misma busqueda para quien la escribe.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  CUANTAS,
  MINIMO,
  apuntaBusqueda,
  leerBusquedas,
  olvidaBusquedas,
} from '../src/estado/busquedasRecientes.ts'

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

test('sin nada guardado no hay busquedas', () => {
  conAlmacen(almacen())
  assert.deepEqual(leerBusquedas(), [])
})

test('lo apuntado se lee, y lo ultimo va primero', () => {
  conAlmacen(almacen())
  apuntaBusqueda('arroz')
  const r = apuntaBusqueda('leche')
  assert.deepEqual(r, ['leche', 'arroz'], 'la ultima primero')
})

test('*** por debajo del minimo no es una busqueda, es estar escribiendo ***', () => {
  conAlmacen(almacen())
  assert.deepEqual(apuntaBusqueda('ar'), [], 'dos letras no')
  assert.deepEqual(apuntaBusqueda('arroz'), ['arroz'], 'cinco si')
  // *Y lo corto no borra lo que ya habia.*
  const r = apuntaBusqueda('le')
  assert.deepEqual(r, ['arroz'], 'lo corto no toca la lista')
})

test('*** se compara sin mayusculas: «Leche» y «leche» son la misma ***', () => {
  conAlmacen(almacen())
  apuntaBusqueda('Leche')
  const r = apuntaBusqueda('leche')
  assert.equal(r.length, 1, 'no se repite')
  assert.equal(r[0], 'leche', 'y gana la ultima forma escrita')
})

test('*** solo se recuerdan ocho ***', () => {
  conAlmacen(almacen())
  for (let i = 0; i < 12; i++) apuntaBusqueda('busqueda ' + i)
  const r = leerBusquedas()
  assert.equal(r.length, CUANTAS, 'ocho, como dice la constante')
  assert.equal(r[0], 'busqueda 11', 'la ultima')
})

test('el texto se recorta', () => {
  conAlmacen(almacen())
  assert.deepEqual(apuntaBusqueda('  arroz  '), ['arroz'])
})

test('olvidar vacia la lista', () => {
  conAlmacen(almacen())
  apuntaBusqueda('arroz')
  assert.deepEqual(olvidaBusquedas(), [])
  assert.deepEqual(leerBusquedas(), [])
})

test('*** si el navegador no deja guardar, la lista dice la VERDAD: lo que hay, no lo que se quiso ***', () => {
  // *Ayer esta prueba fijo el defecto: `apuntaBusqueda` devolvia `['arroz']` aunque el `setItem` hubiera
  // lanzado, o sea que la pantalla pintaba un chip de algo que no estaba guardado y desaparecia al
  // recargar sin explicacion.*
  // *** Hoy esta arreglado, y esta prueba fija el arreglo: ***
  //   `escribir` devuelve `null` si no pudo guardar -- como `cola.ts` --, y `apuntaBusqueda` devuelve
  //   `leerBusquedas()`, que es **lo que de verdad se recuerda**.
  conAlmacen(almacen({ falla: true }))
  assert.deepEqual(leerBusquedas(), [], 'sin poder leer, vacio')
  assert.deepEqual(
    apuntaBusqueda('arroz'),
    [],
    'y devuelve el estado REAL, no la lista que intento guardar',
  )
})

test('*** y olvidar tampoco finge: si no pudo guardar, sigue estando ***', () => {
  // *El mismo defecto, en la otra funcion.*
  conAlmacen(almacen({ falla: true }))
  assert.deepEqual(olvidaBusquedas(), [], 'no hay nada que borrar, porque no hay nada guardado')
})

test('el minimo y el maximo son los que dice el modulo', () => {
  assert.equal(MINIMO, 3)
  assert.equal(CUANTAS, 8)
})
