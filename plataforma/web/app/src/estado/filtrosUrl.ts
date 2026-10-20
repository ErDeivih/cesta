/** Los filtros del buscador viven en la URL, no en el estado del componente.
 *
 *  Tres motivos, y ninguno es estetico:
 *   - Volver atras desde una ficha devuelve a la MISMA busqueda, con sus
 *     filtros. Con el estado en memoria, volver deja la pantalla en blanco.
 *   - Se puede mandar un enlace a "leche sin lactosa de Dia y Alcampo".
 *   - Guardar una combinacion de filtros es guardar una cadena de texto, sin
 *     inventar un formato aparte ni un endpoint que no existe.
 */
import { FILTROS_VACIOS, type FiltrosBuscar } from '../tipos/filtros.ts'

const booleanos = ['comparables', 'conNutricion', 'ofertas', 'marcaPropia', 'sinAlcohol'] as const

export function leerFiltros(params: URLSearchParams): FiltrosBuscar {
  const lista = (clave: string): string[] => {
    const v = params.get(clave)
    if (!v) return []
    return v
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean)
  }
  const limite = Number(params.get('limite') ?? '')
  const salto = Number(params.get('desplazamiento') ?? '')
  return {
    q: params.get('q') ?? '',
    cadenas: lista('cadenas'),
    seccion: params.get('seccion') ?? '',
    comparables: params.get('comparables') === 'true',
    conNutricion: params.get('conNutricion') === 'true',
    ofertas: params.get('ofertas') === 'true',
    marcaPropia: params.get('marcaPropia') === 'true',
    sinAlcohol: params.get('sinAlcohol') === 'true',
    sellos: lista('sellos'),
    conservacion: params.get('conservacion') ?? '',
    limite: Number.isFinite(limite) && limite > 0 ? limite : FILTROS_VACIOS.limite,
    // *Un desplazamiento que no sirve vuelve a cero*: **la primera pagina, que es lo unico que se puede
    // enseñar sin saber el total.**
    desplazamiento: Number.isFinite(salto) && salto > 0 ? Math.floor(salto) : 0,
  }
}

export function escribirFiltros(f: FiltrosBuscar): URLSearchParams {
  const p = new URLSearchParams()
  if (f.q.trim()) p.set('q', f.q.trim())
  if (f.cadenas.length) p.set('cadenas', f.cadenas.join(','))
  if (f.seccion) p.set('seccion', f.seccion)
  for (const b of booleanos) if (f[b]) p.set(b, 'true')
  if (f.sellos.length) p.set('sellos', f.sellos.join(','))
  if (f.conservacion) p.set('conservacion', f.conservacion)
  if (f.limite !== FILTROS_VACIOS.limite) p.set('limite', String(f.limite))
  // *Y no se escribe cuando es cero*: **la primera pagina es la URL sin nada**, y asi el enlace limpio
  // sigue siendo el enlace a la busqueda entera.
  if (f.desplazamiento > 0) p.set('desplazamiento', String(f.desplazamiento))
  return p
}

/** Cuantos filtros hay puestos, sin contar el texto. Se usa para el "3 filtros"
 *  del boton plegado: en un movil, cada fila de filtros es una fila de
 *  resultados que no se ve. */
export function cuantosFiltros(f: FiltrosBuscar): number {
  let n = 0
  if (f.cadenas.length) n += 1
  if (f.seccion) n += 1
  if (f.sellos.length) n += 1
  if (f.conservacion) n += 1
  for (const b of booleanos) if (f[b]) n += 1
  return n
}
