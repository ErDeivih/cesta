/** Los componentes base, escritos a mano.
 *
 *  No se instala el CLI de shadcn: son ocho piezas pequenas y con Tailwind se
 *  escriben en una tarde. Un generador que copia ficheros a tu repositorio
 *  anade una dependencia de herramienta y un monton de codigo que no se lee.
 *
 *  Accesibilidad, que en una tabla de precios no es un adorno:
 *   - Los controles de pulsar miden 44 px de alto como minimo (se usa con una
 *     mano y el carro en la otra).
 *   - Los estados no se distinguen SOLO por color: cada etiqueta lleva texto.
 *   - Avisar de algo es `role="status"`; fallar, `role="alert"`.
 */
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import { useId } from 'react'

import { esSinRed, textoDeError } from '../api/cliente'

export function cx(...clases: (string | false | null | undefined)[]): string {
  return clases.filter(Boolean).join(' ')
}

// ------------------------------------------------------------------ boton ---

type VarianteBoton = 'principal' | 'normal' | 'sutil' | 'peligro'

const ESTILO_BOTON: Record<VarianteBoton, string> = {
  principal:
    'bg-sky-700 text-white hover:bg-sky-800 dark:bg-sky-700 dark:hover:bg-sky-800 border-transparent',
  normal:
    'bg-white text-neutral-800 hover:bg-neutral-50 dark:bg-neutral-800 dark:text-neutral-100 dark:hover:bg-neutral-700 border-neutral-300 dark:border-neutral-600',
  sutil:
    'bg-transparent text-sky-800 hover:bg-sky-50 dark:text-sky-300 dark:hover:bg-sky-950 border-transparent underline underline-offset-2',
  peligro:
    'bg-white text-red-800 hover:bg-red-50 dark:bg-neutral-800 dark:text-red-300 border-red-300 dark:border-red-800',
}

interface PropsBoton extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: VarianteBoton
  /** Para los botones con solo un icono: el texto queda oculto pero lo lee el
   *  lector de pantalla. Un icono sin nombre no es un boton. */
  compacto?: boolean
}

export function Boton({ variante = 'normal', compacto, className, ...resto }: PropsBoton) {
  return (
    <button
      type="button"
      {...resto}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-lg border font-medium transition-colors',
        // 44 px: el minimo para pulsar con el pulgar sin fallar. **En las dos
        // direcciones**: medido en el navegador el 23 de septiembre de 2026, los botones
        // «−» y «+» de la cantidad -- justo lo que se toca con el carro en marcha --
        // median **37 x 44**: el alto estaba, el ancho no, porque un solo caracter con
        // `px-3` no llega. Un `min-w` lo arregla sin tocar ninguna pantalla.
        compacto ? 'min-h-[44px] min-w-[44px] px-3 py-2' : 'min-h-[44px] px-4 py-2',
        'disabled:cursor-not-allowed disabled:opacity-50',
        ESTILO_BOTON[variante],
        className,
      )}
    />
  )
}

// --------------------------------------------------------------- etiqueta ---

type Tono = 'neutro' | 'bien' | 'mal' | 'aviso' | 'info' | 'dato'

const ESTILO_ETIQUETA: Record<Tono, string> = {
  neutro:
    'bg-neutral-200 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-100 border-transparent',
  bien: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100 border-emerald-300 dark:border-emerald-700',
  mal: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-100 border-red-300 dark:border-red-800',
  aviso:
    'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-100 border-amber-300 dark:border-amber-800',
  info: 'bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-100 border-sky-300 dark:border-sky-800',
  dato: 'bg-transparent text-neutral-600 dark:text-neutral-400 border-neutral-300 dark:border-neutral-600',
}

export function Etiqueta({
  tono = 'neutro',
  children,
  titulo,
}: {
  tono?: Tono
  children: ReactNode
  titulo?: string
}) {
  return (
    <span
      title={titulo}
      className={cx(
        'inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs font-medium',
        ESTILO_ETIQUETA[tono],
      )}
    >
      {children}
    </span>
  )
}

// ------------------------------------------------------------------ cajas ---

export function Tarjeta({
  titulo,
  sub,
  acciones,
  children,
  className,
}: {
  titulo?: ReactNode
  sub?: ReactNode
  acciones?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section
      className={cx(
        'rounded-xl border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-700 dark:bg-neutral-800',
        className,
      )}
    >
      {(titulo || acciones) && (
        <header className="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            {titulo && <h2 className="text-base font-semibold">{titulo}</h2>}
            {sub && <p className="mt-0.5 text-sm text-neutral-600 dark:text-neutral-400">{sub}</p>}
          </div>
          {acciones}
        </header>
      )}
      {children}
    </section>
  )
}

