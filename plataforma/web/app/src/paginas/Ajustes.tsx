/** **Tu perfil**: la cuenta, lo que la app tiene que recordar de ti y con qué
 *  avisos cuentas.
 *
 *  La composición es la del artboard aprobado (`designs/cesta-app/project/Perfil.dc.html`):
 *  la cuenta con su nombre, las preferencias, los avisos y «Cerrar sesión» al final. Los
 *  valores —marfil, papel, bosque, tipos, radios y sombra— son los del sistema «Cesta App»,
 *  no se eligen aquí.
 *
 *  **Lo que se pinta es lo que se puede guardar.** El artboard enseñaba también «Dieta» y
 *  «Alérgenos», y las dos se quedan fuera a propósito: no hay ninguna preferencia donde
 *  apuntarlas y ningún sitio de la app que las lea, así que un control ahí sería un adorno
 *  que promete algo que no pasa. Es la regla del encargo: mejor no pintarlo que fingirlo.
 *
 *  **El objetivo de calorías no se edita aquí.** La fila enseña el de hoy y lleva a
 *  Calorías, que es donde se pone y donde se ve con el resto del día. Duplicar el editor en
 *  dos pantallas sería dos sitios que pueden acabar diciendo cosas distintas; y el artboard
 *  ya lo pinta como una fila que lleva a otra pantalla. Si no hay objetivo se dice «Sin
 *  objetivo», nunca un 2.200 de adorno.
 *
 *  **Nada de diagnóstico.** Hasta el 6 de noviembre de 2026 esta pantalla enseñaba la
 *  frescura y la cobertura del catálogo, cadena a cadena. Eso es una herramienta de
 *  administración (§8) y no lo que alguien viene a hacer aquí: vive en `/panel`, que sigue
 *  existiendo para eso. En el perfil solo va lo que cambia una decisión de quien compra.
 *
 *  **La cuenta sale de la sesión, y solo de la sesión.** El nombre es `nombre` si la API lo
 *  trae; si no, el usuario con el que se entra. El correo no se inventa: la API no lo manda,
 *  así que no hay línea de correo. Y sin sesión no hay perfil: se enseña la puerta de
 *  entrada compartida, con su enlace, en vez de una frase sin salida.
 */
import { useId, useState } from 'react'
import { Link } from 'react-router-dom'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { cadenasCerca, guardarPreferencia } from '../api/ajustes'
import { textoDeError } from '../api/cliente'
import { borrarme, salir, yo } from '../api/cesta'
import { nombreCadena, numero } from '../api/formato'
import { EntraParaVer } from '../componentes/PuertaDeSesion'
import {
  Aviso,
  Boton,
  CampoTexto,
  Casilla,
  Etiqueta,
  Fallo,
  Resumen,
} from '../componentes/ui'

/** Las cadenas que existen en el catálogo. Es la misma lista que usa el colector; aquí
 *  solo hace falta para poder marcar una. No se pide a `/estado` porque esa respuesta es
 *  el estado de la ingesta —diagnóstico— y el perfil no tiene por qué depender de él. */
const CADENAS = ['mercadona', 'carrefour', 'dia', 'aldi', 'alcampo', 'lidl'] as const

/** Los tres avisos del artboard. Se guardan como preferencias de la cuenta (el servidor
 *  las guarda por `usuario_id`, no por navegador): dos personas en el mismo aparato no se
 *  pisan. Los valores de partida son los del artboard aprobado; en cuanto se toca uno,
 *  queda guardado. */
const AVISOS: { clave: string; texto: string; porDefecto: boolean }[] = [
  { clave: 'avisos_bajadas_favoritos', texto: 'Bajadas de tus favoritos', porDefecto: true },
  { clave: 'avisos_ofertas_club', texto: 'Ofertas de tu club', porDefecto: true },
  { clave: 'avisos_lista_compartida', texto: 'Lista compartida', porDefecto: false },
]

/** La fecha de hoy en local, que es la misma que usa el diario para el objetivo. */
function hoy(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

/** El objetivo de calorías de hoy, tal y como lo lee Calorías/Tendencias
 *  (`preferencias["objetivo:<fecha>"]`, con `{kcal}` dentro). `null` si no hay. */
function objetivoDe(preferencias: Record<string, unknown>): number | null {
  const guardado = preferencias[`objetivo:${hoy()}`]
  // *El formato que se guarda es `{kcal}`, pero se acepta también un número suelto: es lo
  // que ya hace `Diario.objetivoDe`, y las dos pantallas tienen que leer lo mismo.*
  const valor = guardado && typeof guardado === 'object' && 'kcal' in guardado
    ? (guardado as { kcal?: unknown }).kcal
    : guardado
  return typeof valor === 'number' && Number.isFinite(valor) && valor > 0
    ? Math.round(valor)
    : null
}

/** Un booleano guardado, o el valor de partida si todavía no hay nada guardado. */
function booleano(valor: unknown, porDefecto: boolean): boolean {
  return typeof valor === 'boolean' ? valor : porDefecto
}

/** «Todas», «Mercadona» o «Mercadona, DIA y Aldi», sin una coma colgando. */
function textoDeCadenas(cadenas: string[]): string {
  if (cadenas.length === 0) return 'Todas'
  const nombres = cadenas.map((c) => nombreCadena(c))
  if (nombres.length === 1) return nombres[0]
  return `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`
}

/** La flecha de una fila que lleva a otra pantalla. */
function FlechaDerecha() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className="shrink-0"
    >
      <path d="M9 6l6 6-6 6" />
    </svg>
  )
}

