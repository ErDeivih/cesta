/** La pantalla de entrada: buscar y ver resultados.
 *
 *  Los filtros viven en la URL (ver `estado/filtrosUrl.ts`), asi que esta
 *  pantalla no guarda estado propio salvo el texto que se esta tecleando, que
 *  se retrasa 250 ms antes de salir a la red. Sin ese retraso, escribir "leche"
 *  son cinco peticiones y cinco repintados de cuarenta filas.
 */
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { FILTROS_VACIOS, consultaUtil, useBuscar, useEstado, type FiltrosBuscar } from '../api/consultas'
import { fecha } from '../api/formato'
import { FiltrosBusqueda } from '../componentes/FiltrosBusqueda'
import { TablaResultados } from '../componentes/TablaResultados'
import { VistasGuardadas } from '../componentes/VistasGuardadas'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Vacio } from '../componentes/ui'
import { cuantosFiltros, escribirFiltros, leerFiltros } from '../estado/filtrosUrl'

export function Buscar() {
  const [params, setParams] = useSearchParams()
  const filtros = useMemo(() => leerFiltros(params), [params])
  const consulta = params.toString()

  const estado = useEstado()
  const cadenas = useMemo(() => estado.data?.cadenas.map((c) => c.cadena) ?? [], [estado.data])
  const resultados = useBuscar(filtros)

  const [texto, setTexto] = useState(filtros.q)

  const ponFiltros = (nuevos: FiltrosBuscar) => setParams(escribirFiltros(nuevos), { replace: true })

  // El texto que se teclea y el que se busca no son el mismo: este se retrasa.
  useEffect(() => {
    if (texto === filtros.q) return
    const t = window.setTimeout(() => ponFiltros({ ...filtros, q: texto }), 250)
    return () => window.clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texto, filtros.q])

  // Si la URL cambia por fuera (una vista guardada, el boton de atras), el
  // cuadro de texto se pone al dia. Sin esto quedaria escrito lo de antes.
  useEffect(() => {
    setTexto(filtros.q)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros.q])

  const puestos = cuantosFiltros(filtros)
  const busca = consultaUtil(filtros)

  return (
    <div className="grid gap-4">
      <section aria-label="Buscar" className="grid gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="q" className="sr-only">
            Buscar producto
          </label>
          <input
            id="q"
            type="search"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="leche entera, atún, papel de cocina…"
            autoComplete="off"
            enterKeyHint="search"
            className="min-h-[48px] min-w-[16rem] flex-1 rounded-xl border border-neutral-300 bg-white px-4 py-2 text-base dark:border-neutral-600 dark:bg-neutral-800"
          />
          {puestos > 0 && (
            <Boton variante="normal" onClick={() => ponFiltros({ ...FILTROS_VACIOS, q: filtros.q, limite: filtros.limite })}>
              Quitar {puestos} {puestos === 1 ? 'filtro' : 'filtros'}
            </Boton>
          )}
        </div>

        <FiltrosBusqueda
          filtros={filtros}
          cadenasDisponibles={cadenas}
          onCambio={ponFiltros}
          cuantosPuestos={puestos}
        />

        <VistasGuardadas
          consulta={consulta ? `?${consulta}` : ''}
          onAplicar={(c) => setParams(new URLSearchParams(c.startsWith('?') ? c.slice(1) : c))}
        />
      </section>

      {!busca && (
        <Vacio titulo="Escribe al menos dos letras, o elige un pasillo">
          <p>
            {filtros.q.trim().length === 1
              ? 'Con una sola letra no busco: casaría con media tienda y la lista no diría nada.'
              : 'También puedes explorar un pasillo entero sin escribir nada.'}
          </p>
        </Vacio>
      )}

      {busca && resultados.isPending && <Cargando que="el catálogo" />}

      {busca && resultados.isError && (
        <Fallo error={resultados.error} reintentar={() => void resultados.refetch()} />
      )}

      {busca && resultados.data && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              <strong className="font-semibold text-neutral-900 dark:text-neutral-100">
                {resultados.data.resultados.length}
              </strong>{' '}
              {resultados.data.resultados.length === 1 ? 'resultado' : 'resultados'}
              {filtros.seccion && <> en el pasillo elegido</>}
              <span className="ml-1">· datos del {fecha(resultados.data.fecha_datos)}</span>
            </p>
            {resultados.isFetching && <Etiqueta tono="dato">actualizando…</Etiqueta>}
          </div>

          {resultados.data.resultados.length === 0 ? (
            <Vacio titulo="Nada con esos filtros">
              <p>
                Los filtros de dieta y de oferta se aplican a cada producto que se enseña, no al
                grupo entero: si el grupo solo cumple por uno de sus miembros, no sale. Prueba a
                quitar el sello más exigente.
              </p>
            </Vacio>
          ) : (
            <>
              <TablaResultados filas={resultados.data.resultados} />
              <Aviso tono="info">
                El orden se aplica a estos {resultados.data.resultados.length} resultados, no a todo
                el catálogo. Las filas sin precio por unidad se van al final cuando ordenas por
                precio: un dato que no tenemos no se coloca arriba como si fuera el más barato.
              </Aviso>
            </>
          )}
        </>
      )}
    </div>
  )
}
