/**
 * *** EL SERVICE WORKER QUE SE ENTREGA: lo que tiene que llevar, y por que. ***
 *
 * *Estas pruebas miran el `sw.js` **de origen**, no el construido: el construido se sella con
 * `scripts/sella-sw.mjs` y cambia de hash en cada build, asi que no es un buen asunto de prueba.*
 * *Lo que se comprueba es lo que **no** puede cambiar sin que alguien lo decida:*
 *
 *   1. **el armazon lleva las cuatro piezas que hacen falta para que la app abra**: el documento
 *      (`/`), el manifiesto y los dos iconos. *Si falta el documento, sin red no hay app.*
 *   2. **los dos marcadores** que `sella-sw.mjs` rellena (`__VERSION__` y `__PRECACHE__`).
 *      *Sin `__VERSION__`, dos publicaciones comparten cache y una version nueva sirve el armazon
 *      viejo.* *Sin `__PRECACHE__`, no se cachea ni un trozo.*
 *   3. **se guarda una a una y no con `addAll`**. *`addAll` es atomico: si una URL falla, no se
 *      guarda ninguna y el armazon se queda vacio sin que nadie se entere.* *Eso lo encontro una
 *      prueba, y el comentario del codigo lo dice; esta lo mantiene.*
 *   4. **la navegacion se sirve desde la cache**. *Si no, sin red no hay primera pantalla.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const sw = readFileSync(new URL('../public/sw.js', import.meta.url), 'utf8')

test('*** el armazon lleva las cuatro piezas que hacen falta para abrir sin red ***', () => {
  // *Se saca el array tal cual esta escrito, para no confundirlo con el `PRECACHE`.*
  const m = sw.match(/const ARMAZON = \[([^\]]*)\]/)
  assert.ok(m, 'no encuentro `const ARMAZON = [...]`')
  const dentro = m[1]
  for (const pieza of ["'/'", "'/site.webmanifest'", "'/icono.svg'", "'/icono-192.png'"]) {
    assert.ok(dentro.includes(pieza), 'el armazon no lleva ' + pieza)
  }
  // *** `/` es el index.html: sin el no hay documento, y sin documento no hay app. ***
  assert.ok(dentro.includes("'/'"), 'falta el documento (`/`)')
})

test('*** los dos marcadores que rellena el sello ***', () => {
  assert.ok(sw.includes("'__VERSION__'"), 'falta __VERSION__: dos builds compartirian cache')
  assert.ok(sw.includes('__PRECACHE__'), 'falta __PRECACHE__: no se cachearia ni un trozo')
})

test('*** se guarda una a una, no con `addAll` ***', () => {
  // *`addAll` es atomico. El comentario del codigo dice que una prueba lo encontro; esta lo mantiene.*
  assert.ok(!/\bc\.addAll\s*\(/.test(sw), 'usa addAll: una URL que falle deja el armazon vacio')
  assert.ok(/c\.add\(/.test(sw), 'no guarda ninguna pieza suelta')
})

test('*** la navegacion se sirve desde la cache ***', () => {
  assert.ok(/mode\s*===\s*'navigate'/.test(sw), 'no distingue una navegacion')
  // *Y la respuesta sale de la cache antes que de la red, para que abra sin conexion.*
  assert.ok(/caches\.match/.test(sw) || /c\.match/.test(sw), 'no busca en la cache')
})

test('*** y el precache viaja aparte del armazon ***', () => {
  // *El armazon son cuatro rutas fijas; los 30 trozos los pone el sello leyendo `assets/`.*
  // *Se comprueba que los dos se usan, porque un SW que cachee solo uno de los dos no sirve:*
  // *solo el armazon -> las pantallas diferidas no cargan; solo los trozos -> no hay documento.*
  assert.ok(/ARMAZON\.map/.test(sw), 'no recorre el armazon')
  assert.ok(/PRECACHE\.map/.test(sw) || /PRECACHE\.forEach/.test(sw), 'no recorre el precache')
})
