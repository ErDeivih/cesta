/** *** EL ESTADO DE LA DEMO: LISTA DE LA SEMANA, FAVORITOS Y SUS CUENTAS. *** *
 *
 *  *La demo publicada no tiene servidor. `api.ts` guarda este objeto en IndexedDB y aquí
 *  viven las cuentas: cuánto cuesta una lista, qué precio tiene cada línea en cada cadena,
 *  qué hay en favoritos. Todo es puro y serializable (JSON), para que las pruebas puedan
 *  llamarlo sin navegador y para que lo guardado se pueda volver a leer tal cual.*
 *
 *  *** DOS LISTAS, Y SOLO UNA ES LA DE CASA. *** *
 *
 *  - **La semana** es la lista de casa de la demo: ocho productos reales del catálogo, con
 *    su precio. Es la que se abre al entrar y la que se puede usar de verdad (añadir,
 *    tachar, cambiar cantidad, comparar).
 *  - **La casa (13 nov)** se queda como estaba, con sus seis líneas y sus precios de la
 *    captura antigua. *No se borra: es la muestra que ya estaba publicada, y quitar lo que
 *    había para meter lo nuevo es justo lo que no se hace.*
 */
import datos from './datos.json'

import { CATALOGO, FECHA_CATALOGO, NOMBRE_SECCION, type ProductoCatalogo } from './catalogo'
import type { DetalleLista } from '../api/cesta'
import type {
  Donde,
  Estimacion,
  Favorito,
  Linea,
  Lista,
  OpcionEnTienda,
  OpcionTienda,
  RepartoTiendas,
} from '../tipos'

/** *Sube cuando cambia la forma de la muestra. Lo guardado de una versión anterior no se
 *  mezcla: se vuelve a sembrar. La 3 es la de la lista de la semana con catálogo; la 2 era
 *  la muestra de 120 filas y la 1 la primera demo.* */
export const VERSION_MUESTRA = 3

/** *Lo que se guarda en el dispositivo: todo el estado de la demo, en un objeto.* */
export interface Muestra {
  version: number
  yo: Record<string, unknown>
  estado: Record<string, unknown>
  listas: Lista[]
  detalles: Record<string, Linea[]>
  favoritos: Favorito[]
  /** *Los precios de la lista antigua, por id de línea: se conservan tal como se capturaron.* */
  legado: Record<string, { coste_cent: number | null; mas_barata: string | null; opciones: OpcionEnTienda[] }>
}

const LEGADO = datos as unknown as {
  yo: Record<string, unknown>
  estado: Record<string, unknown>
  detalle: { lineas: Linea[] }
  reparto: { sin_asignar: { linea_id: string; coste_cent: number | null; mas_barata: string | null; opciones: OpcionEnTienda[] }[] }
}

/** *Los productos de la lista de la semana. Elegidos por id del catálogo para que no dependan
 *  de un nombre que cambie: leche, huevos, yogur, pan, pollo, tomate frito, arroz y aceite.* */
const SEMANA = [
  { grupoId: 11627, nombre: 'Leche entera brik 1 l.', cantidad: 2 },
  { grupoId: 4373, nombre: 'Huevos grandes L', cantidad: 1 },
  { grupoId: 3093, nombre: 'Yogur natural', cantidad: 1 },
  { grupoId: 3094, nombre: 'Pan de molde integral sin corteza', cantidad: 1 },
  { grupoId: 21334, nombre: 'Pechuguita de pollo 100 g', cantidad: 2 },
  { grupoId: 22561, nombre: 'Tomate frito Carrefour lata 400 g.', cantidad: 1 },
  { grupoId: 7077, nombre: 'Arroz basmati', cantidad: 1 },
  { grupoId: 78952, nombre: 'Aceite de oliva virgen Hacendado', cantidad: 1 },
]

function nuevoId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `demo-${Math.random().toString(36).slice(2)}-${Date.now()}`
}

function productoDeGrupo(grupoId: number | null): ProductoCatalogo | null {
  if (grupoId === null) return null
  return CATALOGO.find((p) => p.grupo_id === grupoId) ?? null
}

