/** El armazon de la suite: menu lateral, cajon de movil y cabecera de aplicacion.
 *
 *  **Que sustituye, y por que.** Hasta hoy la app tenia una cabecera arriba con destinos
 *  mezclados y una barra abajo, y `SUPERAPP-01` manda lo contrario: **tres aplicaciones
 *  separadas**, cada una con su navegacion, y un menu lateral que se ve entero. La razon no es
 *  estetica: con una sola lista de destinos, "Recetas" y "Favoritos" parecen lo mismo, y no lo son
 *  -- una es un recetario y la otra una lista de la compra.
 *
 *  **Decisiones que se notan al usarlo, y por que son asi:**
 *
 *  - **Escritorio: 248 px fijos desde 1024.** Las tres aplicaciones siempre visibles; las
 *    subsecciones, solo las de la activa. Asi se ve donde estas y a donde puedes ir sin abrir nada.
 *  - **Movil: cajon de 288 px con el foco atrapado.** Un cajon que se abre y deja el foco detras
 *    es una trampa para quien navega con teclado: se pulsa Tab y se acaba en la pagina de abajo,
 *    con el cajon abierto tapando lo que se esta leyendo. Aqui el foco entra, da vueltas dentro y
 *    vuelve al boton al cerrar con Escape.
 *  - **El fondo se queda inerte** (`inert`) mientras el cajon esta abierto: ni se tabula ni se
 *    pulsa lo de detras, que es lo que hace un cajon modal de verdad.
 *  - **El boton dice donde estas**, no solo "Menu": con el cajon cerrado se lee el nombre de la
 *    aplicacion y el titulo de la pantalla, que es la mitad de la orientacion.
 *  - **Nada por debajo de 13 px en metadatos y 14 en tablas.** La referencia de Stitch puso 11 px
 *    en unas etiquetas y se rechazo: se lee mal en un movil al sol, que es donde se usa esto.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode, RefObject } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

import { usePorCogerDeCasa } from '../api/consultas'
import {
  IconoCalendario,
  IconoCarro,
  IconoCorazon,
  IconoGrafica,
  IconoLibro,
  IconoLupa,
  IconoPersona,
  IconoPlato,
} from './iconos'
import { cx } from './ui'

import type { ComponentType, SVGProps } from 'react'

export type ClaveApp = 'compra' | 'recetas' | 'calorias'

/* *** Y cada destino lleva su icono, *y cada aplicacion el suyo. *** *
 *
 * *Un icono **no es adorno**: *es lo que hace reconocible un sitio **sin
 * leerlo**, *y en un lateral de siete destinos eso es la diferencia entre
 * orientarse y leer una lista.* *
 *
 * *Y **solo tienen que distinguirse dentro de su aplicacion**, *porque las
 * subsecciones de las otras **no se ven nunca** *-- *lo dice el campo de
 * abajo --.* *Por eso el libro vale para «Mi recetario» **y** para «Mi
 * diario»: *los dos **son** libros, *y **jamas se ven juntos.*** *
 */
type Subseccion = {
  a: string
  texto: string
  Icono: ComponentType<SVGProps<SVGSVGElement>>
}

type Aplicacion = {
  clave: ClaveApp
  nombre: string
  /** *El icono de la aplicacion, *el que la hace reconocible en el selector
   *  sin leer su nombre.* */
  Icono: ComponentType<SVGProps<SVGSVGElement>>
  raiz: string
  /** Las subsecciones de esta aplicacion. Nunca las de otra. */
  subsecciones: Subseccion[]
}

