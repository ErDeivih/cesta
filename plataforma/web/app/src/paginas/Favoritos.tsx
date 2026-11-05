/** Los favoritos: lo que se compra siempre, **por lo que se ha movido**.
 *
 *  Esta pantalla es de vigilancia, no un catálogo, y lo que se viene a saber es
 *  «¿se ha movido algo de lo que compro siempre?». Por eso el orden y la cifra que
 *  se enseña son el cambio: lo que ha bajado arriba (y lo que más, primero),
 *  después lo que ha subido, y al final lo que no se ha movido.
 *
 *  **La composición es la del artboard aprobado** (`designs/cesta-app/project/Favoritos.dc.html`):
 *  una tarjeta por producto, con su nombre, su cadena, el precio de hoy y el estado; debajo, el
 *  rango del histórico (mínimo–máximo) con la marca de dónde cae hoy. El rango **no se inventa**:
 *  sale de la serie real que ya sirve `/api/grupo` para la ficha, filtrada por el `producto_id` de
 *  ese favorito y solo si la unidad no cambió por el camino. Si no hay serie para él, la tarjeta
 *  enseña su precio y su cambio real, y ninguna barra.
 *
 *  Lo que no se pierde de la versión anterior: la ventana de 7/30/90 días, el orden que decide la
 *  API, el pasar favoritos a una lista (de uno en uno y todos de golpe), el quitar, la puerta de
 *  sesión, los estados de carga/vacío/error con reintento y el motivo de los que no se pueden
 *  comparar (`sin historico`, `cambio de formato`, `ya no esta en el catalogo`).
 *
 *  §8 manda en los textos: nada de API, de IDs, de «gold» ni de cómo se calcula nada. «Historial
 *  de 5 días» o «ha bajado un 8,7 % en 7 días» son la medida dicha, no la receta.
 */
import { useId, useState } from 'react'
import { Link } from 'react-router-dom'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { anadirDesdeFavoritos, misListas, yo } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { quitarFavorito, verFavoritos } from '../api/favoritos'
import { useGrupo } from '../api/consultas'
import {
  eurosUnidad, fecha, ms, nombreCadena, porcentaje,
} from '../api/formato'
import { IconoCorazonLleno } from '../componentes/iconos'
import { Aviso, Boton, Fallo, Vacio, cx } from '../componentes/ui'
import { listaDelDiario } from '../logica/listaDelDiario'
import type { Favorito, PuntoSerie } from '../tipos'

/** Las ventanas que se pueden pedir. Siete días es la que contesta «¿está más caro que la
 *  semana pasada?», que es la pregunta de la compra; treinta y noventa son para mirar una
 *  tendencia. */
const VENTANAS = [7, 30, 90]

/** El día en milisegundos, para contar la ventana real de una serie. */
const UN_DIA = 24 * 60 * 60 * 1000

/** *** EL RANGO DEL HISTÓRICO, CON LOS DATOS QUE HAY. *** *
 *
 *  *La regla es la de siempre: un mínimo que mezcla dos productos o dos unidades no es el mínimo
 *  de nada, y no se enseña.* *Por eso se filtra por el `producto_id` del favorito y se exige que
 *  no haya más de una unidad en la serie. Y se necesitan **dos precios**: con uno solo no hay
 *  rango, hay un precio.*
 *
 *  El precio de hoy entra en la cuenta aunque la última captura de la serie no lo traiga: es un
 *  dato real de hoy, y sin él la marca de la barra podría caer fuera del mínimo y del máximo.
 */
export interface RangoDeFavorito {
  minimo: number
  maximo: number
  actual: number
  /** Días de calendario entre la primera y la última fecha de la serie, contando las dos. */
  dias: number
  desde: string
  hasta: string
  unidad: string | null
  /** Dónde cae el precio de hoy dentro del rango, de 0 a 100. */
  posicion: number
}

