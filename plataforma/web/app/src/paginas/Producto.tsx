/** **La ficha de un producto: qué es, cuánto cuesta, si está caro y dónde sale mejor.**
 *
 *  Un producto se identifica por **su id en la cadena** (`mercadona:5124`), no por el nuestro: eso
 *  es lo único que se puede sacar de la URL de un supermercado, y es lo que usa la extensión de
 *  navegador. Por eso la ruta es `/producto/{cadena}/{id_fuente}`.
 *
 *  ======================== LA JERARQUÍA, Y POR QUÉ ========================
 *
 *  *Se rehízo el 5/11/2026 contra el artboard aprobado (`designs/cesta-app/project/Producto.dc.html`),
 *  y lo que cambió es **el orden en que se contesta**, no los cálculos:* *la lógica que ya medía bien
 *  -- `construyeComparacion`, `loQueDiceLaCurva`, `Chispa`, `fraseDePrecio` -- se queda donde estaba.*
 *
 *  1. **Qué es y cuánto cuesta.** Nombre, marca, precio de hoy grande y el **€/kg al lado**, porque
 *     es la única cifra que permite comparar dos formatos. Si no hay €/kg se dice -- «no hay precio
 *     por kilo» -- y no se rellena.
 *  2. **¿Está caro?** Un chip con flecha y palabra, calculado contra la serie de verdad
 *     (`logica/juicio.ts`) y con su motivo: *«el máximo de los últimos 60 días»*. **Nunca «90 días»**:
 *     la ventana es la que tiene la serie.
 *  3. **El historial**, con el mínimo y el máximo reales al lado del trazo y las fechas de la
 *     ventana. *Un producto nuevo no dibuja una línea falsa: se dice que no hay historial.*
 *  4. **Dónde sale mejor**: primero el **mismo artículo en otras cadenas** (ahí sí hay ahorro, porque
 *     es el mismo producto), y después las otras marcas y formatos. *Un ahorro solo se escribe
 *     cuando los dos precios se pueden restar de verdad; cuando no, se dice por qué.*
 *  5. **El etiquetado** (Nutri-Score, sellos, certificados) y, al final, los datos de la etiqueta.
 *
 *  **Y §8 manda en los textos**: nada de API, de EAN, de «gold», de cómo se calcula nada. Una
 *  explicación que ayuda a leer una medida se queda («3,15 € el kilo», «el máximo de los últimos 60
 *  días»); lo que habla de cómo está hecha la app, no.
 *
 *  ================================ LOS DATOS ================================
 *
 *  *`/api/producto` devuelve **13 claves** y ninguna es `ean`; `/api/grupo` trae la ficha completa de
 *  cada miembro.* *La identidad se lee de `miembro`, no de `producto`: leer `producto.ean` rechazaba
 *  **todo**, incluidas las coincidencias exactas, y el defecto se disfrazaba de arreglo.*
 */
