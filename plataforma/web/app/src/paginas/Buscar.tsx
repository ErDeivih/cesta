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
import { Mosaico } from '../componentes/Mosaico'
import { TablaResultados } from '../componentes/TablaResultados'
import { VistasGuardadas } from '../componentes/VistasGuardadas'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Vacio } from '../componentes/ui'
import { cuantosFiltros, escribirFiltros, leerFiltros } from '../estado/filtrosUrl'
import {
  MINIMO, apuntaBusqueda, leerBusquedas,
} from '../estado/busquedasRecientes'

/** Tres busquedas de ejemplo, que se pueden pulsar.
 *
 *  Los mismos que ofrecia la interfaz vieja (`app.js:254`), y por el mismo
 *  motivo: este estado vacio es lo primero que ve quien abre la app sin saber
 *  que escribir, y una pantalla que solo dice "escribe algo" deja la primera
 *  busqueda en blanco. Un ejemplo pulsable hace esa primera busqueda por ti y
 *  de paso ensena como se escribe aqui: dos palabras cortas, lo que se compra.
 *
 *  Son tres cosas de uso diario: comprobadas contra la API viva, las tres
 *  llenan la primera pantalla de resultados (40 de 40) y traen comparacion
 *  entre cadenas. Un ejemplo que no encuentre nada es peor que no poner
 *  ejemplos, porque ensena que la app no sirve.
 */
const EJEMPLOS = ['leche entera', 'papel de cocina', 'atún en aceite']

