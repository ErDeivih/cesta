/** La cabecera: de que fecha son los datos, siempre a la vista.
 *
 *  `fecha_datos` no es un adorno de pie de pagina. La regla del proyecto es que
 *  **un precio de mas de `dias_precio_valido` dias se ensena con su fecha pero
 *  no decide en que tienda comprar**, y eso solo se puede respetar si quien
 *  mira sabe de que dia es lo que esta viendo. Por eso va arriba, pegada, y no
 *  escondida en un "acerca de".
 */
import { Link, useLocation } from 'react-router-dom'

import { useEstado } from '../api/consultas'
import { fecha, hace } from '../api/formato'
import { NavEscritorio } from './Nav'
import { Etiqueta, cx } from './ui'

export function Cabecera() {
  const { data, isPending, error } = useEstado()
  const { pathname } = useLocation()
  const enPanel = pathname.startsWith('/panel')

  return (
    <header className="sticky top-0 z-30 border-b border-neutral-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:border-neutral-700 dark:bg-neutral-900/95 dark:supports-[backdrop-filter]:bg-neutral-900/80">
      <div className="mx-auto flex max-w-app flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2">
        <Link to="/" className="text-lg font-bold tracking-tight">
          Cesta
        </Link>

        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          {isPending && 'Mirando de qué día son los precios…'}
          {error !== null && !isPending && (
            <span className="text-amber-700 dark:text-amber-400">
              No sé de qué día son los precios: la API no contesta.
            </span>
          )}
          {data && (
            <>
              Datos del <strong className="font-semibold">{fecha(data.fecha_datos)}</strong>{' '}
              <span className="text-neutral-500 dark:text-neutral-500">
                ({hace(data.fecha_datos)})
              </span>
            </>
          )}
        </p>

        {/* Aviso de que cadena va con retraso. No se esconde: una cadena que no
            se ha rascado hoy no puede decidir una compra, y hay que saberlo
            antes de mirar los precios, no despues. */}
        {data && data.cadenas.some((c) => !c.al_dia) && (
          <Etiqueta tono="aviso" titulo="Esas cadenas tienen el precio de otro día">
            {data.cadenas.filter((c) => !c.al_dia).length} de {data.cadenas.length} cadenas con
            retraso
          </Etiqueta>
        )}

        <div className="ml-auto hidden lg:block">
          <NavEscritorio />
        </div>

        {!enPanel && (
          <details className="w-full text-xs text-neutral-600 lg:w-auto dark:text-neutral-400">
            <summary className="min-h-[24px] cursor-pointer">Estado de las cadenas</summary>
            <ul className="mt-1 grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
              {data?.cadenas.map((c) => (
                <li key={c.cadena} className="flex items-center gap-2">
                  <span className="font-medium">{c.cadena}</span>
                  <span className={cx(c.al_dia ? 'text-emerald-700 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400')}>
                    {c.al_dia ? 'al día' : `del ${fecha(c.ultimo_dia)}`}
                  </span>
                </li>
              ))}
              {isPending && <li>…</li>}
            </ul>
            {data && (
              <p className="mt-1">
                Un precio de más de {data.dias_precio_valido} días se enseña con su fecha, pero no
                decide dónde comprar.
              </p>
            )}
          </details>
        )}
      </div>
    </header>
  )
}
