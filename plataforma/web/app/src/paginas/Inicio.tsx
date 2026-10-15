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
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { euros, eurosUnidad, nombreCadena, numero, porcentajeConSigno } from '../api/formato'
import { misListas, reparto, verLista, yo } from '../api/cesta'
import { FILTROS_VACIOS, consultaUtil, useBajadas, useBuscar } from '../api/consultas'
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
      <Tarjeta className="border-borde bg-marfil ">
        <p className="text-sm font-semibold">Todavía no tienes lista</p>
        <p className="mt-1 text-sm text-tinta-suave">
          Busca lo que compras y añádelo. A partir de ahí esta pantalla te dice cuánto te
          falta, en qué tienda conviene comprarlo y qué ha bajado de lo tuyo.
        </p>
        <Link
          to="/buscar"
          className="mt-3 inline-flex min-h-[44px] min-w-[44px] items-center text-sm font-semibold text-terracota underline "
        >
          Ver lo de siempre y añadir
        </Link>
      </Tarjeta>
    )
  }
  return (
    <Tarjeta className="border-borde bg-marfil ">
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
                  <span className="cifra font-semibold text-bien ">
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
        className="mt-3 inline-flex min-h-[44px] min-w-[44px] items-center text-sm font-semibold text-terracota underline "
      >
        Ver la lista entera y tachar
      </Link>
    </Tarjeta>
  )
}

/** El buscador, lo primero: *«esto que tengo en la mano, ¿esta caro?»*.
 *
 *  **Y busca mientras se escribe, sin mandar nada.** La primera version solo navegaba a
 *  `/buscar` al mandar el formulario, y eso es una regresion que encontro la puerta en un
 *  navegador de verdad: en la pantalla de antes (el buscador de `/buscar`) escribir ya
 *  buscaba, asi que quien conoce la aplicacion escribe «leche» y espera. Con un boton, o
 *  sabes que existe o te quedas mirando una caja de texto quieta -- y la barra (a) se juzga
 *  contra alguien que no sabe donde esta el boton.
 *
 *  Ahora los cuatro primeros resultados salen **debajo del campo, en la misma pantalla donde
 *  se escribe**, y el campo no se desmonta: la respuesta a la pregunta 2 no obliga a ir a
 *  ningun sitio. La espera de 350 ms es lo que se tarda en escribir la letra siguiente: sin
 *  ella, «leche» son cinco peticiones y cuatro para tirar.
 */
