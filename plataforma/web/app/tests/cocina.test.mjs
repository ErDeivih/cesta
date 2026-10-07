import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calcular, listaReceta, validarReceta } from '../src/estado/cocina.ts'
import { referenciaLinea } from '../src/estado/referenciaLinea.ts'

const ingrediente = { nombre: 'Arroz crudo', cantidad: 200, base: '100g', kcal: 350, proteinas: null, hidratos: 80, grasas: 0 }
const receta = { version: 1, nombre: 'Prueba', raciones: 2, ingredientes: [ingrediente] }
test('la eleccion exacta gana al grupo y funciona sin grupo', () => {
  assert.deepEqual(referenciaLinea(42, 'dia:123'), { grupo_id: null, producto_id: 'dia:123' })
  assert.deepEqual(referenciaLinea(undefined, 'dia:123'), { grupo_id: null, producto_id: 'dia:123' })
  assert.deepEqual(referenciaLinea(42), { grupo_id: 42, producto_id: null })
  assert.throws(() => referenciaLinea())
})
test('raciones y cero real', () => {
  assert.equal(calcular(receta, 1).kcal.valor, 350)
  assert.equal(calcular(receta, 1).grasas.valor, 0)
  assert.equal(calcular(receta, 1).proteinas.valor, null)
  assert.equal(calcular(receta, 1).proteinas.faltantes, 1)
})
test('subtotal no convierte ausencias en ceros conocidos', () => {
  const r = { ...receta, ingredientes: [ingrediente, { ...ingrediente, kcal: null }] }
  assert.deepEqual(calcular(r, 2).kcal, { valor: 700, faltantes: 1 })
})
test('cantidades se escalan sin conversion implicita ml/g', () => {
  assert.equal(listaReceta({ ...receta, ingredientes: [{ ...ingrediente, base: '100ml' }] }, 4), 'Arroz crudo: 400.0 ml')
})
test('JSON ajeno, infinito, negativos y unidades no admitidas fallan', () => {
  for (const r of [null, {}, { ...receta, raciones: 0 }, { ...receta, raciones: Infinity },
    { ...receta, ingredientes: [{ ...ingrediente, cantidad: -1 }] },
    { ...receta, ingredientes: [{ ...ingrediente, base: 'porcion' }] },
    { ...receta, ingredientes: [{ ...ingrediente, kcal: '100' }] }]) assert.throws(() => validarReceta(r))
})
test('apunte calculado no depende de cambios posteriores', () => {
  const n = calcular(receta, 1).kcal.valor
  const r = { ...receta, ingredientes: [{ ...ingrediente, kcal: 400 }] }
  assert.equal(n, 350)
  assert.equal(calcular(r, 1).kcal.valor, 400)
})
