/** Los contratos de la API, copiados de `docs/API.md` y de `plataforma/api`.
 *
 *  Tres reglas que se ven en los tipos y no son casualidad:
 *
 *  1. Casi todo es `| null`. Un dato que no tenemos es `null`, nunca cero ni
 *     cadena vacia. Si aqui un campo fuera `number`, alguien acabaria pintando
 *     un 0,00 EUR que no es un precio.
 *  2. El dinero va en centimos y en enteros. Los euros se calculan al pintar,
 *     no se guardan.
 *  3. `calidad` y `gama` son excluyentes: la API manda una o la otra, nunca las
 *     dos. Se tipan por separado a proposito, para que sumarlas no sea comodo.
 */

/** La letra de `core/calidad.py`: terciles A/B/C dentro del grupo. */
export type Letra = 'A' | 'B' | 'C'

export type Nutriscore = 'a' | 'b' | 'c' | 'd' | 'e' | string | null

export interface Nutricion {
  /** La cadena publica el kJ, no el kcal: en los datos de hoy `energia_kcal` no
   *  aparece nunca. Se deja escrito porque la tabla de la etiqueta lo busca. */
  energia_kj?: number | null
  energia_kcal?: number | null
  grasas?: number | null
  saturadas?: number | null
  hidratos?: number | null
  azucares?: number | null
  fibra?: number | null
  proteinas?: number | null
  sal?: number | null
  [clave: string]: number | null | undefined
}

/** Una fila de `GET /api/buscar`. Un grupo, con su precio mas bajo. */
export interface ResultadoBusqueda {
  /** El emparejador se lo pone a todo, incluso a grupos de un solo producto,
   *  asi que puede venir null en gold viejo. Lo que hace comparable a un grupo
   *  es `comparable` (dos cadenas o mas), no tener id. */
  grupo_id: number | null
  nombre: string
  /** La marca del miembro **mas barato** del grupo, que es el que la fila
   *  ensena. La API empezo a mandarla el 22 de septiembre de 2026; antes no
   *  estaba y sacarla del nombre seria adivinarla. */
  marca: string | null
  cadena_mas_barata: string | null
  precio_cent: number | null
  precio_unidad_cent: number | null
  precio_unidad_max_cent: number | null
  unidad: string | null
  cadenas: number
  productos: number
  nutriscore: Nutriscore
  imagen: string | null
  con_oferta: boolean
  /** Oferta que solo existe con la tarjeta: no baja lo que pagas en caja. */
  con_oferta_club: boolean
  /** Retirada del mercado. Manda sobre cualquier otra cosa de la fila. */
  con_retirada: boolean
  comparable: boolean
  /** La comparacion no se sostiene (un miembro vale mas del doble que otro en
   *  la misma unidad). Sigue saliendo, pero sin numero de ahorro. */
  dudoso: boolean
  /** 0.0 significa "no comparable" o "dudoso", no "no hay ahorro". */
  ahorro_pct: number
}

/** Un miembro de un grupo, tal como lo manda `GET /api/grupo/{id}`. */
export interface Producto {
  producto_id: string
  fuente: string
  id_fuente: string
  nombre: string
  marca: string | null
  cantidad: number | null
  unidad: string | null
  precio_cent: number | null
  precio_unidad_cent: number | null
  comparable: boolean
  /** Solo si sale de LEER ingredientes. */
  calidad: Letra | null
  /** Solo si sale de ORDENAR por precio. No es calidad, y la interfaz no la
   *  puede llamar asi. */
  gama: Letra | null
  nutriscore: Nutriscore
  nova: number | null
  ean: string | null
  imagen: string | null
  alergenos: string | null
  ingredientes: string | null
  origen: string | null
  promo: string | null
  url: string | null
  sellos: string[]
  /** `certificado` | `etiqueta` | `nombre` | `mixto`. Un certificado auditado y
   *  una palabra en el nombre no valen lo mismo, y se dice en pantalla. */
  sellos_origen: string | null
  certificados: string[]
  conservacion: string | null
  es_marca_propia: boolean | null
  nutricion: Nutricion | null
  nutricion_por: string | null
  envase: string | null
  descripcion: string | null
  tipo_producto: string | null
  dias_caducidad: number | null
  peso_neto_g: number | null
  grado_alcohol: number | null
  promo_hasta: string | null
  promo_club: boolean | null
  es_alcohol: boolean | null
  es_recall: boolean | null
  peso_variacion_pct: number | null
  distintivo: string | null
  advertencias: string[]
  unidades_pack: number | null
}

