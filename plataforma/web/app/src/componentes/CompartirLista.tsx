/** *** COMPARTIR LA LISTA POR ENLACE. *** *
 *
 *  *El enlace lleva la lista dentro (`compartirLista.ts`), así que funciona sin servidor y sin
 *  cuenta en la otra punta: quien lo abre ve una lista local con los mismos productos.*
 *
 *  *Se usa `navigator.share` si el móvil lo tiene; si no, se copia al portapapeles; y si tampoco,
 *  el enlace se queda visible en un campo para copiarlo a mano.*
 */
import { useState } from 'react'

import { codificaLista } from '../logica/compartirLista'
import { Boton } from './ui'
import type { Linea } from '../tipos'

export function CompartirLista({ nombre, lineas }: { nombre: string; lineas: Linea[] }) {
  const [enlace, setEnlace] = useState<string | null>(null)
  const [dicho, setDicho] = useState<string | null>(null)

  const genera = async () => {
    const codigo = codificaLista(nombre, lineas)
    // *El hash es lo que entiende la demo; la ruta se queda en la lista.*
    const url = `${window.location.origin}${window.location.pathname}#/compra/listas?compartir=${codigo}`
    setEnlace(url)
    setDicho(null)
    try {
      if (typeof navigator.share === 'function') {
        await navigator.share({ title: `Lista ${nombre}`, url })
        setDicho('Compartida.')
        return
      }
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        setDicho('Enlace copiado.')
        return
      }
    } catch {
      // *Cancelar el diálogo del sistema no es un fallo: el enlace se queda a la vista.*
    }
    setDicho('Copia el enlace de abajo.')
  }

  return (
    <div className="px-2 pb-1">
      <Boton compacto variante="sutil" className="w-full" onClick={() => void genera()}>
        Compartir por enlace
      </Boton>
      {enlace && (
        <div className="mt-1">
          <label htmlFor="enlace-compartir" className="text-etiqueta text-tinta-suave">
            Enlace para compartir
          </label>
          <input
            id="enlace-compartir"
            readOnly
            value={enlace}
            onFocus={(e) => e.currentTarget.select()}
            className="mt-1 min-h-[44px] w-full rounded-campo border border-borde bg-marfil px-2 text-etiqueta text-tinta"
          />
          {dicho && <p className="mt-1 text-etiqueta text-tinta-suave">{dicho}</p>}
        </div>
      )}
    </div>
  )
}