export function rangoDeLaSerie(
  puntos: PuntoSerie[],
  productoId: string | null | undefined,
  precioActual: number | null | undefined,
  unidad: string | null | undefined,
): RangoDeFavorito | null {
  if (!productoId) return null
  if (precioActual == null || !Number.isFinite(precioActual) || precioActual <= 0) return null

  const delProducto = puntos
    .filter((p) => p.producto_id === productoId)
    .map((p) => ({ ...p, momento: ms(p.fecha) }))
    .filter((p): p is PuntoSerie & { momento: number } => Number.isFinite(p.momento))
    .sort((a, b) => a.momento - b.momento)

  if (delProducto.length === 0) return null

  const conPrecio = delProducto.filter(
    (p) => p.precio_unidad_cent != null && Number.isFinite(p.precio_unidad_cent)
      && p.precio_unidad_cent > 0,
  )
  if (conPrecio.length < 2) return null

  const unidades = [...new Set(
    conPrecio.map((p) => (p.unidad_canon ?? '').trim().toLowerCase()).filter(Boolean),
  )]
  if (unidades.length > 1) return null

  const unidadDelFavorito = (unidad ?? '').trim().toLowerCase()
  if (unidades.length === 1 && unidadDelFavorito && unidades[0] !== unidadDelFavorito) return null

  const primera = delProducto[0]
  const ultima = delProducto[delProducto.length - 1]
  const dias = Math.floor((ultima.momento - primera.momento) / UN_DIA) + 1
  // *Un solo día con dos precios no es una serie: es un dato repetido.*
  if (dias < 2) return null

  const precios = [...conPrecio.map((p) => p.precio_unidad_cent as number), precioActual]
  const minimo = Math.min(...precios)
  const maximo = Math.max(...precios)
  const posicion = maximo === minimo
    ? 50
    : Math.min(100, Math.max(0, ((precioActual - minimo) / (maximo - minimo)) * 100))

  return {
    minimo,
    maximo,
    actual: precioActual,
    dias,
    desde: primera.fecha,
    hasta: ultima.fecha,
    unidad: unidades[0] ?? (unidadDelFavorito || null),
    posicion,
  }
}

/** *** LO QUE DICE EL RANGO, CON PALABRAS. *** *
 *
 *  *Los dos cortes de «cerca» (10 %) son de composición, no de dato: sirven para que la etiqueta
 *  diga lo mismo que se ve en la barra. El dato es el mínimo, el máximo y dónde cae hoy.*
 */
export type TonoDelRango = 'bien' | 'aviso' | 'neutro'

const CERCA = 10

export function estadoDelRango(r: RangoDeFavorito): { texto: string; tono: TonoDelRango } {
  if (r.maximo === r.minimo) return { texto: 'sin cambios', tono: 'neutro' }
  if (r.actual <= r.minimo) return { texto: 'en el mínimo', tono: 'bien' }
  if (r.actual >= r.maximo) return { texto: 'en el máximo', tono: 'aviso' }
  if (r.posicion <= CERCA) return { texto: 'cerca del mínimo', tono: 'bien' }
  if (r.posicion >= 100 - CERCA) return { texto: 'cerca del máximo', tono: 'aviso' }
  return { texto: 'ni mínimo ni máximo', tono: 'neutro' }
}

const COLOR_DEL_TONO: Record<TonoDelRango, string> = {
  bien: 'text-bien',
  aviso: 'text-aviso',
  neutro: 'text-tinta-suave',
}

/** El sentido del cambio, que es lo que ordena la lista. `null` si no se pudo medir. */
function sentidoDe(f: Favorito): 'baja' | 'sube' | 'igual' | null {
  if (!f.comparable) return null
  const pct = f.variacion_pct
  if (pct == null || !Number.isFinite(pct)) return null
  return pct < 0 ? 'baja' : pct > 0 ? 'sube' : 'igual'
}

/** El cambio dicho como se lee: «ha bajado un 8,7 % en 7 días».
 *
 *  Los días son los que hay **de verdad** (`dias_medidos`): un producto que lleva tres días en el
 *  catálogo dice tres. Si la API vieja no los manda, se dice la ventana que se pidió.
 */
export function textoDelCambio(f: Favorito, ventana: number): string | null {
  if (!f.comparable) return null
  const pct = f.variacion_pct
  if (pct == null || !Number.isFinite(pct)) return null
  const medidos = f.dias_medidos != null && f.dias_medidos > 0 ? f.dias_medidos : null
  const pedidos = f.dias != null && f.dias > 0 ? f.dias : ventana
  const dias = medidos ?? pedidos
  const cuando = `en ${dias} ${dias === 1 ? 'día' : 'días'}`
  if (pct === 0) return `sin cambios ${cuando}`
  const cuanto = porcentaje(Math.abs(pct), 1)
  return pct < 0 ? `ha bajado un ${cuanto} ${cuando}` : `ha subido un ${cuanto} ${cuando}`
}

