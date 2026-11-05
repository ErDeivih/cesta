/** *** COMPARAR MI CESTA: la lista entera, valorada en cada cadena. *** *
 *
 *  *Es la casilla «Comparar mi cesta» de `WALL.md`: «lo que compro habitualmente y donde me sale
 *  mejor esta semana».* *La respuesta que tiene que dar la pantalla es **una**: cuanto cuesta
 *  **esta** lista en cada cadena y donde conviene comprarla.*
 *
 *  **Lo que ya habia, y por que esto no es repetirlo.** `Cesta.tsx` enseña el reparto por tiendas
 *  (`RepartoEnTiendas`) y una rejilla de «la lista entera en una tienda» al final. La rejilla daba
 *  seis totales **sin decir cual estaba completo**: una cadena a la que le faltan cuatro productos
 *  salia mas barata y se llevaba la etiqueta «la mas barata». Aqui:
 *
 *   - el total de cada cadena se dice con **cuantos productos lo forman** («con 8 de 12»);
 *   - **solo se corona** una cadena que tiene los 12, y si ninguna los tiene, se dice;
 *   - la diferencia con la mas cara se calcula **entre cadenas igual de completas**, que es la
 *     unica resta que significa algo;
 *   - y debajo, producto a producto, se ve **de donde sale** la diferencia.
 *
 *  **Los numeros son de la API, no de esta pantalla.** `GET /listas/{id}/reparto` ya calcula las
 *  ofertas, agrupa por producto y reparte el descuento entre lineas (`api/cesta.py`); aqui no se
 *  suma ni se resta nada: se ordena, se cuenta y se enseña. *Lo unico que se calcula en el
 *  navegador son las cuentas de cuantos productos entran en cada total, y la resta entre dos
 *  totales completos.*
 *
 *  *** LAS OFERTAS, COMO CONDICION. *** *El motor no resta las de club, cupon ni «solo online»
 *  (`core/promos.py`: `acumulable` y `solo_online` no bajan el ticket), asi que un 2x1 con una
 *  unidad, una oferta de tarjeta o una de internet **no pueden** presentarse como precio final.*
 *  Aqui se enseña el texto del folleto tal cual -- que ya esta en el idioma de quien compra -- y se
 *  dice **que pasa con el total**: si la oferta ya va aplicada (el numero lo dice: hay diferencia
 *  entre el coste con y sin oferta) se dice cuanto; si no, se dice que **no baja lo que pagas**, y
 *  cuando el texto nombra tarjeta, cupon o club, se dice tambien por que.
 *
 *  *** LO QUE NO SE INVENTA. *** *Una linea sin precio en ninguna cadena **no se compara**: se
 *  enseña como «no comparable» y no entra en ningun total. Una cadena que no llega a todos los
 *  productos **no gana**: su total se lee «con N de M» y la frase que corona dice que no se puede
 *  comparar con las completas.* *Y el €/kg solo se enseña cuando se puede: se pide al abrir la
 *  linea (`GET /producto/{fuente}/{id}`), y si el formato no es comparable (`comparable` en la
 *  ficha) se dice, en vez de enseñar un numero que no significa nada.*
 *
 *  **Los cuatro estados, y la puerta antes que el error**: cargando (esqueleto), con datos, sin
 *  sesion (`EntraParaVer`, que es un estado y no un fallo), lista sin lineas, y error con
 *  reintento. *Un 401 que llegue tarde tambien es puerta: si la sesion se ha caido, no se enseña
 *  «No he podido traer esto».*
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { misListas, reparto as pedirReparto, verLista, yo } from '../api/cesta'
import { esErrorApi } from '../api/cliente'
import { useProducto } from '../api/consultas'
import { euros, eurosUnidad, nombreCadena } from '../api/formato'
import { EntraParaVer } from '../componentes/PuertaDeSesion'
import { Aviso, Cargando, Etiqueta, Fallo, Resumen, Tarjeta, Vacio, cx } from '../componentes/ui'
import type { Linea, OpcionTienda, RepartoTiendas } from '../tipos'

/* ------------------------------------------------------- lo que manda la API --- */

/** Una linea resuelta en una cadena. Es `_serializa` de `api/cesta.py`, recortado a lo que se
 *  pinta: el reparto lo manda por cadena en `una_tienda[].productos`. */
