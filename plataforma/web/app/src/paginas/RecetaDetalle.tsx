/** El detalle de una receta: **lo que lleva, lo que cuesta y cómo se hace**.
 *
 *  La composicion es la del artboard aprobado (`designs/cesta-app/project/Receta.dc.html`):
 *  volver, el nombre y las raciones, el coste sobre bosque, los ingredientes con su coste, los
 *  pasos y las acciones. Los valores -- marfil, papel, bosque, lima, tipos, radios y movimiento --
 *  son los del sistema «Cesta App».
 *
 *  ===================== EL COSTE, Y POR QUE NO HAY UN TOTAL FALSO =====================
 *
 *  **El coste solo se enseña si sale de precios que la API trae de verdad.** Cada ingrediente
 *  puede traer el precio de su envase (`precio_cent`), el precio por la unidad canonica
 *  (`precio_unidad_cent`, en €/kg, €/l o €/ud), el tamaño del envase (`tamano_envase` y
 *  `unidad_envase`) y la cadena del producto elegido (el prefijo de `producto_id`). Con eso:
 *
 *  - **Se convierte la unidad**: 200 g de un envase de 1 kg a 1,20 € son 0,24 €, no 240 €.
 *    *La cuenta se hace aqui y no en `costeReceta.ts` porque ese modulo no conoce las unidades;
 *    darle 120 céntimos por kilo como si fueran por gramo fue el defecto que se vio al montar
 *    esta pantalla.*
 *  - **Sin precio no hay cero.** El ingrediente dice «sin coste», y el total dice lo que falta.
 *  - **Un total incompleto se llama parcial**, dice cuántos ingredientes faltan y de qué cadena
 *    salen los precios que sí hay. *Un 3,82 € sobre cuatro de cinco ingredientes no es «el coste
 *    de la receta»: es el coste de cuatro.*
 *  - **Sin ningún precio no se pinta un número**: se dice «Coste no disponible».
 *
 *  El caso medido el 5/11/2026 es que casi ninguna receta es costeable (0/242 con coste
 *  completo); por eso el estado honesto no es un detalle, es **el caso normal**.
 *
 *  Lo que no se pierde de la version anterior: el 404 que no es un fallo, la puerta de sesion,
 *  las raciones escaladas con sus dos cifras, el selector de version, la previa de la compra
 *  antes de pasar a la lista y el formulario de edicion.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { esErrorApi, pide, textoDeError } from '../api/cliente'
import { misListas, yo } from '../api/cesta'
import { useClaveDeCuenta } from '../api/cuenta'
import { cantidad as textoCantidad, euros, nombreCadena } from '../api/formato'
import { usePasarALista, usePreviaDeCompra, useReceta } from '../api/recetas'
import type { Ingrediente } from '../api/recetas'
import { FormularioReceta } from '../componentes/FormularioReceta'
import { EntraParaVer } from '../componentes/PuertaDeSesion'
import { useTitulo } from '../componentes/Titulo'
import {
  Aviso, Boton, Cargando, Fallo, Tarjeta, Vacio,
} from '../componentes/ui'
import {
  costeDeReceta,
  type CosteDeReceta,
  type PrecioDeIngrediente,
} from '../logica/costeReceta'

/* ======================================================= el coste con unidades === */

/** Lo que la API añade a un ingrediente cuando tiene un producto elegido. */
export type IngredienteDeLaApi = Ingrediente & {
  precio_cent?: number | null
  precio_unidad_cent?: number | null
  unidad_canon?: string | null
  tamano_envase?: number | null
  unidad_envase?: string | null
}

const MULTIPLO_DE_LA_UNIDAD: Record<string, number> = {
  g: 1,
  kg: 1000,
  ml: 1,
  l: 1000,
  ud: 1,
  uds: 1,
  unidad: 1,
  unidades: 1,
}

function baseDeLaUnidad(unidad: string | null | undefined): 'peso' | 'volumen' | 'unidad' | null {
  const u = (unidad ?? '').trim().toLowerCase()
  if (u === 'g' || u === 'kg') return 'peso'
  if (u === 'ml' || u === 'l') return 'volumen'
  if (u in MULTIPLO_DE_LA_UNIDAD) return 'unidad'
  return null
}

