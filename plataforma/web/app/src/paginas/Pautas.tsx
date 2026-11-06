/** Pautas de salud: referencias generales y una estimacion declarada.
 *
 *  **Dos capas separadas.** Arriba, pautas generales con su fuente. Abajo, una estimacion
 *  opcional que solo aparece si la persona rellena sus datos. La app **no propone un objetivo**:
 *  el boton lo guarda solo si se pulsa, y la clave es la misma que lee Calorias (`objetivo:<fecha>`).
 *
 *  **Sin formulas en pantalla.** La cuenta se hace y se calla; lo que se lee es un rango, su
 *  margen y la advertencia de que no es consejo medico. El formulario empieza vacio: sin datos
 *  no hay cifra, y no se rellena con valores de ejemplo.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { guardaPreferencia } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { Boton } from '../componentes/ui'

export type Sexo = 'mujer' | 'hombre'
export type Actividad = 'poco' | 'ligero' | 'moderado' | 'alto' | 'mucho'

/** El factor de actividad de cada opcion. **No se enseña**: solo entra en la estimacion. */
const FACTOR: Record<Actividad, number> = {
  poco: 1.2,
  ligero: 1.375,
  moderado: 1.55,
  alto: 1.725,
  mucho: 1.9,
}

const NOMBRE_ACTIVIDAD: Record<Actividad, string> = {
  poco: 'Poco movimiento',
  ligero: 'Algo de movimiento',
  moderado: 'Movimiento moderado',
  alto: 'Mucho movimiento',
  mucho: 'Movimiento intenso',
}

/** Las fuentes, con su nombre y su enlace. **Sin resumen**: quien quiera el detalle lo abre. */
const FUENTES = [
  {
    nombre: 'WHO · Alimentación saludable',
    url: 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet',
  },
  {
    nombre: 'EFSA · Valores de referencia de energía (2013)',
    url: 'https://www.efsa.europa.eu/es/press/news/130110',
  },
  {
    nombre: 'EFSA · Opinión científica sobre energía (2013)',
    url: 'https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2013.3005',
  },
  {
    nombre: 'FAO/WHO/UNU · Necesidades de energía (2004)',
    url: 'https://www.fao.org/4/y5686e/y5686e00.htm',
  },
  {
    nombre: 'AESAN · Recomendaciones dietéticas saludables y sostenibles (2022)',
    url: 'https://cpage.mpr.gob.es/publicacion/recomendaciones-dieteticas-saludables-y-sostenibles-complementadas-con-recomendaciones-de-actividad-fisica-para-la-poblacion-espanola-2022-069220082-0001/',
  },
  {
    nombre: 'Mifflin-St Jeor · Gasto en reposo (1990)',
    url: 'https://europepmc.org/article/MED/2305711',
  },
] as const

/** Los datos que necesita la estimacion. */
export interface DatosParaEstimar {
  sexo: Sexo
  edad: number
  peso: number
  altura: number
  actividad: Actividad
}

/** **El gasto diario estimado**, o `null` si los datos no dan una cifra con sentido.
 *
 *  Mifflin-St Jeor para el reposo y el factor de actividad para el dia. **La formula no se
 *  pinta**: la pantalla enseña el resultado y su margen.
 */
export function gastoEstimado({
  sexo,
  edad,
  peso,
  altura,
  actividad,
}: DatosParaEstimar): number | null {
  if (![edad, peso, altura].every((n) => Number.isFinite(n) && n > 0)) return null
  const reposo = 10 * peso + 6.25 * altura - 5 * edad + (sexo === 'hombre' ? 5 : -161)
  const total = reposo * FACTOR[actividad]
  return Number.isFinite(total) && total > 0 ? total : null
}

/** **El rango que se enseña**, redondeado a decenas para no fingir precision.
 *
 *  Se abre un 10 % a cada lado: la estimacion tiene error y decirlo es parte del dato. El centro
 *  es lo que se guarda si la persona decide usarlo como objetivo.
 */
