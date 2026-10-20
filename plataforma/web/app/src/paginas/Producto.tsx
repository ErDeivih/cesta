/** La ficha de un producto: su historico, su grupo de equivalencias y por que
 *  esta emparejado con esos.
 *
 *  Un producto se identifica por **su id en la cadena** (`dia:12345`), no por el
 *  nuestro: eso es lo unico que se puede sacar de la URL de un supermercado, y
 *  es lo que usa la extension de navegador. Por eso la ruta es
 *  `/producto/{cadena}/{id_fuente}`.
 *
 *  El historico sale de `grupo.serie`, que es la unica serie que da la API. Ojo
 *  con eso: la serie va por **cadena y fecha**, sin decir de que producto es
 *  cada punto. Si la cadena tiene mas de un producto en el grupo, esa linea
 *  mezcla dos productos y no se pinta: se dice.
 */
import { useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useProducto } from '../api/consultas'
import {
  cantidad as textoCantidad,
  euros,
  eurosUnidad,
  fecha as fechaTexto,
  filasNutricion,
  ms,
  NO_LO_SE,
  nombreCadena,
  numero,
  porcentaje,
  porcentajeConSigno,
  selloLegible,
  textoOrigenSello,
} from '../api/formato'
import { BotonAnadirACesta } from '../componentes/BotonAnadirACesta'
import { Campana } from '../componentes/Campana'
import { Chispa, type PuntoChispa } from '../componentes/Chispa'
import { loQueDiceLaCurva } from '../logica/curva'
import { useTitulo } from '../componentes/Titulo'
import { fraseDePrecio } from '../logica/frase'
import { construyeComparacion, identidad, precioComparable } from '../logica/grupo'
import { SelloLetra, SelloNutriscore, SelloOferta, SelloRetirada } from '../componentes/Etiquetas'
import { ExplicacionEmparejamiento } from '../componentes/ExplicacionEmparejamiento'
import { Aviso, Boton, Cargando, Dato, Etiqueta, Fallo, Resumen, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

const NUMERO = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 })