interface PrecioEnCadena {
  producto_id: string
  nombre: string
  cadena: string
  unidades: number
  /** Lo que cuesta la cantidad pedida **con la oferta aplicada**, si la hay. */
  coste_cent: number
  /** Lo mismo **sin oferta**: la diferencia es lo que ahorra, y es un hecho de los numeros. */
  coste_sin_oferta_cent: number
  promo: string | null
  sugerencia?: string | null
  linea_id: string | null
  autorizada?: boolean
  identidad?: string | null
  motivo?: string | null
}

/** Lo que la linea costaria en una cadena si se aceptara el equivalente que propone el motor. */
interface PorConfirmar {
  linea_id?: string | null
  nombre: string
  coste_cent: number
  identidad?: string | null
  motivo?: string | null
}

/** *** Los campos que `OpcionTienda` no declara, y que la API manda. *** *
 *
 *  *`una_tienda` trae `contadas`, `sin_autorizar`, `pendientes` y `productos` desde que el reparto
 *  se escribe (`api/cesta.py:583`), pero el tipo del front solo declara los seis de siempre.* *Se
 *  declaran **aqui, opcionales**, y no en `tipos.ts`, porque esta pantalla es la unica que los lee:
 *  si un dia la API deja de mandarlos, lo que se pierde es el detalle, no el total.* *
 */
interface CadenaComparada extends OpcionTienda {
  /** Lineas que de verdad suman en `total_cent`: las que se pueden comprar tal cual. */
  contadas?: number
  /** Lineas resueltas con un equivalente que la persona no ha confirmado: no suman. */
  sin_autorizar?: number
  pendientes?: PorConfirmar[]
  productos?: PrecioEnCadena[]
}

/* --------------------------------------------------------------- la pantalla --- */

export function CompararCesta() {
  const { listaId: parametro } = useParams<{ listaId: string }>()
  const listaId = parametro ?? ''

  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const detalle = useQuery({
    queryKey: ['lista', listaId],
    queryFn: () => verLista(listaId),
    enabled: Boolean(listaId) && sesion.data?.usuario != null,
  })
  const comparacion = useQuery({
    queryKey: ['reparto', listaId],
    queryFn: () => pedirReparto(listaId),
    enabled: Boolean(listaId) && sesion.data?.usuario != null,
  })

  if (sesion.isLoading) return <Cargando que="tu cesta" />

  // **Sin sesion es un estado, no un error**: el mismo cartel que las otras seis pantallas.
  if (!sesion.data?.usuario) {
    return <EntraParaVer texto="Comparar tu cesta necesita tu lista, y la lista se guarda con tu cuenta." />
  }

  const error = comparacion.error ?? detalle.error
  if (error) {
    // *Si lo que ha caducado es la sesion, lo que toca es la puerta: `textoDeError` diria «Entra
    // para ver esto» dentro de un aviso rojo con boton de reintentar, y no es un fallo.*
    if (esErrorApi(error) && error.estado === 401) {
      return <EntraParaVer texto="Vuelve a entrar para comparar tu lista." />
    }
    return (
      <Fallo
        error={error}
        reintentar={() => {
          void comparacion.refetch()
          void detalle.refetch()
        }}
      />
    )
  }

  if (comparacion.isLoading || detalle.isLoading || !comparacion.data || !detalle.data) {
    return <Cargando que="la comparación" filas={6} />
  }

  return (
    <LaComparacion
      listaId={listaId}
      nombreDeLaLista={listas.data?.find((l) => l.id === listaId)?.nombre ?? null}
      lineas={detalle.data.lineas}
      comparacion={comparacion.data}
    />
  )
}