export function rangoEstimado(centro: number): { bajo: number; alto: number; centro: number } {
  const decena = (n: number) => Math.round(n / 10) * 10
  return { bajo: decena(centro * 0.9), alto: decena(centro * 1.1), centro: decena(centro) }
}

function aNumero(texto: string): number | null {
  const limpio = texto.trim().replace(',', '.')
  if (limpio === '') return null
  const valor = Number(limpio)
  return Number.isFinite(valor) ? valor : null
}

function hoy(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

const CIFRA = new Intl.NumberFormat('es-ES', {
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
  useGrouping: true,
})

function cifra(n: number): string {
  return CIFRA.format(n)
}

export function Pautas() {
  const cliente = useQueryClient()
  const [sexo, setSexo] = useState<Sexo | ''>('')
  const [edad, setEdad] = useState('')
  const [peso, setPeso] = useState('')
  const [altura, setAltura] = useState('')
  const [actividad, setActividad] = useState<Actividad | ''>('')
  const [guardando, setGuardando] = useState(false)
  const [guardado, setGuardado] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const edadN = aNumero(edad)
  const pesoN = aNumero(peso)
  const alturaN = aNumero(altura)
  const datos: DatosParaEstimar | null =
    sexo !== '' && actividad !== '' && edadN !== null && pesoN !== null && alturaN !== null
      ? { sexo, edad: edadN, peso: pesoN, altura: alturaN, actividad }
      : null
  const dentroDeRango = datos !== null
    && datos.edad >= 18 && datos.edad <= 120
    && datos.peso >= 25 && datos.peso <= 300
    && datos.altura >= 100 && datos.altura <= 250
  const estimacion = datos !== null && dentroDeRango ? gastoEstimado(datos) : null
  const rango = estimacion === null ? null : rangoEstimado(estimacion)

  async function guardarObjetivo() {
    if (rango === null) return
    setGuardando(true)
    setError(null)
    try {
      await guardaPreferencia(`objetivo:${hoy()}`, { kcal: rango.centro })
      // La misma clave que leen Diario y Tendencias: al volver, el objetivo ya esta.
      await cliente.invalidateQueries({ queryKey: ['yo'] })
      setGuardado(rango.centro)
    } catch (e) {
      setError(textoDeError(e))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex min-h-full flex-col gap-4">
      <header className="flex items-center gap-2">
        <Link
          to="/calorias"
          aria-label="Volver a Calorías"
          className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M19 12H5M11 18l-6-6 6-6" />
          </svg>
        </Link>
        <div className="min-w-0 flex-1">
          <p className="text-micro uppercase text-tinta-tenue">Calorías</p>
          <h2 className="mt-0.5 font-display text-titulo font-semibold text-tinta">
            Pautas de salud
          </h2>
        </div>
      </header>

      {/* **La linea que no es relleno.** Va arriba porque vale para todo lo de abajo, incluidas
          las pautas generales y la estimacion. */}
      <p className="rounded-campo border border-borde bg-marfil px-3 py-2 text-cuerpo text-secundaria">
        No es consejo médico. Son pautas generales para orientarte.
      </p>

      <section aria-labelledby="pautas" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h3 id="pautas" className="text-cuerpo-fuerte text-tinta">En el día a día</h3>
        <ul className="mt-2 flex flex-col gap-2">
          <li className="text-cuerpo text-tinta-suave">
            <strong className="text-tinta">Varía.</strong> Verduras y frutas a diario; cereales
            integrales, legumbres, frutos secos, huevo, pescado y lácteos a menudo.
          </li>
          <li className="text-cuerpo text-tinta-suave">
            <strong className="text-tinta">Equilibra.</strong> Lo que comes y lo que te mueves van
            juntos: busca el equilibrio, no una cifra.
          </li>
          <li className="text-cuerpo text-tinta-suave">
            <strong className="text-tinta">Modera.</strong> Ultraprocesados, bebidas azucaradas,
            sal y alcohol: poca cantidad y de forma ocasional.
          </li>
          <li className="text-cuerpo text-tinta-suave">
            <strong className="text-tinta">Muévete.</strong> Caminar, subir escaleras o jugar ya
            cuenta. Elige algo que puedas mantener.
          </li>
          <li className="text-cuerpo text-tinta-suave">
            <strong className="text-tinta">Bebe agua.</strong> Tenla a mano; los refrescos
            azucarados, para ocasiones.
          </li>
        </ul>
      </section>

      <section aria-labelledby="estimacion" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h3 id="estimacion" className="text-cuerpo-fuerte text-tinta">
          Estimación de gasto diario
        </h3>
        <p className="mt-1 text-etiqueta text-tinta-suave">
          Opcional. Para personas adultas. Rellena los cinco datos para ver el rango.
        </p>

        <form className="mt-3 flex flex-col gap-3" onSubmit={(e) => e.preventDefault()}>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Sexo
              <select
                value={sexo}
                onChange={(e) => {
                  setSexo(e.target.value as Sexo | '')
                  setError(null)
                }}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
              >
                <option value="">Elige</option>
                <option value="mujer">Mujer</option>
                <option value="hombre">Hombre</option>
              </select>
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Edad
              <input
                value={edad}
                onChange={(e) => {
                  setEdad(e.target.value)
                  setError(null)
                }}
                inputMode="numeric"
                autoComplete="off"
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Peso (kg)
              <input
                value={peso}
                onChange={(e) => {
                  setPeso(e.target.value)
                  setError(null)
                }}
                inputMode="decimal"
                autoComplete="off"
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Altura (cm)
              <input
                value={altura}
                onChange={(e) => {
                  setAltura(e.target.value)
                  setError(null)
                }}
                inputMode="decimal"
                autoComplete="off"
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Actividad
              <select
                value={actividad}
                onChange={(e) => {
                  setActividad(e.target.value as Actividad | '')
                  setError(null)
                }}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
              >
                <option value="">Elige</option>
                {(Object.keys(NOMBRE_ACTIVIDAD) as Actividad[]).map((clave) => (
                  <option key={clave} value={clave}>{NOMBRE_ACTIVIDAD[clave]}</option>
                ))}
              </select>
            </label>
          </div>
        </form>

        {datos !== null && !dentroDeRango && (
          <p className="mt-2 text-etiqueta text-aviso">Revisa la edad, el peso y la altura.</p>
        )}

        {rango !== null && (
          <div
            role="status"
            aria-live="polite"
            className="mt-4 flex flex-col gap-2 rounded-campo bg-marfil p-3"
          >
            <p className="text-etiqueta text-secundaria">Gasto diario estimado</p>
            <p className="font-display text-titulo font-semibold text-tinta tabular-nums">
              Entre {cifra(rango.bajo)} y {cifra(rango.alto)} kcal
            </p>
            <p className="text-etiqueta text-secundaria">
              Es una orientación, no una medida exacta.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <Boton onClick={() => void guardarObjetivo()} disabled={guardando}>
                {guardando ? 'Guardando…' : 'Usar como objetivo'}
              </Boton>
              <span className="text-etiqueta text-tinta-suave">
                Si lo usas: {cifra(rango.centro)} kcal para hoy.
              </span>
            </div>

            {guardado !== null && (
              <p className="text-etiqueta text-verde-fuerte">
                Guardado: {cifra(guardado)} kcal para hoy.
              </p>
            )}
            {error && (
              <p role="alert" className="text-etiqueta text-error">{error}</p>
            )}
          </div>
        )}
      </section>

      <section aria-labelledby="fuentes" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h3 id="fuentes" className="text-cuerpo-fuerte text-tinta">Fuentes</h3>
        <ul className="mt-2 flex flex-col gap-1">
          {FUENTES.map((fuente) => (
            <li key={fuente.url}>
              <a
                href={fuente.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex min-h-[44px] items-center text-cuerpo text-verde underline underline-offset-2"
              >
                {fuente.nombre}
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
