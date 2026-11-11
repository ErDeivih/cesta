/** *** ENVASES ENTEROS: LO QUE HAY QUE COMPRAR PARA UNA CANTIDAD PEDIDA. *** *
 *
 *  *Un pack de 6 × 125 g no se vende por kilos: si necesitas 1 kg, hacen falta **dos packs**
 *  (1,5 kg) y sobran 0,5 kg.* *La cuenta no es `1 / 0.75` y ya: los envases se compran **enteros**,
 *  y el dinero que sale es el de esos envases.*
 *
 *  **Las magnitudes no se mezclan.** *Masa con masa y volumen con volumen; gramos con litros no se
 *  convierte sin densidad, y aquí no se inventa.* *Y si falta el tamaño del envase o la cantidad
 *  pedida, no hay cuenta: devolver `null` es mejor que un cero que parece «gratis».*
 */

const BASE: Record<string, { familia: "masa" | "volumen" | "unidades"; factor: number }> = {
  g: { familia: "masa", factor: 1 },
  gr: { familia: "masa", factor: 1 },
  gramo: { familia: "masa", factor: 1 },
  gramos: { familia: "masa", factor: 1 },
  kg: { familia: "masa", factor: 1000 },
  kilo: { familia: "masa", factor: 1000 },
  kilos: { familia: "masa", factor: 1000 },
  mg: { familia: "masa", factor: 0.001 },
  ml: { familia: "volumen", factor: 1 },
  cc: { familia: "volumen", factor: 1 },
  cl: { familia: "volumen", factor: 10 },
  l: { familia: "volumen", factor: 1000 },
  litro: { familia: "volumen", factor: 1000 },
  litros: { familia: "volumen", factor: 1000 },
  ud: { familia: "unidades", factor: 1 },
  uds: { familia: "unidades", factor: 1 },
  unidad: { familia: "unidades", factor: 1 },
  unidades: { familia: "unidades", factor: 1 },
}

export interface CantidadEnBase {
  cantidad: number
  familia: "masa" | "volumen" | "unidades"
}

export interface CalculoDeEnvases {
  /** Cuántos envases hay que comprar, enteros. */
  envases: number
  /** Lo que se paga por esos envases, en céntimos. */
  coste_cent: number
  /** Lo que sobra, en la unidad del envase (nunca negativo). */
  sobra: number
  /** La unidad de `sobra`. */
  unidad: string
}

/** Una cantidad con su unidad, en la base de su magnitud (gramos, mililitros o unidades). */
export function aBase(cantidad: number, unidad: string): CantidadEnBase | null {
  if (!Number.isFinite(cantidad) || cantidad <= 0) return null
  const ficha = BASE[unidad.trim().toLowerCase()]
  if (!ficha) return null
  return { cantidad: cantidad * ficha.factor, familia: ficha.familia }
}

/**
 * Cuántos envases hacen falta para cubrir `demanda` y cuánto cuestan.
 *
 * `tamanoEnvase` es lo que trae **un** envase, en `unidadEnvase`; `precioCent` es lo que cuesta
 * ese envase. Devuelve `null` si no se puede calcular con lo que hay: no se inventa una compra
 * fraccionaria ni se mezclan masa y volumen.
 */
export function envasesPara(
  demanda: number,
  unidadDemanda: string,
  tamanoEnvase: number,
  unidadEnvase: string,
  precioCent: number,
): CalculoDeEnvases | null {
  const pedido = aBase(demanda, unidadDemanda)
  const envase = aBase(tamanoEnvase, unidadEnvase)
  if (!pedido || !envase) return null
  if (pedido.familia !== envase.familia) return null
  if (!Number.isFinite(precioCent) || precioCent < 0) return null

  const envases = Math.ceil(Number((pedido.cantidad / envase.cantidad).toFixed(9)))
  const sobraBase = Number((envases * envase.cantidad - pedido.cantidad).toFixed(9))
  // *Se devuelve en la unidad del envase, que es la que la persona reconoce.*
  const factor = BASE[unidadEnvase.trim().toLowerCase()]?.factor ?? 1
  return {
    envases,
    coste_cent: Math.round(envases * precioCent),
    sobra: Number((sobraBase / factor).toFixed(6)),
    unidad: unidadEnvase.trim().toLowerCase(),
  }
}
