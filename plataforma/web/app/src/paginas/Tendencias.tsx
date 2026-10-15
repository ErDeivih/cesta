/** Las tendencias: los ultimos dias, con los huecos donde no hay dato.

 *  **Un dia sin dato no es un dia de cero.** Aqui los dias sin energia no llevan barra: llevan la palabra
 *  "sin dato". Un grafico que dibuja cero donde no hay dato dice que se comio nada, y encima hace parecer que
 *  los demas dias estan completos.
 *
 *  **Y tampoco se inventa una media.** Si ningun dia trae dato, no hay nada que promediar y se dice; dibujar
 *  un cero seria inventarse un resultado.
 *
 *  **La medida se declara:** es lo anotado y lo que se sabe, no "lo que comiste".
 */
import { useState } from 'react'

import { textoDeError } from '../api/cliente'
import { useRango } from '../api/diario'
import { GraficaDeLasTres } from '../componentes/GraficaDeLasTres'
import { Cargando, Fallo, Tarjeta, Vacio } from '../componentes/ui'

function hoy(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

function haceDias(cuantos: number): string {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() - cuantos)
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${fecha.getFullYear()}-${mes}-${dia}`
}

export function Tendencias() {
  const [dias, setDias] = useState(14)
  const { data, isPending, error } = useRango(haceDias(dias - 1), hoy())

  const filas = data?.dias ?? []
  const conDato = filas.filter((d) => d.kcal_conocida !== null)
  // **La media, solo de los dias que traen dato.** Meter los huecos como ceros hundiria la media y no seria
  // la media de nada.
  const media = conDato.length
    ? Math.round(conDato.reduce((suma, d) => suma + (d.kcal_conocida ?? 0), 0) / conDato.length)
    : null
  const maximo = conDato.length
    ? Math.max(...conDato.map((d) => d.kcal_conocida ?? 0))
    : 0

  return (
    <div className="flex min-h-full flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-[13px] text-secundaria" htmlFor="dias">
          Ultimos
        </label>
        <select
          id="dias"
          value={dias}
          onChange={(e) => setDias(Number(e.target.value))}
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
        >
          {[7, 14, 30].map((n) => (
            <option key={n} value={n}>
              {n} dias
            </option>
          ))}
        </select>
        <span className="text-[13px] text-secundaria">
          Medido sobre lo <strong>anotado</strong> y lo que se sabe. No es todo lo que comiste.
        </span>
      </div>

      {isPending && <Cargando que="los dias" />}
      {error && <Fallo error={error} />}

      {data && filas.length === 0 && (
        <Vacio titulo="No hay nada anotado en estos dias" className="grow">
          <p>Anota algo en el diario y aparecera aqui.</p>
        </Vacio>
      )}

      {data && filas.length > 0 && (
        <>
          <Tarjeta>
            <p className="font-serif text-[24px] leading-8 font-semibold text-tinta-fuerte tabular-nums">
              {media === null ? 'sin dato' : `${media} kcal`}
            </p>
            <p className="text-[13px] text-secundaria">
              {media === null
                ? 'Ningun dia de los que se anotaron trae energia: no hay media que dar.'
                : `media de los ${conDato.length} dias que traen dato, de ${filas.length} con algo anotado`}
            </p>
          </Tarjeta>

          {/* ***Las tres series: registrado, previsto y objetivo.*** *Y la prevision **cruza a Recetas** por
              una ruta que ya existe -- *porque comprar no es consumir, y **lo previsto no es lo registrado**.*
              *Y si no hay objetivo, son **dos series**, y la leyenda lo dice.* */}
          <GraficaDeLasTres desde={haceDias(dias - 1)} hasta={hoy()} />

          <ul className="flex flex-col gap-2">
            {filas.map((d) => (
              <li key={d.fecha}>
                <Tarjeta>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[14px] text-tinta-fuerte tabular-nums">{d.fecha}</span>
                    <span className="text-[13px] text-secundaria tabular-nums">
                      {d.entradas} {d.entradas === 1 ? 'entrada' : 'entradas'}
                      {d.sin_dato > 0 ? ` · ${d.sin_dato} sin dato` : ''}
                      {d.completo ? ' · completo' : ''}
                    </span>
                  </div>
                  {/* **El hueco, con la palabra.** Sin barra: una barra de longitud cero dice "cero kcal",
                      y lo que pasa es que no se sabe. */}
                  {d.kcal_conocida === null ? (
                    <p className="mt-1 text-[13px] text-aviso">
                      Sin dato de energia en este dia: no se dibuja, porque un cero no es lo mismo que no
                      saber.
                    </p>
                  ) : (
                    <div className="mt-1 h-2 w-full rounded-md bg-marfil">
                      <div
                        className="h-2 rounded-md bg-bosque"
                        style={{ width: `${maximo ? Math.round((d.kcal_conocida / maximo) * 100) : 0}%` }}
                      />
                      <span className="text-[13px] text-tinta-fuerte tabular-nums">
                        {d.kcal_conocida} kcal conocidas
                      </span>
                    </div>
                  )}
                </Tarjeta>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
