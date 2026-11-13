/** Buscar productos del catálogo para una línea que se acaba de importar.
 *
 *  **No existe un endpoint de "adivina qué producto es"**: se usa el buscador que ya hay y se
 *  enseñan pocos candidatos. La persona elige; si no elige, la línea se guarda como texto libre.
 *  Nunca se vincula sola.
 */
import { pide } from './cliente'
import type { RespuestaBuscar, ResultadoBusqueda } from '../tipos'

export async function buscarProductos(
  texto: string,
  limite = 3,
  /** *Se corta si el texto cambió: el buscador con sugerencias pregunta en cada pausa y una
   *  respuesta vieja no puede pisar a la nueva.* */
  senal?: AbortSignal,
): Promise<ResultadoBusqueda[]> {
  const r = await pide<RespuestaBuscar>('/buscar', { q: texto.trim(), limite }, senal)
  // Un resultado sin grupo no se puede enlazar: se queda como texto, no como un vínculo falso.
  return (r.resultados ?? []).filter((x) => x.grupo_id !== null)
}