function colorDelCambio(sentido: 'baja' | 'sube' | 'igual'): string {
  return sentido === 'baja' ? 'text-bien' : sentido === 'sube' ? 'text-error' : 'text-tinta-suave'
}

/** La clave estable de un favorito, para el `key` de React y para saber cuál se está quitando. */
function claveDeFavorito(f: { grupo_id?: number | null; producto_id?: string | null }): string {
  if (f.producto_id) return f.producto_id
  if (f.grupo_id != null) return `grupo-${f.grupo_id}`
  return 'sin-id'
}

/** A dónde lleva el nombre: a la comparación del grupo o a la ficha del producto suelto.
 *
 *  *La ruta nueva, no la redirección de antes: `/compra/comparar/:id` y
 *  `/compra/productos/:fuente/:id`.* *Un favorito que apunta a algo que ya no está no lleva a
 *  ninguna parte.*
 */
function rutaDeLaFicha(f: Favorito): string | null {
  if (f.desconocido) return null
  if (f.grupo_id != null) return `/compra/comparar/${f.grupo_id}`
  const pid = f.producto_id
  if (!pid || !pid.includes(':')) return null
  const [fuente, ...resto] = pid.split(':')
  const idFuente = resto.join(':')
  if (!fuente || !idFuente) return null
  return `/compra/productos/${encodeURIComponent(fuente)}/${encodeURIComponent(idFuente)}`
}

/** La cadena y la marca, sin repetir la marca si ya está en el nombre. */
function metaDe(f: Favorito): string {
  const cadena = f.cadena ?? f.fuente ?? null
  const marca = f.marca?.trim() ?? ''
  const nombre = f.nombre ?? ''
  const marcaRepetida = marca.length > 0 && nombre.toLowerCase().includes(marca.toLowerCase())
  return [cadena ? nombreCadena(cadena) : null, marcaRepetida ? null : marca]
    .filter((x): x is string => Boolean(x))
    .join(' · ')
}

/** Por qué no se puede decir cuánto ha cambiado. */
function motivoDe(f: Favorito): string {
  if (f.desconocido) {
    return f.que === 'grupo'
      ? 'Este producto ya no está en el catálogo.'
      : 'Este producto ya no está en el catálogo de su cadena.'
  }
  if (f.motivo === 'cambio de formato') {
    return 'Cambió el formato, así que el precio de hoy y el de antes no se pueden comparar.'
  }
  return 'Todavía no hay dos precios que comparar: se añadió hace poco.'
}

/* ================================================================== la lista === */

/** El desplegable de listas, con la última usada ya elegida.
 *
 *  Sin listas no hay desplegable: se dice que hace falta crear una, que es lo único que se puede
 *  hacer. El `select` **no lleva tamaño de letra propio**: por debajo de 16 px, Safari del móvil
 *  hace zoom al enfocar y la página se descuadra. Lo vigila `test_ui_movil.py`.
 */
function ElegirLista({ listas, valor, alCambiar, etiqueta }: {
  listas: { id: string; nombre: string }[]
  valor: string
  alCambiar: (id: string) => void
  etiqueta: string
}) {
  if (!listas.length) {
    return (
      <Link
        to="/compra/listas"
        className="inline-flex min-h-[44px] items-center text-etiqueta text-terracota underline underline-offset-2"
      >
        Crea una lista para poder añadir
      </Link>
    )
  }
  return (
    <label className="flex min-h-[44px] items-center gap-2">
      <span className="text-etiqueta text-tinta-tenue">{etiqueta}</span>
      <select
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        className="min-h-[44px] max-w-[9rem] rounded-campo border border-borde-fuerte bg-papel px-2 py-2"
      >
        {!valor && <option value="">Elige una lista</option>}
        {listas.map((l) => (
          <option key={l.id} value={l.id}>{l.nombre}</option>
        ))}
      </select>
    </label>
  )
}

/** El corazón de quitar. 44 px, `aria-pressed` y el nombre en el `aria-label`: el icono solo no
 *  es un botón. */
