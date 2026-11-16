/** *** LAS 10 RECETAS DE LA DEMO, CON CALORÍAS CALCULADAS. *** *
 *
 *  *El JSON lo genera `scripts/genera-recetas-demo.py` a partir del catálogo y de las kcal por
 *  100 g de gold. Aquí solo se suma: gramos × kcal_100g / 100, y se divide por las raciones.
 *  No hay una cifra de calorías escrita a mano en ninguna parte.*
 *
 *  *`kcal_100g` viaja dentro del ingrediente porque es el dato que permite comprobar la cuenta;
 *  la API de verdad no lo manda y entonces no se pinta kcal, en vez de inventarla.*
 */
import datos from './recetas.json'

import type { Ingrediente, Receta, ResumenReceta } from '../api/recetas'

export interface RecetaDemo extends Omit<Receta, 'ingredientes'> {
  ingredientes: (Ingrediente & { kcal_100g?: number | null })[]
}

const DATOS = datos as unknown as { recetas: RecetaDemo[] }

export const RECETAS: RecetaDemo[] = DATOS.recetas

/** *Las kcal de la receta entera, sumando sus ingredientes. `null` si falta algún dato: un total
 *  con un hueco no es un total, y las calorías no se inventan.* */
export function kcalTotal(receta: RecetaDemo): number | null {
  let total = 0
  for (const ingrediente of receta.ingredientes) {
    const gramos = ingrediente.cantidad
    const kcal = ingrediente.kcal_100g
    if (gramos == null || kcal == null || !Number.isFinite(gramos) || !Number.isFinite(kcal)) {
      return null
    }
    total += (kcal * gramos) / 100
  }
  return Math.round(total * 10) / 10
}

/** *Las kcal por ración, que es la cifra que se compara: la misma receta para 2 o para 4 no
 *  cambia lo que come una persona.* */
export function kcalRacion(receta: RecetaDemo): number | null {
  const total = kcalTotal(receta)
  if (total == null || receta.raciones <= 0) return null
  return Math.round((total / receta.raciones) * 10) / 10
}

/** *Lo que necesita el recetario: sin la preparación ni los ingredientes, con las kcal por
 *  ración para que la tarjeta pueda decirlas.* */
export function resumenDe(receta: RecetaDemo): ResumenReceta {
  return {
    id: receta.id,
    nombre: receta.nombre,
    creada: receta.creada,
    archivada: receta.archivada,
    version: receta.version,
    raciones: receta.raciones,
    minutos: receta.minutos,
    etiquetas: receta.etiquetas,
    kcal_racion: kcalRacion(receta),
  }
}

/** *La receta completa, con sus calorías. `raciones` permite escalar la lista de ingredientes
 *  sin tocar la receta guardada, como hace la API.* */
export function recetaDe(id: number, raciones?: number | null): Receta | null {
  const receta = RECETAS.find((r) => r.id === id)
  if (!receta) return null
  const factor = raciones != null && raciones > 0 ? raciones / receta.raciones : 1
  const total = kcalTotal(receta)
  return {
    ...receta,
    ingredientes: receta.ingredientes.map((i) => ({
      ...i,
      cantidad: i.cantidad == null ? null : Math.round(i.cantidad * factor * 10) / 10,
    })),
    raciones: raciones != null && raciones > 0 ? raciones : receta.raciones,
    raciones_receta: receta.raciones,
    escalada: factor !== 1,
    kcal_total: total == null ? null : Math.round(total * factor * 10) / 10,
    kcal_racion: kcalRacion(receta),
  } as Receta
}