/** *La oferta más barata por unidad de un producto. Es la misma regla que la búsqueda: el
 *  precio de venta que se enseña es el de la cadena más barata por kilo o por litro.* */
function ofertaMasBarata(producto: ProductoCatalogo) {
  return [...producto.ofertas].sort((a, b) => a.precio_unidad_cent - b.precio_unidad_cent)[0]
}

/** *Una línea con lo que hace falta para pintarla. Copia, no referencia: la lista que se
 *  enseña no puede mutar el estado guardado sin pasar por las funciones de abajo.* */
function lineaCompleta(linea: Linea): Linea {
  return {
    id: linea.id,
    nombre_visto: linea.nombre_visto,
    cantidad: Math.max(1, Math.min(99, Math.round(linea.cantidad))),
    nota: linea.nota ?? null,
    grupo_id: linea.grupo_id ?? null,
    producto_id: linea.producto_id ?? null,
    tachado_en: linea.tachado_en ?? null,
    seccion: linea.seccion,
    pasillo: linea.pasillo,
    pasillo_orden: linea.pasillo_orden,
  }
}

/** *El coste de una línea, con la cadena y las opciones que tiene hoy. `null` cuando no hay
 *  precio: una línea sin producto del catálogo no se inventa un precio.* */
export function precioDeLinea(
  muestra: Muestra,
  linea: Linea,
): { coste_cent: number; mas_barata: string; opciones: OpcionEnTienda[] } | null {
  const producto = productoDeGrupo(linea.grupo_id)
  if (producto) {
    const opciones = producto.ofertas
      .map((o) => ({
        cadena: o.cadena,
        coste_cent: Math.round(o.precio_cent * linea.cantidad * 100) / 100,
        coste_sin_oferta_cent: Math.round(o.precio_cent * linea.cantidad * 100) / 100,
        promo: o.promocion,
      }))
      .sort((a, b) => a.coste_cent - b.coste_cent)
    if (opciones.length === 0) return null
    return { coste_cent: opciones[0].coste_cent, mas_barata: opciones[0].cadena, opciones }
  }
  const viejo = muestra.legado[linea.id]
  if (viejo && viejo.coste_cent !== null && viejo.opciones.length > 0) {
    return {
      coste_cent: Math.round(viejo.coste_cent * linea.cantidad),
      mas_barata: viejo.mas_barata ?? viejo.opciones[0].cadena,
      opciones: viejo.opciones.map((o) => ({
        ...o,
        coste_cent: Math.round(o.coste_cent * linea.cantidad),
        coste_sin_oferta_cent: Math.round(o.coste_sin_oferta_cent * linea.cantidad),
      })),
    }
  }
  return null
}

/** *Lo que cuesta la lista ahora mismo: la suma de las líneas con precio. `sin_precio` cuenta
 *  las que no lo tienen —no se calla—, y `en_carrito` son las tachadas.* */
export function estimacionDe(muestra: Muestra, id: string): Estimacion {
  const lineas = muestra.detalles[id] ?? []
  let total = 0
  let enCarrito = 0
  let sinPrecio = 0
  for (const linea of lineas) {
    const precio = precioDeLinea(muestra, linea)
    if (!precio) {
      sinPrecio += 1
      continue
    }
    total += precio.coste_cent
    if (linea.tachado_en) enCarrito += precio.coste_cent
  }
  return {
    total_cent: Math.round(total),
    en_carrito_cent: Math.round(enCarrito),
    por_recoger_cent: Math.round(total - enCarrito),
    lineas: lineas.length,
    sin_precio: sinPrecio,
  }
}

/** *El detalle de una lista tal como lo espera la pantalla. `cotizacion` es la del carrito (lo
 *  tachado), que es lo que se confirma al cerrar; no se firma nada de verdad: la demo no
 *  tiene servidor, y el sello solo tiene que ser estable durante la visita.* */
