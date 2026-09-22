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

import { textoDeError } from '../api/cliente'

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
        // 44 px: el minimo para pulsar con el pulgar sin fallar.
        compacto ? 'min-h-[44px] px-3 py-2' : 'min-h-[44px] px-4 py-2',
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
        className="min-h-[44px] rounded-lg border border-neutral-300 bg-white px-3 py-2 dark:border-neutral-600 dark:bg-neutral-800"
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
        className="min-h-[44px] rounded-lg border border-neutral-300 bg-white px-3 py-2 dark:border-neutral-600 dark:bg-neutral-800"
      />
    </div>
  )
}

// ------------------------------------------------------------ estados raros ---

export function Cargando({ que = 'los datos' }: { que?: string }) {
  return (
    <p role="status" className="py-6 text-center text-sm text-neutral-600 dark:text-neutral-400">
      Cargando {que}…
    </p>
  )
}

export function Fallo({ error, reintentar }: { error: unknown; reintentar?: () => void }) {
  // El texto lo pone `textoDeError`, que ya distingue "sin conexion" de "el
  // servidor ha contestado 500". Aqui no se inventa un mensaje nuevo.
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

/** Envoltorio de tabla con scroll horizontal **controlado**.
 *
 *  Una tabla de precios con siete columnas no cabe en un movil, y las tres
 *  salidas malas son: aplastarla hasta que no se lee, esconder columnas (y que
 *  el dato que falta sea justo el que se buscaba) o dejarla salirse de la
 *  pantalla. La buena es scroll horizontal con la primera columna pegada y un
 *  aviso de que se puede deslizar.
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
    <div>
      <p className="mb-1 text-xs text-neutral-500 sm:hidden dark:text-neutral-400">
        Desliza la tabla para ver todas las columnas →
      </p>
      <div
        className="tabla-scroll"
        role="region"
        aria-label={etiqueta}
        tabIndex={0}
      >
        <div style={{ minWidth: minAncho }}>{children}</div>
      </div>
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
          className="inline-flex min-h-[32px] items-center gap-1 hover:text-neutral-900 dark:hover:text-white"
        >
          {contenido}
        </button>
      ) : (
        contenido
      )}
    </th>
  )
}

export function Td({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <td className={cx('border-b border-neutral-100 px-3 py-2 align-top dark:border-neutral-700', className)}>
      {children}
    </td>
  )
}
