/**
 * A03 — Si el precio de un producto puede recomendar una tienda, y por que no.
 *
 * **Esto vivia dentro de `Grupo.tsx` y tenia tres defectos, medidos el 12 de octubre de 2026.**
 * Sacarlo aqui es lo que permite probarlos: *la decision es una funcion pura con reloj controlado, y el
 * componente se queda con el reloj de verdad.* **Es el mismo camino que se tomo con `estaAtascada`** --
 * *y por la misma razon: un renderizador no hace falta para probar una regla.*
 *
 * **Los tres defectos, uno a uno:**
 *
 * 1. **La fecha se tomaba de la cadena, no del producto.** *`cadenas.find(...).ultimo_dia` es la ultima
 *    captura de la cadena **entera**: si Mercadona habia capturado otra cosa hoy, un producto cuya
 *    ultima ficha era de hace una semana **pasaba por fresco**.* **La fecha de la cadena no dice nada
 *    de este producto.**
 * 2. **Un precio sin fecha decidia.** *No se puede saber si es de hoy o de hace un mes, y recomendar una
 *    tienda con el es afirmar lo que no se sabe.*
 * 3. **La antiguedad se medía contra el dia del catalogo.** *Asi, un catalogo que dejara de actualizarse
 *    mantendria frescos sus precios **para siempre**.*
 *
 * **Y el criterio de aceptacion de A03, que es lo que las pruebas comprueban**: *dejar de ingerir cuatro
 * dias tiene que quitar las recomendaciones vigentes **sin borrar ningun dato**.*
 */

/** Que se puede decir de un precio, y por que. */
export type Juicio = {
  /** Si este precio puede decidir donde comprar. */
  decide: boolean
  /** Por que no, en palabras que se puedan enseñar. `null` cuando si decide. */
  motivo: string | null
}

/** Lo que hace falta saber de un precio para juzgarlo. *Nada de la ficha entera: solo esto.* */
export type PrecioAJuzgar = {
  /** La cadena de la que es. */
  fuente: string
  /** El precio por unidad en centimos, o `null` si no se tiene. */
  precioUnidadCent: number | null
  /** De que dia es **el precio de este producto en esa cadena**, o `null` si no se sabe. */
  ultimoDia: string | null
}

export type Contexto = {
  /** Hoy, inyectable. *Es lo que permite probar sin esperar a que pase el tiempo.* */
  hoy: Date
  /** Cuantos dias puede tener un precio y seguir decidiendo. */
  diasValidos: number
  /** Si el catalogo publicado es incoherente con sus precios. *Cuando lo es, no decide nada.* */
  publicacionIncoherente: boolean
  /** El nombre de la cadena, para el texto del motivo. */
  nombreCadena: (fuente: string) => string
  /** Formatea una fecha para el texto del motivo. */
  fechaTexto: (iso: string) => string
}

/** La diferencia en dias entre una fecha ISO y hoy. `null` si la fecha no sirve. */
export function diasDesde(iso: string | null | undefined, hoy: Date): number | null {
  if (!iso) return null
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!partes) return null
  const dia = new Date(Number(partes[1]), Number(partes[2]) - 1, Number(partes[3]))
  if (Number.isNaN(dia.getTime())) return null
  const referencia = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  return Math.round((referencia.getTime() - dia.getTime()) / 86_400_000)
}

/**
 * La decision, entera y en orden. **El orden importa**: *lo que se sabe que esta mal corta antes que lo
 * que no se sabe, porque son motivos distintos y se leen distinto.*
 */
export function juzgaPrecio(p: PrecioAJuzgar, ctx: Contexto): Juicio {
  // 1) **Un catalogo incoherente no recomienda nada.** *Lo que se sirve no es lo que se publico, asi
  //    que ningun precio de aqui acredita nada -- ni el que parece bueno.*
  if (ctx.publicacionIncoherente) {
    return {
      decide: false,
      motivo:
        'La versión del catálogo y sus precios no son coherentes. No se recomienda una tienda con estos datos.',
    }
  }
  // 2) **Sin precio por unidad no hay comparacion posible.** *No es que sea malo: es que falta.*
  if (p.precioUnidadCent === null || !(p.precioUnidadCent > 0)) {
    return {
      decide: false,
      motivo: 'No tenemos el precio por unidad de este producto, así que no entra en la comparación.',
    }
  }
  // 3) **Sin fecha, no decide** -- *y esto era el defecto 2.*
  if (!p.ultimoDia) {
    return {
      decide: false,
      motivo:
        'No sabemos de qué día es el precio de este producto, así que no decide. Se enseña como dato.',
    }
  }
  // 4) **Viejo contra HOY, no contra el dia del catalogo** -- *y esto era el defecto 3.*
  const dias = diasDesde(p.ultimoDia, ctx.hoy)
  if (dias === null) {
    // *Una fecha que no se puede leer es una fecha que no se sabe: mismo trato que no tenerla.*
    return {
      decide: false,
      motivo: 'La fecha del precio de este producto no se puede leer, así que no decide.',
    }
  }
  if (dias > ctx.diasValidos) {
    return {
      decide: false,
      motivo: `El precio de ${ctx.nombreCadena(p.fuente)} es del ${ctx.fechaTexto(p.ultimoDia)} (${dias} días): se enseña con su fecha, pero no decide.`,
    }
  }
  // 5) *Y un precio del futuro tampoco: una fecha por delante de hoy es un dato que no cuadra.*
  if (dias < 0) {
    return {
      decide: false,
      motivo: `El precio de ${ctx.nombreCadena(p.fuente)} tiene fecha del ${ctx.fechaTexto(p.ultimoDia)}, que todavía no ha llegado: no se recomienda una tienda con eso.`,
    }
  }
  return { decide: true, motivo: null }
}
