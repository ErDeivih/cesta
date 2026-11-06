/** *** LAS CIFRAS DE SALUD, CON SU FUENTE Y SU FECHA, Y UNA ESTIMACIÓN DECLARADA. *** *
 *
 *  *Aquí viven dos cosas que no se mezclan:*
 *
 *  - **Las referencias** (`PAUTAS_SALUD`, `RANGOS_MACROS`, `ACTIVIDAD`): qué dicen las
 *    organizaciones, con su enlace y la fecha del documento. No son un consejo para nadie en
 *    concreto.
 *  - **La estimación** (`calcularEstimacion`): la cuenta que sale de los datos que escribe la
 *    persona. Se enseña como rango porque tiene error, y **no se aplica sola**: el objetivo se
 *    calcula cuando alguien elige qué quiere hacer.
 *
 *  **La aritmética vive aquí y no en la pantalla**, por dos motivos: se puede probar sin montar
 *  React, y el JSX no tiene ni una fórmula. La pantalla enseña la cifra, su rango y de dónde
 *  sale; nunca la cuenta.
 *
 *  Lo que **no** se hace aquí: juzgar con el IMC, proponer dietas, fijar un objetivo al abrir la
 *  aplicación ni dar una cifra única sin margen.
 */

// ------------------------------------------------------------------ tipos ---

export type Sexo = 'mujer' | 'hombre'
export type Actividad = 'poco' | 'ligero' | 'moderado' | 'alto' | 'mucho'
export type Objetivo = 'mantener' | 'perder' | 'ganar'
export type ClaveMacro = 'proteina' | 'grasas' | 'hidratos'
export type ClavePauta = 'fibra' | 'azucar' | 'sal' | 'agua' | 'frutaVerdura' | 'alcohol'
export type ClaveFuente = 'mifflin' | 'fao' | 'cdc' | 'efsa' | 'who' | 'sodio' | 'alcohol' | 'aesan'

/** Una referencia: lo que se lee, el documento que hay detrás y **su fecha**.
 *
 *  `documento` no se pinta: va en el `title` del enlace para quien quiera saber qué abre. La
 *  pantalla enseña `nombre` y `fecha`, que es lo que cabe en un móvil.
 */
export interface Fuente {
  /** La organización, tal y como se lee: «WHO», «EFSA», «CDC», «AESAN». */
  nombre: string
  /** El documento concreto, para el `title` del enlace. */
  documento: string
  url: string
  /** La fecha del documento, ya en formato de aquí: `26/03/2010`. */
  fecha: string
}

/** **Las ocho fuentes, verificadas el 2026-11-06.** El enlace es el que se abre. */
export const FUENTES: Record<ClaveFuente, Fuente> = {
  mifflin: {
    // El nombre visible **no lleva el apellido del estudio**: en pantalla sería jerga. Quien
    // quiera el detalle abre el enlace, donde está la cita entera.
    nombre: 'Gasto en reposo',
    documento: 'Mifflin-St Jeor (1990): ecuación del gasto energético en reposo',
    url: 'https://europepmc.org/article/MED/2305711',
    fecha: '1990',
  },
  fao: {
    nombre: 'FAO/WHO/UNU',
    documento: 'Necesidades de energía humanas (2004): niveles de actividad',
    url: 'https://www.fao.org/4/y5686e/y5686e00.htm',
    fecha: '2004',
  },
  cdc: {
    nombre: 'CDC',
    documento: 'Perder peso: ritmo gradual (17/01/2025)',
    url: 'https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html',
    fecha: '17/01/2025',
  },
  efsa: {
    nombre: 'EFSA',
    documento: 'Valores dietéticos de referencia (26/03/2010)',
    url: 'https://www.efsa.europa.eu/en/press/news/nda100326',
    fecha: '26/03/2010',
  },
  who: {
    nombre: 'WHO',
    documento: 'Alimentación saludable (26/01/2026)',
    url: 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet',
    fecha: '26/01/2026',
  },
  sodio: {
    nombre: 'WHO',
    documento: 'Reducir el sodio (11/05/2026)',
    url: 'https://www.who.int/news-room/fact-sheets/detail/sodium-reduction',
    fecha: '11/05/2026',
  },
  alcohol: {
    nombre: 'WHO',
    documento: 'Alcohol (28/06/2024)',
    url: 'https://www.who.int/news-room/fact-sheets/detail/alcohol',
    fecha: '28/06/2024',
  },
  aesan: {
    nombre: 'AESAN',
    documento: 'Recomendaciones dietéticas y de actividad física (2022)',
    url: 'https://www.aesan.gob.es/nutricion/recomendaciones-dieteticas',
    fecha: '2022',
  },
}