function multiploDeLaUnidad(unidad: string | null | undefined): number | null {
  return MULTIPLO_DE_LA_UNIDAD[(unidad ?? '').trim().toLowerCase()] ?? null
}

/** Los precios que trae la API, **en las unidades de la receta**.
 *
 *  `null` cuando no hay ningún precio: no se rellena con un cero ni se busca por nombre.
 *  La conversión se hace aquí porque `costeReceta.ts` trabaja con la unidad del ingrediente y
 *  no con la unidad canonica del catalogo.
 */
export function precioParaElCoste(i: IngredienteDeLaApi): PrecioDeIngrediente | null {
  const envase = i.precio_cent
  const porUnidad = i.precio_unidad_cent
  const hayEnvase = typeof envase === 'number' && Number.isFinite(envase) && envase > 0
  const hayPorUnidad = typeof porUnidad === 'number' && Number.isFinite(porUnidad) && porUnidad > 0
  if (!hayEnvase && !hayPorUnidad) return null

  const baseReceta = baseDeLaUnidad(i.unidad)
  const multiploReceta = multiploDeLaUnidad(i.unidad)
  const precio: PrecioDeIngrediente = {}

  if (hayEnvase) precio.precioEnvaseCent = envase ?? null

  const tamano = i.tamano_envase
  const multiploEnvase = multiploDeLaUnidad(i.unidad_envase)
  if (
    baseReceta !== null &&
    multiploReceta !== null &&
    tamano != null &&
    Number.isFinite(tamano) &&
    tamano > 0 &&
    multiploEnvase !== null &&
    baseDeLaUnidad(i.unidad_envase) === baseReceta
  ) {
    // *Un envase de 1 kg son 1000 g para una receta en gramos; y al reves, 500 g son 0,5 kg.*
    precio.cantidadEnvase = (tamano * multiploEnvase) / multiploReceta
    precio.unidadEnvase = i.unidad ?? i.unidad_envase ?? null
  }

  if (hayPorUnidad) {
    const multiploCanon = multiploDeLaUnidad(i.unidad_canon)
    if (
      baseReceta !== null &&
      baseDeLaUnidad(i.unidad_canon) === baseReceta &&
      multiploCanon !== null &&
      multiploReceta !== null
    ) {
      // *120 céntimos por kilo son 0,12 céntimos por gramo; no 120 por gramo.*
      precio.precioUnidadCent = (porUnidad * multiploReceta) / multiploCanon
    }
  }

  if (precio.precioEnvaseCent == null && precio.precioUnidadCent == null) return null
  return precio
}

export interface CosteVisible {
  coste: CosteDeReceta
  usadoCent: number | null
  envasesCent: number | null
  /** Ingredientes de los que no se sabe lo que cuesta la cantidad usada. */
  sinUso: string[]
  /** Ingredientes sin ningún precio. */
  sinPrecio: string[]
  /** Ingredientes que no dicen cuánto llevan. */
  sinCantidad: string[]
  /** Tienen precio y cantidad, pero no se puede repartir el precio (falta el tamaño). */
  sinMedida: string[]
  /** Cadenas de los productos que pusieron precio, ya con su nombre legible. */
  cadenas: string[]
  /** `true` solo si **todos** los ingredientes tienen coste de lo usado. */
  completo: boolean
}

/** El coste de la receta, con su cobertura. **El total no se declara completo si falta uno.** */
export function costeDeLaReceta(ingredientes: IngredienteDeLaApi[]): CosteVisible {
  const conPrecio = ingredientes.map((i) => ({
    nombre: i.texto,
    cantidad: typeof i.cantidad === 'number' ? i.cantidad : 0,
    unidad: i.unidad ?? '',
    precio: precioParaElCoste(i),
  }))
  const coste = costeDeReceta(conPrecio)
  const sinUso = coste.ingredientes
    .filter((f) => f.costeUsadoCent === null)
    .map((f) => f.nombre)
  const sinPrecio = ingredientes
    .filter((i) => precioParaElCoste(i) === null)
    .map((i) => i.texto)
  const sinCantidad = ingredientes
    .filter((i) => !(typeof i.cantidad === 'number' && i.cantidad > 0))
    .map((i) => i.texto)
  const sinMedida = sinUso.filter(
    (nombre) => !sinPrecio.includes(nombre) && !sinCantidad.includes(nombre),
  )
  const cadenas = [...new Set(
    ingredientes
      .filter((i) => precioParaElCoste(i) !== null)
      .map((i) => (i.producto_id ?? '').split(':')[0]?.trim() ?? '')
      .filter(Boolean)
      .map((cadena) => nombreCadena(cadena)),
  )]

  return {
    coste,
    usadoCent: coste.usadoCent,
    envasesCent: coste.envasesCent,
    sinUso,
    sinPrecio,
    sinCantidad,
    sinMedida,
    cadenas,
    completo: ingredientes.length > 0 && sinUso.length === 0,
  }
}

