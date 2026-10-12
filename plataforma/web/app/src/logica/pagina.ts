/**
 * A07 — La pagina de resultados: cuanto se pide, desde donde, y **cuando hay que volver al principio**.
 *
 * **Lo que faltaba, medido el 12 de octubre de 2026.** *La API ya recibia `desplazamiento`, pero
 * `FiltrosBuscar` no lo tenia*: **la pagina no estaba en la URL**, asi que no se podia compartir un
 * enlace a la pagina tres ni volver atras a ella. *Y por eso tampoco se reiniciaba: no habia nada que
 * reiniciar.*
 *
 * **Y la trampa que la revision avisa, que es la importante:**
 *
 * > *«no ordenar solo la pagina como si fuera el catalogo entero»*
 *
 * *Es el error clasico de la paginacion, y es silencioso*: **si se ordena lo que ya se trajo y luego se
 * corta, la primera pagina no tiene los mejores del catalogo, tiene los mejores de los primeros N.**
 * *El orden lo tiene que hacer el servidor sobre el universo entero* -- *y estas pruebas lo fijan, para
 * que nadie lo "arregle" en el cliente.*
 *
 * **Y la tercera cosa: fijar la version.** *Si el catalogo cambia entre la pagina 1 y la 2, la fila 40
 * de la primera puede ser la 20 de la segunda* -- **o repetirse, o desaparecer.** *Por eso la version
 * viaja con la peticion y, si cambio, se dice en vez de servir una lista que se solapa.*
 */

/** Lo que se pide al servidor para una pagina. *Solo esto: el orden no viaja aqui.* */
export type Peticion = {
  /** Cuantos resultados se quieren, como maximo. */
  limite: number
  /** Cuantos se saltan. **Multiplo del limite** si la pagina es la unica fuente de verdad. */
  desplazamiento: number
  /** La version del catalogo contra la que se pregunta, si se conoce. */
  version: string | null
}

/** El tope de resultados, con su valor por defecto. *El mismo que usa la pantalla.* */
export const LIMITE_POR_DEFECTO = 40

/** Cuantas paginas caben en un total. **Cero resultados son cero paginas**, no una. */
export function paginasDe(total: number, limite: number): number {
  if (!Number.isFinite(total) || total <= 0) return 0
  if (!Number.isFinite(limite) || limite <= 0) return 0
  return Math.ceil(total / limite)
}

/**
 * La pagina en la que esta un desplazamiento, empezando en 1. *Uno-based porque es lo que se enseña.*
 *
 * **Y se acota**: *un desplazamiento mas alla del final devuelve la ultima pagina*, no una pagina
 * inexistente -- *porque llegar ahi pasa de verdad, cuando el catalogo mengua entre dos peticiones.*
 */
export function paginaDe(desplazamiento: number, limite: number, total?: number): number {
  if (!Number.isFinite(limite) || limite <= 0) return 1
  const bruta = Math.floor(Math.max(0, desplazamiento) / limite) + 1
  if (total === undefined) return bruta
  const ultima = Math.max(1, paginasDe(total, limite))
  return Math.min(bruta, ultima)
}

/** El desplazamiento de una pagina, con la misma acotacion. *`pagina` empieza en 1.* */
export function desplazamientoDe(pagina: number, limite: number): number {
  if (!Number.isFinite(limite) || limite <= 0) return 0
  return Math.max(0, Math.floor(pagina) - 1) * limite
}

/**
 * **Cuando hay que volver a la pagina uno.**
 *
 * *La regla es una*: **si cambio lo que se pregunta, la pagina deja de significar lo mismo.** *Estar en
 * la pagina 4 de «leche» y cambiar a «pan» y seguir en la 4 no es «conservar el sitio»: es saltarse
 * las tres primeras paginas de pan*, que el servidor no ha enseñado nunca.
 *
 * *Y el tope tambien cuenta*: **con `limite` distinto, el mismo desplazamiento cae en otra pagina** --
 * *40 resultados por pagina desde el 80 es la tercera; desde el 20, la quinta.*
 *
 * **Lo que NO reinicia**: *nada que no cambie la pregunta. Y por eso se comparan los campos, no el
 * objeto* -- *dos objetos con el mismo contenido son la misma pregunta.*
 */
export function hayQueVolverAlPrincipio(
  antes: Record<string, unknown>,
  despues: Record<string, unknown>,
  claves: string[],
): boolean {
  for (const clave of claves) {
    const a = antes[clave]
    const b = despues[clave]
    // *Las listas se comparan por contenido y en orden*: `['a','b']` y `['b','a']` **no** son la misma
    // pregunta si el servidor las trata distinto, y aqui no se supone que las trate igual.
    if (Array.isArray(a) || Array.isArray(b)) {
      const aa = Array.isArray(a) ? a : []
      const bb = Array.isArray(b) ? b : []
      if (aa.length !== bb.length || aa.some((x, i) => x !== bb[i])) return true
      continue
    }
    if (a !== b) return true
  }
  return false
}

/** El estado de la paginacion, tal como se enseña. *Y `null` cuando no hay nada que enseñar.* */
export type EstadoDePagina = {
  pagina: number
  paginas: number
  /** Si se puede ir hacia atras. */
  hayAntes: boolean
  /** Si se puede ir hacia adelante. */
  hayDespues: boolean
  /** El aviso que hay que dar, si hay uno. */
  aviso: string | null
}

/**
 * **El estado, con el aviso de la version incluido.**
 *
 * *El aviso es lo que A07 pide con «fijar version o cursor»*: **si la version cambio entre paginas, la
 * lista se puede solapar o perder filas** -- *y eso **no se arregla en el cliente**, se dice.*
 *
 * *Cual es la version buena, y por que*: **la de la primera pagina**, porque es la que la persona vio.
 * *Un resultado que venga de otra version es de otro catalogo, aunque el numero de pagina cuadre.*
 */
export function estadoDePagina(
  desplazamiento: number,
  limite: number,
  total: number,
  versionPedida: string | null,
  versionQueLlego: string | null,
): EstadoDePagina {
  const paginas = paginasDe(total, limite)
  const pagina = paginaDe(desplazamiento, limite, total)
  const cambioLaVersion =
    versionPedida !== null && versionQueLlego !== null && versionPedida !== versionQueLlego
  return {
    pagina,
    paginas,
    hayAntes: pagina > 1,
    hayDespues: paginas > 0 && pagina < paginas,
    aviso: cambioLaVersion
      ? `El catálogo cambió mientras mirabas (${versionPedida} → ${versionQueLlego}): ` +
        'esta página puede repetir o saltarse resultados. Vuelve a empezar para verla entera.'
      : null,
  }
}