export interface PuntoSerie {
  /** De que producto del grupo es este punto.
   *
   *  La API lo añadio el 22 de septiembre de 2026 y hace falta de verdad: antes
   *  iba solo `(fuente, fecha)`, y un grupo con dos productos de la misma cadena
   *  daba dos series que empezaban igual y ninguna se podia pintar. Medido ese
   *  dia, hay grupos con 8 productos de 2 cadenas, 6 de ellos de la misma. */
  producto_id: string
  fuente: string
  fecha: string
  precio_unidad_cent: number | null
}

/** Opcional y todavia NO implementado por la API: si algun dia manda la
 *  explicacion del emparejamiento, sale aqui sin tocar nada mas. */
export interface ExplicacionEmparejamiento {
  metodo?: string | null
  motivo?: string | null
  regla?: string | null
  parecido?: number | null
  por?: string | null
  [clave: string]: unknown
}

export interface Grupo {
  grupo_id: number
  nombre: string
  imagen: string | null
  unidad: string | null
  cadenas: number
  ahorro_pct: number
  ahorro_cent: number
  productos: Producto[]
  serie: PuntoSerie[]
  fecha_datos?: string
  /** Campos que la API todavia no manda. Se leen si aparecen. */
  matching?: ExplicacionEmparejamiento | null
  explicacion?: ExplicacionEmparejamiento | string | null
  emparejado_por?: string | null
}

export interface RespuestaBuscar {
  fecha_datos: string
  resultados: ResultadoBusqueda[]
  /** Lo que se ha entendido, cuando lo escrito no encontraba nada y se ha arreglado.
   *
   *  **No viaja `null`**: si no hay correccion, la clave no esta. Y solo llega si la
   *  busqueda corregida **encuentra algo**: anunciar una correccion que no ha servido
   *  de nada seria culpar a quien escribe de un fallo que es nuestro. */
  corregido?: string
}

export interface Seccion {
  seccion: string
  nombre: string
  productos: number
  cadenas: number
  grupos: number
  comparable: boolean
}

export interface RespuestaSecciones {
  fecha_datos: string
  secciones: Seccion[]
}

export interface CadenaEstado {
  cadena: string
  productos: number
  ultimo_dia: string | null
  al_dia: boolean
}

export interface RespuestaEstado {
  fecha_datos: string
  /** Cuantos dias aguanta un precio sin dejar de decidir donde comprar. Hoy 3. */
  dias_precio_valido: number
  cadenas: CadenaEstado[]
}

export interface ComparacionEan {
  fuente: string
  precio_cent: number | null
  precio_unidad_cent: number | null
  diferencia_pct: number | null
}

export interface ProductoEan {
  producto_id: string
  fuente: string
  id_fuente: string
  nombre: string
  marca: string | null
  cantidad: number | null
  unidad: string | null
  precio_cent: number | null
  precio_unidad_cent: number | null
  comparable: boolean
  nutriscore: Nutriscore
}

export interface EanEncontrado {
  encontrado: true
  producto: ProductoEan
  grupo_id: number | null
  /** null = no puedo comparar (el producto solo esta en una cadena). Lista
   *  vacia se leeria como "he mirado y no hay nada mas barato", que no es lo
   *  mismo. */
  comparacion: ComparacionEan[] | null
  nota?: unknown
  fecha_datos: string
}

export interface EanDesconocido {
  encontrado: false
  /** `desconocido` | `sin_ean_en_esa_cadena`. El segundo todavia no se da. */
  motivo: string
  sugerencia: string | null
  fecha_datos: string
}

export type RespuestaEan = EanEncontrado | EanDesconocido

export interface ProductoSuelto {
  producto_id: string
  fuente: string
  grupo_id: number | null
  nombre: string
  marca: string | null
  cantidad: number | null
  unidad: string | null
  precio_cent: number | null
  precio_unidad_cent: number | null
  comparable: boolean
  nutriscore: Nutriscore
}

export interface RespuestaProducto {
  fecha_datos: string
  producto: ProductoSuelto
  /** null cuando el producto no tiene grupo: 32.486 de 51.781 son asi. */
  grupo: Grupo | null
}

export interface Baja {
  grupo_id: number | null
  nombre: string
  marca: string | null
  cadena: string
  imagen: string | null
  unidad: string | null
  precio_cent: number | null
  precio_unidad_cent: number | null
  precio_unidad_antes_cent: number | null
  desde: string | null
  variacion_pct: number
  promo_txt: string | null
  /** La bajada solo existe si tienes la tarjeta. Se ensena, marcada. */
  solo_con_tarjeta: boolean
  precio_antes_cent: number | null
}

export interface RespuestaBajadas {
  fecha_datos: string
  dias: number
  sentido: 'bajadas' | 'subidas'
  resultados: Baja[]
}

// ------------------------------------------------------------------ panel ---

