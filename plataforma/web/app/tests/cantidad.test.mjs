/** *** LAS CANTIDADES PEQUEÑAS SE LEEN, NO SE REDONDEAN A CERO. ***
 *
 *  *Medido el 18/10/2026 en la ficha del azafran `dia/147509`: el envase es de **0,4 g** y la
 *  pantalla decia **«0 kg»**, porque `numero(0.0004, 3)` es `0`.* *Un cero no es un redondeo feo:
 *  dice que el paquete **no pesa**.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { cantidad } from '../src/api/formato.ts'

test('gramos: el azafran de 0,4 g ya no sale como 0 kg', () => {
  assert.equal(cantidad(0.0004, 'kg'), '0,4 g')
  assert.equal(cantidad(0.00015, 'kg'), '0,15 g')
  assert.equal(cantidad(0.0000005, 'kg'), '0,5 mg')
})

test('miligramos: por debajo del gramo se baja a mg', () => {
  assert.equal(cantidad(5e-7, 'kg'), '0,5 mg')
  assert.equal(cantidad(1e-7, 'kg'), '0,1 mg')
})

test('mililitros: la misma regla para volumen', () => {
  assert.equal(cantidad(0.0004, 'l'), '0,4 ml')
  assert.equal(cantidad(0.00075, 'l'), '0,75 ml')
})

test('lo que no hay que tocar sigue igual', () => {
  assert.equal(cantidad(0.5, 'kg'), '0,5 kg')
  assert.equal(cantidad(1, 'kg'), '1 kg')
  assert.equal(cantidad(0.75, 'l'), '0,75 l')
  assert.equal(cantidad(1, 'ud'), '1 ud')
  assert.equal(cantidad(400, 'g'), '400 g')
})

test('desconocidos: no se inventan', () => {
  assert.equal(cantidad(null, 'kg'), 'kg')
  assert.equal(cantidad(undefined, 'ud'), 'ud')
  assert.equal(cantidad(null, null), 'no lo sé')
  assert.equal(cantidad(0.4, null), '0,4')
})

test('un valor POSITIVO nunca se escribe como cero exacto, en ningun camino', () => {
  // *El 0 delante de la coma si vale: «0,4 g» es cuatro decimas de gramo.* *Lo que no vale es
  // **`0 kg`**: que la parte entera sea todo lo que se lee.*
  for (const [cant, ud] of [[1e-10, 'kg'], [1e-13, 'kg'], [0.0001, 'ud'], [1e-10, 'l'], [1e-9, 'l']]) {
    const texto = cantidad(cant, ud)
    const cifra = texto.split(' ')[0]
    assert.notEqual(cifra, '0', cant + ' ' + ud + ' dio ' + JSON.stringify(texto))
    assert.ok(!/^0$|^-0$/.test(cifra.replace(/[.,]$/, '')), 'dio ' + JSON.stringify(texto))
  }
})