export function Aviso({
  tono = 'info',
  titulo,
  children,
}: {
  tono?: 'info' | 'aviso' | 'mal' | 'bien'
  titulo?: ReactNode
  children?: ReactNode
}) {
  const borde: Record<string, string> = {
    info: 'border-sky-300 bg-sky-50 text-sky-950 dark:border-sky-800 dark:bg-sky-950 dark:text-sky-100',
    aviso:
      'border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100',
    mal: 'border-red-300 bg-red-50 text-red-950 dark:border-red-800 dark:bg-red-950 dark:text-red-100',
    bien: 'border-emerald-300 bg-emerald-50 text-emerald-950 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-100',
  }
  return (
    <div
      role={tono === 'mal' ? 'alert' : 'status'}
      className={cx('rounded-lg border px-3 py-2 text-sm', borde[tono])}
    >
      {titulo && <p className="font-semibold">{titulo}</p>}
      {children}
    </div>
  )
}

/** Un dato con su etiqueta. Siempre los dos: un numero sin que es no informa. */
export function Dato({
  etiqueta,
  children,
  className,
}: {
  etiqueta: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <div className={className}>
      <dt className="text-xs uppercase tracking-wide text-tinta-suave">
        {etiqueta}
      </dt>
      <dd className="cifra mt-0.5 text-sm font-medium">{children}</dd>
    </div>
  )
}

// --------------------------------------------------------------- controles ---

interface PropsCasilla extends InputHTMLAttributes<HTMLInputElement> {
  etiqueta: ReactNode
}

export function Casilla({ etiqueta, id, className, ...resto }: PropsCasilla) {
  const generado = useId()
  const mio = id ?? generado
  return (
    <label
      htmlFor={mio}
      // 44 px de alto para poder pulsar la casilla y el texto con el dedo.
      className={cx(
        'inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 py-1 text-sm',
        'border-neutral-300 bg-white hover:bg-neutral-50 dark:border-neutral-600 dark:bg-neutral-800 dark:hover:bg-neutral-700',
        className,
      )}
    >
      <input
        id={mio}
        type="checkbox"
        {...resto}
        className="h-4 w-4 shrink-0 accent-sky-700 dark:accent-sky-500"
      />
      <span>{etiqueta}</span>
    </label>
  )
}

export function Selector({
  etiqueta,
  children,
  id,
  className,
  ...resto
}: SelectHTMLAttributes<HTMLSelectElement> & { etiqueta?: ReactNode }) {
  const generado = useId()
  const mio = id ?? generado
  return (
    <div className={cx('flex flex-col gap-1', className)}>
      {etiqueta && (
        <label htmlFor={mio} className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
          {etiqueta}
        </label>
      )}
      {/* Sin `text-sm`, y a proposito: el tamano se hereda del `html`, que son
          16 px. Por debajo de 16, Safari del movil hace zoom al enfocar el campo,
          la pagina se queda descuadrada y hay que pellizcar para volver. Estaba
          puesto en este componente y en `CampoTexto`, o sea en **todos** los
          campos de la aplicacion: el buscador, el login, los ajustes y las
          cantidades. Lo vigila `tests/test_ui_movil.py`. */}
      <select
        id={mio}
        {...resto}
        className="min-h-[44px] rounded-lg border border-neutral-500 bg-white px-3 py-2 dark:border-neutral-400 dark:bg-neutral-800"
      >
        {children}
      </select>
    </div>
  )
}

export function CampoTexto({
  etiqueta,
  id,
  className,
  ...resto
}: InputHTMLAttributes<HTMLInputElement> & { etiqueta?: ReactNode }) {
  const generado = useId()
  const mio = id ?? generado
  return (
    <div className={cx('flex flex-col gap-1', className)}>
      {etiqueta && (
        <label htmlFor={mio} className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
          {etiqueta}
        </label>
      )}
      {/* Igual que el `select` de arriba: sin `text-sm`. El tamano sale del
          `html` (16 px) porque por debajo Safari hace zoom al enfocar. */}
      <input
        id={mio}
        {...resto}
        className="min-h-[44px] rounded-lg border border-neutral-500 bg-white px-3 py-2 dark:border-neutral-400 dark:bg-neutral-800"
      />
    </div>
  )
}

