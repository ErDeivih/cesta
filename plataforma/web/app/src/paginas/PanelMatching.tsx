/** El panel de matching: cómo fue la última pasada del emparejador.
 *
 *  `GET /api/panel/matching` existe en `plataforma/api/panel.py` desde el 22 de
 *  septiembre de 2026. Si el servidor que me atiende es anterior y contesta 404,
 *  esta pantalla dice exactamente eso en vez de pintar un error rojo, porque no
 *  es un fallo: es una ruta que ese servidor no tiene.
 *
 *  Tres cosas que la API no da y aquí se dicen en vez de disimularse:
 *  - `antes: null` en un cambio significa **"esa métrica antes no se medía"**,
 *    no "valía cero". Se pinta "no lo sé" y el delta no se calcula.
 *  - Las métricas vienen con su nombre crudo, sin traducir. Traducirlas aquí
 *    sería inventarse un vocabulario que la API no tiene.
 *  - Si `ultima` es null, no hay ninguna pasada guardada en gold, y eso es una
 *    respuesta, no un fallo.
 *
 *  **Aquí no hay ningún botón de aprobar ni de rechazar, y no lo va a haber.**
 *  El endpoint es de solo lectura a propósito: en este proyecto no hay validación
 *  humana, nunca. El emparejador decide por reglas y se mide contra los pares que
 *  ya sabemos ciertos por EAN. Un panel aquí sirve para ver **por qué** se aceptó
 *  un par, no para arreglarlo a mano.
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { usePanelMatching } from '../api/consultas'
import { esErrorApi } from '../api/cliente'
import { fecha, numero } from '../api/formato'
import { Aviso, Cargando, Dato, Etiqueta, Fallo, Selector, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

export function PanelMatching() {
  const [limite, setLimite] = useState(20)
  const consulta = usePanelMatching(limite)

  if (consulta.isPending) return <Cargando que="la última pasada del emparejador" />

  if (consulta.isError) {
    const e = consulta.error
    if (!(esErrorApi(e) && e.estado === 404)) {
      return <Fallo error={e} reintentar={() => void consulta.refetch()} />
    }
    return <SinRuta />
  }

  const d = consulta.data
  if (!d) return null

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-bold">Panel de matching</h1>
        <Etiqueta tono="dato">datos del {fecha(d.fecha_datos)}</Etiqueta>
        {d.ultima && (
          <Etiqueta tono="info">pasada {d.ultima.ejecucion_id}</Etiqueta>
        )}
      </div>

      <Aviso tono="info" titulo="Esta pantalla no valida nada">
        <p>
          No hay botón de aprobar ni de rechazar equivalencias, y no lo va a haber: en este
          proyecto no hay validación humana. Lo que se puede hacer aquí es <strong>auditar</strong>{' '}
          por qué el emparejador aceptó un par —su nivel, su método, su confianza y los rasgos que
          lo sostienen—, que es lo que hace que un emparejamiento se pueda explicar.
        </p>
      </Aviso>

      {d.ultima === null ? (
        <Vacio titulo="No hay ninguna pasada guardada">
          <p>
            La API ha contestado bien, pero en <code>data/gold/matching/</code> no hay ninguna
            carpeta <code>ejecucion=…</code>. Cada pasada del emparejador deja la suya, con sus
            métricas y sus pares, y nada se sobrescribe: por eso se pueden comparar dos pasadas.
          </p>
          <p className="mt-2">
            Cuando exista la primera, esta pantalla se rellena sola.
          </p>
        </Vacio>
      ) : (
        <>
          <Tarjeta
            titulo="Última pasada"
            /* **El umbral pasa por `numero`, y no se pinta como sale de la API.** Aquí ponía
               `0.55` con punto, mientras el dato de abajo ponía `0,55`: el mismo número escrito
               de dos formas en la misma tarjeta, y la de arriba en inglés. Es el mismo fallo que
               la frase de la ficha del producto, y se vio igual: mirando la pantalla. */
            sub={`Versión ${d.ultima.version_modelo ?? 'no lo sé'} · umbral ${
              d.ultima.umbral === null || d.ultima.umbral === undefined
                ? 'no lo sé'
                : numero(d.ultima.umbral, 4)
            }`}
          >
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Dato etiqueta="Ejecución">{d.ultima.ejecucion_id}</Dato>
              <Dato etiqueta="Productos">{numero(d.ultima.productos ?? null, 0)}</Dato>
              <Dato etiqueta="Umbral">
                {d.ultima.umbral === null || d.ultima.umbral === undefined
                  ? 'no lo sé'
                  : numero(d.ultima.umbral, 4)}
              </Dato>
              <Dato etiqueta="Pasadas guardadas">{d.ejecuciones.length}</Dato>
            </dl>
            {d.ultima.huella_catalogo && (
              <p className="mt-2 text-xs text-tinta-suave">
                Huella del catálogo: <code>{d.ultima.huella_catalogo}</code>. Dos pasadas con la
                misma huella se hicieron sobre el mismo catálogo y se pueden comparar.
              </p>
            )}
          </Tarjeta>

          <Tarjeta
            titulo="Métricas de la pasada"
            sub="El nombre de cada métrica es el que usa el emparejador; no se traduce"
          >
            {d.metricas.length === 0 ? (
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Esta pasada no ha dejado métricas.
              </p>
            ) : (
              <TablaScroll etiqueta="Métricas del matching" minAncho="34rem">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      <Th>Métrica</Th>
                      <Th>Valor</Th>
                      <Th>Antes</Th>
                      <Th>Cambio</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.metricas.map((m) => {
                      const cambio = d.cambios?.find((c) => c.metrica === m.metrica) ?? null
                      return (
                        <tr key={m.metrica}>
                          <Td>
                            <code>{m.metrica}</code>
                          </Td>
                          <Td className="cifra font-semibold" etiqueta="valor">{numero(m.valor, 4)}</Td>
                          <Td className="cifra" etiqueta="antes">
                            {/* `antes: null` es "esa métrica antes no se medía",
                                no un cero. */}
                            {cambio === null || cambio.antes === null
                              ? 'no lo sé'
                              : numero(cambio.antes, 4)}
                          </Td>
                          <Td className="cifra" etiqueta="cambio">
                            {cambio === null || cambio.delta === null ? (
                              'no lo sé'
                            ) : (
                              /* **La flecha dice el sentido; el color no dice nada, y eso es a
                                 proposito.** Hasta el 27 de septiembre de 2026 esto iba en
                                 verde si subia y en rojo si bajaba, y eso es un veredicto que
                                 esta pantalla no puede dar: subir no es bueno ni malo --
                                 `grupos_comparables` arriba es mejor, `grupos_dudosos_ud` arriba
                                 es peor --, y el aviso de arriba dice justo que aqui no se
                                 valida nada. El color, en este proyecto, dice algo (bueno,
                                 aviso, dudoso); si no lo puede decir, no se pinta. */
                              <span
                                title={cambio.delta > 0
                                  ? 'Sube respecto a la pasada anterior'
                                  : cambio.delta < 0
                                    ? 'Baja respecto a la pasada anterior'
                                    : 'Igual que la pasada anterior'}
                              >
                                {cambio.delta > 0 ? '↑ ' : cambio.delta < 0 ? '↓ ' : ''}
                                {numero(Math.abs(cambio.delta), 4)}
                              </span>
                            )}
                          </Td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </TablaScroll>
            )}
            {d.anterior ? (
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                Comparado con la pasada anterior ({d.anterior.ejecucion_id}). La comparación con la
                anterior es la medida de estabilidad: un emparejador que cambia de opinión cada día
                no sirve para decidir una compra.
              </p>
            ) : (
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                Es la primera pasada guardada, así que no hay con qué compararla.
              </p>
            )}
          </Tarjeta>

          <Tarjeta
            titulo="Muestra de pares aceptados"
            acciones={
              <Selector
                etiqueta="Cuántos"
                value={String(limite)}
                onChange={(e) => setLimite(Number(e.target.value))}
              >
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
              </Selector>
            }
            /* «Muestra», y con el numero que se ha pedido, **porque son los primeros N y no
               todos**: la API no manda el total de pares de la pasada, asi que decir «los 20
               pares» seria afirmar que solo hay veinte. Se audita un par, no doscientos. */
            sub={`los primeros ${d.pares.length} de esta pasada, con su método y sus rasgos`}
          >
            {d.pares.length === 0 ? (
              <Vacio titulo="Esta pasada no ha dejado pares" />
            ) : (
              /* **Una tarjeta por par, y no una tabla de seis columnas.** Era una tabla de
                 «Producto A · Producto B · Nivel · Método · Confianza · Por qué» con 52rem de
                 ancho mínimo: en un móvil de 390 px eso obligaba a deslizar de lado para ver
                 el método o la confianza, y los dos nombres de producto (que son largos y con
                 marca) se aplastaban. La composición es la que diseñó Stitch para esta pantalla
                 (proyecto `15743377346721964880`, «Cesta · Panel de Matching»): el par arriba,
                 sus tres datos en una tira corta y los rasgos debajo, que es lo que se viene a
                 auditar. Medido con `data/debug/estructura.py` el 27 de septiembre de 2026: la
                 pantalla entera medía 4.501 px (5,3 pantallas). */
              <ul className="grid gap-3">
                {d.pares.map((p, i) => (
                  <li
                    key={`${p.producto_a}-${p.producto_b}-${i}`}
                    className="rounded-lg border border-neutral-200 p-3 dark:border-neutral-700"
                  >
                    <p className="text-xs uppercase tracking-wide text-tinta-suave">Producto A</p>
                    <EnlaceProducto clave={p.producto_a} nombre={p.nombre_a} fuente={p.fuente_a} />
                    <p className="mt-2 text-xs uppercase tracking-wide text-tinta-suave">
                      Producto B
                    </p>
                    <EnlaceProducto clave={p.producto_b} nombre={p.nombre_b} fuente={p.fuente_b} />
                    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                      <Nivel nivel={p.nivel} />
                      <span>
                        <span className="text-tinta-suave">método </span>
                        <code className="text-xs">{p.metodo ?? 'no lo sé'}</code>
                      </span>
                      <span title="Confianza del emparejador, de 0 a 1">
                        <span className="text-tinta-suave">confianza </span>
                        <span className="cifra">{numero(p.confianza, 4)}</span>
                      </span>
                    </div>
                    {/* Los rasgos son la explicabilidad: sin ellos, un par aceptado es una caja
                        negra. */}
                    <details className="mt-2">
                      <summary className="flex min-h-[44px] cursor-pointer items-center text-xs text-sky-800 dark:text-sky-400">
                        Por qué: {Object.keys(p.features).length} rasgos
                      </summary>
                      <ul className="mt-1 grid grid-cols-1 gap-0.5 text-xs">
                        {Object.entries(p.features).map(([k, v]) => (
                          <li key={k} className="flex justify-between gap-3">
                            <span className="text-neutral-600 dark:text-neutral-400">{k}</span>
                            <span className="cifra">
                              {v === null || v === undefined
                                ? 'no lo sé'
                                : typeof v === 'boolean'
                                  ? v
                                    ? 'sí'
                                    : 'no'
                                  : typeof v === 'number'
                                    ? numero(v, 4)
                                    : String(v)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </li>
                ))}
              </ul>
            )}
          </Tarjeta>

          <details className="rounded-xl border border-neutral-200 p-3 dark:border-neutral-700">
            {/* El desplegable tambien se pulsa: medido el 27 de septiembre de 2026, medía
                **332 x 20 px**. Es la puerta a la respuesta en crudo, y de pie no se acierta. */}
            <summary className="flex min-h-[44px] cursor-pointer items-center text-sm">
              Ver la respuesta en crudo
            </summary>
            <pre className="mt-2 overflow-x-auto rounded-lg bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
              {JSON.stringify(d, null, 2)}
            </pre>
          </details>
        </>
      )}
    </div>
  )
}

/** El nivel del par, con su nombre legible.
 *
 *  Los tres que da hoy `core/matching.py`: `identico` (mismo producto),
 *  `equivalente` (mismo tipo y formato, otra marca) y `ean` (mismo código de
 *  barras). Un nivel que no esté en la lista se enseña tal cual, sin traducir:
 *  inventarse una etiqueta para un valor desconocido sería peor que el valor.
 */
const NIVELES: Record<string, { texto: string; tono: 'bien' | 'info' | 'dato' }> = {
  ean: { texto: 'mismo código de barras', tono: 'bien' },
  identico: { texto: 'idéntico', tono: 'bien' },
  equivalente: { texto: 'equivalente', tono: 'info' },
}

function Nivel({ nivel }: { nivel: string | null }) {
  if (!nivel) return <Etiqueta tono="dato">no lo sé</Etiqueta>
  const conocido = NIVELES[nivel]
  return (
    <Etiqueta tono={conocido?.tono ?? 'dato'} titulo={nivel}>
      {conocido?.texto ?? nivel}
    </Etiqueta>
  )
}

/** Un producto de un par. `producto_a` es `fuente:id_fuente`, y `nombre` puede
 *  ser null: el par se guarda con claves estables y el producto puede haber
 *  desaparecido del catálogo de hoy.
 *
 *  **El enlace mide 44 px de alto.** Medido con la puerta mecanica el 27 de septiembre de 2026,
 *  dentro de la tarjeta de un par medía **21 px**: es la forma de abrir el producto que se está
 *  auditando, y abrir la ficha es justo lo que se hace para comprobar por qué el emparejador
 *  aceptó el par. En la tabla de equivalencias de la ficha del producto ya se midió lo mismo el
 *  23 de septiembre (161 x 19) y se arregló igual. */
function EnlaceProducto({
  clave,
  nombre,
  fuente,
}: {
  clave: string
  nombre: string | null
  fuente: string
}) {
  const id = clave.includes(':') ? clave.slice(clave.indexOf(':') + 1) : clave
  return (
    <>
      {nombre ? (
        <Link
          to={`/producto/${fuente}/${id}`}
          className="inline-flex min-h-[44px] items-center underline"
        >
          {nombre}
        </Link>
      ) : (
        <span className="text-tinta-suave">
          {clave} (ya no está en el catálogo)
        </span>
      )}
      <span className="block text-xs text-tinta-suave">{clave}</span>
    </>
  )
}

/** El servidor de turno no tiene la ruta.
 *
 *  No es un error de la aplicación ni de la red: es una imagen de la API
 *  anterior a que se implementara. Se dice, y se dice cómo se arregla, en vez de
 *  dejar un "algo ha ido mal" que no ayuda a nadie. */
function SinRuta() {
  return (
    <div className="grid grid-cols-1 gap-4">
      <h1 className="text-xl font-bold">Panel de matching</h1>

      <Vacio titulo="Este servidor todavía no tiene esa ruta">
        <p>
          Esta pantalla pide <code>GET /api/panel/matching</code> y la API ha contestado{' '}
          <strong>404</strong>. La ruta está en <code>plataforma/api/main.py</code> desde el 22 de
          septiembre, así que lo más probable es que el contenedor que está corriendo sea anterior
          al cambio:
        </p>
        <p className="mt-1">
          <code>docker compose up -d --build api</code>
        </p>
      </Vacio>

      <Tarjeta titulo="Qué devuelve cuando está">
        <ul className="grid grid-cols-1 gap-1 text-sm">
          <li>· <code>ultima</code>: la ejecución de la última pasada, con versión del modelo, productos y umbral.</li>
          <li>· <code>metricas</code>: cada métrica con su nombre y su valor.</li>
          <li>· <code>cambios</code>: qué se ha movido respecto a la pasada anterior (la medida de estabilidad).</li>
          <li>· <code>pares</code>: una muestra de pares aceptados, con nivel, método, confianza y los rasgos que los sostienen.</li>
          <li>· <code>ejecuciones</code>: todas las pasadas guardadas en <code>data/gold/matching/</code>.</li>
        </ul>
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
          Está en <code>catalogo.matching()</code>. Si al implementarlo cambia el contrato, se cambia
          también <code>src/tipos.ts</code> aquí.
        </p>
      </Tarjeta>

      <Aviso tono="info" titulo="Esta pantalla no valida nada">
        <p>
          No hay botón de aprobar ni de rechazar equivalencias, y no lo va a haber. En este proyecto
          no hay validación humana: el emparejador decide por reglas y se mide solo. Un panel aquí
          sirve para <strong>ver cómo fue la pasada</strong>, no para arreglarla a mano.
        </p>
      </Aviso>

      <p className="text-sm">
        Mientras tanto, los números que sí existen están en{' '}
        <Link to="/panel" className="underline">
          el panel
        </Link>
        .
      </p>
    </div>
  )
}
