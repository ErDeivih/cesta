/** La navegacion. Abajo en el movil, arriba en el escritorio.
 *
 *  Abajo y no arriba porque la app se usa con una mano y el carro en la otra:
 *  el pulgar llega al borde inferior de la pantalla y no a la esquina de arriba.
 *  En el escritorio la barra de arriba no molesta a nadie.
 *
 *  **Seis destinos desde el 25 de septiembre de 2026, y el sexto lo pidio el dueno**:
 *  *"la web tiene mejor pinta, debes poner la opcion de lista de la compra y favoritas"*.
 *  Hasta ese dia **Favoritos existia y no se llegaba a el**: habia que escribir la
 *  direccion (`/favoritos`) o entrar desde la ficha de un producto. Una pantalla a la
 *  que no se llega no es una pantalla.
 *
 *  Y ahora son seis y no cinco, que era el limite que decia este comentario. Se puede
 *  porque el minimo que de verdad importa no es el numero de iconos sino **cuanto mide
 *  cada uno**: en un movil de 390 px, seis destinos son 65 px por cabeza, por encima
 *  del minimo de 44 px que se pulsa con el pulgar. Con siete serian 55 y ya empieza a
 *  apretar; el dia que haga falta el septimo, lo que toca no es apretarlos mas, es
 *  sacar de aqui lo que no se usa en el pasillo.
 *
 *  **Avisos** (23 de septiembre de 2026) no es un sitio donde estar: es **lo unico que
 *  la aplicacion hace por ti mientras no la miras** -- te busca ella a ti --, y es la
 *  respuesta a *"¿ha bajado algo de lo mio?"*, una de las cuatro preguntas con las que
 *  se abre esto. Ponerlo dentro de otra pantalla habria sido esconderlo en una esquina,
 *  que es justo lo que este encargo quita. Ademas el encargo lo pide literalmente: *"un
 *  punto en el icono"*, y un punto necesita un icono donde estar.
 */
import { NavLink, useLocation } from 'react-router-dom'

import { useAvisosSinVer, usePorCoger } from '../api/consultas'
import {
  IconoCasa,
  IconoCarro,
  IconoCodigoBarras,
  IconoCorazon,
  IconoPanel,
} from './iconos'
import { cx } from './ui'

const ITEMS = [
  // **Inicio** desde el 27 de septiembre de 2026: la pantalla que contesta las cuatro preguntas
  // de `docs/PRUEBA-15-SEGUNDOS.md` sin entrar en ninguna otra (lo que falta y dónde, el
  // buscador arriba, y lo que ha bajado de lo tuyo). Sustituye a «Buscar» en la barra porque el
  // buscador vive **dentro** de Inicio: siete destinos en 390 px son 55 px por cabeza y el
  // propio comentario de arriba ya decía que el séptimo no se mete apretando, sino sacando de
  // aquí lo que no se usa en el pasillo. Buscar sigue en `/buscar`, y se llega por su campo.
  { a: '/', texto: 'Inicio', Icono: IconoCasa, exacto: true },
  { a: '/cesta', texto: 'Lista', Icono: IconoCarro, exacto: false },
  { a: '/favoritos', texto: 'Favoritos', Icono: IconoCorazon, exacto: false },
  { a: '/escaner', texto: 'Escáner', Icono: IconoCodigoBarras, exacto: false },
  { a: '/avisos', texto: 'Avisos', Icono: IconoPanel, exacto: false },
  { a: '/panel', texto: 'Panel', Icono: IconoPanel, exacto: true },
] as const

function Item({ a, texto, Icono, exacto, compacto }: (typeof ITEMS)[number] & { compacto?: boolean }) {
  const { pathname, search } = useLocation()
  // El punto del icono: **cuantos avisos han saltado y nadie ha visto**. Cuenta lo que
  // ha saltado, no lo que hay: una alerta que existe y no se ha cumplido no es un
  // aviso, es una promesa. Y `vista_en` es de la persona, no de la pantalla que se
  // abre: abrirla en el autobus no puede dar por leido lo que no se ha leido.
  const sinVer = useAvisosSinVer()
  // **Y en la cesta, cuantas quedan por coger.** Es la pregunta 3 -- *"¿voy tachando
  // bien?"* -- contestada de un vistazo desde cualquier pantalla, sin abrir la lista. Lo
  // tenia la interfaz vieja (`app.js:507-509`) y era de las cosas que se pierden al
  // servir `dist`. Con cero no se pinta nada: un cero en la barra es ruido.
  const porCoger = usePorCoger()

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
          <span className="relative">
            {texto}
            {a === '/avisos' && sinVer > 0 && (
              <>
                <span
                  aria-hidden="true"
                  className="absolute -right-2 -top-1 h-2 w-2 rounded-full bg-red-600"
                />
                {/* Un punto no dice cuanto. El numero va para quien no ve el color:
                    el punto es la senal, y el numero es la misma senal en palabras. */}
                <span className="sr-only">{sinVer} sin ver</span>
              </>
            )}
            {a === '/cesta' && porCoger > 0 && (
              <>
                {/* Con el numero dentro, no un punto: **aqui el cuanto es la
                    pregunta**. «¿Voy tachando bien?» se contesta sabiendo cuantas
                    quedan, y un punto solo diria "queda algo". */}
                <span
                  aria-hidden="true"
                  className="absolute -right-3 -top-2 min-w-[1.05rem] rounded-full bg-sky-700 px-1 text-center text-[10px] font-semibold leading-4 text-white dark:bg-sky-400 dark:text-neutral-900"
                >
                  {porCoger}
                </span>
                <span className="sr-only">{porCoger} por coger</span>
              </>
            )}
          </span>
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