export function detalleDe(muestra: Muestra, id: string): DetalleLista {
  const lineas = (muestra.detalles[id] ?? []).map(lineaCompleta)
  const estimacion = estimacionDe(muestra, id)
  const carrito = lineas.reduce((total, linea) => {
    if (!linea.tachado_en) return total
    return total + (precioDeLinea(muestra, linea)?.coste_cent ?? 0)
  }, 0)
  return {
    papel: 'dueno',
    lineas,
    estimacion,
    cotizacion: { sello: `demo-${id}-${carrito}`, total_cent: Math.round(carrito) },
    personas: [{
      usuario: 'medicion',
      nombre: 'Medición',
      papel: 'dueno',
      aceptado_en: '2026-11-15T09:00:00+00:00',
    }],
    novedades: [],
    fecha_datos: FECHA_CATALOGO,
  }
}

/** *La lista partida por tiendas. En la demo no hay nada decidido, así que todo va a
 *  `sin_asignar` con sus opciones; es lo que hace que cada línea enseñe su precio y que el
 *  botón de comparar tenga con qué.* */
export function repartoDe(muestra: Muestra, id: string): RepartoTiendas {
  const lineas = muestra.detalles[id] ?? []
  const sinAsignar: RepartoTiendas['sin_asignar'] = []
  let total = 0
  let sinPrecio = 0
  for (const linea of lineas) {
    const precio = precioDeLinea(muestra, linea)
    if (!precio) {
      sinPrecio += 1
      sinAsignar.push({
        linea_id: linea.id,
        nombre: linea.nombre_visto,
        cantidad: linea.cantidad,
        hay_precio: false,
        mas_barata: null,
        coste_cent: null,
        producto_id: linea.producto_id,
        opciones: [],
        autorizado: false,
        autorizado_producto: null,
        autorizado_cadena: null,
      })
      continue
    }
    total += precio.coste_cent
    sinAsignar.push({
      linea_id: linea.id,
      nombre: linea.nombre_visto,
      cantidad: linea.cantidad,
      hay_precio: true,
      mas_barata: precio.mas_barata,
      coste_cent: precio.coste_cent,
      producto_id: linea.producto_id ?? productoDeGrupo(linea.grupo_id)?.ofertas[0]?.producto_id ?? null,
      opciones: precio.opciones,
      autorizado: false,
      autorizado_producto: null,
      autorizado_cadena: null,
    })
  }

  // *Las cadenas que aparecen en alguna línea, para la comparación de una sola tienda.*
  const cadenas = new Set<string>()
  for (const linea of sinAsignar) for (const o of linea.opciones) cadenas.add(o.cadena)

  const unaTienda: OpcionTienda[] = [...cadenas].map((cadena) => {
    let suyo = 0
    let encontrados = 0
    const faltan: string[] = []
    for (const linea of sinAsignar) {
      const opcion = linea.opciones.find((o) => o.cadena === cadena)
      if (opcion) {
        suyo += opcion.coste_cent
        encontrados += 1
      } else if (linea.hay_precio) {
        faltan.push(linea.nombre)
      }
    }
    return {
      cadena,
      total_cent: Math.round(suyo),
      total_sin_ofertas_cent: Math.round(suyo),
      encontrados,
      faltan,
    }
  }).sort((a, b) => a.total_cent - b.total_cent)

  return {
    sublistas: [],
    sin_asignar: sinAsignar,
    sin_encontrar: [],
    total_cent: Math.round(total),
    total_sin_ofertas_cent: Math.round(total),
    ahorro_cent: 0,
    lineas: lineas.length,
    decididas: 0,
    sin_precio: sinPrecio,
    una_tienda: unaTienda,
    repartido: null,
    fecha_datos: FECHA_CATALOGO,
  }
}

/** *«¿Dónde sale más barata la lista entera?», con los mismos números que el reparto. La demo
 *  no tiene una lista decidida en una tienda, así que `repartido` es `null` y la pantalla
 *  enseña las opciones, que es lo que puede afirmar.* */
export function dondeDe(muestra: Muestra, id: string): Donde {
  const reparto = repartoDe(muestra, id)
  return {
    una_tienda: reparto.una_tienda,
    repartido: null,
    lineas: reparto.lineas,
    fecha_datos: FECHA_CATALOGO,
  }
}

