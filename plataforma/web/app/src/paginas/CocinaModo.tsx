/** El modo cocina: por donde ibas, y el tiempo.
 *
 *  **Lo que esta pantalla tiene que decir bien, y es lo unico que importa aqui**: *el tiempo **se calcula**, no se
 *  cuenta.* *Un temporizador **que ya paso** se enseña diciendo **cuanto hace que paso** -- *«se paso hace 2
 *  minutos»* --, **y no desaparece**: *un temporizador que se paso **no es un temporizador que no existe**.*
 *
 *  **Y por eso esto sobrevive a la pantalla**: *si se recarga, o se apaga el movil, o se va la conexion, **al
 *  volver el numero es el correcto** -- *porque **no se estaba contando**, se estaba guardando cuando empezo.*
 */
import { useParams } from 'react-router-dom'

import { apuntaUsado, irAlPaso, ponTemporizador, useCocina, useEmpieza } from '../api/cocina'
import { textoDeError } from '../api/cliente'
import { Boton, Tarjeta } from '../componentes/ui'

/** **Segundos, en palabras.** *Y **negativo es «hace»**, que es informacion y no un error.* */
function cuantoTiempo(s: number): string {
  const abs = Math.abs(s)
  const m = Math.floor(abs / 60)
  const seg = abs % 60
  const dicho = m > 0 ? `${m} min ${seg} s` : `${seg} s`
  return s < 0 ? `se paso hace ${dicho}` : `quedan ${dicho}`
}

export function CocinaModo() {
  const { recetaId, version } = useParams()
  const id = Number(recetaId)
  const v = Number(version)
  const { data, isLoading, error } = useCocina(id, v)
  const empieza = useEmpieza(id, v)

  if (isLoading) return <p className="text-tinta-suave">Cargando la cocina...</p>
  if (error) return <p className="text-red-700">{textoDeError(error)}</p>

  // **Y si no hay cocina empezada, se dice** -- *no se inventa un paso.*
  if (!data || data.paso === null) {
    return (
      <div className="space-y-3">
        <h1 className="text-xl font-semibold">Cocina</h1>
        <p className="text-sm text-tinta-suave">Esta receta no esta empezada.</p>
        <Boton onClick={() => empieza.mutate()} disabled={empieza.isPending}>Empezar a cocinar</Boton>
        {empieza.error ? <p className="text-sm text-red-700">{textoDeError(empieza.error)}</p> : null}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Cocina</h1>
      <p className="text-sm text-tinta-suave">
        Vas por el paso <strong>{(data.paso ?? 0) + 1}</strong>. {data.hechos} ingredientes usados.
      </p>

      {data.paso_actual && (
        <Tarjeta>
          <p className="text-base">{data.paso_actual}</p>
        </Tarjeta>
      )}

      {data.temporizadores.length > 0 && (
        <Tarjeta>
          <ul className="divide-y divide-borde">
            {data.temporizadores.map((t, i) => (
              // **Un temporizador que ya paso se pinta distinto, y sigue estando.**
              <li key={i} className={`py-2 ${t.terminado ? 'text-amber-700' : ''}`}>
                {t.minutos} min — {cuantoTiempo(t.queda_segundos)}
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      <div className="flex flex-wrap gap-2">
        <Boton onClick={() => irAlPaso(id, v, (data.paso ?? 0) + 1)}>Paso siguiente</Boton>
        <Boton onClick={() => ponTemporizador(id, v, 10)}>Temporizador de 10 min</Boton>
      </div>
    </div>
  )
}
