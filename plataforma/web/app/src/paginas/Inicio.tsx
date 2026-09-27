/** La pantalla de entrada: las cuatro preguntas, contestadas de un vistazo.
 *
 *  **Por que existe esta pantalla, y de donde sale.** El 27 de septiembre de 2026 se diseño
 *  con Stitch (proyecto `15743377346721964880`, pantalla «Cesta · Pantalla Principal») a
 *  partir de `.stitch/DESIGN.md`, y su motivo esta en `docs/PRUEBA-15-SEGUNDOS.md`: las cuatro
 *  preguntas con las que se abre la aplicacion se contestaban **entrando en otra pantalla**.
 *
 *      1. «¿Que me falta comprar y donde lo compro?»   antes: 1 toque (Buscar -> Cesta)
 *      2. «Esto que tengo en la mano, ¿esta caro?»     antes: 1 toque (escribir en Buscar)
 *      3. «¿Voy tachando bien?»                        antes: 0 toques (el numero de la barra)
 *      4. «¿Ha bajado algo de lo mio?»                 antes: 1 toque, o 3 por el panel
 *
 *  Aqui las cuatro estan **en la primera pantalla**: el reparto por tiendas y lo que falta
 *  (1 y 3), el buscador arriba (2) y lo que ha bajado de lo tuyo (4). No se quita ninguna
 *  pantalla: se contesta antes de tener que ir.
 *
 *  Tres decisiones que se ven en el codigo:
 *
 *  1. **El numero manda sobre el adorno**: «te faltan N cosas» sale grande y con la cifra en
 *     ancho fijo (`.cifra`), que es la regla del proyecto para todas las cifras.
 *  2. **Lo que se enseña es lo que la API dice que hay**, sin rellenar: si el reparto no ha
 *     cargado o la lista esta vacia, se dice lo que pasa y no se inventa un cero.
 *  3. **Los productos de la lista enlazan a la lista**, no tachan desde aqui. Tachar en el
 *     pasillo sin cobertura funciona porque `Cesta.tsx` tiene la cola del movil
 *     (`estado/cola.ts`); traer el tachado aqui sin esa cola seria un boton que a veces no
 *     hace nada, que es peor que no tenerlo. Cuando la cola se pueda reutilizar entera, este
 *     es el sitio donde debe estar.
 */
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { euros, eurosUnidad, nombreCadena, numero, porcentajeConSigno } from '../api/formato'
import { misListas, reparto, verLista, yo } from '../api/cesta'
import { useBajadas } from '../api/consultas'
import type { Baja, RepartoTiendas } from '../tipos'
import { Etiqueta, Tarjeta, cx } from '../componentes/ui'
import { IconoLupa } from '../componentes/iconos'

/** Las cuatro preguntas, en el orden en que se hacen en la vida.
 *
 *  **Y el caso que no contesta ninguna de las cuatro: la lista vacía.** Medido en un móvil el
 *  27 de septiembre de 2026, con una cuenta recién creada: la tarjeta decía «Lo que te falta:
 *  **0 cosas**» y un enlace a la lista, que también estaba vacía. Es verdad y no sirve para
 *  nada: quien acaba de entrar no tiene una lista vacía, **no tiene lista**, y lo que necesita
 *  es saber por dónde se empieza. Un cero no es una respuesta, es un hueco con forma de
 *  respuesta. Desde entonces se distinguen los tres estados: sin lista, con lista y todo
 *  cogido, y con cosas pendientes.
 */
function Cabecera({ reparto: r, porCoger, total, lineas }: {
  reparto: RepartoTiendas | undefined
  porCoger: number
  total: number
  lineas: number
}) {
  const cadenas = (r?.sublistas ?? []).filter((s) => s.lineas.length > 0)
  if (lineas === 0) {
    return (
      <Tarjeta className="border-sky-200 bg-sky-50/60 dark:border-sky-900 dark:bg-sky-950/30">
        <p className="text-sm font-semibold">Todavía no tienes lista</p>
        <p className="mt-1 text-sm text-tinta-suave">
          Busca lo que compras y añádelo. A partir de ahí esta pantalla te dice cuánto te
          falta, en qué tienda conviene comprarlo y qué ha bajado de lo tuyo.
        </p>
        <Link
          to="/buscar"
          className="mt-3 inline-flex min-h-[44px] items-center text-sm font-semibold text-sky-800 underline dark:text-sky-300"
        >
          Ver lo de siempre y añadir
        </Link>
      </Tarjeta>
    )
  }
  return (
    <Tarjeta className="border-sky-200 bg-sky-50/60 dark:border-sky-900 dark:bg-sky-950/30">
      <p className="text-sm text-tinta-suave">Lo que te falta</p>
      <p className="mt-0.5 text-2xl font-bold leading-tight">
        {porCoger === 0 ? (
          'No te falta nada'
        ) : (
          <>
            <span className="cifra">{numero(porCoger, 0)}</span>{' '}
            {porCoger === 1 ? 'cosa' : 'cosas'}
          </>
        )}
      </p>
      {cadenas.length > 0 && (
        <>
          <p className="mt-1 text-sm">
            {cadenas.map((s, i) => (
              <span key={s.cadena}>
                {i > 0 && ' · '}
                <span className="cifra font-semibold">{numero(s.lineas.length, 0)}</span> en{' '}
                {nombreCadena(s.cadena)}
              </span>
            ))}
          </p>
          {total > 0 && (
            <p className="mt-1 text-sm text-tinta-suave">
              Total estimado <span className="cifra font-semibold">{euros(total)}</span>
              {r && r.ahorro_cent > 0 && (
                <>
                  {' · '}con las ofertas te ahorras{' '}
                  <span className="cifra font-semibold text-emerald-700 dark:text-emerald-400">
                    {euros(r.ahorro_cent)}
                  </span>
                </>
              )}
            </p>
          )}
        </>
      )}
      <Link
        to="/cesta"
        className="mt-3 inline-flex min-h-[44px] items-center text-sm font-semibold text-sky-800 underline dark:text-sky-300"
      >
        Ver la lista entera y tachar
      </Link>
    </Tarjeta>
  )
}