function LaComparacion({ listaId, nombreDeLaLista, lineas, comparacion }: {
  listaId: string
  nombreDeLaLista: string | null
  lineas: Linea[]
  comparacion: RepartoTiendas
}) {
  const cadenas = comparacion.una_tienda as CadenaComparada[]
  const total = comparacion.lineas
  const porComprar = lineas.filter((l) => l.tachado_en === null)
  const tachadas = lineas.length - porComprar.length

  // **Lo que la comparacion no cuenta y hay que decir.** El reparto deja fuera las lineas cuyo
  // grupo ya no es el producto que dicen (`catalogo.lineas_movidas`): contarlas seria dar el
  // precio de otro producto. Se dicen, y con la salida puesta (volver a la lista y buscarlo).
  const movidas = porComprar.filter((l) => l.producto_movido)
  const filas = porComprar.filter((l) => !l.producto_movido)

  const matriz = matrizPorLinea(cadenas)
  const resumen = contarLineas(filas, matriz)
  /** *** Si el reparto NO vino con el detalle por linea. *** *
   *
   *  *`una_tienda[].productos` lo manda la API de hoy, pero el tipo del front no lo declara y un
   *  dia puede no llegar.* *Sin el, la tabla por producto estaria **vacia**, y una tabla vacia se
   *  lee como «no se puede comparar nada» -- que seria falso: los totales de arriba si estan.*
   *  *Asi que cuando no hay detalle, **no se afirma nada de producto a producto**: se enseñan los
   *  totales, que es lo que si llego.* *Un dato que no esta no se convierte en un cero.*
   */
  const hayDetalle = cadenas.some(
    (c) => (c.productos?.length ?? 0) + (c.pendientes?.length ?? 0) > 0,
  )

  if (total === 0) {
    // *Una lista vacia y una lista cuyos productos han cambiado no dicen lo mismo:* la segunda
    // tiene salida («búscalos otra vez») y decirle a alguien que «añada algo» seria no haberlo
    // mirado.
    const soloMovidas = movidas.length > 0 && movidas.length === porComprar.length
    return (
      <div className="flex min-h-full flex-col gap-bloque">
        <Vacio titulo="Esta lista no tiene nada que comparar" comoPagina className="grow">
          <p>
            {soloMovidas
              ? 'Los productos de esta lista han cambiado en el catálogo. Búscalos y vuelve a añadirlos.'
              : tachadas > 0 && tachadas === lineas.length
                ? 'Ya está todo en el carro. Abre otra lista o añade algo a esta.'
                : 'Añade algún producto y vuelve: aquí verás cuánto cuesta en cada cadena.'}
          </p>
          <p className="mt-3">
            <EnlaceALaLista listaId={listaId} texto="Volver a la lista" />
          </p>
        </Vacio>
      </div>
    )
  }

  if (total > 0 && cadenas.length === 0) {
    // *Con lineas pero sin ninguna cadena que las resuelva no hay comparacion posible, y decirlo
    // es la respuesta: un cero inventado seria peor que este cartel.*
    return (
      <div className="flex min-h-full flex-col gap-bloque">
        <Vacio titulo="Hoy no puedo comparar esta lista" comoPagina className="grow">
          <p>
            Ninguna de las cadenas tiene hoy los productos de esta lista. Puede que sean cosas que
            no vendan, o que hayan cambiado de formato.
          </p>
          <p className="mt-3">
            <EnlaceALaLista listaId={listaId} texto="Volver a la lista" />
          </p>
        </Vacio>
      </div>
    )
  }

  /* ---- quien gana, y con que derecho ---- */
  const completas = cadenas
    .filter((c) => contadasDe(c) === total)
    .sort((a, b) => a.total_cent - b.total_cent)
  const ganadora = completas[0] ?? null
  const masCara = completas.length > 1 ? completas[completas.length - 1] : null
  const diferencia = ganadora && masCara ? masCara.total_cent - ganadora.total_cent : null

  const ordenadas = ordenarCadenas(cadenas, total)
  const cadenasConOfertaCondicionada = ordenadas.filter((c) =>
    (c.productos ?? []).some((p) => p.promo && /club|tarjeta|cupon|cupón|acum|online|internet|web/i.test(p.promo)),
  ).length

  return (
    <div className="flex flex-col gap-seccion">
      {/* ------------------------------------------------------- de que lista --- */}
      <header className="flex flex-col gap-2">
        <h2 className="font-serif text-titulo text-tinta-fuerte">Comparar mi cesta</h2>
        <p className="text-cuerpo text-tinta-fuerte">
          {nombreDeLaLista && <strong>{nombreDeLaLista}</strong>}
          {nombreDeLaLista ? ' · ' : ''}
          {plural(total, 'producto', 'productos')}
        </p>
        {hayDetalle && (
          <p className="text-cuerpo text-tinta-suave">
            {resumen.comparables > 0
              ? `${resumen.comparables} ${resumen.comparables === 1 ? 'se puede comparar' : 'se pueden comparar'} entre cadenas`
              : 'Ningún producto se puede comparar entre cadenas'}
            {resumen.noComparables > 0 && (
              <>
                {' '}y {resumen.noComparables} no
                {resumen.soloUnaCadena > 0 && (
                  <> ({resumen.soloUnaCadena} solo {resumen.soloUnaCadena === 1 ? 'está' : 'están'} en una cadena
                    {resumen.sinPrecio > 0 && `, ${resumen.sinPrecio} sin precio hoy`})</>
                )}
                {resumen.soloUnaCadena === 0 && resumen.sinPrecio > 0 && (
                  <> ({resumen.sinPrecio} sin precio hoy)</>
                )}
              </>
            )}
            .
          </p>
        )}
        {tachadas > 0 && (
          <p className="text-etiqueta text-tinta-suave">
            {tachadas === 1
              ? '1 producto ya está en el carro y no lo cuento.'
              : `${tachadas} productos ya están en el carro y no los cuento.`}
          </p>
        )}
        {/* **En cuantas cadenas se ha podido valorar, dicho.** *No todas las cadenas tienen
            todos los productos, y algunas no entran en las comparaciones (una cadena de la que
            solo se capturan las ofertas de la semana no puede decir «no lo tengo» sin mentir).*
            *El numero sale de los datos de esta lista, no de una constante: si mañana se valoran
            mas, la frase sigue siendo cierta sin tocar nada.* */}
        <p className="text-etiqueta text-tinta-suave">
          {cadenas.length === 1
            ? 'Lo he podido valorar en 1 cadena.'
            : `Lo he podido valorar en ${cadenas.length} cadenas.`}
        </p>
        {movidas.length > 0 && (
          <Aviso tono="aviso">
            {movidas.length === 1
              ? '1 producto ha cambiado en el catálogo y no se puede comparar. Búscalo y vuelve a añadirlo a la lista.'
              : `${movidas.length} productos han cambiado en el catálogo y no se pueden comparar. Búscalos y vuelve a añadirlos a la lista.`}
          </Aviso>
        )}
        <EnlaceALaLista listaId={listaId} texto="Volver a la lista" />
      </header>

      {/* ------------------------------------------------- dónde sale mejor --- */}
      <section aria-labelledby="totales-de-la-cesta" className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h3 id="totales-de-la-cesta" className="text-entrada font-semibold text-tinta-fuerte">
            Total en cada cadena
          </h3>
          <p className="text-cuerpo text-tinta-fuerte">
            <QuienGana ganadora={ganadora} masCara={masCara} diferencia={diferencia} total={total} />
          </p>
        </div>

        <ul className="grid gap-2">
          {ordenadas.map((c) => (
            <CadenaEnLaLista
              key={c.cadena}
              cadena={c}
              total={total}
              contadas={contadasDe(c)}
              esLaMasBarata={ganadora?.cadena === c.cadena}
              // *La diferencia se enseña **por cadena y contra la mas barata**, y solo entre
              // las que tienen la lista entera: restar un total incompleto da un numero que no
              // es una diferencia de nada.*
              diferenciaConLaMasBarata={
                ganadora && ganadora.cadena !== c.cadena && contadasDe(c) === total
                  ? c.total_cent - ganadora.total_cent
                  : null
              }
            />
          ))}
        </ul>

        {ordenadas.length < 2 && (
          <p className="text-cuerpo text-tinta-suave">
            Solo una cadena tiene precio para algo de esta lista: no hay con qué comparar.
          </p>
        )}

        {resumen.conEquivalenteSinConfirmar > 0 && (
          <Aviso tono="aviso">
            {resumen.conEquivalenteSinConfirmar === 1
              ? '1 producto solo tiene precio como equivalente de otro. Mientras no lo confirmes, no suma en ningún total.'
              : `${resumen.conEquivalenteSinConfirmar} productos solo tienen precio como equivalente de otro. Mientras no los confirmes, no suman en ningún total.`}{' '}
            <Link to={`/compra/listas/${listaId}`} className="underline">
              Confirmarlos en la lista
            </Link>
          </Aviso>
        )}

        {ordenadas.some((c) => contadasDe(c) < total) && (
          <p className="text-cuerpo text-tinta-suave">
            Una cadena a la que le faltan productos tiene un total más bajo: por eso se dice
            cuántos entran, y solo se compara con las que los tienen todos.
          </p>
        )}
      </section>

      {/* ------------------------------------------------ producto a producto --- */}
      {hayDetalle && (
        <section aria-labelledby="producto-a-producto" className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <h3 id="producto-a-producto" className="text-entrada font-semibold text-tinta-fuerte">
              Producto a producto
            </h3>
            <p className="text-etiqueta text-tinta-suave">
              Abre un producto para ver lo que cuesta en cada cadena y su precio por kilo.
            </p>
          </div>

          <ul className="grid gap-2">
            {filas.map((linea) => (
              <LineaComparada
                key={linea.id}
                linea={linea}
                celdas={matriz.get(linea.id) ?? []}
                cadenas={ordenadas}
              />
            ))}
          </ul>

          {cadenasConOfertaCondicionada > 0 && (
            <p className="text-etiqueta text-tinta-suave">
              Las ofertas que piden tarjeta, cupón o comprar por internet se enseñan como
              condición: no bajan lo que pagas en caja, y por eso no están restadas.
            </p>
          )}
        </section>
      )}
    </div>
  )
}