import { useMemo, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { yo } from '../api/cesta'
import { esErrorApi } from '../api/cliente'
import { useProducto } from '../api/consultas'
import {
  cantidad as textoCantidad,
  diasDesde,
  euros,
  eurosUnidad,
  fecha as fechaTexto,
  filasNutricion,
  ms,
  nombreCadena,
  numero,
  NO_LO_SE,
  selloLegible,
  textoOrigenSello,
} from '../api/formato'
import { BotonAnadirACesta } from '../componentes/BotonAnadirACesta'
import { BotonFavorito } from '../componentes/BotonFavorito'
import { Campana } from '../componentes/Campana'
import { Chispa, type PuntoChispa } from '../componentes/Chispa'
import { SelloOferta, SelloRetirada } from '../componentes/Etiquetas'
import { useTitulo } from '../componentes/Titulo'
import {
  IconoCheck,
  IconoPrecioAbajo,
  IconoPrecioArriba,
  IconoPrecioIgual,
} from '../componentes/iconos'
import { Aviso, Boton, Fallo, Resumen, Vacio, cx } from '../componentes/ui'
import { serieDeChispa } from '../logica/chispa'
import { loQueDiceLaCurva } from '../logica/curva'
import { construyeComparacion, precioComparable } from '../logica/grupo'
import { veredictoDelPrecio, type Veredicto } from '../logica/juicio'
import type { Producto as MiembroDeGrupo, PuntoSerie } from '../tipos'

export function Producto() {
  const { fuente = '', idFuente = '' } = useParams<{ fuente: string; idFuente: string }>()
  const navega = useNavigate()
  const consulta = useProducto(fuente, idFuente)
  const productoIdExacto = `${fuente}:${idFuente}`

  const producto = consulta.data?.producto
  const grupo = consulta.data?.grupo ?? null

  // El título de la pestaña con el nombre del producto, que es lo que distingue esta pestaña de las
  // otras nueve. Mientras el dato viaja se queda «Producto», que lo pone `App` por ruta.
  useTitulo(producto?.nombre ?? grupo?.nombre)

  // **La sesión, para no pintar acciones que no se pueden cumplir.** *«Guardar» y «Añadir» piden
  // sesión; sin ella los dos botones no se pintan (lo decide cada componente), así que la sección
  // entera se salta y no deja un hueco de 24 px en medio de la ficha.*
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const conSesion = sesion.data?.usuario != null

  /** El miembro del grupo que corresponde a este producto, con la ficha completa.
   *
   *  `/api/producto` devuelve menos campos (no trae imágenes, ni promoción, ni ingredientes); la
   *  entrada del grupo los tiene ya. Se usa lo que hay, sin pedir nada de más.
   */
  const miembro = useMemo(
    () =>
      producto && grupo
        ? (grupo.productos.find(
            (p) => p.fuente === producto.fuente && p.id_fuente === idFuente,
          ) ?? null)
        : null,
    [producto, grupo, idFuente],
  )

  /** De dónde salen los sellos, en palabras. `null` si este producto no tiene. */
  const origenDeSellos = textoOrigenSello(miembro?.sellos_origen)

  /** Cuánto puede bailar el peso, si el producto se vende al peso. `null` si no. */
  const pesoVariable = miembro?.peso_variacion_pct ?? null

  /** **La serie de ESTE producto, con sus días y sus huecos.**
   *
   *  *La serie de la API trae `producto_id` desde el 22 de septiembre de 2026, así que se filtra por
   *  producto y no solo por cadena.* *Antes se filtraba por cadena y, si esa cadena tenía dos
   *  productos en el grupo, **no se dibujaba nada** porque la línea mezclaría dos precios.*
   *  *Con el producto en cada punto eso ya no hace falta: se puede dibujar el suyo.* *Y si la API
   *  es vieja y no manda el campo, se cae a la cadena y se mantiene la guarda de siempre: mejor no
   *  dibujar que dibujar dos productos juntos.*
   */
  const historico = useMemo<{
    puntos: PuntoChispa[]
    bloqueado: boolean
    serie: PuntoSerie[]
  }>(() => {
    if (!grupo) return { puntos: [], bloqueado: false, serie: [] }
    const delProducto = grupo.serie.filter((s) => s.producto_id === productoIdExacto)
    const deLaCadena = grupo.serie.filter((s) => s.fuente === fuente)
    const otrosEnLaCadena = grupo.productos.filter(
      (p) => p.fuente === fuente && p.id_fuente !== idFuente,
    ).length
    const propios = delProducto.length > 0 ? delProducto : deLaCadena
    const bloqueado = delProducto.length === 0 && otrosEnLaCadena > 0
    const serie = [...propios].sort((a, b) => ms(a.fecha) - ms(b.fecha))
    const puntos = serie.map<PuntoChispa>((s) => ({
      fecha: s.fecha,
      valor: s.precio_unidad_cent,
      unidad: s.unidad_canon ?? null,
    }))
    return { puntos, bloqueado, serie }
  }, [grupo, fuente, idFuente, productoIdExacto])

  /** Lo que dice la curva: la frase, o el motivo por el que no la hay. */
  const curva = useMemo(
    () => loQueDiceLaCurva(historico.bloqueado ? [] : historico.serie, { numero }),
    [historico],
  )

  /** **El veredicto del chip**, con su ventana real. `null` si no hay serie que juzgar. */
  const veredicto = useMemo(
    () => (historico.bloqueado ? null : veredictoDelPrecio(historico.serie)),
    [historico],
  )

  // ------------------------------------------------------------------ estados

  if (consulta.isPending) return <EsqueletoDeFicha />

  if (consulta.isError) {
    // *** UN 404 NO ES UN FALLO: ES QUE ESE PRODUCTO NO ESTÁ. ***
    // *Antes caía en el error rojo «No he podido traer esto» con un «No existe.» debajo, que se lee
    // como que la aplicación está rota. Y el producto puede haber desaparecido del catálogo de la
    // cadena, que es una respuesta, no una avería.*
    const noEsta = esErrorApi(consulta.error) && consulta.error.estado === 404
    return (
      <div className="flex flex-col gap-4">
        <Boton variante="sutil" onClick={() => navega(-1)} className="self-start pl-0">
          ← Volver
        </Boton>
        {noEsta ? (
          <NoTengoEseProducto />
        ) : (
          <Fallo error={consulta.error} reintentar={() => void consulta.refetch()} />
        )}
      </div>
    )
  }

  if (!producto) {
    return (
      <div className="flex flex-col gap-4">
        <Boton variante="sutil" onClick={() => navega(-1)} className="self-start pl-0">
          ← Volver
        </Boton>
        <NoTengoEseProducto />
      </div>
    )
  }

  // ------------------------------------------------------- lo que se va a pintar

  const cantidadDeEste = textoCantidad(producto.cantidad, producto.unidad)
  const marca = producto.marca?.trim() ?? ''
  const laMarcaYaEsta = marca.length > 0 && producto.nombre.toLowerCase().includes(marca.toLowerCase())
  const unidadDeEste = producto.unidad?.trim() || null
  const nombreDeLaUnidad = nombreUnidad(unidadDeEste)
  const hayPrecioPorUnidad =
    producto.precio_unidad_cent != null &&
    Number.isFinite(producto.precio_unidad_cent) &&
    producto.precio_unidad_cent > 0

  // *** LA IDENTIDAD SALE DE `miembro`, NO DE `producto`. *** *`producto` no trae `ean`.*
  const conIdentidad = miembro ?? producto
  // *Un único resultado de comparación, y todo sale de aquí* (`logica/grupo.ts`).
  const comp = construyeComparacion(conIdentidad, grupo?.productos ?? [])

  const esEste = (p: { fuente: string; id_fuente: string }) =>
    p.fuente === producto.fuente && p.id_fuente === idFuente

  /** **El mismo artículo, cadena a cadena.** *Aquí sí se puede restar: es el mismo producto medido
   *  igual. Y es donde vive el «te ahorras», porque es dinero del artículo que se lleva.*
   *
   *  *Se quita el elegido de `comparables` al pintar y se vuelve a meter por `producto_id`, para que
   *  su fila esté siempre en la lista aunque la API no lo devuelva entre los candidatos.*
   */
  const filasDelMismo = (() => {
    const porId = new Map<string, MiembroDeGrupo>()
    if (miembro) porId.set(miembro.producto_id, miembro)
    for (const p of comp.comparables) porId.set(p.producto_id, p)
    return [...porId.values()]
      .filter((p) => p.precio_unidad_cent != null && p.precio_unidad_cent > 0)
      .sort((a, b) => (a.precio_unidad_cent as number) - (b.precio_unidad_cent as number))
  })()
  const otrasCadenas = filasDelMismo.filter((p) => !esEste(p))
  const precioMinimoDelMismo = filasDelMismo.length > 0
    ? (filasDelMismo[0].precio_unidad_cent as number)
    : null
  const cadenaMasBarata = filasDelMismo.find((p) => !esEste(p) && p.precio_unidad_cent === precioMinimoDelMismo)
  const ahorroPorUnidad =
    hayPrecioPorUnidad && comp.minimo != null && (producto.precio_unidad_cent as number) > comp.minimo
      ? (producto.precio_unidad_cent as number) - comp.minimo
      : null

  /** **Las otras marcas y formatos**: se enseñan, no se restan como si fueran este artículo. */
  const otras = comp.distintas
    .filter((p) => !esEste(p))
    .sort(porPrecioUnidad)
  const mismoOtraBase = comp.mismoSinComparar.filter((p) => !esEste(p))
  const sinVerificar = comp.sinVerificar.filter((p) => !esEste(p))
  const masBarataDeLasOtras = (() => {
    if (otras.length < 2 || !hayPrecioPorUnidad) return null
    const comparables = otras.filter(
      (p) => precioComparable(conIdentidad, p) && p.comparable !== false && p.precio_unidad_cent != null,
    )
    if (comparables.length === 0) return null
    const minimo = Math.min(...comparables.map((p) => p.precio_unidad_cent as number))
    // *** SOLO SE MARCA SI DE VERDAD ES MÁS BARATA QUE LA QUE SE ESTÁ MIRANDO. ***
    // *«La más barata» al lado de una cifra más cara que la de arriba se lee como una oferta, y no
    // lo es: es la menos cara de las otras.* *Cuando todas son más caras, la respuesta ya la da el
    // «+X €/kg» de cada fila, y la más barata es la que se está mirando.*
    return minimo < (producto.precio_unidad_cent as number) ? minimo : null
  })()

  /** Lo que se dice de las otras opciones antes de enseñarlas. *Cuatro casos, y los cuatro son
   *  distintos: hay otras cadenas con el mismo artículo; lo hay pero en otra unidad; no lo sé porque
   *  no hay con qué confirmarlo; o de verdad no hay ninguna.* *Decir «ninguna otra cadena vende este
   *  mismo artículo» cuando Carrefour lo tiene en otra unidad es falso, y la pantalla lo enseñaría
   *  dos bloques más abajo.* */
  const parrafoDeLasOtras =
    otrasCadenas.length > 0
      ? hayPrecioPorUnidad
        ? 'Otra marca o formato. La diferencia va por kilo, frente a esta.'
        : 'Otra marca o formato.'
      : mismoOtraBase.length > 0
        ? 'Ninguna otra cadena lo vende en la misma unidad. Estas son otras marcas o formatos.'
        : sinVerificar.length > 0
          ? 'No sé si otra cadena vende este mismo artículo; estas son otras marcas o formatos.'
          : 'Ninguna otra cadena vende este mismo artículo: estas son otras marcas o formatos.'

  const serie = serieDeChispa(historico.puntos)
  const diasConPrecio = historico.puntos.filter((p) => p.valor != null && p.valor > 0).length
  const unidadDeLaSerie = veredicto?.unidad ?? unidadDeEste ?? grupo?.unidad ?? null

  // Los nutrientes de Open Food Facts, en el orden en que se lee una etiqueta de verdad. `null` es
  // «no lo sabemos», nunca cero.
  const filasOff = (() => {
    const campos: [keyof typeof producto, string, string][] = [
      ['kcal_100g', 'Energía', 'kcal'],
      ['grasas_100g', 'Grasas', 'g'],
      ['grasas_sat_100g', 'de las cuales saturadas', 'g'],
      ['hidratos_100g', 'Hidratos de carbono', 'g'],
      ['azucares_100g', 'de los cuales azúcares', 'g'],
      ['proteinas_100g', 'Proteínas', 'g'],
      ['sal_100g', 'Sal', 'g'],
    ]
    return campos
      .map(([clave, texto, unidad]) => ({
        clave,
        texto,
        unidad,
        valor: typeof producto[clave] === 'number' ? (producto[clave] as number) : null,
      }))
      .filter((f) => f.valor !== null)
  })()

  const datosDeLaEtiqueta = [
    ['Origen', miembro?.origen],
    ['Conservación', miembro?.conservacion],
    ['Envase', miembro?.envase],
    ['Caducidad', miembro?.dias_caducidad != null ? `${numero(miembro.dias_caducidad, 0)} días` : null],
    ['Peso neto', miembro?.peso_neto_g != null ? `${numero(miembro.peso_neto_g, 0)} g` : null],
    ['Graduación', miembro?.grado_alcohol != null ? `${numero(miembro.grado_alcohol)} %` : null],
  ].filter(([, valor]) => Boolean(valor)) as [string, string][]

  const hayEtiquetado = Boolean(
    producto.nutriscore ||
      producto.kcal_100g != null ||
      producto.ecoscore ||
      miembro?.sellos.length ||
      miembro?.certificados.length ||
      miembro?.promo ||
      miembro?.promo_club ||
      miembro?.es_recall,
  )

  return (
    <div className="flex min-h-full flex-col gap-6">
      {/* ------------------------------------------------ volver, sin perder el sitio */}
      <div className="flex items-center justify-between gap-2">
        <Boton variante="sutil" onClick={() => navega(-1)} className="pl-0">
          ← Volver
        </Boton>
        {grupo && conSesion && <BotonFavorito grupoId={grupo.grupo_id} />}
      </div>

      {/* ---------------------------------------------- qué es y cuánto cuesta */}
      <section aria-labelledby="ficha-titulo">
        <p className="text-micro uppercase text-tinta-tenue">
          {(grupo?.cadenas ?? 1) > 1
            ? `${grupo?.cadenas} cadenas lo venden`
            : `solo en ${nombreCadena(producto.fuente)}`}
        </p>
        {/* *** EL NOMBRE ES UN `h2`, NO UN `h1`. *** *El `h1` de la pantalla lo pone el armazón
            (la miga de pan de la suite), y dos `h1` en la misma pantalla dejan el documento sin
            título único: los lectores de pantalla anuncian dos. La jerarquía visual no cambia.* */}
        <h2
          id="ficha-titulo"
          className="mt-1 font-display text-titulo font-semibold text-tinta"
        >
          {producto.nombre}
        </h2>
        <p className="mt-1 text-etiqueta text-tinta-suave">
          {cantidadDeEste}
          {' · '}
          {nombreCadena(producto.fuente)}
          {marca && !laMarcaYaEsta ? ` · ${marca}` : ''}
        </p>

        {/* *** EL PRECIO, Y AL LADO LA CIFRA QUE PERMITE COMPARAR. *** *
            *Si no hay €/kg no se rellena con el precio del envase: se dice que no hay, que es la
            misma regla que el resto de la aplicación.* */}
        <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="cifra text-precio-grande font-semibold text-tinta">
            {euros(producto.precio_cent)}
          </span>
          {hayPrecioPorUnidad ? (
            <span className="cifra text-etiqueta text-precio-unidad">
              {eurosUnidad(
                producto.precio_unidad_cent,
                unidadDeEste,
                producto.precio_por_escurrido,
              )}
            </span>
          ) : (
            <span className="text-etiqueta text-precio-unidad">
              no hay precio por {nombreDeLaUnidad}
            </span>
          )}
        </div>

        {/* *El €/kg sobre el escurrido hay que decirlo donde está la cifra: «4,23 €/kg» y «4,23 €/kg
            escurrido» son dos afirmaciones distintas.* */}
        {producto.precio_por_escurrido && (
          <p className="mt-1 text-etiqueta text-tinta-suave">
            sobre {textoCantidad((producto.peso_escurrido_g ?? 0) / 1000, 'kg')} escurridos
          </p>
        )}

        {veredicto && <ChipDelPrecio v={veredicto} />}

        {/* Al peso, el precio es una estimación y hay que decirlo antes de enterarse en la caja. */}
        {pesoVariable !== null && (
          <p className="mt-2 text-etiqueta text-tinta-suave">
            Al peso: ronda los {cantidadDeEste} y puede variar un {numero(pesoVariable)} %.
          </p>
        )}
      </section>

      {/* ------------------------------------------------ la acción de esta pantalla */}
      {conSesion && (
        <section aria-label="Acciones" className="flex flex-wrap items-center gap-2">
          <BotonAnadirACesta
            key={productoIdExacto}
            productoId={productoIdExacto}
            nombre={producto.nombre}
          />
          {grupo && <Campana grupoId={grupo.grupo_id} />}
        </section>
      )}

      {/* ---------------------------------------------- el historial, con sus días reales */}
      {grupo ? (
        <section
          aria-labelledby="historial"
          className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
        >
          <div className="flex items-baseline justify-between gap-2">
            <h2 id="historial" className="text-cuerpo-fuerte text-tinta">
              Precio en {nombreCadena(fuente)}
            </h2>
            {diasConPrecio > 0 && (
              <span className="cifra text-etiqueta text-tinta-tenue">
                {diasConPrecio} {diasConPrecio === 1 ? 'día' : 'días'} · €/{unidadDeLaSerie ?? 'ud'}
              </span>
            )}
          </div>

          {historico.bloqueado ? (
            <Aviso tono="aviso" titulo="Sin histórico de este precio">
              <p>
                Esta cadena tiene más de un producto parecido y no puedo separar cuál es cuál. No
                dibujo una línea que mezclaría dos precios.
              </p>
            </Aviso>
          ) : historico.puntos.length === 0 ? (
            // *** UN PRODUCTO NUEVO NO DIBUJA UNA LÍNEA. *** *No hay serie, y eso se dice: una línea
            // plana «porque no ha cambiado» sería inventarse un histórico que nadie ha medido.* *Y
            // no se dice «es la primera vez que vemos este precio»: de una serie vacía no se infiere
            // un solo día -- es la regla de `chispa.ts` --, se dice que no hay historial.*
            <p className="mt-3 text-cuerpo text-tinta-suave">
              Todavía no hay historial de este precio.
            </p>
          ) : (
            <>
              {/* *La ventana, en fechas: es el eje que la línea no puede poner sin mentir.* */}
              <p className="mt-1 text-etiqueta text-tinta-suave">
                Del {fechaTexto(historico.puntos[0]?.fecha, true)} a{' '}
                {diasDesde(historico.puntos[historico.puntos.length - 1]?.fecha) === 0
                  ? 'hoy'
                  : fechaTexto(historico.puntos[historico.puntos.length - 1]?.fecha, true)}
              </p>

              {serie.dibujable ? (
                <div
                  className={
                    veredicto
                      ? 'mt-3 grid grid-cols-[auto_minmax(0,1fr)] gap-x-2'
                      : 'mt-3'
                  }
                >
                  {/* *El mínimo y el máximo reales, al lado del trazo: es el eje de verdad.*
                      *Con el precio plano (mínimo = máximo) hay una sola cifra, y va centrada
                      porque la línea va centrada: uPlot abre el eje alrededor del valor.* */}
                  {veredicto && (
                    <div
                      aria-hidden="true"
                      className={cx(
                        'cifra flex h-[120px] flex-col whitespace-nowrap text-right text-etiqueta text-tinta-tenue',
                        veredicto.maximo === veredicto.minimo
                          ? 'justify-center'
                          : 'justify-between',
                      )}
                    >
                      <span>{euros(veredicto.maximo)}</span>
                      {veredicto.maximo !== veredicto.minimo && (
                        <span>{euros(veredicto.minimo)}</span>
                      )}
                    </div>
                  )}
                  <div className="min-w-0">
                    <Chispa
                      puntos={historico.puntos}
                      alto={120}
                      etiqueta={`Precio de ${producto.nombre} en ${nombreCadena(fuente)}`}
                      rango={
                        veredicto && veredicto.maximo > veredicto.minimo
                          ? [veredicto.minimo, veredicto.maximo]
                          : null
                      }
                    />
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-cuerpo text-tinta-suave">{serie.motivoUnidad}</p>
              )}

              {/* **La frase debajo de la curva**: una línea que sube y baja sin decir nada es un
                  adorno. Las reglas -- y sobre todo cuándo NO hay frase -- están en `curva.ts`.
                  *Con el precio plano no se repite el chip*: `curva.ts` diría «es el precio más
                  bajo de los N días», que con todos los días al mismo precio es cierto y no informa
                  de nada.* */}
              {curva.frase && !(veredicto && veredicto.maximo === veredicto.minimo) && (
                <p className="mt-3 text-cuerpo font-semibold text-tinta">{curva.frase}</p>
              )}
              {/* *Con un solo día no se puede decir si está caro: se dice eso, y no se calla.* */}
              {diasConPrecio === 1 && !curva.frase && (
                <p className="mt-3 text-cuerpo text-tinta-suave">
                  Solo tenemos un día de este precio, así que no hay con qué compararlo.
                </p>
              )}
              {curva.motivo && <p className="mt-1 text-etiqueta text-tinta-suave">{curva.motivo}</p>}
              {veredicto && veredicto.huecos > 0 && (
                <p className="mt-1 text-etiqueta text-tinta-suave">
                  {veredicto.huecos} {veredicto.huecos === 1 ? 'día' : 'días'} del histórico{' '}
                  {veredicto.huecos === 1 ? 'no tiene' : 'no tienen'} precio: en la línea se ven
                  como huecos.
                </p>
              )}
            </>
          )}
        </section>
      ) : (
        // *Sin grupo no hay serie ni alternativas, y se dice en una línea en vez de enseñar dos
        // secciones vacías.*
        <section className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
          <h2 className="text-cuerpo-fuerte text-tinta">Sin historial todavía</h2>
          <p className="mt-1 text-cuerpo text-tinta-suave">
            No hay otros productos parecidos con los que compararlo, así que de momento no hay
            precios anteriores ni alternativas que enseñar.
          </p>
        </section>
      )}

      {/* ---------------------------------------------- el mismo artículo, en otras cadenas */}
      {otrasCadenas.length > 0 && (
        <section aria-labelledby="cadenas">
          <div className="flex items-baseline justify-between gap-2">
            <h2 id="cadenas" className="font-display text-titulo font-semibold text-tinta">
              En otras cadenas
            </h2>
            <span className="text-etiqueta text-tinta-tenue">mismo artículo</span>
          </div>

          {/* *** EL AHORRO, CON SU CADENA Y SU UNIDAD. *** *Es lo que se viene a saber: cuánto
              cuesta el mismo producto en otro sitio.* *Y se dice «más barato en» y no «cuesta un 18 %
              más que en»: la segunda forma habla de la diferencia contra una cadena concreta y deja
              fuera a las demás.* */}
          {ahorroPorUnidad != null && cadenaMasBarata && (
            <p className="mt-2 text-cuerpo font-semibold text-tinta">
              Está más barato en {nombreCadena(cadenaMasBarata.fuente)}: te ahorras{' '}
              <span className="cifra text-precio-baja">
                {eurosUnidad(ahorroPorUnidad, unidadDeEste)}
              </span>
              .
            </p>
          )}

          <div className="mt-3 overflow-hidden rounded-tarjeta bg-papel shadow-apoyado">
            {filasDelMismo.map((p) => {
              const propio = esEste(p)
              const barata = !propio && p.precio_unidad_cent === precioMinimoDelMismo
              return (
                <FilaDePrecio
                  key={p.producto_id}
                  p={p}
                  protagonista="cadena"
                  esEste={propio}
                  remate={
                    propio ? (
                      <span className="text-etiqueta-fuerte text-terracota">donde estás</span>
                    ) : barata ? (
                      <RemateMasBarata />
                    ) : p.precio_unidad_cent != null && precioMinimoDelMismo != null ? (
                      <span className="cifra text-etiqueta text-tinta-suave">
                        +{eurosUnidad(p.precio_unidad_cent - precioMinimoDelMismo, unidadDeEste)}
                      </span>
                    ) : null
                  }
                />
              )
            })}
          </div>
        </section>
      )}

      {/* ---------------------------------------------- las otras marcas y formatos */}
      {(otras.length > 0 || mismoOtraBase.length > 0 || sinVerificar.length > 0) && (
        <section aria-labelledby={otras.length > 0 ? 'opciones' : undefined}>
          {/* *El título solo cuando hay lista debajo: un «Otras opciones» con la lista vacía es una
              promesa que la pantalla no cumple.* */}
          {otras.length > 0 && (
            <div className="flex items-baseline justify-between gap-2">
              <h2 id="opciones" className="font-display text-titulo font-semibold text-tinta">
                Otras opciones
              </h2>
              <span className="text-etiqueta text-tinta-tenue">{otras.length}</span>
            </div>
          )}

          {otras.length > 0 && (
            <>
              {/* *Se dice de qué es la diferencia antes de enseñarla: de artículos distintos, por
                  kilo. Sin esto, «1,36 €/kg menos» parece el ahorro del que se lleva.* */}
              <p className="mt-1 text-etiqueta text-tinta-suave">{parrafoDeLasOtras}</p>

              <div className="mt-3 overflow-hidden rounded-tarjeta bg-papel shadow-apoyado">
                {otras.map((p) => {
                  const sePuedeRestar =
                    p.comparable !== false &&
                    p.precio_unidad_cent != null &&
                    hayPrecioPorUnidad &&
                    precioComparable(conIdentidad, p)
                  const diferencia =
                    sePuedeRestar && p.precio_unidad_cent != null
                      ? p.precio_unidad_cent - (producto.precio_unidad_cent as number)
                      : null
                  const barata = masBarataDeLasOtras != null && p.precio_unidad_cent === masBarataDeLasOtras
                  return (
                    <FilaDePrecio
                      key={p.producto_id}
                      p={p}
                      protagonista="producto"
                      resaltada={barata}
                      nota={sePuedeRestar ? null : porqueNoSeResta(p, unidadDeEste)}
                      remate={
                        barata ? (
                          <RemateMasBarata />
                        ) : diferencia != null ? (
                          <span
                            className={cx(
                              'cifra text-etiqueta',
                              diferencia < 0 ? 'font-semibold text-precio-baja' : 'text-tinta-suave',
                            )}
                          >
                            {textoDeLaDiferencia(diferencia, unidadDeEste)}
                          </span>
                        ) : null
                      }
                    />
                  )
                })}
              </div>
            </>
          )}

          {mismoOtraBase.length > 0 && (
            <div className="mt-4">
              <h2 className="font-display text-subtitulo font-semibold text-tinta">
                Mismo artículo, otra forma de medirlo
              </h2>
              <p className="mt-1 text-etiqueta text-tinta-suave">
                Es el mismo producto, pero se mide de otra forma
                {unidadesDe(mismoOtraBase)
                  ? ` (por ${unidadesDe(mismoOtraBase)}${unidadDeEste ? ` y no por ${nombreUnidad(unidadDeEste)}` : ''})`
                  : ''}{' '}
                y los precios no se restan.
              </p>
              <div className="mt-2 overflow-hidden rounded-tarjeta bg-papel shadow-apoyado">
                {mismoOtraBase.map((p) => (
                  <FilaDePrecio
                    key={p.producto_id}
                    p={p}
                    protagonista="producto"
                    nota={porqueNoSeResta(p, unidadDeEste)}
                    remate={null}
                  />
                ))}
              </div>
            </div>
          )}

          {sinVerificar.length > 0 && (
            <div className="mt-4">
              <h2 className="font-display text-subtitulo font-semibold text-tinta">
                No sé si es el mismo producto
              </h2>
              <p className="mt-1 text-etiqueta text-tinta-suave">
                No hay con qué confirmarlo, así que no lo comparo ni lo resto.
              </p>
              <div className="mt-2 overflow-hidden rounded-tarjeta bg-papel shadow-apoyado">
                {sinVerificar.map((p) => (
                  <FilaDePrecio
                    key={p.producto_id}
                    p={p}
                    protagonista="producto"
                    nota={porqueNoSeResta(p, unidadDeEste)}
                    remate={null}
                  />
                ))}
              </div>
            </div>
          )}

          {/* **Enlace a la comparación del grupo**: la ficha responde «¿dónde sale mejor?» con una
              lista; la pantalla de columnas la responde entera, con las curvas de cada cadena. */}
          {grupo && grupo.productos.length > 1 && (
            <p className="mt-4">
              <Link
                to={`/grupo/${grupo.grupo_id}`}
                className="inline-flex min-h-[44px] items-center gap-1 text-cuerpo font-semibold text-verde underline underline-offset-2 transition-colors duration-rapida ease-suave hover:text-verde-fuerte"
              >
                Ver la comparación de las {grupo.cadenas} cadenas
              </Link>
            </p>
          )}
        </section>
      )}

      {/* ---------------------------------------------- el etiquetado, legible */}
      {hayEtiquetado && (
        <section aria-labelledby="etiquetado">
          <h2 id="etiquetado" className="font-display text-titulo font-semibold text-tinta">
            Etiquetado
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2">
            <LetraNutri valor={producto.nutriscore} />
            {producto.kcal_100g != null && (
              <span className="cifra text-etiqueta text-tinta-suave">
                {numero(producto.kcal_100g, 0)} kcal/100 g
              </span>
            )}
            <LetraEco valor={producto.ecoscore} />
            {miembro?.sellos.map((s) => (
              <span
                key={s}
                className="inline-flex min-h-6 items-center rounded-pastilla bg-sello-fondo px-2 text-etiqueta-fuerte text-sello-tinta"
              >
                {selloLegible(s)}
              </span>
            ))}
            {/* *Los certificados van aparte porque son la prueba fuerte: no los dice el nombre, los
                audita un tercero.* */}
            {miembro?.certificados.map((c) => (
              <span
                key={c}
                className="inline-flex min-h-6 items-center rounded-pastilla bg-lavado-verde px-2 text-etiqueta-fuerte text-tinta"
                title="Lo audita un tercero, no lo dice el nombre"
              >
                {selloLegible(c)}
              </span>
            ))}
            <SelloOferta
              texto={miembro?.promo ?? null}
              club={miembro?.promo_club ?? null}
              unidades={miembro?.promo_unidades ?? null}
            />
            <SelloRetirada retirado={miembro?.es_recall ?? null} />
          </div>
          {origenDeSellos && (
            // *Entre paréntesis y sin frase alrededor: el dato es una aclaración de los sellos de
            // arriba, no una línea propia.* *Y así vale para los cuatro valores sin inventar
            // concordancia («sellos leído» no se puede escribir).*
            <p className="mt-2 text-etiqueta text-tinta-suave">({origenDeSellos})</p>
          )}
        </section>
      )}

      {/* ---------------------------------------------- lo que dice la etiqueta */}
      {miembro && (
        <section aria-labelledby="mas-datos">
          <h2 id="mas-datos" className="font-display text-titulo font-semibold text-tinta">
            Más datos
          </h2>

          {/* *Los alérgenos van primero y en rojo: es lo único de esta pantalla que puede hacer
              daño a alguien.* */}
          {miembro.alergenos && (
            <p className="mt-3 rounded-campo bg-lavado-error px-3 py-2 text-cuerpo text-error">
              <strong>Alérgenos:</strong> {miembro.alergenos}
            </p>
          )}

          {miembro.ingredientes && (
            <details className="mt-3">
              {/* *44 px, aunque sea una palabra*: es donde se mira si algo lleva lo que no se puede
                  comer. Lo vigila `test_ui_movil.py`.* */}
              <Resumen className="text-cuerpo-fuerte text-tinta">
                Ingredientes
              </Resumen>
              <p className="mt-1 text-cuerpo">{miembro.ingredientes}</p>
            </details>
          )}

          {/* *Cuando la cadena no publica nutrición, la de Open Food Facts, con la misma forma y la
              base dicha. Es la misma información de otra fuente, no otra cosa.* */}
          {!miembro.nutricion && filasOff.length > 0 && (
            <div className="mt-3">
              <h3 className="text-cuerpo-fuerte text-tinta">Nutrición (por 100 g)</h3>
              <ul className="mt-1 grid gap-1 text-cuerpo">
                {filasOff.map((f) => (
                  <li
                    key={f.clave}
                    className="flex justify-between gap-2 border-b border-borde py-1"
                  >
                    <span className="text-tinta-suave">{f.texto}</span>
                    <span className="cifra font-medium">
                      {f.valor === null ? NO_LO_SE : `${numero(f.valor)} ${f.unidad}`}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-etiqueta text-tinta-tenue">
                De Open Food Facts: pueden faltar o ser aproximados.
              </p>
            </div>
          )}

          {miembro.nutricion && (
            <div className="mt-3">
              <h3 className="text-cuerpo-fuerte text-tinta">
                Nutrición {miembro.nutricion_por ? `(por ${miembro.nutricion_por})` : ''}
              </h3>
              <ul className="mt-1 grid gap-1 text-cuerpo">
                {filasNutricion(miembro.nutricion).map((f) => (
                  <li
                    key={f.clave}
                    className="flex justify-between gap-2 border-b border-borde py-1"
                  >
                    <span className="text-tinta-suave">{f.texto}</span>
                    <span className="cifra font-medium">
                      {f.valor === null
                        ? NO_LO_SE
                        : `${numero(f.valor, 2)}${f.unidad ? ` ${f.unidad}` : ''}`}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {datosDeLaEtiqueta.length > 0 && (
            <dl className="mt-3 grid gap-2">
              {datosDeLaEtiqueta.map(([etiqueta, valor]) => (
                <div key={etiqueta} className="flex justify-between gap-3 border-b border-borde py-1">
                  <dt className="text-cuerpo text-tinta-suave">{etiqueta}</dt>
                  <dd className="text-cuerpo text-right">{valor}</dd>
                </div>
              ))}
            </dl>
          )}

          {miembro.descripcion && (
            <p className="mt-3 text-cuerpo text-tinta-suave">{miembro.descripcion}</p>
          )}

          {miembro.url && (
            <p className="mt-3">
              <a
                href={miembro.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-[44px] items-center text-cuerpo text-verde underline underline-offset-2"
              >
                Ver en {nombreCadena(miembro.fuente)}
              </a>
            </p>
          )}
        </section>
      )}
    </div>
  )
}

/** «No tengo ese producto», que es una respuesta y no un fallo.
 *
 *  *El enlace mide 44 px de alto como todo lo que se pulsa: medido el 5/11/2026 en la página de un
 *  404, «Volver al buscador» medía **132 x 20**.*
 */
function NoTengoEseProducto() {
  return (
    <Vacio titulo="No tengo ese producto">
      <p>Puede que ya no lo vendan o que el enlace esté mal.</p>
      <p className="mt-2">
        <Link to="/" className="inline-flex min-h-[44px] items-center underline">
          Volver al buscador
        </Link>
      </p>
    </Vacio>
  )
}

// ---------------------------------------------------------------- las piezas ---

/** **La respuesta a «¿esto está caro?», con flecha y palabra.**
 *
 *  *El color no basta: el par sube/baja no se distingue de un vistazo para todo el mundo, y menos a
 *  pleno sol en la puerta de un supermercado.* *Por eso el chip lleva su flecha (`aria-hidden`,
 *  porque la palabra ya lo dice) y su motivo escrito.*
 *
 *  *Y el color de cada estado es el del sistema:* `lavado-aviso` con `aviso` para lo caro,
 *  `lavado-verde` con tinta para lo bueno — *sobre `lavado-verde` va tinta, nunca verde, que es la
 *  regla del token* — y papel con `borde-fuerte` para el que no es ni una cosa ni la otra.
 */
function ChipDelPrecio({ v }: { v: Veredicto }) {
  const Flecha =
    v.juicio === 'caro' ? IconoPrecioArriba : v.juicio === 'barato' ? IconoPrecioAbajo : IconoPrecioIgual
  return (
    <p
      className={cx(
        'mt-2 inline-flex min-h-8 items-center gap-1.5 rounded-pastilla px-2.5 text-etiqueta-fuerte',
        v.juicio === 'caro'
          ? 'bg-lavado-aviso text-aviso'
          : v.juicio === 'barato'
            ? 'bg-lavado-verde text-tinta'
            : 'border border-borde-fuerte bg-papel text-tinta-suave',
      )}
    >
      <Flecha
        width={14}
        height={14}
        className={v.juicio === 'barato' ? 'shrink-0 text-bien' : 'shrink-0'}
      />
      {v.texto}
    </p>
  )
}

/** Una fila de precio que lleva a la ficha de ese producto en esa cadena.
 *
 *  **`min-h-[44px]` y no un alto de texto**: se pulsa de pie, con el carro en la otra mano. *El
 *  enlace es la fila entera, así que el objetivo es toda la línea y no una palabra.*
 *
 *  `protagonista` decide qué se lee primero: en el mismo artículo manda la cadena (es lo que se
 *  busca), y en las otras opciones manda el producto (es lo que hay que reconocer en la estantería).
 */
function FilaDePrecio({
  p,
  protagonista,
  esEste = false,
  resaltada = false,
  nota = null,
  remate,
}: {
  p: MiembroDeGrupo
  protagonista: 'cadena' | 'producto'
  esEste?: boolean
  resaltada?: boolean
  nota?: string | null
  remate: ReactNode
}) {
  const marca = p.marca?.trim() ?? ''
  const laMarcaYaEsta = marca.length > 0 && p.nombre.toLowerCase().includes(marca.toLowerCase())
  const piezas = [nombreCadena(p.fuente), laMarcaYaEsta ? null : marca, textoCantidad(p.cantidad, p.unidad)]
    .filter((x): x is string => Boolean(x))
  return (
    <Link to={`/producto/${p.fuente}/${p.id_fuente}`}
      aria-current={esEste ? 'true' : undefined}
      className={cx(
        // *44 px y la fila entera pulsable*: se usa de pie, con el carro en la otra mano. Lo mide
        // `tests/test_ui_movil.py`, que es lo que impide que vuelva a medir 19 px.
        'flex min-h-[44px] items-center gap-3 border-b border-borde px-4 py-3',
        'transition-colors duration-rapida ease-suave last:border-b-0',
        esEste ? 'bg-lavado-terracota' : resaltada ? 'bg-lavado-verde' : 'bg-papel hover:bg-marfil',
      )}
    >
      <span className="min-w-0 flex-1">
        <span className="block text-cuerpo-fuerte text-tinta">
          {protagonista === 'cadena' ? nombreCadena(p.fuente) : p.nombre}
        </span>
        <span className="block truncate text-etiqueta text-tinta-suave">
          {protagonista === 'cadena' ? p.nombre : piezas.join(' · ')}
        </span>
        {nota && <span className="block text-etiqueta text-tinta-tenue">{nota}</span>}
      </span>
      {/* *** EL PRECIO, SU €/UNIDAD Y EL REMATE, EN UNA SOLA COLUMNA. *** *
          *Antes el remate era una tercera columna, y con un nombre largo (`Alubia blanca categoría
          extra Luengo 1 kg.`) la columna del nombre se quedaba en 120 px y el nombre salía en tres
          líneas.* *En un móvil de 390 px caben dos columnas; la tercera se lleva el ancho de la que
          importa.* *Y el remate debajo del €/kg se lee mejor: «1,95 € / 4875,00 €/kg / 2000,00 €/kg
          menos» es una cuenta, no tres datos sueltos.* */}
      <span className="shrink-0 text-right">
        <span className="cifra block text-precio-fila font-semibold text-tinta">
          {euros(p.precio_cent)}
        </span>
        {p.precio_unidad_cent != null && (
          <span className="cifra block text-etiqueta text-precio-unidad">
            {eurosUnidad(p.precio_unidad_cent, p.unidad, p.precio_por_escurrido)}
          </span>
        )}
        {remate && <span className="mt-0.5 block">{remate}</span>}
      </span>
    </Link>
  )
}

/** «la más barata», con su marca y su palabra (el color no basta). */
function RemateMasBarata() {
  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap text-etiqueta-fuerte text-tinta">
      <IconoCheck width={16} height={16} className="shrink-0 text-verde" />
      la más barata
    </span>
  )
}

/** La diferencia de precio por unidad, dicha como se lee: «1,36 €/kg menos» o «+0,46 €/kg».
 *
 *  *Con su unidad y no en euros pelados*: «1,36 €» al lado de un precio de envase se lee como el
 *  ahorro de la compra, y lo que se ha restado son precios **por kilo**.
 */
function textoDeLaDiferencia(centimos: number, unidad: string | null): string {
  if (centimos < 0) return `${eurosUnidad(-centimos, unidad)} menos`
  return `+${eurosUnidad(centimos, unidad)}`
}

/** Por qué dos precios no se restan, en lenguaje de usuario. `null` si sí se pueden restar. */
function porqueNoSeResta(p: MiembroDeGrupo, unidadDeEste: string | null): string | null {  const suya = p.unidad?.trim() || null
  if (!suya) return 'no sé en qué se mide'
  if (unidadDeEste && suya !== unidadDeEste) {
    return `va por ${nombreUnidad(suya)} y no por ${nombreUnidad(unidadDeEste)}`
  }
  if (p.precio_por_escurrido) return 'va sobre el peso escurrido'
  if (p.comparable === false) return 'el precio no es de fiar'
  return null
}

/** Las unidades de un grupo de filas, para decirlas en una frase. */
function unidadesDe(filas: MiembroDeGrupo[]): string {
  const unidades = [...new Set(filas.map((p) => nombreUnidad(p.unidad)))]
  return unidades.join(' y ')
}

/** El nombre de una unidad en castellano: `kg` no se lee, «kilo» sí. */
function nombreUnidad(unidad: string | null | undefined): string {
  const u = (unidad ?? '').trim().toLowerCase()
  if (u === 'kg') return 'kilo'
  if (u === 'g') return 'gramo'
  if (u === 'l') return 'litro'
  if (u === 'ml') return 'mililitro'
  if (u === 'ud') return 'unidad'
  if (u === 'm') return 'metro'
  return 'unidad'
}

/** De mayor a menor precio por unidad; los que no tienen precio, al final. */
function porPrecioUnidad(a: MiembroDeGrupo, b: MiembroDeGrupo): number {
  const uno = a.precio_unidad_cent
  const otro = b.precio_unidad_cent
  if (uno == null) return otro == null ? 0 : 1
  if (otro == null) return -1
  return uno - otro
}

/** El Nutri-Score con los tokens del sistema (`nutri-*`), y su letra dicha en palabras. */
const COLOR_NUTRI: Record<string, string> = {
  a: 'bg-nutri-a text-nutri-texto-a',
  b: 'bg-nutri-b text-nutri-texto-b-e',
  c: 'bg-nutri-c text-nutri-texto-b-e',
  d: 'bg-nutri-d text-nutri-texto-b-e',
  e: 'bg-nutri-e text-nutri-texto-e',
}

function LetraNutri({ valor }: { valor: string | null }) {
  const letra = (valor ?? '').trim().toLowerCase()
  const color = COLOR_NUTRI[letra]
  if (!color) return null
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden="true"
        className={cx(
          'inline-flex h-6 w-6 items-center justify-center rounded-nota text-etiqueta-fuerte',
          color,
        )}
      >
        {letra.toUpperCase()}
      </span>
      <span className="text-etiqueta text-tinta-suave">Nutri-Score {letra.toUpperCase()}</span>
    </span>
  )
}

/** El Eco-Score, cuando la cadena o Open Food Facts lo traen. *«No aplica» no es una nota.* */
function LetraEco({ valor }: { valor: string | null }) {
  if (!valor || valor === 'not-applicable') return null
  const grado = valor.toLowerCase() === 'a-plus' ? 'A+' : valor.toUpperCase()
  return <span className="text-etiqueta text-tinta-suave">Eco-Score {grado}</span>
}

/** El esqueleto de la ficha: la forma de lo que viene, sin una sola cifra inventada. */
function EsqueletoDeFicha() {
  return (
    <div className="flex min-h-full flex-col gap-6" role="status" aria-live="polite">
      <span className="sr-only">Cargando la ficha…</span>
      <div aria-hidden="true" className="flex flex-col gap-6">
        <div className="h-11 w-24 animate-pulse rounded-campo bg-borde" />
        <div className="flex flex-col gap-2">
          <div className="h-3 w-24 animate-pulse rounded-campo bg-borde" />
          <div className="h-7 w-3/4 animate-pulse rounded-campo bg-borde" />
          <div className="h-4 w-1/2 animate-pulse rounded-campo bg-borde" />
          <div className="h-8 w-32 animate-pulse rounded-campo bg-borde" />
          <div className="h-8 w-56 animate-pulse rounded-pastilla bg-borde" />
        </div>
        <div className="h-56 animate-pulse rounded-tarjeta bg-papel" />
        <div className="grid gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-tarjeta bg-papel" />
          ))}
        </div>
      </div>
    </div>
  )
}