// --------------------------------------------------------------- las pautas ---

/** Una pauta de referencia: **una cifra, su detalle si hace falta y sus fuentes**.
 *
 *  Sin párrafos: lo que se lee es la cifra y de dónde sale. El detalle solo existe cuando la
 *  cifra se malinterpretaría sin él (el agua, por ejemplo, es agua total, no solo la bebida).
 */
export interface Pauta {
  clave: ClavePauta
  titulo: string
  cifra: string
  detalle?: string
  fuentes: Fuente[]
}

/** **Las pautas de cada día, con su cifra y su fuente.** El orden es el de la ficha de la OMS. */
export const PAUTAS_SALUD: Pauta[] = [
  {
    clave: 'fibra',
    titulo: 'Fibra',
    cifra: '25 g al día o más',
    fuentes: [FUENTES.efsa, FUENTES.who],
  },
  {
    clave: 'azucar',
    titulo: 'Azúcar libre',
    cifra: 'Menos del 10 % de la energía; mejor, menos del 5 %',
    fuentes: [FUENTES.who],
  },
  {
    clave: 'sal',
    titulo: 'Sal',
    cifra: 'Menos de 5 g al día (2.000 mg de sodio)',
    fuentes: [FUENTES.sodio],
  },
  {
    clave: 'agua',
    titulo: 'Agua',
    cifra: '2,0 L al día en mujeres y 2,5 L en hombres',
    detalle: 'Agua total, contando también la que traen los alimentos.',
    fuentes: [FUENTES.efsa],
  },
  {
    clave: 'frutaVerdura',
    titulo: 'Fruta y verdura',
    cifra: '400 g al día o más, a partir de los 10 años',
    fuentes: [FUENTES.who],
  },
  {
    clave: 'alcohol',
    titulo: 'Alcohol',
    cifra: 'Ningún nivel de consumo es sin riesgo',
    fuentes: [FUENTES.alcohol],
  },
]

// --------------------------------------------------------------- los macros ---

/** Un macro con su rango **en % de la energía** y su fuente. */
export interface RangoMacro {
  clave: ClaveMacro
  nombre: string
  pctMin: number
  pctMax: number
  fuente: Fuente
}

/** **El reparto de referencia**, en % de la energía diaria.
 *
 *  *Proteína y grasas salen de la ficha de la OMS, y los hidratos del valor de referencia de la
 *  EFSA, que es más estrecho (45–60 %) que el de la OMS (45–75 %). Se elige el estrecho para no
 *  mezclar dos referencias en la misma fila y porque es el que se cita en España.*
 *
 *  *La EFSA da para las grasas 20–35 %. La OMS da 15–30 %, y ese es el que se usa: la misma
 *  ficha que la proteína, para que las dos filas se puedan explicar juntas.*
 */
export const RANGOS_MACROS: RangoMacro[] = [
  { clave: 'proteina', nombre: 'Proteína', pctMin: 10, pctMax: 15, fuente: FUENTES.who },
  { clave: 'grasas', nombre: 'Grasas', pctMin: 15, pctMax: 30, fuente: FUENTES.who },
  { clave: 'hidratos', nombre: 'Hidratos', pctMin: 45, pctMax: 60, fuente: FUENTES.efsa },
]

