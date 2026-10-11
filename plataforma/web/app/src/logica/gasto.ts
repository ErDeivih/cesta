/** Que se puede decir de un periodo de gasto. **Y por que `null` no es `0`.**
 *
 *  G05 lo pide en Compra: *«Gasto pagado semanal/mensual a partir de compras guardadas e importes
 *  conocidos. […] **Cobertura de importes historicos `NULL` visible**»*.
 *
 *  La regla, en una linea: **un periodo del que no se sabe el total no se pinta como cero euros.** Un
 *  «0,00 €» se lee «ese mes no gaste nada», y lo que pasa es que **no se sabe** -- y el numero sale
 *  ademas mas bajo de lo real, redondo y creible. Es la forma mas silenciosa de mentir que tiene esta
 *  aplicacion, y por eso la decision vive aqui, fuera de la pantalla, con sus pruebas.
 *
 *  Y la otra mitad: **cuando el total esta y no esta completo, se dicen las dos cosas.** *Un total
 *  parcial sin su aviso es una mentira por omision; un aviso sin el total no informa.*
 *
 *  **Sin dependencias, a proposito.** La primera version importaba `numero` de `api/formato`, y con eso
 *  **el fichero de pruebas del cliente no llegaba ni a cargar** -- `api/formato` arrastra lo que la
 *  aplicacion usa en el navegador. *El formato de un numero no es logica de negocio: aqui se devuelve
 *  **el numero y su condicion**, y el «150,00 €» lo compone quien pinta.* Es la misma disciplina que
 *  `logica/chispa.ts`, que no importa nada y por eso se prueba en un segundo.
 */

/** Una fila de `GET /api/listas/{id}/gasto`. */
export interface FilaDeGasto {
  /** `null` cuando la fila no tiene periodo (lineas sin fecha). */
  periodo: string | null
  /** En centimos, o `null` si **no se sabe**. Nunca `0` por no saber. */
  total_cent: number | null
  compras: number
  con_importe: number
  sin_importe: number
  /** Cuantas **lineas** se quedaron sin precio. */
  lineas_sin_precio?: number
  completo: boolean
}

/** **Si el total se sabe.** Es la pregunta que decide si se pinta un numero o se dice que no. */
export function totalConocido(fila: FilaDeGasto): boolean {
  return fila.total_cent !== null
}

/** El importe en centimos, o `null`. **`null` no es `0`**: uno se pinta y el otro se dice. */
export function importeEnCentimos(fila: FilaDeGasto): number | null {
  return fila.total_cent
}

/** Lo que falta, o `null` si no falta nada. **Se dice en lineas, no solo en compras.** */
export function textoDeLoQueFalta(fila: FilaDeGasto): string | null {
  if (fila.completo) return null
  const lineas = fila.lineas_sin_precio ?? 0
  if (lineas > 0) {
    return lineas === 1 ? 'falta 1 linea sin precio' : `faltan ${lineas} lineas sin precio`
  }
  if (fila.sin_importe > 0) {
    return fila.sin_importe === 1
      ? 'falta 1 compra sin importe'
      : `faltan ${fila.sin_importe} compras sin importe`
  }
  return null
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
  'septiembre', 'octubre', 'noviembre', 'diciembre']

/** El nombre del periodo, legible. */
export function textoDePeriodo(fila: FilaDeGasto, porSemana: boolean): string {
  if (fila.periodo === null) return 'Sin fecha'
  if (!porSemana) {
    const [anio, mes] = fila.periodo.split('-')
    return `${MESES[Number(mes) - 1] ?? mes} de ${anio}`
  }
  return fila.periodo.replace('-W', ' · semana ')
}
