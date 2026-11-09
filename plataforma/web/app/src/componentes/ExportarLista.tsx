/** **La lista se puede llevar.** Copiar como texto o descargar un CSV; nada sale del aparato y
 *  no se pide ninguna cuenta.
 *
 *  La descarga se hace con un `Blob` local: no hay endpoint de exportacion ni se inventa. El
 *  portapapeles puede no estar disponible (navegador antiguo o permiso denegado); en ese caso se
 *  dice y se deja el texto a la vista para copiarlo a mano.
 */
import { useState } from 'react'

import { listaACSV, listaATexto, nombreDeFichero } from '../logica/exportarLista'
import type { Linea } from '../tipos'
import { Boton, Tarjeta } from './ui'

export function ExportarLista({ lineas, nombreLista }: {
  lineas: Linea[]
  nombreLista: string
}) {
  const [aviso, setAviso] = useState<string | null>(null)
  const [textoVisible, setTextoVisible] = useState(false)

  async function copiar() {
    setAviso(null)
    const texto = listaATexto(lineas)
    try {
      if (!navigator.clipboard) throw new Error('sin portapapeles')
      await navigator.clipboard.writeText(texto)
      setAviso('Lista copiada.')
    } catch {
      setTextoVisible(true)
      setAviso('No se ha podido copiar sola. Aqui tienes el texto para copiarlo a mano.')
    }
  }

  function descargar() {
    setAviso(null)
    try {
      const contenido = `\uFEFF${listaACSV(lineas)}`
      const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = nombreDeFichero(nombreLista)
      document.body.appendChild(enlace)
      enlace.click()
      enlace.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setAviso('CSV descargado.')
    } catch {
      setAviso('No se ha podido descargar. Copia la lista como texto.')
      setTextoVisible(true)
    }
  }

  if (lineas.length === 0) return null

  return (
    <Tarjeta
      titulo="Llevar la lista"
      sub="Copia el texto o descarga un CSV. No se conecta con ninguna cadena."
    >
      <p className="text-etiqueta text-tinta-suave">
        {lineas.length === 1 ? '1 linea' : `${lineas.length} lineas`} con su cantidad y su nota.
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Boton onClick={() => void copiar()}>Copiar lista</Boton>
        <Boton variante="sutil" onClick={descargar}>Descargar CSV</Boton>
      </div>
      {aviso && <p role="status" className="mt-2 text-[15px] text-bien">{aviso}</p>}
      {textoVisible && (
        <label className="mt-2 block text-etiqueta text-tinta-suave">
          Texto de la lista
          <textarea
            readOnly
            value={listaATexto(lineas)}
            className="mt-1 min-h-[7rem] w-full rounded-campo border border-borde bg-papel p-2 text-tinta"
          />
        </label>
      )}
    </Tarjeta>
  )
}
