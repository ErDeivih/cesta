/** La portada: lo que hay que ver al abrir Cesta, en un movil de 390 px.
 *
 *  **Sustituye al lanzador del 7 de octubre de 2026.** Aquel repartia tres accesos y
 *  «por donde ibas»; este contesta lo que se viene a mirar al abrir la app de pie en el
 *  pasillo: *que cuesta mi cesta, en que cadena esta mas barata, que se ha movido y por
 *  donde empiezo a buscar*. El artboard aprobado manda la composicion
 *  (`designs/cesta-app/project/Portada.dc.html`); los valores, el sistema de diseno.
 *
 *  Tres reglas que se ven en el codigo:
 *
 *  1. **Lo que no se sabe se dice, y no se rellena.** Sin sesion no hay lista: la tarjeta
 *     dice que hace la app y como empezar, no un «0,00 €» que parece una respuesta. Si la
 *     lista no tiene precios en todas las cadenas, no se corona una «mas barata» que solo
 *     compara tres productos de veinte.
 *  2. **La cifra manda.** El total de la cadena mas barata va en `precio-grande` y con
 *     `cifra` (cifras de ancho fijo): sin eso, comparar dos precios de un vistazo cuesta.
 *  3. **La interfaz no habla de como esta hecha (§8).** Ni API, ni calculos, ni nombres
 *     internos: lo que se lee es lo que sirve para decidir o actuar.
 */
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { euros, fecha, nombreCadena, porcentaje, porcentajeConSigno } from '../api/formato'
import { misListas, reparto, verLista, yo } from '../api/cesta'
import { useBajadas, useSecciones } from '../api/consultas'
import {
  IconoCarro, IconoLibro, IconoLupa, IconoPersona, IconoPlato,
} from '../componentes/iconos'
import { cx } from '../componentes/ui'
import { listaDelDiario } from '../logica/listaDelDiario'
import type { Baja, OpcionTienda, RepartoTiendas } from '../tipos'

/** La fecha de la cabecera, en espanol y en local. No es ISO: se lee, no se depura. */
const FECHA_LARGA = new Intl.DateTimeFormat('es-ES', {
  weekday: 'long',
  day: 'numeric',
  month: 'short',
})

export function fechaDeHoy(ahora: Date = new Date()): string {
  return FECHA_LARGA.format(ahora)
}

/** El enlace de la cuenta: con sesion, a los ajustes; sin ella, donde se entra.
 *
 *  **No hay una ruta `/entrar`**: la puerta de sesion vive en la lista, que es donde se
 *  necesita. Mandar a otra pantalla inventada seria un enlace roto con buenos modales.
 */
const DESTINO_CUENTA = '/ajustes'
const ENTRADA = '/compra/listas'

/* ============================================================== la cabecera === */

function Cabecera({ conSesion }: { conSesion: boolean }) {
  return (
    <header className="flex items-start justify-between gap-3 px-4 pb-2 pt-4">
      <div className="min-w-0">
        <p className="text-micro uppercase text-tinta-tenue">{fechaDeHoy()}</p>
        <h1 className="mt-1 font-serif text-portada font-semibold text-tinta">Cesta</h1>
      </div>
      <Link
        to={conSesion ? DESTINO_CUENTA : ENTRADA}
        aria-label="Tu cuenta"
        className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla border border-borde-fuerte bg-papel text-tinta-suave transition-colors duration-rapida ease-suave hover:text-tinta"
      >
        <IconoPersona width={20} height={20} />
      </Link>
    </header>
  )
}

/* =============================================================== el buscador === */

function Buscador() {
  const navegar = useNavigate()
  return (
    <form
      role="search"
      className="px-4 pt-2"
      onSubmit={(e) => {
        e.preventDefault()
        const texto = new FormData(e.currentTarget).get('q')
        const limpio = typeof texto === 'string' ? texto.trim() : ''
        if (limpio) navegar(`/compra?q=${encodeURIComponent(limpio)}`)
      }}
    >
      <label htmlFor="portada-q" className="sr-only">Buscar un producto</label>
      <div className="relative">
        <IconoLupa
          width={20}
          height={20}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-tinta-suave"
        />
        {/* *44 px de alto y 16 px de letra: el minimo para pulsar y el tamano que
            evita el zoom de Safari al enfocar.* */}
        <input
          id="portada-q"
          name="q"
          type="search"
          inputMode="search"
          enterKeyHint="search"
          autoComplete="off"
          placeholder="Buscar alubias, garbanzos, leche…"
          className="min-h-[44px] w-full rounded-campo border border-borde-fuerte bg-papel py-2 pl-11 pr-3 text-cuerpo text-tinta placeholder:text-tinta-tenue"
        />
      </div>
    </form>
  )
}

