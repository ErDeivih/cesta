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
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { textoDeError } from '../api/cliente'
import { misListas, previaDelPlan, traerDelPlan } from '../api/cesta'
import type { PreviaDelPlan } from '../api/cesta'
import { useDuplicarSemana, usePlan, usePlanificar, useRecetas } from '../api/recetas'
import type { ReciboDeSemana } from '../api/recetas'
import { Boton, Tarjeta, Vacio, Fallo } from '../componentes/ui'

const DIAS = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']

/** *** Las comidas del dia, *y **el orden importa.** *** *
 *
 * *Es **el mismo vocabulario que `core/diario.py:COMIDAS`**, *y **a proposito**: *el diario y el plan
 * **tienen que llamar igual a lo mismo**, *porque **un plan que diga «cena» y un diario que diga
 * «Cena»** son **dos cosas distintas para quien los lee.** *
 *
 * *Y **aqui hace falta la lista y no solo el dato** porque el API manda **las comidas que hay**, *
 * *no **todas las que podrian haber**: *si se pintara en el orden que llega la consulta, *
 * *la pantalla **bailaria** entre recargas *-- *y «merienda» apareceria antes de «comida» un dia si
 * y otro no.* *
 *
 * *Si algun dia se anade una comida **al diario**, *hay que anadirla **aqui tambien**: *esta constante
 * es **un espejo**, *y **lo unico que impide que se separen** es que **el ensayo del diario** siga
 * pasando *(-- *y que quien lea esto sepa que el original esta en Python.* --)*
 */
const COMIDAS = ['desayuno', 'media manana', 'comida', 'merienda', 'cena', 'otras']

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
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
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
          className="min-h-[44px] w-20 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
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

