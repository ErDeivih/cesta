/** El panel: los numeros del sistema, con su tamaño de muestra al lado.
 *
 *  La regla de `plataforma/api/panel.py`, copiada aqui: **cada numero dice sobre
 *  cuantas filas se ha calculado y de que fecha es**. Un 19,4 % sin decir sobre
 *  cuantos grupos no es un panel, es una opinion con tipografia.
 *
 *  Dos cosas que no son opcionales:
 *   - El `aviso` de `/panel/marcas` se enseña SIEMPRE y arriba. Dice que
 *     porcentaje de las letras de calidad salen del precio; sin el, el estudio
 *     se lee justo al reves ("la marca propia es peor").
 *   - **Aqui no se aprueba ni se rechaza nada.** No hay botones de validar
 *     equivalencias ni de corregir emparejamientos: en este proyecto no hay
 *     validacion humana y no la va a haber.
 */
import { Link, useSearchParams } from 'react-router-dom'
import type { ReactNode } from 'react'

import {
  useBajadas,
  usePanelCadenas,
  usePanelHistorico,
  usePanelHoy,
  usePanelMarcas,
  usePanelMovidos,
} from '../api/consultas'
import { euros, eurosUnidad, fecha, numero, porcentaje, porcentajeConSigno } from '../api/formato'
import { Aviso, Cargando, Dato, Etiqueta, Fallo, Selector, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

const PESTANAS = [
  { clave: 'hoy', texto: 'Hoy' },
  { clave: 'cadenas', texto: 'Cadenas' },
  { clave: 'marcas', texto: 'Marcas' },
  { clave: 'historico', texto: 'Histórico' },
  { clave: 'movidos', texto: 'Movidos' },
  { clave: 'bajadas', texto: 'Bajadas' },
] as const

type Clave = (typeof PESTANAS)[number]['clave']

export function Panel() {
  const [params, setParams] = useSearchParams()
  const crudo = params.get('pestana')
  const activa: Clave = (PESTANAS.find((p) => p.clave === crudo)?.clave ?? 'hoy') as Clave

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-xl font-bold">Panel</h1>
        <Link
          to="/panel/matching"
          className="inline-flex min-h-[44px] items-center text-sm underline"
        >
          Panel de matching →
        </Link>
      </div>

      <div role="tablist" aria-label="Secciones del panel" className="flex flex-wrap gap-1">
        {PESTANAS.map((p) => (
          <button
            key={p.clave}
            type="button"
            role="tab"
            aria-selected={activa === p.clave}
            onClick={() => setParams({ pestana: p.clave }, { replace: true })}
            className={
              'min-h-[44px] rounded-lg border px-3 py-1 text-sm font-medium ' +
              (activa === p.clave
                ? 'border-sky-700 bg-sky-700 text-white dark:border-sky-500 dark:bg-sky-700'
                : 'border-neutral-300 bg-white hover:bg-neutral-50 dark:border-neutral-600 dark:bg-neutral-800 dark:hover:bg-neutral-700')
            }
          >
            {p.texto}
          </button>
        ))}
      </div>

      {activa === 'hoy' && <Hoy />}
      {activa === 'cadenas' && <Cadenas />}
      {activa === 'marcas' && <Marcas />}
      {activa === 'historico' && <Historico />}
      {activa === 'movidos' && <Movidos />}
      {activa === 'bajadas' && <Bajadas />}
    </div>
  )
}

/** Envoltorio comun: pinta cargando, fallo y datos sin repetirlo seis veces. */
function Bloque<T>({
  consulta,
  children,
  titulo,
}: {
  consulta: { isPending: boolean; isError: boolean; error: unknown; data?: T; refetch: () => unknown }
  titulo: string
  children: (datos: T) => ReactNode
}) {
  if (consulta.isPending) return <Cargando que={titulo} />
  if (consulta.isError) {
    return <Fallo error={consulta.error} reintentar={() => void consulta.refetch()} />
  }
  if (!consulta.data) return null
  return <>{children(consulta.data)}</>
}

function SelloFecha({ fechaDatos }: { fechaDatos: string }) {
  return <Etiqueta tono="dato">datos del {fecha(fechaDatos)}</Etiqueta>
}

