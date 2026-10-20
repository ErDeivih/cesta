/**
 * *** LA PORTADA: lo que decide como se ve en un movil y como se encuentra. ***
 *
 * *Nada de esto da error si esta mal.* *Un `lang` equivocado hace que el lector de pantalla pronuncie en ingles; un
 * `viewport` sin `initial-scale` deja la app abierta como una pagina de escritorio encogida; un `theme-color` que no
 * coincida con el fondo da un destello del color equivocado al arrancar.*
 *
 * *Se comprueba sobre `index.html` de origen, que es lo que se copia al build.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8')

test('*** el idioma es castellano ***', () => {
  // *`lang="es"` y no `en`.* *El lector de pantalla lo usa para decidir como pronuncia, y el navegador para las
  // reglas de particion de palabras.*
  assert.match(html, /<html[^>]*\blang="es"/, 'la portada no declara lang="es"')
})

test('*** el viewport lleva initial-scale y viewport-fit=cover ***', () => {
  // *`initial-scale=1`: sin el, algunos moviles abren la pagina encogida.*
  assert.match(html, /name="viewport"[^>]*initial-scale=1/, 'sin `initial-scale=1`')
  assert.match(html, /name="viewport"[^>]*width=device-width/, 'sin `width=device-width`')
  // *`viewport-fit=cover`: es lo que deja pintar bajo la muesca del iPhone. Sin el, `env(safe-area-inset-*)`
  // vale cero y las barras se comen el contenido.*
  assert.match(html, /name="viewport"[^>]*viewport-fit=cover/, 'sin `viewport-fit=cover`')
})

test('*** dos theme-color, uno para cada tema ***', () => {
  // *Uno claro y otro oscuro, con su `media`. Un solo color deja la barra de estado destacando en el otro tema.*
  const claros = html.match(/name="theme-color"[^>]*media="\(prefers-color-scheme:light\)"/g) || []
  const oscuros = html.match(/name="theme-color"[^>]*media="\(prefers-color-scheme:dark\)"/g) || []
  assert.equal(claros.length, 1, 'falta el theme-color del tema claro')
  assert.equal(oscuros.length, 1, 'falta el theme-color del tema oscuro')
  // *Y tienen que ser DISTINTOS: el mismo color en los dos es como no tener ninguno.*
  const colores = [...html.matchAll(/name="theme-color"[^>]*content="([^"]+)"/g)].map((m) => m[1])
  assert.notEqual(colores[0], colores[1], 'los dos theme-color son el mismo')
})

test('*** la marca: titulo, icono, manifiesto y Apple ***', () => {
  assert.match(html, /<title>[^<]+<\/title>/, 'sin titulo')
  assert.match(html, /rel="icon"[^>]*href="\/icono\.svg"/, 'sin icono svg')
  assert.match(html, /rel="manifest"[^>]*href="\/site\.webmanifest"/, 'sin manifiesto')
  // *`apple-touch-icon`: sin el, en iOS se instala con una captura de la pantalla en vez del icono.*
  assert.match(html, /rel="apple-touch-icon"[^>]*href="\/icono-192\.png"/, 'sin apple-touch-icon')
  assert.match(html, /name="apple-mobile-web-app-title"/, 'sin titulo para iOS')
})

test('*** una descripcion, y tambien para compartir ***', () => {
  // *La descripcion es lo que se lee en un resultado de busqueda o al pegar el enlace; sin ella se coge la
  // primera frase de la pagina, que suele ser un boton.*
  assert.match(html, /name="description"[^>]*content="[^"]{20,}"/, 'sin `description` util')
  assert.match(html, /property="og:title"[^>]*content="[^"]+"/, 'sin `og:title`')
  assert.match(html, /property="og:locale"[^>]*content="es_ES"/, 'sin `og:locale` es_ES')
})

test('*** nada de scripts ni estilos en linea ***', () => {
  // *La CSP de Caddy es `script-src 'self'` y `style-src 'self'`: un `<script>` incrustado NO se ejecutaria, y
  // el fallo saldria en produccion y no aqui.* *Se comprueba que no hay ninguno en el documento de origen.*
  // *** Sin los comentarios: el propio comentario que explica la CSP contiene la palabra `<script>`. ***
  // *La primera version de esta prueba fallo por eso -- cazo su propio texto explicativo.* *Se quitan los
  // comentarios antes de mirar, que es lo que hace un navegador al construir el DOM.*
  const sinComentarios = html.replace(/<!--[\s\S]*?-->/g, '')
  assert.ok(!/<script(?![^>]*\bsrc=)[^>]*>[\s\S]*?<\/script>/i.test(sinComentarios), 'hay un script en linea')
  assert.ok(!/<style[\s>]/i.test(sinComentarios), 'hay un bloque de estilo en linea')
  assert.ok(!/\sstyle="/i.test(sinComentarios), 'hay un atributo style en linea')
})