/* --------------------------------------------------------------- piezas --- */

/** La frase que contesta «¿dónde conviene?», con lo que se puede afirmar. */
function QuienGana({ ganadora, masCara, diferencia, total }: {
  ganadora: CadenaComparada | null
  masCara: CadenaComparada | null
  diferencia: number | null
  total: number
}) {
  if (!ganadora) {
    return (
      <>
        Ninguna cadena tiene los {plural(total, 'producto', 'productos')} de la lista. Los totales de
        abajo son de lo que hay en cada una, y por eso no se pueden comparar entre sí.
      </>
    )
  }
  return (
    <>
      Con todo lo de la lista, lo más barato es{' '}
      <strong>{nombreCadena(ganadora.cadena)}</strong>:{' '}
      <span className="cifra">{euros(ganadora.total_cent)}</span>.
      {masCara && diferencia !== null && diferencia > 0 && (
        <>
          {' '}
          La más cara de las que también lo tienen todo, {nombreCadena(masCara.cadena)}, sale{' '}
          <span className="cifra">{euros(diferencia)}</span> más.
        </>
      )}
      {!masCara && (
        <> Es la única cadena que tiene la lista entera, así que no hay una segunda con la que compararla.</>
      )}
    </>
  )
}

/** Una cadena con su total y, si le falta algo, dicho. */
function CadenaEnLaLista({ cadena, total, contadas, esLaMasBarata, diferenciaConLaMasBarata }: {
  cadena: CadenaComparada
  total: number
  contadas: number
  esLaMasBarata: boolean
  /** Lo que esta cadena cuesta de mas que la mas barata, o `null` si no se puede restar. */
  diferenciaConLaMasBarata: number | null
}) {
  const faltan = cadena.faltan.length
  return (
    <li
      className={cx(
        'rounded-campo border p-3',
        esLaMasBarata ? 'border-bien bg-bien-suave' : 'border-borde bg-papel',
      )}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h4 className="text-entrada font-semibold text-tinta-fuerte">{nombreCadena(cadena.cadena)}</h4>
        <p className="cifra text-precio font-semibold text-tinta-fuerte">{euros(cadena.total_cent)}</p>
      </div>

      <div className="mt-1 flex flex-wrap items-center gap-2">
        <span className="text-etiqueta text-tinta-suave">
          con {contadas} de {total} {total === 1 ? 'producto' : 'productos'}
        </span>
        {esLaMasBarata && <Etiqueta tono="bien">la más barata</Etiqueta>}
        {diferenciaConLaMasBarata !== null && diferenciaConLaMasBarata > 0 && (
          <span className="text-etiqueta text-tinta-suave">
            {euros(diferenciaConLaMasBarata)} más que la más barata
          </span>
        )}
      </div>

      {faltan > 0 && (
        <p className="mt-1 text-etiqueta text-tinta-suave">
          No lo tiene: {cadena.faltan.join(' · ')}
        </p>
      )}
    </li>
  )
}

