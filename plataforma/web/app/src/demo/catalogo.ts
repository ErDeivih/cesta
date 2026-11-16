/** *** EL CATÁLOGO REAL DE LA DEMO, Y LAS CONSULTAS QUE SE HACEN SOBRE ÉL. *** *
 *
 *  *El JSON lo genera `scripts/genera-catalogo-demo.py` desde gold (la captura del
 *  15/11/2026): 99 grupos con sus precios, su unidad, su supermercado y su imagen. No se
 *  escribe a mano y no se inventa nada.*
 *
 *  *** POR QUÉ ESTO VIVE APARTE DE `api.ts`. *** *
 *
 *  *`api.ts` es el parche de `fetch`: habla HTTP, guarda el estado y atiende las rutas.
 *  Esto es lo que se puede probar sin navegador — buscar, filtrar, comparar — y por eso
 *  está separado: las pruebas de `catalogo.test.ts` lo llaman directamente, sin montar una
 *  página ni una API de mentira.*
 *
 *  *La regla de búsqueda es la misma que la de la app: cada palabra tiene que empezar una
 *  palabra del nombre. Así «pan» no encuentra «filetes empanados», que es el fallo clásico
 *  de un `includes` a secas.*
 */
import datos from './catalogo.json'

import type {
  Grupo,
  Producto,
  ProductoSuelto,
  RespuestaBuscar,
  RespuestaHabituales,
  RespuestaProducto,
  RespuestaSecciones,
  ResultadoBusqueda,
} from '../tipos'

export interface OfertaCatalogo {
  cadena: string
  producto_id: string
  id_fuente: string
  nombre: string
  marca: string | null
  precio_cent: number
  precio_unidad_cent: number
  unidad: string
  imagen: string
  oferta: boolean
  promocion: string | null
  es_marca_propia: boolean
}

export interface ProductoCatalogo {
  grupo_id: number
  nombre: string
  marca: string | null
  imagen: string
  unidad: string
  seccion: string
  categoria: string | null
  precio_cent: number
  precio_unidad_cent: number
  precio_unidad_max_cent: number
  cadenas: number
  productos: number
  ahorro_pct: number
  comparable: boolean
  dudoso: boolean
  ofertas: OfertaCatalogo[]
}

const DATOS = datos as unknown as {
  fecha_datos: string
  fuente: string
  productos: ProductoCatalogo[]
}

export const CATALOGO: ProductoCatalogo[] = DATOS.productos
export const FECHA_CATALOGO: string = DATOS.fecha_datos

/** *El nombre legible de un pasillo. La API manda un código y la pantalla lo traduce;
 *  aquí se hace lo mismo, en un solo sitio, para que el filtro y el resultado digan lo
 *  mismo.* */
export const NOMBRE_SECCION: Record<string, string> = {
  despensa: 'Despensa',
  'lacteos-huevos': 'Lácteos y huevos',
  carniceria: 'Carnicería',
  pescaderia: 'Pescadería',
  'frutas-verduras': 'Frutas y verduras',
  panaderia: 'Panadería',
  'desayuno-dulces': 'Desayuno y dulces',
  bebidas: 'Bebidas',
  'droguería-limpieza': 'Droguería y limpieza',
  congelados: 'Congelados',
  aperitivos: 'Aperitivos',
  preparados: 'Preparados',
}

export interface OpcionesBusqueda {
  q?: string
  cadenas?: string[]
  seccion?: string
  comparables?: boolean
  ofertas?: boolean
  marcaPropia?: boolean
  sinAlcohol?: boolean
  conNutricion?: boolean
  sellos?: string[]
  conservacion?: string
  limite?: number
  desplazamiento?: number
}

/** *Minúsculas, sin tildes y con todo lo que no sea letra o número convertido en espacio.
 *  La misma normalización para el nombre y para lo que se teclea: si no, «atún» y «atun»
 *  serían dos búsquedas distintas.* */