function BotonQuitar({ quitando, alQuitar }: { quitando: boolean; alQuitar: () => void }) {
  return (
    <button
      type="button"
      aria-label="Quitar de favoritos"
      aria-pressed="true"
      title="Quitar de favoritos"
      disabled={quitando}
      onClick={alQuitar}
      className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla text-terracota transition-colors duration-rapida ease-suave hover:bg-lavado-terracota disabled:cursor-not-allowed disabled:opacity-50"
    >
      <IconoCorazonLleno width={20} height={20} />
    </button>
  )
}

/** Un favorito que sí se puede medir: precio, rango real (si hay serie) y cambio. */
function TarjetaDeFavorito({ f, ventana, elegida, quitando, alQuitar, alAnadir, anadiendo }: {
  f: Favorito
  ventana: number
  elegida: string
  quitando: boolean
  alQuitar: () => void
  alAnadir: () => void
  anadiendo: boolean
}) {
  const id = useId()
  const grupo = useGrupo(f.grupo_id)
  const rango = rangoDeLaSerie(
    grupo.data?.serie ?? [],
    f.producto_id,
    f.precio_unidad_cent,
    f.unidad,
  )
  const estado = rango ? estadoDelRango(rango) : null
  const cambio = textoDelCambio(f, ventana)
  const sentido = sentidoDe(f)
  const ruta = rutaDeLaFicha(f)
  const meta = metaDe(f)
  const nombre = f.nombre ?? 'Un producto que seguías'

  return (
    <section
      aria-labelledby={id}
      className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 id={id} className="text-cuerpo-fuerte leading-snug text-tinta">
            {ruta ? (
              <Link
                to={ruta}
                className="flex min-h-[44px] items-center rounded-nota hover:underline focus-visible:underline"
              >
                {nombre}
              </Link>
            ) : (
              nombre
            )}
          </h2>
          {meta && <p className="mt-0.5 text-etiqueta text-tinta-tenue">{meta}</p>}
        </div>

        <div className="shrink-0 text-right">
          <p className="cifra text-precio-fila font-semibold text-tinta">
            {eurosUnidad(f.precio_unidad_cent, f.unidad)}
          </p>
          {estado && (
            <p className={cx('text-etiqueta-fuerte', COLOR_DEL_TONO[estado.tono])}>
              {estado.texto}
            </p>
          )}
        </div>

        <BotonQuitar quitando={quitando} alQuitar={alQuitar} />
      </div>

      {/* *** EL RANGO, SOLO SI HAY SERIE DE VERDAD. *** *
          *El mínimo y el máximo son de la serie de este producto; la marca dice dónde cae hoy.*
          *La barra es decorativa para quien no la ve: debajo va la misma frase en texto.* */}
      {rango && (
        <>
          <div aria-hidden="true" className="mt-3 flex items-center gap-2">
            <span className="cifra w-[4.5rem] shrink-0 truncate text-etiqueta text-tinta-tenue">
              {eurosUnidad(rango.minimo, rango.unidad)}
            </span>
            <span className="relative h-2 min-w-0 flex-1 rounded-pastilla bg-lavado-verde">
              <span
                className="absolute top-1/2 h-3.5 w-[3px] -translate-x-1/2 -translate-y-1/2 rounded-pastilla bg-verde"
                style={{ left: `${rango.posicion}%` }}
              />
            </span>
            <span className="cifra w-[4.5rem] shrink-0 truncate text-right text-etiqueta text-tinta-tenue">
              {eurosUnidad(rango.maximo, rango.unidad)}
            </span>
          </div>
          <p className="sr-only">
            Precio de {nombre}: entre {eurosUnidad(rango.minimo, rango.unidad)} y{' '}
            {eurosUnidad(rango.maximo, rango.unidad)}, del {fecha(rango.desde, true)} al{' '}
            {fecha(rango.hasta, true)}. Hoy, {eurosUnidad(rango.actual, rango.unidad)}.
          </p>
          <div className="mt-1.5 flex flex-wrap items-baseline gap-x-3 gap-y-0.5 text-etiqueta">
            <span className="text-tinta-tenue">Historial de {rango.dias} días</span>
            {cambio && sentido && (
              <span data-cambio={sentido} className={cx('font-medium', colorDelCambio(sentido))}>
                {cambio}
              </span>
            )}
          </div>
        </>
      )}

      {!rango && cambio && sentido && (
        <p className="mt-2 text-etiqueta">
          <span data-cambio={sentido} className={cx('font-medium', colorDelCambio(sentido))}>
            {cambio}
          </span>
        </p>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-x-4">
        <Boton variante="sutil" disabled={!elegida || anadiendo} onClick={alAnadir}>
          A la lista
        </Boton>
      </div>
    </section>
  )
}

/** Un favorito que no se puede comparar: se dice por qué, en vez de enseñar un cero. */
function TarjetaSinMedida({ f, elegida, quitando, alQuitar, alAnadir, anadiendo }: {
  f: Favorito
  elegida: string
  quitando: boolean
  alQuitar: () => void
  alAnadir: () => void
  anadiendo: boolean
}) {
  const id = useId()
  const ruta = rutaDeLaFicha(f)
  const meta = metaDe(f)
  const nombre = f.nombre ?? 'Un producto que seguías'

  return (
    <section
      aria-labelledby={id}
      className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 id={id} className="text-cuerpo-fuerte leading-snug text-tinta">
            {ruta ? (
              <Link
                to={ruta}
                className="flex min-h-[44px] items-center rounded-nota hover:underline focus-visible:underline"
              >
                {nombre}
              </Link>
            ) : (
              nombre
            )}
          </h3>
          {meta && <p className="mt-0.5 text-etiqueta text-tinta-tenue">{meta}</p>}
        </div>

        <div className="shrink-0 text-right">
          {f.precio_unidad_cent != null && (
            <p className="cifra text-precio-fila font-semibold text-tinta">
              {eurosUnidad(f.precio_unidad_cent, f.unidad)}
            </p>
          )}
          <p className={cx(
            'text-etiqueta-fuerte',
            f.desconocido ? 'text-aviso' : 'text-tinta-suave',
          )}>
            {f.desconocido ? 'ya no está' : 'sin comparar'}
          </p>
        </div>

        <BotonQuitar quitando={quitando} alQuitar={alQuitar} />
      </div>

      <p className="mt-2 text-cuerpo text-tinta-suave">{motivoDe(f)}</p>

      <div className="mt-2 flex flex-wrap items-center gap-x-4">
        <Boton variante="sutil" disabled={!elegida || anadiendo} onClick={alAnadir}>
          A la lista
        </Boton>
      </div>
    </section>
  )
}

/* ================================================================ los estados === */

/** Volver a la portada, y el contador de productos cuando ya se sabe cuántos hay. */
function FilaDeVuelta({ cuantos, orden }: { cuantos?: number; orden?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-2">
      <Link
        to="/"
        className="inline-flex min-h-[44px] items-center gap-1.5 rounded-campo pr-2 text-cuerpo text-tinta-suave transition-colors duration-rapida ease-suave hover:text-tinta"
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
          className="shrink-0"
        >
          <path d="M19 12H5M11 18l-6-6 6-6" />
        </svg>
        Volver
      </Link>

      {cuantos != null && (
        <div className="text-right">
          <p className="text-etiqueta text-tinta-tenue">
            {cuantos} {cuantos === 1 ? 'producto' : 'productos'}
          </p>
          {orden && (
            <p className="text-etiqueta text-tinta-tenue">Primero lo que ha bajado</p>
          )}
        </div>
      )}
    </div>
  )
}

/** La forma de lo que viene: tres tarjetas, no una línea de texto. */
function CargandoFavoritos() {
  return (
    <div role="status" aria-live="polite" className="grid gap-3">
      <span className="sr-only">Cargando tus favoritos…</span>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          aria-hidden="true"
          className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
        >
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <div className="h-4 w-2/3 animate-pulse rounded-nota bg-marfil motion-reduce:animate-none" />
              <div className="mt-2 h-3 w-1/3 animate-pulse rounded-nota bg-marfil motion-reduce:animate-none" />
            </div>
            <div className="h-8 w-20 animate-pulse rounded-campo bg-marfil motion-reduce:animate-none" />
            <div className="h-11 w-11 animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
          </div>
          <div className="mt-4 h-2 w-full animate-pulse rounded-pastilla bg-marfil motion-reduce:animate-none" />
        </div>
      ))}
    </div>
  )
}

