/** *** LA FRASE DE COBERTURA: LOS NUMEROS MEDIDOS, Y NADA INVENTADO. ***
 *
 *  *`data/cobertura/<fuente>-<fecha>.json` ya no es solo de Lidl: las cinco cadenas de catalogo
 *  declaran su cobertura **medida** -- filas de hoy, el dia que se toma como referencia, el
 *  porcentaje y lo que se ha movido respecto a la captura anterior.*
 *
 *  *Lo que estas pruebas exigen, y por que:*
 *
 *  1. **Con la medicion, salen las cifras de verdad** -- filas, `%` de su referencia y precios
 *     cambiados --, *porque una cobertura sin numeros al lado es una etiqueta, y una etiqueta no
 *     deja juzgar nada.*
 *  2. **`catalogo_diario` NO se pinta jamas.** *Es el codigo del fichero, no una frase.*
 *  3. **Con datos incompletos no se inventa.** *Si falta el `%`, no se escribe «0 %» ni «-- %».*
 *  4. **El texto de Lidl no cambia.** *Es el unico catalogo parcial de verdad y su frase ya estaba
 *     medida.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { textoCobertura } from '../src/logica/cobertura.ts'

/** Lo que devuelve `GET /api/estado` para Mercadona el 4 de noviembre de 2026. */
const MERCADONA = {
  fuente: 'mercadona',
  cobertura: 'catalogo_diario',
  etiqueta: 'catálogo diario medido',
  fecha: '2026-11-04',
  filas: 4272,
  referencia: 4321,
  referencia_fecha: '2026-10-05',
  pct: 98.9,
  dias_sin_datos: 2,
  dias_en_la_ventana: 30,
  vs_anterior_pct: -1.1,
  veredicto: 'ok',
  novedad: { vs: '2026-11-03', nuevos: 4, cambiados: 71, desaparecen: 9 },
  captura: { fecha: '2026-11-04', escrita: '2026-11-04T12:21:20', filas: 4272 },
  metodo: 'medido sobre data/bronze y data/gold; no autodeclarado',
}

/** Lo que devuelve para Lidl: el unico catalogo parcial, y su frase de siempre. */
const LIDL = {
  fuente: 'lidl',
  cobertura: 'ofertas_semanales_parcial',
  fecha: '2026-11-04',
  fichas_leidas: 91,
  con_precio: 91,
  aviso: 'ofertas conocidas de Lidl, no su catalogo completo',
}

// --------------------------------------------------- el catalogo medido ---

test('*** catalogo con medicion: filas, % de su referencia y precios cambiados ***', () => {
  const frase = textoCobertura(MERCADONA)
  assert.ok(frase, 'con la medicion completa tiene que haber frase')
  // *Las filas. **4272, no «4.272»**: en espanol los numeros de cuatro cifras van sin
  // separador de miles (CLDR `minimumGroupingDigits: 2` para `es-ES`); a partir de cinco sí
  // se agrupa, y eso lo fija la prueba de abajo.*
  assert.match(frase, /4272 filas capturadas/)
  // *El porcentaje, con coma decimal y espacio antes del signo.*
  assert.match(frase, /98,9 %/)
  // *De que dia es la referencia: un `%` sin fecha no dice contra que se mide.*
  assert.match(frase, /del 5 oct/)
  // *Lo que se ha movido, que es lo que se viene a ver.*
  assert.match(frase, /71 precios cambiados/)
})

test('*** y el codigo crudo `catalogo_diario` no aparece ***', () => {
  const frase = textoCobertura(MERCADONA)
  assert.doesNotMatch(frase, /catalogo_diario/)
})

test('*** las cifras de cinco digitos si llevan separador de miles ***', () => {
  // *Carrefour mide 16 782 filas: el caso que demuestra que el formateo es el de `es-ES`.*
  const frase = textoCobertura({ cobertura: 'catalogo_diario', filas: 16782, pct: 99.9, referencia_fecha: '2026-10-31' })
  assert.match(frase, /16\.782 filas capturadas/)
  assert.match(frase, /99,9 %/)
})

// ------------------------------------------------- datos a medias o vacios ---

test('*** catalogo sin campos numericos: frase corta, sin cifras y sin reventar ***', () => {
  // *El fichero existe pero no trae ni filas ni `%`: no puede salir un «0 %».*
  const frase = textoCobertura({ cobertura: 'catalogo_diario' })
  assert.equal(frase, 'catálogo diario')
  assert.doesNotMatch(frase, /\d/)
  assert.doesNotMatch(frase, /%/)
})

test('*** catalogo a medias: se pinta lo que hay y se calla lo que falta ***', () => {
  // *Filas sí, `%` no.*
  const soloFilas = textoCobertura({ cobertura: 'catalogo_diario', filas: 4272 })
  assert.match(soloFilas, /4272 filas capturadas/)
  assert.doesNotMatch(soloFilas, /%/)
  assert.doesNotMatch(soloFilas, /precios cambiados/)

  // *`%` sí, filas no.*
  const soloPct = textoCobertura({ cobertura: 'catalogo_diario', pct: 98.9 })
  assert.match(soloPct, /98,9 %/)
  assert.doesNotMatch(soloPct, /filas/)
})

test('*** un null donde tocaba un numero no se convierte en cero ***', () => {
  const frase = textoCobertura({
    cobertura: 'catalogo_diario',
    filas: null,
    pct: null,
    referencia_fecha: null,
    novedad: { cambiados: null },
  })
  assert.equal(frase, 'catálogo diario')
  assert.doesNotMatch(frase, /\d/)
})

test('*** y un numero que no es numero tampoco se pinta ***', () => {
  // *`NaN` es lo que deja un `parseFloat` que fallo: no es una cifra medida.*
  const frase = textoCobertura({ cobertura: 'catalogo_diario', filas: Number.NaN, pct: Number.POSITIVE_INFINITY })
  assert.equal(frase, 'catálogo diario')
})

// ------------------------------------------------------------- Lidl igual ---

test('*** el texto de Lidl se queda como estaba ***', () => {
  const frase = textoCobertura(LIDL)
  assert.equal(frase, 'ofertas semanales, no el catálogo entero · 91 de 91 con precio')
  assert.doesNotMatch(frase, /ofertas_semanales_parcial/)
})

test('*** Lidl sin las dos cifras tampoco inventa ***', () => {
  const frase = textoCobertura({ cobertura: 'ofertas_semanales_parcial' })
  assert.equal(frase, 'ofertas semanales, no el catálogo entero')
})

// -------------------------------------------------- codigos y ausencias ---

test('*** sin cobertura, no hay frase ***', () => {
  for (const vacio of [null, undefined, {}]) {
    assert.equal(textoCobertura(vacio), null, String(vacio))
  }
})

test('*** un codigo desconocido no se pinta en crudo ***', () => {
  // *Se prefiere no decir nada a enseñar un identificador que nadie sabe leer.*
  assert.equal(textoCobertura({ cobertura: 'otra_cosa_nueva' }), null)
  // *Y si el fichero trae su etiqueta legible, se usa esa.*
  assert.equal(textoCobertura({ cobertura: 'otra_cosa_nueva', etiqueta: 'cobertura nueva' }), 'cobertura nueva')
})