/** Las tres aplicaciones y sus subsecciones, tal y como las fija `SUPERAPP-01` seccion 2. */
export const APLICACIONES: Aplicacion[] = [
  {
    clave: 'compra',
    nombre: 'Compra',
    Icono: IconoCarro,
    raiz: '/compra',
    subsecciones: [
      { a: '/compra', texto: 'Buscar', Icono: IconoLupa },
      { a: '/compra/listas', texto: 'Listas', Icono: IconoCarro },
      { a: '/compra/favoritos', texto: 'Favoritos', Icono: IconoCorazon },
      { a: '/compra/analisis', texto: 'Gasto y ahorro', Icono: IconoGrafica },
    ],
  },
  {
    clave: 'recetas',
    nombre: 'Recetas',
    Icono: IconoLibro,
    raiz: '/recetas',
    subsecciones: [
      { a: '/recetas', texto: 'Mi recetario', Icono: IconoLibro },
      { a: '/recetas/plan', texto: 'Plan semanal', Icono: IconoCalendario },
    ],
  },
  {
    clave: 'calorias',
    nombre: 'Calorias',
    Icono: IconoPlato,
    raiz: '/calorias',
    subsecciones: [
      { a: '/calorias', texto: 'Mi diario', Icono: IconoLibro },
      { a: '/calorias/alimentos', texto: 'Mis alimentos', Icono: IconoPlato },
      { a: '/calorias/tendencias', texto: 'Tendencias', Icono: IconoGrafica },
    ],
  },
]

/** La aplicacion a la que pertenece una ruta, o null si es el lanzador o una pantalla suelta. */
export function aplicacionDe(ruta: string): Aplicacion | null {
  return APLICACIONES.find((a) => ruta === a.raiz || ruta.startsWith(`${a.raiz}/`)) ?? null
}

/** El titulo de la pantalla actual, con el nombre largo de cada subseccion. */
export function tituloDeSeccion(ruta: string): string {
  const app = aplicacionDe(ruta)
  if (!app) return 'Cesta'
  const exacta = app.subsecciones.find((s) => s.a === ruta)
  if (exacta) return exacta.texto
  if (ruta.includes('/productos/')) return 'Producto'
  if (ruta.includes('/comparar/')) return 'Comparar'
  if (ruta.includes('/listas/')) return 'Lista'
  if (app.clave === 'recetas' && ruta !== '/recetas/plan') return 'Receta'
  if (app.clave === 'calorias' && ruta !== '/calorias/alimentos'
      && ruta !== '/calorias/tendencias') return 'Diario'
  return app.nombre
}

/** **El contador de la entrada de Listas.** Va aqui, en el menu, y no en `Nav.tsx`.
 *
 *  **Medido el 11 de octubre de 2026, leyendo los consumidores reales**: todas las rutas montan
 *  `LayoutSuite` (`App.tsx`), y su menu es este `Menu` -- **el mismo para el lateral de escritorio
 *  (`SuiteSidebar`) y el cajon del movil (`CajonLateral`)**. El contador vivia en `Nav.tsx`, que
 *  **ninguna ruta monta**, y alli ademas exigia un destino terminado en `/listas` mientras su
 *  enlace apuntaba a `/cesta`: aunque se hubiera montado, no habria contado nada. Ponerlo aqui
 *  arregla los dos sitios de una vez.
 *
 *  **Cuenta lo pendiente de la lista de casa, y solo eso.** Carga, error, ?no hay lista de casa? y
 *  cero real se dicen cada uno a su manera: un cero que tambien significa ?no lo se? no informa.
 *  El texto para quien no ve el color va en `sr-only`, y **nombra la lista**, que es la mitad del
 *  dato: un numero sin decir de que lista es no se puede comprobar.
 */
function ContadorDeLaLista() {
  const estado = usePorCogerDeCasa()
  if (estado.tipo === 'oculto') return null
  if (estado.tipo === 'cargando') {
    return <span className="text-[13px] text-secundaria" aria-hidden="true">&middot;&middot;&middot;</span>
  }
  if (estado.tipo === 'error') {
    return (
      <>
        <span className="text-[13px] text-secundaria" aria-hidden="true">?</span>
        <span className="sr-only">No he podido contar lo que queda por coger</span>
      </>
    )
  }
  if (estado.tipo === 'sin-lista') {
    return (
      <>
        <span className="text-[13px] text-secundaria" aria-hidden="true">Sin lista de casa</span>
        <span className="sr-only">No hay lista de casa, asi que no hay nada que contar</span>
      </>
    )
  }
  return (
    <>
      {estado.pendientes > 0 && (
        <span
          aria-hidden="true"
          className="min-w-[1.4rem] rounded-full bg-bosque px-1 text-center text-[13px]
                     font-semibold tabular-nums text-papel"
        >
          {estado.pendientes}
        </span>
      )}
      <span className="sr-only">
        {estado.pendientes === 0
          ? `En la lista de casa (${estado.lista}) no queda nada por coger`
          : `${estado.pendientes} por coger en la lista de casa (${estado.lista})`}
      </span>
    </>
  )
}