function Hoy() {
  const consulta = usePanelHoy()
  return (
    <Bloque consulta={consulta} titulo="el estado del día">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">La ingesta de hoy</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          {d.alarmas.length > 0 && (
            <Aviso tono="mal" titulo="Alarmas">
              <ul className="mt-1 grid gap-1">
                {d.alarmas.map((a) => (
                  <li key={a.cadena}>
                    <strong>{a.cadena}</strong>: hoy {numero(a.hoy, 0)} productos, y lo normal son{' '}
                    {numero(a.lo_normal, 0)} ({porcentaje(a.caida_pct)} menos). Una caída así sin un
                    cambio de alcance detrás suele ser algo roto.
                  </li>
                ))}
              </ul>
            </Aviso>
          )}

          <Tarjeta titulo="Qué entró por cadena" sub="Sobre cuántos productos se ha contado cada cosa">
            <TablaScroll etiqueta="Ingesta por cadena" minAncho="40rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Cadena</Th>
                    <Th>Productos</Th>
                    <Th>Comparables</Th>
                    <Th>Con Nutri-Score</Th>
                    <Th>Con EAN</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.cadenas.map((c) => (
                    <tr key={c.cadena}>
                      <Td>{c.cadena}</Td>
                      <Td className="cifra">{numero(c.productos, 0)}</Td>
                      <Td className="cifra">{numero(c.comparables, 0)}</Td>
                      <Td className="cifra">{numero(c.con_nutriscore, 0)}</Td>
                      <Td className="cifra">{numero(c.con_ean, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta titulo="Precios movidos hoy">
            <ul className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2 lg:grid-cols-3">
              {d.movidos.map((m) => (
                <li key={m.cadena} className="flex justify-between gap-2 border-b border-neutral-100 py-1 dark:border-neutral-700">
                  <span className="font-medium">{m.cadena}</span>
                  <span className="cifra">
                    <span className="text-emerald-800 dark:text-emerald-400">
                      {numero(m.bajadas, 0)} ↓
                    </span>{' '}
                    <span className="text-red-800 dark:text-red-400">{numero(m.subidas, 0)} ↑</span>
                  </span>
                </li>
              ))}
              {d.movidos.length === 0 && <li>Hoy no se ha movido nada.</li>}
            </ul>
          </Tarjeta>
        </div>
      )}
    </Bloque>
  )
}

