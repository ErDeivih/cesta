/** **Cuando una espera deja de ser una espera y pasa a ser un atasco.**
 *
 *  Criterio de `F11`/`R08` y `F10`/`R05`: *lo que **no se sabe** no se puede decir como si se supiera.* *Y
 *  «Cargando...» **es una promesa**: dice que algo va a llegar.* **Cuando no va a llegar, decirlo es lo correcto**
 *  -- *y callarlo es lo que hace que alguien espere delante de una pantalla en blanco.*
 *
 *  **El problema, medido el 12 de octubre de 2026**: *React Query da `isLoading` mientras la consulta **no haya
 *  tenido nunca `data`** y **siga intentando**.* **Y si la consulta se atasca -- sin llegar a fallar --, `isLoading`
 *  es verdadero para siempre**, *y la pantalla dice «Cargando...» **indefinidamente***: *le paso a la cocina (con
 *  `refetchInterval`) **y a la despensa, que no lo tiene**.*
 *
 *  **Y por que esta aqui y no dentro del gancho**: *el proyecto prueba **funciones puras** con `node --test`
 *  (`plataforma/web/app/tests/`), y **no tiene renderizador de pruebas**.* *Asi que **la decision se saca a una
 *  funcion** -- *que se prueba* --, **y el gancho se queda con el reloj**, que es lo unico que necesita React.
 */

/** **Si una espera con `cargando` cuenta ya como atascada.**
 *
 *  *Recibe si sigue cargando y **cuanto ha pasado**, y no un reloj: **asi se puede probar sin esperar de verdad**.*
 */
export function estaAtascada(cargando: boolean, transcurridoMs: number, segundos = 10): boolean {
  // **Si ya no carga, no hay atasco** -- *aunque haya tardado mucho: **llego**.*
  if (!cargando) return false
  // **Y el limite es «a partir de», no «mas de»**: *a los diez segundos exactos, ya se dice.*
  return transcurridoMs >= segundos * 1000
}
