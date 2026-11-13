// El contrato de la medicion, comprobado. Sin esto, "ya esta medido" es una
// frase: el informe podria salir sin las tres rutas, sin los dos viewports o
// sin las medidas clave, y nadie se enteraria hasta leerlo entero.
//
// Uso:  node --test scripts/prueba-medicion.test.mjs
//       (rojo mientras no exista medicion.json; verde cuando la medicion ha ido bien)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const SALIDA = process.env.CESTA_SALIDA ?? 'F:\\Proyectos\\cesta'
const MEDICION = join(SALIDA, 'medicion.json')
const CAPTURAS = join(SALIDA, 'capturas')
const RUTAS = ['compra', 'listas', 'comparar']
const VIEWPORTS = ['movil', 'escritorio']

const leer = () => JSON.parse(readFileSync(MEDICION, 'utf8'))

test('existe medicion.json', () => {
  assert.ok(existsSync(MEDICION), `falta ${MEDICION}: la medicion no se ha ejecutado`)
})

test('trae los dos viewports y las tres rutas', () => {
  const m = leer()
  for (const vp of VIEWPORTS) {
    assert.ok(m.rutas[vp], `falta el viewport ${vp}`)
    for (const r of RUTAS) {
      assert.ok(m.rutas[vp][r], `falta la ruta ${r} en ${vp}`)
    }
  }
})

test('cada medida trae lo que el encargo pide', () => {
  const m = leer()
  for (const vp of VIEWPORTS) {
    for (const r of RUTAS) {
      const d = m.rutas[vp][r]
      assert.equal(typeof d.scrollHorizontal, 'boolean', `${vp}/${r}: scrollHorizontal`)
      assert.ok(d.primerContenido && typeof d.primerContenido.top === 'number',
        `${vp}/${r}: primer contenido visible`)
      assert.ok(d.cabecera && typeof d.cabecera.alto === 'number', `${vp}/${r}: alto de cabecera`)
      assert.ok(d.euroKg && typeof d.euroKg.enPantalla === 'number',
        `${vp}/${r}: €/kg en pantalla`)
      assert.ok(Array.isArray(d.textosCortados), `${vp}/${r}: textos cortados`)
      assert.equal(typeof d.filas.visibles, 'number', `${vp}/${r}: filas visibles`)
      assert.equal(d.datosListos, true, `${vp}/${r}: los datos no llegaron a tiempo`)
    }
  }
})

test('las tres rutas se sirvieron sin errores de API ni de consola', () => {
  const m = leer()
  for (const vp of VIEWPORTS) {
    for (const r of RUTAS) {
      const d = m.rutas[vp][r]
      assert.ok(d.api.llamadas > 0, `${vp}/${r}: no se llamo a la API (¿pantalla sin datos?)`)
      assert.deepEqual(d.api.noOk, [], `${vp}/${r}: respuestas que no son 2xx`)
      assert.deepEqual(d.erroresConsola, [], `${vp}/${r}: excepciones en la pagina`)
    }
  }
})

test('hay una captura por ruta y viewport', () => {
  const m = leer()
  assert.ok(existsSync(CAPTURAS), `falta la carpeta ${CAPTURAS}`)
  const ficheros = readdirSync(CAPTURAS)
  for (const vp of VIEWPORTS) {
    for (const r of RUTAS) {
      const nombre = m.rutas[vp][r].captura
      assert.ok(nombre, `${vp}/${r}: sin nombre de captura`)
      assert.ok(ficheros.includes(nombre), `${vp}/${r}: falta la captura ${nombre}`)
    }
  }
})

test('el resumen de medidas clave esta calculado', () => {
  const m = leer()
  for (const vp of VIEWPORTS) {
    const res = m.resumen[vp]
    assert.ok(res, `falta el resumen de ${vp}`)
    for (const r of RUTAS) {
      assert.equal(typeof res.scrollHorizontal[r], 'boolean', `${vp}/${r}: scroll en el resumen`)
      assert.equal(typeof res.altoDeCabecera[r], 'number', `${vp}/${r}: cabecera en el resumen`)
      assert.equal(typeof res.euroPorUnidadEnPantalla[r], 'number',
        `${vp}/${r}: €/ud en el resumen`)
    }
  }
})
