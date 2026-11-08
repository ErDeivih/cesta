/** Llevarse la lista: **texto para pegar y CSV para abrir en otra app**. Sin precios, sin
 *  cuentas y sin llamar a ninguna cadena.
 *
 *  El CSV que se exporta es el mismo formato simple que acepta `PegarEnLaLista`:
 *  `nombre,cantidad,nota`. Asi se puede sacar una lista y volver a meterla sin inventar columnas.
 */
import type { Linea } from '../tipos'

function celdaCSV(valor: string | number | null | undefined): string {
  const texto = valor == null ? '' : String(valor)
  return `"${texto.replace(/"/g, '""')}"`
}

/** CSV con cabecera. Se entrecomilla todo para que una nota con comas o saltos no rompa la fila. */
export function listaACSV(lineas: Linea[]): string {
  const filas = ['nombre,cantidad,nota']
  for (const linea of lineas) {
    filas.push([
      celdaCSV(linea.nombre_visto),
      celdaCSV(linea.cantidad),
      celdaCSV(linea.nota ?? ''),
    ].join(','))
  }
  return `${filas.join('\r\n')}\r\n`
}

/** Texto para pegar en una nota, un mensaje o la lista de otra app. */
export function listaATexto(lineas: Linea[]): string {
  return lineas
    .map((linea) => {
      const cantidad = linea.cantidad > 1 ? `${linea.cantidad} x ` : ''
      const nota = linea.nota ? ` (${linea.nota})` : ''
      return `${cantidad}${linea.nombre_visto}${nota}`
    })
    .join('\n')
}

/** Nombre de fichero seguro: sin barras, sin acentos raros y sin quedarse vacio. */
export function nombreDeFichero(nombreLista: string): string {
  const limpio = nombreLista
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
  return `cesta-${limpio || 'lista'}.csv`
}
