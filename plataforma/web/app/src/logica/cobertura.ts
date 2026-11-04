/** La frase de cobertura de una cadena: lo que se ha medido, en palabras.
 *
 *  **De donde sale.** `GET /api/estado` manda, por cadena, un bloque `cobertura` que hasta el
 *  4 de noviembre de 2026 solo traia Lidl. *Y no era casualidad: Lidl es la unica cuyo catalogo es
 *  **parcial**, y sin decirlo sus 91 fichas se leen como «Lidl tiene 91 productos».* Las cinco
 *  cadenas que catalogan entero ahora tambien mandan su cobertura **medida** -- filas de hoy contra
 *  la referencia de su mejor dia, el `%`, de que dia es esa referencia y cuantos precios se han
 *  movido respecto a la captura anterior.
 *
 *  **Aqui no hay numeros escritos a mano.** Todo sale del bloque que manda la API. *Si un campo
 *  falta, la frase pierde esa parte y no se rellena con un cero* -- que es la regla de toda la app:
 *  un dato que no tenemos no se inventa. Y **los codigos no se pintan**: `catalogo_diario` y
 *  `ofertas_semanales_parcial` son claves de fichero, no frases; un codigo crudo en pantalla se lee
 *  como un fallo. Si llega un codigo que esta version no conoce, se usa su `etiqueta` legible si la
 *  trae, y si no, no se dice nada.
 *
 *  Es una funcion pura a proposito -- no sabe de React ni de la API -- para poder probarla sola y
 *  para que la pantalla que la pinte no tenga que repetir ninguna decision de formato.
 */
import { fecha, numero, porcentaje } from '../api/formato.ts'
import type { CoberturaCadena } from '../tipos.ts'

/** Un numero medido, o `null` si lo que llega no es un numero.
 *
 *  *No es paranoia: el bloque lo escribe un fichero JSON que puede venir a medias, con un `null`
 *  donde tocaba un numero o con un `NaN` de un `parseFloat` que fallo.* **Un `null` no es un cero.**
 */
function medida(valor: unknown): number | null {
  return typeof valor === 'number' && Number.isFinite(valor) ? valor : null
}

/** La frase de cobertura de una cadena, o `null` si no hay nada honesto que decir. */
export function textoCobertura(cobertura: CoberturaCadena | undefined | null): string | null {
  const codigo = cobertura?.cobertura
  if (!codigo) return null

  if (codigo === 'ofertas_semanales_parcial') {
    // *El texto de Lidl, que estaba medido y se queda tal cual.*
    const conPrecio = medida(cobertura?.con_precio)
    const leidas = medida(cobertura?.fichas_leidas)
    const base = 'ofertas semanales, no el catálogo entero'
    return conPrecio !== null && leidas !== null ? `${base} · ${conPrecio} de ${leidas} con precio` : base
  }

  if (codigo === 'catalogo_diario') {
    const partes = ['catálogo diario']

    const filas = medida(cobertura?.filas)
    // *Un cero de filas no se pinta como «0 filas»: un catalogo vacio no es una medida, es un
    // fallo de captura, y decirlo con una cifra lo disfrazaria de dato. Y se dice «capturadas»
    // porque son las filas del **bronce** del dia, no los productos del gold publicado: el 4/11
    // Aldi capturo 2.709 y publico 2.499.*
    if (filas !== null && filas > 0) partes.push(`${numero(filas, 0)} filas capturadas`)

    const pct = medida(cobertura?.pct)
    if (pct !== null) {
      // *Contra que se mide el `%`: una referencia sin fecha no se puede juzgar.*
      const deQueDia = cobertura?.referencia_fecha ? ` del ${fecha(cobertura.referencia_fecha, true)}` : ''
      partes.push(`${porcentaje(pct)} de su referencia${deQueDia}`)
    }

    const cambiados = medida(cobertura?.novedad?.cambiados)
    if (cambiados !== null) partes.push(`${numero(cambiados, 0)} precios cambiados`)

    return partes.join(' · ')
  }

  const etiqueta = cobertura?.etiqueta?.trim()
  return etiqueta ? etiqueta : null
}
