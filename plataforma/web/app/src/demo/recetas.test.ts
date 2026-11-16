/** *** LAS CALORÍAS DE LAS RECETAS SE CALCULAN, NO SE ESCRIBEN. *** *
 *
 *  *La demo tiene que poder decir «287 kcal por ración» y que esa cifra salga de los ingredientes
 *  y de las kcal por 100 g, no de un número pegado en el JSON. Esta prueba hace la cuenta por
 *  fuera y exige que coincida.*
 */
import { describe, expect, it } from 'vitest'

import { CATALOGO } from './catalogo'
import { RECETAS, kcalRacion, kcalTotal, recetaDe, resumenDe } from './recetas'

describe('las recetas de la demo', () => {
  it('hay al menos 10, y todas usan productos del catálogo', () => {
    expect(RECETAS.length).toBeGreaterThanOrEqual(10)
    const grupos = new Set(CATALOGO.map((p) => p.grupo_id))
    for (const receta of RECETAS) {
      expect(receta.ingredientes.length).toBeGreaterThanOrEqual(3)
      for (const ingrediente of receta.ingredientes) {
        expect(ingrediente.grupo_id).toBeTypeOf('number')
        expect(grupos.has(ingrediente.grupo_id as number), ingrediente.texto).toBe(true)
        expect(ingrediente.cantidad).toBeGreaterThan(0)
        expect(ingrediente.kcal_100g).toBeGreaterThan(0)
      }
    }
  })

  it('la kcal por ración es la suma de los ingredientes dividida por las raciones', () => {
    for (const receta of RECETAS) {
      const total = receta.ingredientes.reduce(
        (suma, i) => suma + ((i.kcal_100g as number) * (i.cantidad as number)) / 100,
        0,
      )
      const totalRedondeado = Math.round(total * 10) / 10
      expect(kcalTotal(receta)).toBe(totalRedondeado)
      const esperada = Math.round((totalRedondeado / receta.raciones) * 10) / 10
      expect(kcalRacion(receta)).toBe(esperada)
      expect(kcalRacion(receta)).toBeGreaterThan(0)
    }
  })

  it('el resumen lleva la kcal por ración y el detalle la conserva al escalar', () => {
    const receta = RECETAS[0]
    expect(resumenDe(receta).kcal_racion).toBe(kcalRacion(receta))
    const paraCuatro = recetaDe(receta.id, 4)!
    expect(paraCuatro.raciones).toBe(4)
    expect(paraCuatro.kcal_racion).toBe(kcalRacion(receta))
    expect(paraCuatro.kcal_total).toBeCloseTo((kcalTotal(receta) as number) * 2, 1)
  })
})