/** La energía que da un gramo de cada macro. *Es la cuenta, no se pinta.* */
export const KCAL_POR_GRAMO: Record<ClaveMacro, number> = {
  proteina: 4,
  grasas: 9,
  hidratos: 4,
}

/** Un macro ya calculado para una cifra de kcal: gramos centrales y su horquilla. */
export interface MacroCalculado extends RangoMacro {
  gramos: number
  gramosMin: number
  gramosMax: number
}

/** Los gramos de un macro a un porcentaje dado. *Redondeado al gramo: la décima finge precisión.* */
function gramosDe(kcal: number, pct: number, porGramo: number): number {
  return Math.round((kcal * pct) / 100 / porGramo)
}

/** **El reparto en gramos para una cifra de kcal.**
 *
 *  El centro de cada macro es el **punto medio de su rango**, y se devuelven también los extremos
 *  para que la pantalla pueda enseñar la horquilla. Los tres rangos son referencias
 *  independientes: **no se fuerzan a sumar 100 %**, porque las fuentes no los dan juntos.
 */
export function macrosDelObjetivo(kcal: number): MacroCalculado[] {
  if (!Number.isFinite(kcal) || kcal <= 0) return []
  return RANGOS_MACROS.map((rango) => {
    const porGramo = KCAL_POR_GRAMO[rango.clave]
    return {
      ...rango,
      gramos: gramosDe(kcal, (rango.pctMin + rango.pctMax) / 2, porGramo),
      gramosMin: gramosDe(kcal, rango.pctMin, porGramo),
      gramosMax: gramosDe(kcal, rango.pctMax, porGramo),
    }
  })
}

/** **Los gramos que se guardan con el objetivo**, sin rangos: la cifra de cada macro. */
export function gramosDeMacros(kcal: number): Record<ClaveMacro, number> {
  const salida: Record<ClaveMacro, number> = { proteina: 0, grasas: 0, hidratos: 0 }
  for (const macro of macrosDelObjetivo(kcal)) salida[macro.clave] = macro.gramos
  return salida
}

// ---------------------------------------------------------- la actividad ---

/** Un nivel de actividad: **el factor, cómo se llama y de dónde sale**.
 *
 *  El factor multiplica el gasto en reposo. Los niveles son los de la referencia FAO/WHO/UNU;
 *  el número no se enseña en pantalla — se enseña el nombre del nivel.
 */
export interface NivelActividad {
  factor: number
  nombre: string
  fuente: Fuente
}

export const ACTIVIDAD: Record<Actividad, NivelActividad> = {
  poco: { factor: 1.2, nombre: 'Poco movimiento', fuente: FUENTES.fao },
  ligero: { factor: 1.375, nombre: 'Algo de movimiento', fuente: FUENTES.fao },
  moderado: { factor: 1.55, nombre: 'Movimiento moderado', fuente: FUENTES.fao },
  alto: { factor: 1.725, nombre: 'Mucho movimiento', fuente: FUENTES.fao },
  mucho: { factor: 1.9, nombre: 'Movimiento intenso', fuente: FUENTES.fao },
}

export const ACTIVIDADES: Actividad[] = ['poco', 'ligero', 'moderado', 'alto', 'mucho']

// ----------------------------------------------------------- el objetivo ---

/** Una opción de objetivo: **cuánto se ajusta, cómo se llama y con qué referencia**.
 *
 *  El ajuste se da como horquilla porque es una estimación: 300–500 kcal al día, no una cifra
 *  exacta. La que se aplica es el punto medio (400), y se dice en la pantalla.
 *
 *  *El ancla de «perder» es el ritmo gradual de la CDC (1–2 libras por semana, ≈0,25–0,5 kg): la
 *  horquilla de 300–500 kcal al día es la estimación conservadora que se decidió para esta app,
 *  no una cifra que la ficha de la CDC escriba tal cual. Ganar usa la misma horquilla al espejo,
 *  y mantener no ajusta: equilibrio entre lo que se come y lo que se gasta (WHO).*
 */
