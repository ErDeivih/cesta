/** El plan de la semana: que se cocina cada dia y para cuantos.
 *
 *  **Cada linea dice su version, y no es decorativo.** Al poner una receta en un dia, la API fija la
 *  version que tenia ese dia. Enseñarla es lo que hace visible que el plan no cambia solo: si mañana se
 *  cambia la receta, este dia seguira diciendo la version que se planifico.
 *
 *  La semana empieza **hoy**, no el lunes: quien planifica lo hace para los proximos dias, y arrancar
 *  en un dia que ya paso es empezar por lo que no se puede decidir.
 */
import { useState } from 'react'

import { textoDeError } from '../api/cliente'
import { usePlan, usePlanificar, useRecetas } from '../api/recetas'
import { Boton, Tarjeta, Vacio } from '../componentes/ui'

const DIAS = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']

function fechaLocal(d: Date): string {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

function laSemana(): string[] {
  const hoy = new Date()
  return Array.from({ length: 7 }, (_, i) => {
    const dia = new Date(hoy)
    dia.setDate(hoy.getDate() + i)
    return fechaLocal(dia)
  })
}

function nombreDelDia(fecha: string): string {
  const [a, m, d] = fecha.split('-').map(Number)
  const dia = new Date(a, m - 1, d)
  return `${DIAS[dia.getDay()]} ${d}`
}

function PonerEnUnDia({ fecha, alPoner }: { fecha: string; alPoner: () => void }) {
  const [recetaId, setRecetaId] = useState('')
  const [comensales, setComensales] = useState(2)
  const { data } = useRecetas()
  const planificar = usePlanificar()

  const recetas = data?.recetas ?? []
  return (
    <div className="mt-2 flex flex-wrap items-end gap-2">
      <label className="flex flex-col gap-1 text-[13px] text-secundaria">
        Receta
        <select
          value={recetaId}
          onChange={(e) => setRecetaId(e.target.value)}
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[15px] text-tinta-fuerte"
        >
          <option value="">Elige una receta</option>
          {recetas.map((r) => (
            <option key={r.id} value={r.id}>
              {r.nombre}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-[13px] text-secundaria">
        Comensales
        <input
          type="number"
          min={1}
          value={comensales}
          onChange={(e) => setComensales(Number(e.target.value))}
          className="min-h-[44px] w-20 rounded-md border border-borde-fuerte bg-papel px-2 text-[15px] text-tinta-fuerte tabular-nums"
        />
      </label>
      <Boton
        onClick={() => {
          if (!recetaId) return
          planificar.mutate(
            { fecha, receta_id: Number(recetaId), comensales },
            { onSuccess: alPoner },
          )
        }}
        disabled={!recetaId || planificar.isPending}
      >
        Poner
      </Boton>
      {planificar.error && <p className="text-[14px] text-error">{textoDeError(planificar.error)}</p>}
    </div>
  )
}

export function PlanSemanal() {
  const dias = laSemana()
  const [abierto, setAbierto] = useState<string | null>(null)
  const { data, isPending, error } = usePlan(dias[0], dias[dias.length - 1])
  const porFecha = new Map<string, { nombre: string; version: number; comensales: number }[]>()
  for (const linea of data?.plan ?? []) {
    const lista = porFecha.get(linea.fecha) ?? []
    lista.push({ nombre: linea.nombre, version: linea.version, comensales: linea.comensales })
    porFecha.set(linea.fecha, lista)
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-[14px] leading-[22px] text-secundaria">
        Cada receta se guarda con la version que tenia el dia que se puso. Por eso este plan se puede
        releer tal cual dentro de un mes, aunque las recetas hayan cambiado.
      </p>

      {isPending && <p className="text-[15px] text-secundaria">Leyendo el plan...</p>}
      {error && <p className="text-[15px] text-error">{textoDeError(error)}</p>}

      <ul className="flex flex-col gap-2">
        {dias.map((fecha) => {
          const lineas = porFecha.get(fecha) ?? []
          return (
            <li key={fecha}>
              <Tarjeta>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-serif text-[19px] leading-7 text-tinta-fuerte">
                    {nombreDelDia(fecha)}
                  </span>
                  <button
                    type="button"
                    onClick={() => setAbierto(abierto === fecha ? null : fecha)}
                    className="min-h-[44px] text-[14px] text-secundaria underline"
                  >
                    {abierto === fecha ? 'Cerrar' : 'Poner algo'}
                  </button>
                </div>

                {lineas.length === 0 ? (
                  <p className="mt-1 text-[13px] text-secundaria">Nada planificado.</p>
                ) : (
                  <ul className="mt-1 flex flex-col gap-1">
                    {lineas.map((l) => (
                      <li key={`${l.nombre}-${l.version}`} className="text-[15px] text-tinta-fuerte">
                        {l.nombre}{' '}
                        <span className="text-[13px] text-secundaria tabular-nums">
                          v{l.version} · para {l.comensales}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}

                {abierto === fecha && <PonerEnUnDia fecha={fecha} alPoner={() => setAbierto(null)} />}
              </Tarjeta>
            </li>
          )
        })}
      </ul>

      {data && data.plan.length === 0 && (
        <Vacio titulo="La semana esta vacia">
          <p>Pon una receta en un dia y aparecera aqui con su version y sus comensales.</p>
        </Vacio>
      )}
    </div>
  )
}