/* =============================================================== «Mi cesta» === */

/** La tarjeta que se mira primero: el total y la comparacion, o el estado honesto. */
function MiCesta({ conSesion, cargandoSesion }: {
  conSesion: boolean
  cargandoSesion: boolean
}) {
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: conSesion,
  })
  const listaId = listaDelDiario(listas.data, null)
  const detalle = useQuery({
    queryKey: ['lista', listaId],
    queryFn: () => verLista(listaId as string),
    enabled: listaId != null,
  })
  const comparacion = useQuery({
    queryKey: ['reparto', listaId],
    queryFn: () => reparto(listaId as string),
    enabled: listaId != null,
  })

  if (cargandoSesion || (conSesion && listas.isPending)) {
    return <TarjetaCargando que="tu cesta" />
  }

  if (!conSesion) {
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Entra para guardar tu lista y ver en qué cadena sale más barata.
        </p>
        <EnlaceCesta a={ENTRADA}>Entrar</EnlaceCesta>
      </section>
    )
  }

  if (listas.isError) {
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-error">
          No he podido mirar los precios de tu lista. Tu lista sigue ahí.
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-4">
          <BotonReintentar onClick={() => void listas.refetch()} />
          <EnlaceCesta a={ENTRADA}>Abrir mi lista</EnlaceCesta>
        </div>
      </section>
    )
  }

  if (listaId == null) {
    // *Tener listas y no tener «la de casa» no es lo mismo que no tener ninguna:
    // la primera se arregla eligiendo, la segunda creando. El texto lo dice.*
    const hayListas = (listas.data?.length ?? 0) > 0
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-tinta-suave">
          {hayListas
            ? 'No has marcado una lista de casa. Abre tus listas y elige la de la compra; aquí verás cuánto cuesta en cada cadena.'
            : 'Todavía no tienes una lista de casa. Crea la lista de la compra y aquí verás cuánto cuesta en cada cadena.'}
        </p>
        <EnlaceCesta a={ENTRADA}>{hayListas ? 'Abrir mis listas' : 'Crear mi lista'}</EnlaceCesta>
      </section>
    )
  }

  if (detalle.isPending || comparacion.isPending) {
    return <TarjetaCargando que="los precios de tu lista" />
  }

  if (detalle.isError || comparacion.isError) {
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-error">
          No he podido mirar los precios de tu lista. Tu lista sigue ahí.
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-4">
          <BotonReintentar
            onClick={() => {
              void detalle.refetch()
              void comparacion.refetch()
            }}
          />
          <EnlaceCesta a={ENTRADA}>Abrir mi lista</EnlaceCesta>
        </div>
      </section>
    )
  }

  const lineas = detalle.data?.lineas ?? []
  if (lineas.length === 0) {
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Tu lista está vacía. Busca lo que compras y añádelo; aquí saldrá el total de la
          cadena más barata.
        </p>
        <EnlaceCesta a="/compra">Buscar productos</EnlaceCesta>
      </section>
    )
  }

  const r = comparacion.data
  if (!r) return <TarjetaCargando que="los precios de tu lista" />

  // *** Solo se compara lo que es comparable. *** *Una cadena a la que le faltan
  // nueve productos de veinte sale «mas barata» sin serlo; coronarla seria el mismo
  // fallo que rellenar un dato que falta con un cero.*
  const comparables = r.lineas ?? 0
  if (comparables === 0) {
    // *** CERO NO ES UN PRECIO. *** *Sin ninguna linea comparable el filtro de abajo dejaria
    // pasar a todas las cadenas con total 0 y la tarjeta coronaria «0,00 €» como la mas
    // barata.* *Se dice lo que pasa: no hay ningun precio confirmado que sumar.*
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Todavía no hay ninguna línea con precio confirmado. Confirma los productos de la
          lista y aquí saldrá cuánto cuesta en cada cadena.
        </p>
        <EnlaceCesta a={`/compra/listas/${listaId}`}>Ver mi lista</EnlaceCesta>
      </section>
    )
  }

  const completas = (r.una_tienda ?? [])
    .filter((o) => (o.faltan?.length ?? 0) === 0 && o.encontrados >= comparables)
    .sort((a, b) => a.total_cent - b.total_cent)

  // *Y aunque haya lineas comparables, un total a cero no es un precio: si todas las
  // cadenas suman cero es que no hay nada que coronar.*
  if (completas.length === 0 || !completas.some((o) => o.total_cent > 0)) {
    return (
      <section aria-labelledby="mi-cesta" className={MARCO}>
        <TituloCesta />
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Todavía no puedo comparar la lista entera: hay líneas sin precio confirmado o
          productos que no están en todas las cadenas.
        </p>
        <EnlaceCesta a={`/compra/listas/${listaId}`}>Ver mi lista</EnlaceCesta>
      </section>
    )
  }

  const barata = completas[0]
  const cara = completas[completas.length - 1]
  const ahorroPct = cara.total_cent > barata.total_cent
    ? ((cara.total_cent - barata.total_cent) / cara.total_cent) * 100
    : null
  const filas = completas.slice(0, 3)
  const mayor = filas[filas.length - 1]?.total_cent ?? barata.total_cent
  const cuantas = completas.length

  return (
    <section
      aria-labelledby="mi-cesta"
      className="rounded-tarjeta bg-bosque p-4 text-sobre-bosque shadow-alzado"
    >
      <h2 id="mi-cesta" className="text-micro uppercase">Mi cesta</h2>
      <div className="mt-2 flex flex-wrap items-baseline gap-3">
        <p className="cifra text-precio-grande font-semibold">
          {euros(barata.total_cent)}
        </p>
        {ahorroPct != null && (
          <span className="cifra inline-flex min-h-6 items-center rounded-pastilla bg-lima px-2 text-etiqueta-fuerte text-sobre-lima">
            −{porcentaje(ahorroPct)}
          </span>
        )}
      </div>
      <p className="mt-1 text-etiqueta">
        en {nombreCadena(barata.cadena)}, la más barata de {cuantas}{' '}
        {cuantas === 1 ? 'cadena' : 'cadenas'}
      </p>

      <ul className="mt-3 flex flex-col gap-2">
        {filas.map((o, i) => (
          <FilaDeCadena key={o.cadena} opcion={o} mayor={mayor} mejor={i === 0} />
        ))}
      </ul>

      <Link
        to={`/compra/listas/${listaId}`}
        className="mt-2 inline-flex min-h-[44px] items-center gap-1.5 text-cuerpo-fuerte underline underline-offset-4"
      >
        {cuantas === 1 ? 'Ver la lista' : `Ver las ${cuantas} cadenas`}
        <span aria-hidden="true">→</span>
      </Link>
    </section>
  )
}

