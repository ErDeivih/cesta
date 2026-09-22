/** La pantalla del grupo: el mismo producto en cada cadena, en columnas.
 *
 *  Es la pantalla clave del encargo y la que mas facil es hacer mal. Lo que
 *  decide si sirve o no:
 *
 *   - **Las columnas son cadenas, y dentro de cada una estan SUS productos.**
 *     Dos cadenas pueden tener dos yogures equivalentes en el mismo grupo; si
 *     se mezclan en una lista unica, el `precio_unidad_cent` de una y la `gama`
 *     de otra acaban pareciendo la misma ficha.
 *   - **La diferencia % se mide contra el precio por unidad**, no contra el
 *     precio del envase: un bote de 1 kg y otro de 500 g no se restan.
 *   - **Un precio de mas de `dias_precio_valido` dias no decide.** Se enseña,
 *     con su fecha, y queda fuera del orden y de la referencia del "mejor".
 *   - **La chispa se pinta por producto, no por cadena.** `/api/grupo` manda
 *     `producto_id` en cada punto de la serie desde el 22 de septiembre de 2026;
 *     antes no lo mandaba y habia que callarse cuando la cadena tenia dos
 *     productos en el grupo, porque la serie mezclaba los dos y no se sabia de
 *     cual era cada precio. Pintar esa linea mezclada seria inventar un
 *     historico.
 */
import { useCallback, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useEstado, useGrupo } from '../api/consultas'
import {
  cantidad as textoCantidad,
  diasDesde,
  euros,
  eurosUnidad,
  fecha as fechaTexto,
  ms,
  nombreCadena,
  porcentaje,
} from '../api/formato'
import { Chispa, type PuntoChispa } from '../componentes/Chispa'
import { ControlPesos } from '../componentes/ControlPesos'
import { SelloLetra, SelloNutriscore, SelloOferta, SelloRetirada } from '../componentes/Etiquetas'
import { Aviso, Boton, Cargando, Dato, Etiqueta, Fallo, Vacio, cx } from '../componentes/ui'
import { IconoCodigoBarras } from '../componentes/iconos'
import { PESOS_INICIALES, explicaPesos, puntuaAlternativas, type Alternativa, type Pesos } from '../logica/pesos'
import type { Producto } from '../tipos'

interface Juicio {
  decide: boolean
  motivo: string | null
}

