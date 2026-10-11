/** Dónde se compra cada cosa: la lista partida por tiendas.
 *
 *  Lo pidió el dueño el 25 de septiembre de 2026, y es la pantalla que faltaba entre
 *  «quiero comprar esto» y «voy a la tienda»:
 *
 *    *"en la lista poder elegir en qué supermercado lo quiero comprar y hacer en una
 *    lista que tenga, sublistas dependiendo de dónde he puesto que voy a comprar ese
 *    producto, con el precio final de la lista entera y de cada sublista (explicando
 *    también aplicación de descuentos), con opciones para eliminar fácilmente de la
 *    lista cosas, poder borrar sublista o lista del tirón"*.
 *
 *  Tres decisiones de esta pantalla, y las tres son de dinero:
 *
 *  1. **Cada sublista lleva su cuenta y la lista lleva la suya**, y al lado va lo que
 *     costaría sin decidir nada (todo en la más barata, o repartido en dos). Enseñar
 *     solo el total propio no deja comparar, y comparar es para lo que se entra aquí.
 *  2. **Las ofertas se enseñan desglosadas**: el total con ofertas, el total sin
 *     ellas y la lista de las que se aplican con lo que ahorran. Un total de oferta
 *     sin explicación es un número que no se puede comprobar.
 *  3. **Lo que no se ha decidido no suma.** La lista tiene tres estados, no dos: sin
 *     decidir, decidida y comprada. Sumar por lo más barato lo que aún no se ha
 *     decidido daría un total que no corresponde a ninguna compra posible.
 *
 *  Y una regla de la casa que se ve aquí: una línea puesta en una tienda que no la
 *  tiene **no desaparece**: sale con su nombre. Es la misma que aplica la API.
 */
import { useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { AvisoIdentidad } from './AvisoIdentidad'
import { ponerTienda, reparto as pedirReparto } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { euros } from '../api/formato'
import { avisoDeTransporte } from '../logica/transporte'
import { Aviso, Boton, Etiqueta, Tarjeta, cx } from './ui'
import { autorizarLinea } from '../api/cesta'
import type { OpcionEnTienda, RepartoTiendas } from '../tipos'

/** Lo mínimo que necesita el selector de tienda de una línea. */
interface Elegible {
  linea_id: string | null
  nombre: string
  opciones: OpcionEnTienda[]
  mas_barata: string
  elegida?: string
  /** El producto que la propuesta elegiria, y **lo que la persona ya acepto**. */
  producto_id?: string | null
  autorizado?: boolean
  autorizado_producto?: string | null
  autorizado_cadena?: string | null
}

/** Los nombres de las cadenas, como se escriben. */
const NOMBRE: Record<string, string> = {
  alcampo: 'Alcampo',
  aldi: 'Aldi',
  carrefour: 'Carrefour',
  dia: 'DIA',
  mercadona: 'Mercadona',
}

export function nombreDeCadena(c: string): string {
  return NOMBRE[c] ?? c
}

/** Los botones de tienda de una línea, con lo que cuesta en cada una.
 *
 *  Enseñar el precio dentro del botón no es adorno: elegir tienda es elegir precio, y
 *  un botón que solo diga «DIA» obliga a ir a mirarlo a otro sitio. La más barata va
 *  marcada, y la que ya está puesta, en negrita.
 */
function ElegirTienda({ fila, listaId, deshabilitado, alCambiar }: {
  fila: Elegible
  listaId: string
  deshabilitado: boolean
  alCambiar: () => void
}) {
  const poner = useMutation({
    mutationFn: (cadena: string | null) =>
      ponerTienda(listaId, { cadena, lineas: fila.linea_id ? [fila.linea_id] : [] }),
    onSuccess: alCambiar,
  })
  // **El consentimiento, que no es lo mismo que elegir tienda.** `poner` escribe `cadena_elegida`
  // -- "esto lo compro en DIA" -- y esto escribe `autorizado`, que es lo que el motor mira para
  // decidir si la linea es exacta o confirmada. Una sustitucion sin confirmar no lleva su descuento.
  const consentir = useMutation({
    mutationFn: (si: boolean) =>
      autorizarLinea(listaId, fila.linea_id as string, si,
                     si ? (fila.producto_id ?? null) : null,
                     si ? fila.mas_barata : null),
    onSuccess: alCambiar,
  })
  const opciones = fila.opciones ?? []
  if (!opciones.length) {
    return <Etiqueta tono="aviso">no lo sé</Etiqueta>
  }
  return (
    <div className="flex flex-wrap items-center gap-1">
      {opciones.map((o: OpcionEnTienda) => {
        const puesta = fila.elegida === o.cadena
        const barata = fila.mas_barata === o.cadena
        return (
          <button
            key={o.cadena}
            type="button"
            disabled={deshabilitado || poner.isPending}
            onClick={() => poner.mutate(puesta ? null : o.cadena)}
            title={puesta ? 'Tocar para quitarla de esta tienda' : `Comprar en ${nombreDeCadena(o.cadena)}`}
            className={cx(
              'flex min-h-[44px] flex-col items-start justify-center rounded-lg border px-2 text-left text-xs',
              puesta
                ? 'border-sky-700 bg-sky-50 font-semibold text-sky-900 dark:border-sky-400 dark:bg-sky-950 dark:text-sky-100'
                : 'border-neutral-300 text-neutral-700 dark:border-neutral-600 dark:text-neutral-200',
              deshabilitado && 'opacity-50',
            )}
          >
            <span>{nombreDeCadena(o.cadena)}</span>
            <span className="cifra">
              {euros(o.coste_cent)}
              {barata && !puesta && <span className="ml-1 text-emerald-700 dark:text-emerald-400">más barata</span>}
            </span>
          </button>
        )
      })}
      {fila.elegida && (
        <button
          type="button"
          disabled={deshabilitado || poner.isPending}
          onClick={() => poner.mutate(null)}
          className="min-h-[44px] px-2 text-xs underline"
        >
          quitar de {nombreDeCadena(fila.elegida)}
        </button>
      )}

      {/* **Aceptar o retirar el sustituto.** Solo cuando la mas barata no es la que se pidio: si
          coincide, no hay nada que consentir. Y son la misma puerta, como el endpoint. */}
      {fila.linea_id && fila.mas_barata && fila.autorizado !== true && (
        <button
          type="button"
          disabled={deshabilitado || consentir.isPending}
          onClick={() => consentir.mutate(true)}
          className="min-h-[44px] min-w-[44px] rounded-lg border border-emerald-700 px-2 text-xs text-emerald-800 dark:border-emerald-500 dark:text-emerald-300"
        >
          Aceptar el de {nombreDeCadena(fila.mas_barata)}
        </button>
      )}
      {fila.autorizado === true && (
        <>
          <span className="text-xs text-emerald-800 dark:text-emerald-300">
            Sustituto aceptado
            {fila.autorizado_cadena ? `: ${nombreDeCadena(fila.autorizado_cadena)}` : ''}
          </span>
          <button
            type="button"
            disabled={deshabilitado || consentir.isPending}
            onClick={() => consentir.mutate(false)}
            className="min-h-[44px] min-w-[44px] px-2 text-xs underline"
          >
            Volver al mio
          </button>
        </>
      )}
      {/* **El error, a la vista.** Sin esto un fallo al consentir se ve igual que no haber pulsado,
          que es exactamente lo que me paso en la tarjeta del plan y no he aplicado aqui. Medido el
          13 de octubre de 2026: el boton se pulsaba, no cambiaba nada, y no habia forma de saber si
          fallaba la peticion o el refresco. */}
      {consentir.error && (
        <Aviso tono="mal" titulo="No he podido cambiarlo">{String(consentir.error)}</Aviso>
      )}
    </div>
  )
}

export function RepartoEnTiendas({ listaId, papel, className }: {
  listaId: string
  papel: string
  className?: string
}) {
  const cliente = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const soloMirar = papel === 'mira'

  const reparto = useQuery({
    queryKey: ['reparto', listaId],
    queryFn: () => pedirReparto(listaId),
    enabled: Boolean(listaId),
  })

  const refresca = () => {
    // **`refetchQueries`, no `invalidateQueries`.** Invalidad marca la consulta como obsoleta, pero
    // **no siempre vuelve a pedirla**: si tiene `staleTime`, el repintado puede no llegar. Y eso es
    // exactamente lo que pasaba -- aceptar dejaba el dato bien en el API (medido: `autorizado: true`
    // en el reparto y en la lista) y el boton seguia diciendo ?Aceptar el de DIA? hasta recargar.
    // Medido el 13 de octubre de 2026. `refetchQueries` pide y repinta, que es lo que se quiere.
    void cliente.refetchQueries({ queryKey: ['reparto', listaId] })
    void cliente.invalidateQueries({ queryKey: ['lista', listaId] })
    void cliente.invalidateQueries({ queryKey: ['listas'] })
  }
  const poner = useMutation({
    mutationFn: (c: { cadena: string | null; lineas?: string[]; borrar?: boolean }) =>
      ponerTienda(listaId, c),
    onSuccess: refresca,
    onError: (e) => setError(textoDeError(e)),
  })

  if (reparto.isLoading || !reparto.data) return null
  // **Lo que el total NO incluye, y va antes de los numeros a proposito**: *comparar dos tiendas
  // como si llegar a las dos costara lo mismo que llegar a una es la omision que G05 pide declarar
  // -- «y si falta transporte» --, y el ahorro de repartir puede ser menor que el viaje.*
  // **Las tiendas que de verdad entran**: las sublistas, que son la lista partida por tienda.
  const tiendasDelReparto = reparto.data.sublistas.length
  const avisoTransporte = (
    <p className="text-[13px] text-secundaria">{avisoDeTransporte(tiendasDelReparto)}</p>
  )

  const r: RepartoTiendas = reparto.data

  // Sin ninguna línea decidida y sin nada pendiente, esta tarjeta no tiene nada que
  // decir: la lista está vacía o todo está tachado, y el resto de la pantalla ya lo
  // cuenta. Una tarjeta vacía es ruido.
  if (!r.sublistas.length && !r.sin_asignar.length) return null

  const decididas = r.sublistas.reduce((n, s) => n + s.lineas.length, 0)
  const idsDe = (s: RepartoTiendas['sublistas'][number]) =>
    s.lineas.map((f) => f.linea_id).filter((x): x is string => Boolean(x))

  return (
    <Tarjeta
      titulo="Dónde compro cada cosa"
      sub="Elige la tienda de cada producto y aquí se parte la lista: cada sublista con su precio y el total de todo, con las ofertas aplicadas y explicadas."
      className={className}
    >
      {avisoTransporte}
      {error && (
        <div className="mb-3">
          <Aviso tono="mal" titulo="No he podido cambiarlo">{error}</Aviso>
        </div>
      )}

      {/* ---- la cuenta de la lista entera ---- */}
      <div className="mb-4 rounded-lg border border-neutral-200 p-3 dark:border-neutral-700">
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <p className="cifra text-2xl font-semibold">{euros(r.total_cent)}</p>
          <p className="text-sm text-tinta-suave">
            {decididas} de {r.lineas} línea{r.lineas === 1 ? '' : 's'} decidida
            {decididas === 1 ? '' : 's'}
            {r.sin_asignar.length > 0 && <> · {r.sin_asignar.length} sin decidir</>}
          </p>
        </div>
        {r.ahorro_cent > 0 && (
          <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">
            Con las ofertas aplicadas: sin ellas serían {euros(r.total_sin_ofertas_cent)},
            o sea <strong>{euros(r.ahorro_cent)} menos</strong>.
          </p>
        )}
        {/* La comparación: es lo que convierte el total en una decisión. */}
        {(r.una_tienda.length > 0 || r.repartido) && (
          <p className="mt-2 text-sm text-tinta-suave">
            Sin decidir nada:
            {r.una_tienda[0] && (
              <> todo en {nombreDeCadena(r.una_tienda[0].cadena)} serían{' '}
                <span className="cifra">{euros(r.una_tienda[0].total_cent)}</span>
                {r.una_tienda[0].faltan.length > 0 && (
                  <> (le faltan {r.una_tienda[0].faltan.length})</>
                )}</>
            )}
            {r.repartido && (
              <>; repartido entre {r.repartido.cadenas.map(nombreDeCadena).join(' y ')}:{' '}
                <span className="cifra">{euros(r.repartido.total_cent)}</span>
                {r.repartido.merece_la_pena === false && ' (el ahorro no paga la segunda parada)'}
              </>
            )}
            .
          </p>
        )}

        {!soloMirar && (r.sublistas.length > 0 || r.sin_asignar.length > 0) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {r.una_tienda[0] && (
              <Boton
                variante="normal"
                disabled={poner.isPending}
                onClick={() => poner.mutate({ cadena: r.una_tienda[0].cadena })}
              >
                Todo en {nombreDeCadena(r.una_tienda[0].cadena)}
              </Boton>
            )}
            {r.repartido && (
              <Boton
                variante="normal"
                disabled={poner.isPending}
                onClick={() => {
                  // El reparto propuesto, **línea a línea**: se agrupan las líneas por
                  // la tienda que propone la API y se ponen de una vez. Decidir veinte
                  // líneas a mano para acabar en el reparto que ya está calculado no es
                  // decidir, es copiar; y ponerlas todas en una sola tienda sería otra
                  // cosa (es el botón de al lado).
                  const porCadena = new Map<string, string[]>()
                  for (const p of r.repartido!.productos ?? []) {
                    if (!p.linea_id) continue
                    const cola = porCadena.get(p.cadena) ?? []
                    cola.push(p.linea_id)
                    porCadena.set(p.cadena, cola)
                  }
                  for (const [cadena, lineas] of porCadena) {
                    poner.mutate({ cadena, lineas })
                  }
                }}
                title="Pone cada cosa en la tienda que propone el reparto más barato"
              >
                Repartir en {r.repartido.cadenas.length} tiendas
              </Boton>
            )}
            <Boton
              variante="sutil"
              disabled={poner.isPending}
              onClick={() => poner.mutate({ cadena: null })}
            >
              Quitar todas las tiendas
            </Boton>
          </div>
        )}
      </div>

      {/* ---- una sublista por tienda ---- */}
      {r.sublistas.map((s) => (
        <section key={s.cadena} className="mb-4 rounded-lg border border-neutral-200 dark:border-neutral-700">
          <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-neutral-200 px-3 py-2 dark:border-neutral-700">
            <h3 className="text-sm font-semibold">{nombreDeCadena(s.cadena)}</h3>
            <span className="cifra text-lg font-semibold">{euros(s.total_cent)}</span>
            <span className="text-xs text-tinta-suave">
              {s.lineas.length} línea{s.lineas.length === 1 ? '' : 's'} · {s.unidades} unidad
              {s.unidades === 1 ? '' : 'es'}
            </span>
            {s.ahorro_cent > 0 && (
              <Etiqueta tono="bien">−{euros(s.ahorro_cent)} con ofertas</Etiqueta>
            )}
            {!soloMirar && (
              <span className="ml-auto flex gap-2">
                <button
                  type="button"
                  disabled={poner.isPending}
                  onClick={() => poner.mutate({
                    cadena: s.cadena, lineas: idsDe(s), borrar: true,
                  })}
                  className="min-h-[44px] px-2 text-xs underline"
                  title="Borra todas las líneas de esta sublista"
                >
                  Borrar la sublista
                </button>
                <button
                  type="button"
                  disabled={poner.isPending}
                  onClick={() => poner.mutate({ cadena: null, lineas: idsDe(s) })}
                  className="min-h-[44px] px-2 text-xs underline"
                  title="Deja estas líneas sin tienda, sin borrarlas"
                >
                  Sin tienda
                </button>
              </span>
            )}
          </header>

          {s.sin_encontrar.length > 0 && (
            <div className="px-3 pt-2">
              <Aviso tono="aviso" titulo={`En ${nombreDeCadena(s.cadena)} no lo hay`}>
                {s.sin_encontrar.join(' · ')}. Sigue en la lista: cámbiale la tienda o
                bórralo.
              </Aviso>
            </div>
          )}

          <ul className="divide-y divide-neutral-100 dark:divide-neutral-800">
            {s.lineas.map((f) => (
              <li key={f.linea_id ?? `${s.cadena}-${f.nombre}`} className="grid gap-1 px-3 py-2">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium">{f.nombre}</span>
                  {f.cantidad > 1 && <span className="text-xs text-tinta-suave">×{f.cantidad}</span>}
                  <span className="cifra ml-auto font-semibold">{euros(f.coste_cent)}</span>
                </div>
                {f.promo && f.coste_sin_oferta_cent > f.coste_cent && (
                  <p className="text-xs text-emerald-800 dark:text-emerald-300">
                    {f.promo}: {euros(f.coste_sin_oferta_cent)} sin la oferta, o sea{' '}
                    {euros(f.coste_sin_oferta_cent - f.coste_cent)} menos
                  </p>
                )}
                {f.sugerencia && <p className="text-xs text-tinta-suave">{f.sugerencia}</p>}
                <AvisoIdentidad identidad={f.identidad} motivo={f.motivo} alternativa={f.alternativa} />
                <ElegirTienda fila={f} listaId={listaId} deshabilitado={soloMirar}
                              alCambiar={refresca} />
              </li>
            ))}
          </ul>

          {s.ofertas.length > 0 && (
            <p className="border-t border-neutral-200 px-3 py-2 text-xs text-tinta-suave dark:border-neutral-700">
              Ofertas aplicadas aquí: {s.ofertas.map((o) => o.promo).join(' · ')}. Total sin
              ellas: <span className="cifra">{euros(s.total_sin_ofertas_cent)}</span>.
            </p>
          )}
        </section>
      ))}

      {/* ---- lo que falta por decidir ---- */}
      {r.sin_asignar.length > 0 && (
        <section className="rounded-lg border border-dashed border-neutral-300 p-3 dark:border-neutral-600">
          <h3 className="mb-1 text-sm font-semibold">
            Sin decidir <span className="text-tinta-suave">({r.sin_asignar.length})</span>
          </h3>
          <p className="mb-2 text-xs text-tinta-suave">
            Esto no cuenta en el total de arriba hasta que elijas tienda: sumarlo por lo
            más barato daría un número que no corresponde a ninguna compra.
          </p>
          <ul className="grid gap-2">
            {r.sin_asignar.map((p) => (
              <li key={p.linea_id ?? p.nombre} className="grid gap-1">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium">{p.nombre}</span>
                  {p.cantidad > 1 && <span className="text-xs text-tinta-suave">×{p.cantidad}</span>}
                  {p.coste_cent != null ? (
                    <span className="cifra ml-auto text-sm text-tinta-suave">
                      desde {euros(p.coste_cent)}
                      {p.mas_barata && <> en {nombreDeCadena(p.mas_barata)}</>}
                    </span>
                  ) : (
                    <span className="ml-auto"><Etiqueta tono="aviso">no lo sé</Etiqueta></span>
                  )}
                </div>
                <ElegirTienda
                  // **La fila entera, no campo a campo.** Aqui se copiaban cuatro campos y se
                  // quedaban fuera `producto_id` y los tres `autorizado*`: el boton de consentir
                  // pulsaba, el POST contestaba 200, el refresco invalidaba lo correcto... y el
                  // boton seguia diciendo ?Aceptar el de Mercadona?, porque **el estado no llegaba
                  // a la pantalla**. Es el mismo hueco que habia en `main.py:800`, una capa mas
                  // arriba. Medido el 13 de octubre de 2026, septima vez hoy del mismo patron.
                  fila={{
                    linea_id: p.linea_id, nombre: p.nombre, opciones: p.opciones,
                    mas_barata: p.mas_barata ?? '',
                    producto_id: p.producto_id,
                    autorizado: p.autorizado,
                    autorizado_producto: p.autorizado_producto,
                    autorizado_cadena: p.autorizado_cadena,
                  }}
                  listaId={listaId}
                  deshabilitado={soloMirar}
                  alCambiar={refresca}
                />
              </li>
            ))}
          </ul>
        </section>
      )}
    </Tarjeta>
  )
}
