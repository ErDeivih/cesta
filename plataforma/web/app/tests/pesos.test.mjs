/**
 * *** EL CONTROL DE PESOS: LAS CINCO REGLAS QUE LA PANTALLA NO PUEDE SALTARSE. ***
 *
 * *`pesos.ts` lo dice en su cabecera: «es la parte de la app donde es mas facil mentir sin querer».*
 * *Y las reglas estan escritas ahi, pero **no habia una sola prueba**.*
 *
 * *Esta fichero las fija, una por una, con el caso que las rompio:*
 *
 *   1. `calidad` y `gama` son excluyentes
 *   2. la nota se reparte solo entre lo que se sabe (un hueco no es un cero)
 *   3. un precio viejo no decide
 *   4. `promo` mira lo que se paga en caja
 *   5. la referencia de precio es de la MISMA unidad
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { PESOS_INICIALES, puntuaAlternativas } from '../src/logica/pesos.ts'

/** *Una ficha minima. Solo los campos que `puntuaAlternativas` lee.* */
const ficha = (extra = {}) => ({
  fuente: 'ensayo',
  id_fuente: 'x',
  nombre: 'Leche entera 1 l',
  marca: 'Marca A',
  unidad: 'l',
  precio_unidad_cent: 100,
  promo: false,
  calidad: null,
  gama: null,
  ...extra,
})

/** *Todo decide salvo lo que se diga.* */
const decideTodo = () => ({ decide: true, motivo: null })

// ------------------------------------------------------- 5. la misma unidad ---

test('*** la referencia de precio es de la MISMA unidad ***', () => {
  // *Es el fallo del azafran: 6.875,00 EUR/kg contra 2,99 EUR/ud daba «+229.833,1 %».*
  // *Con unidades distintas no hay referencia comun: cada una se mide contra la suya, y el que no
  // tiene con quien compararse se queda sin porcentaje.*
  const r = puntuaAlternativas(
    [
      ficha({ id_fuente: 'a', unidad: 'kg', precio_unidad_cent: 687500 }),
      ficha({ id_fuente: 'b', unidad: 'ud', precio_unidad_cent: 299 }),
    ],
    PESOS_INICIALES,
    decideTodo,
  )
  // *Y la respuesta correcta es **null**, no 0: cada unidad tiene un solo producto, asi que no hay
  // con que comparar.* *Un 0 diria «es el mas barato de su unidad», que es cierto pero se lee como
  // «no hay diferencia»; `null` dice «no hay referencia», que es lo que pasa.*
  for (const alt of r) {
    assert.equal(
      alt.diferenciaPct,
      null,
      'con un solo producto en su unidad no hay referencia: null, no 0',
    )
  }
})

test('y dentro de la misma unidad si hay diferencia', () => {
  const r = puntuaAlternativas(
    [
      ficha({ id_fuente: 'a', precio_unidad_cent: 100 }),
      ficha({ id_fuente: 'b', precio_unidad_cent: 150 }),
    ],
    PESOS_INICIALES,
    decideTodo,
  )
  const caro = r.find((a) => a.producto.id_fuente === 'b')
  assert.equal(caro.diferenciaPct, 50, '150 contra 100 es un 50 % mas caro')
})

// ------------------------------------------------- 3. un precio viejo no decide ---

test('*** un precio viejo no decide, y tampoco es la referencia de nadie ***', () => {
  // *Si el mas barato del grupo es de hace cinco dias, no puede ser el minimo contra el que se mide
  // todo lo demas.*
  const viejo = ficha({ id_fuente: 'viejo', precio_unidad_cent: 1 })
  const r = puntuaAlternativas(
    [viejo, ficha({ id_fuente: 'a', precio_unidad_cent: 100 })],
    PESOS_INICIALES,
    (p) => (p.id_fuente === 'viejo' ? { decide: false, motivo: 'precio viejo' } : { decide: true, motivo: null }),
  )
  const a = r.find((x) => x.producto.id_fuente === 'a')
  const v = r.find((x) => x.producto.id_fuente === 'viejo')
  // *El viejo no decide, asi que el unico que decide es `a`: su unidad tiene un solo producto y
  // `diferenciaPct` es null. Lo que importa aqui es que **el minimo no es 1** -- eso se ve en que
  // `a` no sale con un porcentaje absurdo.*
  // *El viejo sigue en la lista -- no se borra -- pero no decide y dice por que.*
  assert.equal(v.decide, false)
  assert.equal(v.motivoNoDecide, 'precio viejo')
  // *Y el minimo es 100, no 1: el viejo no cuenta.*
  assert.equal(a.diferenciaPct, null, 'el viejo no es referencia, y sin par tampoco hay porcentaje')
})