/** El buscador, lo primero: *«esto que tengo en la mano, ¿esta caro?»*. */
function Buscador() {
  const [texto, setTexto] = useState('')
  const navegar = useNavigate()
  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault()
        const limpio = texto.trim()
        if (limpio) navegar(`/buscar?q=${encodeURIComponent(limpio)}`)
      }}
      className="flex items-center gap-2"
    >
      <label htmlFor="q-inicio" className="sr-only">
        Buscar un producto
      </label>
      <div className="relative flex-1">
        <IconoLupa
          width={18}
          height={18}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-tinta-suave"
        />
        <input
          id="q-inicio"
          type="search"
          inputMode="search"
          enterKeyHint="search"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="leche entera, atún, papel de cocina…"
          className="min-h-[44px] w-full rounded-lg border border-neutral-300 bg-white py-2 pl-10 pr-3 text-base dark:border-neutral-700 dark:bg-neutral-900"
        />
      </div>
      <button
        type="submit"
        className="min-h-[44px] rounded-lg bg-sky-700 px-3 text-sm font-semibold text-white dark:bg-sky-500 dark:text-neutral-900"
      >
        Buscar
      </button>
    </form>
  )
}

/** Lo que ha bajado, con el antes y el ahora.
 *
 *  **Y de quién es lo que se enseña, que es lo que hay que decir bien.** La API contesta
 *  `solo_mios` diciendo **si filtró**, no si se pidió: sin sesión no hay "lo mío" y devuelve
 *  las mayores bajadas del catálogo, así que el campo viene en `false`. Poniendo el título
 *  fijo «Ha bajado de lo tuyo», esta pantalla enseñaba sesenta bajadas de todo el catálogo
 *  bajo un título que mentía -- y es justo el caso de quien abre la aplicación por primera
 *  vez, que es quien no tiene cuenta. Es el mismo fallo que ya se corrigió en el servidor
 *  (`plataforma/api/main.py`), reintroducido en el cliente: el campo viaja para poder usarlo.
 */
function HaBajado({ bajadas, cargando, soloMios, haySesion, hayLista }: {
  bajadas: Baja[]
  cargando: boolean
  soloMios: boolean
  haySesion: boolean
  hayLista: boolean
}) {
  if (cargando) return null
  const titulo = soloMios ? 'Ha bajado de lo tuyo' : 'Lo que más ha bajado'
  if (bajadas.length === 0) {
    return (
      <Tarjeta>
        <p className="text-sm font-semibold">{titulo}</p>
        <p className="mt-1 text-sm text-tinta-suave">
          {!soloMios
            ? 'Nada ha bajado en los últimos 7 días en las cadenas que miras.'
            : hayLista
              ? 'Nada de tu lista ha bajado en los últimos 7 días. Se mira solo lo que está en tus listas y con la fecha de los precios a la vista.'
              : 'Todavía no hay nada tuyo que mirar: en cuanto tengas algo en la lista, aquí sale lo que haya bajado.'}
        </p>
      </Tarjeta>
    )
  }
  return (
    <Tarjeta>
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-semibold">{titulo}</p>
        {soloMios && (
          <Link to="/avisos" className="text-xs font-semibold text-sky-800 underline dark:text-sky-300">
            Avisos
          </Link>
        )}
      </div>
      {!soloMios && (
        <p className="mt-1 text-xs text-tinta-suave">
          Son las mayores bajadas del catálogo, no las de tu lista.{' '}
          {haySesion ? (
            'En cuanto tengas algo apuntado, esta tarjeta enseña solo lo tuyo.'
          ) : (
            <>
              Para ver lo tuyo,{' '}
              <Link to="/ajustes" className="underline">
                entra o crea una cuenta
              </Link>
              .
            </>
          )}
        </p>
      )}
      <ul className="mt-2 divide-y divide-neutral-200 dark:divide-neutral-700">
        {bajadas.slice(0, 3).map((b, i) => (
          <li key={`${b.nombre}-${b.cadena}-${i}`} className="py-2">
            <div className="flex items-baseline justify-between gap-2">
              <span className="min-w-0 truncate text-sm">{b.nombre}</span>
              <span className="cifra shrink-0 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                {porcentajeConSigno(b.variacion_pct)}
              </span>
            </div>
            <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 text-xs text-tinta-suave">
              <span>{nombreCadena(b.cadena)}</span>
              {b.precio_unidad_antes_cent != null && b.precio_unidad_cent != null && (
                <span>
                  <span className="cifra line-through">
                    {eurosUnidad(b.precio_unidad_antes_cent, b.unidad)}
                  </span>{' '}
                  <span className="cifra font-semibold text-neutral-900 dark:text-neutral-100">
                    {eurosUnidad(b.precio_unidad_cent, b.unidad)}
                  </span>
                </span>
              )}
              {b.solo_con_tarjeta && <Etiqueta tono="aviso">solo con tarjeta</Etiqueta>}
            </div>
          </li>
        ))}
      </ul>
      {bajadas.length > 3 && (
        <p className="mt-2 text-xs">
          <Link
            to="/panel?pestana=bajadas"
            className="font-semibold text-sky-800 underline dark:text-sky-300"
          >
            y <span className="cifra">{numero(bajadas.length - 3, 0)}</span> más bajadas
          </Link>
        </p>
      )}
    </Tarjeta>
  )
}

