/**
 * *** LA FRASE QUE MAS SE LEE DE TODA LA APLICACION. ***
 *
 * *`frase.ts` lo dice en su cabecera:*
 *
 *   «Esta es **la frase que mas se lee de toda la aplicacion** -- es la respuesta a la pregunta 2 --, y
 *    se juzga contra alguien que lee español, no contra el codigo. Se vio en una captura.»
 *
 * *Y da **su propia tabla de decision**, que es lo unico que hay que mirar:*
 *
 *      fiable  cadenas  caso                frase
 *      no      cualq.   no es de fiar       null
 *      si      1        una sola cadena     null
 *      si      2+       es la mas barata    «Es la mas barata de las N cadenas.»
 *      si      2+       hay mas barato      «Cuesta un X % mas que en CADENA.»
 *      si      2+       empate (0 %)        «Esta al mismo precio en N cadenas.»
 *
 * *** Este fichero es esa tabla, fila por fila. ***
 *
 * *Y se puede escribir porque `frase.ts` ya no importa `api/formato`: **pide** las dos funciones de
 * formato y aqui se pasan dos dobles triviales.* *Antes de eso, este fichero no llegaba ni a cargar.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { fraseDePrecio } from '../src/logica/frase.ts'

/** *Los dos dobles: lo que `api/formato` haria, sin arrastrar el navegador.* */
const formato = {
  euros: (c) => `${(c / 100).toFixed(2).replace('.', ',')} €`,
  nombreCadena: (c) => c.charAt(0).toUpperCase() + c.slice(1),
}

const datos = (extra = {}) => ({
  cadenas: 3,
  ahorro_pct: 20,
  ahorro_cent: 50,
  fiable: true,
  cadena_mas_barata: 'mercadona',
  cadena_de_este: 'dia',
  precio_unidad_este: 120,
  precio_unidad_minimo: 100,
  ...extra,
})

// --------------------------------------------------------- las dos filas de null ---

test('*** fila 1: si el grupo NO es de fiar, no hay frase ***', () => {
  assert.equal(fraseDePrecio(datos({ fiable: false }), formato), null)
  assert.equal(fraseDePrecio(datos({ fiable: false, cadenas: 5, ahorro_pct: 80 }), formato), null)
})

test('*** fila 2: con una sola cadena no hay comparacion, y no se inventa ***', () => {
  assert.equal(fraseDePrecio(datos({ cadenas: 1 }), formato), null)
  assert.equal(fraseDePrecio(datos({ cadenas: 0 }), formato), null)
})

// -------------------------------------------------------- es la mas barata ---

test('*** fila 3: si es la mas barata, se dice cuantas cadenas son ***', () => {
  const frase = fraseDePrecio(
    datos({ precio_unidad_este: 100, precio_unidad_minimo: 100, ahorro_cent: 50 }),
    formato,
  )
  assert.ok(frase)
  assert.match(frase, /m[aá]s barata/i)
  assert.match(frase, /3 cadenas/, 'tiene que decir de cuantas')
})

// ----------------------------------------------------------- hay mas barato ---

test('*** fila 4: si hay mas barato, se dice cuanto y donde ***', () => {
  const frase = fraseDePrecio(datos(), formato)
  assert.ok(frase)
  assert.match(frase, /Cuesta un .* m[aá]s/, 'la frase de «cuesta mas»')
  assert.match(frase, /Mercadona/, 'nombra la cadena como se llama, con mayuscula')
})

test('*** y las tildes estan: «más», no «mas» ***', () => {
  // *El fallo del 27/9/2026: «Cuesta un 41 % mas que en mercadona.»* *Es la frase mas leida de la
  // aplicacion y lleva tilde.*
  const frase = fraseDePrecio(datos(), formato)
  assert.match(frase, /m[aá]s/, 'la frase lleva «más» con tilde')
  assert.doesNotMatch(frase, /\bmas\b/, 'sin tilde no')
})

// ------------------------------------------------------------------ empate ---

test('*** fila 5: con empate se dice que estan al mismo precio ***', () => {
  const frase = fraseDePrecio(
    datos({ ahorro_cent: 0, precio_unidad_este: 100, precio_unidad_minimo: 100 }),
    formato,
  )
  assert.ok(frase)
  assert.match(frase, /mismo precio/i, 'un empate no es «cuesta un 0 % mas»')
  assert.match(frase, /3 cadenas/, 'y se dice en cuantas')
})

test('con dos cadenas, el empate dice «las dos»', () => {
  const frase = fraseDePrecio(
    datos({ cadenas: 2, ahorro_cent: 0, precio_unidad_este: 100, precio_unidad_minimo: 100 }),
    formato,
  )
  assert.match(frase, /las dos cadenas/)
})

// ------------------------------------------------------------- sin datos que dar ---

test('*** sin los dos precios por unidad, no se pone un porcentaje ***', () => {
  // *«Decirlo a ojo con el `ahorro_pct` del grupo seria hablar del grupo entero como si fuera de este
  // producto. Mejor la frase sin numero que un numero falso.»*
  const frase = fraseDePrecio(datos({ precio_unidad_este: null, precio_unidad_minimo: null }), formato)
  if (frase !== null) {
    assert.doesNotMatch(frase, /\d+\s*%/, 'sin datos no se pone un porcentaje')
  }
})
