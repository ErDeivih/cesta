/** **Los puntos de las tres series**, a partir de lo que devuelve la API.
 *
 * *Tres funciones, una por serie, y las tres hacen lo mismo: **decir lo que hay, y `null` donde no hay**.*
 *
 * **Y la regla que importa esta en `puntosPrevistos`:** un dia con **varias comidas** se suma **solo si
 * todas traen su energia**. *Si a una le falta, el dia entero va a `null` y no a una suma parcial* -- *porque
 * **una suma parcial no es «lo previsto»: es lo previsto menos algo**, y quien la leyera creeria que el dia
 * esta cubierto. Es la misma regla de `diario.py`: «**lo que no se sabe sigue sin saberse**».*
 *
 * *Y por eso este fichero **solo importa el tipo** de `chispa.ts` (`import type`), que se borra al ejecutar:
 * asi `logica/` sigue siendo hojas, y se puede probar con `node --test`.*
 */
import type { PuntoChispa } from './chispa'

/** Un dia de `/api/diario/rango`. **`kcal_conocida` es `null` cuando no hay dato.** */
export interface DiaDeRango {
  fecha: string
  kcal_conocida: number | null
}

/** Un ingrediente de la prevision, como lo devuelve la API. */
export interface LineaDeLaApi {
  texto: string
  producto_id: string | null
  nutrientes: Record<string, number | null> | null
  motivo: 'sin_catalogo' | 'sin_cantidad' | null
}

/** Una comida de la prevision. */
export interface ComidaDeLaApi {
  fecha: string
  receta_id: number
  version: number
  comensales: number
  lineas: LineaDeLaApi[]
  /** *Los subtotales, tal y como los da la API -- que ya los calcula con `diario.resumen`.* */
  conocido: Record<string, number | null>
  cobertura: Record<string, { con_dato: number; total: number; completa: boolean }>
  completo: boolean
}

/** ***Lo registrado***: un punto por dia, y `null` donde la API no sabe. */
export function puntosRegistrados(dias: DiaDeRango[]): PuntoChispa[] {
  return dias.map((d) => ({ fecha: d.fecha, valor: d.kcal_conocida }))
}

/** ***Lo previsto***: **un punto por dia**, sumando sus comidas **solo si todas traen energia.**
 *
 * *Y si a una le falta, el dia va a `null` -- **no a la suma de las que si**, que se leeria como el dia
 * entero. Y no se pierde el dato: `cobertura` sigue diciendo de cuantas lineas sale cada numero.*
 */
export function puntosPrevistos(comidas: ComidaDeLaApi[]): PuntoChispa[] {
  const porDia = new Map<string, number | null>()
  for (const comida of comidas) {
    const kcal = comida.conocido?.kcal ?? null
    const antes = porDia.get(comida.fecha)
    if (kcal === null || antes === null) {
      // *Un dia con una comida sin energia **es un dia sin energia conocida**, y no la suma de las demas.*
      porDia.set(comida.fecha, null)
    } else {
      porDia.set(comida.fecha, (antes ?? 0) + kcal)
    }
  }
  return [...porDia.entries()].map(([fecha, valor]) => ({ fecha, valor }))
}

/** ***El objetivo***: **la clave `objetivo:<fecha>` que la persona haya puesto.**
 *
 * *Y **un dia sin objetivo no es un dia de cero**: no aparece, o aparece con `null`.* *Por eso se recorre el
 * calendario que se pide, y no las claves que hay: **un objetivo puesto para un dia sin datos tambien
 * cuenta.***
 */
export function puntosObjetivo(
  preferencias: Record<string, unknown> | null | undefined,
  fechas: string[],
): PuntoChispa[] {
  const prefs = preferencias ?? {}
  return fechas.map((fecha) => {
    const valor = prefs[`objetivo:${fecha}`]
    const kcal =
      valor && typeof valor === 'object' && 'kcal' in valor
        ? (valor as { kcal: unknown }).kcal
        : null
    return { fecha, valor: typeof kcal === 'number' ? kcal : null }
  })
}