const MARCO = 'rounded-tarjeta border border-borde bg-papel p-4 shadow-apoyado'

function TituloCesta() {
  return <h2 id="mi-cesta" className="text-micro uppercase text-tinta-tenue">Mi cesta</h2>
}

function EnlaceCesta({ a, children }: { a: string; children: ReactNode }) {
  return (
    <Link
      to={a}
      className="mt-1 inline-flex min-h-[44px] items-center text-cuerpo-fuerte text-verde underline underline-offset-4"
    >
      {children}
    </Link>
  )
}

function BotonReintentar({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex min-h-[44px] items-center text-cuerpo-fuerte text-verde underline underline-offset-4"
    >
      Volver a intentarlo
    </button>
  )
}

/** Una cadena de la comparacion: nombre, barra proporcional y su total.
 *
 *  *La barra es la comparacion hecha forma: la mas barata va en `lima` y las demas en
 *  `papel` sobre el bosque. El color no basta, por eso cada fila lleva su cifra al lado.*
 */
function FilaDeCadena({ opcion, mayor, mejor }: {
  opcion: OpcionTienda
  mayor: number
  mejor: boolean
}) {
  const ancho = mayor > 0 ? Math.max(4, Math.min(100, (opcion.total_cent / mayor) * 100)) : 0
  return (
    <li className="flex items-center gap-2">
      <span className="w-16 shrink-0 truncate text-etiqueta">{nombreCadena(opcion.cadena)}</span>
      <span className="flex flex-1 items-center">
        <span
          style={{ width: `${ancho}%` }}
          className={cx('block h-2 rounded-pastilla', mejor ? 'bg-lima' : 'bg-papel')}
        />
      </span>
      <span className="cifra w-16 shrink-0 text-right text-etiqueta">
        {euros(opcion.total_cent)}
      </span>
    </li>
  )
}

