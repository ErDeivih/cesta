/**
 * El buscador y los filtros del recetario. **Sin dependencias, para poder probarlo.**
 *
 * G12 pide en su 218 *«biblioteca, **busqueda/filtros**, crear/editar/versionar/archivar…»*, y el
 * recetario tenia la biblioteca y no tenia buscador. **Es la primera funcion de interfaz que este
 * encargo encuentra ausente** -- en once paquetes, todo lo demas estaba escrito.
 *
 * **Se filtra en el cliente y no en el servidor, y eso es una decision, no una comodidad.** La lista
 * que llega ya viene **filtrada por dueno** desde `almacen.listas_de`/`recetas.listar(con, propietario)`
 * -- *que es la puerta del 223: «privadas por defecto»* --, asi que **filtrar aqui no puede enseñar
 * nada que no fuera tuyo**: lo que se esconde es un subconjunto de lo que ya te tocaba. **Hacerlo en
 * el servidor anadiria un parametro mas que habria que recordar comprobar contra el dueno, y ese es
 * justo el sitio donde un olvido se convierte en una fuga.**
 */

/** Lo minimo que hace falta para filtrar. *El llamante pasa lo que tenga: no se inventa campos.* */
export interface RecetaParaFiltrar {
  id: number
  nombre: string
  /**
   * Las etiquetas de la ultima version, si las tiene.
   *
   * **Y puede venir de dos formas, porque el servidor manda una `string`.** La columna `etiquetas` de
   * `version` es texto, asi que llega tal cual -- *«cena,rapida» o el JSON segun como se guardara* --
   * y no una lista. **Se aceptan las dos**: *declarar solo la que yo esperaba fue un error de tipo que
   * `tsc` cazo, y la forma de arreglarlo no es cambiar el tipo del servidor sino aceptar la suya.*
   */
  etiquetas?: string | string[] | null
  archivada?: boolean
}

export interface Filtro {
  /** El texto buscado. *Vacio significa «todo».* */
  texto?: string
  /** Una etiqueta por la que filtrar. *Vacia o ausente significa «todas».* */
  etiqueta?: string | null
  /** Si se incluyen las archivadas. *Por defecto no: archivada no es borrada.* */
  incluirArchivadas?: boolean
}

/** Las palabras del texto, en minusculas y sin acentos. *«Atun» encuentra «atún».* */
function palabras(texto: string): string[] {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .split(/\s+/)
    .filter((p) => p.length > 0)
}

/** Lo mismo para comparar: sin acentos y sin mayusculas. */
function comparable(texto: string): string {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * Las recetas que pasan el filtro. **Y el orden no se toca**: *el que traia la lista es el del
 * servidor, y reordenar por parecido es lo que hace que una busqueda parezca que «encuentra» cosas.*
 *
 * **Todas las palabras tienen que aparecer**, no una: *buscar «tortilla patata» y que salga cualquier
 * tortilla es peor que no encontrar nada, porque te hace leer la lista entera.*
 */
export function filtraRecetas<T extends RecetaParaFiltrar>(recetas: T[], filtro: Filtro = {}): T[] {
  const buscadas = palabras(filtro.texto ?? '')
  const etiqueta = filtro.etiqueta ? comparable(filtro.etiqueta) : null

  return recetas.filter((r) => {
    // **Archivada no es borrada, pero tampoco es lo que se busca.** *Sale solo si se pide.*
    if (r.archivada && !filtro.incluirArchivadas) return false

    if (etiqueta) {
      if (!etiquetasDeUna(r).map(comparable).includes(etiqueta)) return false
    }

    if (buscadas.length > 0) {
      const heno = comparable(r.nombre)
      if (!buscadas.every((p) => heno.includes(p))) return false
    }
    return true
  })
}

/**
 * **Las etiquetas de una receta, vengan como vengan.** *Una lista se usa tal cual; una cadena se parte
 * por comas -- que es como se guardan -- y se le quitan los corchetes si venia como JSON.*
 */
export function etiquetasDeUna(r: RecetaParaFiltrar): string[] {
  const crudo = r.etiquetas
  if (!crudo) return []
  if (Array.isArray(crudo)) return crudo.filter((e) => !!e)
  return crudo
    .replace(/^\s*\[|\]\s*$/g, '')
    .split(',')
    .map((e) => e.trim().replace(/^["']|["']$/g, ''))
    .filter((e) => e.length > 0)
}

/** Todas las etiquetas que aparecen, ordenadas y sin repetir. *Para pintar el desplegable.* */
export function etiquetasDe(recetas: RecetaParaFiltrar[]): string[] {
  const vistas = new Set<string>()
  for (const r of recetas) for (const e of etiquetasDeUna(r)) vistas.add(e)
  return [...vistas].sort((a, b) => a.localeCompare(b, 'es'))
}

/**
 * **Que decir cuando no sale nada.**
 *
 * *Un filtro que esconde todo sin decir por que es lo mismo que una lista vacia* -- y peor, porque
 * parece que no tienes recetas. **Asi que el vacio se explica con el filtro que lo causo**, que es la
 * costumbre del proyecto: *decir lo que falta en vez de enseñar un cero.*
 */
export function textoDelVacio(filtro: Filtro, cuantasHay: number): string {
  const partes: string[] = []
  if (filtro.texto?.trim()) partes.push(`«${filtro.texto.trim()}»`)
  if (filtro.etiqueta) partes.push(`la etiqueta «${filtro.etiqueta}»`)
  if (partes.length === 0) {
    // **Sin filtro y sin nada: es que no hay recetas, y eso se dice sin rodeos.**
    return cuantasHay === 0 ? 'Todavia no hay recetas.' : 'No hay nada que enseñar.'
  }
  const cuantas = cuantasHay === 1 ? '1 receta' : `${cuantasHay} recetas`
  return `Ninguna receta coincide con ${partes.join(' y ')}. Hay ${cuantas} en total.`
}
