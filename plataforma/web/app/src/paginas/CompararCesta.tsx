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
 *  ficha) se dice, en vez de enseñar un numero que no significa nada.* *El **precio por unidad de
 *  cada cadena**, en cambio, llega ya en el reparto (`precio_unidad_cent` y `unidad`): cuando
 *  viene se enseña junto al coste de la fila, y cuando no viene se calla y la fila se queda como
 *  estaba -- un €/unidad que no ha llegado no se calcula aqui.*
 *
 *  *** Y LA RESPUESTA, EN UNA CIFRA. *** *Arriba de los totales va el ahorro, en el unico caso
 *  en que se puede afirmar:*
 *
 *   - **si dos cadenas tienen la lista entera**, el de comprarla toda en la mas barata en vez de
 *     en la mas cara -- el importe, el porcentaje sobre el total caro y los dos nombres;
 *   - **si no** (que es lo normal: la autorizacion de equivalentes es **una por linea**, asi que
 *     una linea solo puede confirmarse para una cadena y rara vez hay dos completas), el de
 *     comprar **cada cosa donde esta mas barata**: la suma, linea a linea, de lo que separa al
 *     precio mas caro del mas barato, con el porcentaje sobre la suma de los maximos.* *Ahi
 *     cuentan **todos los precios de hoy**, tambien los de los equivalentes que aun no se han
 *     confirmado -- que no suman en los totales, y la nota de la tarjeta lo dice.*
 *
 *  *Sin dos completas ni una linea con dos precios, la tarjeta **no se pinta**: se sigue
 *  contestando con la frase de «Total en cada cadena», que es lo unico que se puede afirmar.* *Y
 *  cada total lleva una barra fina de longitud relativa al total mas caro, para ver de un vistazo
 *  cuanto se separan sin tener que restar.*
 *
 *  **Los cuatro estados, y la puerta antes que el error**: cargando (esqueleto), con datos, sin
 *  sesion (`EntraParaVer`, que es un estado y no un fallo), lista sin lineas, y error con
 *  reintento. *Un 401 que llegue tarde tambien es puerta: si la sesion se ha caido, no se enseña
 *  «No he podido traer esto».*
 */
import { useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { misListas, reparto as pedirReparto, verLista, yo } from '../api/cesta'
import { esErrorApi } from '../api/cliente'
import { useProducto } from '../api/consultas'
import { euros, eurosUnidad, nombreCadena, porcentaje } from '../api/formato'
import { envasesPara } from '../logica/envases'
import { mejorCompra, type MejorCompra } from '../logica/optimizar'
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
  /** *** El precio por unidad de medida del formato, si la API lo manda. *** *
   *
   *  *`precio_unidad_cent` y `unidad` son el contrato nuevo del reparto (`129` y `l` para
   *  «1,29 €/l»).* *Se declaran **opcionales** porque esta pantalla no puede dar por hecho
   *  que la API que le contesta los traiga: si faltan, la fila se enseña como antes -- solo
   *  el coste --, que es lo honesto; un €/unidad inventado seria peor que su ausencia.*
   */
  precio_unidad_cent?: number | null
  unidad?: string | null
}

/** Lo que la linea costaria en una cadena si se aceptara el equivalente que propone el motor. */
interface PorConfirmar {
  linea_id?: string | null
  nombre: string
  coste_cent: number
  identidad?: string | null
  motivo?: string | null
  /** El formato medido del equivalente, si el catálogo lo trae. */
  precio_unidad_cent?: number | null
  unidad?: string | null
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
  /** *** ORDEN POR AHORRO. *** *
   *
   *  *La pantalla se lee de arriba abajo y lo primero que interesa es donde hay diferencia: se
   *  ordenan los productos por lo que separa su precio mas barato del mas caro (con los precios de
   *  hoy, ronde o no el equivalente). Empate: se deja el orden de la lista. Antes se pintaban en el
   *  orden en que se anadieron, asi que el producto con 3,00 EUR de diferencia podia quedar el
   *  ultimo, detras de diez que costaban lo mismo en todas las cadenas.*
   */
  const filasOrdenadas = [...filas]
    .map((linea) => ({ linea, diferencia: diferenciaDeLinea(matriz.get(linea.id) ?? []) }))
    .sort((a, b) => (b.diferencia ?? -1) - (a.diferencia ?? -1))
    .map(({ linea }) => linea)
  const todasSinConfirmar = cadenas.length > 0 && cadenas.every((c) => contadasDe(c) === 0)
  /** La mejor compra en 1 o 2 tiendas, con los precios que hay para cada línea. */
  const mejor = mejorCompra(filas.map((l) => l.id), new Map(filas.map((l) => [
    l.id,
    (matriz.get(l.id) ?? []).map((c) => ({ cadena: c.cadena, coste_cent: c.coste_cent })),
  ])))
  // *** El grafico del ahorro, con las mismas lineas y el mismo orden. *** *
  // *No es una segunda verdad: se calcula con `diferenciaDeLinea`, igual que el orden y la
  // pastilla bajo el nombre. Solo se pinta si hay al menos una linea con dos precios distintos;
  // la escala es la mayor diferencia, para que la barra mas larga sea la que mas ahorra.*
  const diferencias = filasOrdenadas
    .map((linea) => ({ linea, diferencia: diferenciaDeLinea(matriz.get(linea.id) ?? []) }))
    .filter((x): x is { linea: Linea; diferencia: number } => x.diferencia !== null)
  const mayorDiferencia = diferencias.reduce((maximo, x) => Math.max(maximo, x.diferencia), 0)
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