/** Una linea de la lista, con lo que cuesta en cada cadena. */
function LineaComparada({ linea, celdas, cadenas }: {
  linea: Linea
  celdas: CeldaDeLaLinea[]
  /** **Todas** las cadenas, no solo las que tienen el producto: una cadena donde no esta
   *  tambien es una respuesta, y es la que explica por que su total es mas bajo. */
  cadenas: CadenaComparada[]
}) {
  const [abierta, setAbierta] = useState(false)
  const autorizadas = celdas.filter((c) => c.autorizada)
  const desde = autorizadas.length
    ? Math.min(...autorizadas.map((c) => c.coste_cent))
    : null
  // *La ficha que se abre —y su precio por kilo— es la de **la cadena mas barata** de esta
  // linea: es la que se mira, y su €/kg es el que se acaba comparando en la estanteria.*
  const conProducto =
    [...autorizadas].sort((a, b) => a.coste_cent - b.coste_cent)[0] ?? celdas[0] ?? null
  // *** El estado de la linea, dicho sin adornos.*** *
  // *«desde 1,29 €» es una comparacion; «1,29 € · solo en Aldi» no lo es, y son dos cosas
  // distintas aunque el numero sea el mismo.* *Y una linea que solo tiene precio de un
  // equivalente sin confirmar no se puede llamar comparable.*
  const soloEn = desde !== null && autorizadas.length === 1 ? autorizadas[0].cadena : null
  const estado =
    desde === null
      ? celdas.length === 0
        ? 'no comparable'
        : 'por confirmar'
      : soloEn
        ? `${euros(desde)} · solo en ${nombreCadena(soloEn)}`
        : `desde ${euros(desde)}`

  return (
    <li className="rounded-campo border border-borde bg-papel">
      <details
        // *La linea se abre **y solo entonces** se pide el precio por kilo: una peticion por
        // producto abierto, no doce al entrar.*
        onToggle={(e) => setAbierta(e.currentTarget.open)}
      >
        <Resumen className="px-3">
          <span className="min-w-0 flex-1 break-words text-cuerpo font-medium text-tinta-fuerte">
            {linea.nombre_visto}
            {linea.cantidad > 1 && (
              <span className="ml-2 text-etiqueta font-normal text-tinta-suave">
                {linea.cantidad} unidades
              </span>
            )}
          </span>
          <span
            className={cx(
              'cifra shrink-0 text-etiqueta',
              desde !== null ? 'text-tinta-fuerte' : 'text-tinta-suave',
            )}
          >
            {estado}
          </span>
        </Resumen>

        <div className="px-3 pb-3">
          <ul className="grid gap-1">
            {cadenas.map((cadena) => {
              const celda = celdas.find((c) => c.cadena === cadena.cadena)
              if (!celda) {
                return (
                  <li
                    key={cadena.cadena}
                    className="flex flex-wrap items-baseline justify-between gap-x-2 border-t border-borde pt-1 first:border-0 first:pt-0"
                  >
                    <span className="text-etiqueta text-tinta-suave">
                      {nombreCadena(cadena.cadena)}
                    </span>
                    <span className="text-etiqueta text-tinta-suave">no está</span>
                  </li>
                )
              }
              return (
                <li
                  key={cadena.cadena}
                  className="border-t border-borde pt-1 first:border-0 first:pt-0"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                    <span className="text-etiqueta text-tinta-suave">{nombreCadena(cadena.cadena)}</span>
                    <span className="cifra text-precio-fila font-medium text-tinta-fuerte">
                      {euros(celda.coste_cent)}
                      {!celda.autorizada && (
                        <span className="ml-1 text-etiqueta font-normal text-aviso">por confirmar</span>
                      )}
                    </span>
                  </div>
                  {celda.promo && <Oferta promo={celda.promo} ahorro_cent={celda.ahorro_cent} />}
                  {celda.sugerencia && (
                    <p className="text-etiqueta text-tinta-suave">{celda.sugerencia}</p>
                  )}
                </li>
              )
            })}
          </ul>

          {celdas.length === 0 && (
            <p className="mt-1 text-etiqueta text-tinta-suave">
              Hoy no está en ninguna cadena, así que no se puede comparar.
            </p>
          )}

          {abierta && conProducto && <PrecioPorKilo productoId={conProducto.producto_id} />}

          <p className="mt-2 flex flex-wrap items-center gap-3">
            {conProducto && <EnlaceALaFicha productoId={conProducto.producto_id} />}
            <Link
              to={`/compra?q=${encodeURIComponent(linea.nombre_visto)}`}
              className="inline-flex min-h-[44px] items-center text-cuerpo text-tinta-suave underline"
            >
              Buscar «{linea.nombre_visto}»
            </Link>
          </p>
        </div>
      </details>
    </li>
  )
}

