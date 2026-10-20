/** Lo que cuesta una receta: **lo que usas y lo que hay que comprar, y no son lo mismo**.
 *
 *  G05 lo pide en Recetas: *«nutricion por racion y coste estimado, **distinguiendo cantidad usada de
 *  coste de comprar envases**; **indicar ingredientes sin datos**»*.
 *
 *  **El caso que da sentido al modulo**: la receta dice «200 g de arroz» y el catalogo vende «1 kg por
 *  1,20 €». **Lo que usas cuesta 0,24 €; lo que compras cuesta 1,20 €.** Los dos numeros son ciertos y
 *  significan cosas distintas -- *lo que cuesta hacer el plato, y lo que sale de tu bolsillo hoy* --, y
 *  dar uno solo como «el coste de la receta» es elegir por quien lee sin decírselo.
 *
 *  **Y el caso que no se puede prorratear**: «2 huevos». *Un huevo no tiene fraccion: o compras el
 *  envase o no lo compras.* Ahi `costeUsadoCent` **es** el del envase, y decir otra cosa seria inventar
 *  una fraccion de huevo.
 *
 *  **Sin dependencias, a proposito**, como `logica/chispa.ts` y `logica/gasto.ts`: nada de `api/`, para
 *  que `node --test` lo cargue y las reglas se prueben en un segundo. *Y la cobertura va en la forma
 *  `{valor, faltantes}` que el proyecto usa en `estado/cocina.ts`: **los ingredientes sin datos se
 *  cuentan y se nombran**, porque un total sobre la mitad de los ingredientes no es el total.*
 */

/** Lo que el catalogo sabe de un ingrediente. Todo puede faltar. */
export interface PrecioDeIngrediente {
  /** El envase entero, en centimos. */
  precioEnvaseCent?: number | null
  /** Cuanto trae el envase, en la unidad del ingrediente (`500` para 500 g). */
  cantidadEnvase?: number | null
  /** `g`, `ml` o `ud`. **En `ud` no se prorratea.** */
  unidadEnvase?: string | null
  /** €/unidad ya normalizado, si el catalogo lo trae. *Si no, se deduce del envase.* */
  precioUnidadCent?: number | null
}

export interface IngredienteConPrecio {
  nombre: string
  /** Lo que pide la receta, ya escalado a las raciones que se piden. */
  cantidad: number
  /** La unidad en que esta `cantidad`: `g`, `ml` o `ud`. */
  unidad: string
  precio?: PrecioDeIngrediente | null
}

export interface CosteDeIngrediente {
  nombre: string
  cantidad: number
  unidad: string
  /** **Lo que cuesta la cantidad usada.** `null` si no se puede saber. */
  costeUsadoCent: number | null
  /** **Lo que cuesta comprar el envase.** `null` si no se sabe el precio. */
  costeEnvaseCent: number | null
  /** *** Cuantos envases hay que comprar para tener la cantidad pedida. ***
   * *Uno, casi siempre; **dos o mas cuando la receta pide mas de lo que trae un envase**.*
   * `null` si no se sabe cuanto trae el envase.
   */
  envasesQueHacenFalta: number | null
  /** Por que falta lo que falta, para poder decirlo en pantalla. */
  motivo: string | null
}

export interface CosteDeReceta {
  ingredientes: CosteDeIngrediente[]
  /** Suma de lo usado **solo** de los que se sabe. `null` si no se sabe de ninguno. */
  usadoCent: number | null
  /** Suma de los envases **solo** de los que se sabe. `null` si no se sabe de ninguno. */
  envaseCent: number | null
  /** *** Lo que sale del bolsillo: cada envase por los que hacen falta. ***
   * *No es `envaseCent`, que suma **un** envase por ingrediente.* */
  envasesCent: number | null
  /** Cuantos ingredientes entraron en las sumas. */
  conDatos: number
  /** **Cuantos se quedaron fuera, y sus nombres.** *Un total sobre la mitad no es el total.* */
  sinDatos: string[]
  /** `false` en cuanto falte uno: el total existe, pero no esta completo. */
  completo: boolean
}

const UNIDADES_QUE_NO_SE_PRORRATEAN = new Set(['ud', 'uds', 'unidad', 'unidades'])

function esProrrateable(unidad: string): boolean {
  return !UNIDADES_QUE_NO_SE_PRORRATEAN.has(unidad.trim().toLowerCase())
}

