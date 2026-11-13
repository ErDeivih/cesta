/** *** LA VENTANA DE UNA LISTA LARGA. *** *
 *
 *  *Con sesenta lineas en el movil, pintar las sesenta es lo que paga el primer pintado entero.*
 *  *Esta pieza pinta solo la ventana visible mas un margen a cada lado y reserva la altura de las
 *  que no estan, para que la barra de desplazamiento diga la verdad.*
 *
 *  **La ventana se calcula aqui, con `alto` y `alturaFila` por prop.** *No se usa
 *  `createVirtualizer` de `@ui-sdk/core` porque ese lee `clientHeight` del contenedor y esta
 *  pieza recibe la ventana declarada (tambien en jsdom, donde no hay maquetacion). Es la unica
 *  de las cuatro piezas que no delega en `@ui-sdk`; el motivo esta escrito donde se decide.*
 *
 *  Lo que si se implementa es el contrato accesible completo:
 *   - `role="group"` con nombre, enfocable, y las flechas/Inicio/Fin/AvPag/AntPag dentro;
 *   - `aria-posinset`/`aria-setsize` en cada fila: el lector sabe que hay 60 aunque solo vea 12;
 *   - un `aria-live` que dice «linea N de M» al moverse y al desplazarse.
 */
import { cloneElement, useRef, useState, type ReactElement, type ReactNode } from 'react'

import { cx } from '../ui'

export function ListaVirtualizada<T>({
  filas,
  alturaFila,
  alto,
  overscan = 3,
  etiqueta,
  render,
  className,
}: {
  /** Las filas completas: solo se pinta una ventana, pero la altura reservada es la de todas. */
  filas: readonly T[]
  /** Altura fija de cada fila, en px. Se usa para la ventana y para reservar el hueco. */
  alturaFila: number
  /** Alto visible del contenedor con scroll, en px. */
  alto: number
  /** Filas extra a cada lado de la ventana, para que un desplazamiento rapido no deje huecos. */
  overscan?: number
  /** Nombre de la lista para el lector de pantalla. */
  etiqueta: string
  /** La fila, tal cual. Se le anaden `aria-posinset` y `aria-setsize`. */
  render: (fila: T, indice: number) => ReactNode
  className?: string
}) {
  const caja = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const [anuncio, setAnuncio] = useState('')

  const total = filas.length
  /** Las que caben enteras en la ventana. Con 300 px y filas de 50 son 6. */
  const visibles = Math.max(1, Math.ceil(alto / alturaFila))
  /** El tamano de la ventana: las visibles y el overscan de los dos lados. */
  const tamano = Math.min(total, visibles + 2 * overscan)
  const filaArriba = Math.floor(scrollTop / alturaFila)
  const inicio = Math.max(0, Math.min(filaArriba - overscan, Math.max(0, total - tamano)))
  const fin = Math.min(total, inicio + tamano)
  const maximo = Math.max(0, total * alturaFila - alto)

  /** El anuncio que oye quien no ve la barra: donde empieza la ventana. */
  function anuncia(fila: number) {
    if (total === 0) {
      setAnuncio('')
      return
    }
    setAnuncio(`línea ${Math.min(total, Math.max(1, fila + 1))} de ${total}`)
  }

  /** Mueve el scroll a `destino` y anuncia la fila `fila` (la primera visible). */
  function desplaza(destino: number, fila: number) {
    const el = caja.current
    const siguiente = Math.max(0, Math.min(maximo, destino))
    if (el) el.scrollTop = siguiente
    setScrollTop(siguiente)
    anuncia(fila)
  }

  function alTeclear(evento: React.KeyboardEvent<HTMLDivElement>) {
    const abajo = Math.floor(scrollTop / alturaFila)
    let destino: number | null = null
    let fila = abajo
    if (evento.key === 'ArrowDown') {
      destino = scrollTop + alturaFila
      fila = abajo + 1
    } else if (evento.key === 'ArrowUp') {
      destino = scrollTop - alturaFila
      fila = abajo - 1
    } else if (evento.key === 'PageDown') {
      destino = scrollTop + alto
      fila = Math.floor((scrollTop + alto) / alturaFila)
    } else if (evento.key === 'PageUp') {
      destino = scrollTop - alto
      fila = Math.floor(Math.max(0, scrollTop - alto) / alturaFila)
    } else if (evento.key === 'Home') {
      desplaza(0, 0)
      evento.preventDefault()
      return
    } else if (evento.key === 'End') {
      desplaza(maximo, total - 1)
      evento.preventDefault()
      return
    }
    if (destino === null) return
    evento.preventDefault()
    desplaza(destino, fila)
  }

  return (
    <div
      ref={caja}
      role="group"
      aria-label={etiqueta}
      tabIndex={0}
      onScroll={() => {
        const el = caja.current
        if (!el) return
        setScrollTop(el.scrollTop)
        anuncia(Math.floor(el.scrollTop / alturaFila))
      }}
      onKeyDown={alTeclear}
      className={cx(
        'overflow-y-auto rounded-campo outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bosque',
        className,
      )}
      style={{ height: alto }}
    >
      {/* *El hueco de las que no estan, con la altura de todas: sin el, la barra diria que la
          lista acaba donde acaba la ventana y no se podria deslizar hasta el final.* */}
      <div style={{ height: total * alturaFila, position: 'relative' }}>
        <ul
          style={{
            position: 'absolute',
            top: inicio * alturaFila,
            left: 0,
            right: 0,
            margin: 0,
            padding: 0,
            listStyle: 'none',
          }}
        >
          {filas.slice(inicio, fin).map((fila, i) => {
            const indice = inicio + i
            const pintada = render(fila, indice)
            return (
              <Fragmento key={indice}>
                {marcaPosicion(pintada, indice, total)}
              </Fragmento>
            )
          })}
        </ul>
      </div>
      <span className="sr-only" aria-live="polite">
        {anuncio}
      </span>
    </div>
  )
}

/** *El lector de pantalla tiene que oir «12 de 60» aunque en el DOM solo haya 12.* */
function marcaPosicion(pintada: ReactNode, indice: number, total: number): ReactNode {
  if (!pintada || typeof pintada !== 'object' || !('type' in pintada)) return pintada
  const elemento = pintada as ReactElement<Record<string, unknown>>
  return cloneElement(elemento, {
    'aria-posinset': indice + 1,
    'aria-setsize': total,
  })
}

/** *Un `key` por indice: la ventana se recorre en orden y las filas no se reordenan.* */
function Fragmento({ children }: { children: ReactNode }) {
  return <>{children}</>
}
