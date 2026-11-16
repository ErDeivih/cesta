/**
 * *** LO QUE HACE QUE LA APP SE PUEDA INSTALAR: el manifiesto y sus iconos. ***
 *
 * *Un manifiesto mal escrito no da error en ninguna parte: la app funciona en el navegador y simplemente **no se
 * ofrece instalarla**, o se instala sin icono.* *Es la clase de fallo que no se nota hasta que alguien la instala.*
 *
 * *Se comprueba sobre `public/`, que es la fuente; el `dist` lo copia tal cual.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'

const LEER = new URL('../public/', import.meta.url)
const man = JSON.parse(readFileSync(new URL('site.webmanifest', LEER), 'utf8'))

/** *Una ruta del manifiesto, sin el prefijo que la hace absoluta.* *
 *
 * *El manifiesto pasó a rutas **relativas** el 16/11/2026: la misma compilación se sirve en la
 * raíz de Caddy y bajo `/cesta-demo/` en GitHub Pages, y un `/icono.svg` absoluto en Pages
 * pedía `https://erdeivih.github.io/icono.svg` -- 404, medido. Relativo al manifiesto, cada
 * sitio encuentra el suyo. Para comprobar el fichero, `.` y `/` son la misma carpeta.*
 */
const relativa = (src) => src.replace(/^\.?\//, '')

test('*** el manifiesto dice como se llama y como se abre ***', () => {
  // *El nombre nuevo, aplicado de verdad: el manifiesto es lo que se instala en el movil y
  // lo que enseña la tienda del sistema. «Avío», con tilde, es el mismo que el de la
  // cabecera y el de la pestaña.*
  assert.equal(man.name, 'Avío')
  assert.equal(man.short_name, 'Avío')
  // *`.` (o `/`) y no una ruta profunda: la app arranca en la portada, también bajo `/cesta-demo/`.*
  assert.match(man.start_url, /^(\.|\/)$/, 'la app no arranca en la portada')
  // *`standalone` y no `browser`: instalada, sin barra de direcciones.*
  assert.equal(man.display, 'standalone')
})

test('*** los dos colores, porque son los que pintan el arranque ***', () => {
  // *`theme_color` es la barra de estado; `background_color`, la pantalla mientras carga. Si faltan, se ve un
  // destello blanco al abrir la app instalada -- medido en el movil, y es lo unico que se ve en ese momento.*
  assert.match(man.theme_color, /^#[0-9a-f]{6}$/i)
  assert.match(man.background_color, /^#[0-9a-f]{6}$/i)
  // *El lema, el mismo que la portada: una sola frase en todos los metadatos.*
  assert.match(man.description, /bien hilada/, 'el manifiesto no lleva el lema')
})

test('*** los cuatro iconos, y cada uno existe ***', () => {
  const srcs = man.icons.map((i) => relativa(i.src))
  for (const s of ['icono-192.png', 'icono-512.png', 'icono-maskable-512.png', 'icono.svg']) {
    assert.ok(srcs.includes(s), 'el manifiesto no declara ' + s)
  }
  for (const i of man.icons) {
    const f = new URL(relativa(i.src), LEER)
    assert.ok(existsSync(f), 'el manifiesto declara ' + i.src + ' y no existe')
    assert.ok(i.type, i.src + ' sin `type`: algunos navegadores lo exigen')
  }
})

test('*** y el maskable es un fichero DISTINTO del normal ***', () => {
  // *Un icono maskable lleva margen: el sistema recorta hasta el 20 % del borde. Si fuera una copia del normal,
  // el recorte se comeria el dibujo.* *Se comprueba que son ficheros distintos, no que el margen sea el correcto
  // -- eso hay que mirarlo.*
  const normal = readFileSync(new URL('./icono-512.png', LEER))
  const mask = readFileSync(new URL('./icono-maskable-512.png', LEER))
  assert.notEqual(normal.toString('base64'), mask.toString('base64'),
    'el maskable es una copia del normal: el recorte se comeria el dibujo')
  assert.equal(mask.length > 0, true)
})

test('*** el tamano declarado es el tamano real ***', () => {
  // *Se lee la cabecera PNG: bytes 16..24 son ancho y alto en big-endian.* *Un 192x192 declarado y 512x512 de
  // verdad no rompe nada visible, pero descoloca la eleccion del sistema.*
  const anchoAlto = (f) => {
    const b = readFileSync(new URL(relativa(f), LEER))
    return { ancho: b.readUInt32BE(16), alto: b.readUInt32BE(20) }
  }
  for (const i of man.icons) {
    if (!i.src.endsWith('.png')) continue
    const { ancho, alto } = anchoAlto(i.src)
    const [w, h] = i.sizes.split('x').map(Number)
    assert.equal(ancho, w, i.src + ': declara ' + i.sizes + ' y mide ' + ancho + 'x' + alto)
    assert.equal(alto, h, i.src + ': declara ' + i.sizes + ' y mide ' + ancho + 'x' + alto)
  }
})