function TarjetaCargando({ que }: { que: string }) {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">Cargando {que}…</span>
      <div aria-hidden="true" className="rounded-tarjeta border border-borde bg-papel p-4">
        <div className="h-3 w-24 animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
        <div className="mt-3 h-8 w-32 animate-pulse rounded-campo bg-marfil motion-reduce:animate-none" />
        <div className="mt-3 h-2 w-full animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
        <div className="mt-2 h-2 w-2/3 animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
      </div>
    </div>
  )
}

/* ========================================================= «Se han movido» === */

function SeHanMovido({ conSesion }: { conSesion: boolean }) {
  // *Con sesion, lo de tu lista; sin ella, las bajadas mayores del catalogo -- y se
  // dice, porque un titulo que promete «lo tuyo» cuando no hay «tuyo» miente.*
  const bajadas = useBajadas(7, false, [], conSesion)
  const lista = bajadas.data?.resultados ?? []
  const soloMios = bajadas.data?.solo_mios === true

  return (
    <section aria-labelledby="se-han-movido">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 id="se-han-movido" className="font-serif text-titulo font-semibold text-tinta">
          Se han movido
        </h2>
        <span className="text-etiqueta text-tinta-tenue">Últimos 7 días</span>
      </div>

      {!soloMios && !bajadas.isPending && (
        <p className="mb-2 text-etiqueta text-tinta-suave">
          {conSesion
            ? 'Bajadas de todas las cadenas, no solo de tu lista.'
            : 'Bajadas de todas las cadenas.'}
        </p>
      )}

      {bajadas.isPending && (
        <div role="status" aria-live="polite">
          <span className="sr-only">Cargando lo que ha bajado…</span>
          <div aria-hidden="true" className="grid gap-2">
            {[0, 1].map((i) => (
              <div
                key={i}
                className="h-16 animate-pulse rounded-tarjeta bg-papel motion-reduce:animate-none"
              />
            ))}
          </div>
        </div>
      )}

      {bajadas.isError && (
        <div role="alert" className="rounded-tarjeta border border-borde bg-papel p-4">
          <p className="text-cuerpo text-tinta">No he podido mirar lo que ha bajado.</p>
          <BotonReintentar onClick={() => void bajadas.refetch()} />
        </div>
      )}

      {!bajadas.isPending && !bajadas.isError && lista.length === 0 && (
        <p className="rounded-tarjeta border border-dashed border-borde-fuerte bg-papel p-4 text-cuerpo text-tinta-suave">
          Nada ha bajado en los últimos 7 días.
        </p>
      )}

      {lista.length > 0 && (
        <ul className="flex flex-col gap-2">
          {lista.slice(0, 3).map((b, i) => (
            <FilaDeBajada key={`${b.nombre}-${b.cadena}-${i}`} baja={b} />
          ))}
        </ul>
      )}
      {lista.length > 3 && (
        <Link
          to="/avisos"
          className="mt-1 inline-flex min-h-[44px] items-center text-cuerpo-fuerte text-verde underline underline-offset-4"
        >
          Ver todas las bajadas
        </Link>
      )}
    </section>
  )
}

function FilaDeBajada({ baja }: { baja: Baja }) {
  const diferencia = baja.precio_antes_cent != null && baja.precio_cent != null
    ? baja.precio_antes_cent - baja.precio_cent
    : null
  const bajaDePrecio = diferencia == null ? baja.variacion_pct <= 0 : diferencia >= 0
  const cuanto = diferencia != null && diferencia !== 0
    ? `${diferencia > 0 ? '−' : '+'}${euros(Math.abs(diferencia))}`
    : porcentajeConSigno(baja.variacion_pct)
  const sentido = bajaDePrecio ? 'baja' : 'sube'
  const cuando = fecha(baja.desde, true)

  const contenido = (
    <>
      <span className="min-w-0 flex-1">
        <span className="block text-etiqueta text-tinta-tenue">
          {nombreCadena(baja.cadena)} · {cuando} · {sentido}
        </span>
        <span className="block break-words text-cuerpo-fuerte text-tinta">{baja.nombre}</span>
      </span>
      <span className="shrink-0 text-right">
        <span className="cifra block text-precio-fila text-tinta">{euros(baja.precio_cent)}</span>
        <span
          className={cx(
            'cifra inline-flex items-center gap-0.5 text-etiqueta-fuerte',
            bajaDePrecio ? 'text-precio-baja' : 'text-precio-sube',
          )}
        >
          <span aria-hidden="true">{bajaDePrecio ? '↓' : '↑'}</span>
          {cuanto}
        </span>
      </span>
    </>
  )

  const clases = 'flex min-h-[64px] items-center gap-3 rounded-tarjeta bg-papel p-3 shadow-apoyado'
  if (baja.grupo_id == null) return <li className={clases}>{contenido}</li>
  return (
    <li>
      <Link
        to={`/compra/comparar/${baja.grupo_id}`}
        className={cx(
          clases,
          'transition-colors duration-rapida ease-suave hover:bg-marfil',
        )}
      >
        {contenido}
      </Link>
    </li>
  )
}

