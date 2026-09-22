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
import { Chispa, type PuntoChispa } from '../componentes/Chispa'
import { SelloLetra, SelloNutriscore, SelloOferta, SelloRetirada } from '../componentes/Etiquetas'
import { ExplicacionEmparejamiento } from '../componentes/ExplicacionEmparejamiento'
import { Aviso, Boton, Cargando, Dato, Etiqueta, Fallo, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

export function Producto() {
  const { fuente = '', idFuente = '' } = useParams<{ fuente: string; idFuente: string }>()
  const navega = useNavigate()
  const consulta = useProducto(fuente, idFuente)

  const producto = consulta.data?.producto
  const grupo = consulta.data?.grupo ?? null

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
    if (!grupo) return { puntos: [] as PuntoChispa[], bloqueado: false, filas: 0 }
    const deLaCadena = grupo.serie.filter((s) => s.fuente === fuente)
    // Cuantos productos de ESTA cadena hay en el grupo: la serie no los separa.
    const cuantos = grupo.productos.filter((p) => p.fuente === fuente).length
    const puntos = deLaCadena
      .map<PuntoChispa>((s) => ({ fecha: s.fecha, valor: s.precio_unidad_cent }))
      .sort((a, b) => ms(a.fecha) - ms(b.fecha))
    return { puntos, bloqueado: cuantos > 1, filas: cuantos }
  }, [grupo, fuente])

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

  /** La referencia de las diferencias: el precio por unidad más bajo del grupo.
   *  `null` si no hay ninguno, para no acabar comparando contra un cero. */
  const baratoDelGrupo = (() => {
    const valores = (grupo?.productos ?? [])
      .map((p) => p.precio_unidad_cent)
      .filter((c): c is number => c !== null && Number.isFinite(c) && c > 0)
    return valores.length > 0 ? Math.min(...valores) : null
  })()

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Boton variante="sutil" onClick={() => navega(-1)}>
          ← Volver
        </Boton>
        {grupo && (
          <Link
            to={`/grupo/${grupo.grupo_id}`}
            className="inline-flex min-h-[44px] items-center rounded-lg border border-neutral-300 px-3 text-sm dark:border-neutral-600"
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
            className="h-28 w-28 rounded-lg border border-neutral-200 bg-white object-contain dark:border-neutral-700"
          />
        )}
        <div className="min-w-[16rem] flex-1">
          <h1 className="text-xl font-bold leading-tight">{producto.nombre}</h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
            <Etiqueta tono="info">{nombreCadena(producto.fuente)}</Etiqueta>
            {producto.marca && <span>{producto.marca}</span>}
            <span>{textoCantidad(producto.cantidad, producto.unidad)}</span>
            {consulta.data?.fecha_datos && (
              <Etiqueta tono="dato">datos del {fechaTexto(consulta.data.fecha_datos)}</Etiqueta>
            )}
          </p>

          <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Dato etiqueta="Precio">{euros(producto.precio_cent)}</Dato>
            <Dato etiqueta="Precio por unidad">
              {eurosUnidad(producto.precio_unidad_cent, producto.unidad)}
            </Dato>
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
            <SelloOferta texto={miembro?.promo ?? null} club={miembro?.promo_club ?? null} />
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
              <span className="text-xs text-tinta-suave">
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
              <Vacio titulo="Sin histórico">
                <p>Solo tenemos un día de este precio.</p>
              </Vacio>
            ) : (
              <>
                <Chispa puntos={historico.puntos} alto={120} etiqueta={`Histórico de ${producto.nombre}`} />
                <dl className="mt-3 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                  <Dato etiqueta="Mínimo">{eurosUnidad(resumen.min, grupo.unidad)}</Dato>
                  <Dato etiqueta="Máximo">{eurosUnidad(resumen.max, grupo.unidad)}</Dato>
                  <Dato etiqueta="Media">{eurosUnidad(resumen.media, grupo.unidad)}</Dato>
                  <Dato etiqueta="Primer dato">{eurosUnidad(resumen.primero, grupo.unidad)}</Dato>
                  <Dato etiqueta="Último dato">{eurosUnidad(resumen.ultimo, grupo.unidad)}</Dato>
                  <Dato etiqueta="Evolución">{porcentajeConSigno(evolucion)}</Dato>
                </dl>
                <p className="mt-2 text-xs text-tinta-suave">
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
              <table className="w-full border-collapse text-sm">
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
                    const dif =
                      baratoDelGrupo !== null &&
                      p.precio_unidad_cent !== null &&
                      p.precio_unidad_cent > 0
                        ? Math.round(
                            (100 * (p.precio_unidad_cent - baratoDelGrupo)) / baratoDelGrupo * 10,
                          ) / 10
                        : null
                    return (
                      <tr key={p.producto_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/60">
                        <Td>
                          <Link to={`/producto/${p.fuente}/${p.id_fuente}`} className="underline">
                            {p.nombre}
                          </Link>
                          {p.marca && (
                            <span className="block text-xs text-tinta-suave">
                              {p.marca}
                            </span>
                          )}
                        </Td>
                        <Td>{p.fuente}</Td>
                        <Td className="cifra">{euros(p.precio_cent)}</Td>
                        <Td className="cifra">{eurosUnidad(p.precio_unidad_cent, p.unidad)}</Td>
                        <Td className="cifra">
                          {dif === null ? 'no lo sé' : dif <= 0 ? 'el más barato' : `+${porcentaje(dif)}`}
                        </Td>
                        <Td>
                          <SelloLetra producto={p} />
                        </Td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </TablaScroll>
            {grupo.cadenas >= 2 && (
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                De la más barata a la más cara hay {porcentaje(grupo.ahorro_pct)} por unidad (
                {euros(grupo.ahorro_cent)}). Son precios de una unidad comparable; los productos de
                otra unidad no entran en esa cuenta.
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
            <p className="mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-950 dark:border-red-800 dark:bg-red-950 dark:text-red-100">
              <strong>Alérgenos:</strong> {miembro.alergenos}
            </p>
          )}

          {miembro.ingredientes && (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-medium">Ingredientes</summary>
              <p className="mt-1 text-sm">{miembro.ingredientes}</p>
            </details>
          )}

          {miembro.descripcion && (
            <p className="mt-3 text-sm text-neutral-700 dark:text-neutral-300">
              {miembro.descripcion}
            </p>
          )}

          {miembro.nutricion && (
            <div className="mt-3">
              <h3 className="text-sm font-semibold">
                Nutrición {miembro.nutricion_por ? `(por ${miembro.nutricion_por})` : ''}
              </h3>
              <ul className="mt-1 grid gap-1 text-sm sm:grid-cols-2">
                {filasNutricion(miembro.nutricion).map((f) => (
                  <li key={f.clave} className="flex justify-between gap-2 border-b border-neutral-100 py-0.5 dark:border-neutral-700">
                    <span className="text-neutral-600 dark:text-neutral-400">{f.texto}</span>
                    <span className="cifra font-medium">
                      {f.valor === null
                        ? NO_LO_SE
                        : `${f.valor}${f.unidad ? ` ${f.unidad}` : ''}`}
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
                className="text-sm underline"
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