export function Grupo() {
  const { grupoId } = useParams<{ grupoId: string }>()
  const id = Number(grupoId)
  const navega = useNavigate()

  const consulta = useGrupo(Number.isFinite(id) ? id : null)
  const estado = useEstado()
  const [pesos, setPesos] = useState<Pesos>(PESOS_INICIALES)

  const grupo = consulta.data
  const diasValidos = estado.data?.dias_precio_valido ?? 3

  /** De que dia es el precio de esa cadena.
   *
   *  Primero `/api/estado`, que es la fuente buena. Si esa cadena no esta ahi,
   *  se mira la ultima fecha de la propia serie del grupo: es peor dato, pero
   *  es mejor que decir "no se" cuando si se sabe. */
  const ultimoDiaDe = useCallback(
    (fuente: string): string | null => {
      const deEstado = estado.data?.cadenas.find((c) => c.cadena === fuente)?.ultimo_dia
      if (deEstado) return deEstado
      const fechas = (grupo?.serie ?? [])
        .filter((s) => s.fuente === fuente)
        .map((s) => s.fecha)
        .sort()
      return fechas.length > 0 ? (fechas[fechas.length - 1] as string) : null
    },
    [estado.data, grupo],
  )

  /** Si ese precio puede decidir donde comprar. */
  const juzga = useCallback(
    (p: Producto): Juicio => {
      if (p.precio_unidad_cent === null || !(p.precio_unidad_cent > 0)) {
        return {
          decide: false,
          motivo: 'No tenemos el precio por unidad de este producto, así que no entra en la comparación.',
        }
      }
      const ultimo = ultimoDiaDe(p.fuente)
      if (!ultimo) {
        // Sin fecha no se puede decir que sea viejo. Se deja decidir y se avisa.
        return { decide: true, motivo: null }
      }
      const referencia = grupo?.fecha_datos ?? estado.data?.fecha_datos ?? null
      const dias = referencia
        ? diasDesde(ultimo, new Date(`${referencia}T00:00:00`))
        : diasDesde(ultimo)
      if (dias !== null && dias > diasValidos) {
        return {
          decide: false,
          motivo: `El precio de ${nombreCadena(p.fuente)} es del ${fechaTexto(ultimo)} (${dias} días): se enseña con su fecha, pero no decide.`,
        }
      }
      return { decide: true, motivo: null }
    },
    [diasValidos, estado.data, grupo, ultimoDiaDe],
  )

  const alternativas = useMemo(
    () => (grupo ? puntuaAlternativas(grupo.productos, pesos, juzga) : []),
    [grupo, pesos, juzga],
  )

  /** Las alternativas agrupadas por cadena, y las columnas de mejor a peor. */
  const columnas = useMemo(() => {
    const mapa = new Map<string, Alternativa[]>()
    for (const a of alternativas) {
      const lista = mapa.get(a.producto.fuente) ?? []
      lista.push(a)
      mapa.set(a.producto.fuente, lista)
    }
    const mejor = (lista: Alternativa[]): number => {
      const conPuntos = lista.filter((a) => a.decide && a.puntos !== null)
      if (conPuntos.length === 0) return -1
      return Math.max(...conPuntos.map((a) => a.puntos as number))
    }
    return [...mapa.entries()].sort((x, y) => mejor(y[1]) - mejor(x[1]))
  }, [alternativas])

  const cuantasLetras = useMemo(() => {
    let calidad = 0
    let gama = 0
    for (const a of alternativas) {
      if (a.componentes.letraDe === 'calidad') calidad += 1
      else if (a.componentes.letraDe === 'gama') gama += 1
    }
    return { calidad, gama }
  }, [alternativas])

  const explicacion = useMemo(() => explicaPesos(pesos, cuantasLetras), [pesos, cuantasLetras])

  // ------------------------------------------------------------------ estados

  if (consulta.isPending) return <Cargando que="el grupo" />
  if (consulta.isError) {
    return (
      <div className="grid grid-cols-1 gap-3">
        <Boton variante="sutil" onClick={() => navega(-1)} className="justify-self-start">
          ← Volver
        </Boton>
        <Fallo error={consulta.error} reintentar={() => void consulta.refetch()} />
      </div>
    )
  }

  if (!grupo) {
    return (
      <Vacio titulo="No tengo ese producto">
        <p>Puede que ya no lo vendan.</p>
        <p className="mt-2">
          <Link to="/" className="underline">
            Volver al buscador
          </Link>
        </p>
      </Vacio>
    )
  }

  const unidadDelGrupo = grupo.unidad
  const otrasUnidades = grupo.productos.filter(
    (p) => p.unidad !== null && unidadDelGrupo !== null && p.unidad !== unidadDelGrupo,
  )
  const decidientes = alternativas.filter((a) => a.decide)
  const ganadora = decidientes[0] ?? null
  const sinFecha = alternativas.filter((a) => a.decide && ultimoDiaDe(a.producto.fuente) === null)

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Boton variante="sutil" onClick={() => navega(-1)}>
          ← Volver
        </Boton>
        <Link
          to="/escaner"
          className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-neutral-300 px-3 text-sm dark:border-neutral-600"
        >
          <IconoCodigoBarras width={18} height={18} />
          Escanear un código
        </Link>
      </div>

      <header className="flex flex-wrap items-start gap-4">
        {grupo.imagen && (
          <img
            src={grupo.imagen}
            alt=""
            loading="lazy"
            width={96}
            height={96}
            // Si el CDN de la cadena no contesta, el hueco queda limpio: un
            // icono de imagen rota en medio de la ficha no aporta nada.
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
            className="h-24 w-24 rounded-lg border border-neutral-200 bg-white object-contain dark:border-neutral-700"
          />
        )}
        <div className="min-w-[16rem] flex-1">
          <h1 className="text-xl font-bold leading-tight">{grupo.nombre}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
            <span>{grupo.productos.length} productos</span>
            <span>·</span>
            <span>
              {grupo.cadenas} {grupo.cadenas === 1 ? 'cadena' : 'cadenas'}
            </span>
            <span>·</span>
            <span>por {unidadDelGrupo ?? 'unidad desconocida'}</span>
            {grupo.fecha_datos && (
              <>
                <span>·</span>
                <Etiqueta tono="dato">datos del {fechaTexto(grupo.fecha_datos)}</Etiqueta>
              </>
            )}
          </div>

          <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Dato etiqueta="Alternativa que gana contigo">
              {ganadora ? (
                <>
                  {nombreCadena(ganadora.producto.fuente)}
                  <span className="block text-xs font-normal text-neutral-500 dark:text-neutral-400">
                    {eurosUnidad(ganadora.producto.precio_unidad_cent, ganadora.producto.unidad)}
                  </span>
                </>
              ) : (
                'no lo sé'
              )}
            </Dato>
            <Dato etiqueta="Diferencia entre la más cara y la más barata">
              {grupo.cadenas >= 2
                ? `${porcentaje(grupo.ahorro_pct)} · ${euros(grupo.ahorro_cent)} por unidad`
                : 'sin comparación: está en una sola cadena'}
            </Dato>
            <Dato etiqueta="Precios que deciden">
              {decidientes.length} de {alternativas.length}
              <span className="block text-xs font-normal text-neutral-500 dark:text-neutral-400">
                los de más de {diasValidos} días no cuentan
              </span>
            </Dato>
            <Dato etiqueta="Datos del">{grupo.fecha_datos ? fechaTexto(grupo.fecha_datos) : 'no lo sé'}</Dato>
          </dl>
        </div>
      </header>

      {otrasUnidades.length > 0 && (
        <Aviso tono="aviso" titulo="Este grupo mezcla unidades">
          {otrasUnidades.length} de sus productos se miden en otra unidad (
          {[...new Set(otrasUnidades.map((p) => p.unidad))].join(', ')}) y no entran en la
          comparación de precio: restar euros por kilo de euros por unidad da números enormes y
          falsos. Se ven abajo, con su unidad.
        </Aviso>
      )}

      {sinFecha.length > 0 && (
        <Aviso tono="aviso" titulo="Hay precios que no sé de cuándo son">
          {[...new Set(sinFecha.map((a) => a.producto.fuente))].join(', ')}: sin fecha no se puede
          decir que el precio sea viejo, así que cuenta, pero no lo puedo fechar.
        </Aviso>
      )}

      <ControlPesos pesos={pesos} onCambio={setPesos} explicacion={explicacion} />

      {columnas.length === 0 ? (
        <Vacio titulo="Este grupo no tiene ningún producto con precio" />
      ) : (
        <div className="sm:overflow-x-auto">
          {/* En el movil las columnas se apilan; a partir de tablet se ponen en
              fila y se deslizan en horizontal, que es la unica forma de que
              cinco cadenas se puedan comparar de un vistazo. `grid-cols-none`
              limpia la plantilla de una columna antes de pasar a flujo por
              columnas: si no, `grid-cols-1` ganaria y apilaria todo otra vez. */}
          <div className="grid grid-cols-1 gap-3 sm:grid-flow-col sm:grid-cols-none sm:auto-cols-[minmax(17rem,21rem)]">
            {columnas.map(([cadena, lista], indice) => {
              const ultimo = ultimoDiaDe(cadena)
              const alDia = lista.some((a) => a.decide)
              return (
                <section
                  key={cadena}
                  aria-label={`Alternativas de ${cadena}`}
                  className="rounded-xl border border-neutral-200 bg-white p-3 dark:border-neutral-700 dark:bg-neutral-800"
                >
                  <header className="mb-2 flex flex-wrap items-center gap-2">
                    <h2 className="text-base font-semibold">{nombreCadena(cadena)}</h2>
                    {indice === 0 && ganadora && <Etiqueta tono="bien">la mejor contigo</Etiqueta>}
                    {alDia ? (
                      <Etiqueta tono="dato">al día</Etiqueta>
                    ) : (
                      <Etiqueta tono="aviso">precio del {fechaTexto(ultimo)}</Etiqueta>
                    )}
                  </header>

                  <div className="grid grid-cols-1 gap-3">
                    {lista.map((a) => (
                      <FichaAlternativa
                        key={a.producto.producto_id}
                        alternativa={a}
                        pesos={pesos}
                        puntosSerie={
                          // Se filtra por `producto_id`, no por cadena: es lo que
                          // permite pintar la chispa aunque la cadena tenga dos
                          // productos en el grupo. Sin ese campo la serie mezcla
                          // los dos y no hay forma de saber de cual es cada
                          // precio, que es por lo que antes solo se pintaba
                          // cuando la cadena tenia un producto.
                          grupo.serie
                            .filter((s) => s.producto_id === a.producto.producto_id)
                            .map<PuntoChispa>((s) => ({
                              fecha: s.fecha,
                              valor: s.precio_unidad_cent,
                            }))
                        }
                        chispaBloqueada={lista.length > 1}
                        fechaDatos={grupo.fecha_datos ?? null}
                      />
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

/** La frase de la diferencia, que depende de si ese precio puede decidir.
 *
 *  El caso que obliga a separarlo: una alternativa con el precio MÁS BAJO pero
 *  de hace dos semanas tiene una diferencia negativa contra el mejor que sí
 *  decide. Pintarla como "el más barato por unidad" sería enseñar un precio
 *  viejo como si fuera una ganga de hoy, que es justo lo que la regla de
 *  `dias_precio_valido` existe para evitar.
 */
function textoDiferencia(a: Alternativa): string {
  const { diferenciaPct, decide } = a
  if (diferenciaPct === null) return 'sin precio por unidad'
  if (!decide) {
    return diferenciaPct < 0
      ? `${porcentaje(Math.abs(diferenciaPct))} por debajo del mejor que decide`
      : `+${porcentaje(diferenciaPct)} frente al mejor que decide`
  }
  if (diferenciaPct <= 0) return 'el más barato por unidad'
  return `+${porcentaje(diferenciaPct)} frente al más barato`
}

/** Una alternativa, con su nota y su desglose.
 *
 *  El desglose no es un adorno: sin el, mover un peso cambia el orden y no se
 *  sabe por que. Con el, se ve que ese producto gana por precio y pierde por
 *  letra, que es la informacion que hace falta para decidir.
 */
function FichaAlternativa({
  alternativa,
  pesos,
  puntosSerie,
  chispaBloqueada,
  fechaDatos,
}: {
  alternativa: Alternativa
  pesos: Pesos
  puntosSerie: PuntoChispa[]
  chispaBloqueada: boolean
  fechaDatos: string | null
}) {
  const p = alternativa.producto
  // El orden de esta lista es el orden en que se mira la pantalla, y cada
  // componente lleva SU peso al lado: el numero de la nota tiene que poder
  // reconstruirse a mano con lo que se ve.
  const componentes: { clave: keyof Pesos; nombre: string; valor: number | null }[] = [
    { clave: 'precio', nombre: 'precio por unidad', valor: alternativa.componentes.precio },
    {
      clave: 'letra',
      nombre:
        alternativa.componentes.letraDe === 'gama'
          ? 'gama (por precio, no es calidad)'
          : 'calidad (leída de ingredientes)',
      valor: alternativa.componentes.letra,
    },
    { clave: 'cercania', nombre: 'cercanía al mejor', valor: alternativa.componentes.cercania },
    { clave: 'promo', nombre: 'promoción', valor: alternativa.componentes.promo },
  ]

  return (
    <article
      className={cx(
        'rounded-lg border p-3',
        alternativa.decide
          ? 'border-neutral-200 dark:border-neutral-700'
          : 'border-amber-300 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30',
      )}
    >
      <div className="flex items-start gap-3">
        {p.imagen ? (
          <img
            src={p.imagen}
            alt=""
            loading="lazy"
            width={72}
            height={72}
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
            className="h-[72px] w-[72px] shrink-0 rounded border border-neutral-200 bg-white object-contain dark:border-neutral-700"
          />
        ) : null}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium leading-snug">{p.nombre}</p>
          {p.marca && <p className="text-xs text-neutral-600 dark:text-neutral-400">{p.marca}</p>}
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            {textoCantidad(p.cantidad, p.unidad)}
            {p.unidades_pack && ` · pack de ${p.unidades_pack}`}
          </p>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="cifra text-lg font-bold">{euros(p.precio_cent)}</span>
        <span className="cifra text-sm text-neutral-700 dark:text-neutral-300">
          {eurosUnidad(p.precio_unidad_cent, p.unidad)}
        </span>
        <span
          className={cx(
            'cifra text-sm font-semibold',
            !alternativa.decide
              ? 'text-amber-800 dark:text-amber-400'
              : alternativa.diferenciaPct === null
                ? 'text-neutral-500 dark:text-neutral-400'
                : alternativa.diferenciaPct <= 0
                  ? 'text-emerald-800 dark:text-emerald-400'
                  : 'text-neutral-800 dark:text-neutral-200',
          )}
        >
          {textoDiferencia(alternativa)}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1">
        <SelloLetra producto={p} />
        <SelloNutriscore valor={p.nutriscore} />
        <SelloOferta texto={p.promo} club={p.promo_club} />
        <SelloRetirada retirado={p.es_recall} />
        {p.es_marca_propia && <Etiqueta tono="dato">marca propia</Etiqueta>}
        {p.comparable === false && (
          <Etiqueta
            tono="aviso"
            titulo="Su precio por unidad y su precio de venta se contradicen: no puede decidir la comparación"
          >
            precio en disputa
          </Etiqueta>
        )}
      </div>

      {p.promo && (
        <p className="mt-1 text-xs text-neutral-700 dark:text-neutral-300">
          {p.promo}
          {p.promo_hasta && ` · hasta el ${fechaTexto(p.promo_hasta)}`}
          {p.promo_club && ' · solo con tarjeta: no baja lo que pagas en caja'}
        </p>
      )}

      {p.advertencias.length > 0 && (
        <p className="mt-1 text-xs text-amber-800 dark:text-amber-400">
          {p.advertencias.join('. ')}
        </p>
      )}

      {alternativa.motivoNoDecide && (
        <p className="mt-1 text-xs font-medium text-amber-800 dark:text-amber-400">
          {/* Se dice también que va al final, porque si no la nota de abajo
              (que puede ser la más alta) no cuadra con la posición. */}
          Va la última de su columna. {alternativa.motivoNoDecide}
        </p>
      )}

      <p className="mt-2 text-xs text-neutral-600 dark:text-neutral-400">
        Nota contigo:{' '}
        <strong className="cifra font-semibold text-neutral-900 dark:text-neutral-100">
          {alternativa.puntos === null ? 'no lo sé' : alternativa.puntos.toFixed(1)}
        </strong>{' '}
        de 100
      </p>

      <details className="mt-1">
        <summary className="cursor-pointer text-xs text-sky-800 dark:text-sky-400">
          Por qué está en esta posición
        </summary>
        <ul className="mt-1 grid gap-0.5 text-xs">
          {componentes.map((c) => (
            <li key={c.clave} className="flex justify-between gap-2">
              <span>
                {c.nombre} <span className="text-neutral-500">(peso {pesos[c.clave]})</span>
              </span>
              <span className="cifra">{c.valor === null ? 'sin dato' : c.valor.toFixed(2)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
          La nota reparte los pesos solo entre los componentes con dato: lo que no sabemos no
          resta. Las alternativas sin precio por unidad no sacan un cero por eso.
        </p>
      </details>

      <div className="mt-2">
        {chispaBloqueada ? (
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            No pinto el histórico: esta cadena tiene más de un producto en el grupo y la serie de
            `/api/grupo` no dice de cuál es cada punto.
          </p>
        ) : (
          <Chispa
            puntos={[...puntosSerie].sort((a, b) => ms(a.fecha) - ms(b.fecha))}
            etiqueta={`Histórico de ${p.nombre}`}
            alto={36}
          />
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-2 text-xs">
        <Link
          to={`/producto/${p.fuente}/${p.id_fuente}`}
          className="inline-flex min-h-[36px] items-center rounded-md border border-neutral-300 px-2 font-medium hover:bg-neutral-50 dark:border-neutral-600 dark:hover:bg-neutral-700"
        >
          Ficha e histórico
        </Link>
        {p.url && (
          <a
            href={p.url}
            target="_blank"
            // `noopener` porque si no la pagina de destino puede manejar esta.
            rel="noopener noreferrer"
            className="inline-flex min-h-[36px] items-center rounded-md border border-neutral-300 px-2 font-medium hover:bg-neutral-50 dark:border-neutral-600 dark:hover:bg-neutral-700"
          >
            Ver en {nombreCadena(p.fuente)}
          </a>
        )}
      </div>

      {fechaDatos && !alternativa.decide && (
        <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
          Datos del grupo: {fechaTexto(fechaDatos)}.
        </p>
      )}
    </article>
  )
}