function EnlaceLateral({ a, texto, Icono, onNavegar, chapa }: Subseccion & {
  onNavegar?: () => void
  chapa?: ReactNode
}) {
  return (
    <NavLink
      to={a}
      end={a.split('/').length === 2}
      onClick={onNavegar}
      className={({ isActive }) =>
        cx(
          // *** El icono, y el hueco con el texto. *** *
          //
          // *`gap-2.5` y no un `gap` a ojo: *el icono **no pega** con la palabra
          // ni se despega, *y el mismo hueco vale en los once destinos.* *
          //
          // *Y el radio es **`campo`**, *que es el de **lo que se pulsa**: *antes
          // era el `rounded-md` de fabrica, *el mismo que el de un boton ... *y por
          // eso ninguno de los dos decia nada.* *
          'flex min-h-[44px] items-center gap-2.5 rounded-campo px-3 py-2 text-cuerpo',
          isActive ? 'font-semibold text-terracota' : 'text-tinta-fuerte hover:bg-marfil',
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icono width={18} height={18} className="shrink-0" />
          {/* *El subrayado va en la **palabra**, *no en toda la fila: *asi marca el
              destino **sin** subrayar tambien el icono y el contador.* */}
          <span
            className={cx(
              isActive && 'underline decoration-terracota decoration-2 underline-offset-4',
            )}
          >
            {texto}
          </span>
          {chapa && <span className="ml-auto flex items-center">{chapa}</span>}
        </>
      )}
    </NavLink>
  )
}

/** El contenido del menu, que usan el lateral de escritorio y el cajon del movil. */
function Menu({ app, onNavegar, idBotonCerrar }: {
  app: Aplicacion | null
  onNavegar?: () => void
  idBotonCerrar?: string
}) {
  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <nav aria-label="Aplicaciones" className="flex flex-col gap-1">
        {APLICACIONES.map((otra) => (
          <NavLink
            key={otra.clave}
            to={otra.raiz}
            onClick={onNavegar}
            aria-current={app?.clave === otra.clave ? 'page' : undefined}
            className={cx(
              // *** El nombre de la aplicacion lleva SU icono. *** *
              //
              // *Es donde mas hace falta: *las tres se ven **a la vez**, *y el
              // icono las distingue **de un vistazo** sin leer tres palabras.* *
              //
              // *Y el tamano es **`entrada`** (17 px) y no un `[19px]` a medida:
              // *la escala tiene seis pasos **y este es uno**, *y un numero suelto
              // aqui es como empezaron las 996 clases.* *
              'flex min-h-[44px] items-center gap-2.5 rounded-campo px-3 font-serif text-entrada',
              app?.clave === otra.clave
                ? 'bg-bosque font-semibold text-papel'
                : 'text-tinta-fuerte hover:bg-marfil',
            )}
          >
            <otra.Icono width={20} height={20} className="shrink-0" />
            {otra.nombre}
          </NavLink>
        ))}
      </nav>
      {app && (
        <nav aria-label={`Secciones de ${app.nombre}`} className="flex flex-col gap-1">
          <p className="px-3 text-[13px] uppercase tracking-wide text-secundaria">
            {app.nombre}
          </p>
          {app.subsecciones.map((s) => (
            <EnlaceLateral
              key={s.a}
              {...s}
              onNavegar={onNavegar}
              chapa={s.a === '/compra/listas' ? <ContadorDeLaLista /> : undefined}
            />
          ))}
        </nav>
      )}
      <nav aria-label="Cuenta y ayuda" className="mt-auto flex flex-col gap-1">
        <EnlaceLateral a="/ajustes" texto="Cuenta y preferencias" Icono={IconoPersona}
          onNavegar={onNavegar} />
        <EnlaceLateral a="/aprender" texto="Aprender" Icono={IconoLibro}
          onNavegar={onNavegar} />
        {idBotonCerrar && (
          <button
            type="button"
            id={idBotonCerrar}
            onClick={onNavegar}
            className="mt-2 min-h-[44px] rounded-campo px-3 text-left text-[15px] text-secundaria hover:bg-marfil"
          >
            Cerrar menu
          </button>
        )}
      </nav>
    </div>
  )
}