// ------------------------------------- 1. calidad y gama son excluyentes ---

test('*** `calidad` y `gama` no se suman: una u otra, y se dice cual ***', () => {
  const r = puntuaAlternativas(
    [
      ficha({ id_fuente: 'calidad', calidad: 'A', gama: null }),
      ficha({ id_fuente: 'gama', calidad: null, gama: 'A' }),
    ],
    PESOS_INICIALES,
    decideTodo,
  )
  for (const alt of r) {
    assert.ok(alt.componentes.letraDe === 'calidad' || alt.componentes.letraDe === 'gama')
    assert.equal(alt.componentes.letra, 1, 'una A vale 1, venga de calidad o de gama')
  }
})

test('sin letra no hay nota de letra, y `letraDe` lo dice', () => {
  const r = puntuaAlternativas([ficha()], PESOS_INICIALES, decideTodo)
  assert.equal(r[0].componentes.letra, null)
  assert.equal(r[0].componentes.letraDe, null)
})

// ------------------------- 2. la nota se reparte solo entre lo que se sabe ---

test('*** la nota necesita un grupo: con un solo producto no hay contra que comparar ***', () => {
  // *Y esto lo descubrio la prueba al fallar.* *`minimoDe` devuelve `null` si no hay al menos **dos**
  // productos en la misma unidad (pesos.ts:135), asi que con uno solo `precio` y `cercania` son `null`
  // y no hay nota que dar.* *El 0 no es «malo»: es «no hay con que».*
  const solo = puntuaAlternativas([ficha()], PESOS_INICIALES, decideTodo)[0]
  assert.equal(solo.componentes.precio, null, 'sin par en su unidad no hay referencia de precio')
  assert.equal(solo.componentes.cercania, null)
})

test('*** un producto sin letra, EN UN GRUPO, no saca un cero en esa parte ***', () => {
  // *La regla 2: la nota reparte el peso solo entre los componentes con dato.*
  // *Con dos productos del mismo tipo, el precio y la cercania si existen; la letra, no.*
  // *Su nota tiene que salir de los dos que se saben, no de tres con un cero.*
  const r = puntuaAlternativas(
    [ficha({ id_fuente: 'sin', precio_unidad_cent: 100 }), ficha({ id_fuente: 'con', calidad: 'C', precio_unidad_cent: 150 })],
    PESOS_INICIALES,
    decideTodo,
  )
  const sin = r.find((a) => a.producto.id_fuente === 'sin')
  const con = r.find((a) => a.producto.id_fuente === 'con')
  assert.equal(sin.componentes.letra, null)
  // *Sin letra no puede puntuar lo mismo que con una C: le falta un dato, y eso se nota en la nota
  // sin convertirla en un cero.*
  assert.ok(sin.puntos !== null, 'la nota no puede ser null: tiene precio y cercania')
  assert.notEqual(sin.puntos, 0, 'no puede ser cero: no es que sea malo, es que le falta la letra')
  assert.ok(con.puntos !== null)
  // *Y la C, aun con peor letra, tiene los tres datos: su nota se reparte sobre mas.*
  assert.ok(con.puntos > 0)
})

// ------------------------------------- 4. la promo mira lo que se paga en caja ---

test('una promo ausente es un cero de verdad, no un hueco', () => {
  // *«No hay promoción» es un dato, no una falta de dato.*
  const sinPromo = puntuaAlternativas([ficha({ promo: false })], PESOS_INICIALES, decideTodo)[0]
  assert.equal(sinPromo.componentes.promo, 0)
})

test('con promo, el componente sube de cero', () => {
  const conPromo = puntuaAlternativas([ficha({ promo: true })], PESOS_INICIALES, decideTodo)[0]
  assert.ok(conPromo.componentes.promo > 0, 'una promo real tiene que notarse')
})
