/** *** CON LA ESTRUCTURA REAL DE `/api/producto`, NO CON UNA INVENTADA. ***
 *
 *  *Las pruebas de `grupo.test.mjs` pasaban objetos con `ean` y por eso **no vieron el fallo de
 *  integracion**: la pantalla pasaba `producto`, y **`producto` no trae `ean`**.*
 *
 *  *Medido el 18/10/2026: `/api/producto` devuelve un objeto `producto` de **13 claves** --*
 *  *`cantidad, comparable, fuente, grupo_id, marca, nombre, nutriscore, peso_escurrido_g,
 *  precio_cent, precio_por_escurrido, precio_unidad_cent, producto_id, unidad` --* **y ninguna es
 *  `ean`**.* *El EAN esta en cada entrada de `grupo.productos`.*
 *
 *  *Asi que aqui se monta el objeto **tal cual viene** y se comprueba que las comparaciones buenas
 *  siguen saliendo.* *Que la frase incorrecta desaparezca no es el exito: el exito es que
 *  **aparezca la correcta y no la incorrecta**.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { identidad, precioComparable, construyeComparacion, esAhorroDelElegido } from '../src/logica/grupo.ts'

// *** El objeto `producto` REAL: 13 claves, sin `ean`. ***
const PRODUCTO_API = {
  producto_id: 'dia:147509',
  fuente: 'dia',
  grupo_id: 11627,
  nombre: 'Azafrán en hebras Pote 0,4 g',
  marca: 'Pote',
  cantidad: 0.0004,
  unidad: 'kg',
  precio_cent: 275,
  precio_unidad_cent: 687500.0,
  comparable: true,
  nutriscore: null,
  peso_escurrido_g: null,
  precio_por_escurrido: false,
}

// *** Y las entradas del grupo, que SI traen `ean`. ***
const CARREFOUR_POTE = {
  fuente: 'carrefour', id_fuente: '699603651', nombre: 'Azafrán en hebra Pote sin gluten 400 mg.',
  marca: 'POTE', ean: '8412206003235', unidad: 'ud', precio_unidad_cent: 299.0,
  comparable: true, precio_por_escurrido: false,
}
const MERCADONA_HACENDADO = {
  fuente: 'mercadona', id_fuente: '8370', nombre: 'Azafrán hebra Hacendado',
  marca: 'Hacendado', ean: '8402001022050', unidad: 'kg', precio_unidad_cent: 487500.0,
  comparable: true, precio_por_escurrido: false,
}
const DIA_POTE = {
  fuente: 'dia', id_fuente: '147509', nombre: 'Azafrán en hebras Pote 0,4 g',
  marca: 'Pote', ean: '8412206003235', unidad: 'kg', precio_unidad_cent: 687500.0,
  comparable: true, precio_por_escurrido: false,
}
const GRUPO = [CARREFOUR_POTE, MERCADONA_HACENDADO, DIA_POTE]

test('el fallo que esto cubre: `producto` NO trae ean, y por eso no vale como identidad', () => {
  assert.equal(PRODUCTO_API.ean, undefined, 'si la API empieza a mandar ean, quitar esta prueba')
  assert.equal(identidad(PRODUCTO_API, CARREFOUR_POTE), 'no-verificada',
    'sin ean NO se puede afirmar que sea distinto: es «no verificado»')
  assert.equal(esAhorroDelElegido(PRODUCTO_API, DIA_POTE), false,
    'y por eso el filtro con `producto` rechazaba hasta el mismo producto')
})

test('la identidad se resuelve con el MIEMBRO del grupo, que si trae ean', () => {
  assert.equal(identidad(DIA_POTE, CARREFOUR_POTE), 'mismo', 'mismo EAN: es el mismo articulo')
  assert.equal(identidad(DIA_POTE, MERCADONA_HACENDADO), 'distinto', 'otro EAN: otro articulo')
})

test('una COINCIDENCIA EXACTA sigue apareciendo: Carrefour es el mismo Pote', () => {
  const c = construyeComparacion(DIA_POTE, GRUPO)
  assert.deepEqual(c.mismoSinComparar.filter((p) => p.fuente !== 'dia'), [CARREFOUR_POTE],
    'Carrefour es el mismo articulo y tiene que salir, no desaparecer')
})

test('una ALTERNATIVA no sustituye a la coincidencia exacta', () => {
  const c = construyeComparacion(DIA_POTE, GRUPO)
  assert.deepEqual(c.comparables.filter((p) => p.fuente !== 'dia'), [],
    'el Hacendado NO entra como comparable: otro EAN')
  assert.ok(c.distintas.some((p) => p.fuente === 'mercadona'), 'el Hacendado va a alternativas')
})

test('mismo EAN con otra base de precio NO es «producto distinto»', () => {
  assert.equal(identidad(DIA_POTE, CARREFOUR_POTE), 'mismo')
  assert.equal(precioComparable(DIA_POTE, CARREFOUR_POTE), false, 'kg frente a ud: no se resta')
})

test('una IDENTIDAD DESCONOCIDA no se declara distinta', () => {
  const sinEan = { ...CARREFOUR_POTE, ean: null }
  assert.equal(identidad(DIA_POTE, sinEan), 'no-verificada')
  const c = construyeComparacion(DIA_POTE, [sinEan])
  assert.equal(c.distintas.length, 0, 'no se puede afirmar que sea otra cosa')
  assert.deepEqual(c.sinVerificar, [sinEan], 'va a «sin identidad verificada»')
})

test('con un comparable de verdad, la frase SI sale', () => {
  const mismoKg = { ...MERCADONA_HACENDADO, ean: DIA_POTE.ean, precio_unidad_cent: 600000.0 }
  assert.equal(esAhorroDelElegido(DIA_POTE, mismoKg), true,
    'mismo EAN y misma unidad: aqui si hay una diferencia que se puede contar')
})

test('el peso escurrido no se mezcla con el neto', () => {
  const escurrido = { ...DIA_POTE, fuente: 'alcampo', precio_por_escurrido: true }
  assert.equal(identidad(DIA_POTE, escurrido), 'mismo')
  assert.equal(precioComparable(DIA_POTE, escurrido), false, 'neto contra escurrido no se resta')
})


// *** LA REGRESION QUE PEDIA EL PROPIETARIO. ***
// *El elegido es el mas barato, hay otra oferta exacta (mismo EAN, misma base) **mas cara**, y una
// alternativa **mucho mas cara**.* *La alternativa no puede cambiar ni el ahorro ni el numero de
// cadenas anunciados.*
test('una alternativa mas cara NO cambia el ahorro ni las cadenas anunciadas', () => {
  const elegido = { ...DIA_POTE, precio_unidad_cent: 500000.0, precio_cent: 200 }
  const exactaMasCara = { ...CARREFOUR_POTE, unidad: 'kg', precio_unidad_cent: 600000.0, precio_cent: 240 }
  const alternativaCarisima = { ...MERCADONA_HACENDADO, unidad: 'kg', precio_unidad_cent: 9900000.0, precio_cent: 3960 }

  const soloExacta = construyeComparacion(elegido, [exactaMasCara])
  const conAlternativa = construyeComparacion(elegido, [exactaMasCara, alternativaCarisima])

  assert.equal(conAlternativa.cadenas, soloExacta.cadenas, 'las cadenas no cambian por una alternativa')
  assert.equal(conAlternativa.cadenas, 1, 'aqui solo cuenta la cadena de la oferta exacta')
  assert.equal(conAlternativa.maximo, soloExacta.maximo, 'el maximo no cambia')
  assert.equal(conAlternativa.diferenciaPct, soloExacta.diferenciaPct, 'el porcentaje no cambia')
  assert.equal(conAlternativa.diferenciaCent, soloExacta.diferenciaCent, 'la diferencia no cambia')
  assert.equal(conAlternativa.ahorroEnvaseCent, null, 'el elegido ya es el mas barato: no hay ahorro')
})

test('la diferencia normalizada lleva su unidad y se distingue del ahorro del envase', () => {
  const elegido = { ...DIA_POTE, precio_unidad_cent: 600000.0, precio_cent: 300 }
  const masBarato = { ...CARREFOUR_POTE, unidad: 'kg', precio_unidad_cent: 500000.0, precio_cent: 250 }
  const c = construyeComparacion(elegido, [masBarato])
  assert.equal(c.unidad, 'kg', 'la base se conserva')
  assert.equal(c.diferenciaCent, 100000, 'la diferencia va POR KILO')
  assert.equal(c.ahorroEnvaseCent, 50, 'y el ahorro del envase es dinero del envase, no por kilo')
})

test('DOS BASES DESCONOCIDAS no son comparables', () => {
  const a = { ean: '8412206003235', unidad: null }
  const b = { ean: '8412206003235', unidad: null }
  assert.equal(precioComparable(a, b), false, 'no saber la base no demuestra que coincidan')
  assert.equal(esAhorroDelElegido(a, b), false)
})

test('una base ausente frente a una declarada tampoco', () => {
  assert.equal(precioComparable({ ean: '1', unidad: null }, { ean: '1', unidad: 'kg' }), false)
  assert.equal(precioComparable({ ean: '1', unidad: '' }, { ean: '1', unidad: '' }), false)
})

test('y sin base comparable no se anuncia ninguna cifra', () => {
  const sinUnidad = { ...DIA_POTE, unidad: null }
  const c = construyeComparacion(sinUnidad, [{ ...CARREFOUR_POTE, unidad: null }])
  assert.equal(c.unidad, null)
  assert.equal(c.diferenciaCent, null, 'sin base no hay diferencia que anunciar')
  assert.equal(c.ahorroEnvaseCent, null)
})
