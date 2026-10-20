/**
 * *** LA NUTRICION DE UNA RECETA: LO QUE SE SABE, LO QUE FALTA, Y LO QUE NO SE INVENTA. ***
 *
 * *`estado/cocina.ts` valida una receta importada y calcula su nutricion por racion.*
 * *Tres decisiones que valen y no se ven:*
 *
 *   1. **Un nutriente con huecos da `valor` y `faltantes`** -- *y si no hay **ninguno** conocido, el valor
 *      es `null`, no cero.* *Un cero se lee «no tiene proteinas» y seria mentira.*
 *   2. **Escala por raciones**: *la receta es de `r.raciones`, y se piden otras.*
 *   3. **La lista no fusiona ingredientes por nombre parecido**: *«no demuestra que sean el mismo
 *      ingrediente».*
 *
 * *** Y no tenia pruebas. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { calcular, listaReceta, nutrientes, validarReceta } from '../src/estado/cocina.ts'

/** *Un ingrediente de 100 g con los nutrientes que se digan.* */
const ing = (extra = {}) => ({
  nombre: 'Arroz',
  cantidad: 100,
  base: '100g',
  kcal: 350,
  proteinas: 7,
  hidratos: 78,
  grasas: 1,
  ...extra,
})

const receta = (extra = {}) => ({
  version: 1,
  nombre: 'Arroz con cosas',
  raciones: 2,
  ingredientes: [ing()],
  ...extra,
})

// ------------------------------------------------------------------- validar ---

test('una receta bien formada pasa', () => {
  assert.ok(validarReceta(receta()))
})

test('*** lo que no es una receta se rechaza con un mensaje legible ***', () => {
  for (const roto of [null, undefined, {}, 'texto', 42, []]) {
    // *Los dos mensajes del modulo son «El archivo no contiene una receta.» y «Revisa nombre, raciones y
    // formato del archivo.»* *Un `[]` cae en el segundo: es un objeto, pero no una receta.*
    assert.throws(() => validarReceta(roto), /receta|Revisa/i, JSON.stringify(roto))
  }
})

test('*** y una receta con version o raciones mal no pasa ***', () => {
  assert.throws(() => validarReceta(receta({ version: 2 })), /Revisa/i)
  assert.throws(() => validarReceta(receta({ raciones: 0 })), /Revisa/i)
  assert.throws(() => validarReceta(receta({ raciones: -1 })), /Revisa/i)
  assert.throws(() => validarReceta(receta({ nombre: '   ' })), /Revisa/i)
})

test('*** un ingrediente con cantidad no positiva se rechaza ***', () => {
  assert.throws(() => validarReceta(receta({ ingredientes: [ing({ cantidad: 0 })] })), /ingrediente/i)
  assert.throws(() => validarReceta(receta({ ingredientes: [ing({ cantidad: -5 })] })), /ingrediente/i)
})

test('*** un nutriente que no es numero ni null se rechaza ***', () => {
  assert.throws(() => validarReceta(receta({ ingredientes: [ing({ kcal: 'muchas' })] })), /nutrientes/i)
})

test('*** pero un nutriente en `null` SI se acepta: es «no lo sabemos» ***', () => {
  assert.ok(validarReceta(receta({ ingredientes: [ing({ grasas: null })] })))
})

// ------------------------------------------------------------------- calcular ---

test('el calculo es por 100 de base y por racion', () => {
  const r = calcular(receta(), 2)
  // *100 g de arroz son 350 kcal; la receta es de 2 raciones, y se piden 2.*
  assert.equal(r.kcal.valor, 350)
  assert.equal(r.kcal.faltantes, 0)
})

test('*** pedir el doble de raciones dobla el valor ***', () => {
  assert.equal(calcular(receta(), 4).kcal.valor, 700)
})

test('*** y la mitad lo parte ***', () => {
  assert.equal(calcular(receta(), 1).kcal.valor, 175)
})

test('*** un nutriente SIN NINGUN dato da `null`, no cero ***', () => {
  // *Un cero se lee «no tiene grasas» y seria mentira: es que no se sabe.*
  const r = calcular(receta({ ingredientes: [ing({ grasas: null })] }))
  assert.equal(r.grasas.valor, null, 'sin datos, null')
  assert.equal(r.grasas.faltantes, 1, 'y se dice cuantos faltan')
})

test('*** y con algunos datos, el valor es de los que se saben y `faltantes` lo dice ***', () => {
  // *«Un total sobre la mitad de los ingredientes no es el total»: por eso van los dos juntos.*
  const r = calcular(receta({
    ingredientes: [ing({ kcal: 350 }), ing({ nombre: 'Agua', cantidad: 100, kcal: null })],
  }))
  assert.equal(r.kcal.valor, 350, 'solo cuenta el que se sabe')
  assert.equal(r.kcal.faltantes, 1, 'pero se dice que falta uno')
})

test('*** los cuatro nutrientes siempre vienen, aunque sea con null ***', () => {
  const r = calcular(receta())
  for (const k of nutrientes) {
    assert.ok(k in r, 'falta ' + k)
    assert.ok('valor' in r[k] && 'faltantes' in r[k])
  }
})

test('*** raciones imposibles se rechazan ***', () => {
  assert.throws(() => calcular(receta(), 0), /raciones/i)
  assert.throws(() => calcular(receta(), -2), /raciones/i)
})

// ------------------------------------------------------------- la lista ---

test('*** la lista escala las cantidades y no funde ingredientes parecidos ***', () => {
  // *«No fusionar por parecido de nombre: no demuestra que sean el mismo ingrediente.»*
  const r = receta({
    ingredientes: [ing({ nombre: 'Tomate', cantidad: 200 }), ing({ nombre: 'Tomate triturado', cantidad: 100 })],
  })
  const lista = listaReceta(r, 2)
  const lineas = lista.split('\n')
  assert.equal(lineas.length, 2, 'dos ingredientes, dos lineas: no se funden')
  assert.match(lineas[0], /^Tomate: 200\.0 g$/)
  assert.match(lineas[1], /^Tomate triturado: 100\.0 g$/)
})

test('y con mas raciones, las cantidades crecen', () => {
  const lista = listaReceta(receta({ raciones: 2 }), 4)
  assert.match(lista, /200\.0 g/, 'de 100 g para 2 raciones a 200 g para 4')
})

test('*** pero para 1 racion baja a la mitad ***', () => {
  assert.match(listaReceta(receta({ raciones: 2 }), 1), /50\.0 g/)
})