export function normaliza(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function escapa(token: string): string {
  return token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** *¿Empieza alguna palabra del texto por esta? El `(?:^| )` es lo que evita que «pan»
 *  case dentro de «empanados»: se busca el principio de una palabra, no un trozo.* */
function empiezaPalabra(heno: string, aguja: string): boolean {
  return new RegExp(`(?:^| )${escapa(aguja)}`).test(heno)
}

/** *Las ofertas que quedan al aplicar el filtro de cadena. Si no se filtra, todas.* */
function ofertasDe(producto: ProductoCatalogo, cadenas: string[]): OfertaCatalogo[] {
  if (cadenas.length === 0) return producto.ofertas
  const pedidas = new Set(cadenas)
  return producto.ofertas.filter((o) => pedidas.has(o.cadena))
}

/** *Una fila de `/api/buscar` a partir del producto y de las ofertas que han sobrevivido
 *  al filtro. El precio que se enseña es **el de la cadena más barata de las que se
 *  miran**, no el global: si se ha filtrado a DIA, el precio tiene que ser el de DIA.* */
function filaDe(producto: ProductoCatalogo, ofertas: OfertaCatalogo[]): ResultadoBusqueda {
  const ordenadas = [...ofertas].sort(
    (a, b) => a.precio_unidad_cent - b.precio_unidad_cent,
  )
  const barata = ordenadas[0]
  const maximo = ordenadas[ordenadas.length - 1]
  const unidades = ordenadas.map((o) => o.precio_unidad_cent)
  const minimoUnidad = Math.min(...unidades)
  const maximoUnidad = Math.max(...unidades)
  const comparables = ordenadas.length >= 2 && !producto.dudoso
  return {
    grupo_id: producto.grupo_id,
    nombre: barata.nombre,
    marca: barata.marca,
    cadena_mas_barata: barata.cadena,
    precio_cent: barata.precio_cent,
    precio_unidad_cent: barata.precio_unidad_cent,
    precio_unidad_max_cent: maximo.precio_unidad_cent,
    unidad: barata.unidad,
    cadenas: new Set(ordenadas.map((o) => o.cadena)).size,
    productos: ordenadas.length,
    nutriscore: null,
    imagen: barata.imagen ?? producto.imagen,
    ecoscore: null,
    kcal_100g: null,
    hidratos_100g: null,
    proteinas_100g: null,
    grasas_100g: null,
    grasas_sat_100g: null,
    azucares_100g: null,
    sal_100g: null,
    con_oferta: ordenadas.some((o) => o.oferta),
    con_oferta_club: false,
    oferta_unidades: null,
    con_retirada: false,
    comparable: comparables,
    dudoso: producto.dudoso,
    ahorro_pct: comparables && maximoUnidad > 0
      ? Math.round(((maximoUnidad - minimoUnidad) / maximoUnidad) * 1000) / 10
      : 0,
  }
}

/** *** BUSCAR: lo que hace que la demo sirva sin backend. *** *
 *
 *  *Misma forma que `GET /api/buscar`: `{ fecha_datos, resultados }`. Los filtros son los
 *  de la pantalla y se aplican aquí, no en el componente, porque el componente ya está
 *  probado contra la API y no hay que tocarlo.*
 */
export function buscaCatalogo(opciones: OpcionesBusqueda = {}): RespuestaBuscar {
  const cadenas = opciones.cadenas ?? []
  const limite = Number.isFinite(opciones.limite) ? Number(opciones.limite) : 40
  const desplazamiento = Math.max(0, Number(opciones.desplazamiento ?? 0) || 0)

  const agujas = normaliza(opciones.q ?? '').split(' ').filter(Boolean)
  const hayTexto = agujas.length > 0
  const hayPasillo = Boolean(opciones.seccion)
  if (!hayTexto && !hayPasillo) {
    return { fecha_datos: FECHA_CATALOGO, resultados: [] }
  }

  const filas: ResultadoBusqueda[] = []
  for (const producto of CATALOGO) {
    if (opciones.seccion && producto.seccion !== opciones.seccion) continue

    const heno = normaliza(`${producto.nombre} ${producto.marca ?? ''}`)
    if (hayTexto && !agujas.every((a) => empiezaPalabra(heno, a))) continue

    const ofertas = ofertasDe(producto, cadenas)
    if (ofertas.length === 0) continue
    if (opciones.comparables && new Set(ofertas.map((o) => o.cadena)).size < 2) continue
    if (opciones.ofertas && !ofertas.some((o) => o.oferta)) continue
    if (opciones.marcaPropia && !ofertas.some((o) => o.es_marca_propia)) continue
    // *Sin alcohol y con nutrición no tienen dato en este catálogo: si se piden, no se
    // puede afirmar que el producto los cumpla, así que no se enseña. Callarlo sería
    // mentir con un filtro puesto.*
    if (opciones.sinAlcohol || opciones.conNutricion) continue
    if ((opciones.sellos?.length ?? 0) > 0 || opciones.conservacion) continue

    filas.push(filaDe(producto, ofertas))
  }

  // *Primero lo comparable —que es lo que la app existe para contestar— y dentro, lo más
  // barato por unidad. El nombre desempata para que dos visitas den el mismo orden.*
  filas.sort((a, b) => {
    if (a.comparable !== b.comparable) return a.comparable ? -1 : 1
    const precioA = a.precio_unidad_cent ?? Number.POSITIVE_INFINITY
    const precioB = b.precio_unidad_cent ?? Number.POSITIVE_INFINITY
    if (precioA !== precioB) return precioA - precioB
    return a.nombre.localeCompare(b.nombre, 'es')
  })

  return {
    fecha_datos: FECHA_CATALOGO,
    resultados: filas.slice(desplazamiento, desplazamiento + limite),
  }
}

/** *Un miembro del grupo con la forma que espera `Grupo`. Los campos que el catálogo de la
 *  demo no trae van a `null` —que es «no lo sé», no cero— y no se inventan.* */
function productoDeOferta(oferta: OfertaCatalogo): Producto {
  return {
    producto_id: oferta.producto_id,
    fuente: oferta.cadena,
    id_fuente: oferta.id_fuente,
    nombre: oferta.nombre,
    marca: oferta.marca,
    cantidad: null,
    unidad: oferta.unidad,
    precio_cent: oferta.precio_cent,
    precio_unidad_cent: oferta.precio_unidad_cent,
    comparable: true,
    calidad: null,
    calidad_de: null,
    gama: null,
    nutriscore: null,
    nova: null,
    ecoscore: null,
    kcal_100g: null,
    hidratos_100g: null,
    proteinas_100g: null,
    grasas_100g: null,
    grasas_sat_100g: null,
    azucares_100g: null,
    sal_100g: null,
    ean: null,
    imagen: oferta.imagen,
    alergenos: null,
    ingredientes: null,
    origen: null,
    promo: oferta.promocion,
    url: null,
    sellos: [],
    sellos_origen: null,
    certificados: [],
    conservacion: null,
    es_marca_propia: oferta.es_marca_propia,
    nutricion: null,
    nutricion_por: null,
    envase: null,
    descripcion: null,
    tipo_producto: null,
    dias_caducidad: null,
    peso_neto_g: null,
    grado_alcohol: null,
    promo_hasta: null,
    promo_club: false,
    promo_unidades: null,
    es_alcohol: false,
    es_recall: false,
    peso_variacion_pct: null,
    distintivo: null,
    advertencias: [],
    unidades_pack: null,
  }
}

/** *** LA COMPARACIÓN: EL MISMO PRODUCTO, CADA CADENA Y SU PRECIO. *** *
 *
 *  *Devuelve la forma de `GET /api/grupo/{id}`, que es la que ya pinta
 *  `OfertasDelProducto` y la ficha. `ahorro_cent` va en céntimos **por unidad** (lo que
 *  resta la pantalla es un precio por kilo o por litro), no el total de la compra.*
 */
export function grupoDelCatalogo(grupoId: number): Grupo | null {
  const producto = CATALOGO.find((p) => p.grupo_id === grupoId)
  if (!producto) return null
  const ofertas = [...producto.ofertas].sort(
    (a, b) => a.precio_unidad_cent - b.precio_unidad_cent,
  )
  const unidades = ofertas.map((o) => o.precio_unidad_cent)
  const minimo = Math.min(...unidades)
  const maximo = Math.max(...unidades)
  return {
    grupo_id: producto.grupo_id,
    nombre: producto.nombre,
    imagen: producto.imagen,
    unidad: producto.unidad,
    cadenas: new Set(ofertas.map((o) => o.cadena)).size,
    ahorro_pct: maximo > 0 ? Math.round(((maximo - minimo) / maximo) * 1000) / 10 : 0,
    ahorro_cent: Math.round((maximo - minimo) * 100) / 100,
    productos: ofertas.map(productoDeOferta),
    serie: [],
    fecha_datos: FECHA_CATALOGO,
  }
}

/** *La ficha de un producto suelto: la que se abre desde el nombre o desde el escáner. La
 *  demo no tiene EAN, así que el escáner no la usa; el enlace del resultado sí.* */
export function productoDelCatalogo(fuente: string, idFuente: string): RespuestaProducto | null {
  for (const producto of CATALOGO) {
    const oferta = producto.ofertas.find(
      (o) => o.cadena === fuente && o.id_fuente === idFuente,
    )
    if (!oferta) continue
    const suelto: ProductoSuelto = {
      ecoscore: null,
      kcal_100g: null,
      hidratos_100g: null,
      proteinas_100g: null,
      grasas_100g: null,
      grasas_sat_100g: null,
      azucares_100g: null,
      sal_100g: null,
      producto_id: oferta.producto_id,
      fuente: oferta.cadena,
      grupo_id: producto.grupo_id,
      nombre: oferta.nombre,
      marca: oferta.marca,
      cantidad: null,
      unidad: oferta.unidad,
      precio_cent: oferta.precio_cent,
      precio_unidad_cent: oferta.precio_unidad_cent,
      comparable: true,
      nutriscore: null,
    }
    return {
      fecha_datos: FECHA_CATALOGO,
      producto: suelto,
      grupo: grupoDelCatalogo(producto.grupo_id),
    }
  }
  return null
}

/** *«Lo de siempre» del mosaico: un producto por pasillo, para que la primera pantalla
 *  enseñe la compra entera y no siete leches. El orden de los pasillos es el de la
 *  compra: despensa, frescos, pan, desayuno.* */
export function habitualesDelCatalogo(limite = 12): RespuestaHabituales {
  const porSeccion = new Map<string, ProductoCatalogo[]>()
  for (const producto of CATALOGO) {
    const lista = porSeccion.get(producto.seccion) ?? []
    lista.push(producto)
    porSeccion.set(producto.seccion, lista)
  }
  const orden = [
    'despensa',
    'lacteos-huevos',
    'carniceria',
    'pescaderia',
    'frutas-verduras',
    'panaderia',
    'desayuno-dulces',
    'bebidas',
    'congelados',
    'droguería-limpieza',
    'aperitivos',
  ]
  const habituales: RespuestaHabituales['habituales'] = []
  let vuelta = 0
  while (habituales.length < limite) {
    let anadido = false
    for (const seccion of orden) {
      const lista = porSeccion.get(seccion) ?? []
      const producto = lista[vuelta]
      if (!producto) continue
      habituales.push({
        grupo_id: producto.grupo_id,
        nombre: producto.nombre,
        imagen: producto.imagen,
        precio_unidad_cent: producto.precio_unidad_cent,
        unidad: producto.unidad,
        cadena_mas_barata: producto.ofertas[0]?.cadena ?? null,
        fiable: true,
        origen: 'basico',
      })
      anadido = true
      if (habituales.length >= limite) break
    }
    if (!anadido) break
    vuelta += 1
  }
  return { origenes: ['basico'], habituales, fecha_datos: FECHA_CATALOGO }
}

/** *Los pasillos que tienen algo, con su cuenta. La API los usa para el filtro; la demo,
 *  para que el desplegable no enseñe pasillos vacíos.* */
export function seccionesDelCatalogo(): RespuestaSecciones {
  const porSeccion = new Map<string, { productos: number; cadenas: Set<string> }>()
  for (const producto of CATALOGO) {
    const actual = porSeccion.get(producto.seccion) ?? { productos: 0, cadenas: new Set() }
    actual.productos += 1
    for (const oferta of producto.ofertas) actual.cadenas.add(oferta.cadena)
    porSeccion.set(producto.seccion, actual)
  }
  return {
    fecha_datos: FECHA_CATALOGO,
    secciones: [...porSeccion.entries()]
      .map(([seccion, datos]) => ({
        seccion,
        nombre: NOMBRE_SECCION[seccion] ?? seccion,
        productos: datos.productos,
        cadenas: datos.cadenas.size,
        grupos: datos.productos,
        comparable: datos.productos > 1,
      }))
      .sort((a, b) => b.productos - a.productos),
  }
}

/** *Las cadenas que tienen oferta en el catálogo, para el filtro y la cabecera. El orden es
 *  el de la app (las cinco de siempre) y no el alfabético.* */
export function cadenasDelCatalogo(): string[] {
  const orden = ['alcampo', 'carrefour', 'dia', 'mercadona', 'aldi', 'lidl']
  const dentro = new Set<string>()
  for (const producto of CATALOGO) {
    for (const oferta of producto.ofertas) dentro.add(oferta.cadena)
  }
  return [...orden.filter((c) => dentro.has(c)), ...[...dentro].filter((c) => !orden.includes(c)).sort()]
}
