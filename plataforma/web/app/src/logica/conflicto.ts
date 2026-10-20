/** *** LA COTIZACION NUEVA QUE MANDA UN 409 DE CIERRE. ***
 *
 * *Cuando el total cambia entre mirar la lista y cerrarla, el servidor contesta:*
 *
 *     { detalle, sello_visto, cotizacion_nueva }
 *
 * *donde `cotizacion_nueva` es el resultado entero de `cotiza`.*
 *
 * *** Y no es un «no»: es «lo que viste ha cambiado, mira la previa nueva y confirma». ***
 * *Hasta hace dos rondas el cuerpo se recibia y se tiraba, asi que la pantalla se quedaba en el aviso y el
 * unico camino era recargar.*
 *
 * *Aqui se decide **si hay algo que ofrecer**, y se comprueban los dos campos que hacen falta:*
 *   - **`sello`** ... *sin el no se puede reintentar con la cotizacion nueva*
 *   - **`total_cent`** ... *sin el no hay nada que enseñar*
 *
 * *** Si falta uno, se devuelve `null` y no se ofrece nada: un boton que reintenta con `undefined` seria
 * peor que no ofrecerlo. ***
 */

export interface CotizacionDelConflicto {
  sello: string
  total_cent: number
}

export function cotizacionDelConflicto(e: unknown): CotizacionDelConflicto | null {
  // *Solo un 409. Un 500 no manda cotizacion nueva, y un 404 menos.*
  if (typeof e !== 'object' || e === null) return null
  const err = e as { estado?: unknown; cuerpo?: unknown }
  if (err.estado !== 409) return null

  const cuerpo = err.cuerpo as { cotizacion_nueva?: unknown } | null
  const nueva = cuerpo?.cotizacion_nueva
  if (typeof nueva !== 'object' || nueva === null) return null

  const c = nueva as { sello?: unknown; total_cent?: unknown }
  if (typeof c.sello !== 'string' || !c.sello) return null
  if (typeof c.total_cent !== 'number' || !Number.isFinite(c.total_cent)) return null

  // *`total_cent: 0` es valido: un cero es un dato, no un hueco.*
  return { sello: c.sello, total_cent: c.total_cent }
}