  // *** ESTADO VACIO PROPIO: NI DETALLE NI UN SOLO TOTAL. *** *
  // *Cuando la API no manda el detalle por producto y **todos** los totales son cero, no es que
  // se pueda comparar: es que no hay precio de nada. Se dice distinto de «hoy no puedo comparar»
  // (no hay cadenas que la resuelvan) y del estado normal (hay precios pero faltan equivalentes),
  // con la misma salida: volver a la lista. Si algún total no es cero, se enseñan los totales,
  // que es lo que sí llegó.*
  const sinNingunPrecio = cadenas.length > 0 && cadenas.every((c) => c.total_cent === 0)
  if (filas.length > 0 && !hayDetalle && sinNingunPrecio) {
    return (
      <div className="flex min-h-full flex-col gap-bloque">
        <Vacio titulo="Todavía no hay precios de esta lista" comoPagina className="grow">
          <p>
            Ninguna cadena tiene hoy precio de los productos de esta lista. Puede que falte la
            captura del día o que hayan cambiado de formato.
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
  /** *** El total contra el que se mide la barra de cada cadena. *** *
   *
   *  *Es el **total mas caro** de los que se enseñan: la barra mas larga es la de ese, y las
   *  demas dicen su proporcion.* *Se mide sobre lo que se pinta -- las cadenas de esta lista --, no
   *  sobre un maximo inventado, y por eso la comparacion es entre las de aqui.*
   */
  const totalMasCaro = ordenadas.reduce((maximo, c) => Math.max(maximo, c.total_cent), 0)
  /** *** El segundo caso de la tarjeta: sin dos completas, cada cosa donde esta mas barata. *** *
   *
   *  *Se calcula aqui y no en el componente porque necesita `matriz` y `filas`, que es la tabla
   *  que esta pantalla ya tiene montada.* *Devuelve `null` si no hay ninguna linea con dos
   *  precios (o si no hay diferencia), y entonces la tarjeta no se pinta.*
   */
  const ahorroPosible = ahorroDeCadaCosa(filas, matriz)
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

      {/* -------------------------------------------------- lo que te ahorras --- */}
      {/* *** La cifra grande, y solo cuando es una cuenta que significa algo. *** *
          *Primero el caso fuerte: **dos cadenas con la lista entera** (`masCara` solo existe
          entonces) y una diferencia positiva; con una sola completa no hay contra que restar, y
          un empate no es un ahorro.* *Si ese caso no se da, se usa el de **cada cosa donde esta
          mas barata**, que es el que se puede afirmar en datos reales (la autorizacion es una por
          linea); si tampoco hay lineas con dos precios, no se pinta nada.* */}
      {ganadora && masCara && diferencia !== null && diferencia > 0 ? (
        <AhorroDeLaCesta
          ahorro_cent={diferencia}
          base_cent={masCara.total_cent}
          nota={NOTA_PRECIOS_DE_HOY}
        >
          Comprando en {nombreCadena(ganadora.cadena)} en vez de en {nombreCadena(masCara.cadena)}.
        </AhorroDeLaCesta>
      ) : ahorroPosible ? (
        <AhorroDeLaCesta
          ahorro_cent={ahorroPosible.ahorro_cent}
          base_cent={ahorroPosible.base_cent}
          nota={NOTA_PRECIOS_DE_HOY_CON_EQUIVALENTES}
        >
          Comprando cada cosa donde está más barata, frente a comprarla toda en la cadena más
          cara.
        </AhorroDeLaCesta>
      ) : null}

      <LaMejorCompra mejor={mejor} total={filas.length} />

      {/* *La letra pequeña con las fórmulas, para quien quiera comprobar la cifra.* */}
      <ComoSeCalcula hayDosCompletas={masCara !== null} />

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
              totalMasCaro={totalMasCaro}
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
            {todasSinConfirmar ? (
              <>
                Todavía no hay ningún producto con el precio confirmado: los totales de abajo salen
                a cero y no se pueden comparar entre sí.{' '}
                <Link to={`/compra/listas/${listaId}`} className="underline">
                  Confirmarlos en la lista
                </Link>
              </>
            ) : (
              <>
                {resumen.conEquivalenteSinConfirmar === 1
                  ? '1 producto solo tiene precio como equivalente de otro. Mientras no lo confirmes, no suma en ningún total.'
                  : `${resumen.conEquivalenteSinConfirmar} productos solo tienen precio como equivalente de otro. Mientras no los confirmes, no suman en ningún total.`}{' '}
                <Link to={`/compra/listas/${listaId}`} className="underline">
                  Confirmarlos en la lista
                </Link>
              </>
            )}
          </Aviso>
        )}

