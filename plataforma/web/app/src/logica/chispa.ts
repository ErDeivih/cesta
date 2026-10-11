/** Que se dibuja en una chispa, y que no. **Sin uPlot y sin DOM: se puede probar.**
 *
 *  Existe porque las tres reglas de esta decision son de G05 y hay que fijarlas con una prueba, no
 *  con un `tsc` verde -- *compilar no es acertar*. Las tres salen del mismo principio: **lo que no se
 *  observo no se puede dibujar como si se hubiera observado**.
 *
 *  - **Un hueco es un hueco**: un `null` entre dos precios se conserva como `null`. *G05: «no
 *    conectar datos ausentes como si hubiera observaciones».*
 *  - **Una fecha ilegible no es 1970**: el punto se descarta y se cuenta. *G05: «no convertir
 *    ausencias en cero»*; antes iba al origen del eje y arrastraba la escala.
 *  - **De una serie vacia no se infiere nada**: por eso el resultado lleva `dibujable`, y quien
 *    pinta dice que **no hay serie**, no que haya un solo dia. *G05: «no inferir "solo un dia" de una
 *    serie vacia».*
 *
 *  Y devuelve la **cobertura**, en la forma que el proyecto ya usa en `estado/cocina.ts`
 *  (`{valor, faltantes}`): *cuantos puntos se dibujan y cuantos se quedaron fuera por no tener dato
 *  o por no tener fecha*. Sin eso, un hueco y una ausencia se ven igual.
 */
export interface PuntoChispa {
  fecha: string
  valor: number | null
  /** **La unidad con la que se midio ESE dia.** La API puede no mandarla. */
  unidad?: string | null
}

export interface SerieDeChispa {
  /** Lo que se dibuja: una x por punto valido, con `null` donde no hubo observacion. */
  xs: number[]
  ys: (number | null)[]
  /** Puntos recibidos. */
  total: number
  /** Con fecha legible y en la serie, aunque el valor sea `null`: **un hueco cuenta como punto**. */
  dibujados: number
  /** Descartados por fecha ilegible o vacia: **no se colocan en el eje**. */
  sinFecha: number
  /** `false` cuando no hay nada que dibujar. **No significa «un solo dia».** */
  dibujable: boolean
  /** Las unidades distintas que traia la serie, si traia mas de una. */
  unidades: string[]
  /** **Por que no se dibuja, cuando es por la unidad.** Mismo criterio y mismas palabras que
   *  `logica/curva.ts`: *«tres dias en `kg` y uno en `ud` son dos series pegadas, y el minimo de las
   *  dos juntas no es el minimo de nada»*. Y `api/alertas.py` ya dice lo mismo: *«si la unidad
   *  cambio, no es una bajada»*. **La chispa era la unica pieza del sistema que lo ignoraba.** */
  motivoUnidad: string | null
}

/** La fecha en milisegundos, o `null` si no es una fecha. */
export function aMs(fecha: string): number | null {
  if (!fecha) return null
  const t = new Date(fecha.length <= 10 ? `${fecha}T00:00:00` : fecha).getTime()
  return Number.isNaN(t) ? null : t
}

export function serieDeChispa(puntos: PuntoChispa[]): SerieDeChispa {
  const validos: { x: number; y: number | null; u: string | null }[] = []
  let sinFecha = 0
  for (const p of puntos) {
    const x = aMs(p.fecha)
    if (x === null) {
      sinFecha += 1
      continue
    }
    validos.push({
      x,
      y: p.valor === null || !Number.isFinite(p.valor) ? null : p.valor,
      u: p.unidad ?? null,
    })
  }
  // **La unidad, si la API la manda.** Se miran solo los puntos que se van a dibujar: un punto
  // descartado no puede decidir que la serie mezcla unidades.
  const unidades = [...new Set(validos.map((q) => q.u).filter((u): u is string => Boolean(u)))]
  const mezcla = unidades.length > 1
  const motivoUnidad = mezcla
    ? `La unidad de este producto cambió en el histórico (${unidades.join(', ')}), ` +
      'así que el precio de esos días no se puede comparar con el de hoy.'
    : null

  return {
    xs: validos.map((q) => q.x),
    ys: validos.map((q) => q.y),
    total: puntos.length,
    dibujados: validos.length,
    sinFecha,
    // **Con dos unidades no se dibuja una linea**: se dice por que, como hace `curva.ts`.
    dibujable: validos.length > 0 && !mezcla,
    unidades,
    motivoUnidad,
  }
}

/** Una fila de la tabla accesible: **los huecos van incluidos y se ven como huecos.**
 *
 *  La aceptacion de G05 pide «tabla accesible de los mismos datos», y aqui «los mismos» incluye lo
 *  que no hay: *una tabla que omitiera las fechas sin precio haria invisible justo el hueco que la
 *  chispa ha dejado de tapar*. Por eso el hueco es una fila con `valor: null` y su texto lo dice.
 */
export interface FilaDeChispa {
  fecha: string
  valor: number | null
  /** Lo que se lee en la celda. **Un hueco se lee como «sin dato», nunca como 0 ni vacio.** */
  texto: string
}

export function filasDeChispa(puntos: PuntoChispa[], unidad = ''): FilaDeChispa[] {
  const sufijo = unidad ? ` ${unidad}` : ''
  return puntos.map((p) => {
    const hay = p.valor !== null && Number.isFinite(p.valor)
    return {
      fecha: p.fecha,
      valor: hay ? (p.valor as number) : null,
      texto: hay ? `${p.valor}${sufijo}` : 'sin dato',
    }
  })
}