function TraerALaLista({ desde, hasta }: { desde: string; hasta: string }) {
  const cliente = useQueryClient()
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas })
  // **El destino NO se elige a dedo.** *El plan lo pide con estas palabras:
  // «`PlanSemanal.tsx` elige la lista de casa o, si no existe, la primera lista. **Debe elegir destino
  // explícito, no escribir en otra lista silenciosamente**.»*
  //
  // *Antes esto era `?? listas.data?.[0]?.id`: *si no habia lista de casa, **escribia en la primera
  // que hubiera** -- *que puede ser una lista compartida, o de otra cosa --, *y **la pantalla no decia
  // en cual.** *Y si **no habia ninguna**, el componente hacia `return null`: *el boton **desaparecia
  // sin decir por que**, *que es la otra mitad del mismo defecto.*
  //
  // *Asi que ahora:*
  //   - **el destino es la lista de casa, y solo esa**;
  //   - **se dice cual es**, en el titulo;
  //   - *y si no hay ninguna, **se dice que hace falta una** en vez de desaparecer.
  const destino = listas.data?.find((l) => l.es_de_casa) ?? null
  const listaId = destino?.id ?? null
  const [previa, setPrevia] = useState<PreviaDelPlan | null>(null)
  const [traido, setTraido] = useState(0)
  const [fuera, setFuera] = useState<string[]>([])

  const ver = useMutation({
    mutationFn: () => previaDelPlan(listaId as string, desde, hasta),
    onSuccess: (p) => { setPrevia(p); setTraido(0) },
  })
  const traer = useMutation({
    mutationFn: () => traerDelPlan(listaId as string, desde, hasta),
    onSuccess: () => {
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      setTraido(previa?.total ?? 0)
      setFuera(previa?.sin_catalogo ?? [])
      setPrevia(null)
    },
  })

  // **Y si no hay lista de casa, se dice** -- *no se escribe en otra, ni se desaparece.*
  if (listaId === null) {
    if (!listas.isSuccess) return null
    return (
      <Tarjeta>
        <span className="text-[16px] text-tinta-fuerte">Del plan a la lista</span>
        <p className="mt-2 text-[15px] text-tinta-suave">
          Para traer el plan a la lista hace falta una lista de la casa. Crea una en Compra y vuelve.
        </p>
      </Tarjeta>
    )
  }
  return (
    <Tarjeta>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[16px] text-tinta-fuerte">
          Del plan a la lista
          {/* **Y el destino, dicho**: *«no escribir en otra lista silenciosamente» incluye decir en cual. */}
          {destino && <span className="text-tinta-suave"> · {destino.nombre}</span>}
        </span>
        <Boton onClick={() => ver.mutate()} disabled={ver.isPending}>
          Ver que entraria
        </Boton>
      </div>

      {(traido > 0 || fuera.length > 0) && (
        <p className="mt-2 text-[15px] text-tinta-fuerte">
          {traido === 1 ? 'Ha entrado 1 ingrediente.' : `Han entrado ${traido} ingredientes.`}
          {fuera.length > 0 && (traido > 0 ? ' ' : '') +
            (fuera.length === 1
              ? 'Uno se ha quedado fuera: no esta en el catalogo.'
              : `${fuera.length} se han quedado fuera: no estan en el catalogo.`)}
        </p>
      )}

      {previa && (
        <div className="mt-2 flex flex-col gap-2">
          {previa.total === 0 ? (
            <p className="text-[15px] text-secundaria">
              No hay nada que traer: lo del plan ya esta en la lista.
            </p>
          ) : (
            <>
              <p className="text-[15px] text-tinta-fuerte">
                {previa.total === 1 ? 'Entraria 1 ingrediente:' : `Entrarian ${previa.total} ingredientes:`}
              </p>
              <ul className="flex flex-col gap-1">
                {previa.entrarian.map((x) => (
                  <li key={`${x.receta}-${x.nombre}-${x.fecha}`} className="text-[15px] text-tinta-fuerte">
                    {x.nombre}
                    {x.cantidad !== null && (
                      <span className="text-[13px] text-secundaria tabular-nums">
                        {' '}{x.cantidad} {x.unidad ?? ''}
                      </span>
                    )}
                    <span className="text-[13px] text-secundaria"> ? de {x.receta}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {previa.ya_estaban.length > 0 && (
            <p className="text-[14px] text-secundaria">
              Ya estaban en la lista, y no se repiten: {previa.ya_estaban.join(', ')}.
            </p>
          )}

          {/* **Lo que no puede entrar, se dice.** Un ingrediente escrito a mano no esta enlazado con
              el catalogo y no se puede anadir: antes se prometia y la accion reventaba. Medido el 13
              de octubre de 2026. */}
          {previa.sin_catalogo.length > 0 && (
            <p className="text-[14px] text-secundaria">
              {previa.sin_catalogo.length === 1
                ? 'Uno no se puede anadir, porque no esta enlazado con el catalogo: '
                : `${previa.sin_catalogo.length} no se pueden anadir, porque no estan enlazados con el catalogo: `}
              {previa.sin_catalogo.join(', ')}.
            </p>
          )}

          {previa.total > 0 && (
            <Boton onClick={() => traer.mutate()} disabled={traer.isPending}>
              Si, traerlo a la lista
            </Boton>
          )}
        </div>
      )}

      {/* **El error, FUERA del bloque de la previa.** Estaba dentro, y al confirmar yo limpiaba la
          previa: un fallo al traer se veia exactamente igual que no haber pulsado nada. Medido el 13
          de octubre de 2026 -- un 500 invisible. */}
      {(ver.error || traer.error) && (
        <p className="mt-2 text-[14px] text-error">{textoDeError(ver.error ?? traer.error)}</p>
      )}
    </Tarjeta>
  )
}

/**
 * *** Duplicar la semana: *lo planeado de estos siete dias, *a los siete siguientes.** *** *
 *
 * *Es **la tercera frase de B07** *--* «*Plan con varias comidas por dia, *** repetir/duplicar
 * semana *** y raciones por ocurrencia» --, *y **solo se puede ofrecer desde que la ocurrencia tiene
 * identidad**: *antes **no habia que copiar**, *porque una receta por dia **era una fila.** *
 *
 * *** Y enseña el recibo, *no un «hecho». *** *Porque **«hecho» no dice si copio tres o ninguna**, *
 * *y **lo que ya estaba NO se pisa** *(-- *lo dice B05: *«*misma clave con contenido distinto produce
 * *** conflicto, no exito ficticio ***» --). *Asi que se dicen **los dos numeros.** *
 */
function DuplicarLaSemana({ desde, hasta }: { desde: string; hasta: string }) {
  const duplicar = useDuplicarSemana()
  const [recibo, setRecibo] = useState<ReciboDeSemana | null>(null)
  const semanaSiguiente = fechaLocal(new Date(new Date(`${desde}T00:00:00`).getTime() + 7 * 86400000))

  return (
    <Tarjeta>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[16px] text-tinta-fuerte">
          Repetir la semana
          {/* *Y **a cual**, dicho* -- *igual que el destino de la lista se dice.* */}
          <span className="text-tinta-suave"> · a la del {semanaSiguiente}</span>
        </span>
        <Boton
          onClick={() => duplicar.mutate({ desde, hacia: semanaSiguiente }, { onSuccess: setRecibo })}
          disabled={duplicar.isPending}
        >
          {duplicar.isPending ? 'Copiando...' : 'Copiar el plan'}
        </Boton>
      </div>

      {duplicar.error && <p className="mt-2 text-[15px] text-error">{textoDeError(duplicar.error)}</p>}

      {recibo && (
        <p className="mt-2 text-[15px] text-tinta-fuerte">
          {recibo.creadas === 0 && recibo.ya_estaban === 0
            ? 'No habia nada que copiar: esta semana esta vacia.'
            : `${recibo.creadas === 1 ? 'Ha entrado 1' : `Han entrado ${recibo.creadas}`} · ` +
              `${recibo.ya_estaban === 1 ? '1 ya estaba' : `${recibo.ya_estaban} ya estaban`}.`}
        </p>
      )}
    </Tarjeta>
  )
}

export function PlanSemanal() {
  const dias = laSemana()
  const [abierto, setAbierto] = useState<string | null>(null)
  const { data, isPending, error } = usePlan(dias[0], dias[dias.length - 1])
  // *** Y el plan se agrupa **por dia Y por comida**, *que es lo que el modelo ahora distingue. *** *
  //
  // *Hasta el 14/10/2026 esto era un mapa por **fecha**, *y **descartaba** la comida y las raciones
  // porque **no existian**: *el plan era `(fecha, receta_id)`, *una receta por dia. *Hoy la clave es
  // **`(fecha, comida, receta_id)`**, *asi que **la misma receta puede ir a la comida y a la cena**,
  // *y **cada una con sus raciones** -- *y si la pantalla siguiera agrupando por fecha, **se verian
  // dos veces sin decir por que.** *
  const porFechaYComida = new Map<
    string,
    { nombre: string; version: number; comensales: number; comida: string; raciones: number | null }[]
  >()
  for (const linea of data?.plan ?? []) {
    const clave = `${linea.fecha}|${linea.comida}`
    const lista = porFechaYComida.get(clave) ?? []
    lista.push({
      nombre: linea.nombre,
      version: linea.version,
      comensales: linea.comensales,
      comida: linea.comida,
      raciones: linea.raciones,
    })
    porFechaYComida.set(clave, lista)
  }
  // *Y **las comidas que hay ese dia**, en el orden del vocabulario del diario -- *no en el que
  // devuelva la consulta --, *para que la pantalla **no baile** entre recargas.* *
  const comidasDelDia = (fecha: string) =>
    COMIDAS.filter((c) => porFechaYComida.has(`${fecha}|${c}`))

  return (
    <div className="flex flex-col gap-3">
      <p className="text-[14px] leading-[22px] text-secundaria">
        Cada receta se guarda con la version que tenia el dia que se puso. Por eso este plan se puede
        releer tal cual dentro de un mes, aunque las recetas hayan cambiado.
      </p>

      <TraerALaLista desde={dias[0]} hasta={dias[dias.length - 1]} />

      <DuplicarLaSemana desde={dias[0]} hasta={dias[dias.length - 1]} />

      {isPending && <p className="text-[16px] text-secundaria">Leyendo el plan...</p>}
      {error && <Fallo error={error} />}

      <ul className="flex flex-col gap-2">
        {dias.map((fecha) => {
          // *** Y dentro del dia, **una seccion por comida** *-- *y **en el orden del vocabulario**,
          // *no en el que devuelva la consulta.* *
          const comidas = comidasDelDia(fecha)
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
                    className="min-h-[44px] min-w-[44px] text-[14px] text-secundaria underline"
                  >
                    {abierto === fecha ? 'Cerrar' : 'Poner algo'}
                  </button>
                </div>

                {comidas.length === 0 ? (
                  <p className="mt-1 text-[13px] text-secundaria">Nada planificado.</p>
                ) : (
                  <div className="mt-1 flex flex-col gap-2">
                    {comidas.map((comida) => (
                      <div key={comida}>
                        {/* *La comida, dicha **con su nombre** -- *que es lo que distingue dos
                            lineas de la misma receta el mismo dia.* */}
                        <p className="text-[13px] uppercase tracking-wide text-secundaria">{comida}</p>
                        <ul className="flex flex-col gap-1">
                          {(porFechaYComida.get(`${fecha}|${comida}`) ?? []).map((l) => (
                            <li
                              key={`${l.nombre}-${l.version}`}
                              className="text-[16px] text-tinta-fuerte"
                            >
                              {l.nombre}{' '}
                              <span className="text-[13px] text-secundaria tabular-nums">
                                v{l.version} · para {l.comensales}
                                {/* *** Y las raciones, *donde `null` NO es cero. *** *
                                    *`null` quiere decir **«las de la receta»**, *asi que se dice
                                    *-- *y **no se pone «0 raciones»**, *que seria **inventar un
                                    * dato** *y ademas **el contrario** del que hay.* */}
                                {l.raciones === null
                                  ? ' · las raciones de la receta'
                                  : ` · ${l.raciones} raciones`}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
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
