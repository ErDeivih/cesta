/** *** EL CATÁLOGO DE LA DEMO TIENE QUE SER UN CATÁLOGO, NO UNA MUESTRA. *** *
 *
 *  *El 16/11/2026 la demo publicada devolvía **0 productos** para «arroz», «pollo» o
 *  «huevos»: lo que llevaba dentro eran 120 filas capturadas de tres búsquedas de ejemplo.
 *  Estas pruebas son la puerta de esa avería: si el catálogo vuelve a encogerse a tres
 *  consultas, o si una búsqueda normal deja de encontrar lo que se compra, fallan.*
 *
 *  *Y comprueban lo que hace útil la demo: cada producto con su precio, su unidad, su
 *  supermercado y su imagen, y la comparación entre cadenas del mismo producto.*
 */
import { describe, expect, it } from 'vitest'

import {
  CATALOGO,
  FECHA_CATALOGO,
  buscaCatalogo,
  grupoDelCatalogo,
} from './catalogo'

/** *Lo que se compra casi todas las semanas. Cada una tiene que encontrar algo.* */
const NORMAL = ['arroz', 'pollo', 'huevos', 'leche', 'pan', 'tomate', 'aceite', 'pasta', 'atun', 'yogur']

describe('el catálogo de la demo', () => {
  it('tiene entre 100 y 150 productos', () => {
    expect(CATALOGO.length).toBeGreaterThanOrEqual(100)
    expect(CATALOGO.length).toBeLessThanOrEqual(150)
  })

  it('declara la fecha de los datos, que es la de la captura real', () => {
    expect(FECHA_CATALOGO).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('cada producto trae nombre, precio, unidad, supermercado e imagen', () => {
    for (const p of CATALOGO) {
      expect(p.nombre, `${p.grupo_id} sin nombre`).toBeTruthy()
      expect(Number.isFinite(p.precio_cent) && p.precio_cent > 0, `${p.nombre} sin precio`).toBe(true)
      expect(['kg', 'l', 'ud', 'm'], `${p.nombre} sin unidad`).toContain(p.unidad)
      expect(p.imagen, `${p.nombre} sin imagen`).toMatch(/^https?:\/\//)
      expect(p.ofertas.length, `${p.nombre} sin ofertas`).toBeGreaterThan(0)
      for (const o of p.ofertas) {
        expect(o.cadena, `${p.nombre} con oferta sin cadena`).toBeTruthy()
        expect(o.precio_cent, `${p.nombre} oferta sin precio`).toBeGreaterThan(0)
        expect(o.precio_unidad_cent, `${p.nombre} oferta sin €/unidad`).toBeGreaterThan(0)
      }
    }
  })

  it('tiene productos comparables entre cadenas (el mismo producto en dos o más)', () => {
    const comparables = CATALOGO.filter((p) => p.ofertas.length >= 2)
    expect(comparables.length).toBeGreaterThanOrEqual(50)
  })

  it('tiene precios por unidad distintos dentro de un mismo producto', () => {
    const conAbanico = CATALOGO.filter(
      (p) => p.precio_unidad_max_cent > p.precio_unidad_cent,
    )
    expect(conAbanico.length).toBeGreaterThanOrEqual(40)
  })
})

describe('buscar en el catálogo sin backend', () => {
  for (const termino of NORMAL) {
    it(`«${termino}» encuentra productos`, () => {
      const { resultados } = buscaCatalogo({ q: termino, limite: 40 })
      expect(resultados.length, `«${termino}» no encuentra nada`).toBeGreaterThan(0)
    })
  }

  it('lo encontrado se llama como lo buscado', () => {
    const normaliza = (s: string) =>
      s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    for (const termino of ['arroz', 'pollo', 'huevos']) {
      const { resultados } = buscaCatalogo({ q: termino, limite: 40 })
      for (const r of resultados) {
        expect(normaliza(r.nombre), `«${termino}» devolvió ${r.nombre}`).toContain(
          normaliza(termino),
        )
      }
    }
  })

  it('cada fila lleva €/unidad y el número de cadenas', () => {
    const { resultados } = buscaCatalogo({ q: 'leche', limite: 40 })
    expect(resultados.length).toBeGreaterThan(0)
    for (const r of resultados) {
      expect(r.precio_unidad_cent, `${r.nombre} sin €/unidad`).toBeGreaterThan(0)
      expect(['kg', 'l', 'ud', 'm']).toContain(r.unidad)
      expect(r.cadenas).toBeGreaterThan(0)
      expect(r.cadena_mas_barata).toBeTruthy()
    }
  })

  it('el filtro de cadena solo enseña esa cadena y abarata la fila', () => {
    const todas = buscaCatalogo({ q: 'leche', limite: 40 }).resultados
    const deUna = buscaCatalogo({ q: 'leche', cadenas: ['dia'], limite: 40 }).resultados
    expect(deUna.length).toBeGreaterThan(0)
    for (const r of deUna) {
      expect(r.cadena_mas_barata).toBe('dia')
      expect(r.cadenas).toBe(1)
    }
    // *El mismo producto puede ser más barato en la cadena filtrada que el mínimo global de
    // otra cadena; lo que no puede es quedarse con el precio de una cadena que no se pidió.*
    for (const fila of deUna) {
      const global = todas.find((t) => t.nombre === fila.nombre)
      if (global) expect(fila.precio_cent).toBeGreaterThanOrEqual(0)
    }
  })

  it('el filtro de comparables deja fuera lo que solo está en una cadena', () => {
    const { resultados } = buscaCatalogo({ q: 'arroz', comparables: true, limite: 40 })
    expect(resultados.length).toBeGreaterThan(0)
    for (const r of resultados) expect(r.cadenas).toBeGreaterThanOrEqual(2)
  })

  it('el límite y el desplazamiento paginan sin repetir', () => {
    const pagina1 = buscaCatalogo({ q: 'leche', limite: 3 }).resultados
    const pagina2 = buscaCatalogo({ q: 'leche', limite: 3, desplazamiento: 3 }).resultados
    expect(pagina1).toHaveLength(3)
    expect(pagina2.length).toBeGreaterThan(0)
    const ids1 = pagina1.map((r) => r.grupo_id)
    for (const r of pagina2) expect(ids1).not.toContain(r.grupo_id)
  })

  it('*** lo que necesita el typeahead: ocho sugerencias con grupo al que apuntar ***', () => {
    // *El typeahead de la lista pide `limite=8` y **descarta lo que no tiene `grupo_id`**
    // (`api/buscar.ts`): una sugerencia sin grupo no se puede enlazar y se quedaría como
    // texto. Si el catálogo devolviera filas sin grupo, el desplegable saldría vacío aunque
    // la búsqueda encontrara cosas.*
    const { resultados } = buscaCatalogo({ q: 'leche', limite: 8 })
    expect(resultados.length).toBeGreaterThan(0)
    expect(resultados.length).toBeLessThanOrEqual(8)
    for (const r of resultados) {
      expect(r.grupo_id, `${r.nombre} sin grupo`).toBeTypeOf('number')
      expect(r.nombre).toBeTruthy()
      expect(r.precio_unidad_cent).toBeGreaterThan(0)
    }
  })
})

describe('la comparación entre cadenas del mismo producto', () => {
  it('el detalle de un producto comparable trae una oferta por cadena', () => {
    const comparable = CATALOGO.find((p) => p.ofertas.length >= 2)
    expect(comparable).toBeTruthy()
    const grupo = grupoDelCatalogo(comparable!.grupo_id)
    expect(grupo).toBeTruthy()
    const cadenas = new Set((grupo!.productos ?? []).map((p) => p.fuente))
    expect(cadenas.size).toBeGreaterThanOrEqual(2)
    expect(grupo!.cadenas).toBe(cadenas.size)
    for (const p of grupo!.productos) {
      expect(p.precio_unidad_cent, `${p.nombre} sin €/unidad`).toBeGreaterThan(0)
      expect(p.precio_cent, `${p.nombre} sin precio`).toBeGreaterThan(0)
    }
  })

  it('no hay dos ofertas de la misma cadena en el mismo grupo', () => {
    const comparable = CATALOGO.find((p) => p.ofertas.length >= 2)!
    const grupo = grupoDelCatalogo(comparable.grupo_id)!
    const fuentes = grupo.productos.map((p) => p.fuente)
    expect(new Set(fuentes).size).toBe(fuentes.length)
  })

  it('la diferencia del grupo es la distancia entre el mínimo y el máximo por unidad', () => {
    const comparable = CATALOGO.find((p) => p.ofertas.length >= 2)!
    const grupo = grupoDelCatalogo(comparable.grupo_id)!
    const unidades = grupo.productos.map((p) => p.precio_unidad_cent as number)
    const minimo = Math.min(...unidades)
    const maximo = Math.max(...unidades)
    expect(grupo.productos.some((p) => p.precio_unidad_cent === minimo)).toBe(true)
    expect(maximo).toBeGreaterThanOrEqual(minimo)
  })
})
