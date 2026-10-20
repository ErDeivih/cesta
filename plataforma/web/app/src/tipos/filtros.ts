/** *** LO QUE ES UN FILTRO DE BUSQUEDA, Y LO QUE ES UN FILTRO VACIO. ***
 *
 * *Esto vivia en `api/consultas.ts`, y ahi no pinta nada: es **un tipo y una constante**, no una
 * llamada al servidor.*
 *
 * *Y no era solo cuestion de orden: `estado/filtrosUrl.ts` los importaba de `api/consultas`, que
 * arrastra el cliente HTTP, y por eso `node --test` no podia cargar `filtrosUrl.ts` -- el mismo
 * `ERR_MODULE_NOT_FOUND` que tenian `frase.ts` y `curva.ts`.*
 *
 * *** Un tipo no deberia arrastrar un cliente HTTP. ***
 */

export interface FiltrosBuscar {
  q: string
  cadenas: string[]
  seccion: string
  comparables: boolean
  conNutricion: boolean
  ofertas: boolean
  marcaPropia: boolean
  sinAlcohol: boolean
  sellos: string[]
  conservacion: string
  limite: number
  /**
   * **Cuantos resultados se saltan**, para la pagina. *Vive en la URL como todo lo demas* -- asi un
   * enlace lleva a la pagina tres y volver atras devuelve a ella.
   *
   * *No cuenta como filtro*: `cuantosFiltros` mira campo a campo, y estar en la pagina 2 no es haber
   * puesto una traba a la busqueda.
   */
  desplazamiento: number
}

export const FILTROS_VACIOS: FiltrosBuscar = {
  q: '',
  cadenas: [],
  seccion: '',
  comparables: false,
  conNutricion: false,
  ofertas: false,
  marcaPropia: false,
  sinAlcohol: false,
  sellos: [],
  conservacion: '',
  limite: 40,
  desplazamiento: 0,
}