function Cadenas() {
  const consulta = usePanelCadenas()
  return (
    <Bloque consulta={consulta} titulo="las cadenas">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">Quién gana y cuánto se mueve</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          <Tarjeta
            titulo="Quién es más barato"
            sub={`Sobre ${numero(d.dispersion.grupos, 0)} grupos con dos cadenas o más`}
          >
            <TablaScroll etiqueta="Quién es más barato" minAncho="34rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Cadena</Th>
                    <Th>Compite en</Th>
                    <Th>Gana</Th>
                    <Th>% de veces que gana</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.mas_barata.map((c) => (
                    <tr key={c.cadena}>
                      <Td>{c.cadena}</Td>
                      <Td className="cifra">{numero(c.compite_en, 0)}</Td>
                      <Td className="cifra">{numero(c.gana, 0)}</Td>
                      <Td className="cifra font-semibold">{porcentaje(c.pct)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta
            titulo="Cuánto se mueve cada cadena"
            sub="Mediana de la variación, solo entre los precios que se movieron"
          >
            <TablaScroll etiqueta="Movimiento por cadena" minAncho="34rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Cadena</Th>
                    <Th>Observaciones</Th>
                    <Th>Movidos</Th>
                    <Th>%</Th>
                    <Th>Mediana</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.movimiento.map((m) => (
                    <tr key={m.cadena}>
                      <Td>{m.cadena}</Td>
                      <Td className="cifra">{numero(m.observaciones, 0)}</Td>
                      <Td className="cifra">{numero(m.movidos, 0)}</Td>
                      <Td className="cifra">{porcentaje(m.pct, 2)}</Td>
                      <Td className="cifra">{euros(m.mediana_cent)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta titulo="Dispersión dentro del mismo grupo">
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Dato etiqueta="Grupos comparables">{numero(d.dispersion.grupos, 0)}</Dato>
              <Dato etiqueta="Diferencia mediana">{porcentaje(d.dispersion.mediana_pct)}</Dato>
              <Dato etiqueta="Percentil 90">{porcentaje(d.dispersion.p90_pct)}</Dato>
              <Dato etiqueta="Sospechosos (más del triple)">
                {numero(d.dispersion.sospechosos, 0)}
              </Dato>
            </dl>
            <p className="mt-2 text-xs text-tinta-suave">
              «Sospechosos» es donde la más cara vale más del triple que la más barata. Ahí casi
              siempre hay un problema de unidades o de emparejamiento, no una oferta.
            </p>
          </Tarjeta>
        </div>
      )}
    </Bloque>
  )
}

function Marcas() {
  const consulta = usePanelMarcas()
  return (
    <Bloque consulta={consulta} titulo="las marcas">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">Marca propia contra marca</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          {/* Este aviso es obligatorio: sin el, el estudio se lee al revés. */}
          <Aviso tono="aviso" titulo="Antes de mirar los números">
            <p>{d.aviso}</p>
          </Aviso>

          <Tarjeta
            titulo="Precio por unidad"
            sub={`Sobre ${numero(d.grupos_con_ambas, 0)} grupos que tienen a la vez marca propia y de marca`}
          >
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Dato etiqueta="Media, marca propia">{euros(d.media_propia_cent)}</Dato>
              <Dato etiqueta="Media, marca">{euros(d.media_marca_cent)}</Dato>
              <Dato etiqueta="Diferencia">{porcentaje(d.ahorro_pct)}</Dato>
            </dl>
          </Tarjeta>

          <Tarjeta
            titulo="El duelo cara a cara"
            sub="Solo con letras leídas de una etiqueta de verdad, nunca con las que salen del precio"
          >
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-4">
              <Dato etiqueta="Grupos">{numero(d.duelo.grupos, 0)}</Dato>
              <Dato etiqueta="Gana la propia">{numero(d.duelo.gana_propia, 0)}</Dato>
              <Dato etiqueta="Empatan">{numero(d.duelo.empatan, 0)}</Dato>
              <Dato etiqueta="Gana la marca">{numero(d.duelo.gana_marca, 0)}</Dato>
            </dl>
            {d.duelo.grupos < 100 && (
              <p className="mt-2 text-xs text-tinta-suave">
                Con tan pocos grupos, esto es una pista y no una conclusión. La muestra es pequeña
                porque son pocas las cadenas que publican ingredientes.
              </p>
            )}
          </Tarjeta>

          <Tarjeta titulo="De dónde salen las letras de calidad">
            <TablaScroll etiqueta="Origen de las letras de calidad" minAncho="24rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Origen</Th>
                    <Th>Productos</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.calidad_origen.map((o) => (
                    <tr key={o.origen}>
                      <Td>{o.origen === 'precio' ? 'ordenar por precio (es gama, no calidad)' : o.origen}</Td>
                      <Td className="cifra">{numero(o.productos, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta titulo="Marcas propias con más productos">
            <ul className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2 lg:grid-cols-3">
              {d.marcas_propias.map((m) => (
                <li key={`${m.cadena}-${m.marca}`} className="flex justify-between gap-2 border-b border-neutral-100 py-1 dark:border-neutral-700">
                  <span>
                    <span className="font-medium">{m.marca}</span>{' '}
                    <span className="text-tinta-suave">({m.cadena})</span>
                  </span>
                  <span className="cifra">{numero(m.productos, 0)}</span>
                </li>
              ))}
            </ul>
          </Tarjeta>
        </div>
      )}
    </Bloque>
  )
}

function Historico() {
  const consulta = usePanelHistorico()
  return (
    <Bloque consulta={consulta} titulo="el histórico">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">
              {numero(d.dias, 0)} {d.dias === 1 ? 'día guardado' : 'días guardados'}
            </h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          <Tarjeta titulo="Lo que se desbloquea cuando haya más días">
            <ul className="grid grid-cols-1 gap-2 text-sm">
              {d.pendientes.map((p) => (
                <li key={p.que} className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-100 py-1 dark:border-neutral-700">
                  <span>
                    <code className="font-mono">{p.que}</code> — {p.para}
                  </span>
                  <span className="cifra">
                    {p.faltan === 0 ? (
                      <Etiqueta tono="bien">ya está</Etiqueta>
                    ) : (
                      <Etiqueta tono="dato">
                        faltan {numero(p.faltan, 0)} de {numero(p.necesita, 0)} días
                      </Etiqueta>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </Tarjeta>

          <Tarjeta titulo="Observaciones por día">
            <TablaScroll etiqueta="Observaciones por día" minAncho="26rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Día</Th>
                    <Th>Observaciones</Th>
                    <Th>Cadenas</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.serie.map((s) => (
                    <tr key={s.fecha}>
                      <Td>{fecha(s.fecha)}</Td>
                      <Td className="cifra">{numero(s.observaciones, 0)}</Td>
                      <Td className="cifra">{numero(s.cadenas, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>
        </div>
      )}
    </Bloque>
  )
}

function Movidos() {
  const consulta = usePanelMovidos()
  return (
    <Bloque consulta={consulta} titulo="lo que se ha movido">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">Lo que se ha movido hoy</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>
          {d.movidos.length === 0 ? (
            <Vacio titulo="Hoy no se ha movido nada" />
          ) : (
            <TablaScroll etiqueta="Precios movidos hoy" minAncho="44rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Producto</Th>
                    <Th>Cadena</Th>
                    <Th>Por unidad</Th>
                    <Th>Variación</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.movidos.map((m, i) => (
                    <tr key={`${m.cadena}-${m.grupo_id}-${i}`}>
                      <Td>
                        {m.grupo_id === null ? (
                          m.nombre
                        ) : (
                          <Link to={`/grupo/${m.grupo_id}`} className="underline">
                            {m.nombre}
                          </Link>
                        )}
                        {m.marca && (
                          <span className="block text-xs text-tinta-suave">
                            {m.marca}
                          </span>
                        )}
                      </Td>
                      <Td>{m.cadena}</Td>
                      <Td className="cifra">{eurosUnidad(m.precio_unidad_cent, m.unidad)}</Td>
                      <Td className="cifra">
                        <span
                          className={
                            m.baja
                              ? 'font-semibold text-emerald-800 dark:text-emerald-400'
                              : 'font-semibold text-red-800 dark:text-red-400'
                          }
                        >
                          {m.baja ? '↓' : '↑'} {euros(m.variacion_cent)}
                        </span>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          )}
        </div>
      )}
    </Bloque>
  )
}

function Bajadas() {
  const [params, setParams] = useSearchParams()
  const dias = Number(params.get('dias') ?? '7') || 7
  const subidas = params.get('subidas') === 'true'
  const consulta = useBajadas(dias, subidas, [])

  return (
    <Bloque consulta={consulta} titulo="las bajadas">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-end gap-3">
            <h2 className="text-base font-semibold">
              Lo que más ha {subidas ? 'subido' : 'bajado'} en {numero(d.dias, 0)} días
            </h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
            <Selector
              etiqueta="Ventana"
              value={String(dias)}
              onChange={(e) => setParams({ ...Object.fromEntries(params), dias: e.target.value }, { replace: true })}
            >
              <option value="1">1 día</option>
              <option value="7">7 días</option>
              <option value="30">30 días</option>
              <option value="90">90 días</option>
            </Selector>
            <button
              type="button"
              aria-pressed={subidas}
              onClick={() =>
                setParams({ ...Object.fromEntries(params), subidas: subidas ? 'false' : 'true' }, { replace: true })
              }
              className="min-h-[44px] rounded-lg border border-neutral-300 bg-white px-3 text-sm font-medium dark:border-neutral-600 dark:bg-neutral-800"
            >
              Ver las subidas
            </button>
          </div>

          {d.resultados.length === 0 ? (
            <Vacio titulo={`Nada ha ${subidas ? 'subido' : 'bajado'} en ${d.dias} días`} />
          ) : (
            <TablaScroll etiqueta="Cambios de precio" minAncho="46rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <Th>Producto</Th>
                    <Th>Cadena</Th>
                    <Th>Antes</Th>
                    <Th>Ahora</Th>
                    <Th>Cambio</Th>
                    <Th>Desde</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.resultados.map((b, i) => (
                    <tr key={`${b.cadena}-${b.grupo_id}-${i}`}>
                      <Td>
                        {b.grupo_id === null ? (
                          b.nombre
                        ) : (
                          <Link to={`/grupo/${b.grupo_id}`} className="underline">
                            {b.nombre}
                          </Link>
                        )}
                        <div className="mt-0.5 flex flex-wrap gap-1">
                          {b.solo_con_tarjeta && (
                            <Etiqueta tono="aviso" titulo="Sin la tarjeta no existe esta bajada">
                              solo con tarjeta
                            </Etiqueta>
                          )}
                          {b.promo_txt && <Etiqueta tono="dato">{b.promo_txt}</Etiqueta>}
                        </div>
                      </Td>
                      <Td>{b.cadena}</Td>
                      <Td className="cifra">{eurosUnidad(b.precio_unidad_antes_cent, b.unidad)}</Td>
                      <Td className="cifra">{eurosUnidad(b.precio_unidad_cent, b.unidad)}</Td>
                      <Td className="cifra font-semibold">{porcentajeConSigno(b.variacion_pct)}</Td>
                      <Td>{b.desde ? fecha(b.desde) : 'no lo sé'}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          )}

          <Aviso tono="info">
            Solo entran los cambios en los que el precio de venta se ha movido en el mismo sentido y
            la unidad y la cantidad siguen siendo las mismas: si lo que cambió fue el formato, eso
            no es una bajada.
          </Aviso>
        </div>
      )}
    </Bloque>
  )
}
