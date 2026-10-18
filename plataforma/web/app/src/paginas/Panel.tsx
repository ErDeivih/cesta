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
  useCadenasCerca,
  useEstado,
  useIndice,
  useOfertasDudosas,
  usePanelCadenas,
  usePanelDonde,
  usePanelHistorico,
  usePanelHoy,
  usePanelMarcas,
  usePanelMovidos,
  usePosicion,
  useSecciones,
} from '../api/consultas'
import { euros, eurosUnidad, fecha, nombreCadena, numero, porcentaje, porcentajeConSigno } from '../api/formato'
import { GraficoIndice } from '../componentes/GraficoIndice'
import { LoQueHasPagado } from '../componentes/LoQueHasPagado'
import { Aviso, Cargando, Dato, Etiqueta, Fallo, Selector, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

const PESTANAS = [
  { clave: 'hoy', texto: 'Hoy' },
  // **«Dónde comprar» va la primera de las de análisis, y es una decision.** El dueno
  // pidio el 25 de septiembre de 2026 *"datos mas claros para elegir donde comprar o
  // donde comprar cada producto"*: la pregunta que se hace de verdad es esa, no la del
  // indice. Las otras cuatro tablas siguen ahi, detras, para quien quiera el detalle.
  { clave: 'donde', texto: 'Dónde comprar' },
  { clave: 'cadenas', texto: 'Cadenas' },
  { clave: 'marcas', texto: 'Marcas' },
  { clave: 'historico', texto: 'Histórico' },
  { clave: 'movidos', texto: 'Movidos' },
  { clave: 'bajadas', texto: 'Bajadas' },
  // Las tres que faltaban respecto de la interfaz vieja (`app.js:762-768`):
  // `indice` y `posicion` son las que contestan "¿en que soy caro?" y "¿a que
  // ritmo se mueve el nivel de precios?", y `dudosas` es el verificador de
  // ofertas. Eran las tres pantallas que hacian que el panel nuevo no pudiera
  // sustituir al viejo.
  { clave: 'indice', texto: 'Índice' },
  { clave: 'posicion', texto: 'Posición' },
  { clave: 'dudosas', texto: 'Ofertas dudosas' },
] as const

type Clave = (typeof PESTANAS)[number]['clave']

/** Las pestanas en las que "¿de que cadenas hablamos?" significa algo.
 *
 *  En las de un solo dato global (hoy, marcas, historico) filtrar por cadena no
 *  tendria sentido: no hay desglose por cadena que recortar. */
const CON_FILTRO: Clave[] = ['indice', 'posicion', 'dudosas', 'bajadas']

export function Panel() {
  const [params, setParams] = useSearchParams()
  const crudo = params.get('pestana')
  const activa: Clave = (PESTANAS.find((p) => p.clave === crudo)?.clave ?? 'hoy') as Clave

  // **El filtro por cadenas cercanas, que era el otro hueco de esta pantalla.**
  // `Panel.tsx` llamaba a `useBajadas(dias, subidas, [])` con la lista vacia y
  // ninguna pestana leia `cadenas_cerca`: las cinco cadenas pesaban lo mismo
  // aunque en la calle solo haya dos. El valor por defecto son las que la persona
  // tiene puestas en Ajustes, y la UI dice **de donde sale** el filtro: sin eso,
  // quien ve tres cadenas y no las cinco no sabe si faltan datos o si es su ajuste.
  const cercanas = useCadenasCerca()
  const estado = useEstado()
  const crudoCadenas = params.get('cadenas')
  const puestas =
    crudoCadenas === 'todas'
      ? []
      : crudoCadenas
        ? crudoCadenas.split(',').filter(Boolean)
        : cercanas
  const dePreferencias = crudoCadenas === null && cercanas.length > 0
  const cambiaCadenas = (sel: string[]) =>
    setParams(
      { ...Object.fromEntries(params), cadenas: sel.length ? [...sel].sort().join(',') : 'todas' },
      { replace: true },
    )
  const alternaCadena = (c: string) =>
    cambiaCadenas(puestas.includes(c) ? puestas.filter((x) => x !== c) : [...puestas, c])

  return (
    <div className="flex min-h-full flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-bold">Panel</h2>
        <Link
          to="/panel/matching"
          className="inline-flex min-h-[44px] min-w-[44px] items-center text-cuerpo underline"
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
              'min-h-[44px] rounded-campo border px-3 py-1 text-cuerpo font-medium ' +
              (activa === p.clave
                ? 'border-terracota bg-terracota text-papel '
                : 'border-borde bg-papel hover:bg-marfil dark:hover:bg-papel')
            }
          >
            {p.texto}
          </button>
        ))}
      </div>

      {CON_FILTRO.includes(activa) && (
        <FiltroCadenas
          conocidas={(estado.data?.cadenas ?? []).map((c) => c.cadena)}
          puestas={puestas}
          dePreferencias={dePreferencias}
          alterna={alternaCadena}
          todas={() => cambiaCadenas([])}
        />
      )}

      {activa === 'hoy' && <Hoy />}
      {activa === 'donde' && <DondeComprar />}
      {activa === 'cadenas' && <Cadenas />}
      {activa === 'marcas' && <Marcas />}
      {activa === 'historico' && <Historico />}
      {activa === 'movidos' && <Movidos />}
      {activa === 'bajadas' && <Bajadas cadenas={puestas} />}
      {activa === 'indice' && <Indice cadenas={puestas} />}
      {activa === 'posicion' && <Posicion cadenas={puestas} />}
      {activa === 'dudosas' && <Dudosas cadenas={puestas} />}
    </div>
  )
}

