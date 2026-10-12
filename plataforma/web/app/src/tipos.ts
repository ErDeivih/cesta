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
  /** Eco-Score de Open Food Facts: de `a` a `f`, mas `a-plus` y `not-applicable`. */
  ecoscore: string | null
  /** Nutrientes por 100 g, de Open Food Facts. Null es "no lo sabemos", nunca cero. */
  kcal_100g: number | null
  hidratos_100g: number | null
  proteinas_100g: number | null
  grasas_100g: number | null
  grasas_sat_100g: number | null
  azucares_100g: number | null
  sal_100g: number | null
  con_oferta: boolean
  /** Oferta que solo existe con la tarjeta: no baja lo que pagas en caja. */
  con_oferta_club: boolean
  /** Cuántas unidades exige la mecánica de la oferta, cuando la cadena lo dice en número
   *  (Alcampo, 1.639 productos). «Oferta» a secas se lee como «más barata hoy», y una oferta
   *  de «2ª unidad −50 %» no es el precio de una. `null` cuando no exige más de una. */
  oferta_unidades?: number | null
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
  /** Eco-Score de Open Food Facts: de `a` a `f`, mas `a-plus` y `not-applicable`. */
  ecoscore: string | null
  /** Nutrientes por 100 g, de Open Food Facts. Null es "no lo sabemos", nunca cero. */
  kcal_100g: number | null
  hidratos_100g: number | null
  proteinas_100g: number | null
  grasas_100g: number | null
  grasas_sat_100g: number | null
  azucares_100g: number | null
  sal_100g: number | null
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
  /** El peso escurrido (sin el líquido de cobertura), cuando la cadena lo publica.
   *
   *  Solo Mercadona, en 179 conservas y tarros. **Es el peso sobre el que se calcula el
   *  precio por kilo cuando existe**, porque es lo que se come y porque es la base que usan
   *  las otras cadenas: la ventresca de Mercadona declara 111 g y dice que el escurrido son
   *  78 g, y Alcampo, Carrefour y DIA venden la misma lata declarando 73 g. Medido el 26 de
   *  septiembre de 2026 (`projects.cesta.auditar_escurrido`): dividiendo por lo declarado,
   *  Mercadona salía en el 59 % de la mediana de las otras cadenas (1 de 18 grupos dentro del
   *  20 %); por el escurrido, en el 98 % (13 de 18). Y cuesta 3,1 puntos de acuerdo con la
   *  ficha de la propia Mercadona, que calcula su referencia sobre lo declarado. */
  peso_escurrido_g?: number | null
  /** Si el precio por unidad de esta fila va sobre el escurrido. Lo dice la API, que es
   *  quien hizo la cuenta: la interfaz no lo deduce, solo lo enseña. */
  precio_por_escurrido?: boolean
  grado_alcohol: number | null
  promo_hasta: string | null
  promo_club: boolean | null
  /** Cuántas unidades exige la mecánica de la oferta (Alcampo lo publica en número). La ficha
   *  lo dice porque es una condición del precio: «2ª unidad −50 %» no es el precio de una. */
  promo_unidades?: number | null
  /** **Viaja y no se pinta, y está mirado** (`data/debug/campos_sin_pintar.py`): el buscador
   *  tiene el filtro «Sin alcohol» y la ficha enseña el grado (`grado_alcohol`), que dice más
   *  que el booleano. El booleano decide el filtro y nada mas. */
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
  /** Con que unidad se midio ESE dia, si la API la manda.
   *
   *  La API lo añadio el 23 de septiembre de 2026, para la frase de debajo de la
   *  curva: sin la unidad no se puede decir "es el mas bajo de los N dias que
   *  tenemos" -- si la unidad cambio por el camino, ese minimo no significa nada, y
   *  es la misma regla que ya aplican las alertas ("si la unidad cambio, no es una
   *  bajada"). Se lee como opcional: una API mas vieja no lo manda y entonces no hay
   *  frase, que es lo honesto. */
  unidad_canon?: string | null
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
  version_catalogo?: string | null
  vigencia_precio?: {
    comprobable: boolean
    coherente: boolean | null
    motivo?: string | null
  }
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
  /** Eco-Score de Open Food Facts: de `a` a `f`, mas `a-plus` y `not-applicable`. */
  ecoscore: string | null
  /** Nutrientes por 100 g, de Open Food Facts. Null es "no lo sabemos", nunca cero. */
  kcal_100g: number | null
  hidratos_100g: number | null
  proteinas_100g: number | null
  grasas_100g: number | null
  grasas_sat_100g: number | null
  azucares_100g: number | null
  sal_100g: number | null
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
  /** El peso escurrido y si el precio por unidad va sobre él. Ver `ProductoDelGrupo`. */
  peso_escurrido_g?: number | null
  precio_por_escurrido?: boolean
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
  /** **Viaja y no se pinta, y está mirado**: es el precio **de venta** de antes, y el panel
   *  enseña el **precio por unidad** antes y después, que es lo comparable entre formatos. */
  precio_antes_cent: number | null
}

