/**
 * *** EL BUSCADOR DEL RECETARIO: TODAS LAS PALABRAS, Y EL ORDEN NO SE TOCA. ***
 *
 * *`recetario.ts` lo dice en su cabecera:*
 *
 *   «**Sin dependencias, para poder probarlo.**»
 *
 *   «G12 pide busqueda/filtros: el recetario tenia la biblioteca y no tenia buscador. **Es la primera
 *    funcion de interfaz que el encargo encuentra ausente**.»
 *
 * *** Y no tenia pruebas. ***
 *
 * *Y dos reglas que se leen y no se comprueban solas:*
 *
 *   - **Todas las palabras tienen que aparecer**, no una: buscar «tortilla patata» y que salga cualquier
 *     tortilla es peor que no encontrar nada, porque te hace leer la lista entera.
 *   - **El orden no se toca**: reordenar por parecido es lo que hace que una busqueda parezca que
 *     «encuentra» cosas.
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  etiquetasDe,
  etiquetasDeUna,
  filtraRecetas,
  textoDelVacio,
} from '../src/logica/recetario.ts'

const receta = (extra = {}) => ({
  id: 1,
  nombre: 'Tortilla de patata',
  etiquetas: [],
  archivada: false,
  ...extra,
})

// ------------------------------------------------------ todas las palabras ---

test('*** TODAS las palabras tienen que aparecer, no una ***', () => {
  // *Es la regla que el modulo pone por escrito, y la que evita que una busqueda «encuentre» de mas.*
  const recetas = [
    receta({ id: 1, nombre: 'Tortilla de patata' }),
    receta({ id: 2, nombre: 'Tortilla francesa' }),
  ]
  const r = filtraRecetas(recetas, { texto: 'tortilla patata' })
  assert.equal(r.length, 1, 'solo la que tiene las dos palabras')
  assert.equal(r[0].id, 1)
})

test('*** y el ORDEN no se toca: no se reordena por parecido ***', () => {
  // *«Reordenar por parecido es lo que hace que una busqueda parezca que encuentra cosas.»*
  const recetas = [
    receta({ id: 10, nombre: 'Arroz con leche' }),
    receta({ id: 20, nombre: 'Arroz al horno' }),
    receta({ id: 30, nombre: 'Arroz blanco' }),
  ]
  const r = filtraRecetas(recetas, { texto: 'arroz' })
  assert.deepEqual(r.map((x) => x.id), [10, 20, 30], 'el orden del servidor se respeta')
})

// --------------------------------------------------------- acentos y mayusculas ---

test('*** «Atun» encuentra «atún» ***', () => {
  const recetas = [receta({ id: 1, nombre: 'Atún con tomate' })]
  assert.equal(filtraRecetas(recetas, { texto: 'atun' }).length, 1)
  assert.equal(filtraRecetas(recetas, { texto: 'ATÚN' }).length, 1)
  assert.equal(filtraRecetas(recetas, { texto: 'Atun' }).length, 1)
})

test('el texto vacio significa «todo»', () => {
  const recetas = [receta({ id: 1 }), receta({ id: 2, nombre: 'Otra' })]
  assert.equal(filtraRecetas(recetas, { texto: '' }).length, 2)
  assert.equal(filtraRecetas(recetas, {}).length, 2)
})

// ------------------------------------------------------------- las etiquetas ---

test('*** una receta archivada no sale salvo que se pida ***', () => {
  // *«Archivada no es borrada»: existe, pero no en la lista de todos los dias.*
  const recetas = [receta({ id: 1 }), receta({ id: 2, archivada: true })]
  assert.equal(filtraRecetas(recetas, {}).length, 1, 'por defecto, sin archivadas')
  assert.equal(filtraRecetas(recetas, { incluirArchivadas: true }).length, 2)
})

test('filtrar por etiqueta deja solo las que la tienen', () => {
  const recetas = [
    receta({ id: 1, etiquetas: ['cena', 'rapida'] }),
    receta({ id: 2, etiquetas: ['postre'] }),
  ]
  const r = filtraRecetas(recetas, { etiqueta: 'cena' })
  assert.equal(r.length, 1)
  assert.equal(r[0].id, 1)
})

test('etiqueta vacia o ausente significa «todas»', () => {
  const recetas = [receta({ id: 1, etiquetas: ['cena'] }), receta({ id: 2 })]
  assert.equal(filtraRecetas(recetas, { etiqueta: null }).length, 2)
  assert.equal(filtraRecetas(recetas, { etiqueta: '' }).length, 2)
})

test('*** las etiquetas del servidor pueden venir como texto, y se entienden ***', () => {
  // *La columna es texto: «cena,rapida» o el JSON segun como se guardara.*
  const r = filtraRecetas([receta({ id: 1, etiquetas: 'cena,rapida' })], { etiqueta: 'cena' })
  assert.equal(r.length, 1, 'una etiqueta dentro de un texto tambien cuenta')
})

// ------------------------------------------------------- las etiquetas sueltas ---

test('*** `etiquetasDeUna` las devuelve TAL CUAL: deduplicar es del desplegable ***', () => {
  // *Lo cace porque la prueba fallo: yo esperaba `['cena','postre']` -- ordenadas y sin repetir -- y el
  // modulo devuelve `['postre','cena','postre']`.*
  // *Y es correcto: esta funcion dice **que etiquetas tiene esta receta**, y eso es un hecho, no una
  // lista para pintar.* *El «ordenadas y sin repetir» esta en `etiquetasDe`, que lo dice en su
  // docstring: «para pintar el desplegable».*
  const e = etiquetasDeUna(receta({ etiquetas: ['postre', 'cena', 'postre'] }))
  assert.deepEqual(e, ['postre', 'cena', 'postre'], 'tal cual, sin ordenar ni deduplicar')
})

test('*** la cadena VACIA se cae; los espacios no, porque `!!e` no recorta ***', () => {
  // *Septima expectativa mia equivocada: esperaba que `'  '` tambien se cayera.*
  // *El contrato es «quitar lo falso» (`.filter(e => !!e)`), y `'  '` es verdadero.* *No es un
  // defecto: es que la funcion no recorta, y decirlo asi evita que alguien cuente con que lo haga.*
  assert.deepEqual(etiquetasDeUna(receta({ etiquetas: ['cena', ''] })), ['cena'])
  assert.deepEqual(etiquetasDeUna(receta({ etiquetas: ['cena', '  '] })), ['cena', '  '])
  assert.deepEqual(etiquetasDeUna(receta({ etiquetas: [] })), [])
})

test('`etiquetasDe` junta las de todas, sin repetir', () => {
  const e = etiquetasDe([
    receta({ id: 1, etiquetas: ['cena'] }),
    receta({ id: 2, etiquetas: ['cena', 'postre'] }),
  ])
  assert.deepEqual(e, ['cena', 'postre'])
})

// ------------------------------------------------------------ el texto del vacio ---

test('*** un vacio por filtro no dice «no tienes recetas» ***', () => {
  // *Es la regla de los estados vacios: decir que no hay cuando lo que pasa es que el filtro no deja
  // pasar nada es mandar a mirar donde no esta el problema.*
  const conFiltro = textoDelVacio({ texto: 'azafran' }, 12)
  assert.ok(conFiltro.length > 0)
  assert.doesNotMatch(conFiltro, /no tienes/i, 'con 12 recetas guardadas no puede decir «no tienes»')
})

test('sin recetas de verdad, el vacio lo dice', () => {
  const vacio = textoDelVacio({}, 0)
  assert.ok(vacio.length > 0)
})
