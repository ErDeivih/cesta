/**
 * A07 — La pagina de resultados, con sus tres reglas.
 *
 * **Lo que estas pruebas fijan, y por que cada una.**
 *
 *  1. **La pagina se puede calcular y acotar** -- *y acotarla importa: el catalogo mengua entre dos
 *     peticiones y una pagina 9 de 3 no existe.*
 *  2. **Al cambiar la pregunta se vuelve al principio** -- *seguir en la pagina 4 de «pan» despues de
 *     buscar «leche» es saltarse tres paginas que nadie ha visto.*
 *  3. **Y si el catalogo cambio entre paginas, se dice** -- *en vez de servir una lista que se solapa.*
 *
 * **Y el orden NO esta aqui, a proposito.** *Es la trampa que la revision avisa: «no ordenar solo la
 * pagina como si fuera el catalogo entero».* **Hay una prueba que comprueba que este modulo no ordena
 * nada**, para que nadie lo «arregle» en el cliente.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

import {
  LIMITE_POR_DEFECTO,
  desplazamientoDe,
  estadoDePagina,
  hayQueVolverAlPrincipio,
  paginaDe,
  paginasDe,
} from '../src/logica/pagina.ts'

// ------------------------------------------------------------------- contar ---

test('las paginas de un total, y el caso de cero', () => {
  assert.equal(paginasDe(0, 40), 0, 'cero resultados son cero paginas, no una')
  assert.equal(paginasDe(1, 40), 1)
  assert.equal(paginasDe(40, 40), 1, 'exacto no añade una pagina vacia')
  assert.equal(paginasDe(41, 40), 2)
  assert.equal(paginasDe(100, 40), 3)
})

test('un limite que no sirve no fabrica paginas', () => {
  // *Cero o negativo no puede dar infinitas paginas: da cero, y la pantalla no enseña paginador.*
  assert.equal(paginasDe(100, 0), 0)
  assert.equal(paginasDe(100, -5), 0)
  assert.equal(paginaDe(80, 0), 1, 'sin limite, la pagina es la primera')
  assert.equal(desplazamientoDe(3, 0), 0)
})

test('la pagina de un desplazamiento, empezando en uno', () => {
  assert.equal(paginaDe(0, 40), 1)
  assert.equal(paginaDe(39, 40), 1)
  assert.equal(paginaDe(40, 40), 2, 'el desplazamiento 40 es la segunda pagina')
  assert.equal(paginaDe(80, 40), 3)
})

test('un desplazamiento mas alla del final cae en la ultima pagina, no en una que no existe', () => {
  // *Y pasa de verdad: si el catalogo mengua entre dos peticiones, la pagina que se pedia ya no esta.*
  assert.equal(paginaDe(4000, 40, 100), 3, '100 resultados son 3 paginas: la 101 seria la 3')
  assert.equal(paginaDe(80, 40, 45), 2, 'con 45 resultados solo hay 2 paginas')
  // *Y sin total no se acota nada, porque no hay con que.*
  assert.equal(paginaDe(4000, 40), 101)
})

test('el desplazamiento de una pagina es la ida y vuelta de la otra', () => {
  for (const p of [1, 2, 3, 9]) {
    assert.equal(paginaDe(desplazamientoDe(p, 40), 40), p, `pagina ${p}`)
  }
  assert.equal(desplazamientoDe(1, 40), 0)
  assert.equal(desplazamientoDe(2, 40), 40)
  // *Una pagina 0 o negativa se trata como la primera: no hay «antes del principio».*
  assert.equal(desplazamientoDe(0, 40), 0)
  assert.equal(desplazamientoDe(-3, 40), 0)
})

// --------------------------------------------- volver al principio al cambiar ---

const CLAVES = ['q', 'cadenas', 'seccion', 'ofertas', 'limite']

test('cambiar el texto devuelve a la primera pagina', () => {
  assert.equal(hayQueVolverAlPrincipio({ q: 'leche' }, { q: 'pan' }, CLAVES), true)
})

test('cambiar cualquier filtro devuelve a la primera pagina', () => {
  // *Y se prueban uno a uno: si alguien añade un filtro y se olvida de la lista, esta prueba no lo
  // cazaria -- pero si lo caza el que la lista este escrita en un solo sitio.*
  assert.equal(hayQueVolverAlPrincipio({ seccion: 'lacteos' }, { seccion: 'pan' }, CLAVES), true)
  assert.equal(hayQueVolverAlPrincipio({ ofertas: false }, { ofertas: true }, CLAVES), true)
  assert.equal(hayQueVolverAlPrincipio({ cadenas: ['dia'] }, { cadenas: ['dia', 'aldi'] }, CLAVES), true)
  assert.equal(hayQueVolverAlPrincipio({ limite: 40 }, { limite: 80 }, CLAVES), true)
})

test('el TOPE tambien devuelve al principio, y es el caso que se olvida', () => {
  /* **Con `limite` distinto, el mismo desplazamiento cae en otra pagina.** *40 resultados por pagina
   * desde el 80 es la tercera; desde el 20, la quinta.* **Seguir en el mismo desplazamiento seria
   * enseñar otra cosa sin decirlo.**
   */
  assert.equal(hayQueVolverAlPrincipio({ limite: 40 }, { limite: 20 }, CLAVES), true)
  assert.equal(desplazamientoDe(3, 40), 80)
  assert.equal(desplazamientoDe(3, 20), 40, 'la misma pagina 3, otro sitio: 40 y no 80')
})