export interface PanelHoy {
  fecha_datos: string
  cadenas: {
    cadena: string
    productos: number
    comparables: number
    con_nutriscore: number
    con_ean: number
  }[]
  movidos: { cadena: string; bajadas: number; subidas: number }[]
  /** Una cadena que entra con muchos menos productos de lo normal. */
  alarmas: { cadena: string; hoy: number; lo_normal: number; caida_pct: number }[]
}

export interface PanelCadenas {
  fecha_datos: string
  mas_barata: { cadena: string; compite_en: number; gana: number; pct: number }[]
  movimiento: {
    cadena: string
    observaciones: number
    movidos: number
    pct: number
    mediana_cent: number
  }[]
  dispersion: {
    grupos: number
    mediana_pct: number
    p90_pct: number
    sospechosos: number
  }
}

export interface PanelMarcas {
  fecha_datos: string
  grupos_con_ambas: number
  media_propia_cent: number
  media_marca_cent: number
  ahorro_pct: number
  calidad_origen: { origen: string; productos: number }[]
  /** Hay que ensenarlo SIEMPRE: sin el, el estudio se lee al reves. */
  aviso: string
  duelo: { grupos: number; gana_propia: number; empatan: number; gana_marca: number }
  marcas_propias: { cadena: string; marca: string; productos: number }[]
}

export interface PanelHistorico {
  fecha_datos: string
  dias: number
  serie: { fecha: string; observaciones: number; cadenas: number }[]
  pendientes: { que: string; necesita: number; faltan: number; para: string }[]
}

export interface PanelMovidos {
  fecha_datos: string
  movidos: {
    cadena: string
    nombre: string
    marca: string | null
    unidad: string | null
    grupo_id: number | null
    precio_unidad_cent: number | null
    variacion_cent: number
    baja: boolean
  }[]
}

// ------------------------------------------------- el panel de matching ---

/** Una metrica de la pasada: nombre y valor. Los nombres los pone
 *  `core/matching.py` y la interfaz los enseña tal cual, sin traducirlos: si
 *  se renombra una metrica, se entera quien la lee. */
export interface MetricaMatching {
  metrica: string
  valor: number
}

/** Lo que ha cambiado respecto a la pasada anterior. `antes` es null si la
 *  metrica es nueva, y eso **no es un cero**: significa que antes no se medía. */
export interface CambioMatching {
  metrica: string
  antes: number | null
  ahora: number | null
  delta: number
}

export interface ParMatching {
  producto_a: string
  producto_b: string
  nombre_a: string | null
  nombre_b: string | null
  fuente_a: string
  fuente_b: string
  /** `identico` (mismo EAN), `equivalente` (mismo tipo y formato, otra marca). */
  nivel: string | null
  metodo: string | null
  confianza: number | null
  /** Los rasgos que hicieron aceptar el par. Es la explicabilidad del encargo. */
  features: Record<string, unknown>
}

export interface PanelMatching {
  fecha_datos: string
  /** null cuando todavía no hay ninguna pasada guardada en gold. */
  ultima: {
    ejecucion_id: string
    version_modelo?: string | null
    productos?: number | null
    umbral?: number | null
    huella_catalogo?: string | null
  } | null
  metricas: MetricaMatching[]
  anterior: { ejecucion_id: string } | null
  cambios: CambioMatching[] | null
  pares: ParMatching[]
  ejecuciones: string[]
}

/* ------------------------------------------------------------ la cesta --- */

/** Quien ha entrado. `null` = nadie. */
export interface Sesion {
  usuario: { id: string; usuario: string; nombre: string | null } | null
  preferencias: Record<string, unknown>
}

/** Una lista de la compra. */
export interface Lista {
  id: string
  nombre: string
  es_de_casa: boolean
  papel?: string
  lineas?: number
  actualizada?: string
}

/** Una linea de la lista: lo que se quiere comprar. */
export interface Linea {
  id: string
  nombre_visto: string
  cantidad: number
  grupo_id: number | null
  producto_id: string | null
  tachado_en: string | null
  /** El pasillo, y donde cae en el recorrido de la tienda.
   *
   *  **Opcionales a proposito**: mientras gold no traiga la columna `seccion`, o
   *  cuando el grupo no esta en gold, no vienen -- y entonces la lista se pinta
   *  como siempre, de un tiron y sin encabezados. La pantalla distingue "no lo se"
   *  (la clave no esta) de "es de este pasillo", que es la regla del proyecto: un
   *  dato que no tenemos no se rellena. */
  seccion?: string
  pasillo?: string
  pasillo_orden?: number
}

/** Una tarjeta del mosaico de lo habitual.
 *
 *  **`origen` viaja en cada tarjeta** y no una vez por respuesta: una cuadricula
 *  puede tener cosas tuyas y cosas de la compra basica a la vez, y no valen lo
 *  mismo. Sin ese campo, la pantalla ensenaria "lo que sueles comprar" con lo que
 *  compra otro. */