/** El filtro de cadenas del panel: **de que cadenas habla esta pantalla**.
 *
 *  Por defecto, las que la persona tiene cerca (`Ajustes` → `cadenas_cerca`), y se
 *  dice en voz alta para que nadie crea que faltan datos. Un toque por cadena y un
 *  atajo para volver a las cinco. Objetivos de 44 px porque esto se usa de pie.
 */
function FiltroCadenas({
  conocidas,
  puestas,
  dePreferencias,
  alterna,
  todas,
}: {
  conocidas: string[]
  puestas: string[]
  dePreferencias: boolean
  alterna: (cadena: string) => void
  todas: () => void
}) {
  const sinFiltro = puestas.length === 0
  return (
    <div className="grid gap-1">
      <p className="text-etiqueta text-tinta-suave">
        {sinFiltro
          ? 'Mirando las cinco cadenas.'
          : dePreferencias
            ? 'Mirando solo las cadenas que tienes cerca, las de Ajustes.'
            : 'Mirando solo estas cadenas.'}
      </p>
      <div className="flex flex-wrap gap-1">
        {(conocidas.length ? conocidas : puestas).map((c) => (
          <button
            key={c}
            type="button"
            aria-pressed={puestas.includes(c)}
            onClick={() => alterna(c)}
            className={
              'inline-flex min-h-[44px] items-center rounded-full border px-3 text-cuerpo font-medium ' +
              (puestas.includes(c)
                ? 'border-terracota bg-terracota text-papel '
                : 'border-borde bg-papel hover:bg-marfil dark:hover:bg-papel')
            }
          >
            {nombreCadena(c)}
          </button>
        ))}
        <button
          type="button"
          aria-pressed={sinFiltro}
          onClick={todas}
          className={
            'inline-flex min-h-[44px] items-center rounded-full border px-3 text-cuerpo font-medium ' +
            (sinFiltro
              ? 'border-terracota bg-terracota text-papel '
              : 'border-borde bg-papel hover:bg-marfil dark:hover:bg-papel')
          }
        >
          Todas
        </button>
      </div>
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
            {/* **«Ingesta» significa dos cosas** y aquí sólo vale una: lo que el raspador trajo al
                catálogo, no lo que come nadie. *El rótulo decía «La ingesta de hoy» dentro de
                «Gasto y ahorro», y se leía como «lo que has comido hoy» -- justo la confusion
                entre Compra y Calorias que hay que evitar.* G06, punto 157: mensajes ambiguos. */}
            <h2 className="text-entrada font-semibold">Lo que entró hoy en el catálogo</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          {d.alarmas.length > 0 && (
            <Aviso tono="mal" titulo="Alarmas">
              <ul className="mt-1 grid gap-1">
                {d.alarmas.map((a) => (
                  <li key={a.cadena}>
                    <strong>{nombreCadena(a.cadena)}</strong>: hoy {numero(a.hoy, 0)} productos, y lo normal son{' '}
                    {numero(a.lo_normal, 0)} ({porcentaje(a.caida_pct)} menos). Una caída así sin un
                    cambio de alcance detrás suele ser algo roto.
                  </li>
                ))}
              </ul>
            </Aviso>
          )}

          {/* **Primero el dinero.** La pagina se llama «Gasto y ahorro» y hasta hoy no
              tenia gasto: sus secciones eran todas del catalogo. Lo que has pagado sale de
              las compras que cerraste, y va con su cobertura -- *cuantas lineas se quedaron
              sin precio* --, porque un total parcial sin su aviso es una mentira por
              omision. */}
          <LoQueHasPagado />

          <Tarjeta titulo="Qué entró por cadena" sub="Sobre cuántos productos se ha contado cada cosa">
            <TablaScroll etiqueta="Productos por cadena" minAncho="40rem">
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td>{nombreCadena(c.cadena)}</Td>
                      <Td className="cifra" etiqueta="productos">{numero(c.productos, 0)}</Td>
                      <Td className="cifra" etiqueta="comparables">{numero(c.comparables, 0)}</Td>
                      <Td className="cifra" etiqueta="con Nutri-Score">{numero(c.con_nutriscore, 0)}</Td>
                      <Td className="cifra" etiqueta="con EAN">{numero(c.con_ean, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta titulo="Precios movidos hoy">
            <ul className="grid grid-cols-1 gap-1 text-cuerpo sm:grid-cols-2 lg:grid-cols-3">
              {d.movidos.map((m) => (
                <li key={m.cadena} className="flex justify-between gap-2 border-b border-borde py-1 ">
                  <span className="font-medium">{nombreCadena(m.cadena)}</span>
                  <span className="cifra">
                    <span className="text-bien ">
                      {numero(m.bajadas, 0)} ↓
                    </span>{' '}
                    <span className="text-error ">{numero(m.subidas, 0)} ↑</span>
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

/** **Dónde comprar**: la pantalla que contesta la pregunta del dueño.
 *
 *  *"Cosas mejor explicadas, o datos más claros para elegir dónde comprar o dónde comprar
 *  cada producto"* (25 de septiembre de 2026). Tres decisiones, y las tres son para que
 *  esto se pueda usar de verdad:
 *
 *  1. **Se mide sobre los mismos productos.** Para cada producto comparable, el desvío
 *     respecto a la mediana de las OTRAS cadenas de su grupo, y luego la mediana de esos
 *     desvíos. Comparar la cesta media de cada cadena no vale: cada una tiene su catálogo y
 *     quien tiene más productos caros parece más caro aunque en lo que comparten sea más
 *     barato.
 *  2. **Se dice lo que no se puede decir.** Esta pantalla no dice cuál es la cadena más
 *     barata en total, porque con estos datos no se puede. Lo que sí dice es en cuántos
 *     pasillos gana cada una.
 *  3. **Se dice cuánto separa al ganador del siguiente**, porque un pasillo donde la
 *     diferencia es de medio punto no decide nada, y decir "compra aquí" ahí sería mentir
 *     con un número.
 */
function DondeComprar() {
  const consulta = usePanelDonde()
  return (
    <Bloque consulta={consulta} titulo="dónde comprar">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-entrada font-semibold">Dónde hacer la compra</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          <Aviso tono="info" titulo="Cómo se mide esto, y qué no dice">
            <p>
              Para cada producto que está en dos o más cadenas se mira cuánto se desvía cada
              una respecto a la mediana de <strong>las otras</strong> de su grupo, y del
              pasillo se enseña la mediana de esos desvíos. Al ser el mismo producto en los
              dos lados de la resta, el número <strong>no depende del surtido</strong>: no
              premia a quien tiene menos productos caros.
            </p>
            <p className="mt-1">
              Lo que <strong>no</strong> dice: cuál es la cadena más barata en total. Eso no
              se puede saber con estos datos, porque cada cadena vende su catálogo. Lo que sí
              se puede contar es en cuántos pasillos gana cada una, y eso está abajo.
            </p>
            <p className="mt-1 text-etiqueta">
              {d.medida}. Solo se enseñan los pasillos con {d.minimo_por_celda} productos o
              más por cadena: con menos, la mediana es el ruido de dos o tres fichas.
            </p>
          </Aviso>

          <Tarjeta
            titulo="Quién gana en cada pasillo"
            sub={`${d.pasillos_totales} pasillos con productos comparables de dos cadenas o más`}
          >
            <TablaScroll etiqueta="Quién gana en cada pasillo" minAncho="44rem">
              <table className="w-full border-collapse text-cuerpo">
                <thead>
                  <tr>
                    <Th>Pasillo</Th>
                    <Th>Más barata</Th>
                    <Th>Desvio</Th>
                    <Th>Le sigue</Th>
                    <Th>Diferencia</Th>
                    <Th>Más cara</Th>
                    <Th>Productos</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.pasillos.map((p) => (
                    <tr key={p.seccion}>
                      <Td>{p.nombre}</Td>
                      <Td className="font-semibold" etiqueta="más barata">{nombreCadena(p.gana)}</Td>
                      <Td className="cifra" etiqueta="desvío">{porcentajeConSigno(p.desvio_pct)}</Td>
                      <Td etiqueta="le sigue">{p.siguiente ? nombreCadena(p.siguiente) : '—'}</Td>
                      <Td className="cifra" etiqueta="diferencia">
                        {p.ventaja_sobre_la_siguiente_pct == null
                          ? '—'
                          : `${porcentaje(p.ventaja_sobre_la_siguiente_pct)} pts`}
                      </Td>
                      <Td etiqueta="más cara">
                        {nombreCadena(p.peor)}{' '}
                        <span className="cifra text-tinta-suave">
                          {porcentajeConSigno(p.peor_pct)}
                        </span>
                      </Td>
                      <Td className="cifra" etiqueta="productos">{numero(p.productos, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
            <p className="mt-2 text-etiqueta text-tinta-suave">
              «Desvio» es cuánto se separa del resto del pasillo, en porcentaje: negativo es
              más barata. «Diferencia» es cuánto le saca a la siguiente; cuando es de medio
              punto, ese pasillo no decide nada.
            </p>
          </Tarjeta>

          <Tarjeta
            titulo="Cuántos pasillos gana cada cadena"
            sub="Contar pasillos ganados es lo único que se puede comparar entre catálogos distintos"
          >
            <ul className="grid gap-2">
              {d.victorias.map((v) => (
                <li key={v.cadena} className="flex items-baseline gap-3">
                  <span className="min-w-[7rem] font-medium">{nombreCadena(v.cadena)}</span>
                  <span className="cifra text-lg font-semibold">{v.pasillos}</span>
                  <span className="text-cuerpo text-tinta-suave">
                    de {d.pasillos_totales} pasillos
                    {d.pasillos_totales > 0 && (
                      <> ({porcentaje((100 * v.pasillos) / d.pasillos_totales, 0)})</>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </Tarjeta>

          <Tarjeta
            titulo="Dónde comprar cada producto"
            sub={`Los ${d.oportunidades.productos.length} productos donde más se nota, de mayor a menor diferencia`}
          >
            <p className="mb-2 text-cuerpo text-tinta-suave">{d.oportunidades.filtros}.</p>
            <p className="mt-2 text-cuerpo text-tinta-suave">
              La diferencia es entre la cadena mas barata y la mas cara de cada grupo, y los
              dos extremos se ven en la tabla con su cadena: pueden ser articulos distintos -- mismo
              envase y misma marca si, pero cada uno con su EAN. No es el ahorro de uno solo.
            </p>
            <TablaScroll etiqueta="Productos donde más se nota" minAncho="44rem">
              <table className="w-full border-collapse text-cuerpo">
                <thead>
                  <tr>
                    <Th>Producto</Th>
                    <Th>Más barato en</Th>
                    <Th>Precio</Th>
                    <Th>Más caro en</Th>
                    <Th>Precio</Th>
                    <Th>Diferencia</Th>
                  </tr>
                </thead>
                <tbody>
                  {d.oportunidades.productos.slice(0, 20).map((p) => (
                    <tr key={p.grupo_id}>
                      <Td>
                        <Link to={`/grupo/${p.grupo_id}`} className="underline">
                          {p.nombre}
                        </Link>
                      </Td>
                      <Td className="font-semibold">{nombreCadena(p.mas_barata)}</Td>
                      <Td className="cifra">
                        {eurosUnidad(p.precio_cent, p.unidad)}
                      </Td>
                      <Td>{nombreCadena(p.mas_cara)}</Td>
                      <Td className="cifra">{eurosUnidad(p.precio_caro_cent, p.unidad)}</Td>
                      <Td className="cifra font-semibold">
                        {eurosUnidad(p.diferencia_cent, p.unidad)}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
            <p className="mt-2 text-etiqueta text-tinta-suave">
              Precio por unidad canónica (kilo, litro o unidad), no el del envase: es la única
              forma de comparar un bote de 400 g con uno de 1 kg. La ficha de cada uno dice
              además los precios de las cinco cadenas, y la lista permite ponerlo en la tienda
              que quieras.
            </p>
          </Tarjeta>

          <Tarjeta titulo="El detalle, cadena por cadena" sub="Para ver quién está segundo y por cuánto">
            {d.pasillos.slice(0, 8).map((p) => (
              <div key={p.seccion} className="mb-3">
                <p className="text-cuerpo font-medium">{p.nombre}</p>
                <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-cuerpo">
                  {p.cadenas.map((c) => (
                    <li key={c.cadena}>
                      {nombreCadena(c.cadena)}{' '}
                      <span className="cifra">{porcentajeConSigno(c.desvio_pct)}</span>{' '}
                      <span className="text-etiqueta text-tinta-suave">
                        ({numero(c.productos, 0)})
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
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
            <h2 className="text-entrada font-semibold">Quién gana y cuánto se mueve</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          <Tarjeta
            titulo="Quién es más barato"
            sub={`Sobre ${numero(d.dispersion.grupos, 0)} grupos con dos cadenas o más`}
          >
            <TablaScroll etiqueta="Quién es más barato" minAncho="34rem">
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td>{nombreCadena(c.cadena)}</Td>
                      <Td className="cifra" etiqueta="compite en">{numero(c.compite_en, 0)}</Td>
                      <Td className="cifra" etiqueta="gana">{numero(c.gana, 0)}</Td>
                      <Td className="cifra font-semibold" etiqueta="de las veces que gana">{porcentaje(c.pct)}</Td>
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
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td>{nombreCadena(m.cadena)}</Td>
                      <Td className="cifra" etiqueta="observaciones">{numero(m.observaciones, 0)}</Td>
                      <Td className="cifra" etiqueta="movidos">{numero(m.movidos, 0)}</Td>
                      {/* **La etiqueta no puede ser «%»**: el valor ya lleva su «%», y en el
                          móvil se leia «% 69,4 %». La etiqueta dice de que es el porcentaje, que
                          es lo unico que la cabecera daba y la fila apilada no tiene. Medido en
                          la captura de `/panel?pestana=cadenas` el 28 de septiembre de 2026. */}
                      <Td className="cifra" etiqueta="de las observaciones">{porcentaje(m.pct, 2)}</Td>
                      <Td className="cifra" etiqueta="mediana">{euros(m.mediana_cent)}</Td>
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
            <p className="mt-2 text-etiqueta text-tinta-suave">
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
            <h2 className="text-entrada font-semibold">Marca propia contra marca</h2>
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
              <p className="mt-2 text-etiqueta text-tinta-suave">
                Con tan pocos grupos, esto es una pista y no una conclusión. La muestra es pequeña
                porque son pocas las cadenas que publican ingredientes.
              </p>
            )}
          </Tarjeta>

          <Tarjeta titulo="De dónde salen las letras de calidad">
            <TablaScroll etiqueta="Origen de las letras de calidad" minAncho="24rem">
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td className="cifra" etiqueta="productos">{numero(o.productos, 0)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaScroll>
          </Tarjeta>

          <Tarjeta titulo="Marcas propias con más productos">
            <ul className="grid grid-cols-1 gap-1 text-cuerpo sm:grid-cols-2 lg:grid-cols-3">
              {d.marcas_propias.map((m) => (
                <li key={`${m.cadena}-${m.marca}`} className="flex justify-between gap-2 border-b border-borde py-1 ">
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
            <h2 className="text-entrada font-semibold">
              {numero(d.dias, 0)} {d.dias === 1 ? 'día guardado' : 'días guardados'}
            </h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          <Tarjeta titulo="Lo que se desbloquea cuando haya más días">
            <ul className="grid grid-cols-1 gap-2 text-cuerpo">
              {d.pendientes.map((p) => (
                <li key={p.que} className="flex flex-wrap items-baseline justify-between gap-2 border-b border-borde py-1 ">
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
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td className="cifra" etiqueta="observaciones">{numero(s.observaciones, 0)}</Td>
                      <Td className="cifra" etiqueta="cadenas">{numero(s.cadenas, 0)}</Td>
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
            <h2 className="text-entrada font-semibold">Lo que se ha movido hoy</h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>
          {d.movidos.length === 0 ? (
            <Vacio titulo="Hoy no se ha movido nada" className="grow" />
          ) : (
            <TablaScroll etiqueta="Precios movidos hoy" minAncho="44rem">
              <table className="w-full border-collapse text-cuerpo">
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
                          <span className="block text-etiqueta text-tinta-suave">
                            {m.marca}
                          </span>
                        )}
                      </Td>
                      <Td>{nombreCadena(m.cadena)}</Td>
                      <Td className="cifra">{eurosUnidad(m.precio_unidad_cent, m.unidad)}</Td>
                      <Td className="cifra">
                        <span
                          className={
                            m.baja
                              ? 'font-semibold text-bien '
                              : 'font-semibold text-error '
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

function Bajadas({ cadenas }: { cadenas: string[] }) {
  const [params, setParams] = useSearchParams()
  const dias = Number(params.get('dias') ?? '7') || 7
  const subidas = params.get('subidas') === 'true'
  // "Solo lo mio" contesta a la cuarta de las cuatro preguntas con las que se abre
  // la aplicacion: *"¿ha bajado algo de lo mio?"*. Va en la direccion como los otros
  // filtros: asi se puede volver a lo mismo con el boton de atras y compartirlo.
  const soloMios = params.get('mios') === 'true'
  // **Las cadenas que el panel tiene puestas, no una lista vacia.** Estaba aqui
  // `[]` a mano (el hueco que apunto `BACKLOG.md` §0.8): la pestana que contesta
  // "¿ha bajado algo de lo mio?" enseñaba el catalogo entero de las cinco cadenas
  // aunque en la calle haya dos.
  const consulta = useBajadas(dias, subidas, cadenas, soloMios)
  const alterna = (clave: string, valor: string) =>
    setParams({ ...Object.fromEntries(params), [clave]: valor }, { replace: true })

  return (
    <Bloque consulta={consulta} titulo="las bajadas">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-end gap-3">
            {/* El titulo y el vacio dicen **lo que el servidor ha hecho**, no lo que se
                le ha pedido: `d.solo_mios` es "he filtrado por lo tuyo" y la peticion
                puede quedarse sin efecto -- sin sesion no hay "lo mio" --. Con lo que
                se pidio, la pantalla ensenaria el catalogo entero bajo el titulo "Lo
                tuyo que ha bajado". Lo encontro la verificacion contra un PostgreSQL de
                verdad; el boton sigue diciendo lo que has pedido, que eso es un mando. */}
            <h2 className="text-entrada font-semibold">
              {d.solo_mios ? 'Lo tuyo que ha' : 'Lo que más ha'}{' '}
              {subidas ? 'subido' : 'bajado'} en {numero(d.dias, 0)} días
            </h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
            <Selector
              etiqueta="Ventana"
              value={String(dias)}
              onChange={(e) => alterna('dias', e.target.value)}
            >
              <option value="1">1 día</option>
              <option value="7">7 días</option>
              <option value="30">30 días</option>
              <option value="90">90 días</option>
            </Selector>
            <button
              type="button"
              aria-pressed={subidas}
              onClick={() => alterna('subidas', subidas ? 'false' : 'true')}
              className="min-h-[44px] rounded-campo border border-borde bg-papel px-3 text-cuerpo font-medium "
            >
              Ver las subidas
            </button>
            {/* El boton que separa "todo el catalogo" de "lo mio". Sin el, esta
                pantalla contesta "¿que ha bajado?" -- que no es la pregunta: la
                pregunta es "¿ha bajado algo de lo mio?". */}
            <button
              type="button"
              aria-pressed={soloMios}
              onClick={() => alterna('mios', soloMios ? 'false' : 'true')}
              className="min-h-[44px] rounded-campo border border-borde bg-papel px-3 text-cuerpo font-medium "
            >
              {soloMios ? 'Ver todo el catálogo' : 'Solo lo mío'}
            </button>
          </div>

          {d.resultados.length === 0 ? (
            /* Dos vacios distintos, y decir el mismo texto en los dos seria
               mentir en uno: "nada ha bajado" no es lo mismo que "de lo tuyo no
               ha bajado nada", y la segunda tiene arreglo (apuntar cosas en una
               lista o en favoritos), que es lo que hay que decir. Y se elige por
               `d.solo_mios`, que es lo que el servidor ha hecho de verdad. */
            d.solo_mios ? (
              <Vacio titulo={`Nada de lo tuyo ha ${subidas ? 'subido' : 'bajado'} en ${d.dias} días`} className="grow">
                <p>
                  Este filtro mira lo que tienes en tus listas y en favoritos. Si
                  apuntas la compra, la próxima vez esto contesta solo.
                </p>
              </Vacio>
            ) : (
              <Vacio titulo={`Nada ha ${subidas ? 'subido' : 'bajado'} en ${d.dias} días`} className="grow" />
            )
          ) : (
            <TablaScroll etiqueta="Cambios de precio" minAncho="46rem">
              <table className="w-full border-collapse text-cuerpo">
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
                      <Td>{nombreCadena(b.cadena)}</Td>
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

/* ------------------------------------------------------------ el indice ----
   "¿A que ritmo se mueve el nivel de precios?" no se contesta con una lista de
   ofertas: un yogur que baja no dice nada del nivel. El indice encadenado compara
   **el mismo producto consigo mismo** contra la captura anterior de esa cadena, asi
   que no se mueve porque cambie el surtido -- que es el error clasico de una cesta
   fija mal hecha. Lo que no se puede leer de un indice, y por eso va todo junto:
   cuantos productos sostienen cada eslabon, cuantos relativos se recortaron y
   cuantas capturas hay.
*/
function Indice({ cadenas }: { cadenas: string[] }) {
  const consulta = useIndice()
  return (
    <Bloque consulta={consulta} titulo="el índice">
      {(d) => {
        const series = cadenas.length
          ? d.series.filter((s) => cadenas.includes(s.cadena))
          : d.series
        if (series.length === 0) {
          return (
            <Vacio titulo="Ninguna de esas cadenas tiene índice todavía" className="grow">
              <p>El índice necesita dos capturas de la misma cadena para empezar a moverse.</p>
            </Vacio>
          )
        }
        const orden = [...series].sort((a, b) => a.variacion_pct - b.variacion_pct)
        const baja = orden[0]
        const sube = orden[orden.length - 1]
        const capturas = Math.max(...series.map((s) => s.capturas))
        const recortados = series.reduce(
          (t, s) => t + (s.puntos[s.puntos.length - 1]?.recortados ?? 0),
          0,
        )
        // Si alguna cadena tiene un eslabon que cubre mas de un dia, se enseña: el indice esta
        // encadenado dia a dia y esos dias no se rastrearon.
        const haySaltos = series.some((s) => s.puntos.some((p) => (p.dias_del_salto ?? 1) > 1))
        return (
          <div className="grid grid-cols-1 gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-entrada font-semibold">El nivel de precios de cada cadena</h2>
              <SelloFecha fechaDatos={d.fecha_datos} />
            </div>

            {/* La frase primero: el dato que se lee de un vistazo. Y con la
                advertencia pegada, porque un +0,3 % en catorce capturas es una
                tendencia, no un chollo ni una catastrofe. */}
            <p className="font-semibold">
              {baja.cadena === sube.cadena
                ? `Solo hay una cadena en el gráfico: ${nombreCadena(baja.cadena)}, ${porcentajeConSigno(baja.variacion_pct)} desde la primera captura.`
                : `${nombreCadena(baja.cadena)} es quien más ha bajado (${porcentajeConSigno(baja.variacion_pct)}) y ${nombreCadena(sube.cadena)} quien más ha subido (${porcentajeConSigno(sube.variacion_pct)}) en ${numero(capturas, 0)} capturas.`}
            </p>
            <p className="text-cuerpo text-tinta-suave">
              Son décimas: en unas semanas un catálogo entero no se mueve mucho, y el valor está en
              la tendencia, no en el día.
            </p>

            <Tarjeta titulo="Índice encadenado" sub={`${d.base} · ${d.metodo}`}>
              <GraficoIndice series={series} />
            </Tarjeta>

            <Tarjeta titulo="Los números" sub="La tabla no es un extra: el color de cinco series no se distingue, y el dato no puede depender de verlo bien">
              <TablaScroll etiqueta="Índice de precios por cadena" minAncho="34rem">
                <table className="w-full border-collapse text-cuerpo">
                  <thead>
                    <tr>
                      <Th>Cadena</Th>
                      <Th>Índice</Th>
                      <Th>Variación</Th>
                      <Th>Capturas</Th>
                      <Th>Productos</Th>
                      {haySaltos && <Th>Salto</Th>}
                      {recortados > 0 && <Th>Recortados</Th>}
                    </tr>
                  </thead>
                  <tbody>
                    {orden.map((s) => {
                      const u = s.puntos[s.puntos.length - 1]
                      return (
                        <tr key={s.cadena}>
                          <Td>{nombreCadena(s.cadena)}</Td>
                          <Td className="cifra" etiqueta="índice">{numero(s.indice, 2)}</Td>
                          <Td className="cifra font-semibold" etiqueta="variación">
                            {porcentajeConSigno(s.variacion_pct, 2)}
                          </Td>
                          <Td className="cifra" etiqueta="capturas">{numero(s.capturas, 0)}</Td>
                          <Td className="cifra" etiqueta="productos">{numero(u?.productos, 0)}</Td>
                          {recortados > 0 && (
                            <Td className="cifra" etiqueta="recortados">
                              {numero(u?.recortados, 0)}
                            </Td>
                          )}
                          {/* **Los dias que cubre el eslabon mas largo de esa cadena.** El indice
                              esta encadenado dia a dia, y donde la cadena no se rastreo un dia el
                              eslabon salta: la columna sale solo cuando hay algun salto (como
                              «Recortados») y dice cual es el peor de cada cadena. `dias_del_salto`
                              viajaba en `/api/indice` y **no lo pintaba nadie**: el dibujo hacia
                              como si hubiera visto todos los dias. */}
                          {haySaltos && (
                            <Td className="cifra" etiqueta="salto">
                              {numero(Math.max(...s.puntos.map((p) => p.dias_del_salto ?? 1)), 0)}
                            </Td>
                          )}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </TablaScroll>
              {recortados > 0 && (
                <p className="mt-2 text-etiqueta text-tinta-suave">
                  «Recortados» son los relativos fuera del rango creíble: el índice no los usa. Si
                  fueran muchos, ese eslabón sería flojo y el índice estaría midiendo otra cosa.
                </p>
              )}
              {haySaltos && (
                <p className="mt-2 text-etiqueta text-tinta-suave">
                  «Salto» son los días que cubre el eslabón más largo de esa cadena. Donde pasa de
                  1, la cadena no se rastreó ese día y el índice se movió sin haberlo visto: de esa
                  semana se lee la tendencia, no el día.
                </p>
              )}
            </Tarjeta>
          </div>
        )
      }}
    </Bloque>
  )
}

/* ----------------------------------------------------------- la posicion ----
   La pregunta util no es "¿quien es mas barato?" sino **"¿en que soy caro?"**.
   Una cadena puede ir un 20 % por debajo en lacteos y un 25 % por encima en
   pescaderia, y la media de las dos no se parece a ninguna. Se ordena por cuanto
   se separan las cadenas dentro de la seccion: donde estan empatadas, elegir
   tienda no cambia el ticket y esa seccion no tiene por que abrir la pantalla.
*/
function Posicion({ cadenas }: { cadenas: string[] }) {
  const consulta = usePosicion()
  // Los nombres de las secciones vienen de `/secciones`, que ya esta en cache
  // porque lo pide el buscador: aqui solo se traducen. Un slug que no este se
  // enseña tal cual, que es mejor que esconderlo.
  const secciones = useSecciones([])
  const nombre = (s: string) =>
    secciones.data?.secciones.find((x) => x.seccion === s)?.nombre ?? s

  return (
    <Bloque consulta={consulta} titulo="la posición">
      {(d) => {
        const visibles = d.secciones
          .map((s) => ({ ...s, cadenas: cadenas.length ? s.cadenas.filter((c) => cadenas.includes(c.cadena)) : s.cadenas }))
          .filter((s) => s.cadenas.length > 0)
        if (visibles.length === 0) {
          return (
            <Vacio titulo="Todavía no hay secciones comparables" className="grow">
              <p>
                Esto se llena cuando la cadena publica la sección y hay grupos con dos cadenas o más.
              </p>
            </Vacio>
          )
        }
        const horquilla = (s: (typeof visibles)[number]) => {
          const v = s.cadenas.map((c) => c.desvio_pct)
          return v.length > 1 ? Math.max(...v) - Math.min(...v) : 0
        }
        const orden = [...visibles].sort((a, b) => horquilla(b) - horquilla(a))
        const tope = Math.max(...visibles.flatMap((s) => s.cadenas.map((c) => Math.abs(c.desvio_pct))), 5)
        return (
          <div className="grid grid-cols-1 gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-entrada font-semibold">En qué es cara cada cadena</h2>
              <SelloFecha fechaDatos={d.fecha_datos} />
            </div>
            <p className="text-cuerpo text-tinta-suave">
              Cada cadena contra <strong>las otras</strong> dentro de cada grupo de productos
              equivalentes. No es el precio medio de la sección: eso mediría el surtido, no el
              precio. Ordenado por cuánto se separan las cadenas: donde están empatadas, elegir
              tienda no cambia nada.
            </p>

            {orden.map((s) => (
              <Tarjeta
                key={s.seccion}
                titulo={nombre(s.seccion)}
                sub={
                  horquilla(s) > 0
                    ? `${numero(s.productos, 0)} productos emparejados · ${numero(horquilla(s), 1)} puntos entre la más barata y la más cara`
                    : `${numero(s.productos, 0)} productos emparejados · aquí están empatadas`
                }
              >
                <ul className="grid gap-2">
                  {[...s.cadenas]
                    .sort((a, b) => a.desvio_pct - b.desvio_pct)
                    .map((c) => {
                      const ancho = 50 * Math.min(1, Math.abs(c.desvio_pct) / tope)
                      const caro = c.desvio_pct > 0
                      return (
                        <li
                          key={c.cadena}
                          className="grid grid-cols-[5.5rem_1fr_3.5rem] items-center gap-2 text-etiqueta"
                        >
                          <span className="truncate font-medium">{nombreCadena(c.cadena)}</span>
                          {/* Barra a los dos lados del cero: a la izquierda lo que
                              está por debajo de las demás, a la derecha lo que está
                              por encima. El número va fuera de la barra, siempre
                              visible, porque es el dato. */}
                          <span className="relative block h-3 w-full rounded bg-marfil ">
                            <span
                              aria-hidden
                              className="absolute inset-y-0 left-1/2 w-px bg-borde "
                            />
                            <span
                              aria-hidden
                              className={
                                'absolute inset-y-0 rounded ' +
                                (caro ? 'bg-error ' : 'bg-bien ')
                              }
                              style={
                                caro
                                  ? { left: '50%', width: `${ancho}%` }
                                  : { right: '50%', width: `${ancho}%` }
                              }
                            />
                          </span>
                          <span
                            className={
                              'cifra text-right font-semibold ' +
                              (caro
                                ? 'text-error '
                                : 'text-bien ')
                            }
                          >
                            {porcentajeConSigno(c.desvio_pct)}
                          </span>
                        </li>
                      )
                    })}
                </ul>
              </Tarjeta>
            ))}

            <Aviso tono="info">
              El desvío se mide <strong>solo sobre lo emparejado y con la misma unidad</strong>: cada
              producto contra la mediana de ese mismo producto en las otras cadenas. Un ±5 % con
              pocos productos es una pista, no una conclusión.
            </Aviso>
          </div>
        )
      }}
    </Bloque>
  )
}

/* ------------------------------------------------------- ofertas dudosas ----
   El verificador de ofertas. La pregunta no es cuanto cuesta: es **si el descuento
   que anuncian existe**. La respuesta la calcula el servidor y viene en `por_que`,
   y aqui se enseña lo primero, antes de la foto y antes del precio: si el cartel
   dice "-50 %" y el producto cuesta lo de siempre, eso es lo que hay que leer.
   El aviso del final no es un adorno legal: `oferta_sospechosa` (la regla que
   caza subir el precio antes de anunciar la oferta) esta **dormida** hasta que
   haya 45 dias de historico, asi que no se puede prometer lo que no se mide.
*/
function Dudosas({ cadenas }: { cadenas: string[] }) {
  const consulta = useOfertasDudosas(cadenas)
  return (
    <Bloque consulta={consulta} titulo="las ofertas dudosas">
      {(d) => (
        <div className="grid grid-cols-1 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-entrada font-semibold">
              {d.resultados.length === 0
                ? 'Ninguna oferta sospechosa'
                : `${numero(d.resultados.length, 0)} ofertas que conviene mirar dos veces`}
            </h2>
            <SelloFecha fechaDatos={d.fecha_datos} />
          </div>

          {d.resultados.length === 0 ? (
            <Vacio titulo="Hoy ninguna oferta anunciada se cae del histórico" className="grow">
              <p>
                Aquí salen las ofertas anunciadas cuyo precio de hoy no está por debajo de lo que ese
                producto cuesta normalmente. Que no haya ninguna es una buena noticia.
              </p>
            </Vacio>
          ) : (
            <>
              <p className="text-cuerpo text-tinta-suave">
                No son mentiras necesariamente: son las que el histórico no sostiene, y por eso
                conviene mirarlas dos veces antes de llenar el carro.
              </p>
              <ul className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                {d.resultados.map((x, i) => {
                  const pos =
                    x.posicion_90d === null ? null : Math.round(100 * Math.min(1, Math.max(0, x.posicion_90d)))
                  return (
                    <li
                      key={`${x.cadena}-${x.grupo_id ?? x.nombre}-${i}`}
                      className="grid grid-cols-[4.5rem_1fr] gap-3 rounded-tarjeta border border-borde bg-papel p-3 "
                    >
                      {x.imagen ? (
                        <img
                          src={x.imagen}
                          alt=""
                          loading="lazy"
                          className="h-[4.5rem] w-[4.5rem] rounded-campo object-contain"
                        />
                      ) : (
                        <span aria-hidden className="h-[4.5rem] w-[4.5rem]" />
                      )}
                      <div className="grid gap-1">
                        <h3 className="text-cuerpo font-semibold">
                          {x.grupo_id === null ? (
                            x.nombre
                          ) : (
                            /* `min-h-[44px]`: el nombre es el enlace a la ficha, y un
                               enlace de 19 px de alto no se acierta de pie con el carro
                               en la mano. Lo midio la puerta del navegador el 24 de
                               septiembre de 2026: 28 de estos, entre 145 x 19 y 248 x 39. */
                            <Link
                              to={`/grupo/${x.grupo_id}`}
                              className="inline-flex min-h-[44px] min-w-[44px] items-center underline"
                            >
                              {x.nombre}
                            </Link>
                          )}
                        </h3>
                        <p className="text-etiqueta text-tinta-suave">
                          {x.marca ? `${x.marca} · ` : ''}
                          {nombreCadena(x.cadena)}
                        </p>
                        {/* La respuesta, antes que el precio y antes que la foto. */}
                        <p className="text-cuerpo font-semibold">{x.por_que}</p>
                        <p className="flex flex-wrap items-center gap-1 text-etiqueta">
                          <span className="cifra">{eurosUnidad(x.precio_unidad_cent, x.unidad)}</span>
                          <span className="text-tinta-suave">
                            hoy · su precio de siempre{' '}
                            <span className="cifra">{eurosUnidad(x.precio_base_cent, x.unidad)}</span>
                          </span>
                        </p>
                        {x.promo_txt && <Etiqueta tono="dato">{x.promo_txt}</Etiqueta>}
                        {x.solo_con_tarjeta && (
                          <Etiqueta tono="aviso" titulo="Sin la tarjeta de la cadena, ese precio no existe">
                            solo con tarjeta
                          </Etiqueta>
                        )}
                        {pos !== null && (
                          <div className="grid gap-1">
                            <span className="text-etiqueta text-tinta-suave">
                              Dónde cae hoy dentro de sus últimos 90 días
                            </span>
                            <span className="relative block h-3 w-full rounded bg-marfil ">
                              <span
                                aria-hidden
                                className="absolute inset-y-0 w-1 rounded bg-papel "
                                style={{ left: `calc(${pos}% - 2px)` }}
                              />
                            </span>
                            <span className="flex justify-between text-etiqueta text-tinta-suave">
                              <span className="cifra">{euros(x.min_90d_cent)}</span>
                              <span>lo más caro fue {euros(x.max_90d_cent)}</span>
                            </span>
                            <span className="sr-only">
                              Posición {pos} de 100 dentro de sus 90 días.
                            </span>
                          </div>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </>
          )}

          <Aviso tono="info">
            Se marca <strong>anuncia oferta y hoy no cuesta menos de lo que cuesta siempre</strong>.
            La regla que caza el caso feo de verdad —subir el precio normal justo antes de anunciar
            la oferta— necesita 45 días de histórico y hoy no los tenemos, así que esa comprobación
            todavía no está y no se promete.
          </Aviso>

          {/* **Lo que no se ha podido juzgar, dicho en voz alta.** Son ofertas
              anunciadas que no bajan pero que no se pueden medir con el precio de una
              unidad (`/api/ofertas-dudosas` → `sin_poder_juzgar`): un 3x2 no baja el
              precio de una, baja el de la tercera; "Stock Fuera" no es una oferta; y
              si el tamaño declarado cambió, los dos números no son del mismo
              producto. Un dato que no tenemos es «no lo sé», y esconderlo sería hacer
              parecer que la lista está completa. */}
          {d.sin_poder_juzgar.total > 0 && (
            <p className="text-etiqueta text-tinta-suave">
              Y <strong>{numero(d.sin_poder_juzgar.total, 0)}</strong> ofertas anunciadas más no se
              juzgan aquí: {numero(d.sin_poder_juzgar.por_varias_unidades, 0)} dependen de cuántas
              unidades compres (un 3x2 no baja el precio de una),{' '}
              {numero(d.sin_poder_juzgar.sin_descuento_de_precio, 0)} no anuncian un descuento de
              precio, y {numero(d.sin_poder_juzgar.cantidad_cambiada, 0)} tienen un tamaño declarado
              que cambió y no se pueden comparar consigo mismas.
            </p>
          )}
        </div>
      )}
    </Bloque>
  )
}