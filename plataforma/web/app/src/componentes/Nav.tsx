/** La navegacion. Abajo en el movil, arriba en el escritorio.
 *
 *  Abajo y no arriba porque la app se usa con una mano y el carro en la otra:
 *  el pulgar llega al borde inferior de la pantalla y no a la esquina de arriba.
 *  En el escritorio la barra de arriba no molesta a nadie.
 *
 *  **Cuatro destinos, y son los cuatro de estar un rato en la tienda**: buscar,
 *  la cesta, el escaner y el panel. Antes estaba el panel de matching en lugar de
 *  la cesta; se ha cambiado porque la lista de la compra es a lo que se va, y el
 *  matching es una pantalla de auditoria que se mira en casa. Sigue accesible
 *  desde el panel (`/panel/matching`), que es donde se busca.
 *
 *  Una barra de ocho iconos no se lee, se busca a tientas.
 */
import { NavLink, useLocation } from 'react-router-dom'

import { IconoCodigoBarras, IconoLupa, IconoPanel, IconoGrafica } from './iconos'
import { cx } from './ui'

const ITEMS = [
  { a: '/', texto: 'Buscar', Icono: IconoLupa, exacto: true },
  { a: '/cesta', texto: 'Cesta', Icono: IconoGrafica, exacto: false },
  { a: '/escaner', texto: 'Escáner', Icono: IconoCodigoBarras, exacto: false },
  { a: '/panel', texto: 'Panel', Icono: IconoPanel, exacto: true },
] as const

function Item({ a, texto, Icono, exacto, compacto }: (typeof ITEMS)[number] & { compacto?: boolean }) {
  const { pathname, search } = useLocation()

  /* Pulsar "Buscar" **estando ya en el buscador** no puede borrar la busqueda.
   *
   * El texto y los filtros viven en la direccion (`?q=leche&cadenas=dia,...`),
   * asi que un enlace a `/` a secas los tira: para volver a ver lo mismo hay que
   * escribirlo otra vez, de pie en el pasillo. La interfaz vieja no lo hacia
   * porque no volvia a pintar la pantalla; aqui hay que decirlo a proposito.
   *
   * Desde otra pantalla si se entra limpio, y eso tambien es a proposito: lo que
   * se va a hacer es empezar a buscar. Y la flecha de atras sigue devolviendo la
   * busqueda anterior, que es como se busca "lo de antes" sin pensarlo. */
  const destino = a === '/' && pathname === '/' ? { pathname: '/', search } : a

  return (
    <NavLink
      to={destino}
      end={exacto}
      className={({ isActive }) =>
        cx(
          'flex flex-1 flex-col items-center justify-center gap-0.5 rounded-lg px-2 py-1 text-xs font-medium',
          compacto ? 'min-h-[56px]' : 'min-h-[44px]',
          isActive
            ? 'text-sky-800 dark:text-sky-300'
            : 'text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100',
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icono width={compacto ? 22 : 18} height={compacto ? 22 : 18} />
          <span>{texto}</span>
          {/* El estado activo no se marca solo con color: lleva un subrayado,
              que se ve tambien en una pantalla con el brillo bajo y al sol. */}
          <span
            aria-hidden="true"
            className={cx(
              'mt-0.5 h-0.5 w-8 rounded-full',
              isActive ? 'bg-sky-700 dark:bg-sky-400' : 'bg-transparent',
            )}
          />
        </>
      )}
    </NavLink>
  )
}

export function NavAbajo() {
  return (
    <nav
      aria-label="Secciones"
      // `pb-[env(safe-area-inset-bottom)]` para el iPhone, que tiene una raya
      // abajo que se come el ultimo boton.
      className="fixed inset-x-0 bottom-0 z-40 border-t border-neutral-200 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden dark:border-neutral-700 dark:bg-neutral-900"
    >
      <div className="mx-auto flex max-w-app items-stretch gap-1 px-2">
        {ITEMS.map((i) => (
          <Item key={i.a} {...i} compacto />
        ))}
      </div>
    </nav>
  )
}

export function NavEscritorio() {
  return (
    <nav aria-label="Secciones" className="hidden lg:block">
      <ul className="flex items-center gap-1">
        {ITEMS.map((i) => (
          <li key={i.a} className="flex">
            <Item {...i} />
          </li>
        ))}
      </ul>
    </nav>
  )
}
