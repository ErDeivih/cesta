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

import { cx } from './ui'

export type ClaveApp = 'compra' | 'recetas' | 'calorias'

type Subseccion = { a: string; texto: string }

type Aplicacion = {
  clave: ClaveApp
  nombre: string
  raiz: string
  /** Las subsecciones de esta aplicacion. Nunca las de otra. */
  subsecciones: Subseccion[]
}

/** Las tres aplicaciones y sus subsecciones, tal y como las fija `SUPERAPP-01` seccion 2. */
export const APLICACIONES: Aplicacion[] = [
  {
    clave: 'compra',
    nombre: 'Compra',
    raiz: '/compra',
    subsecciones: [
      { a: '/compra', texto: 'Buscar' },
      { a: '/compra/listas', texto: 'Listas' },
      { a: '/compra/favoritos', texto: 'Favoritos' },
      { a: '/compra/analisis', texto: 'Gasto y ahorro' },
    ],
  },
  {
    clave: 'recetas',
    nombre: 'Recetas',
    raiz: '/recetas',
    subsecciones: [
      { a: '/recetas', texto: 'Mi recetario' },
      { a: '/recetas/plan', texto: 'Plan semanal' },
    ],
  },
  {
    clave: 'calorias',
    nombre: 'Calorias',
    raiz: '/calorias',
    subsecciones: [
      { a: '/calorias', texto: 'Mi diario' },
      { a: '/calorias/alimentos', texto: 'Mis alimentos' },
      { a: '/calorias/tendencias', texto: 'Tendencias' },
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

function EnlaceLateral({ a, texto, onNavegar }: Subseccion & { onNavegar?: () => void }) {
  return (
    <NavLink
      to={a}
      end={a.split('/').length === 2}
      onClick={onNavegar}
      className={({ isActive }) =>
        cx(
          'block rounded-md px-3 py-2 text-[15px] leading-6',
          isActive
            ? 'font-semibold text-terracota underline decoration-terracota decoration-2 underline-offset-4'
            : 'text-tinta-fuerte hover:bg-marfil',
        )
      }
    >
      {texto}
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
              'flex min-h-[44px] items-center rounded-md px-3 font-serif text-[19px] leading-7',
              app?.clave === otra.clave
                ? 'bg-bosque font-semibold text-papel'
                : 'text-tinta-fuerte hover:bg-marfil',
            )}
          >
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
            <EnlaceLateral key={s.a} {...s} onNavegar={onNavegar} />
          ))}
        </nav>
      )}
      <nav aria-label="Cuenta y ayuda" className="mt-auto flex flex-col gap-1">
        <EnlaceLateral a="/ajustes" texto="Cuenta y preferencias" onNavegar={onNavegar} />
        <EnlaceLateral a="/aprender" texto="Aprender" onNavegar={onNavegar} />
        {idBotonCerrar && (
          <button
            type="button"
            id={idBotonCerrar}
            onClick={onNavegar}
            className="mt-2 min-h-[44px] rounded-md px-3 text-left text-[15px] text-secundaria hover:bg-marfil"
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
      <div className="absolute inset-0 bg-neutral-900/40" onClick={onCerrar} aria-hidden="true" />
      <div
        ref={caja}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de la suite"
        className="absolute inset-y-0 left-0 w-[288px] max-w-[85vw] border-r border-borde bg-papel shadow-lg"
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
    <header className="sticky top-0 z-30 border-b border-borde bg-white/95 backdrop-blur">
      <div className="flex items-center gap-3 px-4 py-3 lg:px-8">
        <button
          type="button"
          ref={refBoton}
          onClick={onAbrir}
          aria-expanded={abierto}
          aria-controls="menu-suite"
          className="flex min-h-[44px] min-w-[44px] items-center gap-2 rounded-md border border-borde-fuerte px-3 text-[15px] text-tinta-fuerte lg:hidden"
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
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[60] focus:rounded-md focus:bg-bosque focus:px-3 focus:py-2 focus:text-papel"
      >
        Saltar al contenido
      </a>
      <SuiteSidebar app={aplicacion} />
      <div className="flex min-w-0 flex-1 flex-col" inert={abierto || undefined}>
        <ModuleHeader app={aplicacion} abierto={abierto} onAbrir={() => setAbierto(true)}
          refBoton={botonMenu} />
        <main id="contenido" className="mx-auto w-full max-w-app flex-1 px-4 py-5 lg:px-8">
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
