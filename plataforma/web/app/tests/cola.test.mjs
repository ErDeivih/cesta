/**
 * *** LOS CAMBIOS QUE NO HAN LLEGADO AL SERVIDOR. ***
 *
 * *`cola.ts` guarda en el movil lo que se toca sin cobertura. Su cabecera tiene tres reglas, y las tres
 * estan aqui:*
 *
 *   1. **La hora es la del movil** (`momento`), y se pone al tocar, no al subir. *Tachar a las 18:04 sin
 *      cobertura y subirlo a las 18:20 tiene que contar como las 18:04; si no, el servidor se inventa el
 *      orden de los hechos.*
 *   2. **Un cambio por linea, gana el ultimo** -- *pero los campos se juntan: tachar y luego cambiar la
 *      cantidad son dos campos del mismo PATCH, y el segundo no puede borrar al primero.*
 *   3. *** Nada de `try/catch` tragandose fallos ***: si no se puede guardar, **se dice** (`null`), y la
 *      pantalla lo cuenta. *Una cola que no se guarda es una promesa que se pierde al cerrar la pestaña.*
 *
 * *** Y no tenia pruebas. *** *Es el punto pendiente de M15: «sincronizacion offline sin probar».*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  apuntaCambio,
  cuantosEsperan,
  leerCola,
  vaciaCola,
} from '../src/estado/cola.ts'

/** *Un `localStorage` de mentira, con la misma forma que el del navegador.* */
function almacen({ falla = false } = {}) {
  const datos = new Map()
  return {
    getItem: (k) => (datos.has(k) ? datos.get(k) : null),
    setItem: (k, v) => {
      if (falla) throw new Error('sin permiso')
      datos.set(k, v)
    },
    removeItem: (k) => datos.delete(k),
    /** *Para mirar crudo lo guardado en una prueba.* */
    _datos: datos,
  }
}

/** *Se instala antes de llamar: `cola.ts` lee `window` dentro de las funciones, no al cargar.* */
const conAlmacen = (st) => {
  globalThis.window = { localStorage: st }
}

const cambio = (lineaId, c, momento = '2026-10-20T18:04:00.000Z') => ({
  lineaId,
  cambio: c,
  momento,
})

// ------------------------------------------------------------------ lo basico ---

test('una cola vacia no tiene nada', () => {
  conAlmacen(almacen())
  assert.deepEqual(leerCola('lista-1'), [])
  assert.equal(cuantosEsperan('lista-1'), 0)
})

test('lo apuntado se lee, con su hora', () => {
  conAlmacen(almacen())
  const cola = apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  assert.equal(cola.length, 1)
  assert.equal(cola[0].lineaId, 'l-1')
  assert.equal(cola[0].cambio.tachado, true)
  assert.equal(cola[0].momento, '2026-10-20T18:04:00.000Z', 'la hora es la del movil')
})

// ------------------------------------- la regla 2: un cambio por linea, campos juntos ---

test('*** dos cambios de LA MISMA linea son UNO, el ultimo ***', () => {
  conAlmacen(almacen())
  apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  const cola = apuntaCambio('lista-1', cambio('l-1', { tachado: false }))
  assert.equal(cola.length, 1, 'no son dos cambios que subir en orden')
  assert.equal(cola[0].cambio.tachado, false, 'gana el ultimo')
})

test('*** y los CAMPOS se juntan: tachar y cambiar cantidad no se pisan ***', () => {
  // *«La cantidad y el tachado son campos distintos del mismo PATCH.»*
  conAlmacen(almacen())
  apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  const cola = apuntaCambio('lista-1', cambio('l-1', { cantidad: 3 }))
  assert.equal(cola.length, 1)
  assert.equal(cola[0].cambio.tachado, true, 'el tachado sigue')
  assert.equal(cola[0].cambio.cantidad, 3, 'y la cantidad entra')
})

test('lineas distintas son cambios distintos', () => {
  conAlmacen(almacen())
  apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  const cola = apuntaCambio('lista-1', cambio('l-2', { tachado: true }))
  assert.equal(cola.length, 2)
})

test('*** y las listas NO se mezclan ***', () => {
  conAlmacen(almacen())
  apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  apuntaCambio('lista-2', cambio('l-9', { tachado: true }))
  assert.equal(cuantosEsperan('lista-1'), 1)
  assert.equal(cuantosEsperan('lista-2'), 1)
  assert.equal(leerCola('lista-1')[0].lineaId, 'l-1')
})

// --------------------------------------------------- la regla 3: si no se guarda, se dice ---

test('*** si el navegador no deja guardar, se dice `null` y NO se finge ***', () => {
  // *En modo privado el navegador deja leer pero lanza al escribir.*
  conAlmacen(almacen({ falla: true }))
  const cola = apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  assert.equal(cola, null, 'la pantalla tiene que poder contarlo')
})

test('*** y una cola corrupta no rompe la aplicacion ***', () => {
  // *`JSON.parse` de basura no puede tumbar la lista de la compra.*
  const st = almacen()
  st.setItem('cesta.cola.v1', 'esto no es json')
  conAlmacen(st)
  assert.deepEqual(leerCola('lista-1'), [])
})

test('y un cambio con forma invalida se descarta, no se cuela', () => {
  const st = almacen()
  st.setItem('cesta.cola.v1', JSON.stringify({ 'lista-1': [{ lineaId: 'l-1' }, cambio('l-2', { tachado: true })] }))
  conAlmacen(st)
  const cola = leerCola('lista-1')
  assert.equal(cola.length, 1, 'el que no tiene hora ni cambio no entra')
  assert.equal(cola[0].lineaId, 'l-2')
})

// ------------------------------------------------------------- vaciar ---

test('*** vaciar vacia SOLO esa lista ***', () => {
  conAlmacen(almacen())
  apuntaCambio('lista-1', cambio('l-1', { tachado: true }))
  apuntaCambio('lista-2', cambio('l-9', { tachado: true }))
  vaciaCola('lista-1')
  assert.equal(cuantosEsperan('lista-1'), 0)
  assert.equal(cuantosEsperan('lista-2'), 1, 'la otra no se toca')
})
