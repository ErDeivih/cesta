/** Lo que el reparto **no** cuenta: el transporte y el tiempo.
 *
 *  G05 lo pide en Compra, y lo pide con estas palabras: *«declarar cuantas lineas tienen precio,
 *  restricciones de tiendas/club/ofertas, referencia contra la que se compara **y si falta
 *  transporte**»*.
 *
 *  **Y no aparecia en ninguna parte del proyecto.** El reparto compara el total de dos tiendas **como
 *  si llegar a las dos costara lo mismo que llegar a una**, y no es lo mismo: *el ahorro de repartir
 *  puede ser menor que el viaje.* No es un error de calculo -- la cuenta esta bien -- es una omision de
 *  contexto, y aqui se dice.
 *
 *  Puro y sin dependencias, como `chispa.ts`, `gasto.ts` y `costeReceta.ts`: `node --test` lo carga y
 *  la regla se prueba en un segundo. *Y la frase se decide aqui y no en la pantalla, porque «comparar
 *  dos tiendas sin decir que son dos viajes» tiene que estar cubierto por una prueba, no por un
 *  descuido de quien escriba el texto.*
 */

/** La frase que dice lo que el total no incluye. **Siempre hay una**, con una tienda o con cinco. */
export function avisoDeTransporte(tiendas: number): string {
  const una = 'El total no incluye el transporte ni el tiempo: es lo que cuesta la compra, no el viaje.'
  if (!Number.isFinite(tiendas) || tiendas <= 1) {
    return una
  }
  // **Con mas de una tienda se nombra el viaje**, que es cuando el aviso cambia una decision.
  return `${una} Con ${tiendas} tiendas hay ${tiendas} viajes, y el ahorro puede ser menor que el ` +
    `${tiendas === 2 ? 'segundo viaje' : 'tiempo de hacerlos'}.`
}

/** Si el aviso tiene que mencionar que hay mas de un viaje. Sirve para la prueba y para la pantalla. */
export function hayVariosViajes(tiendas: number): boolean {
  return Number.isFinite(tiendas) && tiendas > 1
}