/** El lateral de escritorio. Oculto por debajo de 1024 px, donde manda el cajon. */
export function SuiteSidebar({ app }: { app: Aplicacion | null }) {
  return (
    <aside
      aria-label="Menu de la suite"
      className="sticky top-0 hidden h-screen w-[248px] shrink-0 border-r border-borde bg-papel lg:block"
    >
      <div className="border-b border-borde px-4 py-5">
        <NavLink to="/" className="font-serif text-[22px] font-semibold text-tinta-fuerte">
          Cesta
        </NavLink>
      </div>
      <Menu app={app} />
    </aside>
  )
}

/** El cajon del movil, con foco atrapado, Escape para cerrar y el fondo inerte. */
export function CajonLateral({ app, abierto, onCerrar }: {
  app: Aplicacion | null
  abierto: boolean
  onCerrar: () => void
}) {
  const caja = useRef<HTMLDivElement>(null)

  // El foco no puede escaparse del cajon mientras esta abierto: se da la vuelta dentro.
  const atrapar = useCallback((evento: KeyboardEvent) => {
    if (evento.key !== 'Tab' || !caja.current) return
    const enfocables = caja.current.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    )
    if (enfocables.length === 0) return
    const primero = enfocables[0]
    const ultimo = enfocables[enfocables.length - 1]
    if (evento.shiftKey && document.activeElement === primero) {
      evento.preventDefault()
      ultimo.focus()
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault()
      primero.focus()
    }
  }, [])

  useEffect(() => {
    if (!abierto) return
    const primero = caja.current?.querySelector<HTMLElement>('a[href], button:not([disabled])')
    primero?.focus()
    // Escape cierra: es lo que espera cualquiera que haya abierto un cajon, y con teclado es la
    // unica salida razonable sin recorrer el menu entero hasta "Cerrar menu".
    const escapar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') {
        evento.preventDefault()
        onCerrar()
      }
    }
    document.addEventListener('keydown', atrapar)
    document.addEventListener('keydown', escapar)
    return () => {
      document.removeEventListener('keydown', atrapar)
      document.removeEventListener('keydown', escapar)
    }
  }, [abierto, atrapar, onCerrar])

  if (!abierto) return null
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* El fondo cierra al pulsarlo, y no lleva foco: es decorativo. */}
      <div
            className="entra-velo absolute inset-0 bg-tinta-translucida/40"
            onClick={onCerrar}
            aria-hidden="true" />
      <div
        ref={caja}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de la suite"
        className="entra-cajon absolute inset-y-0 left-0 w-[288px] max-w-[85vw] border-r border-borde bg-papel shadow-lg"
      >
        <Menu app={app} onNavegar={onCerrar} idBotonCerrar="cerrar-menu" />
      </div>
    </div>
  )
}

