import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calcular, listaReceta, validarReceta } from '../src/estado/cocina.ts'
import { referenciaLinea } from '../src/estado/referenciaLinea.ts'
import { aMs, filasDeChispa, serieDeChispa } from '../src/logica/chispa.ts'

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
// --- G05: la chispa no puede dibujar lo que no se observo --------------------
// Las tres reglas son del documento y se fijan aqui, porque `tsc` verde dice que compila y no que
// acierte. La primera es la que mas importa: **un hueco no se conecta**.
test('un hueco en la serie NO se conecta', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 100 },
    { fecha: '2026-01-02', valor: null },
    { fecha: '2026-01-03', valor: 120 },
  ])
  assert.deepEqual(s.ys, [100, null, 120])
  assert.equal(s.dibujados, 3, 'un hueco cuenta como punto: esta en la serie, sin valor')
  assert.equal(s.dibujable, true)
  assert.equal(s.sinFecha, 0)
})

test('una serie vacia NO dice «solo un dia»', () => {
  const s = serieDeChispa([])
  assert.equal(s.dibujable, false)
  assert.equal(s.total, 0)
  assert.equal(s.dibujados, 0)
})

test('una fecha ilegible no se coloca en 1970, se descarta', () => {
  assert.equal(aMs(''), null)
  assert.equal(aMs('no-es-una-fecha'), null)
  assert.equal(aMs('2026-01-01'), Date.parse('2026-01-01T00:00:00'))
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 100 },
    { fecha: 'no-es-una-fecha', valor: 999 },
  ])
  assert.equal(s.dibujados, 1)
  assert.equal(s.sinFecha, 1, 'y se cuenta: una ausencia se declara, no se disimula')
  assert.deepEqual(s.ys, [100])
})

test('un valor no finito es un hueco, no un cero', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: Number.NaN },
    { fecha: '2026-01-02', valor: Number.POSITIVE_INFINITY },
  ])
  assert.deepEqual(s.ys, [null, null])
  assert.equal(s.dibujados, 2)
})
test('la tabla lista los huecos, y los lee como «sin dato»', () => {
  const filas = filasDeChispa([
    { fecha: '2026-01-01', valor: 1.5 },
    { fecha: '2026-01-02', valor: null },
    { fecha: '2026-01-03', valor: 1.8 },
  ], '€')
  assert.equal(filas.length, 3, 'el hueco es una fila, no se omite')
  assert.equal(filas[1].valor, null)
  assert.equal(filas[1].texto, 'sin dato')
  assert.equal(filas[0].texto, '1.5 €')
  assert.equal(filas[2].texto, '1.8 €')
})
test('una serie que mezcla unidades NO se dibuja como una sola linea', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: '2026-01-02', valor: 155, unidad: 'kg' },
    { fecha: '2026-01-03', valor: 90, unidad: 'ud' },
  ])
  assert.equal(s.dibujable, false, 'kg y ud no son la misma escala')
  assert.deepEqual(s.unidades, ['kg', 'ud'])
  assert.match(s.motivoUnidad, /cambió en el histórico \(kg, ud\)/)
})

test('una serie con una sola unidad SI se dibuja', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: '2026-01-02', valor: 155, unidad: 'kg' },
  ])
  assert.equal(s.dibujable, true)
  assert.deepEqual(s.unidades, ['kg'])
  assert.equal(s.motivoUnidad, null)
})

test('sin unidad, se dibuja: la API puede no mandarla y eso no rompe nada', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150 },
    { fecha: '2026-01-02', valor: 155 },
  ])
  assert.equal(s.dibujable, true)
  assert.deepEqual(s.unidades, [])
  assert.equal(s.motivoUnidad, null)
})

test('el punto descartado por fecha no decide que la serie mezcla', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: 'no-fecha', valor: 90, unidad: 'ud' },
  ])
  assert.equal(s.dibujable, true, 'el de ud no se dibuja, asi que no mezcla nada')
  assert.deepEqual(s.unidades, ['kg'])
})