export function Producto() {
  const { fuente = '', idFuente = '' } = useParams<{ fuente: string; idFuente: string }>()
  const navega = useNavigate()
  const consulta = useProducto(fuente, idFuente)
  const productoIdExacto = `${fuente}:${idFuente}`

  const producto = consulta.data?.producto
  const grupo = consulta.data?.grupo ?? null

  // El titulo de la pestana con el nombre del producto, que es lo que distingue esta
  // pestana de las otras nueve. Mientras el dato viaja se queda "Producto", que lo
  // pone `App` por ruta: aqui solo se mejora cuando se sabe mas.
  useTitulo(producto?.nombre ?? grupo?.nombre)

  /** El miembro del grupo que corresponde a este producto, con la ficha
   *  completa. `/api/producto` devuelve menos campos (no trae imágenes, ni
   *  promoción, ni ingredientes); `/api/grupo` los tiene ya. Se usa lo que hay,
   *  sin pedir nada de más. */
  const miembro = useMemo(
    () =>
      producto && grupo
        ? // `/api/producto` no devuelve `id_fuente`, así que se empareja con el
          // identificador de la propia ruta, que es el mismo dato.
          (grupo.productos.find(
            (p) => p.fuente === producto.fuente && p.id_fuente === idFuente,
          ) ?? null)
        : null,
    [producto, grupo, idFuente],
  )

  /** De donde salen los sellos, en palabras. `null` si este producto no tiene.
   *
   *  Se calcula aqui y no dentro del `map` a proposito: es un dato por ficha,
   *  no uno por sello, y dentro del `map` se repetiria en cada etiqueta. */
  const origenDeSellos = textoOrigenSello(miembro?.sellos_origen)

  /** Cuanto puede bailar el peso, si el producto se vende al peso. `null` si no. */
  const pesoVariable = miembro?.peso_variacion_pct ?? null

  const historico = useMemo(() => {
    if (!grupo) {
      return { puntos: [] as PuntoChispa[], bloqueado: false, filas: 0, serie: [] }
    }
    const deLaCadena = grupo.serie.filter((s) => s.fuente === fuente)
    // Cuantos productos de ESTA cadena hay en el grupo: la serie no los separa.
    const cuantos = grupo.productos.filter((p) => p.fuente === fuente).length
    const puntos = deLaCadena
      .map<PuntoChispa>((s) => ({ fecha: s.fecha, valor: s.precio_unidad_cent,
        unidad: s.unidad_canon ?? null }))
      .sort((a, b) => ms(a.fecha) - ms(b.fecha))
    // La serie **con su unidad**, ordenada, que es lo que necesita la frase de debajo
    // de la curva: sin la unidad no se puede decir "el mas bajo de los N dias" sin
    // arriesgarse a comparar kg con ud (`logica/curva.ts`).
    const serie = [...deLaCadena].sort((a, b) => ms(a.fecha) - ms(b.fecha))
    return { puntos, bloqueado: cuantos > 1, filas: cuantos, serie }
  }, [grupo, fuente])

  /** Lo que dice la curva: la frase, o el motivo por el que no la hay.
   *
   *  Se calcula desde la serie **con la unidad** y no desde los puntos de la chispa:
   *  `Chispa` solo necesita fecha y valor, y la unidad es lo que impide comparar dos
   *  series pegadas (`logica/curva.ts`). */
  const curva = useMemo(
    () => loQueDiceLaCurva(historico.bloqueado ? [] : historico.serie),
    [historico.bloqueado, historico.serie],
  )

  const resumen = useMemo(() => {
    const valores = historico.puntos
      .map((p) => p.valor)
      .filter((v): v is number => v !== null && Number.isFinite(v))
    if (valores.length === 0) {
      return { n: 0, min: null, max: null, media: null, primero: null, ultimo: null }
    }
    const min = Math.min(...valores)
    const max = Math.max(...valores)
    const media = valores.reduce((a, b) => a + b, 0) / valores.length
    return {
      n: valores.length,
      min,
      max,
      media,
      primero: valores[0] ?? null,
      ultimo: valores[valores.length - 1] ?? null,
    }
  }, [historico.puntos])

  if (consulta.isPending) return <Cargando que="la ficha" />
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
  if (!producto) {
    return (
      <Vacio titulo="No tengo ese producto">
        <p>
          <Link to="/" className="underline">
            Volver al buscador
          </Link>
        </p>
      </Vacio>
    )
  }

  const evolucion =
    resumen.primero !== null && resumen.ultimo !== null && resumen.primero > 0
      ? (100 * (resumen.ultimo - resumen.primero)) / resumen.primero
      : null

  /** **Dónde está más barato y cuánto se ahorra, en euros por unidad de uso.**
   *
   *  Apartado 2 del punto 3 del encargo, y es la mitad que faltaba en esta ficha: la
   *  frase de arriba ya dice *"cuesta un 18 % más que en DIA"*, pero un porcentaje
   *  abstracto no es lo que se compara en la tienda. Aquí va el producto más barato
   *  del grupo con su €/unidad, y lo que te ahorras comprándolo ahí.
   *
   *  **Solo cuenta lo que se puede comparar de verdad**: misma unidad y precio fiable.
   *  Lo primero no es un detalle: la primera versión de este dato salió en pantalla
   *  diciendo *«te ahorras 6872,01 €/kg»* en la ficha de un azafrán de 0,4 g, porque
   *  comparaba su precio por kilo con el de un bote medido en unidades. Restar €/kg de
   *  €/ud es el disparate que el proyecto ya tiene escrito en tres sitios, y me lo
   *  encontró la puerta del navegador, no una prueba de código.
   *
   *  `null` cuando no hay nada que ahorrar -- este es el más barato de los comparables,
   *  o el grupo no tiene con qué compararlo --: un *"te ahorras 0,00 €"* es ruido. */
  // Los nutrientes de Open Food Facts, en el orden en que se lee una etiqueta de verdad. Null es
  // "no lo sabemos", nunca cero: la guarda de la extraccion ya dejo fuera lo imposible.
  // **NO ES UN `useMemo`, *y ese era el fallo*.**
  //
  // *Estaba escrito con `useMemo` **despues de los tres retornos condicionales** de
  // arriba (`:133` cargando, `:134` error, `:144` producto ausente).*
  // **Una regla de React: los hooks se llaman en el mismo orden en todos los renders.**
  // *Durante la carga ese `useMemo` no se ejecutaba; al llegar el producto, si.*
  // *Un hook mas que en el render anterior => React lanza **#310** y desmonta la raiz:*
  // *por eso se veia el esqueleto y luego la pantalla vacia, y por eso no habia
  // mensaje en el build (-- *en produccion el #310 va minificado* --).*
  //
  // *Se calcula como una expresion normal, que **no es un hook** y por tanto puede ir
  // detras de los retornos sin romper el orden.* *Los siete campos y su guarda son los
  // mismos: lo que no es numero sigue siendo `null` y se descarta, **no se convierte en
  // cero**.*
  const filasOff = (() => {
    const campos: [keyof typeof producto, string, string][] = [
      ['kcal_100g', 'Energia', 'kcal'],
      ['grasas_100g', 'Grasas', 'g'],
      ['grasas_sat_100g', 'de las cuales saturadas', 'g'],
      ['hidratos_100g', 'Hidratos de carbono', 'g'],
      ['azucares_100g', 'de los cuales azucares', 'g'],
      ['proteinas_100g', 'Proteinas', 'g'],
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

  // **La identidad sale de `miembro`, NO de `producto`.**
  //
  // *El objeto `producto` que devuelve `/api/producto` tiene 13 claves y **ninguna es `ean`**
  // (medido el 18/10/2026).* *Filtrar con `producto.ean` rechazaba **todo**, tambien las
  // coincidencias exactas, y el defecto se disfrazaba de arreglo: la frase incorrecta desaparecia
  // porque desaparecia todo.*
  //
  // *`miembro` es la entrada del grupo que corresponde a este producto -- se busca por `fuente` e
  // `id_fuente` mas arriba --, y **esa si trae `ean`**.* *Si no lo trae, `identidad()` devuelve
  // `'no-verificada'`: no se afirma ni que si ni que no.*
  const conIdentidad = miembro ?? producto

  // *** UN UNICO RESULTADO, Y TODO SALE DE AQUI. ***
  // *La frase y las tarjetas recibian `grupo.cadenas` y `grupo.ahorro_cent`, que son del **grupo
  // entero** -- alternativas incluidas --, aunque los candidatos estuvieran filtrados.* *Si el
  // elegido era el mas barato, se podia anunciar un ahorro y un numero de cadenas que no eran de
  // ese articulo.*
  //
  // *`construyeComparacion` solo cuenta candidatos **exactos** (`'mismo'`) y con **base declarada y
  // coincidente**.* *Las alternativas no entran ni en las cadenas, ni en el minimo, ni en el
  // ahorro.*
  const comp = construyeComparacion(conIdentidad, grupo?.productos ?? [])

  const masBarato = (() => {
    if (!grupo || producto.precio_unidad_cent === null) return null
    const mio = producto.precio_unidad_cent
    if (!Number.isFinite(mio) || mio <= 0) return null
    // *De `comp`, no del grupo: solo exactos y con base declarada.*
    const otros = comp.comparables.filter(
      (p) =>
        p.fuente !== producto.fuente &&
        p.comparable &&
        p.precio_unidad_cent !== null &&
        p.precio_unidad_cent > 0,
    )
    if (!otros.length) return null
    const minimo = Math.min(...otros.map((p) => p.precio_unidad_cent as number))
    if (mio <= minimo) return null
    const otro = otros.find((p) => p.precio_unidad_cent === minimo)
    return { fuente: otro?.fuente ?? '', precio_unidad_cent: minimo, ahorro: mio - minimo }
  })()

  return (
    <div className="flex min-h-full flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Boton variante="sutil" onClick={() => navega(-1)}>
          ← Volver
        </Boton>
        {grupo && (
          <Link
            to={`/grupo/${grupo.grupo_id}`}
            className="inline-flex min-h-[44px] items-center rounded-campo border border-borde px-3 text-cuerpo "
          >
            Ver las {grupo.cadenas} cadenas en columnas
          </Link>
        )}
      </div>

      <header className="flex flex-wrap items-start gap-4">
        {miembro?.imagen && (
          <img
            src={miembro.imagen}
            alt=""
            loading="lazy"
            width={112}
            height={112}
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
            className="h-28 w-28 rounded-campo border border-borde bg-papel object-contain "
          />
        )}
        <div className="min-w-[16rem] flex-1">
          <h2 className="text-xl font-bold leading-tight">{producto.nombre}</h2>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-cuerpo text-secundaria ">
            <Etiqueta tono="info">{nombreCadena(producto.fuente)}</Etiqueta>
            {producto.marca && <span>{producto.marca}</span>}
            <span>{textoCantidad(producto.cantidad, producto.unidad)}</span>
            {consulta.data?.fecha_datos && (
              <Etiqueta tono="dato">datos del {fechaTexto(consulta.data.fecha_datos)}</Etiqueta>
            )}
          </p>

          {/* **Apuntarlo y seguirlo, desde aquí.** A esta pantalla se llega escaneando el
              código de barras, y hasta el 27 de septiembre de 2026 no había forma de apuntar
              nada: había que abrir el grupo («Ver las N cadenas en columnas»), buscarlo y
              añadirlo allí, con el paquete en la mano. El flujo documentado en
              `docs/PANTALLAS.md` §6 dice «+ ficha + añadir» para el caso de «lo conozco y puedo
              comparar», y la pantalla no tenía ese añadir. Se usa el mismo botón que la ficha
              del grupo (`componentes/BotonAnadirACesta.tsx`): dos copias habrían acabado en dos
              comportamientos. */}
          <div className="mt-2 flex flex-wrap items-center gap-2">
          <BotonAnadirACesta key={productoIdExacto} productoId={productoIdExacto} nombre={producto.nombre} />
            <p className="text-cuerpo text-tinta-suave">Añade este artículo de esta cadena, sin sustituirlo por otra marca.</p>
          </div>
          {grupo && (
            <div className="mt-2">
              <Campana grupoId={grupo.grupo_id} />
            </div>
          )}

          {/* **La frase, antes que la tabla.** Punto 3 del encargo: «una tabla no
              es una respuesta». Va aqui arriba, antes del precio y de la tabla de
              cadenas, porque es lo primero que se mira con el paquete en la mano.

              Se calcula aqui mismo y no en un `useMemo` de mas arriba **para que la
              frase y los datos que la forman esten en el mismo sitio**: el dia que
              alguien cambie que es «fiable», tiene que cambiar la frase al lado, no
              a treinta lineas de distancia. Las reglas de la frase estan en
              `logica/frase.ts`, que es donde se deciden.

              Y si no hay frase **no se pinta nada**: la tabla de abajo ya deja
              comparar con desconfianza, y una frase inventada se cree. */}
          {(() => {
            if (!grupo || !miembro) return null
            // Solo cuentan los productos con precio y marcados como comparables
            // por la API: es su señal, no una regla reinventada aqui.
            // **Solo el mismo articulo.** *La frase dice «cuesta un X % mas que en ...», y eso
            // solo es cierto si es **el mismo producto**.* *Con el grupo entero, el azafran Pote
            // de DIA salia «un 41 % mas que en Mercadona» comparado con el **Hacendado**.*
            // *** LAS CIFRAS SALEN DE `comp`, NO DEL GRUPO. ***
            // *Esto recibia `grupo.ahorro_cent` y `grupo.cadenas`, que cuentan las alternativas.*
            // *Ahora solo cuenta lo exacto y comparable: `comp.cadenas`, `comp.diferenciaCent` y
            // `comp.diferenciaPct`.*
            const conPrecio = comp.comparables.filter(
              (p) => p.comparable && p.precio_unidad_cent != null,
            )
            if (conPrecio.length < 2) return null
            // *Sin cifras no hay frase: no se inventa un cero.*
            if (comp.diferenciaPct == null || comp.diferenciaCent == null) return null
            const barato = conPrecio.find((p) => p.precio_unidad_cent === comp.minimo)
            const frase = fraseDePrecio({
              cadenas: comp.cadenas,
              ahorro_pct: comp.diferenciaPct,
              ahorro_cent: comp.diferenciaCent,
              fiable: comp.unidad !== null && comp.cadenas >= 2 && conPrecio.length >= 2,
              cadena_mas_barata: barato?.fuente ?? null,
              cadena_de_este: miembro.fuente,
              precio_unidad_este: miembro.precio_unidad_cent,
              precio_unidad_minimo: comp.minimo,
            }, { euros, nombreCadena })
            if (!frase) return null
            return <p className="mt-3 text-entrada font-semibold leading-snug">{frase}</p>
          })()}

          {/* *** LO QUE NO ES ESTE ARTICULO VA APARTE, Y NO SE RESTA. ***
              *Medido el 18/10/2026 con el azafran `dia/147509`: el grupo traia el **Hacendado** de
              Mercadona (otro EAN, otra marca) y el **mismo Pote** de Carrefour pero **medido por
              unidad** en vez de por kilo.* *Con eso, la ficha decia «Cuesta un 41 % mas que en
              Mercadona», que es comparar Pote con Hacendado.*

              **Aqui no se resta nada y no se sustituye nada**: se enseña que existe, con su nombre
              y su marca, para que quien mire decida. *Un ahorro que no es del articulo elegido es
              una afirmacion falsa, y la pantalla no la hace.* */}
          {(() => {
            if (!grupo) return null
            // *** CUATRO CAJONES, NO DOS. ***
            // *Mismo articulo comparable, mismo articulo con otra base de precio, otro articulo, e
            // identidad sin verificar.* *Antes solo habia «este» y «no este», y ahi se perdian dos
            // cosas: el mismo articulo con otra unidad se llamaba «no es este articulo» (falso), y
            // una identidad desconocida se presentaba como alternativa (afirmar sin dato).*
            const c = comp
            const sinEl = <T extends { fuente?: string }>(xs: T[]) =>
              xs.filter((p) => p.fuente !== producto.fuente)
            const mismaBase = sinEl(c.mismoSinComparar)
            const otras = sinEl(c.distintas)
            const sinVerificar = sinEl(c.sinVerificar)
            if (!mismaBase.length && !otras.length && !sinVerificar.length) return null
            const fila = (p: { fuente: string; nombre: string; marca?: string | null; unidad?: string | null; precio_unidad_cent?: number | null; precio_por_escurrido?: boolean | null }, nota: string) => (
              <li key={`${p.fuente}:${p.nombre}`} className="flex flex-wrap justify-between gap-2">
                <span>
                  {p.nombre}
                  {p.marca ? ` \u00b7 ${p.marca}` : ''}
                  {nota && <span className="text-tinta-suave"> -- {nota}</span>}
                </span>
                <span className="tabular-nums">
                  {p.precio_unidad_cent == null
                    ? 'sin precio'
                    : eurosUnidad(p.precio_unidad_cent, p.unidad ?? null, p.precio_por_escurrido ?? false)}
                </span>
              </li>
            )
            return (
              <section className="mt-4 rounded-lg border border-tinta-suave p-3">
                <h2 className="text-entrada font-semibold">El mismo articulo y otras opciones</h2>
                {mismaBase.length > 0 && (
                  <>
                    <h3 className="mt-2 text-xs font-semibold">Mismo articulo, precio no comparable</h3>
                    <p className="text-xs text-tinta-suave">
                      Es el mismo producto (mismo EAN), pero su precio va en otra base (por unidad de
                      venta en vez de por kilo, o al reves). No se resta.
                    </p>
                    <ul className="mt-1 grid gap-1 text-xs">
                      {mismaBase.map((p) => fila(p, 'mismo articulo, otra base'))}
                    </ul>
                  </>
                )}
                {otras.length > 0 && (
                  <>
                    <h3 className="mt-3 text-xs font-semibold">Otras opciones del grupo</h3>
                    <p className="text-xs text-tinta-suave">
                      No son este articulo: cambian de marca o de formato. Van aparte y no se restan
                      de su precio.
                    </p>
                    <ul className="mt-1 grid gap-1 text-xs">
                      {otras.map((p) => fila(p, ''))}
                    </ul>
                  </>
                )}
                {sinVerificar.length > 0 && (
                  <>
                    <h3 className="mt-3 text-xs font-semibold">Sin identidad verificada</h3>
                    <p className="text-xs text-tinta-suave">
                      No hay EAN con el que confirmar si es el mismo articulo. No se afirma ni que si
                      ni que no, y no se resta.
                    </p>
                    <ul className="mt-1 grid gap-1 text-xs">
                      {sinVerificar.map((p) => fila(p, 'identidad no verificada'))}
                    </ul>
                  </>
                )}
              </section>
            )
          })()}

          <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Dato etiqueta="Precio">{euros(producto.precio_cent)}</Dato>
            <Dato etiqueta="Precio por unidad">
              {eurosUnidad(producto.precio_unidad_cent, producto.unidad,
                           producto.precio_por_escurrido)}
              {producto.precio_por_escurrido && (
                <span className="block text-etiqueta font-normal text-tinta-suave">
                  sobre {textoCantidad((producto.peso_escurrido_g ?? 0) / 1000, 'kg')} escurridos
                </span>
              )}
            </Dato>
            {/* Dónde está más barato y cuánto, en euros por unidad. Va pegado al
                precio por unidad porque es lo que se compara con él. Solo sale cuando
                hay algo que ahorrar (ver `masBarato`). */}
            {masBarato && (
              <Dato etiqueta="Más barato en">
                {nombreCadena(masBarato.fuente)}
                <span className="block text-etiqueta font-normal text-tinta-suave">
                  {eurosUnidad(masBarato.precio_unidad_cent, producto.unidad)} · te ahorras{' '}
                  {eurosUnidad(masBarato.ahorro, producto.unidad)}
                </span>
              </Dato>
            )}
            {/* Al peso, el precio es una estimacion y hay que decirlo antes de
                que se entere en la caja. Son los 711 productos del catalogo que
                traen `peso_variacion_pct` (todos al 25 %), y sin esta linea el
                €/kg parece una promesa cuando es un calculo. */}
            {pesoVariable !== null && (
              <Dato etiqueta="Al peso">
                ronda los {textoCantidad(producto.cantidad, producto.unidad)} y puede variar
                un {numero(pesoVariable)} %
              </Dato>
            )}
            <Dato etiqueta="Nutri-Score">
              <SelloNutriscore valor={producto.nutriscore} />
            </Dato>
            <Dato etiqueta="Código de barras">{miembro?.ean ?? 'no lo sé'}</Dato>
          </dl>

          <div className="mt-2 flex flex-wrap items-center gap-1">
            {miembro && <SelloLetra producto={miembro} />}
            <SelloOferta texto={miembro?.promo ?? null} club={miembro?.promo_club ?? null}
                         unidades={miembro?.promo_unidades ?? null} />
            <SelloRetirada retirado={miembro?.es_recall ?? null} />
            {/* Los sellos con su nombre legible: `sin-gluten` en crudo se lee
                regular, y el dato viene de la API en codigo. */}
            {miembro?.sellos.map((s) => (
              <Etiqueta key={s} tono="dato">
                {selloLegible(s)}
              </Etiqueta>
            ))}
            {/* Y detras, **de donde salen**, que es lo que no se puede
                disimular: un certificado auditado no vale lo mismo que una
                palabra en el nombre del producto, y decir "sin gluten" igual en
                los dos casos seria mentir sin decir ninguna mentira. */}
            {origenDeSellos && (
              <span className="text-etiqueta text-tinta-suave">
                ({origenDeSellos})
              </span>
            )}
            {/* Los certificados van aparte y en verde, porque son la prueba
                fuerte: no los dice el nombre, los audita un tercero. */}
            {miembro?.certificados.map((c) => (
              <Etiqueta key={c} tono="bien" titulo="Certificado: lo audita un tercero, no lo dice el nombre">
                {selloLegible(c)}
              </Etiqueta>
            ))}
            {/* Y esto lo dice la cadena, no nosotros. Ponerlo como si fuera
                nuestro seria vender su marketing como dato. */}
            {miembro?.distintivo && (
              <Etiqueta tono="neutro" titulo="Es lo que dice la cadena, no lo que decimos nosotros">
                la cadena dice: {selloLegible(miembro.distintivo)}
              </Etiqueta>
            )}
          </div>
        </div>
      </header>

      {!grupo && (
        <Aviso tono="aviso" titulo="Este producto no tiene grupo">
          <p>
            Es uno de los que el emparejador deja sueltos: no hay con qué compararlo, así que no
            hay alternativas ni histórico de grupo que enseñar. Sigue saliendo en el buscador,
            marcado, porque esconderlo sería esconder casi dos tercios del catálogo.
          </p>
        </Aviso>
      )}

      {grupo && (
        <>
          <Tarjeta
            titulo="El histórico de este precio"
            sub={`Precio por unidad de ${nombreCadena(fuente)}${grupo.unidad ? ` · €/${grupo.unidad}` : ''}`}
          >
            {historico.bloqueado ? (
              <Aviso tono="aviso" titulo="No pinto la línea, y lo explico">
                <p>
                  Esta cadena tiene {historico.filas} productos dentro del mismo grupo, y la serie
                  que devuelve <code>/api/grupo</code> va por cadena y fecha sin decir de cuál es
                  cada punto. Dibujarla mezclaría dos productos y parecería un histórico que no
                  existe.
                </p>
              </Aviso>
            ) : historico.puntos.length === 0 ? (
              <Vacio titulo="Sin histórico" className="grow">
                <p>Solo tenemos un día de este precio.</p>
              </Vacio>
            ) : (
              <>
                <Chispa puntos={historico.puntos} alto={120} etiqueta={`Histórico de ${producto.nombre}`} />
                {/* **La frase debajo de la curva.** Punto 3 del encargo, apartado 3:
                    *"la curva, que ya existe, con una frase debajo"*. Una linea que
                    sube y baja sin decir nada es un adorno del dato -- lo dice el
                    propio `Chispa.tsx` --, y lo que se viene a saber es si **hoy** esta
                    caro o barato. Las reglas (y sobre todo cuando NO hay frase) estan
                    en `logica/curva.ts`. */}
                {curva.frase && (
                  <p className="mt-2 text-entrada font-semibold leading-snug">{curva.frase}</p>
                )}
                {curva.motivo && (
                  <p className="mt-2 text-cuerpo text-tinta-suave">{curva.motivo}</p>
                )}
                <dl className="mt-3 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                  <Dato etiqueta="Mínimo">{eurosUnidad(resumen.min, grupo.unidad)}</Dato>
                  <Dato etiqueta="Máximo">{eurosUnidad(resumen.max, grupo.unidad)}</Dato>
                  <Dato etiqueta="Media">{eurosUnidad(resumen.media, grupo.unidad)}</Dato>
                  <Dato etiqueta="Primer dato">{eurosUnidad(resumen.primero, grupo.unidad)}</Dato>
                  <Dato etiqueta="Último dato">{eurosUnidad(resumen.ultimo, grupo.unidad)}</Dato>
                  <Dato etiqueta="Evolución">{porcentajeConSigno(evolucion)}</Dato>
                </dl>
                <p className="mt-2 text-etiqueta text-tinta-suave">
                  {resumen.n} {resumen.n === 1 ? 'día' : 'días'} de histórico, del{' '}
                  {fechaTexto(historico.puntos[0]?.fecha ?? null)} al{' '}
                  {fechaTexto(historico.puntos[historico.puntos.length - 1]?.fecha ?? null)}. La
                  media es la de los días que tenemos, no la de todo el año.
                </p>
              </>
            )}
          </Tarjeta>

          <Tarjeta
            titulo="Su grupo de equivalencias"
            sub={`${grupo.productos.length} productos en ${grupo.cadenas} ${grupo.cadenas === 1 ? 'cadena' : 'cadenas'} · datos del ${fechaTexto(grupo.fecha_datos ?? consulta.data?.fecha_datos ?? null)}`}
          >
            <TablaScroll etiqueta="Productos equivalentes" minAncho="44rem">
              <table className="w-full border-collapse text-cuerpo">
                <thead>
                  <tr>
                    <Th>Producto</Th>
                    <Th>Cadena</Th>
                    <Th>Precio</Th>
                    <Th>Por unidad</Th>
                    <Th>Diferencia</Th>
                    <Th>Letra</Th>
                  </tr>
                </thead>
                <tbody>
                  {grupo.productos.map((p) => {
                    // La referencia de la diferencia es **el mas barato de SU unidad**,
                    // no el minimo del grupo. El minimo del grupo puede estar medido en
                    // otra unidad, y entonces «+162.943,5 %» es un numero que no
                    // significa nada: medido en un navegador el 23 de septiembre de 2026
                    // en la ficha de un azafran de 0,4 g, comparando 4.875,00 EUR/kg con
                    // 2,99 EUR/ud. La API ya calcula su `ahorro_pct` asi (`catalogo.py`),
                    // y la nota de abajo dice exactamente eso: que los productos de otra
                    // unidad no entran en la cuenta. Ahora la columna lo cumple.
                    // *** LA DIFERENCIA SOLO SE CALCULA DONDE HAY IDENTIDAD Y BASE. ***
                    //
                    // *Esto filtraba por `comparable` y por **misma unidad**, pero **no por
                    // EAN**.* *Asi que en la ficha del azafran la fila de DIA (kg) se comparaba
                    // con el **Hacendado** (kg, otro articulo) y salia «diferencia +41 %»: el
                    // mismo defecto que ya se habia corregido en la frase y en el apartado,
                    // vivo en la tercera superficie.*
                    //
                    // *Ahora: **mismo articulo** (`identidad`) **y** precio comparable (`misma
                    // unidad` y misma convencion de peso).* *Si no, la celda lo dice en vez de
                    // inventar un porcentaje.*
                    const esEste = identidad(conIdentidad, p) === 'mismo'
                    const comparableConEste = esEste && precioComparable(conIdentidad, p)
                    const referencia = comparableConEste ? comp.minimo : null
                    const dif =
                      referencia !== null &&
                      referencia > 0 &&
                      p.precio_unidad_cent !== null &&
                      Number.isFinite(p.precio_unidad_cent) &&
                      p.precio_unidad_cent > 0
                        ? Math.round(
                            ((100 * (p.precio_unidad_cent - referencia)) / referencia) * 10,
                          ) / 10
                        : null
                    return (
                      <tr key={p.producto_id} className="hover:bg-marfil">
                        <Td>
                          {/* **44 px de alto, medido.** El 23 de septiembre de 2026 este
                              enlace medía 161 x **19**: es la forma de saltar a la ficha de
                              otro producto del grupo, que es justo lo que se hace con el
                              paquete en la mano, y de pie no se acierta. La marca va dentro
                              del mismo enlace para que el objetivo sea el nombre entero. */}
                          <Link to={`/producto/${p.fuente}/${p.id_fuente}`}
                                className="inline-flex min-h-[44px] min-w-[44px] items-center underline">
                            {p.nombre}
                          </Link>
                          {p.marca && (
                            <span className="block text-etiqueta text-tinta-suave">
                              {p.marca}
                            </span>
                          )}
                        </Td>
                        <Td etiqueta="cadena">{nombreCadena(p.fuente)}</Td>
                        <Td className="cifra" etiqueta="precio">{euros(p.precio_cent)}</Td>
                        <Td className="cifra" etiqueta="por unidad">
                          {eurosUnidad(p.precio_unidad_cent, p.unidad)}
                        </Td>
                        <Td className="cifra" etiqueta="diferencia">
                          {esEste && !comparableConEste
                                ? 'mismo articulo, otra base'
                                : !esEste
                                  ? 'otro articulo'
                                  : dif === null
                                    ? 'no lo sé'
                                    : dif <= 0
                                      ? 'el más barato'
                                      : `+${porcentaje(dif)}`}
                        </Td>
                        <Td etiqueta="letra">
                          <SelloLetra producto={p} />
                        </Td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </TablaScroll>
            {comp.cadenas >= 2 && comp.unidad !== null && (
              <p className="mt-2 text-cuerpo text-secundaria ">
                {/* *** SON ARTICULOS DISTINTOS, Y HAY QUE DECIRLO. ***
                    *Esta frase decia solo «de la mas barata a la mas cara hay 41 % por unidad
                    (2000,00 EUR)», y hablaba de la **unidad** pero no del **articulo**.* *En el
                    azafran `dia/147509` compara el Pote de DIA con el **Hacendado** de Mercadona:
                    **otro artículo**.* *Leido de corrido parece el ahorro del que tienes en la
                    mano, y no lo es.*

                    **El dato se queda** -- *la horquilla del grupo existe y es verdad* --, *pero se
                    dice de que es: de articulos distintos.* */}
                {/* *** LA MAGNITUD TAMBIEN LLEVA UNIDAD. ***
                    *Decia «2000,00 EUR» cuando la diferencia es **2000 EUR/kg**.* *Sin la unidad,
                    el numero se lee como un ahorro de dinero en la compra, y no lo es: es la
                    horquilla de precios **por unidad** entre articulos distintos del grupo.* */}
                De la mas barata a la mas cara <strong>de este mismo articulo</strong> hay{" "}
                {porcentaje(comp.diferenciaPct)} de diferencia por {comp.unidad ?? 'unidad'} (
                {euros(comp.diferenciaCent)} por {comp.unidad ?? 'unidad'}).{" "}
                {comp.ahorroEnvaseCent != null && (
                  <>
                    Lo que te ahorras en el envase son{" "}
                    <strong>{euros(comp.ahorroEnvaseCent)}</strong>.{" "}
                  </>
                )}
                <span className="text-tinta-suave">
                  Las alternativas -- otro EAN -- no entran en esta cuenta.
                </span>
              </p>
            )}
          </Tarjeta>

          <Tarjeta titulo="Por qué está emparejado con esos">
            <ExplicacionEmparejamiento grupo={grupo} />
          </Tarjeta>
        </>
      )}

      {miembro && (
        <Tarjeta titulo="Ficha del producto en la cadena">
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Dato etiqueta="Tipo">{miembro.tipo_producto ?? 'no lo sé'}</Dato>
            <Dato etiqueta="Envase">{miembro.envase ?? 'no lo sé'}</Dato>
            <Dato etiqueta="Conservación">{miembro.conservacion ?? 'no lo sé'}</Dato>
            <Dato etiqueta="Origen">{miembro.origen ?? 'no lo sé'}</Dato>
            <Dato etiqueta="NOVA">{miembro.nova ?? 'no lo sé'}</Dato>
            <Dato etiqueta="Días de caducidad">{miembro.dias_caducidad ?? 'no lo sé'}</Dato>
            <Dato etiqueta="Peso neto">
              {miembro.peso_neto_g === null ? 'no lo sé' : `${miembro.peso_neto_g} g`}
            </Dato>
            <Dato etiqueta="Graduación">
              {miembro.grado_alcohol === null ? 'sin alcohol' : `${miembro.grado_alcohol} %`}
            </Dato>
            <Dato etiqueta="Marca propia">{miembro.es_marca_propia ? 'sí' : 'no'}</Dato>
          </dl>

          {miembro.alergenos && (
            // Los alérgenos van en rojo y los primeros: es lo único de esta
            // pantalla que puede hacer daño a alguien.
            <p className="mt-3 rounded-campo border border-error bg-marfil px-3 py-2 text-cuerpo text-error ">
              <strong>Alérgenos:</strong> {miembro.alergenos}
            </p>
          )}

          {miembro.ingredientes && (
            <details className="mt-3">
              {/* **44 px, aunque sea una palabra.** Medido en un móvil de 390 x 844 el 23 de
                  septiembre de 2026: este `<summary>` medía 324 x **20**. Es un objetivo de
                  verdad (abre los ingredientes, que es donde se mira si algo lleva lo que no
                  se puede comer) y a 20 px no se acierta de pie con el carro en la otra mano.
                  Es la misma regla que la puerta comprueba ya pintada en las demás
                  pantallas. */}
              <Resumen className="text-cuerpo font-medium">
                Ingredientes
              </Resumen>
              <p className="mt-1 text-cuerpo">{miembro.ingredientes}</p>
            </details>
          )}

          {miembro.descripcion && (
            <p className="mt-3 text-cuerpo text-secundaria ">
              {miembro.descripcion}
            </p>
          )}

          {/* **Cuando la cadena no publica nutricion, la de Open Food Facts.** Cuatro de las
              cinco cadenas no publican ninguna: solo DIA. Y 10.778 productos si tienen los valores
              por 100 g de OFF, asi que sin esto la ficha de un producto de Carrefour, Mercadona,
              Alcampo o Aldi no ensena nada nutricional. Misma forma que el bloque de al lado, misma
              base dicha, mismo NO_LO_SE: es la misma informacion de otra fuente, no otra cosa. */}
          {!miembro.nutricion && filasOff.length > 0 && (
            <div className="mt-3">
              <h3 className="text-cuerpo font-semibold">Nutrición (por 100 g)</h3>
              <ul className="mt-1 grid gap-1 text-cuerpo sm:grid-cols-2">
                {filasOff.map((f) => (
                  <li key={f.clave} className="flex justify-between gap-2 border-b border-borde py-0.5 ">
                    <span className="text-secundaria ">{f.texto}</span>
                    <span className="cifra font-medium">
                      {f.valor === null ? NO_LO_SE : `${NUMERO.format(f.valor)} ${f.unidad}`}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-[11px] text-secundaria ">
                Datos de Open Food Facts. Pueden faltar o ser aproximados.
              </p>
            </div>
          )}

          {miembro.nutricion && (
            <div className="mt-3">
              <h3 className="text-cuerpo font-semibold">
                Nutrición {miembro.nutricion_por ? `(por ${miembro.nutricion_por})` : ''}
              </h3>
              <ul className="mt-1 grid gap-1 text-cuerpo sm:grid-cols-2">
                {filasNutricion(miembro.nutricion).map((f) => (
                  <li key={f.clave} className="flex justify-between gap-2 border-b border-borde py-0.5 ">
                    <span className="text-secundaria ">{f.texto}</span>
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

          {miembro.url && (
            <p className="mt-3">
              <a
                href={miembro.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cuerpo underline"
              >
                Ver en {nombreCadena(miembro.fuente)}
              </a>
            </p>
          )}
        </Tarjeta>
      )}
    </div>
  )
}