        {ordenadas.some((c) => contadasDe(c) < total) && (
          <p className="text-cuerpo text-tinta-suave">
            Una cadena a la que le faltan productos tiene un total más bajo: por eso se dice
            cuántos entran, y solo se compara con las que los tienen todos.
          </p>
        )}
      </section>

      {/* ------------------------------------------------ el grafico del ahorro --- */}
      {/* *Barras de lo que se ahorra en cada producto, en el mismo orden que el desglose. La
          escala es la mayor diferencia: la barra mas larga es donde mas hay que decidir.* */}
      {diferencias.length > 0 && (
        <section aria-labelledby="grafico-del-ahorro" className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <h3 id="grafico-del-ahorro" className="text-entrada font-semibold text-tinta-fuerte">
              El ahorro, producto a producto
            </h3>
            <p className="text-etiqueta text-tinta-suave">
              Lo que separa el precio más alto del más bajo de cada producto, con los precios de
              hoy. Ordenado por diferencia.
            </p>
          </div>
          <ul className="grid gap-3">
            {diferencias.map(({ linea, diferencia }, indice) => (
              <li key={linea.id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1">
                <span className="min-w-0 truncate text-etiqueta text-tinta">
                  <span className="cifra mr-1 text-tinta-suave">{indice + 1}.</span>
                  {linea.nombre_visto}
                </span>
                <span className="cifra text-etiqueta font-medium text-tinta-fuerte">
                  {euros(diferencia)}
                </span>
                <span
                  aria-hidden="true"
                  className="col-span-2 h-2 overflow-hidden rounded-pastilla bg-marfil"
                >
                  <span
                    className="block h-full rounded-pastilla bg-lima"
                    style={{ width: `${Math.max(2, Math.round((diferencia / mayorDiferencia) * 100))}%` }}
                  />
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ------------------------------------------------ producto a producto --- */}
      {hayDetalle && (
        <section aria-labelledby="producto-a-producto" className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <h3 id="producto-a-producto" className="text-entrada font-semibold text-tinta-fuerte">
              Producto a producto
            </h3>
            <p className="text-etiqueta text-tinta-suave">
              Ordenados por lo que se ahorra. Abre un producto para ver lo que cuesta en cada
              cadena, su precio por unidad y su precio por kilo.
            </p>
          </div>

          <ul className="grid gap-2">
            {filasOrdenadas.map((linea) => (
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
        Ninguna cadena tiene los {plural(total, 'producto', 'productos')} confirmados. Los
        totales de abajo son de lo que está confirmado en cada una, y por eso no se pueden
        comparar entre sí.
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

/** *** La letra pequeña de la cifra, en sus dos versiones. *** *
 *
 *  *No dicen lo mismo, y por eso son dos:*
 *
 *   - *en el caso de **dos completas**, la resta sale de los totales, que **solo cuentan lo
 *     autorizado**: los equivalentes sin confirmar no entran, y la nota no puede decir que si;*
 *   - *en el caso de **cada cosa**, el calculo usa **todos** los precios de hoy, tambien los de
 *     esos equivalentes -- que siguen sin sumar en los totales de abajo --, y la nota lo dice.*
 *
 *  *En las dos, la condicion de las ofertas: una oferta de tarjeta, cupón o internet no baja lo que
 *  se paga y no esta restada.*
 */
const NOTA_PRECIOS_DE_HOY =
  'Con los precios de hoy. Las ofertas que piden tarjeta, cupón o comprar por internet no están restadas.'

const NOTA_PRECIOS_DE_HOY_CON_EQUIVALENTES =
  'Con los precios de hoy, incluidos los equivalentes que aún no has confirmado (esos no suman en los totales de abajo). Las ofertas que piden tarjeta, cupón o comprar por internet no están restadas.'

/** *** LA CIFRA GRANDE: LO QUE TE AHORRAS, SEGUN LO QUE SE PUEDA AFIRMAR. *** *
 *
 *  *Es la respuesta de la pantalla en un solo golpe de vista, y por eso va **arriba de los
 *  totales** y con el color de la marca.* *Se usa en los dos casos de la tarjeta, que solo cambian
 *  en dos cosas: el importe y **sobre que** se mide el porcentaje.*
 *
 *   - *dos cadenas completas: la resta de la cara a la barata, y el porcentaje sobre el total de
 *     la **cara**, que es la que se dejaria de pagar;*
 *   - *si no las hay: la suma de lo que se ahorra comprando cada cosa donde esta mas barata, y el
 *     porcentaje sobre **la suma de los maximos**, que es lo que costaria comprarlo todo en la
 *     cadena mas cara de cada linea.*
 *
 *  *Debajo del importe, la frase dice **que** se esta comparando: un ahorro sin sujeto no se puede
 *  comprobar.* *Y en pequeño, con que precios se ha hecho la cuenta: los de hoy, y con las ofertas
 *  condicionadas sin restar.*
 *
 *  *El porcentaje se redondea al entero porque es una cifra de portada, no una medida: los
 *  centimos ya estan en el importe.*
 *
 *  *Accesible sin depender del color: el importe, el porcentaje y la frase son **texto**; el color
 *  de la tarjeta solo refuerza.*
 */
function AhorroDeLaCesta({ ahorro_cent, base_cent, nota, children }: {
  ahorro_cent: number
  /** El total contra el que se mide el porcentaje: la cadena cara o la suma de los maximos. */
  base_cent: number
  /** La letra pequeña de **este** calculo (`NOTA_PRECIOS_DE_HOY...`), porque no dicen lo mismo. */
  nota: string
  /** La frase que dice **que** se compara; el importe y el porcentaje van encima. */
  children: ReactNode
}) {
  // *`base_cent > 0` esta garantizado por quien llama, pero se comprueba igual: una division por
  // cero no se deja al azar de los datos.*
  const porcentajeDelAhorro = base_cent > 0 ? (ahorro_cent / base_cent) * 100 : null
  // *** Un ahorro positivo puede redondear al 0 %. *** *
  // *Un centimo sobre una cesta grande es un ahorro real, pero un «−0 %» en grande diria que no
  // hay ahorro -- que es falso --, y el importe ya esta justo al lado.* *Asi que por debajo del
  // 0,5 % **se calla el porcentaje**: callar una cifra que no informa es distinto de inventarla.*
  const porcentajeEntero =
    porcentajeDelAhorro === null ? null : Math.round(porcentajeDelAhorro)
  return (
    <section
      aria-labelledby="ahorro-de-la-cesta"
      className="rounded-tarjeta bg-bosque p-4 text-sobre-bosque shadow-alzado"
    >
      <h3 id="ahorro-de-la-cesta" className="text-micro uppercase">
        Lo que te ahorras
      </h3>
      <div className="mt-2 flex flex-wrap items-baseline gap-3">
        <p className="cifra text-precio-grande font-semibold">{euros(ahorro_cent)}</p>
        {porcentajeEntero !== null && porcentajeEntero >= 1 && (
          <span className="cifra inline-flex min-h-6 items-center rounded-pastilla bg-lima px-2 text-etiqueta-fuerte text-sobre-lima">
            −{porcentaje(porcentajeEntero, 0)}
          </span>
        )}
      </div>
      <p className="mt-1 text-etiqueta">{children}</p>
      {/* *El aviso pequeño, para que la cifra no se lea como una promesa: con que precios se ha
          calculado y que ofertas no estan restadas. El texto lo elige quien llama, porque el caso
          de las completas no usa precios sin confirmar y el de cada cosa si.* */}
      <p className="mt-1 text-etiqueta opacity-80">{nota}</p>
    </section>
  )
}

/** *** LA RESPUESTA PRACTICA: UNA TIENDA O DOS, Y CUANTO SE AHORRA. *** *
 *
 *  *El algoritmo está en `logica/optimizar.ts`: prueba todas las tiendas y todas las parejas, exige
 *  que cubran todos los productos y se queda la más barata.* *Aquí solo se cuenta en una frase.*
 *
 *  *Si repartir no ahorra, **no se anuncia un ahorro**: se dice que no compensa partir la compra.*
 */
function LaMejorCompra({ mejor, total }: { mejor: MejorCompra; total: number }) {
  if (!mejor.una && !mejor.dos) return null
  const dos = mejor.dos
  const una = mejor.una
  const ahorro = mejor.ahorro_cent
  let frase: string
  if (dos && (!una || ahorro !== null)) {
    frase = una
      ? `Comprando todo en ${nombreCadena(una.cadena)}: ${euros(una.total_cent)}. `
        + `Repartiendo entre ${nombreCadena(dos.a)} y ${nombreCadena(dos.b)}: ${euros(dos.total_cent)}. `
        + `Te ahorras ${euros(ahorro as number)}.`
      : `Ninguna tienda tiene todo; repartiendo entre ${nombreCadena(dos.a)} y ${nombreCadena(dos.b)}: `
        + `${euros(dos.total_cent)}.`
  } else if (una) {
    frase = `No compensa partir la compra: todo en ${nombreCadena(una.cadena)} sale a `
      + `${euros(una.total_cent)}.`
  } else {
    return null
  }
  const partes = dos ? dos.partes.filter((p) => p.lineas > 0) : []
  return (
    <Tarjeta titulo="La cesta más barata en 1 o 2 tiendas">
      <p className="text-cuerpo text-tinta">{frase}</p>
      {partes.length > 0 && (
        <ul className="mt-2 grid gap-1">
          {partes.map((p) => (
            <li key={p.cadena} className="flex flex-wrap justify-between gap-2 text-etiqueta">
              <span className="text-tinta-suave">{nombreCadena(p.cadena)}</span>
              <span className="text-tinta">
                {p.lineas} de {total} productos · {euros(p.total_cent)}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-etiqueta text-tinta-suave">
        Con los precios de hoy, incluidas alternativas sin confirmar. Las ofertas que piden
        tarjeta, cupón o comprar por internet no están restadas.
      </p>
    </Tarjeta>
  )
}

/** *** LA EXPLICACION, A UN TOQUE Y SIN TECNICISMOS. *** *
 *
 *  *La cifra grande no se sostiene sola: quien la lee tiene derecho a saber que suma, que no, y
 *  por que el porcentaje se mide sobre una base y no sobre otra.* *Va en un desplegable para no
 *  tapar la comparacion con cuatro parrafos, y usa los dos casos reales de la tarjeta: con dos
 *  cadenas completas el ahorro es una resta; sin ellas, la suma de lo que separa cada producto.*
 */
function ComoSeCalcula({ hayDosCompletas }: { hayDosCompletas: boolean }) {
  return (
    <details className="rounded-campo border border-borde bg-papel">
      <Resumen className="px-3 text-cuerpo">¿Cómo se calcula?</Resumen>
      <div className="flex flex-col gap-2 px-3 pb-3 text-etiqueta text-tinta-suave">
        <p>
          <strong className="text-tinta">Los totales por cadena</strong> suman solo los productos
          que esa cadena tiene hoy, con su oferta aplicada. Si le falta alguno, se dice cuántos
          entran: una cadena incompleta no se compara con las que tienen la lista entera.
        </p>
        <p>
          <strong className="text-tinta">El ahorro.</strong>{' '}
          {hayDosCompletas
            ? 'Con dos cadenas completas, es la diferencia entre sus totales; el porcentaje va sobre el total de la más cara.'
            : 'Es la suma, producto a producto, de lo que separa el precio más caro del más barato de hoy; el porcentaje va sobre la suma de esos precios máximos.'}
        </p>
        <p>
          <strong className="text-tinta">El €/kg y el €/l</strong> son los del formato de cada
          producto: comparan el mismo producto entre cadenas, no dos formatos distintos. Si el
          formato no está medido, no se enseña una unidad inventada.
        </p>
        <p>
          <strong className="text-tinta">Lo que no se resta:</strong> las ofertas que piden tarjeta,
          cupón o comprar por internet. Los equivalentes sin confirmar cuentan en el ahorro posible,
          pero no en los totales de cada cadena.
        </p>
      </div>
    </details>
  )
}

/** Una cadena con su total y, si le falta algo, dicho. */
function CadenaEnLaLista({ cadena, total, contadas, totalMasCaro, esLaMasBarata, diferenciaConLaMasBarata }: {
  cadena: CadenaComparada
  total: number
  contadas: number
  /** El total mas caro que se enseña: contra el se mide la barra de esta cadena. */
  totalMasCaro: number
  esLaMasBarata: boolean
  /** Lo que esta cadena cuesta de mas que la mas barata, o `null` si no se puede restar. */
  diferenciaConLaMasBarata: number | null
}) {
  const faltan = cadena.faltan.length
  // *** La barra: solo CSS, y solo si hay un total contra el que medir. *** *
  // *Una cadena sin precio no lleva barra vacia, porque una barra a cero se lee «la mas barata»
  // y es justo lo contrario: no tiene precio. La longitud es la parte que le toca del total mas
  // caro -- la mas cara llega al 100 % -- y el color no dice nada por si solo: el total esta
  // escrito al lado.*
  const proporcion =
    contadas > 0 && totalMasCaro > 0
      ? Math.min(100, Math.round((cadena.total_cent / totalMasCaro) * 100))
      : null
  return (
    <li
      className={cx(
        'rounded-campo border p-3',
        esLaMasBarata ? 'border-bien bg-bien-suave' : 'border-borde bg-papel',
      )}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h4 className="text-entrada font-semibold text-tinta-fuerte">{nombreCadena(cadena.cadena)}</h4>
        {/* *** Un cero no es un precio. *** *Una cadena que no tiene ningun producto de la
            lista sumaba 0,00 € y se leia como «gratis»; se dice que no hay precio.* */}
        {contadas === 0 ? (
          <p className="text-etiqueta text-tinta-suave">sin precio</p>
        ) : (
          <p className="cifra text-precio font-semibold text-tinta-fuerte">{euros(cadena.total_cent)}</p>
        )}
      </div>

      {proporcion !== null && (
        <div
          aria-hidden="true"
          className="mt-2 h-1.5 w-full overflow-hidden rounded-pastilla bg-marfil"
        >
          <div
            className={cx('h-full rounded-pastilla', esLaMasBarata ? 'bg-bien' : 'bg-bosque')}
            style={{ width: `${proporcion}%` }}
          />
        </div>
      )}

      <div className="mt-1 flex flex-wrap items-center gap-2">
        {contadas < total ? (
          <span className="text-etiqueta text-tinta-suave">
            Subtotal · faltan {total - contadas}
          </span>
        ) : (
          <span className="text-etiqueta text-tinta-suave">Cesta completa</span>
        )}
        {esLaMasBarata && <Etiqueta tono="bien">la más barata</Etiqueta>}
        {diferenciaConLaMasBarata !== null && diferenciaConLaMasBarata > 0 && (
          <span className="text-etiqueta text-tinta-suave">
            {euros(diferenciaConLaMasBarata)} más que la más barata
          </span>
        )}
      </div>

      {faltan > 0 && (
        <p className="mt-1 text-etiqueta text-tinta-suave">
          No lo tiene: {cadena.faltan.slice(0, 3).join(' · ')}
          {faltan > 3 && ` y ${faltan - 3} más`}
        </p>
      )}
    </li>
  )
}

/** El formato del pack, cuando se puede decir: «6 × 125 g» o «500 g».
 *
 *  *Primero se busca en el nombre porque es el dato publicado; si no está, se deduce del coste
 *  del envase y su €/kg o €/l. Si no hay ninguna de las dos cosas, `null`: no se inventa.*
 */
function formatoDelPack(nombre: string, celda: CeldaDeLaLinea, cantidad: number): string | null {
  const pack = nombre.match(/(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(g|kg|ml|l|cl|ud)\b/i)
  if (pack) return `${pack[1]} × ${pack[2].replace('.', ',')} ${pack[3]}`
  if (celda.precio_unidad_cent == null || celda.precio_unidad_cent <= 0 || !celda.unidad) {
    return null
  }
  const neto = (celda.coste_cent / Math.max(1, cantidad)) / celda.precio_unidad_cent
  if (!Number.isFinite(neto) || neto <= 0) return null
  if (celda.unidad === 'kg') {
    return neto < 1 ? `${Math.round(neto * 1000)} g` : `${Number(neto.toFixed(2))} kg`
  }
  if (celda.unidad === 'l') {
    return neto < 1 ? `${Math.round(neto * 1000)} ml` : `${Number(neto.toFixed(2))} l`
  }
  return `${Number(neto.toFixed(2))} ${celda.unidad}`
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
  // *** El precio por unidad, en el resumen, sin tener que abrir la linea. *** *
  // *La comparacion es entre formatos: «desde 3,15 €» y «desde 0,79 €/l» no son lo mismo.
  // Se enseña el €/unidad de la celda mas barata que lo trae; si la API no lo manda (o el
  // formato no es medible), no se inventa y el resumen se queda como estaba.*
  const conUnidad = autorizadas
    .filter((c) => c.precio_unidad_cent !== null && c.unidad)
    .sort((a, b) => a.coste_cent - b.coste_cent)
  const unidadDelResumen = conUnidad.length > 0
    ? eurosUnidad(conUnidad[0].precio_unidad_cent as number, conUnidad[0].unidad as string)
    : null
  const estado =
    desde === null
      ? celdas.length === 0
        ? 'no comparable'
        : 'por confirmar'
      : soloEn
        ? `${euros(desde)} · solo en ${nombreCadena(soloEn)}`
        : `desde ${euros(desde)}`
  // *** La marca del minimo, la misma pastilla que en la lista. *** *
  // *`minimo` viene solo si la API lo manda y sus datos son frescos (`tipos.ts`); si la clave no
  // esta, la linea se pinta como siempre.* *Y si vinieran las dos banderas se enseña la fuerte
  // (`nuevo_minimo`): un minimo nuevo tambien esta «en su minimo», y dos pastillas serian la misma
  // noticia repetida.*
  const minimo = linea.minimo ?? null
  const minimoNuevo = minimo?.nuevo_minimo === true
  const enSuMinimo = minimo?.vuelve_al_minimo === true

  return (
    <li className="rounded-campo border border-borde bg-papel">
      <details
        // *La linea se abre **y solo entonces** se pide el precio por kilo: una peticion por
        // producto abierto, no doce al entrar.*
        onToggle={(e) => setAbierta(e.currentTarget.open)}
      >
        <Resumen className="px-3">
          <span className="min-w-0 flex-1">
            <span className="block break-words text-cuerpo font-medium text-tinta-fuerte">
              {linea.nombre_visto}
              {linea.cantidad > 1 && (
                <span className="ml-2 text-etiqueta font-normal text-tinta-suave">
                  {linea.cantidad} unidades
                </span>
              )}
            </span>
            {unidadDelResumen && (
              <span className="mt-0.5 block text-etiqueta text-tinta-suave">
                {unidadDelResumen}
              </span>
            )}
            {diferenciaDeLinea(celdas) !== null && (
              <span className="mt-0.5 block text-etiqueta text-tinta-suave">
                hasta {euros(diferenciaDeLinea(celdas) as number)} de diferencia
              </span>
            )}
            {minimo && (minimoNuevo || enSuMinimo) && (
              <span className="mt-0.5 flex flex-wrap items-center gap-2">
                {minimoNuevo ? (
                  <Etiqueta tono="bien">Mínimo nuevo · {euros(minimo.minimo_cent)}</Etiqueta>
                ) : (
                  <Etiqueta tono="dato">En su mínimo · {euros(minimo.minimo_cent)}</Etiqueta>
                )}
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
                    <Etiqueta tono="dato">Sin equivalente</Etiqueta>
                  </li>
                )
              }
              return (
                <li
                  key={cadena.cadena}
                  className="border-t border-borde pt-1 first:border-0 first:pt-0"
                >
                  {/* *** Primero lo que se paga, despues el formato y el €/kg. *** *
                      *El coste de compra es el numero que se mira en la estanteria; el €/kg y
                      * el formato del pack van debajo, en la misma fila, para comparar sin
                      * confundir el precio del envase con el precio normalizado.* */}
                  <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                    <span className="text-etiqueta text-tinta-suave">{nombreCadena(cadena.cadena)}</span>
                    <span className="cifra text-precio-fila font-medium text-tinta-fuerte">
                      {euros(celda.coste_cent)}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
                    <span className="text-etiqueta text-tinta-suave">
                      {formatoDelPack(linea.nombre_visto, celda, linea.cantidad) ?? 'formato sin medir'}
                      {celda.precio_unidad_cent != null && celda.unidad ? (
                        <> · {eurosUnidad(celda.precio_unidad_cent, celda.unidad)}</>
                      ) : (
                        <> · sin medida</>
                      )}
                    </span>
                    <span className="flex flex-wrap items-center justify-end gap-1">
                      <Etiqueta tono={celda.identidad === 'exacto' ? 'dato' : 'aviso'}>
                        {celda.identidad === 'exacto' ? 'Mismo producto' : 'Alternativa'}
                      </Etiqueta>
                      {celda.motivo && (
                        <span className="max-w-[16rem] text-etiqueta text-tinta-suave" title={celda.motivo}>
                          {celda.motivo}
                        </span>
                      )}
                      {!celda.autorizada && (
                        <span className="text-etiqueta font-normal text-aviso">por confirmar</span>
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

          {celdas.length > 0 && (
            <CalculadoraDeEnvases celdas={celdas} cantidad={linea.cantidad} />
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
/** *** CALCULADORA DE ENVASES. *** *
 *
 *  *La comparación da €/kg y €/l, pero no dice cuántos envases hay que comprar para una cantidad:
 *  un pack de 6 × 125 g no se vende por kilos.* *Aquí se escribe lo que se necesita (1 kg) y se
 *  ve, cadena a cadena, cuántos envases enteros hacen falta, lo que se paga y lo que sobra.*
 *
 *  **El tamaño del envase no se inventa**: se obtiene de lo que la API ya manda -- el coste de una
 *  unidad y su €/kg o €/l -- dividiendo. Si falta el dato, o la cantidad no es de la misma
 *  magnitud (kg contra l), se dice que no se puede calcular. Y una cadena sin precio **no se pinta
 *  como 0 €**: se queda como «sin equivalente» en la fila de arriba.
 */
function CalculadoraDeEnvases({ celdas, cantidad }: {
  celdas: CeldaDeLaLinea[]
  cantidad: number
}) {
  const [demanda, setDemanda] = useState('')
  const [unidad, setUnidad] = useState('kg')
  const numero = Number(demanda.replace(',', '.'))
  const hayDemanda = demanda.trim() !== '' && Number.isFinite(numero) && numero > 0

  return (
    <details className="mt-2 rounded-campo border border-borde bg-papel">
      <Resumen className="px-3 text-etiqueta">Calcular envases para una cantidad</Resumen>
      <div className="px-3 pb-3">
        <p className="mb-2 text-etiqueta text-tinta-suave">
          Se compran envases enteros: se redondea hacia arriba y se dice lo que sobra. El coste es
          el de esos envases, no el de la cantidad exacta.
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-0.5 text-etiqueta text-tinta-suave">
            Cantidad
            <input
              inputMode="decimal"
              value={demanda}
              onChange={(e) => setDemanda(e.target.value)}
              placeholder="1"
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-2 py-1 text-cuerpo text-tinta"
            />
          </label>
          <label className="flex flex-col gap-0.5 text-etiqueta text-tinta-suave">
            Unidad
            <select
              value={unidad}
              onChange={(e) => setUnidad(e.target.value)}
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 py-1 text-cuerpo text-tinta"
            >
              {['kg', 'g', 'l', 'ml', 'ud'].map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </label>
        </div>
        {hayDemanda ? (
          <ul className="mt-2 grid gap-1">
            {celdas.map((c) => {
              const conMedida = c.precio_unidad_cent != null && c.precio_unidad_cent > 0 && c.unidad
              if (!conMedida) {
                return (
                  <li key={c.cadena} className="flex flex-wrap justify-between gap-2 text-etiqueta">
                    <span className="text-tinta-suave">{nombreCadena(c.cadena)}</span>
                    <span className="text-tinta-suave">no se sabe el tamaño del envase</span>
                  </li>
                )
              }
              const porEnvase = c.coste_cent / Math.max(1, cantidad)
              // *Los dos números están en céntimos: el coste del envase y el €/kg o €/l. Al
              // dividirlos se va el factor 100, y queda el tamaño en la unidad del precio.*
              const tamano = porEnvase / (c.precio_unidad_cent as number)
              const calculo = envasesPara(numero, unidad, tamano, c.unidad as string, porEnvase)
              return (
                <li key={c.cadena} className="flex flex-wrap justify-between gap-2 text-etiqueta">
                  <span className="text-tinta-suave">{nombreCadena(c.cadena)}</span>
                  <span className="text-tinta">
                    {calculo
                      ? `${calculo.envases} ${calculo.envases === 1 ? 'envase' : 'envases'} · ${euros(calculo.coste_cent)}${calculo.sobra > 0 ? ` · sobran ${String(calculo.sobra).replace('.', ',')} ${calculo.unidad}` : ''}`
                      : 'no se puede comparar con esa unidad'}
                  </span>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="mt-2 text-etiqueta text-tinta-suave">
            Escribe una cantidad para ver los envases y lo que cuestan.
          </p>
        )}
      </div>
    </details>
  )
}

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
  /** El precio por unidad de medida del formato en esta cadena, o `null` si no llego. */
  precio_unidad_cent: number | null
  /** La unidad de ese precio (`kg`, `l`, `ud`), o `null` si no llego. */
  unidad: string | null
  /** El veredicto de identidad: `exacto`, `alternativa`, ... o `null` si no llego. */
  identidad: string | null
  /** Por qué se decidió esa identidad, para poder explicar cada fila. */
  motivo: string | null
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
        // *El contrato nuevo del reparto; si una API vieja no lo manda, `null` y la fila se
        // pinta sin €/unidad en vez de con uno inventado.*
        precio_unidad_cent: p.precio_unidad_cent ?? null,
        unidad: p.unidad ?? null,
        identidad: p.identidad ?? null,
        motivo: p.motivo ?? null,
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
        // *La alternativa tambien puede traer su formato medido: desde que la API lo manda en
        // `pendientes`, se enseña junto al coste en vez de decir «sin medida».*
        precio_unidad_cent: p.precio_unidad_cent ?? null,
        unidad: p.unidad ?? null,
        identidad: p.identidad ?? 'alternativa',
        motivo: p.motivo ?? null,
      })
    }
  }
  return porLinea
}

/** *** LO QUE SE AHORRA COMPRANDO CADA COSA DONDE ESTA MAS BARATA. *** *
 *
 *  *Cuando no hay dos cadenas completas -- que es lo normal: la autorizacion de equivalentes es
 *  **una por linea**, asi que una linea solo se confirma para una cadena y nunca hay dos celdas
 *  autorizadas en la misma linea -- la resta entre totales completos no se puede hacer.* *Lo que
 *  si se puede afirmar es, linea a linea, lo que separa al precio mas caro del mas barato de
 *  **esa** linea: es exactamente lo que se ahorra comprando cada cosa donde esta mas barata.*
 *
 *  *** Cuenta TODA celda con precio, tambien las de equivalencias sin confirmar. *** *Es una
 *  decision medida, no un descuido: si solo contaran las autorizadas, la tarjeta no saldria nunca
 *  en uso real (una linea no puede tener dos autorizadas).* *El precio por confirmar es lo que
 *  costaria hoy el equivalente, y para **este** calculo es un precio valido; lo que no hace es
 *  sumar en los totales de abajo, que siguen contando solo lo autorizado (`contarLineas`).* *Esa
 *  diferencia se dice en la nota de la tarjeta, para que nadie lea el ahorro como si ya estuviera
 *  en los totales.*
 *
 *  *Una linea con un solo precio **no aporta nada**: ni diferencia (no hay eleccion) ni divisor.*
 *  *El porcentaje se mide sobre **la suma de los maximos**, que es lo que costaria comprarlo todo
 *  en la cadena mas cara de cada linea.* *Sin ninguna linea con dos precios -- o sin diferencia --
 *  no hay tarjeta: un cero no es un ahorro.*
 */
function ahorroDeCadaCosa(
  lineas: Linea[],
  matriz: Map<string, CeldaDeLaLinea[]>,
): { ahorro_cent: number; base_cent: number } | null {
  let ahorro_cent = 0
  let base_cent = 0
  let conDosPrecios = 0
  for (const linea of lineas) {
    // *Todas las celdas, autorizadas o no: ver el docstring.*
    const costes = (matriz.get(linea.id) ?? []).map((c) => c.coste_cent)
    if (costes.length < 2) continue
    ahorro_cent += Math.max(...costes) - Math.min(...costes)
    base_cent += Math.max(...costes)
    conDosPrecios += 1
  }
  if (conDosPrecios === 0 || base_cent <= 0 || ahorro_cent <= 0) return null
  return { ahorro_cent, base_cent }
}

/** La diferencia entre el precio mas barato y el mas caro de una linea, o `null`.
 *
 *  *Es el criterio del orden por ahorro y lo que se dice bajo el nombre: si los diez productos
 *  cuestan lo mismo en todas las cadenas, no hay nada que ordenar. Se calcula con las celdas que
 *  llegaron, como la tarjeta de ahorro.*
 */
function diferenciaDeLinea(celdas: CeldaDeLaLinea[]): number | null {
  const costes = celdas.map((c) => c.coste_cent)
  if (costes.length < 2) return null
  const diferencia = Math.max(...costes) - Math.min(...costes)
  return diferencia > 0 ? diferencia : null
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