/* ================================================================== la página === */

export function Favoritos() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const [ventana, setVentana] = useState(7)
  const favoritos = useQuery({
    queryKey: ['favoritos', ventana],
    queryFn: () => verFavoritos(ventana),
    enabled: sesion.data?.usuario != null,
  })
  const [destino, setDestino] = useState<string>('')
  const [dicho, setDicho] = useState<string | null>(null)
  const elegida = listaDelDiario(listas.data, destino) ?? ''
  const idSinCambio = useId()

  const quitar = useMutation({
    mutationFn: (f: { grupo_id: number | null; producto_id?: string | null }) =>
      quitarFavorito(f.grupo_id, f.producto_id ?? null),
    onSuccess: () => {
      cliente.invalidateQueries({ queryKey: ['favoritos'] })
      setDicho('Quitado de favoritos')
      setTimeout(() => setDicho(null), 4000)
    },
  })

  const pasar = useMutation({
    mutationFn: (f: { grupo_id?: number | null; producto_id?: string | null
                      todos?: Favorito[] }) => {
      const grupo_ids: number[] = []
      const producto_ids: string[] = []
      if (f.todos) {
        for (const x of f.todos) {
          if (x.grupo_id != null) grupo_ids.push(x.grupo_id)
          else if (x.producto_id) producto_ids.push(x.producto_id)
        }
      } else {
        if (f.grupo_id != null) grupo_ids.push(f.grupo_id)
        else if (f.producto_id) producto_ids.push(f.producto_id)
      }
      return anadirDesdeFavoritos(elegida, { grupo_ids, producto_ids })
    },
    onSuccess: (cuantos) => {
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', elegida] })
      cliente.invalidateQueries({ queryKey: ['reparto', elegida] })
      setDicho(
        cuantos === 0
          ? 'Ya estaban en la lista'
          : cuantos === 1
            ? 'Añadido a la lista'
            : `Añadidos ${cuantos} a la lista`,
      )
      setTimeout(() => setDicho(null), 4000)
    },
  })

  if (sesion.isLoading || favoritos.isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
        <FilaDeVuelta />
        <CargandoFavoritos />
      </div>
    )
  }

  if (!sesion.data?.usuario) {
    // **La puerta es la de siempre**, pero **sin un segundo `h1`**: el título de la página ya lo
    // pone la cabecera de la suite («Favoritos»), y dos `h1` en el mismo documento dejan el
    // encabezado sin dueño. El título de la puerta se lee igual; lo que cambia es la etiqueta.
    return (
      <Vacio titulo="Entra para ver tus favoritos" className="grow">
        <p>
          Los favoritos se guardan en tu cuenta. Se entra desde{' '}
          <Link to="/compra/listas" className="inline-flex min-h-[44px] items-center underline">
            la lista
          </Link>
          .
        </p>
      </Vacio>
    )
  }

  if (favoritos.isError) {
    // **`Fallo` y no un cartel escrito aquí**: es el que decide el tono (sin cobertura no es rojo)
    // y el que deja volver a intentarlo sin recargar la página a mano.
    return (
      <div className="mx-auto flex w-full max-w-lectura grow flex-col gap-4">
        <FilaDeVuelta />
        <Fallo error={favoritos.error} reintentar={() => void favoritos.refetch()} />
      </div>
    )
  }

  const lista = favoritos.data?.favoritos ?? []
  const fechaDatos = favoritos.data?.fecha_datos
  const nombreDeDestino = listas.data?.find((l) => l.id === elegida)?.nombre
  // La API ya manda los comparables en el orden bueno: bajadas, subidas y quietos. Aquí solo se
  // parten para poder decir **por qué** los de abajo no tienen cifra.
  const conCambio = lista.filter((f) => f.comparable)
  const sinCambio = lista.filter((f) => !f.comparable)

  if (!lista.length) {
    return (
      <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
        <FilaDeVuelta />
        <section
          aria-labelledby="favoritos-vacio"
          className="rounded-tarjeta bg-papel p-4 shadow-apoyado"
        >
          <h2 id="favoritos-vacio" className="font-display text-titulo font-semibold text-tinta">
            No sigues ningún producto
          </h2>
          <p className="mt-2 text-cuerpo text-tinta-suave">
            Aquí van los productos que compras siempre, para ver si se mueven sin tener que
            buscarlos. Se añaden desde la ficha de un producto, con el corazón.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              to="/compra"
              className="inline-flex min-h-[44px] items-center justify-center rounded-campo border border-transparent bg-bosque px-4 text-cuerpo font-medium text-marfil shadow-apoyado transition-colors duration-rapida ease-suave hover:brightness-110"
            >
              Buscar un producto
            </Link>
            <Link
              to="/compra/listas"
              className="inline-flex min-h-[44px] items-center justify-center rounded-campo border border-borde-fuerte bg-papel px-4 text-cuerpo font-medium text-tinta transition-colors duration-rapida ease-suave hover:bg-marfil"
            >
              Ver mi lista
            </Link>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-lectura flex-col gap-4">
      <FilaDeVuelta cuantos={lista.length} orden={conCambio.length > 0} />

      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <div
            role="group"
            aria-label="Ventana del cambio"
            className="flex flex-wrap items-center gap-1.5"
          >
            <span className="text-etiqueta text-tinta-tenue">Cambio en</span>
            {VENTANAS.map((d) => (
              <button
                key={d}
                type="button"
                aria-pressed={ventana === d}
                onClick={() => setVentana(d)}
                className={cx(
                  'cifra min-h-[44px] rounded-pastilla border px-3 text-etiqueta font-semibold transition-colors duration-rapida ease-suave',
                  ventana === d
                    ? 'border-terracota bg-terracota text-sobre-terracota'
                    : 'border-borde-fuerte bg-papel text-tinta-suave hover:bg-marfil',
                )}
              >
                {d} días
              </button>
            ))}
          </div>
          {/* *La ventana, dicha con palabras y no solo con el color del botón pulsado.* */}
          <p className="text-etiqueta text-tinta-tenue" aria-live="polite">
            Ventana activa: {ventana} días
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <ElegirLista
            listas={listas.data ?? []}
            valor={elegida}
            alCambiar={setDestino}
            etiqueta="Añadir a"
          />
          <Boton
            variante="normal"
            disabled={!elegida || pasar.isPending}
            onClick={() => pasar.mutate({ todos: lista })}
          >
            {pasar.isPending ? 'Añadiendo…' : `Añadir los ${lista.length} a la lista`}
          </Boton>
          <Link
            to={elegida ? `/compra/listas/${encodeURIComponent(elegida)}` : '/compra/listas'}
            className="inline-flex min-h-[44px] items-center text-etiqueta text-terracota underline underline-offset-2"
          >
            {nombreDeDestino ? `Ver «${nombreDeDestino}»` : 'Ver la lista'}
          </Link>
        </div>

        {dicho && <Aviso tono="bien" titulo={dicho} />}
        {pasar.isError && (
          <Aviso tono="mal" titulo="No he podido añadirlos">
            {textoDeError(pasar.error)}
          </Aviso>
        )}
        {quitar.isError && (
          <Aviso tono="mal" titulo="No he podido quitarlo">
            {textoDeError(quitar.error)}
          </Aviso>
        )}
      </div>

      <div className="grid gap-3">
        {conCambio.map((f) => {
          const clave = claveDeFavorito(f)
          return (
            <TarjetaDeFavorito
              key={clave}
              f={f}
              ventana={ventana}
              elegida={elegida}
              quitando={quitar.isPending}
              anadiendo={pasar.isPending}
              alQuitar={() => quitar.mutate({
                grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
              })}
              alAnadir={() => pasar.mutate({
                grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
              })}
            />
          )
        })}
      </div>

      {/* **El grupo de los que no se pueden comparar, al final y con su motivo.** Un favorito sin
          histórico se pintaba igual que los demás, con su precio y sin decir nada del cambio, y
          eso se lee como «no se ha movido». */}
      {sinCambio.length > 0 && (
        <section className="grid gap-3" aria-labelledby={idSinCambio}>
          <div>
            <h2
              id={idSinCambio}
              className="font-display text-subtitulo font-semibold text-tinta"
            >
              Sin cambio que medir todavía
            </h2>
            <p className="mt-1 text-etiqueta text-tinta-suave">
              No se pueden comparar en los últimos {ventana} días. Se dice por qué.
            </p>
          </div>
          <div className="grid gap-3">
            {sinCambio.map((f) => {
              const clave = claveDeFavorito(f)
              return (
                <TarjetaSinMedida
                  key={clave}
                  f={f}
                  elegida={elegida}
                  quitando={quitar.isPending}
                  anadiendo={pasar.isPending}
                  alQuitar={() => quitar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                  alAnadir={() => pasar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                />
              )
            })}
          </div>
        </section>
      )}

      {fechaDatos && (
        <p className="text-etiqueta text-tinta-tenue">Precios del {fecha(fechaDatos)}.</p>
      )}
    </div>
  )
}