/** *** LA OFERTA, COMO LO QUE ES: UNA CONDICION. *** *
 *
 *  *El texto se enseña tal cual porque es lo que dice el folleto, y ya esta escrito para quien
 *  compra («2ª unidad al 50 %», «solo con tarjeta», «5 EUR de descuento comprando 15»).* *Lo que
 *  no se hace es convertirlo en un precio:*
 *
 *   - **si el numero dice que esta aplicada** (el coste con oferta es menor que sin ella), se
 *     enseña cuanto baja, porque eso ya esta dentro del total;
 *   - **si no**, se dice que no baja lo que se paga, y cuando el texto nombra tarjeta, cupon,
 *     monedero o internet se dice tambien el motivo.
 *
 *  *Y no se deduce la mecanica: el tipo normalizado no viaja a la interfaz (`AUDITORIA-APP`
 *  §4).* *Se leen las palabras del folleto y los dos numeros de la API; nada mas.*
 */
function Oferta({ promo, ahorro_cent }: { promo: string; ahorro_cent: number }) {
  const pideTarjeta = /club|tarjeta|cupon|cupón|acum|monedero|cheque|vale/i.test(promo)
  const soloPorInternet = /online|internet|\bweb\b/i.test(promo)
  return (
    <p className="text-etiqueta">
      <span className="text-tinta-suave">Oferta: «{promo}»</span>
      <span className="block text-tinta-fuerte">
        {ahorro_cent > 0
          ? `Ya va aplicada: ${euros(ahorro_cent)} menos en este producto.`
          : pideTarjeta
            ? 'Solo con tarjeta o cupón del club: no baja lo que pagas en caja.'
            : soloPorInternet
              ? 'Solo comprando por internet: no baja lo que pagas en la tienda.'
              : 'Con lo que llevas no baja este total.'}
      </span>
    </p>
  )
}

