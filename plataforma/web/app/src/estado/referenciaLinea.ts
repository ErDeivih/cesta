/** Una ficha concreta no autoriza una sustitucion por otro miembro del grupo. */
export function referenciaLinea(grupoId?: number, productoId?: string) {
  if (productoId) return { grupo_id: null, producto_id: productoId }
  if (grupoId !== undefined) return { grupo_id: grupoId, producto_id: null }
  throw new Error('Falta el producto que quieres añadir.')
}