/** La cabecera de la aplicacion: su nombre, el titulo actual y el boton de menu en el movil. */
export function ModuleHeader({ app, abierto, onAbrir, refBoton }: {
  app: Aplicacion | null
  abierto: boolean
  onAbrir: () => void
  refBoton?: RefObject<HTMLButtonElement | null>
}) {
  const { pathname } = useLocation()
  const titulo = tituloDeSeccion(pathname)
  return (
    <header className="sticky top-0 z-30 border-b border-borde bg-papel backdrop-blur">
      <div className="flex items-center gap-3 px-4 py-3 lg:px-8">
        <button
          type="button"
          ref={refBoton}
          onClick={onAbrir}
          aria-expanded={abierto}
          aria-controls="menu-suite"
          className="flex min-h-[44px] min-w-[44px] items-center gap-2 rounded-campo border border-borde-fuerte px-3 text-[15px] text-tinta-fuerte lg:hidden"
        >
          <span aria-hidden="true">&#9776;</span>
          {/* El boton dice donde estas, no solo "Menu". */}
          <span className="font-medium">{app?.nombre ?? 'Cesta'}</span>
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] uppercase tracking-wide text-secundaria">
            {app?.nombre ?? 'Cesta'}
          </p>
          <h1 className="truncate font-serif text-[28px] leading-[34px] font-semibold text-tinta-fuerte lg:text-[32px] lg:leading-[38px]">
            {titulo}
          </h1>
        </div>
      </div>
    </header>
  )
}

/** El armazon completo de una aplicacion: lateral o cajon, cabecera y contenido. */
export function LayoutSuite({ app, children }: { app: ClaveApp | null; children: ReactNode }) {
  // *La ruta, que hace falta para la `key` de la entrada de pantalla.* *
  // *Se saca aqui y no dentro del `main` para que se lea una sola vez.* *
  const { pathname: ruta } = useLocation()
  const [abierto, setAbierto] = useState(false)
  const botonMenu = useRef<HTMLButtonElement>(null)
  const { pathname } = useLocation()
  const aplicacion = APLICACIONES.find((a) => a.clave === app) ?? null

  const cerrar = useCallback(() => setAbierto(false), [])

  // **El foco vuelve al boton de menu, pero cuando el cajon ya se ha cerrado.** Pedirlo antes no
  // sirve: mientras `abierto` es `true` la cabecera esta inerte, y un elemento dentro de un subarbol
  // `inert` no se puede enfocar -- el navegador ignora la llamada sin avisar. Y solo se devuelve si
  // el foco se ha quedado sin sitio: si se cerro pulsando un enlace, el foco se va con el.
  useEffect(() => {
    if (abierto) return
    if (document.activeElement === document.body || document.activeElement === null) {
      botonMenu.current?.focus()
    }
  }, [abierto])

  // Al cambiar de pantalla el cajon se cierra: dejarlo abierto tapando lo que se acaba de pedir
  // es de las cosas que hacen pensar que la app no ha hecho nada.
  useEffect(() => setAbierto(false), [pathname])

  return (
    <div className="flex min-h-screen bg-marfil">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[60] focus:rounded-campo focus:bg-bosque focus:px-3 focus:py-2 focus:text-papel"
      >
        Saltar al contenido
      </a>
      <SuiteSidebar app={aplicacion} />
      <div className="flex min-w-0 flex-1 flex-col" inert={abierto || undefined}>
        <ModuleHeader app={aplicacion} abierto={abierto} onAbrir={() => setAbierto(true)}
          refBoton={botonMenu} />
                {/* *** Y la `key` es LA RUTA, *que es lo que hace que se repita. *** *
            *
            * *React **no vuelve a montar** un elemento si su posicion no cambia, *asi
            * que sin `key` la animacion correria **una sola vez** y al navegar no se
            * veria.* *Con la ruta como `key`, **cada pantalla es un montaje nuevo** y
            * la animacion corre **cada vez**.* *
            *
            * *Y se usa **`pathname` y no la direccion entera**: *cambiar la busqueda
            * *(-- `?q=leche` --)* **no es cambiar de pantalla**, *y ahi **no tiene que
            * parpadear** *-- *que es justo lo que molestaria buscando.* *
            */}
        <main
          key={ruta}
          id="contenido"
          className="entra-pantalla mx-auto w-full max-w-app flex-1 px-4 py-5 lg:px-8"
        >
          {children}
        </main>
      </div>
      {abierto && (
        <div id="menu-suite">
          <CajonLateral app={aplicacion} abierto={abierto} onCerrar={cerrar} />
        </div>
      )}
    </div>
  )
}