test('cambiar una lista de cadenas de orden SI cuenta como cambio', () => {
  // *No se supone que el servidor trate igual `['a','b']` y `['b','a']`: si lo hiciera, daria igual; si
  // no, cambiar el orden cambiaria los resultados y la pagina dejaria de significar lo mismo.*
  assert.equal(hayQueVolverAlPrincipio({ cadenas: ['dia', 'aldi'] }, { cadenas: ['aldi', 'dia'] }, CLAVES), true)
})

test('lo que no cambia la pregunta NO devuelve al principio', () => {
  /* **Y esto es lo que hace usable el paginador**: *pasar de la pagina 1 a la 2 no es cambiar la
   * pregunta.* Si esto devolviera `true`, el boton «siguiente» no funcionaria.
   */
  assert.equal(hayQueVolverAlPrincipio({ q: 'leche' }, { q: 'leche' }, CLAVES), false)
  assert.equal(
    hayQueVolverAlPrincipio(
      { q: 'leche', cadenas: ['dia'], limite: 40 },
      { q: 'leche', cadenas: ['dia'], limite: 40 },
      CLAVES,
    ),
    false,
  )
  // *Dos objetos distintos con el mismo contenido son la misma pregunta.*
  assert.equal(hayQueVolverAlPrincipio({ q: 'x' }, { q: 'x' }, CLAVES), false)
})

test('el desplazamiento en si no esta entre las claves que reinician', () => {
  /* *A proposito*: **si lo estuviera, cada cambio de pagina se reiniciaria a si mismo.** *Es la prueba
   * que impide que alguien «arregle» el paginador rompiendolo.*
   */
  assert.equal(CLAVES.includes('desplazamiento'), false)
  assert.equal(CLAVES.includes('pagina'), false)
})

// ------------------------------------------------------- el aviso de version ---

test('sin cambio de version no hay aviso', () => {
  const e = estadoDePagina(40, 40, 200, '20261007-103000', '20261007-103000')
  assert.equal(e.pagina, 2)
  assert.equal(e.paginas, 5)
  assert.equal(e.hayAntes, true)
  assert.equal(e.hayDespues, true)
  assert.equal(e.aviso, null)
})

test('si el catalogo cambio entre paginas, se dice en vez de solapar filas', () => {
  /* **El criterio de A07**: *«fijar version o cursor para no duplicar filas cuando cambia el catalogo
   * entre paginas».* *Y lo que se hace cuando cambio no es recalcular en silencio: es decirlo.*
   */
  const e = estadoDePagina(40, 40, 200, '20261007-103000', '20261011-124542')
  assert.notEqual(e.aviso, null)
  assert.match(e.aviso, /puede repetir o saltarse resultados/)
  assert.match(e.aviso, /Vuelve a empezar/)
})

test('sin version conocida NO se inventa un aviso', () => {
  // *No saber la version no es un cambio de version.* **La regla de la fase, dentro del paginador.**
  assert.equal(estadoDePagina(0, 40, 200, null, '20261011-124542').aviso, null)
  assert.equal(estadoDePagina(0, 40, 200, '20261007-103000', null).aviso, null)
  assert.equal(estadoDePagina(0, 40, 200, null, null).aviso, null)
})

test('los botones se apagan donde no hay a donde ir', () => {
  const primera = estadoDePagina(0, 40, 200, null, null)
  assert.equal(primera.hayAntes, false, 'en la primera no hay «antes»')
  assert.equal(primera.hayDespues, true)

  const ultima = estadoDePagina(160, 40, 200, null, null)
  assert.equal(ultima.pagina, 5)
  assert.equal(ultima.hayDespues, false, 'en la ultima no hay «despues»')

  // *Y sin resultados no hay ni una cosa ni la otra.*
  const vacia = estadoDePagina(0, 40, 0, null, null)
  assert.equal(vacia.paginas, 0)
  assert.equal(vacia.hayAntes, false)
  assert.equal(vacia.hayDespues, false)
})

// --------------------------------------------------- lo que este modulo NO hace ---

test('este modulo NO ordena nada: el orden es del servidor, sobre todo el catalogo', () => {
  /* **Es la trampa que la revision avisa**: *«no ordenar solo la pagina como si fuera el catalogo
   * entero»*. **Si se ordenara aqui, la primera pagina no tendria los mejores del catalogo, tendria los
   * mejores de los primeros N** -- *y eso no se nota mirando la pantalla.*
   *
   * *La prueba lee el fuente del modulo y exige que no haya un `sort`.* **Es tosca a proposito**: *lo
   * que impide es que alguien lo añada «para arreglar el orden» sin darse cuenta de donde esta el
   * problema.*
   */
  const fuente = readFileSync(new URL('../src/logica/pagina.ts', import.meta.url), 'utf8')
  const codigo = fuente.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '')
  assert.equal(codigo.includes('.sort('), false, 'aqui no se ordena: el orden lo hace el servidor')
})

test('el tope por defecto es el mismo que usa la pantalla', () => {
  assert.equal(LIMITE_POR_DEFECTO, 40)
})
