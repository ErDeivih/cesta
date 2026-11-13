/** *** LO QUE SE ABRE ENCIMA DE LA PANTALLA. *** *
 *
 *  *Una hoja sin trampa de foco deja al teclado detras de la capa, y al cerrar no vuelve a quien
 *  la abrio: la persona se queda al principio de la pagina sin saber por que.*
 *
 *  Pieza de comportamiento: **`Dialog` de `@ui-sdk/react/dialog`** (Apache-2.0). El dialogo de
 *  `@ui-sdk` resuelve lo que es dificil: `role="dialog"` y `aria-modal`, Escape y pulsacion fuera
 *  que cierran, y el apilado de capas. Aqui se le añaden las dos piezas que dependen de **esta**
 *  pantalla, porque el dialogo se abre desde un boton suyo y no desde un `DialogTrigger`:
 *  **el foco entra al abrir y vuelve a quien lo abrio al cerrar**, y **Tab no se escapa**.
 */
import { useEffect, useRef, type KeyboardEvent, type ReactNode } from 'react'

import {
  Dialog, DialogBackdrop, DialogContent, DialogDescription, DialogTitle,
} from '@ui-sdk/react/dialog'

import { cx } from '../ui'

/** Lo que puede recibir el foco dentro de la capa, en orden de tabulacion. */
const FOCALIZABLES =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function Dialogo({
  abierto,
  alCerrar,
  titulo,
  descripcion,
  children,
  className,
}: {
  /** Se controla desde fuera: la pantalla sabe cuando hay algo que confirmar. */
  abierto: boolean
  /** Se llama al cerrar: Escape, pulsar fuera o el boton de salir. */
  alCerrar: () => void
  /** El nombre del dialogo. Sin el, el lector de pantalla anuncia una capa sin nombre. */
  titulo: string
  descripcion?: ReactNode
  children: ReactNode
  className?: string
}) {
  /** El primer elemento de la capa: lo que recibe el foco al abrir. */
  const caja = useRef<HTMLDivElement>(null)
  /** Quien tenia el foco antes de abrir: ahi vuelve al cerrar. */
  const anterior = useRef<HTMLElement | null>(null)
  /** El cierre de la pantalla, sin volver a lanzar el efecto en cada render. */
  const alCerrarRef = useRef(alCerrar)
  alCerrarRef.current = alCerrar

  /** El contenido de la capa se monta un tick despues de pedir abrir (el popup lo monta en su
   *  efecto), asi que el foco se pide en el primer fotograma en que la capa ya existe. */
  useEffect(() => {
    if (!abierto) return
    anterior.current = document.activeElement as HTMLElement | null
    let vivo = true
    let fotograma = 0
    const intenta = () => {
      if (!vivo) return
      const dentro = caja.current?.querySelectorAll<HTMLElement>(FOCALIZABLES)
      if (dentro?.length) {
        // *El foco entra en el primer boton: es lo que se viene a decidir.*
        dentro[0].focus()
        return
      }
      if (caja.current) {
        // *Sin botones dentro, el foco al panel del dialogo, que es lo que lleva el nombre.*
        const panel = caja.current.closest('[data-slot="dialog-content"]') as HTMLElement | null
        panel?.focus()
        return
      }
      fotograma = requestAnimationFrame(intenta)
    }
    intenta()
    return () => {
      vivo = false
      cancelAnimationFrame(fotograma)
      // *El foco vuelve a quien abrio, no al principio de la pagina.*
      anterior.current?.focus?.()
    }
  }, [abierto])

  function alTeclear(evento: KeyboardEvent<HTMLDivElement>) {
    if (evento.key !== 'Tab') return
    const dentro = caja.current?.querySelectorAll<HTMLElement>(FOCALIZABLES)
    if (!dentro?.length) {
      evento.preventDefault()
      return
    }
    const primero = dentro[0]
    const ultimo = dentro[dentro.length - 1]
    if (evento.shiftKey && document.activeElement === primero) {
      evento.preventDefault()
      ultimo.focus()
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault()
      primero.focus()
    }
  }

  return (
    <Dialog
      open={abierto}
      onOpenChange={(siguiente) => {
        if (!siguiente) alCerrarRef.current()
      }}
      onOpenChangeComplete={(siguiente) => {
        if (siguiente) {
          caja.current?.querySelector<HTMLElement>(FOCALIZABLES)?.focus()
        }
      }}
    >
      <DialogBackdrop className="fixed inset-0 z-40 bg-tinta/50" />
      <DialogContent
        className={cx(
          'fixed left-1/2 top-1/2 z-50 flex w-[min(24rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 flex-col gap-3 rounded-tarjeta bg-papel p-4 shadow-hoja',
          className,
        )}
      >
        <DialogTitle className="font-serif text-titulo font-semibold text-tinta">
          {titulo}
        </DialogTitle>
        {descripcion && (
          <DialogDescription className="text-etiqueta text-tinta-suave">
            {descripcion}
          </DialogDescription>
        )}
        <div ref={caja} onKeyDown={alTeclear} className="flex flex-col gap-2">
          {children}
        </div>
      </DialogContent>
    </Dialog>
  )
}