/** El €/kg, que no viene en el reparto: se pide a la ficha y solo cuando la linea se abre. */
function PrecioPorKilo({ productoId }: { productoId: string }) {
  const corte = productoId.indexOf(':')
  const fuente = corte > 0 ? productoId.slice(0, corte) : productoId
  const idFuente = corte > 0 ? productoId.slice(corte + 1) : ''
  const producto = useProducto(fuente, idFuente)

  if (producto.isLoading) {
    return <p className="mt-1 text-etiqueta text-tinta-suave">Mirando el precio por kilo…</p>
  }
  if (producto.isError) {
    return (
      <p className="mt-1 text-etiqueta text-tinta-suave">
        No he podido mirar el precio por kilo.
      </p>
    )
  }
  const p = producto.data?.producto
  if (!p) return null
  if (p.comparable === false) {
    return (
      <p className="mt-1 text-etiqueta text-tinta-suave">
        Este formato no se puede comparar por kilo.
      </p>
    )
  }
  if (p.precio_unidad_cent === null) {
    return (
      <p className="mt-1 text-etiqueta text-tinta-suave">
        No tengo el precio por kilo de este formato.
      </p>
    )
  }
  return (
    <p className="mt-1 text-etiqueta text-tinta-fuerte">
      {eurosUnidad(p.precio_unidad_cent, p.unidad)} en {nombreCadena(p.fuente)}
    </p>
  )
}

function EnlaceALaFicha({ productoId }: { productoId: string }) {
  const corte = productoId.indexOf(':')
  if (corte <= 0) return null
  const fuente = productoId.slice(0, corte)
  const idFuente = productoId.slice(corte + 1)
  return (
    <Link
      to={`/compra/productos/${fuente}/${idFuente}`}
      className="inline-flex min-h-[44px] items-center text-cuerpo underline"
    >
      Ver la ficha
    </Link>
  )
}

function EnlaceALaLista({ listaId, texto }: { listaId: string; texto: string }) {
  return (
    <Link to={`/compra/listas/${listaId}`} className="inline-flex min-h-[44px] items-center text-cuerpo underline">
      {texto}
    </Link>
  )
}

/* ----------------------------------------------------------- las cuentas --- */

/** Una celda: lo que esta linea cuesta en una cadena. */
interface CeldaDeLaLinea {
  cadena: string
  coste_cent: number
  promo: string | null
  sugerencia: string | null
  /** Lo que la oferta baja de verdad en este producto (`coste_sin_oferta_cent - coste_cent`). */
  ahorro_cent: number
  /** `false` cuando el precio es de un equivalente que la persona aun no ha confirmado. */
  autorizada: boolean
  producto_id: string
}