/** El €/unidad, del catalogo o deducido del envase. **Sin dato no se inventa.** */
function precioUnidad(p: PrecioDeIngrediente): number | null {
  const directo = p.precioUnidadCent
  if (directo !== undefined && directo !== null && Number.isFinite(directo) && directo > 0) return directo
  const { precioEnvaseCent, cantidadEnvase } = p
  if (precioEnvaseCent === undefined || precioEnvaseCent === null) return null
  if (cantidadEnvase === undefined || cantidadEnvase === null || !(cantidadEnvase > 0)) return null
  return precioEnvaseCent / cantidadEnvase
}

function costeDeUno(i: IngredienteConPrecio): CosteDeIngrediente {
  const p = i.precio ?? null
  const base = { nombre: i.nombre, cantidad: i.cantidad, unidad: i.unidad }
  // *** SIN CANTIDAD NO HAY COSTE, Y NO ES CERO. ***
  // *`cantidad: 0` daba `costeUsadoCent: 0` y `completo: true`: un ingrediente del que no se sabe
  // cuanto lleva se contaba como que no cuesta nada, y el total se declaraba **completo**.
  // Es la regla de siempre -- «null no es 0» -- en el coste de una receta.*
  // *Va lo PRIMERO, antes de mirar el precio: sin cantidad no hay nada que multiplicar.*
  if (!(base.cantidad > 0)) {
    return { ...base, costeUsadoCent: null, costeEnvaseCent: null, envasesQueHacenFalta: null,
             motivo: 'la receta no dice cuanta cantidad' }
  }
  if (!p) {
    return { ...base, costeUsadoCent: null, costeEnvaseCent: null, envasesQueHacenFalta: null,
      motivo: 'sin precio en el catálogo' }
  }
  const envase = p.precioEnvaseCent ?? null

  // **En unidades no se prorratea**: un huevo no tiene fraccion. *Lo que usas cuesta el envase.*
  if (!esProrrateable(i.unidad)) {
    if (envase === null) {
      return { ...base, costeUsadoCent: null, costeEnvaseCent: null, envasesQueHacenFalta: null,
                     motivo: 'sin precio en el catálogo' }
    }
    // *En unidades no se prorratea, pero **el envase es uno**: o lo compras o no.*
    return { ...base, costeUsadoCent: envase, costeEnvaseCent: envase, envasesQueHacenFalta: 1,
             motivo: null }
  }

  const unitario = precioUnidad(p)
  if (unitario === null) {
    // Se sabe el envase pero no cuanto trae: **lo usado no se puede deducir**, y no se inventa.
    return {
      ...base,
      costeUsadoCent: null,
      costeEnvaseCent: envase,
      envasesQueHacenFalta: null,
      motivo: envase === null
        ? 'sin precio en el catálogo'
        : 'se sabe el precio del envase, pero no cuánto trae',
    }
  }
  // El redondeo, al centimo: *un coste con tres decimales no es un precio de nada.*
  return {
    ...base,
    costeUsadoCent: Math.round(unitario * i.cantidad),
    costeEnvaseCent: envase,
    // *** Cuantos envases hacen falta de verdad. ***
    // *Un envase de 131 g no cubre 200 g: hacen falta **dos**, y lo que sale del bolsillo es el doble.*
    envasesQueHacenFalta:
      p.cantidadEnvase !== undefined && p.cantidadEnvase !== null && p.cantidadEnvase > 0
        ? Math.max(1, Math.ceil(i.cantidad / p.cantidadEnvase))
        : null,
    motivo: null,
  }
}

/** El coste de una receta, **con sus dos numeros y su cobertura**. */
export function costeDeReceta(ingredientes: IngredienteConPrecio[]): CosteDeReceta {
  const filas = ingredientes.map(costeDeUno)
  const usados = filas.map((f) => f.costeUsadoCent).filter((v): v is number => v !== null)
  const envases = filas.map((f) => f.costeEnvaseCent).filter((v): v is number => v !== null)
  const sinDatos = filas
    .filter((f) => f.costeUsadoCent === null && f.costeEnvaseCent === null)
    .map((f) => f.nombre)
  return {
    ingredientes: filas,
    usadoCent: usados.length ? usados.reduce((s, v) => s + v, 0) : null,
    envaseCent: envases.length ? envases.reduce((s, v) => s + v, 0) : null,
    envasesCent: filas.some((f) => f.costeEnvaseCent !== null)
      ? filas.reduce((s, f) => s + (f.costeEnvaseCent ?? 0) * (f.envasesQueHacenFalta ?? 1), 0)
      : null,
    conDatos: filas.length - sinDatos.length,
    sinDatos,
    completo: sinDatos.length === 0,
  }
}
