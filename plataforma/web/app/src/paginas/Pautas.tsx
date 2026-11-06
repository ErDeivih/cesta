/** Pautas de salud: las referencias con su fuente y una estimación declarada.
 *
 *  **Dos capas separadas.** Arriba, las cifras de referencia con su enlace y su fecha. Abajo, una
 *  estimación opcional que solo aparece si la persona rellena sus datos, y un objetivo que **solo
 *  existe cuando se elige qué hacer**: la app no propone una cifra al abrir ni al registrar nada.
 *  Lo que se guarda va a la misma clave que lee Calorías (`objetivo:<fecha>`), y solo al pulsar.
 *
 *  **La cuenta vive en `logica/salud.ts`.** Aquí no se hace ni una: esta pantalla enseña la
 *  cifra, su rango, el «por qué» en llano y de dónde sale. El formulario empieza vacío: sin datos
 *  no hay cifra, y no se rellena con valores de ejemplo.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { guardaPreferencia } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { Boton, cx } from '../componentes/ui'
import {
  ACTIVIDAD,
  ACTIVIDADES,
  AJUSTES,
  AVISO_MEDICO,
  FUENTES,
  OBJETIVOS,
  PAUTAS_SALUD,
  SUELO_OBJETIVO,
  TEXTO_ESTIMACION,
  calcularEstimacion,
  gastoConRango,
  gramosDeMacros,
  porQueDelObjetivo,
  type Actividad,
  type DatosParaEstimar,
  type Fuente,
  type Objetivo,
  type Sexo,
} from '../logica/salud'

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

/** **Una fuente, con su fecha, tal y como se lee.** El documento va en el `title`: quien quiera
 *  saber qué abre lo tiene a mano, y quien no, no carga con un párrafo. */
function EnlaceFuente({ fuente }: { fuente: Fuente }) {
  return (
    <a
      href={fuente.url}
      target="_blank"
      rel="noopener noreferrer"
      title={fuente.documento}
      className="inline-flex min-h-[44px] items-center text-etiqueta text-verde underline underline-offset-2"
    >
      {fuente.nombre} · {fuente.fecha}
    </a>
  )
}

