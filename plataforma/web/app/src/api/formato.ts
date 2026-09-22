/** Convertir los datos de la API en texto, con las reglas del proyecto.
 *
 *  La regla que manda aqui: **un dato que no tenemos es "no lo se"**, nunca un
 *  cero. Un 0,00 EUR se lee como "gratis" y una letra vacia como "malo"; las dos
 *  cosas serian mentira. Por eso casi todas estas funciones devuelven una frase
 *  cuando el dato es null, y ninguna tiene un valor por defecto numerico.
 *
 *  El dinero llega en centimos enteros y se pasa a euros solo al pintar. No se
 *  redondea antes de tiempo: 0,1 + 0,2 no da 0,3.
 */
import type { Nutricion } from '../tipos'

const EUROS = new Intl.NumberFormat('es-ES', {
  style: 'currency',
  currency: 'EUR',
})

const NUMERO = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 })

export const NO_LO_SE = 'no lo sé'

/** Centimos a "3,45 €". `null` es "no lo sé", no "0,00 €". */
export function euros(cent: number | null | undefined): string {
  if (cent === null || cent === undefined || !Number.isFinite(cent)) return NO_LO_SE
  return EUROS.format(cent / 100)
}

/** El sufijo de la unidad canonica: €/kg, €/l, €/ud. */
export function sufijoUnidad(unidad: string | null | undefined): string {
  if (!unidad) return ''
  const u = unidad.trim().toLowerCase()
  if (u === 'kg' || u === 'l' || u === 'ud' || u === 'm' || u === 'g' || u === 'ml') {
    return `/${u}`
  }
  return u ? `/${u}` : ''
}

/** Precio por unidad. Sin dato, "no lo sé", que es distinto de "barato". */
export function eurosUnidad(
  cent: number | null | undefined,
  unidad: string | null | undefined,
): string {
  if (cent === null || cent === undefined || !Number.isFinite(cent)) return NO_LO_SE
  // Los precios por unidad llevan dos decimales: 0,09 €/ud y 0,10 €/ud son
  // distintos, y son la diferencia entre dos marcas de papel de cocina.
  return `${EUROS.format(cent / 100)}${sufijoUnidad(unidad)}`
}

export function numero(n: number | null | undefined, decimales = 1): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return NO_LO_SE
  return new Intl.NumberFormat('es-ES', {
    maximumFractionDigits: decimales,
    minimumFractionDigits: 0,
  }).format(n)
}

export function porcentaje(p: number | null | undefined, decimales = 1): string {
  if (p === null || p === undefined || !Number.isFinite(p)) return NO_LO_SE
  return `${numero(p, decimales)} %`
}

/** Con signo, para las variaciones. Una bajada se lee de un vistazo. */
export function porcentajeConSigno(p: number | null | undefined, decimales = 1): string {
  if (p === null || p === undefined || !Number.isFinite(p)) return NO_LO_SE
  const signo = p > 0 ? '+' : p < 0 ? '−' : ''
  return `${signo}${numero(Math.abs(p), decimales)} %`
}

const FECHA_CORTA = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

const FECHA_DIA = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' })

/** "2026-09-17" o "2026-09-17T10:04:00Z" a "17 sept 2026". */
export function fecha(iso: string | null | undefined, corta = false): string {
  if (!iso) return NO_LO_SE
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso)
  if (Number.isNaN(d.getTime())) return NO_LO_SE
  return (corta ? FECHA_DIA : FECHA_CORTA).format(d)
}

/** Dias enteros entre una fecha de datos y hoy. Negativo si es futuro. */
export function diasDesde(iso: string | null | undefined, hoy = new Date()): number | null {
  if (!iso) return null
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso)
  if (Number.isNaN(d.getTime())) return null
  const unDia = 24 * 60 * 60 * 1000
  const a = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
  const b = Date.UTC(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  return Math.round((b - a) / unDia)
}

/** "hoy", "ayer", "hace 5 días". */
export function hace(iso: string | null | undefined): string {
  const d = diasDesde(iso)
  if (d === null) return NO_LO_SE
  if (d === 0) return 'hoy'
  if (d === 1) return 'ayer'
  if (d < 0) return `dentro de ${-d} días`
  return `hace ${d} días`
}

/** Milisegundos de una fecha ISO, para las graficas. */
export function ms(iso: string): number {
  return new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso).getTime()
}

/** El nombre de la cadena, con la primera letra en mayuscula: vienen en
 *  minusculas (`alcampo`) y en medio de una frase quedan raras. */