/* ================================================================ la cabecera === */

function CabeceraDelPerfil() {
  return (
    <header className="flex items-start gap-2">
      <Link
        to="/"
        aria-label="Volver a la portada"
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
        <p className="text-micro uppercase text-tinta-tenue">Tu cuenta</p>
        <h2 className="mt-1 break-words font-display text-titulo font-semibold text-tinta">
          Tu perfil
        </h2>
      </div>
    </header>
  )
}

/* ================================================================ los avisos === */

/** Una fila de aviso: el texto a la izquierda y la casilla a la derecha, en toda la fila.
 *  Mide 52 px de alto para que se pueda pulsar con el pulgar, no solo el cuadradito. */
function FilaDeAviso({ texto, activo, deshabilitado, alCambiar }: {
  texto: string
  activo: boolean
  deshabilitado: boolean
  alCambiar: (valor: boolean) => void
}) {
  const id = useId()
  return (
    <label
      htmlFor={id}
      className="flex min-h-[52px] cursor-pointer items-center justify-between gap-3 border-t border-borde"
    >
      <span className="text-cuerpo text-tinta">{texto}</span>
      <input
        id={id}
        type="checkbox"
        checked={activo}
        disabled={deshabilitado}
        onChange={(e) => alCambiar(e.target.checked)}
        className="h-[22px] w-[22px] shrink-0 accent-verde disabled:cursor-not-allowed disabled:opacity-50"
      />
    </label>
  )
}

/* ================================================================= los estados === */

function CargandoPerfil() {
  return (
    <div role="status" aria-live="polite" className="flex flex-col gap-4">
      <span className="sr-only">Cargando tu perfil…</span>
      <div aria-hidden="true" className="flex items-center gap-3">
        <div className="h-14 w-14 animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
        <div className="min-w-0 flex-1">
          <div className="h-4 w-1/2 animate-pulse rounded-nota bg-marfil motion-reduce:animate-none" />
          <div className="mt-2 h-3 w-1/3 animate-pulse rounded-nota bg-marfil motion-reduce:animate-none" />
        </div>
      </div>
      {[0, 1].map((i) => (
        <div
          key={i}
          aria-hidden="true"
          className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
        >
          <div className="h-3 w-1/4 animate-pulse rounded-nota bg-marfil motion-reduce:animate-none" />
          <div className="mt-4 h-11 w-full animate-pulse rounded-campo bg-marfil motion-reduce:animate-none" />
          <div className="mt-2 h-11 w-full animate-pulse rounded-campo bg-marfil motion-reduce:animate-none" />
        </div>
      ))}
    </div>
  )
}

/* =================================================================== la página === */