/** *** DE CADA CADENA A CADA LINEA. *** *
 *
 *  *Es la tabla que la pantalla necesita y la API no manda girada: el reparto va por cadenas y
 *  aqui se lee por lineas.* *Se une lo resuelto (`productos`) con lo que espera confirmacion
 *  (`pendientes`), y lo que no esta en ninguna de las dos es que **esa cadena no lo tiene**.*
 */
function matrizPorLinea(cadenas: CadenaComparada[]): Map<string, CeldaDeLaLinea[]> {
  const porLinea = new Map<string, CeldaDeLaLinea[]>()
  const anade = (lineaId: string | null | undefined, celda: CeldaDeLaLinea) => {
    if (!lineaId) return
    const suyas = porLinea.get(lineaId) ?? []
    // *Una cadena, una vez:* si el mismo id llegara resuelto y pendiente, manda lo resuelto.
    if (suyas.some((c) => c.cadena === celda.cadena && c.autorizada)) return
    porLinea.set(lineaId, [...suyas.filter((c) => c.cadena !== celda.cadena), celda])
  }

  for (const cadena of cadenas) {
    for (const p of cadena.productos ?? []) {
      anade(p.linea_id, {
        cadena: cadena.cadena,
        coste_cent: p.coste_cent,
        promo: p.promo,
        sugerencia: p.sugerencia ?? null,
        ahorro_cent: Math.max(0, p.coste_sin_oferta_cent - p.coste_cent),
        autorizada: p.autorizada !== false,
        producto_id: p.producto_id,
      })
    }
    for (const p of cadena.pendientes ?? []) {
      anade(p.linea_id, {
        cadena: cadena.cadena,
        coste_cent: p.coste_cent,
        promo: null,
        sugerencia: null,
        ahorro_cent: 0,
        autorizada: false,
        producto_id: '',
      })
    }
  }
  return porLinea
}

/** Cuantos productos de la lista se pueden comparar, y cuantos no, con el motivo. */
function contarLineas(filas: Linea[], matriz: Map<string, CeldaDeLaLinea[]>) {
  let comparables = 0
  let soloUnaCadena = 0
  let sinPrecio = 0
  let conEquivalenteSinConfirmar = 0
  for (const linea of filas) {
    const celdas = matriz.get(linea.id) ?? []
    if (celdas.length === 0) sinPrecio += 1
    else if (celdas.length === 1) soloUnaCadena += 1
    else comparables += 1
    if (celdas.some((c) => !c.autorizada)) conEquivalenteSinConfirmar += 1
  }
  return {
    comparables,
    soloUnaCadena,
    sinPrecio,
    conEquivalenteSinConfirmar,
    noComparables: soloUnaCadena + sinPrecio,
  }
}

/** *** CUANTOS PRODUCTOS ENTRAN EN UN TOTAL, SIN SUPONER NADA. *** *
 *
 *  *`contadas` es lo que la API cuenta de verdad (solo lo autorizado suma).* *Si una version
 *  anterior de la API no lo mandara, se deduce de `encontrados` menos lo pendiente -- que es la
 *  misma cuenta que hace `_total_autorizado` --, y nunca se supone que entran todos.*
 */
function contadasDe(cadena: CadenaComparada): number {
  if (typeof cadena.contadas === 'number') return cadena.contadas
  return Math.max(0, cadena.encontrados - (cadena.sin_autorizar ?? 0))
}

/** Primero las que lo tienen entero (y entre ellas la mas barata); detras, las incompletas. */
function ordenarCadenas(cadenas: CadenaComparada[], total: number): CadenaComparada[] {
  return [...cadenas].sort((a, b) => {
    const completasA = contadasDe(a) === total ? 0 : 1
    const completasB = contadasDe(b) === total ? 0 : 1
    if (completasA !== completasB) return completasA - completasB
    if (completasA === 0) return a.total_cent - b.total_cent
    return contadasDe(b) - contadasDe(a) || a.total_cent - b.total_cent
  })
}

/** "1 producto" / "12 productos", sin el «1 productos» que se lee en media aplicación. */
function plural(n: number, uno: string, varios: string): string {
  return `${n} ${n === 1 ? uno : varios}`
}