export interface Habitual {
  grupo_id: number
  nombre: string
  /** No viaja si no hay foto: la pantalla sabe dibujar su hueco. */
  imagen?: string
  precio_unidad_cent: number
  unidad: string | null
  cadena_mas_barata: string | null
  fiable: boolean
  origen: 'tuyo' | 'de todos' | 'basico'
  /** Solo en las de `tuyo`: son la historia de esta persona. */
  veces?: number
  ultima_vez?: string
}

export interface RespuestaHabituales {
  /** Los escalones que han entrado, para poder explicar el mosaico. */
  origenes: string[]
  habituales: Habitual[]
  fecha_datos: string
}

/** Una alerta de precio, tal cual la guarda la API.
 *
 *  **`salto_en` y `vista_en` son dos relojes distintos**: `salto_en` es cuando se
 *  cumplio la condicion -- lo pone el vigilante de la API en cuanto cambia gold, sin
 *  que nadie abra nada -- y `vista_en` es cuando esta persona lo ha visto. La pantalla
 *  no los puede confundir: el punto de "sin ver" es `vista_en`, y la fecha que se
 *  ensena es `salto_en`. */
export interface Alerta {
  id: string
  grupo_id: number
  tipo: 'baja_de' | 'minimo_90d' | 'cualquier_bajada'
  umbral_cent: number | null
  creada_en: string
  vista_en: string | null
  salto_en: string | null
  /** La frase, guardada cuando salto: se mide contra el gold de ese dia. */
  salto_texto: string | null
  /** La tarjeta del grupo, que la API anade en `GET /api/alertas`.
   *
   *  Sin el nombre, la pantalla solo puede decir "producto", y un aviso que no dice
   *  **de que** producto es no es un aviso. Si el grupo ya no esta en el catalogo no
   *  llegan: entonces no hay nombre que poner y la pantalla lo dice. */
  nombre?: string
  imagen?: string
  precio_unidad_cent?: number
  unidad?: string | null
  cadena_mas_barata?: string | null
  fiable?: boolean
}

/** Una alerta que se cumple **hoy**, con la frase que la explica. */
export interface AlertaQueSalta {
  grupo_id: number
  nombre: string
  cadena: string
  unidad: string | null
  precio_unidad_cent: number
  alerta_id: string
  tipo: string
  por_que: string
}

export interface RespuestaAlertas {
  fecha_datos: string
  alertas: Alerta[]
  saltan: AlertaQueSalta[]
}

/** Lo que cuesta la lista ahora mismo, en la cadena mas barata de cada cosa. */
export interface Estimacion {
  total_cent: number
  en_carrito_cent: number
  por_recoger_cent: number
  lineas: number
  sin_precio: number
}

/** Lo que costaria la lista entera en UNA cadena. */
export interface OpcionTienda {
  cadena: string
  total_cent: number
  total_sin_ofertas_cent: number
  encontrados: number
  /** Los que no tiene, POR SU NOMBRE. Un numero no dice cual falta. */
  faltan: string[]
}

/** Repartir la compra entre varias tiendas. */
export interface Reparto {
  cadenas: string[]
  total_cent: number
  faltan: string[]
  ahorro_cent?: number
  /** Con ahorros de menos de 1,50 EUR no compensa la segunda parada. */
  merece_la_pena?: boolean
  /** Cuantas lineas de la lista se compran en cada cadena, por nombre:
   *  `{ alcampo: 7, dia: 3 }`. Son LINEAS, no unidades: "3 en dia" son tres
   *  cosas que coger, aunque una sea "2 botes".
   *
   *  Es lo que hace planificable el reparto: con el total y el ahorro solos no
   *  se sabe si la segunda parada es por una cosa o por veinte. La API lo manda
   *  desde siempre (`plataforma/api/cesta.py:195`) y la interfaz vieja lo
   *  enseñaba (`app.js:718`).
   *
   *  Opcional a proposito: la interfaz no puede dar por hecho que la API que le
   *  contesta traiga el campo, y un reparto sin desglose se enseña sin cuentas
   *  en vez de inventarselas. */
  reparto?: Record<string, number>
}

export interface Donde {
  una_tienda: OpcionTienda[]
  repartido: Reparto | null
  lineas: number
  fecha_datos: string
}
/** Un favorito. La lista viene mezclada: los guardados por GRUPO traen el
 *  resumen del grupo, y los guardados por PRODUCTO traen la ficha del producto.
 *  Por eso casi todo es opcional: se pinta lo que venga, sin inventar el resto. */
export interface Favorito {
  grupo_id: number | null
  producto_id?: string | null
  nombre: string
  /** En los de grupo, la cadena mas barata de hoy. */
  cadena?: string
  fuente?: string
  unidad?: string | null
  precio_unidad_cent?: number | null
  ahorro_pct?: number
  marca?: string | null
}