// ------------------------------------------------------------ estados raros ---

export function Cargando({ que = 'los datos' }: { que?: string }) {
  // **Un hueco, no una linea de texto.** Lo pide el encargo (§8): *"los estados de
  // carga: nada de saltos de maquetacion. Un hueco del tamaño de lo que va a venir"*.
  // Una linea que dice "Cargando…" y despues se convierte en una lista de nueve filas
  // hace saltar todo lo que hay debajo -- y en el movil, con el pulgar ya camino del
  // boton, el boton se mueve.
  return (
    <div role="status" className="grid min-h-[6rem] place-items-center py-6">
      <p className="text-sm text-neutral-600 dark:text-neutral-400">Cargando {que}…</p>
    </div>
  )
}

/** El hueco de una lista o una tabla que todavia no ha llegado.
 *
 *  Con **la forma** de lo que va a venir: `filas` bloques de la altura de una fila, con
 *  el mismo hueco entre ellos que la lista de verdad (`gap-2`). Asi, cuando el dato
 *  llega, el contenido no empuja nada: ocupa el sitio que ya estaba reservado.
 *
 *  Un esqueleto que no se parece a lo que viene es peor que una linea de texto: reserva
 *  el sitio equivocado y encima promete una forma que no es. Por eso las dos formas que
 *  hay -- filas y rejilla -- son las de las dos cosas que se esperan en esta aplicacion:
 *  listas y cuadriculas.
 */
export function Esqueleto({ filas = 4, alto = '3.25rem' }: { filas?: number; alto?: string }) {
  return (
    <div role="status" className="grid gap-2">
      {Array.from({ length: filas }).map((_, i) => (
        <div
          key={i}
          style={{ height: alto }}
          className="animate-pulse rounded-lg bg-neutral-100 dark:bg-neutral-700/60"
        />
      ))}
      <span className="sr-only">Cargando…</span>
    </div>
  )
}

/** Lo mismo, con la forma de la cuadricula del mosaico. */
export function EsqueletoRejilla({ tarjetas = 6, alto = '11rem' }:
                                 { tarjetas?: number; alto?: string }) {
  return (
    <div role="status" className="grid grid-cols-3 gap-2">
      {Array.from({ length: tarjetas }).map((_, i) => (
        <div
          key={i}
          style={{ height: alto }}
          className="animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-700/60"
        />
      ))}
      <span className="sr-only">Cargando…</span>
    </div>
  )
}

export function Fallo({ error, reintentar }: { error: unknown; reintentar?: () => void }) {
  // El texto lo pone `textoDeError`, que ya distingue "sin conexion" de "el
  // servidor ha contestado 500". Aqui no se inventa un mensaje nuevo.
  //
  // **Y el color tambien lo decide eso**, no la pantalla que llama: si lo que pasa
  // es que no hay red, esto no es un fallo, es un movil en un pasillo de supermercado
  // -- y en rojo, con `role="alert"`, se lee como "la aplicacion se ha roto" y se
  // deja de usar justo donde mas sirve. Se arregla en **un solo sitio** y no en las
  // seis pantallas que usan `Fallo`: buscar, la ficha, el grupo, el escaner, el panel
  // y el panel de matching. Si se arreglara pantalla por pantalla, la septima
  // volveria a nacer en rojo.
  if (esSinRed(error)) {
    return (
      <Aviso tono="aviso" titulo="Sin cobertura">
        <p>No he podido traer esto: no hay conexion con casa.</p>
        {reintentar && (
          <>
            <p className="mt-1">Vuelve a intentarlo cuando tengas red.</p>
            <Boton variante="normal" className="mt-2" onClick={reintentar}>
              Volver a intentarlo
            </Boton>
          </>
        )}
      </Aviso>
    )
  }
  return (
    <Aviso tono="mal" titulo="No he podido traer esto">
      <p>{textoDeError(error)}</p>
      {reintentar && (
        <Boton variante="normal" className="mt-2" onClick={reintentar}>
          Volver a intentarlo
        </Boton>
      )}
    </Aviso>
  )
}

