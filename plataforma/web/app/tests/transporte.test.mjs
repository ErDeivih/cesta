/**
 * *** «EL AHORRO PUEDE SER MENOR QUE EL VIAJE». ***
 *
 * *`transporte.ts` lo dice en su cabecera:*
 *
 *   «El reparto compara el total de dos tiendas **sin llegar a las dos**: si llegar a las dos costara lo
 *    mismo que llegar a una, y no es lo mismo: *el ahorro puede ser menor que el viaje*. No es un error de
 *    calculo -- la cuenta esta bien -- es contexto, y aqui se dice.»
 *
 * *Y añade, sobre esta misma prueba:*
 *
 *   «La frase se decide aqui y no en la pantalla, porque **“dos tiendas sin decir que son dos viajes”
 *    tiene que estar cubierto por una prueba**, no por el descuido de quien escriba el texto.»
 *
 * *** Y no la tenia. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { avisoDeTransporte, hayVariosViajes } from '../src/logica/transporte.ts'

// ------------------------------------------------- siempre se dice algo ---

test('*** con una tienda (o ninguna) el aviso YA existe: el transporte nunca se calla ***', () => {
  // *Lo que no puede pasar es que una pantalla enseñe un total sin decir que le falta el viaje.*
  for (const n of [0, 1]) {
    const frase = avisoDeTransporte(n)
    assert.ok(frase.length > 0, `con ${n} tienda(s) tiene que haber aviso igual`)
    assert.match(frase, /transporte/i, 'el aviso tiene que nombrar el transporte')
  }
})

test('*** con DOS tiendas se dice que son DOS viajes ***', () => {
  // *Es la frase que el modulo dice que no puede depender del descuido de quien escriba el texto.*
  const frase = avisoDeTransporte(2)
  assert.match(frase, /2 tiendas/, 'tiene que decir cuantas son')
  assert.match(frase, /2 viajes/, 'y que son dos viajes, no dos tiendas sin mas')
  assert.match(frase, /segundo viaje/, 'y nombrar el segundo viaje')
})

test('con tres o mas, el aviso habla del tiempo de hacerlos', () => {
  const frase = avisoDeTransporte(3)
  assert.match(frase, /3 tiendas/)
  assert.match(frase, /3 viajes/)
  assert.match(frase, /tiempo de hacerlos/, 'con tres ya no es «el segundo», es el tiempo')
})

test('*** el «ahorro» solo se nombra cuando hay con que comparar ***', () => {
  // *Lo cace porque la prueba fallo: con **una** tienda la frase es «es lo que cuesta la compra, no el
  // viaje» -- **no habla de ahorro**, porque no hay dos totales que comparar.*
  // *Y es correcto: el ahorro es la diferencia entre ir a una y a dos, asi que sin dos no existe.*
  assert.doesNotMatch(
    avisoDeTransporte(1),
    /ahorro/i,
    'con una tienda no hay ahorro que anunciar',
  )
  // *Desde dos si, porque ahi empieza la comparacion.*
  assert.match(avisoDeTransporte(2), /ahorro/i)
  assert.match(avisoDeTransporte(3), /ahorro/i)
})

// --------------------------------------------------- valores que no son tiendas ---

test('*** un numero que no es un numero no rompe el aviso ***', () => {
  // *`NaN` e `Infinity` no son «muchas tiendas»: son un dato roto, y el aviso vuelve al de una.*
  for (const roto of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
    const frase = avisoDeTransporte(roto)
    assert.ok(frase.length > 0)
    assert.ok(!/NaN|Infinity/.test(frase), 'no se enseña el numero roto al usuario')
    assert.match(frase, /transporte/i)
  }
})

test('una tienda, cero y negativo dicen lo mismo: la frase base', () => {
  const base = avisoDeTransporte(1)
  assert.equal(avisoDeTransporte(0), base)
  assert.equal(avisoDeTransporte(-3), base)
})

// --------------------------------------------------- ¿hay varios viajes? ---

test('*** `hayVariosViajes` solo dice que si a partir de DOS ***', () => {
  assert.equal(hayVariosViajes(1), false, 'una tienda es un viaje')
  assert.equal(hayVariosViajes(2), true, 'dos tiendas son dos viajes')
  assert.equal(hayVariosViajes(5), true)
})

test('y con un dato roto o sin tiendas, dice que no', () => {
  for (const raro of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.equal(hayVariosViajes(raro), false, `${raro} no es «varios viajes»`)
  }
})