export function Buscar() {
  const [params, setParams] = useSearchParams()
  const filtros = useMemo(() => leerFiltros(params), [params])
  const consulta = params.toString()

  const estado = useEstado()
  const cadenas = useMemo(() => estado.data?.cadenas.map((c) => c.cadena) ?? [], [estado.data])
  const resultados = useBuscar(filtros)

  const [texto, setTexto] = useState(filtros.q)
  const [recientes, setRecientes] = useState<string[]>([])

  // Las ultimas busquedas se leen del aparato al abrir, no del servidor: son de
  // este movil y no tienen por que viajar.
  useEffect(() => {
    setRecientes(leerBusquedas())
  }, [])

  const ponFiltros = (nuevos: FiltrosBuscar) => setParams(escribirFiltros(nuevos), { replace: true })

  /** Quitar los filtros deja el texto y el tope de resultados: lo que se
   *  pregunta sigue siendo lo mismo, solo que sin las trabas. Es la MISMA
   *  accion en la cabecera y en el estado vacio; dos botones con el mismo
   *  nombre que hicieran cosas distintas serian peores que no tener ninguno. */
  const quitarFiltros = () =>
    ponFiltros({ ...FILTROS_VACIOS, q: filtros.q, limite: filtros.limite })

  /** Un ejemplo no lleva a otra pantalla: escribe la busqueda por ti y la lanza.
   *
   *  Se ponen las dos cosas de un tiron -- el texto del campo y la URL -- porque
   *  el texto que se teclea y el que se busca son estados distintos: cambiando
   *  solo la URL, el cuadro se quedaria vacio un instante y el retraso de 250 ms
   *  volveria a buscar la cadena vacia, dejando al que ha pulsado en el mismo
   *  sitio donde estaba. */
  const buscaEjemplo = (ejemplo: string) => {
    setTexto(ejemplo)
    ponFiltros({ ...filtros, q: ejemplo })
    setRecientes(apuntaBusqueda(ejemplo))
  }

  /** Y una busqueda de verdad se recuerda sola, sin pulsar nada.
   *
   *  **Con un segundo de calma a proposito**: el texto que se busca va con 250 ms de
   *  retraso, y eso basta para que al teclear "leche" despacio se guarde tambien
   *  "lech". Un segundo es mas de lo que se tarda en escribir la palabra entera y
   *  menos de lo que se tarda en mirar los resultados, asi que lo que se apunta es lo
   *  que alguien quiso buscar. Y solo si hay resultados: una busqueda que no
   *  encuentra nada no se recuerda, porque volver a pulsarla no ayuda.
   */
  useEffect(() => {
    const q = filtros.q.trim()
    if (q.length < MINIMO || !resultados.data) return
    const t = window.setTimeout(() => setRecientes(apuntaBusqueda(q)), 1000)
    return () => window.clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros.q, resultados.data])

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

  /** Los filtros que pueden estar tapando algo, sin contar el pasillo.
   *
   *  El pasillo no es una traba que se ponga encima de la busqueda: es lo que se
   *  esta mirando. Contarlo como filtro haria que un pasillo vacio ofreciera
   *  "quitar los filtros", que saca de la pantalla en vez de arreglar nada. */
  const filtrosPuestos = puestos - (filtros.seccion ? 1 : 0)

  /** De que se puede hablar en el mensaje de "no hay nada".
   *
   *  Sin texto no se puede decir "nada con «»": era el fallo de la interfaz
   *  vieja (`app.js:322`), que al entrar en un pasillo vacio escribia
   *  literalmente «Nada con «».». */
  const loBuscado = filtros.q.trim() ? `«${filtros.q.trim()}»` : 'este pasillo'

  return (
    <div className="grid grid-cols-1 gap-4">
      <section aria-label="Buscar" className="grid grid-cols-1 gap-3">
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
            <Boton variante="normal" onClick={quitarFiltros}>
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
          {/* Los ejemplos van dentro del estado vacio y no en un sitio aparte:
              es la primera pantalla que ve quien abre la app, y la primera
              busqueda no puede depender de que se te ocurra una palabra. */}
          <p className="mt-3">Busca lo que compras. Por ejemplo:</p>
          <div className="mt-2 flex flex-wrap justify-center gap-2">
            {EJEMPLOS.map((ejemplo) => (
              <Boton key={ejemplo} variante="normal" onClick={() => buscaEjemplo(ejemplo)}>
                {ejemplo}
              </Boton>
            ))}
          </div>

          {/* Y debajo, lo que ya has buscado: la compra se repite cada semana, y
              "leche entera" es la misma busqueda que la de la semana pasada. Se
              guardan en el aparato (ver `estado/busquedasRecientes.ts`), no viajan,
              y van despues de los ejemplos porque un ejemplo siempre encuentra algo
              y una busqueda vieja puede no encontrar nada. */}
          {recientes.length > 0 && (
            <>
              <p className="mt-4 text-xs uppercase tracking-wide text-neutral-500">
                Lo que has buscado
              </p>
              <div className="mt-2 flex flex-wrap justify-center gap-2">
                {recientes.map((q) => (
                  <Boton key={q} variante="sutil" onClick={() => buscaEjemplo(q)}>
                    {q}
                  </Boton>
                ))}
              </div>
            </>
          )}
        </Vacio>
      )}

      {/* Y debajo, lo que se compra: **el mosaico de lo de siempre**, de un toque, y
          si no hay historial -- o el endpoint todavia no esta desplegado -- la
          tarjeta de la primera vez, que ensena la aplicacion funcionando con cuatro
          precios reales. El que decide entre las dos es `Mosaico`, que es el unico
          sitio que sabe si esta persona tiene historial: tener esa decision en dos
          sitios es como acaban pintandose las dos cosas a la vez.

          Va fuera del `Vacio` a proposito: una cuadricula dentro de una caja centrada
          y de texto pequenito se lee mal, y esto es lo primero que se mira. Solo sale
          con el buscador vacio, asi que no se cuela debajo de los resultados. */}
      {!busca && <Mosaico />}

      {busca && resultados.isPending && <Cargando que="el catálogo" />}

      {busca && resultados.isError && (
        <Fallo error={resultados.error} reintentar={() => void resultados.refetch()} />
      )}

      {busca && resultados.data && (
        <>
          {/* Cuando lo escrito no encontraba nada y el servidor lo ha arreglado, se
              dice **que** se ha entendido. Sin esto, quien escribe "asucar" y ve
              resultados de azucar no sabe si la aplicacion le entiende o le esta
              ensenando otra cosa -- y con el tiempo deja de fiarse del buscador. */}
          {resultados.data.corregido && (
            <Aviso tono="info">
              <p>
                No he encontrado <strong>«{filtros.q.trim()}»</strong>. Esto es lo que
                hay para <strong>«{resultados.data.corregido}»</strong>.
              </p>
            </Aviso>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              <strong className="font-semibold text-neutral-900 dark:text-neutral-100">
                {resultados.data.resultados.length}
              </strong>{' '}
              {resultados.data.resultados.length === 1 ? 'resultado' : 'resultados'}
              {filtros.seccion && <> en el pasillo elegido</>}
              <span> · datos del {fecha(resultados.data.fecha_datos)}</span>
            </p>
            {resultados.isFetching && <Etiqueta tono="dato">actualizando…</Etiqueta>}
          </div>

          {resultados.data.resultados.length === 0 ? (
            /* Cero resultados tiene DOS causas y se arreglan de forma distinta:
               cambiar la palabra o quitar los filtros. Con un solo mensaje, quien
               lleva un filtro puesto se queda mirando una pantalla vacia sin
               saber que el problema es suyo -- y el filtro esta plegado, asi que
               es una trampa. Los tres casos son los de la interfaz vieja
               (`app.js:325-332`); el tercero es el pasillo sin texto, donde no
               se puede hablar de "la palabra buscada". */
            filtrosPuestos > 0 ? (
              <Vacio titulo={`Nada en ${loBuscado} con los filtros puestos`}>
                <p>
                  Los filtros de dieta y de oferta se aplican a cada producto que se enseña, no
                  al grupo entero: si el grupo solo cumple por uno de sus miembros, no sale. Un
                  sello exigente deja la lista en nada en cuanto la palabra es amplia.
                </p>
                {/* El boton, aqui mismo: decir cual es el problema y no dar la
                    forma de arreglarlo obliga a subir a buscar el de arriba. */}
                <div className="mt-3">
                  <Boton variante="normal" onClick={quitarFiltros}>
                    Quitar los filtros
                  </Boton>
                </div>
              </Vacio>
            ) : filtros.q.trim() ? (
              <Vacio titulo={`Nada con ${loBuscado}`}>
                <p>
                  Prueba con una palabra más corta, o marca alguna cadena: sin ninguna marcada se
                  usan todas, o tus cadenas de casa si las tienes guardadas.
                </p>
              </Vacio>
            ) : (
              <Vacio titulo="Este pasillo está vacío">
                <p>
                  En las cadenas que miras no hay nada en este pasillo. Prueba a marcar alguna
                  cadena más.
                </p>
              </Vacio>
            )
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
