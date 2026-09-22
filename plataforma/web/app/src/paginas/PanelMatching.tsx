/** El panel de matching: como fue la ultima pasada del emparejador.
 *
 *  `GET /api/panel/matching` **todavia no existe**. Esta pantalla lo pide de
 *  verdad, y cuando contesta 404 dice exactamente eso: "esa ruta aun no esta".
 *  No se pinta un error rojo, porque no es un fallo — es una ruta que falta —,
 *  y tampoco se rellena con numeros de ejemplo, que seria peor.
 *
 *  **Aqui no hay ningun boton de aprobar ni de rechazar, y no lo va a haber.**
 *  En este proyecto no existe la validacion humana: el emparejador decide por
 *  reglas y se mide contra los pares que ya sabemos ciertos por EAN. Una
 *  pantalla de validar equivalencias a mano convertiria un problema de
 *  ingenieria en una tarea de mecanografia, y ademas haria que el resultado no
 *  se pudiera reproducir.
 */
import { Link } from 'react-router-dom'

import { usePanelMatching } from '../api/consultas'
import { esErrorApi } from '../api/cliente'
import { fecha } from '../api/formato'
import { Aviso, Cargando, Etiqueta, Fallo, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

export function PanelMatching() {
  const consulta = usePanelMatching()

  if (consulta.isPending) return <Cargando que="el panel de matching" />

  if (consulta.isError) {
    const e = consulta.error
    const noExiste = esErrorApi(e) && e.estado === 404

    if (!noExiste) {
      return <Fallo error={e} reintentar={() => void consulta.refetch()} />
    }

    return (
      <div className="grid gap-4">
        <h1 className="text-xl font-bold">Panel de matching</h1>

        <Vacio titulo="Todavía no hay endpoint">
          <p>
            Esta pantalla pide <code>GET /api/panel/matching</code> y la API ha contestado{' '}
            <strong>404</strong>: la ruta no existe todavía. No es un fallo del servidor ni de la
            red; es que aún no está escrita.
          </p>
        </Vacio>

        <Tarjeta titulo="Qué debería devolver" sub="Cuando exista, esta pantalla se rellena sola: solo pide y pinta.">
          <ul className="grid gap-1 text-sm">
            <li>· La fecha de la última pasada del emparejador y cuántos productos entraron.</li>
            <li>· Cuántos pares se aceptaron, y con qué método (<code>identico</code>,{' '}
              <code>equivalente</code>).</li>
            <li>· La medida de calidad: los pares que ya sabemos ciertos por EAN se usan como
              respuestas correctas, escondiendo el EAN al algoritmo.</li>
            <li>· Cuántos grupos quedaron de un solo producto, y cuántos comparables (dos cadenas o
              más).</li>
            <li>· Lo que se rechazó y por qué, y por qué se rechazó.</li>
          </ul>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
            La lista está sacada de lo que hoy devuelven los otros paneles
            (<code>/api/panel/hoy</code>, <code>/api/panel/cadenas</code>) y de{' '}
            <code>core/matching.py</code>. Si al implementarlo conviene otro contrato, se cambia en{' '}
            <code>docs/API.md</code> y se cambia aquí.
          </p>
        </Tarjeta>

        <Aviso tono="info" titulo="Esta pantalla no valida nada">
          <p>
            No hay botón de aprobar ni de rechazar equivalencias, y no lo va a haber. Se decidió que
            en este proyecto no hay validación humana: el emparejador decide por reglas y se mide
            solo. Un panel aquí sirve para <strong>ver cómo fue la pasada</strong>, no para
            arreglarla a mano.
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

  const datos = consulta.data ?? {}
  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-bold">Panel de matching</h1>
        {typeof datos['fecha_datos'] === 'string' && (
          <Etiqueta tono="dato">datos del {fecha(datos['fecha_datos'])}</Etiqueta>
        )}
      </div>
      <Aviso tono="info" titulo="El endpoint ya contesta">
        <p>
          Ha llegado una respuesta de <code>/api/panel/matching</code>. Esta pantalla todavía no
          conoce su contrato, así que pinta los números tal cual vienen, sin interpretarlos: mejor
          un dato en crudo que un dato inventado.
        </p>
      </Aviso>
      <Recorrido valor={datos} />
      <details>
        <summary className="cursor-pointer text-sm text-sky-800 dark:text-sky-400">
          Ver la respuesta entera en crudo
        </summary>
        <pre className="mt-1 overflow-x-auto rounded-lg bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
          {JSON.stringify(datos, null, 2)}
        </pre>
      </details>
    </div>
  )
}

/** Un pintor tolerante: escalares en una lista de datos y listas de objetos en
 *  tablas. No intenta adivinar el significado de cada campo, solo enseñarlo. */
function Recorrido({ valor }: { valor: Record<string, unknown> }) {
  const escalares = Object.entries(valor).filter(
    ([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean',
  )
  const listas = Object.entries(valor).filter(
    ([, v]) => Array.isArray(v) && v.length > 0 && typeof v[0] === 'object' && v[0] !== null,
  )
  const objetos = Object.entries(valor).filter(
    ([, v]) => typeof v === 'object' && v !== null && !Array.isArray(v),
  )

  return (
    <div className="grid gap-4">
      {escalares.length > 0 && (
        <Tarjeta titulo="Cifras">
          <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {escalares.map(([k, v]) => (
              <div key={k} className="border-b border-neutral-100 py-0.5 dark:border-neutral-700">
                <dt className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
                  {k}
                </dt>
                <dd className="cifra text-sm font-medium">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </Tarjeta>
      )}

      {listas.map(([k, v]) => {
        const filas = (v as Record<string, unknown>[]).slice(0, 100)
        const columnas = [...new Set(filas.flatMap((f) => Object.keys(f)))]
        return (
          <Tarjeta key={k} titulo={k} sub={`${(v as unknown[]).length} filas`}>
            <TablaScroll etiqueta={k} minAncho="40rem">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    {columnas.map((c) => (
                      <Th key={c}>{c}</Th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filas.map((f, i) => (
                    <tr key={i}>
                      {columnas.map((c) => (
                        <Td key={c} className="cifra">
                          {f[c] === null || f[c] === undefined
                            ? 'no lo sé'
                            : typeof f[c] === 'object'
                              ? JSON.stringify(f[c])
                              : String(f[c])}
                        </Td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>
        )
      })}

      {objetos.map(([k, v]) => (
        <Tarjeta key={k} titulo={k}>
          <pre className="overflow-x-auto rounded-lg bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
            {JSON.stringify(v, null, 2)}
          </pre>
        </Tarjeta>
      ))}
    </div>
  )
}