/** *** LA MUESTRA QUE SE SIEMBRA LA PRIMERA VEZ. *** *
 *
 *  *La lista de la semana con ocho productos del catálogo, la lista antigua como estaba, y
 *  dos favoritos para que la pantalla de favoritos no empiece vacía. Todo serializable.*
 */
export function creaMuestra(): Muestra {
  const semana: Lista = {
    id: nuevoId(),
    nombre: 'La semana',
    es_de_casa: true,
    papel: 'dueno',
    lineas: SEMANA.length,
  }
  const casa: Lista = {
    id: nuevoId(),
    nombre: 'La casa (13 nov)',
    es_de_casa: false,
    papel: 'dueno',
    lineas: (LEGADO.detalle?.lineas ?? []).length,
  }

  const lineasSemana: Linea[] = SEMANA.map(({ grupoId, nombre, cantidad }) => {
    const producto = productoDeGrupo(grupoId)
    return {
      id: nuevoId(),
      nombre_visto: nombre,
      cantidad,
      nota: null,
      grupo_id: grupoId,
      producto_id: null,
      tachado_en: null,
      seccion: producto?.seccion,
      pasillo: producto ? NOMBRE_SECCION[producto.seccion] ?? producto.seccion : undefined,
    }
  })

  const legado: Muestra['legado'] = {}
  for (const fila of LEGADO.reparto?.sin_asignar ?? []) {
    legado[fila.linea_id] = {
      coste_cent: fila.coste_cent,
      mas_barata: fila.mas_barata,
      opciones: fila.opciones ?? [],
    }
  }

  return {
    version: VERSION_MUESTRA,
    yo: structuredClone(LEGADO.yo),
    estado: structuredClone(LEGADO.estado),
    listas: [semana, casa],
    detalles: {
      [semana.id]: lineasSemana,
      [casa.id]: (LEGADO.detalle?.lineas ?? []).map((l) => lineaCompleta(l)),
    },
    favoritos: [],
    legado,
  }
}

/** *Añadir una línea. Se guarda el grupo, no el precio: el precio se lee del catálogo cada
 *  vez, así que un cambio de la muestra no deja precios viejos pegados a la lista.* */
export function anadeLinea(
  muestra: Muestra,
  id: string,
  linea: {
    id?: string
    nombre: string
    grupoId: number | null
    productoId: string | null
    cantidad?: number
    nota?: string | null
  },
): Linea {
  const producto = productoDeGrupo(linea.grupoId)
  const nueva: Linea = {
    id: linea.id ?? nuevoId(),
    nombre_visto: linea.nombre,
    cantidad: linea.cantidad ?? 1,
    nota: linea.nota ?? null,
    grupo_id: linea.grupoId,
    producto_id: linea.productoId,
    tachado_en: null,
    seccion: producto?.seccion,
    pasillo: producto ? NOMBRE_SECCION[producto.seccion] ?? producto.seccion : undefined,
  }
  muestra.detalles[id] = [...(muestra.detalles[id] ?? []), nueva]
  const lista = muestra.listas.find((l) => l.id === id)
  if (lista) lista.lineas = muestra.detalles[id].length
  return nueva
}

/** *Cambiar una línea. `borrado` la quita; `tachado`/`en_carrito` la meten o la sacan del
 *  carro; `cantidad` y `nota` se cambian donde se ven.* */
export function cambiaLinea(
  muestra: Muestra,
  id: string,
  lineaId: string,
  cambio: { tachado?: boolean; en_carrito?: boolean; cantidad?: number; nota?: string | null; borrado?: boolean },
): boolean {
  const lineas = muestra.detalles[id] ?? []
  const linea = lineas.find((l) => l.id === lineaId)
  if (!linea) return false
  if (cambio.borrado === true) {
    muestra.detalles[id] = lineas.filter((l) => l.id !== lineaId)
    const lista = muestra.listas.find((l) => l.id === id)
    if (lista) lista.lineas = muestra.detalles[id].length
    return true
  }
  if (typeof cambio.cantidad === 'number') {
    linea.cantidad = Math.max(1, Math.min(99, Math.round(cambio.cantidad)))
  }
  if ('nota' in cambio) linea.nota = cambio.nota ?? null
  if (typeof cambio.tachado === 'boolean' || typeof cambio.en_carrito === 'boolean') {
    const dentro = cambio.tachado === true || cambio.en_carrito === true
    linea.tachado_en = dentro ? new Date().toISOString() : null
  }
  return true
}

