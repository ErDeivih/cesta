/**
 * *** «2 kg» NO SON DOS ENVASES. ***
 *
 * *M05 lo pide con estas palabras: «Texto libre y pegar varias lineas con previa; **no interpretar
 * «2 kg» como dos envases sin base**».*
 *
 * *Estas pruebas fijan **lo que el parser hace y lo que no**: separa la cantidad del nombre, y la
 * deja como TEXTO. No decide cuantos envases son, porque eso depende del formato que se compre y
 * aqui no se sabe.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { parteLoPegado, partirCantidad, resumenDeLaPrevia } from '../src/logica/pegar.ts'

test('«2 kg de arroz» da cantidad y unidad, y el nombre limpio', () => {
  const p = partirCantidad('2 kg de arroz')
  assert.equal(p.nombre, 'arroz')
  assert.equal(p.cantidad, '2')
  assert.equal(p.unidad, 'kg')
  assert.equal(p.nota, '2 kg')
})

test('*** y la cantidad NO se convierte en envases ***', () => {
  // *Es la regla que la especificacion nombra. `cantidad` es texto, y no se suma a nada.*
  const p = partirCantidad('2 kg de arroz')
  assert.equal(typeof p.cantidad, 'string', 'la cantidad es texto, no un numero de envases')
  assert.equal(p.cantidad, '2')
  // *Y 2 kg NO es «2 envases»: el parser no tiene campo de envases, y eso es a proposito.*
  assert.equal('envases' in p, false, 'el parser no inventa un numero de envases')
})

test('sin unidad reconocida, el numero se queda en el nombre', () => {
  // *«2 cosas» no dice cuanto es nada: partir seria inventar.*
  const p = partirCantidad('2 cosas raras')
  assert.equal(p.nombre, '2 cosas raras')
  assert.equal(p.cantidad, null)
})

test('«Arroz 2 kg» se queda entero: partir por el medio es peor', () => {
  // *«pan de 2 kg» -> «pan de» seria un nombre roto.*
  const p = partirCantidad('Arroz 2 kg')
  assert.equal(p.nombre, 'Arroz 2 kg')
  assert.equal(p.cantidad, null)
})

test('las vinetas y la numeracion se quitan', () => {
  const pegadas = parteLoPegado('1. leche\n- pan\n• arroz\n2) huevos')
  assert.deepEqual(pegadas.map((p) => p.nombre), ['leche', 'pan', 'arroz', 'huevos'])
})

test('las lineas vacias se descartan, y los repetidos se conservan', () => {
  // *Pegar de un documento trae saltos de mas; apuntar «leche» dos veces es valido.*
  const pegadas = parteLoPegado('leche\n\n\nleche\n')
  assert.equal(pegadas.length, 2)
  assert.deepEqual(pegadas.map((p) => p.nombre), ['leche', 'leche'])
})

test('la previa dice cuantas lineas y cuantas traen cantidad', () => {
  const pegadas = parteLoPegado('2 kg de arroz\npan\n1 l de leche')
  assert.equal(pegadas.length, 3)
  const resumen = resumenDeLaPrevia(pegadas)
  assert.match(resumen, /3 lineas/)
  assert.match(resumen, /2 con cantidad/)
  assert.match(resumen, /no se convierte en envases/)
})

test('y sin cantidades lo dice tambien', () => {
  const resumen = resumenDeLaPrevia(parteLoPegado('pan\nleche'))
  assert.match(resumen, /Ninguna trae cantidad/)
})

test('un texto vacio no da lineas', () => {
  assert.deepEqual(parteLoPegado('   \n  \n'), [])
  assert.match(resumenDeLaPrevia([]), /No hay ninguna/)
})