export function Ajustes() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })

  // **Lo que se acaba de tocar, por delante de lo que trajo la sesión.** El guardado es una
  // llamada de red; sin esto, la casilla no se movería hasta que volviera la respuesta y
  // parecería que no ha hecho nada. Si el guardado falla, se quita el adelanto y vuelve a
  // verse lo que hay de verdad en la cuenta.
  const [locales, setLocales] = useState<Record<string, unknown>>({})
  const [baja, setBaja] = useState(false)
  const [texto, setTexto] = useState('')

  const guarda = useMutation({
    mutationFn: (cambio: { clave: string; valor: unknown }) =>
      guardarPreferencia(cambio.clave, cambio.valor),
    onSuccess: () => {
      // La misma clave `['yo']` que leen el buscador (cadenas de cerca) y la gráfica
      // (objetivo). Al refrescarla, lo guardado vale para el resto de la aplicación.
      void cliente.invalidateQueries({ queryKey: ['yo'] })
    },
    onError: (_error, cambio) => {
      setLocales((antes) => {
        const copia = { ...antes }
        delete copia[cambio.clave]
        return copia
      })
    },
  })

  const salirSesion = useMutation({
    mutationFn: salir,
    // Se recarga todo, no solo `['yo']`: al salir no queda nada de esta cuenta que enseñar.
    // **Solo si de verdad se ha salido**: si la llamada falla, la sesión sigue pudiendo ser
    // válida y enseñar la puerta de entrada sería mentir sobre lo que ha pasado.
    onSuccess: () => {
      void cliente.invalidateQueries()
    },
  })

  const borra = useMutation({
    mutationFn: borrarme,
    onSuccess: () => {
      void cliente.invalidateQueries()
    },
  })

  const preferencias: Record<string, unknown> = {
    ...(sesion.data?.preferencias ?? {}),
    ...locales,
  }
  const puestas = cadenasCerca(preferencias)
  const objetivo = objetivoDe(preferencias)
  const quien = sesion.data?.usuario?.usuario ?? ''

  function guardaClave(clave: string, valor: unknown) {
    setLocales((antes) => ({ ...antes, [clave]: valor }))
    guarda.mutate({ clave, valor })
  }

  function alternaCadena(cadena: string) {
    const nuevas = puestas.includes(cadena)
      ? puestas.filter((c) => c !== cadena)
      : [...puestas, cadena]
    guardaClave('cadenas_cerca', nuevas)
  }

  if (sesion.isPending) {
    return (
      <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
        <CabeceraDelPerfil />
        <CargandoPerfil />
      </div>
    )
  }

  if (sesion.isError) {
    return (
      <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
        <CabeceraDelPerfil />
        <Fallo
          error={sesion.error}
          reintentar={() => void sesion.refetch()}
          titulo="No he podido traer tu perfil"
        />
      </div>
    )
  }

  if (!sesion.data?.usuario) {
    // **La puerta de siempre, la misma que usan el diario y las tendencias.** El perfil es
    // de cada uno, así que sin sesión no hay nada que enseñar ni que guardar.
    return <EntraParaVer texto="Tus preferencias se guardan con tu cuenta." />
  }

  const usuario = sesion.data.usuario
  const nombre = usuario.nombre?.trim() || usuario.usuario
  const inicial = (Array.from(nombre)[0] ?? '·').toUpperCase()
  const opciones = [
    ...CADENAS,
    ...puestas.filter((c) => !(CADENAS as readonly string[]).includes(c)),
  ]
  const resumenCadenas = textoDeCadenas(puestas)

  return (
    <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
      <CabeceraDelPerfil />

      {/* ---------------------------------------------------------------- la cuenta */}
      <section aria-label="Cuenta" className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="inline-flex h-14 w-14 shrink-0 items-center justify-center rounded-pastilla bg-bosque font-display text-titulo font-semibold text-sobre-bosque"
        >
          {inicial}
        </span>
        <div className="min-w-0">
          <p className="truncate text-cuerpo-fuerte text-tinta">{nombre}</p>
          <p className="truncate text-etiqueta text-tinta-tenue">@{usuario.usuario}</p>
        </div>
      </section>

      {/* ------------------------------------------------------------ preferencias */}
      <section
        aria-labelledby="preferencias"
        className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
      >
        <h2 id="preferencias" className="text-micro uppercase text-tinta-tenue">
          Preferencias
        </h2>

        <details className="mt-1 border-t border-borde">
          <Resumen className="min-h-[52px] text-cuerpo">
            {/* *** En dos lineas, no en una con elipsis. *** *El valor del ajuste que decide
                que cadenas ves no cabia al lado del nombre y se cortaba; debajo se lee entero
                y la flecha del desplegable queda a la derecha.* */}
            <span className="flex min-w-0 flex-col gap-0.5 py-1">
              <span className="text-tinta">Cadenas que tienes cerca</span>
              <span className="text-tinta-suave">{resumenCadenas}</span>
            </span>
          </Resumen>
          <div className="pb-3 pt-1">
            <p className="mb-2 text-etiqueta text-tinta-suave">
              La búsqueda solo enseña productos de las cadenas que marques. Sin ninguna, se
              miran todas.
            </p>
            <fieldset>
              <legend className="sr-only">Cadenas que tienes cerca</legend>
              <div className="flex flex-wrap gap-2">
                {opciones.map((c) => (
                  <Casilla
                    key={c}
                    etiqueta={nombreCadena(c)}
                    checked={puestas.includes(c)}
                    disabled={guarda.isPending}
                    onChange={() => alternaCadena(c)}
                  />
                ))}
              </div>
            </fieldset>
            {puestas.length > 0 && (
              <Boton
                variante="sutil"
                className="mt-2"
                disabled={guarda.isPending}
                onClick={() => guardaClave('cadenas_cerca', [])}
              >
                Quitar todas
              </Boton>
            )}
          </div>
        </details>

        {/* *El objetivo se cambia donde se ve el día entero*, que es Calorías. Aquí solo se
            enseña el de hoy: dos editores para el mismo dato acabarían diciendo cosas
            distintas, y el artboard ya lo dibuja como una fila que lleva a otra pantalla. */}
        <Link
          to="/calorias"
          className="flex min-h-[52px] items-center justify-between gap-3 border-t border-borde text-cuerpo text-tinta transition-colors duration-rapida ease-suave hover:text-terracota"
        >
          <span className="shrink-0">Objetivo de calorías</span>
          <span className="ml-auto flex min-w-0 items-center gap-1.5 text-tinta-suave">
            <span className="truncate">
              {objetivo === null ? 'Sin objetivo' : `${numero(objetivo, 0)} kcal`}
            </span>
            <FlechaDerecha />
          </span>
        </Link>
      </section>

      {/* ------------------------------------------------------------------ avisos */}
      <section
        aria-labelledby="avisos"
        className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
      >
        <h2 id="avisos" className="text-micro uppercase text-tinta-tenue">
          Avisos
        </h2>
        <div className="mt-1">
          {AVISOS.map((aviso) => (
            <FilaDeAviso
              key={aviso.clave}
              texto={aviso.texto}
              activo={booleano(preferencias[aviso.clave], aviso.porDefecto)}
              deshabilitado={guarda.isPending}
              alCambiar={(valor) => guardaClave(aviso.clave, valor)}
            />
          ))}
        </div>
      </section>

      {guarda.isError && (
        <Aviso tono="mal" titulo="No he podido guardar tus preferencias">
          {textoDeError(guarda.error)}
        </Aviso>
      )}

      {/* ---------------------------------------------------------------- la baja */}
      <details className="rounded-tarjeta border border-borde bg-papel p-4">
        <Resumen className="text-cuerpo text-tinta-suave">Dar de baja la cuenta</Resumen>
        <p className="mt-2 text-etiqueta text-tinta-suave">
          Se borran <strong className="text-tinta">tus listas, tus favoritos y tu cuenta</strong>.
          Lo que añadiste a listas de otras personas se queda, sin tu nombre. Esto no se puede
          deshacer.
        </p>
        {!baja && (
          <Boton variante="sutil" className="mt-2" onClick={() => setBaja(true)}>
            Quiero darme de baja
          </Boton>
        )}
        {baja && (
          <div className="mt-2 grid gap-2">
            <CampoTexto
              etiqueta={`Escribe ${quien} para confirmarlo`}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              autoComplete="off"
              autoCapitalize="none"
              spellCheck={false}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Boton
                variante="peligro"
                disabled={texto.trim() !== quien || borra.isPending}
                onClick={() => borra.mutate()}
              >
                {borra.isPending ? 'Dándome de baja…' : 'Darme de baja'}
              </Boton>
              <Boton
                variante="sutil"
                onClick={() => {
                  setBaja(false)
                  setTexto('')
                }}
              >
                No, déjalo
              </Boton>
            </div>
            {borra.isError && (
              <Etiqueta tono="aviso">{textoDeError(borra.error)}</Etiqueta>
            )}
          </div>
        )}
      </details>

      {/* -------------------------------------------------------------- la sesión */}
      <div className="flex flex-col gap-2">
        <Boton
          variante="normal"
          className="w-full justify-center"
          disabled={salirSesion.isPending}
          onClick={() => salirSesion.mutate()}
        >
          {/* *El color va en el texto y no en el botón*: la variante `normal` trae
              `text-tinta-fuerte`, y una clase de color añadida al botón no gana a la del
              componente —las dos son utilidades del mismo tipo y el orden lo decide el CSS
              generado—. El `<span>` sí pinta su propio color. */}
          <span className="text-terracota">
            {salirSesion.isPending ? 'Saliendo…' : 'Cerrar sesión'}
          </span>
        </Boton>
        {salirSesion.isError && (
          <Etiqueta tono="mal">{textoDeError(salirSesion.error)}</Etiqueta>
        )}
      </div>

      {/* **El aviso legal sigue aquí y no es un texto de desarrollador.** Quien compra
          tiene derecho a saber que los precios los publican las cadenas, que Cesta no
          está afiliada a ninguna y de dónde sale la nutrición. No explica cómo está hecha
          la app; dice qué se está mirando. */}
      <footer className="mt-2 border-t border-borde pt-4 text-etiqueta text-tinta-tenue">
        <p>
          Los precios son orientativos y pueden variar: los publica cada cadena y Cesta se
          limita a leerlos. Cesta <strong>no está afiliada, asociada ni patrocinada</strong>{' '}
          por ninguno de estos supermercados.
        </p>
        <p className="mt-2">
          Los datos viven en el ordenador de casa y no salen de ahí. Información nutricional
          de{' '}
          <a
            className="inline-flex min-h-[44px] items-center underline"
            href="https://openfoodfacts.org"
            rel="noreferrer noopener"
            target="_blank"
          >
            Open Food Facts
          </a>
          , bajo licencia ODbL.
        </p>
      </footer>
    </div>
  )
}