export function creaLista(muestra: Muestra, nombre: string, esDeCasa = false): Lista {
  if (esDeCasa) for (const lista of muestra.listas) lista.es_de_casa = false
  const nueva: Lista = { id: nuevoId(), nombre, es_de_casa: esDeCasa, papel: 'dueno', lineas: 0 }
  muestra.listas.push(nueva)
  muestra.detalles[nueva.id] = []
  return nueva
}

export function renombraLista(muestra: Muestra, id: string, nombre: string): boolean {
  const lista = muestra.listas.find((l) => l.id === id)
  if (!lista) return false
  lista.nombre = nombre
  return true
}

export function borraLista(muestra: Muestra, id: string): boolean {
  const antes = muestra.listas.length
  muestra.listas = muestra.listas.filter((l) => l.id !== id)
  delete muestra.detalles[id]
  return muestra.listas.length < antes
}

/** *«He terminado la compra»: lo tachado sale de la lista y queda como compra. En la demo no
 *  hay historial de compras, así que solo se devuelve el recibo de lo que ha salido.* */
export function cierraCompra(muestra: Muestra, id: string) {
  const lineas = muestra.detalles[id] ?? []
  const tachadas = lineas.filter((l) => l.tachado_en !== null)
  const total = tachadas.reduce(
    (suma, linea) => suma + (precioDeLinea(muestra, linea)?.coste_cent ?? 0),
    0,
  )
  muestra.detalles[id] = lineas.filter((l) => l.tachado_en === null)
  const lista = muestra.listas.find((l) => l.id === id)
  if (lista) lista.lineas = muestra.detalles[id].length
  return {
    lineas: tachadas.length,
    total_cent: Math.round(total),
    quedan: muestra.detalles[id].length,
    sin_precio: 0,
    diferencia_cent: null,
  }
}

/** *Un favorito con el estado de hoy. Solo se guarda si el producto está en el catálogo: un
 *  favorito que apunta a nada no se puede enseñar ni comparar.* */
export function anadeFavorito(muestra: Muestra, grupoId: number): boolean {
  const producto = productoDeGrupo(grupoId)
  if (!producto) return false
  if (muestra.favoritos.some((f) => f.grupo_id === grupoId)) return false
  const barata = ofertaMasBarata(producto)
  const favorito: Favorito = {
    grupo_id: producto.grupo_id,
    producto_id: null,
    nombre: producto.nombre,
    cadena: barata?.cadena ?? null,
    unidad: producto.unidad,
    precio_cent: barata?.precio_cent ?? producto.precio_cent,
    precio_unidad_cent: barata?.precio_unidad_cent ?? producto.precio_unidad_cent,
    ahorro_pct: producto.ahorro_pct,
    marca: producto.marca,
    n_cadenas: producto.cadenas,
    comparable: producto.comparable,
    motivo: null,
    variacion_pct: null,
    precio_unidad_antes_cent: null,
    dias_medidos: null,
    dias: 7,
    desconocido: false,
    que: 'grupo',
  }
  muestra.favoritos.push(favorito)
  return true
}

export function quitaFavorito(muestra: Muestra, grupoId: number): boolean {
  const antes = muestra.favoritos.length
  muestra.favoritos = muestra.favoritos.filter((f) => f.grupo_id !== grupoId)
  return muestra.favoritos.length < antes
}

export function misFavoritos(muestra: Muestra, dias = 7) {
  return {
    favoritos: muestra.favoritos.map((f) => ({ ...f, dias })),
    dias,
    fecha_datos: FECHA_CATALOGO,
  }
}