/** «Mercadona», «Mercadona y DIA», «Mercadona, DIA y Lidl». */
export function enEspanol(items: string[]): string {
  if (items.length === 0) return ''
  if (items.length === 1) return items[0]
  return `${items.slice(0, -1).join(', ')} y ${items[items.length - 1]}`
}

/** Lo que falta, dicho por su nombre. *No un «faltan datos» que no dice qué datos.* */
export function avisosDeCobertura(c: CosteVisible): string[] {
  const avisos: string[] = []
  if (c.sinPrecio.length > 0) {
    // *** Con muchos nombres, un contador y una pista; no un muro de seis productos. *** *
    // *Medido en una receta real: seis nombres seguidos en una frase dentro de la tarjeta de
    // coste. Los nombres ya estan abajo, cada uno con su «sin coste».*
    avisos.push(
      c.sinPrecio.length === 1
        ? `Falta el precio de ${c.sinPrecio[0]}.`
        : c.sinPrecio.length <= 3
          ? `Faltan precios de ${enEspanol(c.sinPrecio)}.`
          : `Faltan precios de ${c.sinPrecio.length} ingredientes: los marcados como «sin coste» aquí abajo.`,
    )
  }
  if (c.sinCantidad.length > 0) {
    avisos.push(
      c.sinCantidad.length === 1
        ? `${c.sinCantidad[0]} no dice cuánto lleva.`
        : `No dicen cuánto llevan: ${enEspanol(c.sinCantidad)}.`,
    )
  }
  if (c.sinMedida.length > 0) {
    avisos.push(
      c.sinMedida.length === 1
        ? `No se sabe cuánto cuesta la cantidad usada de ${c.sinMedida[0]}.`
        : `No se sabe cuánto cuesta la cantidad usada de ${enEspanol(c.sinMedida)}.`,
    )
  }
  return avisos
}

/** Los pasos, uno por linea. **Los numeros que ya trajera el texto se quitan** para no
 *  enseñar «1. 1. Pela…» al pintarlos como lista numerada. */
export function pasosDePreparacion(preparacion: string): string[] {
  return preparacion
    .split('\n')
    .map((linea) => linea.replace(/^\s*\d+[.)]\s*/, '').trim())
    .filter((linea) => linea.length > 0)
}

/* ================================================================== el coste === */