export function Pautas() {
  const cliente = useQueryClient()
  const [sexo, setSexo] = useState<Sexo | ''>('')
  const [edad, setEdad] = useState('')
  const [peso, setPeso] = useState('')
  const [altura, setAltura] = useState('')
  const [actividad, setActividad] = useState<Actividad | ''>('')
  const [objetivo, setObjetivo] = useState<Objetivo | ''>('')
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

  // **Sin los cinco datos no hay gasto, y sin objetivo elegido no hay objetivo.** Las dos cosas
  // son `null` a propósito: la pantalla no rellena el hueco con una cifra de ejemplo.
  const gasto = datos === null ? null : gastoConRango(datos)
  const estimacion = datos === null || objetivo === '' ? null : calcularEstimacion(datos, objetivo)
  const porQue = estimacion === null ? null : porQueDelObjetivo(estimacion, cifra)
  const yaGuardado = estimacion !== null && guardado !== null && guardado === estimacion.centro

  function cambia() {
    setError(null)
    setGuardado(null)
  }

  async function guardarObjetivo() {
    if (estimacion === null) return
    setGuardando(true)
    setError(null)
    try {
      await guardaPreferencia(`objetivo:${hoy()}`, {
        kcal: estimacion.centro,
        motivo: estimacion.objetivo,
        ajuste: estimacion.ajuste,
        macros: gramosDeMacros(estimacion.centro),
      })
      // La misma clave que leen Diario y Tendencias: al volver, el objetivo ya está.
      await cliente.invalidateQueries({ queryKey: ['yo'] })
      setGuardado(estimacion.centro)
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

      {/* **El límite, arriba y corto.** Vale para las pautas y para la estimación. */}
      <p className="rounded-campo border border-borde bg-marfil px-3 py-2 text-cuerpo text-secundaria">
        {AVISO_MEDICO}
      </p>

      <section aria-labelledby="pautas" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h3 id="pautas" className="text-cuerpo-fuerte text-tinta">En el día a día</h3>
        <ul className="mt-2 flex flex-col">
          {PAUTAS_SALUD.map((pauta) => (
            <li
              key={pauta.clave}
              className="border-b border-borde py-2 first:pt-0 last:border-b-0 last:pb-0"
            >
              <p className="text-cuerpo text-tinta-suave">
                <strong className="text-tinta">{pauta.titulo}.</strong> {pauta.cifra}
              </p>
              {pauta.detalle && (
                <p className="text-etiqueta text-tinta-suave">{pauta.detalle}</p>
              )}
              <div className="mt-1 flex flex-wrap gap-x-3">
                {pauta.fuentes.map((fuente) => (
                  <EnlaceFuente key={fuente.url} fuente={fuente} />
                ))}
              </div>
            </li>
          ))}
        </ul>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 text-etiqueta text-tinta-suave">
          <span>En España,</span>
          <EnlaceFuente fuente={FUENTES.aesan} />
        </div>
      </section>

      <section aria-labelledby="estimacion" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h3 id="estimacion" className="text-cuerpo-fuerte text-tinta">
          Tu gasto estimado
        </h3>
        <p className="mt-1 text-etiqueta text-tinta-suave">
          Opcional. A partir de 14 años. Rellena los cinco datos y elige qué quieres hacer.
        </p>

        <form className="mt-3 flex flex-col gap-3" onSubmit={(e) => e.preventDefault()}>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Sexo
              <select
                value={sexo}
                onChange={(e) => {
                  setSexo(e.target.value as Sexo | '')
                  cambia()
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
                  cambia()
                }}
                inputMode="numeric"
                autoComplete="off"
                aria-invalid={datos !== null && gasto === null}
                aria-describedby={datos !== null && gasto === null ? 'aviso-datos' : undefined}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Peso (kg)
              <input
                value={peso}
                onChange={(e) => {
                  setPeso(e.target.value)
                  cambia()
                }}
                inputMode="decimal"
                autoComplete="off"
                aria-invalid={datos !== null && gasto === null}
                aria-describedby={datos !== null && gasto === null ? 'aviso-datos' : undefined}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Altura (cm)
              <input
                value={altura}
                onChange={(e) => {
                  setAltura(e.target.value)
                  cambia()
                }}
                inputMode="decimal"
                autoComplete="off"
                aria-invalid={datos !== null && gasto === null}
                aria-describedby={datos !== null && gasto === null ? 'aviso-datos' : undefined}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>

            <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
              Actividad
              <select
                value={actividad}
                onChange={(e) => {
                  setActividad(e.target.value as Actividad | '')
                  cambia()
                }}
                className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
              >
                <option value="">Elige</option>
                {ACTIVIDADES.map((clave) => (
                  <option key={clave} value={clave}>{ACTIVIDAD[clave].nombre}</option>
                ))}
              </select>
            </label>
          </div>
        </form>

        {datos !== null && gasto === null && (
          <p id="aviso-datos" role="status" className="mt-2 text-etiqueta text-aviso">
            Revisa los datos: la edad va de 14 a 100 años, el peso de 30 a 250 kg y la altura de
            120 a 230 cm.
          </p>
        )}

        {gasto !== null && objetivo === '' && (
          <div
            role="status"
            aria-live="polite"
            className="mt-4 flex flex-col gap-2 rounded-campo bg-marfil p-3"
          >
            <p className="text-etiqueta text-secundaria">Gasto diario estimado</p>
            <p className="font-display text-titulo font-semibold text-tinta tabular-nums">
              Entre {cifra(gasto.bajo)} y {cifra(gasto.alto)} kcal
            </p>
            <p className="text-etiqueta text-secundaria">{TEXTO_ESTIMACION}</p>
          </div>
        )}
      </section>

      {gasto !== null && (
        <section aria-labelledby="objetivo" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
          <h3 id="objetivo" className="text-cuerpo-fuerte text-tinta">
            ¿Qué quieres hacer?
          </h3>

          <fieldset className="mt-2 min-w-0">
            <legend className="sr-only">Objetivo</legend>
            <div className="flex flex-wrap gap-2">
              {OBJETIVOS.map((clave) => (
                <label
                  key={clave}
                  className={cx(
                    'inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-campo border px-3 text-cuerpo',
                    objetivo === clave
                      ? 'border-verde bg-lavado-verde text-verde-fuerte'
                      : 'border-borde-fuerte bg-papel text-tinta hover:bg-marfil',
                  )}
                >
                  <input
                    type="radio"
                    name="objetivo"
                    value={clave}
                    checked={objetivo === clave}
                    onChange={() => {
                      setObjetivo(clave)
                      cambia()
                    }}
                    className="h-4 w-4 shrink-0 accent-bosque"
                  />
                  {AJUSTES[clave].nombre}
                </label>
              ))}
            </div>
          </fieldset>

          {objetivo === '' && (
            <p className="mt-2 text-etiqueta text-tinta-suave">
              Elige una opción y verás la cifra.
            </p>
          )}

          {estimacion !== null && estimacion.bajoSuelo && datos !== null && (
            <div
              role="status"
              aria-live="polite"
              className="mt-4 rounded-campo bg-lavado-aviso p-3 text-cuerpo text-tinta"
            >
              Con estos datos, un objetivo para perder quedaría por debajo de{' '}
              {cifra(SUELO_OBJETIVO[datos.sexo])} kcal al día. No te damos esa cifra:{' '}
              habla con un profesional.
            </div>
          )}

          {estimacion !== null && !estimacion.bajoSuelo && (
            <div className="mt-4 flex flex-col gap-2 rounded-campo bg-marfil p-3">
              {/* **Se anuncia la cifra y su por qué, no la ficha entera.** La región de estado
                  envuelve solo lo que cambia al elegir; las fuentes y los macros se leen cuando
                  se quieren, no cada vez que se toca una opción. */}
              <div
                role="status"
                aria-live="polite"
                aria-label="Tu objetivo"
                className="flex flex-col gap-2"
              >
                <h4 className="text-etiqueta uppercase tracking-wide text-tinta-suave">
                  Tu objetivo
                </h4>
                <p className="font-display text-titulo font-semibold text-tinta tabular-nums">
                  {cifra(estimacion.centro)} kcal al día
                </p>
                <p className="text-etiqueta text-tinta-suave">
                  Entre {cifra(estimacion.bajo)} y {cifra(estimacion.alto)} kcal al día.
                </p>
                {porQue !== null && <p className="text-cuerpo text-tinta-suave">{porQue}</p>}
              </div>

              {estimacion.ajuste !== 0 && (
                <div className="flex flex-wrap items-center gap-x-2 text-etiqueta text-tinta-suave">
                  <span>Un cambio moderado: 300–500 kcal al día.</span>
                  <EnlaceFuente fuente={FUENTES.cdc} />
                </div>
              )}

              <div className="flex flex-wrap items-center gap-x-2 text-etiqueta text-tinta-suave">
                <span>De dónde sale:</span>
                <EnlaceFuente fuente={FUENTES.mifflin} />
                <EnlaceFuente fuente={FUENTES.fao} />
              </div>

              <div>
                <h4 className="text-etiqueta uppercase tracking-wide text-tinta-suave">
                  Reparto orientativo
                </h4>
                <dl className="mt-1 grid gap-2 sm:grid-cols-3">
                  {estimacion.macros.map((macro) => (
                    <div key={macro.clave}>
                      <dt className="text-etiqueta text-tinta-suave">{macro.nombre}</dt>
                      <dd className="text-cuerpo font-semibold text-tinta tabular-nums">
                        {cifra(macro.gramos)} g
                      </dd>
                      <dd className="text-etiqueta text-tinta-suave">
                        Entre {cifra(macro.gramosMin)} y {cifra(macro.gramosMax)} g ·{' '}
                        {macro.pctMin}–{macro.pctMax} % de la energía
                      </dd>
                    </div>
                  ))}
                </dl>
                <div className="mt-1 flex flex-wrap items-center gap-x-2 text-etiqueta text-tinta-suave">
                  <span>Proteína y grasas:</span>
                  <EnlaceFuente fuente={FUENTES.who} />
                  <span>Hidratos:</span>
                  <EnlaceFuente fuente={FUENTES.efsa} />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Boton onClick={() => void guardarObjetivo()} disabled={guardando}>
                  {guardando ? 'Guardando…' : 'Usar como objetivo'}
                </Boton>
                <span className="text-etiqueta text-tinta-suave">
                  Si lo usas: {cifra(estimacion.centro)} kcal para hoy.
                </span>
              </div>

              {yaGuardado && (
                <p className="text-etiqueta text-verde-fuerte">
                  Guardado: {cifra(estimacion.centro)} kcal para hoy.
                </p>
              )}
              {error && (
                <p role="alert" className="text-etiqueta text-error">{error}</p>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