function Buscador() {
  const [texto, setTexto] = useState('')
  const [diferido, setDiferido] = useState('')
  const navegar = useNavigate()

  useEffect(() => {
    const t = setTimeout(() => setDiferido(texto.trim()), 350)
    return () => clearTimeout(t)
  }, [texto])

  const filtros = useMemo(
    // Cinco y no cuatro: el quinto es el que dice si hay mas. La respuesta no trae un total
    // (`RespuestaBuscar` no lo manda), asi que la unica forma honesta de decir «y hay mas» es
    // haber pedido una de mas.
    () => ({ ...FILTROS_VACIOS, q: diferido, limite: 5 }),
    [diferido],
  )
  const util = consultaUtil(filtros)
  const busqueda = useBuscar(filtros)
  const todos = util ? (busqueda.data?.resultados ?? []) : []
  const resultados = todos.slice(0, 4)

  return (
    <div>
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
            className="min-h-[44px] min-w-[44px] w-full rounded-lg border border-borde bg-white py-2 pl-10 pr-3 text-base "
          />
        </div>
        <button
          type="submit"
          className="min-h-[44px] rounded-lg bg-terracota px-3 text-sm font-semibold text-white "
        >
          Buscar
        </button>
      </form>

      {util && (
        <Tarjeta className="mt-2">
          {busqueda.isPending ? (
            <p className="text-sm text-tinta-suave">Buscando «{diferido}»…</p>
          ) : busqueda.isError ? (
            // **No se puede decir «nada con esas palabras» cuando lo que ha fallado es la
            // API**: sería culpar a quien escribe de un fallo nuestro, y encima le quita las
            // ganas de reintentar. Lo mismo que hace la pantalla del buscador, con sus
            // palabras.
            <p className="text-sm text-aviso ">
              No he podido buscar: la API no contesta. El resto de la pantalla sigue en pie.
            </p>
          ) : resultados.length === 0 ? (
            <p className="text-sm text-tinta-suave">
              Nada con esas palabras. Prueba con menos, o{' '}
              <Link to={`/buscar?q=${encodeURIComponent(diferido)}`} className="underline">
                míralo entero en el buscador
              </Link>
              .
            </p>
          ) : (
            <>
              <ul className="divide-y divide-borde ">
                {resultados.map((f) => (
                  <li key={`${f.grupo_id ?? 'suelto'}-${f.nombre}`}>
                    <Link
                      to={f.grupo_id === null ? `/buscar?q=${encodeURIComponent(diferido)}` : `/grupo/${f.grupo_id}`}
                      className="flex min-h-[44px] min-w-[44px] items-baseline justify-between gap-2 py-2"
                    >
                      <span className="min-w-0 truncate text-sm">{f.nombre}</span>
                      <span className="shrink-0 text-right text-sm">
                        <span className="cifra font-semibold">{euros(f.precio_cent)}</span>
                        {f.precio_unidad_cent != null && f.unidad && (
                          <span className="cifra block text-xs text-tinta-suave">
                            {eurosUnidad(f.precio_unidad_cent, f.unidad)}
                          </span>
                        )}
                        {f.cadena_mas_barata && (
                          <span className="block text-xs text-tinta-suave">
                            {nombreCadena(f.cadena_mas_barata)}
                          </span>
                        )}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              <Link
                to={`/buscar?q=${encodeURIComponent(diferido)}`}
                className="mt-1 inline-flex min-h-[44px] min-w-[44px] items-center text-sm font-semibold text-terracota underline "
              >
                {todos.length > resultados.length
                  ? 'Ver todos los resultados'
                  : 'Abrir en el buscador'}
              </Link>
            </>
          )}
        </Tarjeta>
      )}
    </div>
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
          <Link
            to="/avisos"
            className="inline-flex min-h-[44px] min-w-[44px] items-center justify-end text-xs font-semibold text-terracota underline "
          >
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
      <ul className="mt-2 divide-y divide-borde ">
        {bajadas.slice(0, 3).map((b, i) => (
          <li key={`${b.nombre}-${b.cadena}-${i}`} className="py-2">
            <div className="flex items-baseline justify-between gap-2">
              <span className="min-w-0 truncate text-sm">{b.nombre}</span>
              <span className="cifra shrink-0 text-sm font-semibold text-bien ">
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
                  <span className="cifra font-semibold text-tinta-fuerte ">
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
            className="inline-flex min-h-[44px] min-w-[44px] items-center font-semibold text-terracota underline "
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
    // *** El ritmo, *que es lo que reparte el alto. *** *
    //
    // *`space-y-bloque` (1,5 rem) y no un `space-y-4` de fabrica: *el hueco
    // **vertical** entre bloques **no existia en el tema** *-- *lo anadio la
    // FASE 1 --, *y es lo que evita que el contenido **se apine arriba.*** *
    <div className="space-y-bloque">
      {/* **El titulo de la pantalla, para quien navega por encabezados.** No se ve porque en
          esta pantalla la identidad la lleva la barra de abajo (el icono «Inicio» marcado) y
          poner un titular grande encima del buscador empujaria la primera respuesta hacia
          abajo, que es justo lo que esta pantalla vino a arreglar. Pero una pagina sin ningun
          `h1` deja a quien usa un lector de pantalla sin saber donde esta: medido con
          `data/debug/accesibilidad.py` el 27 de septiembre de 2026. */}
      <h1 className="sr-only">Inicio</h1>
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
                {/* Los enlaces pequeños de esta pantalla llevan su area de 44 px: medido en un
                    movil con la puerta mecanica el 27 de septiembre de 2026, este medía
                    **89 x 16 px** y el de «Avisos» **35 x 16**. Un enlace de texto de 16 px de
                    alto no se acierta con el pulgar en un pasillo, por mucho que se vea. */}
                <Link
                  to="/cesta"
                  className="inline-flex min-h-[44px] min-w-[44px] items-center justify-end text-xs font-semibold text-terracota underline "
                >
                  Toca para tachar
                </Link>
              </div>
              <ul className="mt-2 divide-y divide-borde ">
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
                          <span className="text-aviso ">
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