export function Vacio({ titulo, children }: { titulo: ReactNode; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-neutral-300 px-4 py-8 text-center dark:border-neutral-600">
      <p className="font-medium">{titulo}</p>
      {children && (
        <div className="mx-auto mt-2 max-w-prose text-sm text-neutral-600 dark:text-neutral-400">
          {children}
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------------ tabla ---

/** Envoltorio de tabla: **en el móvil se apila, en pantalla ancha se desliza si hace falta**.
 *
 *  Una tabla de precios con siete columnas no cabe en un móvil, y las tres salidas malas son:
 *  aplastarla hasta que no se lee, esconder columnas (y que el dato que falta sea justo el que
 *  se buscaba) o dejarla salirse de la pantalla. Hasta el 27 de septiembre de 2026 la salida
 *  era scroll horizontal con la primera columna pegada y un aviso de que se podía deslizar, y
 *  **el aviso era el sintoma de que la respuesta no se veía**: en un móvil de 390 px lo que
 *  quedaba fuera era la columna del precio, medido en el buscador y en el panel. Ahora, por
 *  debajo de 640 px, cada fila es una línea y las celdas fluyen debajo (lo hace `.tabla-scroll`
 *  en `estilos.css`); de 640 px para arriba sigue la tabla de verdad, que es donde comparar
 *  columnas tiene sentido.
 *
 *  `minAncho` se queda para la tabla ancha, y en el móvil se anula: si no, el ancho mínimo
 *  seguiría empujando la página en horizontal.
 */
export function TablaScroll({
  children,
  etiqueta,
  minAncho = '46rem',
}: {
  children: ReactNode
  etiqueta: string
  minAncho?: string
}) {
  return (
    <div
      className="tabla-scroll"
      role="region"
      aria-label={etiqueta}
      tabIndex={0}
    >
      <div style={{ minWidth: minAncho }}>{children}</div>
    </div>
  )
}

export function Th({
  children,
  ordenable,
  activo,
  direccion,
  onClick,
  className,
}: {
  children: ReactNode
  ordenable?: boolean
  activo?: boolean
  direccion?: 'asc' | 'desc' | false
  onClick?: (evento?: unknown) => void
  className?: string
}) {
  const contenido = (
    <span className="inline-flex items-center gap-1">
      {children}
      {activo && <span aria-hidden="true">{direccion === 'desc' ? '▾' : '▴'}</span>}
    </span>
  )
  return (
    <th
      scope="col"
      aria-sort={activo ? (direccion === 'asc' ? 'ascending' : 'descending') : 'none'}
      className={cx(
        'sticky top-0 z-10 border-b border-neutral-200 bg-neutral-50 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
        className,
      )}
    >
      {ordenable && onClick ? (
        <button
          type="button"
          // El manejador de TanStack espera un evento: se le pasa el del boton
          // tal cual, que es lo que necesita para el orden multiple con Shift.
          onClick={(e) => onClick(e)}
          className="inline-flex min-h-[44px] items-center gap-1 hover:text-neutral-900 dark:hover:text-white"
        >
          {contenido}
        </button>
      ) : (
        contenido
      )}
    </th>
  )
}

/** Una celda.
 *
 *  `etiqueta` es **para el móvil**: por debajo de 640 px las tablas se apilan (una fila por
 *  línea, con las celdas fluyendo en varias líneas) y ahí no hay cabecera de columna que diga
 *  qué es cada número. Las celdas cuyo valor se explica solo («0,96 €/l», «−18 %», una fecha)
 *  no necesitan etiqueta; las que son un número pelado («1.234»), sí, o el dato se queda sin
 *  sujeto. Ver `.tabla-scroll` en `estilos.css`.
 *
 *  La etiqueta es **texto de verdad y no un `::before` de CSS**, y eso importa: el contenido
 *  de un pseudo-elemento no lo lee un lector de pantalla ni aparece en `innerText`, así que la
 *  medida de la puerta («¿dice sobre cuántos productos?») no lo vería. Se comprobó el 27 de
 *  septiembre de 2026: con `::before`, la comprobación del índice del panel se puso roja con la
 *  etiqueta puesta y visible.
 */
export function Td({ children, className, etiqueta }: {
  children: ReactNode
  className?: string
  etiqueta?: string
}) {
  return (
    <td
      data-etiqueta={etiqueta}
      className={cx('border-b border-neutral-100 px-3 py-2 align-top dark:border-neutral-700', className)}
    >
      {etiqueta && (
        // El espacio va **dentro del texto**, no solo en el margen: `mr-1` separa al mirarlo,
        // pero `innerText` -- y un lector de pantalla -- leian «precio1,95 €». Medido con
        // `data/debug/cifras.py` el 27 de septiembre de 2026.
        <span className="mr-1 text-xs text-tinta-suave sm:hidden">{`${etiqueta} `}</span>
      )}
      {children}
    </td>
  )
}