export interface AjusteObjetivo {
  nombre: string
  /** Cómo se dice en la frase del «por qué»: «para mantener», «para perder». */
  frase: string
  min: number
  max: number
  fuente: Fuente
}

export const AJUSTES: Record<Objetivo, AjusteObjetivo> = {
  mantener: { nombre: 'Mantener', frase: 'para mantener', min: 0, max: 0, fuente: FUENTES.who },
  perder: { nombre: 'Perder', frase: 'para perder', min: -500, max: -300, fuente: FUENTES.cdc },
  ganar: { nombre: 'Ganar', frase: 'para ganar', min: 300, max: 500, fuente: FUENTES.who },
}

export const OBJETIVOS: Objetivo[] = ['mantener', 'perder', 'ganar']

/** El ajuste que se aplica: **el punto medio de la horquilla**. Mantener es 0. */
export function ajusteAplicado(objetivo: Objetivo): number {
  const { min, max } = AJUSTES[objetivo]
  return min === max ? min : Math.round((min + max) / 2)
}

// ---------------------------------------------------------------- límites ---

/** **Hasta dónde tiene sentido la estimación.** Fuera de aquí no se calcula: es preferible no
 *  enseñar una cifra que enseñar una que no significa nada. */
export const LIMITES = {
  edad: { min: 14, max: 100 },
  peso: { min: 30, max: 250 },
  altura: { min: 120, max: 230 },
}

/** **El suelo por debajo del cual la app no da un objetivo para perder.**
 *
 *  *No es una recomendación ni una pauta de salud: es un límite de seguridad de la app para no
 *  enseñar como «objetivo» una cifra que puede ser peligrosa.* *La estimación sigue existiendo
 *  (se puede ver el gasto), pero el objetivo de pérdida no se calcula ni se guarda por debajo.*
 */
export const SUELO_OBJETIVO: Record<Sexo, number> = { mujer: 1200, hombre: 1500 }

/** Los cinco datos que necesita la estimación. */
export interface DatosParaEstimar {
  sexo: Sexo
  edad: number
  peso: number
  altura: number
  actividad: Actividad
}

/** ¿Los datos están dentro de lo razonable? *Se comprueba antes de dividir nada.* */
export function datosDentroDeRango({ edad, peso, altura }: DatosParaEstimar): boolean {
  return (
    Number.isFinite(edad) && edad >= LIMITES.edad.min && edad <= LIMITES.edad.max &&
    Number.isFinite(peso) && peso >= LIMITES.peso.min && peso <= LIMITES.peso.max &&
    Number.isFinite(altura) && altura >= LIMITES.altura.min && altura <= LIMITES.altura.max
  )
}

// ------------------------------------------------------------ la estimación ---

/** **El gasto diario estimado**, o `null` si los datos no dan una cifra con sentido.
 *
 *  *Gasto en reposo (Mifflin-St Jeor, 1990) multiplicado por el nivel de actividad. La cuenta se
 *  hace aquí y se calla: la pantalla enseña el resultado y su margen, no la fórmula.*
 */
export function gastoEstimado({ sexo, edad, peso, altura, actividad }: DatosParaEstimar): number | null {
  if (![edad, peso, altura].every((n) => Number.isFinite(n) && n > 0)) return null
  const nivel = ACTIVIDAD[actividad]
  if (!nivel) return null
  const reposo = 10 * peso + 6.25 * altura - 5 * edad + (sexo === 'hombre' ? 5 : -161)
  const total = reposo * nivel.factor
  return Number.isFinite(total) && total > 0 ? total : null
}

/** **El rango que se enseña**, redondeado a decenas para no fingir precisión.
 *
 *  Se abre un 10 % a cada lado: la estimación tiene error y decirlo es parte del dato.
 */