/* ============================================================== los pasillos === */

function PorPasillo() {
  const secciones = useSecciones([])
  const lista = (secciones.data?.secciones ?? []).slice(0, 6)

  return (
    <section aria-labelledby="por-pasillo">
      <h2 id="por-pasillo" className="mb-3 font-serif text-titulo font-semibold text-tinta">
        Por pasillo
      </h2>

      {secciones.isPending && (
        <div role="status" aria-live="polite">
          <span className="sr-only">Cargando los pasillos…</span>
          <div aria-hidden="true" className="flex flex-wrap gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-11 w-32 animate-pulse rounded-campo bg-papel motion-reduce:animate-none"
              />
            ))}
          </div>
        </div>
      )}

      {secciones.isError && (
        <div role="alert" className="rounded-tarjeta border border-borde bg-papel p-4">
          <p className="text-cuerpo text-tinta">No he podido traer los pasillos.</p>
          <BotonReintentar onClick={() => void secciones.refetch()} />
        </div>
      )}

      {!secciones.isPending && !secciones.isError && lista.length === 0 && (
        <p className="text-cuerpo text-tinta-suave">Todavía no hay pasillos que enseñar.</p>
      )}

      {lista.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {lista.map((s) => (
            <li key={s.seccion}>
              <Link
                to={`/compra?seccion=${encodeURIComponent(s.seccion)}`}
                className="inline-flex min-h-[44px] items-center rounded-campo border border-borde-fuerte bg-papel px-3.5 text-cuerpo text-tinta transition-colors duration-rapida ease-suave hover:bg-marfil"
              >
                {s.nombre}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/* ============================================================ la barra de abajo === */

const DESTINOS = [
  { a: '/compra', texto: 'Compra', Icono: IconoCarro },
  { a: '/recetas', texto: 'Recetas', Icono: IconoLibro },
  { a: '/calorias', texto: 'Calorías', Icono: IconoPlato },
] as const

function BarraDeAbajo() {
  const { pathname } = useLocation()
  return (
    <nav
      aria-label="Secciones"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-borde bg-papel pb-[env(safe-area-inset-bottom)]"
    >
      <div className="mx-auto flex max-w-portada items-stretch gap-2 px-2 py-2">
        {DESTINOS.map(({ a, texto, Icono }) => {
          // *La portada pertenece a Compra: por eso `Compra` esta activo en `/`.*
          const activa = a === '/compra'
            ? pathname === '/' || pathname.startsWith('/compra')
            : pathname.startsWith(a)
          return (
            <Link
              key={a}
              to={a}
              aria-current={activa ? 'page' : undefined}
              className={cx(
                'flex min-h-[56px] flex-1 flex-col items-center justify-center gap-1 rounded-campo px-1 text-micro font-semibold transition-colors duration-rapida ease-suave',
                activa ? 'text-terracota' : 'text-tinta-suave hover:text-tinta',
              )}
            >
              <Icono width={22} height={22} />
              {texto}
              <span
                aria-hidden="true"
                className={cx(
                  'h-0.5 w-7 rounded-pastilla',
                  activa ? 'bg-terracota' : 'bg-transparent',
                )}
              />
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

/* ================================================================== la portada === */

export function Portada() {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const conSesion = sesion.data?.usuario != null

  return (
    <div className="min-h-screen bg-marfil text-tinta">
      <div className="mx-auto flex min-h-screen w-full max-w-portada flex-col">
        <Cabecera conSesion={conSesion} />
        <Buscador />
        <main className="entra-pantalla flex flex-1 flex-col gap-6 px-4 pb-[calc(7rem+env(safe-area-inset-bottom))] pt-4">
          <MiCesta conSesion={conSesion} cargandoSesion={sesion.isPending} />
          <SeHanMovido conSesion={conSesion} />
          <PorPasillo />
        </main>
        <BarraDeAbajo />
      </div>
    </div>
  )
}