export function nombreCadena(cadena: string | null | undefined): string {
  if (!cadena) return NO_LO_SE
  return cadena.charAt(0).toUpperCase() + cadena.slice(1)
}

/** "1 kg", "500 g". `cantidad` puede venir null aunque haya unidad. */
export function cantidad(
  cantidad: number | null | undefined,
  unidad: string | null | undefined,
): string {
  if (cantidad === null || cantidad === undefined) return unidad ?? NO_LO_SE
  return `${numero(cantidad, 3)} ${unidad ?? ''}`.trim()
}

export const SELLOS_LEGIBLES: Record<string, string> = {
  'sin-gluten': 'sin gluten',
  'sin-lactosa': 'sin lactosa',
  vegano: 'vegano',
  vegetariano: 'vegetariano',
  ecologico: 'ecológico',
  'sin-azucar': 'sin azúcar',
  'sin-sal': 'sin sal',
  'sin-aceite-palma': 'sin aceite de palma',
  // Los certificados. No son "sellos" del mismo tipo que los de arriba: estos
  // los audita un tercero, y son la prueba fuerte de lo que dice el envase. Los
  // nueve de abajo salen hoy en los datos (comprobado sobre el catalogo: 21
  // codigos distintos) y sin traducir se leian como `origen espana`, sin la ene.
  'origen-espana': 'Origen España',
  'rainforest-alliance': 'Rainforest Alliance',
  'comercio-justo': 'Comercio justo',
  msc: 'MSC (pesca sostenible)',
  asc: 'ASC (acuicultura sostenible)',
  'bienestar-animal': 'Bienestar animal',
  dop: 'DOP (denominación de origen)',
  igp: 'IGP (indicación geográfica)',
  etg: 'ETG (especialidad tradicional)',
}

export function selloLegible(s: string): string {
  return SELLOS_LEGIBLES[s] ?? s.replace(/-/g, ' ')
}

/** De donde sale un sello. Un certificado auditado no vale lo mismo que una
 *  palabra en el nombre del producto, y decir lo contrario seria lo peor que
 *  puede hacer esta app. */
export const ORIGEN_SELLO: Record<string, string> = {
  certificado: 'certificado',
  etiqueta: 'leído en la etiqueta',
  nombre: 'solo está en el nombre',
  mixto: 'certificado y etiqueta',
}

export function textoOrigenSello(origen: string | null | undefined): string | null {
  if (!origen) return null
  return ORIGEN_SELLO[origen] ?? origen
}

/** La tabla de la etiqueta, con el nombre que pone el envase.
 *
 *  Las claves llegan de la cadena tal cual (`energia_kj`, `saturadas`) y en
 *  crudo no dicen nada: `saturadas` sin el "de las cuales" delante se lee como
 *  si fueran todas las grasas del producto, y un numero sin unidad no se puede
 *  comparar con el de la fila de al lado.
 *
 *  El orden es el del envase, no el del objeto de la API: primero la energia y
 *  detras los grupos que la componen. Y una clave que aqui no este **sale
 *  igualmente**, detras y en crudo: en esta casa un dato que no sabemos leer es
 *  mejor que un dato que no ensenamos. */
const NUTRIENTES: [string, string, string][] = [
  // `energia_kcal` no aparece en los datos de hoy (la cadena publica el kJ),
  // pero se busca lo mismo, por si un dia llega.
  ['energia_kj', 'Energía', 'kJ'],
  ['energia_kcal', 'Energía', 'kcal'],
  ['grasas', 'Grasas', 'g'],
  ['saturadas', 'de las cuales saturadas', 'g'],
  ['hidratos', 'Hidratos', 'g'],
  ['azucares', 'de los cuales azúcares', 'g'],
  ['fibra', 'Fibra', 'g'],
  ['proteinas', 'Proteínas', 'g'],
  ['sal', 'Sal', 'g'],
]

export interface FilaNutricion {
  clave: string
  texto: string
  /** Vacio en las claves que no conocemos: inventarla seria peor que no ponerla. */
  unidad: string
  valor: number | null
}

export function filasNutricion(nutricion: Nutricion): FilaNutricion[] {
  const puestas = new Set<string>()
  const filas: FilaNutricion[] = []
  for (const [clave, texto, unidad] of NUTRIENTES) {
    if (!(clave in nutricion)) continue
    puestas.add(clave)
    filas.push({ clave, texto, unidad, valor: nutricion[clave] ?? null })
  }
  for (const clave of Object.keys(nutricion).sort()) {
    if (puestas.has(clave)) continue
    filas.push({ clave, texto: clave, unidad: '', valor: nutricion[clave] ?? null })
  }
  return filas
}
