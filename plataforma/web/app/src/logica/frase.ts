/** La frase que contesta «¿esto esta caro?», antes que ninguna tabla.
 *
 *  Punto 3 del encargo de UX, y su razon es literal: *"«¿Esto esta caro?» hoy se
 *  contesta con una tabla, y una tabla no es una respuesta"*. El orden que pide es
 *  este: **primero una frase**, despues el ahorro en euros, despues la curva, y
 *  **solo al final la tabla**. Nadie mira cinco precios en una columna para decidir
 *  si coge el paquete que tiene en la mano: mira una frase y decide.
 *
 *  **Y la regla que no se salta: si el grupo no es de fiar, NO se inventa la
 *  frase.** Un grupo mal emparejado da frases seguras y falsas («es el mas barato
 *  de las cinco») sobre productos que no son el mismo, y eso es peor que no decir
 *  nada: la tabla al menos se puede mirar con desconfianza, una frase se cree.
 *  Cuando no hay frase, la pantalla tiene que decir **por que** no la hay.
 *
 *  Esta funcion no pinta nada: solo decide que se dice. Se separa para poder
 *  probarla y para que la regla no acabe enterrada en medio del JSX de una ficha.
 */

/** Lo que hace falta para decidir la frase. Todos los datos vienen de `/api/grupo`. */
/** *** LO QUE LA FRASE NECESITA DEL FORMATO, Y QUE LE DA QUIEN LA LLAMA. ***
 *
 * *Antes esto importaba `euros` y `nombreCadena` de `../api/formato`.* *Y `api/formato` arrastra cosas
 * que la aplicacion usa en el navegador, asi que **`node --test` no podia ni cargar este modulo**: la
 * prueba se quedaba en `ERR_MODULE_NOT_FOUND`.*
 *
 * *No es un problema de la aplicacion -- funciona en el navegador -- sino de **testabilidad**, y es el
 * mismo que `gasto.ts` documenta haber tenido y resuelto.*
 *
 * *Se podria haber copiado aqui un `euros` de tres lineas. No se ha hecho: **duplicar el formato es
 * garantizar que algun dia digan cosas distintas**.* *En su lugar, el modulo **pide** las dos funciones y
 * cada llamador pasa las suyas -- las de `api/formato`, que siguen siendo las unicas.*
 *
 * *Y eso ademas deja probarlo: en la prueba se pasan dos dobles triviales y se comprueba la tabla de
 * decision sin arrastrar el navegador.*
 */
export interface FormatoDeLaFrase {
  /** *Centimos a texto: `€` con coma decimal.* */
  euros: (centimos: number) => string
  /** *El nombre de la cadena como se escribe: `Mercadona`, no `mercadona`.* */
  nombreCadena: (cadena: string) => string
}

export interface DatosParaLaFrase {
  /** Cuantas cadenas distintas tienen este producto. */
  cadenas: number
  /** Diferencia entre la mas cara y la mas barata, en % y en centimos. */
  ahorro_pct: number
  ahorro_cent: number
  /** Si la comparacion es de fiar. Si no lo es, no hay frase, y esto no es una opinion. */
  fiable: boolean
  /** La cadena mas barata del grupo, para nombrarla. */
  cadena_mas_barata?: string | null
  /** La cadena del producto que se esta mirando, si se mira una ficha concreta. */
  cadena_de_este?: string | null
  /** Precio por unidad del que se mira, y el minimo del grupo, para el % exacto. */
  precio_unidad_este?: number | null
  precio_unidad_minimo?: number | null
}

/** Una frase, o `null` si no hay nada honesto que decir.
 *
 *  **Las palabras que salen en pantalla llevan sus tildes, y el nombre de la cadena va como
 *  se llama.** Hasta el 27 de septiembre de 2026 esta funcion decia «Cuesta un 41 % mas que en
 *  mercadona.»: sin tilde en «más» y con la cadena en minusculas, mientras el resto de la
 *  aplicacion escribe «Todavía no tienes lista» y «Mercadona». Esta es **la frase que mas se
 *  lee de toda la aplicacion** -- es la respuesta a la pregunta 2 --, y se juzga contra alguien
 *  que lee español, no contra el codigo. Se vio en una captura.
 *
 *  La tabla de decision, que es lo unico que hay que mirar para saber si esto
 *  funciona:
 *
 *      fiable  cadenas  caso                            frase
 *      no      cualq.   el grupo no es de fiar          null
 *      si      1        una sola cadena                 null
 *      si      2+       es la mas barata                "Es la más barata de las N cadenas."
 *      si      2+       hay mas barato                  "Cuesta un X % más que en CADENA."
 *      si      2+       empate (0 %)                    "Está al mismo precio en N cadenas."
 *
 *  Un `null` no es un fallo de la funcion: es la respuesta correcta cuando no hay
 *  comparacion que hacer o cuando no nos la creemos.
 */
export function fraseDePrecio(d: DatosParaLaFrase, formato: FormatoDeLaFrase): string | null {
  if (!d.fiable) return null
  if (d.cadenas < 2) return null

  const este = d.precio_unidad_este
  const minimo = d.precio_unidad_minimo
  const barata = d.cadena_mas_barata ?? null

  // Sin los dos precios por unidad no se puede decir el porcentaje exacto, y
  // decirlo a ojo con el `ahorro_pct` del grupo seria hablar del grupo entero
  // como si fuera de este producto. Mejor la frase sin numero que un numero falso.
  if (este == null || minimo == null) {
    return barata ? `La más barata está en ${formato.nombreCadena(barata)}.` : null
  }

  // Empate: no hay ahorro que anunciar, y decir "un 0 % mas barato" es ruido.
  if (este <= minimo) {
    const cuantas = d.cadenas === 2 ? 'las dos cadenas' : `las ${d.cadenas} cadenas`
    return este === minimo && d.ahorro_cent === 0
      ? `Está al mismo precio en ${cuantas}.`
      : `Es la más barata de ${cuantas}: te ahorras ${formato.euros(d.ahorro_cent)} ` +
        `frente a la más cara.`
  }

  const mas = Math.round((100 * (este - minimo)) / minimo)
  return barata
    ? `Cuesta un ${mas} % más que en ${formato.nombreCadena(barata)}.`
    : `Cuesta un ${mas} % más que la más barata.`
}