export function Inicio() {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const listaId = listas.data?.find((l) => l.es_de_casa)?.id ?? listas.data?.[0]?.id ?? null
  const detalle = useQuery({
    queryKey: ['lista', listaId],
    queryFn: () => verLista(listaId as string),
    enabled: listaId != null,
  })
  const rep = useQuery({
    queryKey: ['reparto', listaId],
    queryFn: () => reparto(listaId as string),
    enabled: listaId != null,
  })
  const bajadas = useBajadas(7, false, [], sesion.data?.usuario != null)

  const lineas = detalle.data?.lineas ?? []
  const porCoger = lineas.filter((l) => l.tachado_en === null)
  const sinSesion = sesion.data?.usuario == null

  return (
    <div className="space-y-4">
      <Buscador />

      {sinSesion ? (
        <Tarjeta>
          <p className="text-sm font-semibold">Tu compra, de un vistazo</p>
          <p className="mt-1 text-sm text-tinta-suave">
            Con una cuenta, esta pantalla te dice lo que te falta, en qué tienda conviene
            comprarlo y qué ha bajado de lo tuyo.{' '}
            <Link to="/ajustes" className="underline">
              Entra o crea una cuenta
            </Link>
            .
          </p>
        </Tarjeta>
      ) : (
        <>
          <Cabecera reparto={rep.data} porCoger={porCoger.length}
                    total={rep.data?.total_cent ?? 0} lineas={lineas.length} />

          {porCoger.length > 0 && (
            <Tarjeta>
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-semibold">Pendientes de coger</p>
                <Link to="/cesta" className="text-xs font-semibold text-sky-800 underline dark:text-sky-300">
                  Toca para tachar
                </Link>
              </div>
              <ul className="mt-2 divide-y divide-neutral-200 dark:divide-neutral-700">
                {porCoger.slice(0, 4).map((l) => {
                  // La cadena y el precio de cada linea salen del reparto, que es quien
                  // sabe donde esta mas barata cada cosa. Si no ha cargado, se enseña el
                  // nombre y nada mas: un hueco es mejor que una cifra inventada.
                  const enTienda = (rep.data?.sublistas ?? [])
                    .flatMap((s) => s.lineas.map((f) => ({ ...f, cadena: s.cadena })))
                    .find((f) => f.linea_id === l.id)
                  return (
                    <li key={l.id} className="py-2">
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="min-w-0 truncate text-sm">{l.nombre_visto}</span>
                        {enTienda && (
                          <span className="cifra shrink-0 text-sm font-semibold">
                            {euros(enTienda.coste_cent)}
                          </span>
                        )}
                      </div>
                      <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 text-xs text-tinta-suave">
                        {l.pasillo && <span>{l.pasillo}</span>}
                        {enTienda && <span>en {nombreCadena(enTienda.cadena)}</span>}
                        {!enTienda && l.grupo_id == null && (
                          <span className="text-amber-800 dark:text-amber-400">
                            sin comparar: no está en el catálogo
                          </span>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
              {porCoger.length > 4 && (
                <p className="mt-2 text-xs text-tinta-suave">
                  y <span className="cifra">{numero(porCoger.length - 4, 0)}</span> más en la lista
                </p>
              )}
            </Tarjeta>
          )}
        </>
      )}

      <HaBajado bajadas={bajadas.data?.resultados ?? []} cargando={bajadas.isLoading}
                soloMios={bajadas.data?.solo_mios === true} haySesion={!sinSesion}
                hayLista={lineas.length > 0} />

      <p className={cx('px-1 text-xs text-tinta-suave')}>
        {rep.data?.fecha_datos
          ? `Precios del ${rep.data.fecha_datos}. Se comparan cinco cadenas y se enseña el precio por unidad.`
          : 'Precios de la última captura. Se comparan cinco cadenas y se enseña el precio por unidad.'}
      </p>
    </div>
  )
}
