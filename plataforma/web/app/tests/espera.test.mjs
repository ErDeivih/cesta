import { test } from 'node:test'
import assert from 'node:assert/strict'

import { estaAtascada } from '../src/logica/espera.ts'

test('mientras carga y no ha pasado el limite, no esta atascada', () => {
  assert.equal(estaAtascada(true, 0, 10), false)
  assert.equal(estaAtascada(true, 9_999, 10), false)
})

test('a los diez segundos exactos ya se dice que esta atascada', () => {
  // **«A partir de», no «mas de»**: *al limite exacto, la pantalla ya deja de prometer.*
  assert.equal(estaAtascada(true, 10_000, 10), true)
  assert.equal(estaAtascada(true, 60_000, 10), true)
})

test('si dejo de cargar, no hay atasco aunque haya tardado mucho', () => {
  // **Lo que importa: que haya llegado manda sobre cuanto tardo.** *Una respuesta lenta no es un atasco.*
  assert.equal(estaAtascada(false, 0, 10), false)
  assert.equal(estaAtascada(false, 999_999, 10), false)
})

test('el limite se puede cambiar, y el defecto son diez segundos', () => {
  assert.equal(estaAtascada(true, 5_000, 5), true)
  assert.equal(estaAtascada(true, 5_000), false)
})
