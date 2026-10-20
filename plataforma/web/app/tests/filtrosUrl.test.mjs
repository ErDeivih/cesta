/**
 * *** LOS FILTROS VIVEN EN LA URL, Y ESO ES UNA DECISION, NO ESTETICA. ***
 *
 * *`filtrosUrl.ts` lo dice:*
 *
 *   «Tres motivos, y ninguno es estetico:
 *    - Volver atras desde una ficha devuelve a la MISMA busqueda, con sus filtros. Con el estado en
 *      memoria, volver deja la pantalla en blanco.
 *    - Se puede mandar un enlace a "leche sin lactosa de Dia y Alcampo".
 *    - Guardar una combinacion de filtros es guardar una cadena de texto, sin inventar un formato aparte
 *      ni un endpoint que no existe.»*
 *
 * *Y aqui se prueba el ida y vuelta: **lo que se escribe en la URL es lo que se lee de ella**.*
 * *** Si esa vuelta se rompe, los tres motivos de arriba dejan de ser ciertos. ***
 *
 * *Este fichero no existia porque no se podia ni cargar; ahora si, porque el tipo y la constante que
 * importaba salieron de `api/` a `src/tipos/`.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { cuantosFiltros, escribirFiltros, leerFiltros } from '../src/estado/filtrosUrl.ts'

/** *Los filtros vacios, copiados a mano para no depender de `api/consultas` en la prueba.* */
const VACIOS = {
  q: '',
  cadenas: [],
  seccion: '',
  comparables: false,
  conNutricion: false,
  ofertas: false,
  marcaPropia: false,
  sinAlcohol: false,
  sellos: [],
  conservacion: '',
  limite: 40,
  desplazamiento: 0,
}

// ------------------------------------------------------------ el ida y vuelta ---

test('*** lo que se escribe es lo que se lee ***', () => {
  const filtros = {
    ...VACIOS,
    q: 'leche sin lactosa',
    cadenas: ['dia', 'alcampo'],
    ofertas: true,
    sellos: ['sin-lactosa'],
    limite: 20,
    desplazamiento: 40,
  }
  const vuelta = leerFiltros(escribirFiltros(filtros))
  assert.equal(vuelta.q, 'leche sin lactosa')
  assert.deepEqual(vuelta.cadenas, ['dia', 'alcampo'])
  assert.equal(vuelta.ofertas, true)
  assert.deepEqual(vuelta.sellos, ['sin-lactosa'])
  assert.equal(vuelta.limite, 20)
  assert.equal(vuelta.desplazamiento, 40)
})

test('*** una URL vacia da los filtros vacios ***', () => {
  assert.deepEqual(leerFiltros(new URLSearchParams()), VACIOS)
})

test('*** la primera pagina es la URL sin nada ***', () => {
  // *«Y no se escribe cuando es cero: la primera pagina es la URL sin nada, y asi sigue siendo el enlace
  // a la busqueda entera.»* *Un `?desplazamiento=0` haria dos enlaces distintos para la misma pantalla.*
  const p = escribirFiltros(VACIOS)
  assert.equal(p.toString(), '', 'sin filtros no hay parametros')
  assert.equal(p.has('limite'), false)
})

test('*** y las listas vacias tampoco ensucian la URL ***', () => {
  const p = escribirFiltros({ ...VACIOS, cadenas: [], sellos: [] })
  assert.equal(p.has('cadenas'), false)
  assert.equal(p.has('sellos'), false)
})

// ------------------------------------------------------------------ el texto ---

test('el texto se recorta al escribir', () => {
  assert.equal(escribirFiltros({ ...VACIOS, q: '  arroz  ' }).get('q'), 'arroz')
})

test('*** y un texto de solo espacios no se escribe ***', () => {
  assert.equal(escribirFiltros({ ...VACIOS, q: '   ' }).has('q'), false)
})

test('las cadenas se escriben separadas por coma y se leen de vuelta', () => {
  const p = escribirFiltros({ ...VACIOS, cadenas: ['mercadona', 'lidl'] })
  assert.equal(p.get('cadenas'), 'mercadona,lidl')
  assert.deepEqual(leerFiltros(p).cadenas, ['mercadona', 'lidl'])
})

test('*** una lista con huecos no se cuela ***', () => {
  assert.deepEqual(
    leerFiltros(new URLSearchParams('cadenas=dia,,alcampo')).cadenas,
    ['dia', 'alcampo'],
  )
})

// ------------------------------------------------------------- cuantos filtros ---

test('*** el contador NO cuenta el texto buscado ***', () => {
  // *«Se usa para el "3 filtros" del boton plegado: en un movil, cada fila de filtros es una fila de
  // resultados que no se ve.»* *El texto no es un filtro plegable: esta a la vista.*
  assert.equal(cuantosFiltros({ ...VACIOS, q: 'arroz' }), 0)
})

test('y cuenta cada cosa puesta, sin contar dos veces una lista', () => {
  assert.equal(cuantosFiltros({ ...VACIOS, cadenas: ['dia'] }), 1)
  assert.equal(cuantosFiltros({ ...VACIOS, cadenas: ['dia'], seccion: 'lacteos' }), 2)
  assert.equal(cuantosFiltros({ ...VACIOS, ofertas: true, conNutricion: true }), 2)
  assert.equal(cuantosFiltros({ ...VACIOS, cadenas: ['dia', 'lidl'] }), 1, 'una lista, un filtro')
})