export interface RespuestaBajadas {
  fecha_datos: string
  dias: number
  sentido: 'bajadas' | 'subidas'
  /** **Lo que el servidor ha hecho, no lo que se le pidio.**
   *
   *  Sin sesion no hay "lo mio" que filtrar, asi que la peticion se queda sin efecto y
   *  esto llega `false` aunque se haya pedido `solo_mios=true`. La pantalla tiene que
   *  decir el titulo por este campo: con lo pedido, ensenaria el catalogo entero bajo
   *  el titulo "Lo tuyo que ha bajado". */
  solo_mios: boolean
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

/** `GET /api/indice` — el nivel de precios de cada cadena, base 100.
 *
 *  Cada eslabon compara **el mismo producto consigo mismo** contra la captura
 *  anterior de esa cadena, asi que el indice no se mueve porque cambie el
 *  surtido. Es la diferencia entre "ha subido el nivel de precios" y "han
 *  entrado productos mas caros", que es lo que mide una cesta fija mal hecha.
 */
export interface PuntoIndice {
  fecha: string
  indice: number
  variacion_pct: number
  /** Cuantos productos sostienen este eslabon. Sin esto, un indice es un numero suelto. */
  productos: number
  dias_del_salto: number
  /** Relativos fuera del recorte: el eslabon no los usa, y hay que decirlo. */
  recortados: number
}

export interface SerieIndice {
  cadena: string
  indice: number
  variacion_pct: number
  capturas: number
  puntos: PuntoIndice[]
}

export interface RespuestaIndice {
  fecha_datos: string
  base: string
  metodo: string
  series: SerieIndice[]
}

/** `GET /api/posicion` — en que es cara cada cadena, seccion a seccion.
 *
 *  No es "quien es mas barato": una cadena puede ir un 20 % por debajo en
 *  lacteos y un 25 % por encima en pescaderia, y la media de las dos no se
 *  parece a ninguna. `desvio_pct` es la mediana del desvio de cada producto
 *  respecto a la mediana de **las otras** cadenas de su grupo comparable.
 */
export interface RespuestaPosicion {
  fecha_datos: string
  medida: string
  secciones: {
    seccion: string
    productos: number
    cadenas: { cadena: string; productos: number; desvio_pct: number }[]
  }[]
}

/** `GET /api/ofertas-dudosas` — ofertas anunciadas que el historico no sostiene.
 *
 *  `por_que` es la respuesta, no un adorno: viene calculada de los datos
 *  (`movimientos._por_que`) y es lo primero que se lee.
 */
export interface OfertaDudosa {
  grupo_id: number | null
  nombre: string
  marca: string | null
  cadena: string
  imagen: string | null
  promo_txt: string | null
  /** La unidad de `precio_unidad_cent`: "kg", "l" o "ud". Sin ella, un 1,29 €
   *  se lee como el precio del envase y no lo es. */
  unidad: string | null
  precio_unidad_cent: number | null
  precio_base_cent: number | null
  /** 0 = el mas barato de sus 90 dias, 1 = el mas caro. */
  posicion_90d: number | null
  min_90d_cent: number | null
  max_90d_cent: number | null
  solo_con_tarjeta: boolean
  por_que: string
}

/** Lo que **no se puede juzgar** con el precio de una unidad, contado por motivo.
 *
 *  Un 3x2 no baja el precio de una unidad, baja el de la tercera: acusarlo sería un
 *  error de la pantalla, no una mentira de la cadena. Y "Stock Fuera" no es una
 *  oferta, es una etiqueta. Se cuentan y se dicen, porque esconderlos haría parecer
 *  que la lista está completa. */
export interface OfertasSinPoderJuzgar {
  por_varias_unidades: number
  sin_descuento_de_precio: number
  /** El tamaño declarado cambió dentro de la ventana que se compara. */
  cantidad_cambiada: number
  total: number
}

export interface RespuestaOfertasDudosas {
  fecha_datos: string
  resultados: OfertaDudosa[]
  sin_poder_juzgar: OfertasSinPoderJuzgar
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
  /** **Viaja y no se pinta, y está mirado**: cuándo se tocó por última vez. El desplegable
   *  enseña el nombre y cuántas líneas tiene, que es lo que decide con cuál se trabaja; una
   *  fecha ahí no cambia ninguna decisión. */
  actualizada?: string
}

/** Una linea de la lista: lo que se quiere comprar. */
export interface Linea {  id: string
  nombre_visto: string
  cantidad: number
  /** Lo que se apunta en el pasillo cuando el nombre no basta («2 bricks de los grandes»).
   *
   *  El campo existe en la base desde el primer dia (`lista_linea.nota`) y **no lo pintaba
   *  ninguna pantalla** hasta el 30 de septiembre de 2026: llegaba en la respuesta y se
   *  tiraba. Es el mismo tipo de hueco que `novedades` y que el orden de los favoritos. */
  nota?: string | null
  grupo_id: number | null
  producto_id: string | null
  tachado_en: string | null
  /** El grupo al que apunta esta linea **ya no es** el producto que dice el nombre.
   *
   *  El emparejador numera los grupos en el orden en que aparecen los productos, asi
   *  que una pasada puede renumerarlos y una linea guardada acaba apuntando a otra
   *  cosa (medido el 28 de septiembre de 2026: «Leche entera» con el precio de una
   *  barra de labios). Cuando pasa, la API no la cuenta ni la reparte
   *  (`catalogo.lineas_movidas`) y la pantalla lo dice con una salida: volver a
   *  buscarla. La migracion de verdad -- guardar el producto estable en vez del
   *  numero -- esta apuntada en `docs/MODELO.md`. */
  producto_movido?: boolean
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
  /** **Viaja y no se pinta, y está mirado**: cuándo se compró la última vez. El mosaico ya
   *  viene ordenado por el ranking con decaimiento (`almacen.historial_de`), así que la fecha
   *  no añade nada a la decisión de tocar «Añadir». */
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
  /** **Viaja y no se pinta, y está mirado**: cuándo se pidió el aviso. Lo que la pantalla
   *  enseña es **cuándo saltó** (`salto_en`) y su frase, que es lo que se viene a saber: la
   *  fecha de la promesa no explica nada de lo que ha pasado. */
  creada_en: string
  vista_en: string | null
  salto_en: string | null
  /** La frase, guardada cuando salto: se mide contra el gold de ese dia. */
  salto_texto: string | null
  /** **El producto que salto**, guardado con la frase.
   *
   *  El nombre de la tarjeta (`nombre`, abajo) se lee del gold de hoy y la frase es del dia que
   *  salto: sin este campo la pantalla enseñaba las dos epocas juntas. Medido el 28 de septiembre
   *  de 2026: «TWIX Barritas de chocolate ... esta al precio mas bajo de los ultimos 90 dias:
   *  0.96 EUR/l en mercadona», que es la frase de la leche entera (el grupo 10226 era la leche el
   *  dia que salto). Las filas que saltaron antes de que existiera esta columna vienen con `null`,
   *  y entonces la pantalla usa el nombre del grupo: no se inventa un nombre que no se guardo. */
  salto_nombre?: string | null
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
  /** Las líneas del reparto, con su tienda y su coste.
   *
   *  Es lo que permite **aplicarlo**: el botón de «repartir en dos tiendas» pone la
   *  tienda de cada línea, y para eso hace falta saber qué línea va a cada sitio. Sin
   *  esto, lo único que se podría hacer es ponerlas todas en una, que es otra cosa. */
  productos?: {
    producto_id: string
    nombre: string
    cadena: string
    unidades: number
    coste_cent: number
    /** De qué línea de la lista sale, para poder asignarla. */
    linea_id?: string | null
  }[]
}

export interface Donde {
  una_tienda: OpcionTienda[]
  repartido: Reparto | null
  lineas: number
  fecha_datos: string
}

/* ------------------------------------------- donde hacer la compra (panel) --- */

/** El desvío de una cadena en un pasillo, medido sobre los mismos productos. */
export interface DesvioEnPasillo {
  cadena: string
  productos: number
  /** Mediana del desvío respecto a las otras cadenas del mismo grupo. Negativo = más barata. */
  desvio_pct: number
}

/** Un pasillo con quién gana en él. */
export interface PasilloDeCompra {
  seccion: string
  /** El nombre que se lee («Lácteos y huevos»), no el slug. */
  nombre: string
  productos: number
  gana: string
  desvio_pct: number
  peor: string
  peor_pct: number
  /** Cuánto se separa la primera de la siguiente. Si es poco, el pasillo no decide nada. */
  ventaja_sobre_la_siguiente_pct: number | null
  siguiente: string | null
  cadenas: DesvioEnPasillo[]
}

export interface PanelDonde {
  fecha_datos: string
  /** Cómo se ha medido, en una frase, para poder discutirlo. */
  medida: string
  /** Productos mínimos por celda: con menos, la mediana es ruido. */
  minimo_por_celda: number
  pasillos: PasilloDeCompra[]
  pasillos_totales: number
  /** Cuántos pasillos gana cada cadena: el único resumen válido de «quién es más barato». */
  victorias: { cadena: string; pasillos: number }[]
  /** Productos concretos donde más se nota la diferencia entre cadenas. */
  oportunidades: {
    productos: {
      grupo_id: number
      nombre: string
      mas_barata: string
      precio_cent: number
      mas_cara: string
      precio_caro_cent: number
      unidad: string
      cadenas: number
      diferencia_cent: number
    }[]
    /** Los tres filtros que quitan las mentiras conocidas, en una frase. */
    filtros: string
  }
}


/* ------------------------------------------- la lista, partida por tiendas --- */

/** Lo que cuesta UNA linea en UNA tienda concreta. */
export interface OpcionEnTienda {
  cadena: string
  coste_cent: number
  coste_sin_oferta_cent: number
  /** La oferta que se ha aplicado, si hay alguna. */
  promo: string | null
}

/** Una linea dentro de la sublista de su tienda. */
export interface FilaEnTienda {
  /** De que linea de la lista viene. `null` si la linea no tiene id (no pasa hoy). */
  linea_id: string | null
  nombre: string
  cantidad: number
  producto_id: string
  coste_cent: number
  coste_sin_oferta_cent: number
  promo: string | null
  /** «Llevando 3 en vez de 2, 0,50 EUR menos por unidad»: la oferta explicada. */
  sugerencia: string | null
  /** Si el producto propuesto es el que se pidio: `exacto`, `probable`, `alternativa`, `cuarentena`
   *  o `abstiene`. `null` cuando la API no puede afirmar nada, que no es lo mismo que decir que si. */
  identidad?: string | null
  /** Si esta linea cuenta en el total. `false` significa que se enseña y no suma. */
  autorizada?: boolean
  /** La opcion que se puede pedir en su lugar: nombre, precio y cadena. */
  alternativa?: { producto_id: string; nombre: string; coste_cent: number; fuente: string } | null
  /** Por que no es el mismo, en palabras. Es lo que permite juzgarlo en vez de confiar. */
  motivo?: string | null
  /** Lo mismo en las otras tiendas, de mas barata a mas cara. */
  opciones: OpcionEnTienda[]
  /** La tienda en la que esta puesta. */
  elegida?: string
  mas_barata: string
}

/** La compra de una tienda: sus lineas y su cuenta. */
export interface SubLista {
  cadena: string
  lineas: FilaEnTienda[]
  unidades: number
  total_cent: number
  /** Lo que costaria sin las ofertas: la resta es lo que ahorran. */
  total_sin_ofertas_cent: number
  ahorro_cent: number
  ofertas: { nombre: string; promo: string; ahorro_cent: number }[]
  /** Lo que esta asignado a esta tienda y aqui no hay, por su nombre. */
  sin_encontrar: string[]
}

/** Una linea que todavia no se ha decidido, con la opcion mas barata al lado. */
export interface PendienteDeDecidir {
  linea_id: string | null
  nombre: string
  cantidad: number
  /** **Viaja y no se pinta, y está mirado**: «hay precio en alguna cadena». La pantalla usa
   *  `coste_cent == null` y dice «no lo sé» (`RepartoEnTiendas`), que distingue lo mismo sin
   *  afirmar de más: el precio de hoy puede no estar y el producto seguir en el catálogo. */
  hay_precio: boolean
  mas_barata: string | null
  coste_cent: number | null
  producto_id: string | null
  opciones: OpcionEnTienda[]
  /** **Lo que la persona ya decidio sobre esta linea.** Va por linea y no por lista: autoriza una
   *  sustitucion concreta, no "lo que haga falta" en toda la compra. Y `autorizado_producto` dice
   *  **que** se acepto, no solo que se acepto. Medido el 13 de octubre de 2026: viajaban en la
   *  peticion y no llegaban a la pantalla. */
  autorizado: boolean
  autorizado_producto: string | null
  autorizado_cadena: string | null
}

/** La respuesta de `GET /listas/{id}/reparto`: la lista partida por lo decidido. */
export interface RepartoTiendas {
  sublistas: SubLista[]
  sin_asignar: PendienteDeDecidir[]
  /** Lineas asignadas a una tienda que no las tiene. No desaparecen nunca. */
  sin_encontrar: { cadena: string; nombres: string[] }[]
  total_cent: number
  total_sin_ofertas_cent: number
  ahorro_cent: number
  lineas: number
  decididas: number
  sin_precio: number
  /** La comparacion: donde saldria mas barata entera, y el mejor reparto. */
  una_tienda: OpcionTienda[]
  repartido: Reparto | null
  fecha_datos: string
}

/** Un favorito.
 *
 *  Las dos formas de seguir algo -- un grupo (desde la ficha del grupo) y un
 *  producto concreto (desde la ficha del producto) -- llegan **con la misma
 *  forma**: desde el 30 de septiembre de 2026 la API las normaliza, y antes la de
 *  producto llegaba con otro sobre. */
export interface Favorito {
  grupo_id: number | null
  producto_id?: string | null
  /** `null` cuando el favorito apunta a algo que ya no esta en el catalogo. */
  nombre: string | null
  /** En los de grupo, la cadena mas barata de hoy. */
  cadena?: string | null
  fuente?: string | null
  unidad?: string | null
  precio_cent?: number | null
  precio_unidad_cent?: number | null
  ahorro_pct?: number | null
  marca?: string | null
  /** Cuantas cadenas lo tienen. 1 en los que se siguen por producto suelto. */
  n_cadenas?: number
  /** **Lo que se ha movido**, que es lo que se viene a mirar aqui. */
  comparable?: boolean
  /** `sin historico`, `cambio de formato` o `ya no esta en el catalogo`. */
  motivo?: string | null
  variacion_pct?: number | null
  precio_unidad_antes_cent?: number | null
  /** Los dias que hay **de verdad** entre las dos capturas comparadas. */
  dias_medidos?: number | null
  /** La ventana que se pidio (7, 30 o 90 dias). */
  dias?: number
  /** El favorito apunta a algo que ya no se puede resolver. */
  desconocido?: boolean
  que?: string
}