function CosteDeLaReceta({ ingredientes, raciones }: {
  ingredientes: IngredienteDeLaApi[]
  raciones: number
}) {
  const c = costeDeLaReceta(ingredientes)
  const porRacion = c.usadoCent !== null && raciones > 0
    ? Math.round(c.usadoCent / raciones)
    : null
  const avisos = avisosDeCobertura(c)

  return (
    <section
      aria-labelledby="coste-ingredientes"
      className="rounded-tarjeta bg-bosque p-4 text-sobre-bosque shadow-alzado"
    >
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="coste-ingredientes" className="text-micro uppercase">
          Coste de ingredientes
        </h2>
        {/* *El tiempo no es coste: ya esta en la cabecera («RECETA · 4 RACIONES · 40 MIN») y aqui
            ponia «40 min» al lado de un precio, que se lee como si fuera parte de la cuenta.* */}
      </div>

      {c.usadoCent !== null ? (
        <>
          <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className="cifra text-precio-grande font-semibold">{euros(c.usadoCent)}</p>
            {porRacion !== null && (
              <p className="cifra text-etiqueta">{euros(porRacion)} / ración</p>
            )}
            {!c.completo && (
              <span className="inline-flex min-h-6 items-center rounded-pastilla bg-lima px-2 text-etiqueta-fuerte text-sobre-lima">
                Parcial
              </span>
            )}
          </div>

          {c.cadenas.length > 0 && (
            <p className="mt-1 break-words text-etiqueta">Precios de {enEspanol(c.cadenas)}</p>
          )}

          {!c.completo && (
            <div className="mt-2 flex flex-col gap-0.5 text-etiqueta">
              {avisos.map((aviso, posicion) => (
                <p key={`${posicion}-${aviso}`}>{aviso}</p>
              ))}
              <p>El total es solo de lo que se sabe.</p>
            </div>
          )}
        </>
      ) : (
        <>
          <p className="mt-2 font-display text-precio font-semibold">Coste no disponible</p>
          {ingredientes.length === 0 ? (
            <p className="mt-1 text-etiqueta">No hay ingredientes que costear.</p>
          ) : (
            <div className="mt-1 flex flex-col gap-0.5 text-etiqueta">
              {avisos.map((aviso, posicion) => (
                <p key={`${posicion}-${aviso}`}>{aviso}</p>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}

/* ============================================================ los ingredientes === */

function Ingredientes({ ingredientes, coste }: {
  ingredientes: IngredienteDeLaApi[]
  coste: CosteVisible
}) {
  if (ingredientes.length === 0) {
    return (
      <section aria-labelledby="ingredientes" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
        <h2 id="ingredientes" className="text-cuerpo-fuerte text-tinta">Ingredientes</h2>
        <p className="mt-2 text-cuerpo text-tinta-suave">Sin ingredientes apuntados.</p>
      </section>
    )
  }

  return (
    <section aria-labelledby="ingredientes" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
      <h2 id="ingredientes" className="text-cuerpo-fuerte text-tinta">Ingredientes</h2>

      <ul className="mt-1">
        {ingredientes.map((i, posicion) => {
          const fila = coste.coste.ingredientes[posicion]
          const cuanta = typeof i.cantidad === 'number' && i.cantidad > 0
            ? textoCantidad(i.cantidad, i.unidad)
            : 'sin cantidad'
          return (
            <li
              key={`${i.texto}-${posicion}`}
              className="flex min-h-[44px] items-baseline justify-between gap-3 border-t border-borde py-2 first:border-t-0"
            >
              <span className="min-w-0 break-words text-cuerpo text-tinta">
                {i.texto}{' '}
                <span className="text-etiqueta text-tinta-tenue">{cuanta}</span>
              </span>
              <span className="shrink-0 text-right">
                {fila.costeUsadoCent !== null ? (
                  <span className="cifra text-cuerpo font-medium text-tinta">
                    {euros(fila.costeUsadoCent)}
                  </span>
                ) : (
                  <span className="text-etiqueta text-tinta-tenue">sin coste</span>
                )}
              </span>
            </li>
          )
        })}
      </ul>

      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2 border-t border-borde-fuerte pt-2">
        <span className="text-cuerpo-fuerte text-tinta">
          {coste.usadoCent === null || coste.completo ? 'Total' : 'Total parcial'}
        </span>
        {coste.usadoCent !== null ? (
          <span className="cifra text-precio font-semibold text-tinta">
            {euros(coste.usadoCent)}
          </span>
        ) : (
          <span className="text-etiqueta text-tinta-tenue">No disponible</span>
        )}
      </div>

      {coste.envasesCent !== null && coste.envasesCent !== coste.usadoCent && (
        <p className="mt-1 text-etiqueta text-tinta-suave">
          {coste.completo
            ? 'Comprando los envases enteros: '
            : 'Comprando los envases enteros de los que hay precio: '}
          <span className="cifra">{euros(coste.envasesCent)}</span>
        </p>
      )}
    </section>
  )
}

/* ================================================================== los pasos === */

function Pasos({ preparacion }: { preparacion: string }) {
  const pasos = pasosDePreparacion(preparacion)
  if (pasos.length === 0) return null
  return (
    <section aria-labelledby="preparacion">
      <h2 id="preparacion" className="font-display text-titulo font-semibold text-tinta">
        Preparación
      </h2>
      <ol
        aria-label="Pasos de la preparación"
        className="mt-2 flex list-decimal flex-col gap-2 pl-5 text-cuerpo text-tinta-suave"
      >
        {pasos.map((paso, posicion) => (
          <li key={`${posicion}-${paso.slice(0, 24)}`}>{paso}</li>
        ))}
      </ol>
    </section>
  )
}

/* ========================================================= pasar a la lista === */

/**
 * **Pasar la receta a la lista, enseñando antes lo que se va a comprar.**
 *
 * *Dos pasos a proposito*: se pide la previa -- que **no escribe nada** -- y solo despues se
 * confirma. **Y la previa enseña lo que NO se puede comprar**, que es la mitad de su valor:
 * *saber que la sal no entra porque no se sabe cuánto es mejor que ver una lista sin sal y no
 * entender por qué.*
 */
function PasarALista({ recetaId }: { recetaId: number }) {
  const [abierta, setAbierta] = useState(false)
  const [listaId, setListaId] = useState('')
  const [hecho, setHecho] = useState<string | null>(null)
  const previa = usePreviaDeCompra(abierta ? recetaId : null)
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas, enabled: abierta })
  const pasar = usePasarALista(recetaId)

  if (!abierta) {
    return (
      <Boton variante="principal" className="w-full" onClick={() => setAbierta(true)}>
        Añadir a la lista
      </Boton>
    )
  }

  const suyas = listas.data ?? []
  return (
    <Tarjeta titulo="Lo que habría que comprar">
      {previa.isPending && <p className="text-cuerpo text-tinta-suave">Mirando qué hace falta…</p>}
      {previa.error && (
        <Aviso tono="mal" titulo="No he podido mirar lo que hace falta">
          {textoDeError(previa.error)}
        </Aviso>
      )}
      {previa.data && (
        <div className="flex flex-col gap-3">
          {previa.data.lineas.length === 0 && (
            <p className="text-cuerpo text-tinta-suave">
              Nada que comprar: ningún ingrediente tiene cantidad.
            </p>
          )}

          {previa.data.lineas.length > 0 && (
            <ul className="flex flex-col">
              {previa.data.lineas.map((ln) => (
                <li
                  key={ln.clave}
                  className="flex min-h-[44px] flex-wrap items-baseline justify-between gap-2 border-t border-borde py-2 text-cuerpo first:border-t-0"
                >
                  <span className="text-tinta">{ln.texto}</span>
                  <span className="cifra text-right text-etiqueta text-tinta-suave">
                    {textoCantidad(ln.cantidad, ln.unidad)}
                    {ln.envases !== null && ` · ${ln.envases} envase${ln.envases === 1 ? '' : 's'}`}
                    {ln.sobrante ? ` · sobran ${ln.sobrante} ${ln.unidad}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {previa.data.sin_cantidad.length > 0 && (
            <p className="text-etiqueta text-tinta-suave">
              Sin cantidad, no se compra: {enEspanol(previa.data.sin_cantidad)}.
            </p>
          )}
          {previa.data.sin_consolidar.length > 0 && (
            <p className="text-etiqueta text-tinta-suave">
              No se pudieron juntar: {previa.data.sin_consolidar.join('; ')}.
            </p>
          )}

          {listas.error && (
            <Aviso tono="mal" titulo="No he podido mirar tus listas">
              {textoDeError(listas.error)}
            </Aviso>
          )}

          <div className="flex flex-wrap items-center gap-2">
            {suyas.length === 0 && !listas.isPending && !listas.error ? (
              <Link
                to="/compra/listas"
                className="inline-flex min-h-[44px] items-center text-cuerpo text-terracota underline underline-offset-2"
              >
                Crea una lista para poder añadir
              </Link>
            ) : (
              <label className="flex min-h-[44px] items-center gap-2">
                <span className="sr-only">Lista de destino</span>
                <select
                  value={listaId}
                  onChange={(e) => setListaId(e.target.value)}
                  aria-label="Lista de destino"
                  className="min-h-[44px] max-w-full rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta"
                >
                  <option value="">Elige una lista…</option>
                  {suyas.map((l) => (
                    <option key={l.id} value={l.id}>{l.nombre}</option>
                  ))}
                </select>
              </label>
            )}
            <Boton
              variante="principal"
              disabled={!listaId || pasar.isPending}
              onClick={() => pasar.mutate(listaId, {
                onSuccess: (r) => setHecho(
                  r && (r as { ya_estaba?: boolean }).ya_estaba
                    ? 'Ya estaba en la lista: no se ha duplicado.'
                    : 'Añadido a la lista.',
                ),
              })}
            >
              {pasar.isPending ? 'Pasando…' : 'Pasar a la lista'}
            </Boton>
            <Boton onClick={() => { setAbierta(false); setHecho(null) }}>Cerrar</Boton>
          </div>

          {hecho && <p role="status" className="text-cuerpo text-tinta">{hecho}</p>}
          {pasar.error && (
            <Aviso tono="mal" titulo="No he podido pasarla">
              {textoDeError(pasar.error)}
            </Aviso>
          )}
        </div>
      )}
    </Tarjeta>
  )
}

/* ================================================================ la pantalla === */

export function RecetaDetalle() {
  // **Sin sesión no se pide la receta.** *`/api/recetas/{id}` contesta 401, y eso no es «esa
  // receta no existe» ni un fallo: es que no ha entrado nadie. La pantalla lo dice con la salida
  // puesta y la consulta ni se lanza.*
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  if (sesion.isPending) return <Cargando que="la receta" filas={3} />
  if (!sesion.data?.usuario) {
    return <EntraParaVer texto="Las recetas se guardan con tu cuenta." />
  }
  return <DetalleDeLaReceta />
}

function DetalleDeLaReceta() {
  const { recetaId } = useParams()
  const numero = recetaId ? Number(recetaId) : null
  const id = numero !== null && Number.isFinite(numero) ? numero : null
  const [version, setVersion] = useState<number | null>(null)
  /** Para cuantas raciones se quieren los ingredientes. Vacio = las de la receta. */
  const [raciones, setRaciones] = useState<number | null>(null)
  const { data, isPending, error, refetch } = useReceta(id, version, raciones)
  useTitulo(data?.nombre)

  // **Cuál es la última versión, para no llamar «última» a la que se está mirando.** *El
  // `version` que devuelve la receta es el de la versión pedida, así que por sí solo no sirve
  // para saber si es la última; y la lista de versiones ya existe.*
  const cuenta = useClaveDeCuenta()
  const versiones = useQuery({
    queryKey: ['versiones', cuenta, id],
    queryFn: () => pide<{ versiones: number[] }>(`/recetas/${id}/versiones`),
    enabled: id !== null && data != null,
  })
  const disponibles = versiones.data?.versiones ?? []
  const ultima = disponibles.length > 0 ? Math.max(...disponibles) : (data?.version ?? null)
  // **Mientras la lista de versiones llega, las opciones salen de la propia receta**: así el
  // selector no se queda con una sola opción en el primer pintado.
  const opcionesDeVersion = disponibles.length > 0
    ? [...new Set([...disponibles, ...(data ? [data.version] : [])])].sort((a, b) => a - b)
    : data
      ? Array.from({ length: data.version }, (_, i) => i + 1)
      : []
  const esAnterior = version !== null && ultima !== null && version < ultima

  if (id === null) {
    return (
      <Vacio titulo="Esa receta no existe" className="grow">
        <p>
          Puede que se haya archivado o que el enlace esté mal.{' '}
          <Link to="/recetas" className="inline-flex min-h-[44px] items-center underline">
            Vuelve al recetario
          </Link>
          .
        </p>
      </Vacio>
    )
  }

  if (isPending) {
    return <Cargando que="la receta" filas={3} />
  }

  if (error) {
    // **404 no es un fallo.** Se distingue del resto para no pintar en rojo algo que es una respuesta.
    if (esErrorApi(error) && error.estado === 404) {
      return (
        <Vacio titulo="Esa receta no existe" className="grow">
          <p>
            Puede que se haya archivado o que el enlace esté mal.{' '}
            <Link to="/recetas" className="inline-flex min-h-[44px] items-center underline">
              Vuelve al recetario
            </Link>
            .
          </p>
        </Vacio>
      )
    }
    return (
      <Fallo
        error={error}
        reintentar={() => void refetch()}
        titulo="No he podido traer la receta"
      />
    )
  }
  if (!data) return null

  const ingredientes = data.ingredientes as IngredienteDeLaApi[]
  const coste = costeDeLaReceta(ingredientes)

  return (
    <div className="flex min-h-full flex-col gap-6">
      {/* ------------------------------------------ volver, donde estas y el nombre */}
      <header className="flex items-start gap-2">
        <Link
          to="/recetas"
          aria-label="Volver a las recetas"
          className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M19 12H5M11 18l-6-6 6-6" />
          </svg>
        </Link>
        <div className="min-w-0 flex-1">
          <p className="text-micro uppercase text-tinta-tenue">
            Receta · {data.raciones} {data.raciones === 1 ? 'ración' : 'raciones'}
            {data.minutos != null && data.minutos > 0 ? ` · ${data.minutos} min` : ''}
          </p>
          <h2 className="mt-1 break-words font-display text-titulo font-semibold text-tinta">
            {data.nombre}
          </h2>
        </div>
        <Link
          to="/recetas/plan"
          className="inline-flex min-h-[44px] shrink-0 items-center text-etiqueta text-terracota underline underline-offset-2"
        >
          Planificar
        </Link>
      </header>

      {/* ------------------------------------------------- raciones y version */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave" htmlFor="raciones">
            <span>Para</span>
            <span className="flex items-center gap-2">
              <input
                id="raciones"
                type="number"
                min={1}
                value={raciones ?? data.raciones_receta ?? data.raciones}
                onChange={(e) => {
                  const cuantas = Number(e.target.value)
                  // Vacio o cero es "las de la receta": no se manda una escala que no se ha pedido.
                  setRaciones(cuantas >= 1 ? cuantas : null)
                }}
                className="min-h-[44px] w-20 rounded-campo border border-borde-fuerte bg-papel px-2 py-2 text-[16px] tabular-nums text-tinta"
              />
              <span className="text-cuerpo text-tinta-suave">raciones</span>
            </span>
          </label>

          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave" htmlFor="version">
            <span>Versión</span>
            <select
              id="version"
              value={version ?? data.version}
              onChange={(e) => setVersion(Number(e.target.value))}
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta"
            >
              {/* De la 1 a la última: la lista sale de la receta, sin inventar números. */}
              {opcionesDeVersion.map((n) => (
                <option key={n} value={n}>
                  {n}
                  {n === ultima ? ' (última)' : ''}
                </option>
              ))}
            </select>
          </label>
        </div>

        {data.escalada && (
          <p className="text-etiqueta text-aviso tabular-nums">
            Calculado para {data.raciones}; la receta es de {data.raciones_receta}.
          </p>
        )}

        {esAnterior && (
          <p className="flex flex-wrap items-center gap-2 text-etiqueta text-aviso">
            Estás viendo una versión anterior. La última es la {ultima}.
            <button
              type="button"
              onClick={() => setVersion(null)}
              className="inline-flex min-h-[44px] items-center underline underline-offset-2"
            >
              Ver la última
            </button>
          </p>
        )}
      </div>

      <CosteDeLaReceta
        ingredientes={ingredientes}
        raciones={data.raciones}
      />

      <Ingredientes ingredientes={ingredientes} coste={coste} />

      <Pasos preparacion={data.preparacion} />

      {/* ------------------------------------------------------------ acciones */}
      <section aria-labelledby="acciones" className="flex flex-col gap-2">
        <h2 id="acciones" className="sr-only">Acciones</h2>
        <PasarALista recetaId={data.id} />
        <Link
          to={`/compra/cocina/${data.id}/${data.version}`}
          className="inline-flex min-h-[44px] w-full items-center justify-center rounded-campo border border-borde-fuerte bg-papel px-4 text-cuerpo font-medium text-tinta transition-colors duration-rapida ease-suave hover:bg-marfil"
        >
          Empezar a cocinar
        </Link>
        {data.escalada && (
          <p className="text-etiqueta text-tinta-suave">
            La lista se hará con las raciones de la receta ({data.raciones_receta}), no con
            las que estás mirando.
          </p>
        )}
        {esAnterior && (
          <p className="text-etiqueta text-tinta-suave">
            La lista se hará con la última versión de la receta.
          </p>
        )}
      </section>

      <section aria-labelledby="editar" className="flex flex-col gap-2">
        <h2 id="editar" className="font-display text-subtitulo font-semibold text-tinta">
          Editar
        </h2>
        <FormularioReceta receta={data} />
      </section>
    </div>
  )
}
