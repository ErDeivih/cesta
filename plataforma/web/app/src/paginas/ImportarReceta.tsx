/** Importar una receta: **la previa, antes de guardar**.
 *
 *  **Lo que esta pantalla tiene que decir bien, y es lo unico que importa aqui**: *cuando no se puede importar,
 *  **dice que ha pasado** -- y las tres cosas que pueden pasar **se dicen distinto**.*
 *
 *  1. **«No se puede importar de esa direccion: <motivo>»** -- *la fuente no vale, o el esquema. **Y no se ha
 *     leido nada.***
 *  2. **«Esa pagina no trae una receta legible»** -- *la fuente **si** valia, y la pagina no publica el
 *     estandar.* **Son problemas distintos y se arreglan distinto.**
 *  3. **Y si hay receta, sale la previa** -- *con **su fuente**, con lo que **falta**, y **diciendo que no se ha
 *     guardado nada**.*
 *
 *  **Y no hay boton de guardar**, a proposito: *el criterio pide **previa, fuente, unidades y edicion ANTES de
 *  guardar**, y **guardar es un paso que no esta** -- *asi que no se puede pulsar por error.*
 */
import { useState } from 'react'

import { verPrevia, type Previa } from '../api/importar'
import { textoDeError } from '../api/cliente'
import { Boton, Tarjeta } from '../componentes/ui'

/** *Lo que la receta dice de un ingrediente, y **nada mas**.* */
function comoSeLee(i: { cantidad: number | null; unidad: string | null; texto: string }): string {
  if (i.cantidad === null) return i.texto
  return `${i.cantidad}${i.unidad ? ' ' + i.unidad : ''} - ${i.texto}`
}

export function ImportarReceta() {
  const [url, setUrl] = useState('')
  const [previa, setPrevia] = useState<Previa | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [mirando, setMirando] = useState(false)

  const mira = async () => {
    setAviso(null); setPrevia(null); setMirando(true)
    try {
      setPrevia(await verPrevia(url.trim()))
    } catch (e) {
      // **El motivo del servidor, tal cual.** *Es lo que distingue «no puedo importar de ahi» de «esa pagina no
      // tiene receta» -- y esa distincion es todo el valor de esta pantalla.*
      setAviso(textoDeError(e))
    } finally {
      setMirando(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Importar una receta</h1>
      <p className="text-cuerpo text-tinta-suave">
        Pega la direccion de una receta. Se enseña <strong>antes de guardar nada</strong>, y solo se lee
        de las fuentes permitidas.
      </p>

      <Tarjeta>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[18rem] flex-1 flex-col text-cuerpo">
            Direccion
            <input className="min-h-11 rounded border border-borde px-2 py-1" value={url}
                   onChange={(e) => setUrl(e.target.value)}
                   placeholder="https://.../receta" />
          </label>
          <Boton onClick={mira} disabled={!url.trim() || mirando}>
            {mirando ? 'Mirando...' : 'Ver la previa'}
          </Boton>
        </div>
      </Tarjeta>

      {aviso && (
        <Tarjeta>
          <p className="text-cuerpo text-aviso">{aviso}</p>
          <p className="mt-1 text-etiqueta text-tinta-suave">
            No se ha leido ni guardado nada de esa direccion.
          </p>
        </Tarjeta>
      )}

      {previa && (
        <div className="space-y-3">
          <Tarjeta>
            <p className="text-etiqueta text-tinta-suave">
              <strong>No se ha guardado nada.</strong> Esto es la previa.
            </p>
            <h2 className="mt-1 text-entrada font-semibold">{previa.nombre}</h2>
            <p className="text-cuerpo text-tinta-suave">
              {previa.raciones} raciones
              {previa.minutos !== null ? ` - ${previa.minutos} min` : ''}
            </p>
            <p className="mt-1 text-etiqueta text-tinta-suave break-all">Fuente: {previa.fuente}</p>
            {previa.faltantes.length > 0 && (
              <p className="mt-2 text-cuerpo text-aviso">
                Falta por decir: {previa.faltantes.join('; ')}
              </p>
            )}
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-cuerpo font-semibold">Ingredientes ({previa.ingredientes.length})</h3>
            <ul className="mt-1 divide-y divide-borde">
              {previa.ingredientes.map((i, n) => (
                <li key={n} className="py-1 text-cuerpo">{comoSeLee(i)}</li>
              ))}
            </ul>
          </Tarjeta>

          {previa.preparacion && (
            <Tarjeta>
              <h3 className="text-cuerpo font-semibold">Preparacion</h3>
              <p className="mt-1 whitespace-pre-line text-cuerpo">{previa.preparacion}</p>
            </Tarjeta>
          )}
        </div>
      )}
    </div>
  )
}