export function rangoEstimado(centro: number): { bajo: number; alto: number; centro: number } {
  const decena = (n: number) => Math.round(n / 10) * 10
  return { bajo: decena(centro * 0.9), alto: decena(centro * 1.1), centro: decena(centro) }
}

/** El gasto estimado con su horquilla, sin haber elegido objetivo todavía. */
export interface GastoEstimado {
  gasto: number
  centro: number
  bajo: number
  alto: number
}

/** **El gasto con su rango**, o `null` si falta un dato o no está en lo razonable. */
export function gastoConRango(datos: DatosParaEstimar): GastoEstimado | null {
  if (!datosDentroDeRango(datos)) return null
  const gasto = gastoEstimado(datos)
  if (gasto === null) return null
  const rango = rangoEstimado(gasto)
  return { gasto, centro: rango.centro, bajo: rango.bajo, alto: rango.alto }
}

/** La estimación completa: **el objetivo elegido, con su ajuste, su rango y sus macros**. */
export interface Estimacion {
  /** El gasto estimado sin ajustar, que es lo que explica el «por qué». */
  gasto: number
  objetivo: Objetivo
  /** Lo que se suma al gasto: 0 al mantener, −400 al perder, +400 al ganar. */
  ajuste: number
  centro: number
  bajo: number
  alto: number
  macros: MacroCalculado[]
  /** *El objetivo de pérdida salió por debajo del suelo de seguridad: no se enseña ni se guarda.* */
  bajoSuelo: boolean
}

/** **El objetivo, calculado a partir de los datos y de lo que la persona ha elegido.**
 *
 *  Sin objetivo elegido no hay estimación: la función no adivina. Y fuera de los límites
 *  tampoco: devuelve `null` antes que una cifra que no significa nada.
 */
export function calcularEstimacion(
  datos: DatosParaEstimar | null,
  objetivo: Objetivo,
): Estimacion | null {
  if (datos === null) return null
  const base = gastoConRango(datos)
  if (base === null) return null
  const ajuste = ajusteAplicado(objetivo)
  const rango = rangoEstimado(base.gasto + ajuste)
  const bajoSuelo = objetivo === 'perder' && rango.centro < SUELO_OBJETIVO[datos.sexo]
  return {
    gasto: base.gasto,
    objetivo,
    ajuste,
    centro: rango.centro,
    bajo: rango.bajo,
    alto: rango.alto,
    macros: macrosDelObjetivo(rango.centro),
    bajoSuelo,
  }
}

// ----------------------------------------------------------------- textos ---

/** **El límite, escrito una vez y corto.** No es letra pequeña: va en la pantalla. */
export const AVISO_MEDICO =
  'No es consejo médico. Si tienes una condición de salud, consulta con un profesional.'

/** Lo que se dice del rango para que no se lea como una medición. */
export const TEXTO_ESTIMACION = 'Es una estimación, no una medida exacta.'

/** El texto del «por qué», **sin fórmulas**, con la cifra que se acaba de calcular.
 *
 *  Se compone aquí para que la pantalla no invente frases y para poder probarlo: *«partimos de tu
 *  gasto estimado y ajustamos…»*.
 */
export function porQueDelObjetivo(estimacion: Estimacion, cifra: (n: number) => string): string {
  const gasto = `${cifra(estimacion.gasto)} kcal al día`
  if (estimacion.ajuste === 0) {
    return `Partimos de tu gasto estimado (${gasto}). Para mantener, no ajustamos la cifra.`
  }
  const signo = estimacion.ajuste > 0 ? '+' : '−'
  const ajuste = `${signo}${cifra(Math.abs(estimacion.ajuste))}`
  return `Partimos de tu gasto estimado (${gasto}) y, ${AJUSTES[estimacion.objetivo].frase}, ajustamos ${ajuste} kcal al día.`
}
