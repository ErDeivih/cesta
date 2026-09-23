/** Ajustes: lo poco que hay que configurar, y por que.
 *
 *  Una sola cosa cambia de verdad lo que se ve: **las cadenas que tienes a
 *  mano**. Con eso puesto, el buscador y el panel dejan de ofrecerte cosas de una
 *  cadena a la que no vas.
 *
 *  La fecha de los datos y el aviso de las cadenas con retraso **no** van aqui:
 *  estan en la cabecera, siempre a la vista. Esconderlos en una pantalla de
 *  ajustes seria justo lo contrario de lo que pide el proyecto.
 */
import { useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { cadenasCerca, guardarPreferencia } from '../api/ajustes'
import { textoDeError } from '../api/cliente'
import { salir, yo } from '../api/cesta'
import { useEstado } from '../api/consultas'
import { Boton, Cargando, Etiqueta, Tarjeta, Vacio } from '../componentes/ui'

export function Ajustes() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const estado = useEstado()
  const [guardado, setGuardado] = useState<string | null>(null)

  const prefs = sesion.data?.preferencias
  const puestas = cadenasCerca(prefs)

  const guarda = useMutation({
    mutationFn: (cadenas: string[]) => guardarPreferencia('cadenas_cerca', cadenas),
    onSuccess: (_r, cadenas) => {
      setGuardado(cadenas.length
        ? `Guardado: ${cadenas.join(', ')}`
        : 'Guardado: ninguna, se miran todas')
      cliente.invalidateQueries({ queryKey: ['yo'] })
    },
  })

  if (sesion.isLoading) return <Cargando que="tus ajustes" />

  if (!sesion.data?.usuario) {
    return (
      <Vacio titulo="Entra para cambiar tus ajustes">
        <p>Los ajustes son de cada uno, así que hacen falta tus listas.</p>
      </Vacio>
    )
  }

  const cadenas = estado.data?.cadenas.map((c) => c.cadena) ?? []

  function alterna(cadena: string) {
    const nueva = puestas.includes(cadena)
      ? puestas.filter((c) => c !== cadena)
      : [...puestas, cadena]
    guarda.mutate(nueva)
  }

  return (
    <div className="grid gap-4">
      <header>
        <h1 className="text-xl font-semibold">Ajustes</h1>
        <p className="text-sm text-tinta-suave">
          Has entrado como <strong>{sesion.data.usuario.usuario}</strong>.
          <button
            className="ml-2 inline-flex min-h-[44px] min-w-[44px] items-center justify-center underline"
            onClick={async () => {
              await salir()
              cliente.invalidateQueries()
            }}
          >
            Salir
          </button>
        </p>
      </header>

      <Tarjeta>
        <h2 className="mb-1 text-base font-semibold">Las cadenas que tienes cerca</h2>
        <p className="mb-3 text-sm text-tinta-suave">
          Marca las que te pillan a mano. Con eso puesto, la búsqueda y el panel
          dejan de ofrecerte cosas de una cadena a la que no vas. Sin ninguna
          marcada se miran las cinco, que es lo que hace por defecto.
        </p>
        <div className="flex flex-wrap gap-2">
          {cadenas.map((c) => {
            const dentro = puestas.includes(c)
            return (
              <button
                key={c}
                onClick={() => alterna(c)}
                disabled={guarda.isPending}
                aria-pressed={dentro}
                className={
                  'inline-flex min-h-[44px] items-center rounded-full border px-3 py-1 text-sm ' +
                  (dentro
                    ? 'border-bien bg-bien-suave font-medium'
                    : 'border-borde')
                }
              >
                {c}
              </button>
            )
          })}
          {estado.isPending && <span className="text-sm text-tinta-suave">…</span>}
        </div>
        {puestas.length > 0 && (
          <Boton
            variante="sutil"
            className="mt-3"
            disabled={guarda.isPending}
            onClick={() => guarda.mutate([])}
          >
            Quitar todas
          </Boton>
        )}
        {guardado && <p className="mt-2 text-sm"><Etiqueta tono="bien">{guardado}</Etiqueta></p>}
        {guarda.isError && (
          <p className="mt-2 text-sm text-aviso">{textoDeError(guarda.error)}</p>
        )}
      </Tarjeta>
    </div>
  )
}
