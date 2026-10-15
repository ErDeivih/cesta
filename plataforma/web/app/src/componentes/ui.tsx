/** Los componentes base, escritos a mano.
 *
 * No se instala el CLI de shadcn: son ocho piezas pequenas y con Tailwind se
 * escriben en una tarde. Un generador que copia ficheros a tu repositorio
 * anade una dependencia de herramienta y un monton de codigo que no se lee.
 *
 * Accesibilidad, que en una tabla de precios no es un adorno:
 * - Los controles de pulsar miden 44 px de alto como minimo (se usa con una
 * mano y el carro en la otra).
 * - Los estados no se distinguen SOLO por color: cada etiqueta lleva texto.
 * - Avisar de algo es `role="status"`; fallar, `role="alert"`.
 */
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import { useId } from 'react'

import { esSinRed, textoDeError } from '../api/cliente'

export function cx(...clases: (string | false | null | undefined)[]): string {
 return clases.filter(Boolean).join(' ')
}

// ------------------------------------------------------------------ boton ---

type VarianteBoton = 'principal' | 'normal' | 'sutil' | 'peligro'

/** *** Las variantes del boton, *ya con los colores de la casa. *** *
 *
 * *Y lo que habia antes, *medido el 15/10/2026: *** `bg-sky-700` ***.* *El boton
 * principal era **azul**, *y el propio `tailwind.config.js` dice que `bosque` es
 * «navegacion y accion principal».* *O sea: *la direccion estaba **escrita** y la
 * pieza **enchufada a la paleta de Tailwind.** *
 *
 * *Es la causa de que la app pareciera generica **teniendo componentes**: *
 * *611 clases del proyecto usaban la paleta por defecto *(-- **355** solo de
 * `neutral` --)* *y 398 la propia.* *Estaba **mas de la mitad pintada de fabrica.*** *
 *
 * *Y el brillo del `hover` se hace con `brightness` y **no con opacidad**:
 * *`bg-bosque/90` **no se puede** *-- *el test de colores lo dice, *«*una variable
 * de CSS no vale ahi*»: *saldria un color invalido que el navegador ignora* --.* *
 */
const ESTILO_BOTON: Record<VarianteBoton, string> = {
 principal:
 'bg-bosque text-marfil border-transparent shadow-apoyado hover:brightness-110',
 normal:
 'bg-papel text-tinta-fuerte border-borde-fuerte hover:bg-marfil',
 sutil:
 'bg-transparent text-terracota border-transparent underline underline-offset-2 hover:text-tinta-fuerte',
 peligro:
 'bg-papel text-error border-error hover:brightness-95',
}

interface PropsBoton extends ButtonHTMLAttributes<HTMLButtonElement> {
 variante?: VarianteBoton
 /** Para los botones con solo un icono: el texto queda oculto pero lo lee el
 * lector de pantalla. Un icono sin nombre no es un boton. */
 compacto?: boolean
}

export function Boton({ variante = 'normal', compacto, className, ...resto }: PropsBoton) {
 return (
 <button
 type="button"
 {...resto}
 className={cx(
 'inline-flex items-center justify-center gap-2 rounded-campo border font-medium',
 // *El movimiento, *con las dos duraciones de la direccion: *rapida porque
 // **responde al dedo** *(-- no es un cambio de pantalla --).*
 'transition-colors duration-rapida ease-suave',
 // 44 px: el minimo para pulsar con el pulgar sin fallar. **En las dos
 // direcciones**: medido en el navegador el 23 de septiembre de 2026, los botones
 // «−» y «+» de la cantidad -- justo lo que se toca con el carro en marcha --
 // median **37 x 44**: el alto estaba, el ancho no, porque un solo caracter con
 // `px-3` no llega. Un `min-w` lo arregla sin tocar ninguna pantalla.
 compacto ? 'min-h-[44px] min-w-[44px] px-3 py-2' : 'min-h-[44px] px-4 py-2',
 'disabled:cursor-not-allowed disabled:opacity-50',
 ESTILO_BOTON[variante],
 className,
 )}
 />
 )
}

// --------------------------------------------------------------- etiqueta ---

type Tono = 'neutro' | 'bien' | 'mal' | 'aviso' | 'info' | 'dato'

/** *** Y los tonos, *con los colores que SIGNIFICAN algo. *** *
 *
 * *Antes: *`bg-emerald-100`, *`bg-red-100`, *`bg-amber-100`, *`bg-sky-100`.*
 * *Cuatro familias de Tailwind, *cada una con **su propio verde, su propio rojo y
 * su propio ambar**, *que no son los de esta app.* *
 *
 * *Y el de «info» era *** `sky` ***: *un azul que **no esta en la direccion**.*
 * *Aqui pasa a ser **neutro**, *que es lo honesto: *«informacion» **no es un
 * estado**, *es texto que se lee.* *Si algun dia hace falta un azul, *se anade a
 * `DIRECCION.md` **y a los dos temas**, *no se cuela por una pieza.* *
 */
const ESTILO_ETIQUETA: Record<Tono, string> = {
 neutro: 'bg-marfil text-secundaria border-borde-fuerte',
 bien: 'bg-bien-suave text-bien border-bien',
 mal: 'bg-papel text-error border-error',
 aviso: 'bg-papel text-aviso border-aviso',
 info: 'bg-papel text-secundaria border-borde',
 dato: 'bg-transparent text-secundaria border-borde-fuerte',
}

export function Etiqueta({
 tono = 'neutro',
 children,
 titulo,
}: {
 tono?: Tono
 children: ReactNode
 titulo?: string
}) {
 return (
 <span
 title={titulo}
 className={cx(
 'inline-flex items-center gap-1 rounded-nota border px-1.5 py-0.5 text-etiqueta font-medium',
 ESTILO_ETIQUETA[tono],
 )}
 >
 {children}
 </span>
 )
}

// ------------------------------------------------------------------ cajas ---

export function Tarjeta({
 titulo,
 sub,
 acciones,
 children,
 className,
}: {
 titulo?: ReactNode
 sub?: ReactNode
 acciones?: ReactNode
 children: ReactNode
 className?: string
}) {
 return (
 <section
 className={cx(
 // *** La tarjeta: *papel, borde y **grosor**. *** *
 //
 // *Antes era `rounded-xl border-neutral-200 bg-white shadow-sm`.* *
 // *-- *** `bg-white` *** *y no `papel`: *el blanco puro **no es de esta
 // casa**, *que es de papel calido ✓
 // *-- *** `border-neutral-200` *** *y no `borde`: *un gris **frio** ✓
 // *-- *y *** `shadow-sm` ***, *que es una sombra **gris**: *sobre marfil
 // **se ve sucia**, *porque el marfil es calido y el gris no ✓
 // *Ahora la sombra es **`apoyado`**, *que lleva el marron del papel dentro,
 // y el radio es **`tarjeta`** *-- *el suyo, *no el mismo que un boton.* *
 'rounded-tarjeta border border-borde bg-papel p-4 shadow-apoyado',
 className,
 )}
 >
 {(titulo || acciones) && (
 <header className="mb-3 flex flex-wrap items-start justify-between gap-2">
 <div>
 {titulo && <h2 className="text-entrada font-semibold text-tinta-fuerte">{titulo}</h2>}
 {sub && <p className="mt-0.5 text-etiqueta text-secundaria">{sub}</p>}
 </div>
 {acciones}
 </header>
 )}
 {children}
 </section>
 )
}

export function Aviso({
 tono = 'info',
 titulo,
 children,
}: {
 tono?: 'info' | 'aviso' | 'mal' | 'bien'
 titulo?: ReactNode
 children?: ReactNode
}) {
 // *** Y los avisos, *con los colores que ya significan algo. *** *
 //
 // *Antes eran `sky`, `amber`, `red` y `emerald` **crudos** *-- *cuatro familias de
 // Tailwind, *cada una con su tono.* *Y un aviso **no es un color**: *es **lo que
 // hay que mirar** *(-- `aviso` --)*, *** lo que ha fallado *** *(-- `error` --)*,
 // *o **lo que ha salido bien** *(-- `bien` --).* *
 const borde: Record<string, string> = {
 info: 'border-borde bg-papel text-tinta-fuerte',
 aviso: 'border-aviso bg-papel text-aviso',
 mal: 'border-error bg-papel text-error',
 bien: 'border-bien bg-bien-suave text-bien',
 }
 return (
 <div
 role={tono === 'mal' ? 'alert' : 'status'}
 className={cx('rounded-campo border px-3 py-2 text-cuerpo', borde[tono])}
 >
 {titulo && <p className="font-semibold">{titulo}</p>}
 {children}
 </div>
 )
}

/** Un dato con su etiqueta. Siempre los dos: un numero sin que es no informa. */
export function Dato({
 etiqueta,
 children,
 className,
}: {
 etiqueta: ReactNode
 children: ReactNode
 className?: string
}) {
 return (
 <div className={className}>
 <dt className="text-etiqueta uppercase tracking-wide text-tinta-suave">
 {etiqueta}
 </dt>
 <dd className="cifra mt-0.5 text-cuerpo font-medium">{children}</dd>
 </div>
 )
}

// --------------------------------------------------------------- controles ---

interface PropsCasilla extends InputHTMLAttributes<HTMLInputElement> {
 etiqueta: ReactNode
}

export function Casilla({ etiqueta, id, className, ...resto }: PropsCasilla) {
 const generado = useId()
 const mio = id ?? generado
 return (
 <label
 htmlFor={mio}
 // 44 px de alto para poder pulsar la casilla y el texto con el dedo.
 className={cx(
 'inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-campo border px-3 py-1 text-cuerpo',
 'border-borde-fuerte bg-papel hover:bg-marfil dark:hover:bg-papel',
 className,
 )}
 >
 <input
 id={mio}
 type="checkbox"
 {...resto}
 className="h-4 w-4 shrink-0 accent-bosque "
 />
 <span>{etiqueta}</span>
 </label>
 )
}

export function Selector({
 etiqueta,
 children,
 id,
 className,
 ...resto
}: SelectHTMLAttributes<HTMLSelectElement> & { etiqueta?: ReactNode }) {
 const generado = useId()
 const mio = id ?? generado
 return (
 <div className={cx('flex flex-col gap-1', className)}>
 {etiqueta && (
 <label htmlFor={mio} className="text-etiqueta font-medium text-secundaria ">
 {etiqueta}
 </label>
 )}
 {/* Sin `text-cuerpo`, y a proposito: el tamano se hereda del `html`, que son
 16 px. Por debajo de 16, Safari del movil hace zoom al enfocar el campo,
 la pagina se queda descuadrada y hay que pellizcar para volver. Estaba
 puesto en este componente y en `CampoTexto`, o sea en **todos** los
 campos de la aplicacion: el buscador, el login, los ajustes y las
 cantidades. Lo vigila `tests/test_ui_movil.py`. */}
 <select
 id={mio}
 {...resto}
 className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-3 py-2 "
 >
 {children}
 </select>
 </div>
 )
}

export function CampoTexto({
 etiqueta,
 id,
 className,
 ...resto
}: InputHTMLAttributes<HTMLInputElement> & { etiqueta?: ReactNode }) {
 const generado = useId()
 const mio = id ?? generado
 return (
 <div className={cx('flex flex-col gap-1', className)}>
 {etiqueta && (
 <label htmlFor={mio} className="text-etiqueta font-medium text-secundaria ">
 {etiqueta}
 </label>
 )}
 {/* Igual que el `select` de arriba: sin `text-cuerpo`. El tamano sale del
 `html` (16 px) porque por debajo Safari hace zoom al enfocar. */}
 <input
 id={mio}
 {...resto}
 className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-3 py-2 "
 />
 </div>
 )
}

// ------------------------------------------------------------ estados raros ---

export function Cargando({ que = 'los datos' }: { que?: string }) {
 // **Un hueco, no una linea de texto.** Lo pide el encargo (§8): *"los estados de
 // carga: nada de saltos de maquetacion. Un hueco del tamaño de lo que va a venir"*.
 // Una linea que dice "Cargando…" y despues se convierte en una lista de nueve filas
 // hace saltar todo lo que hay debajo -- y en el movil, con el pulgar ya camino del
 // boton, el boton se mueve.
 return (
 <div role="status" className="grid min-h-[6rem] place-items-center py-6">
 <p className="text-cuerpo text-secundaria ">Cargando {que}…</p>
 </div>
 )
}

/** El hueco de una lista o una tabla que todavia no ha llegado.
 *
 * Con **la forma** de lo que va a venir: `filas` bloques de la altura de una fila, con
 * el mismo hueco entre ellos que la lista de verdad (`gap-2`). Asi, cuando el dato
 * llega, el contenido no empuja nada: ocupa el sitio que ya estaba reservado.
 *
 * Un esqueleto que no se parece a lo que viene es peor que una linea de texto: reserva
 * el sitio equivocado y encima promete una forma que no es. Por eso las dos formas que
 * hay -- filas y rejilla -- son las de las dos cosas que se esperan en esta aplicacion:
 * listas y cuadriculas.
 */
export function Esqueleto({ filas = 4, alto = '3.25rem' }: { filas?: number; alto?: string }) {
 return (
 <div role="status" className="grid gap-2">
 {Array.from({ length: filas }).map((_, i) => (
 <div
 key={i}
 style={{ height: alto }}
 className="animate-pulse rounded-campo bg-marfil /60"
 />
 ))}
 <span className="sr-only">Cargando…</span>
 </div>
 )
}

/** Lo mismo, con la forma de la cuadricula del mosaico. */
export function EsqueletoRejilla({ tarjetas = 6, alto = '11rem' }:
 { tarjetas?: number; alto?: string }) {
 return (
 <div role="status" className="grid grid-cols-3 gap-2">
 {Array.from({ length: tarjetas }).map((_, i) => (
 <div
 key={i}
 style={{ height: alto }}
 className="animate-pulse rounded-tarjeta bg-marfil /60"
 />
 ))}
 <span className="sr-only">Cargando…</span>
 </div>
 )
}

export function Fallo({ error, reintentar }: { error: unknown; reintentar?: () => void }) {
 // El texto lo pone `textoDeError`, que ya distingue "sin conexion" de "el
 // servidor ha contestado 500". Aqui no se inventa un mensaje nuevo.
 //
 // **Y el color tambien lo decide eso**, no la pantalla que llama: si lo que pasa
 // es que no hay red, esto no es un fallo, es un movil en un pasillo de supermercado
 // -- y en rojo, con `role="alert"`, se lee como "la aplicacion se ha roto" y se
 // deja de usar justo donde mas sirve. Se arregla en **un solo sitio** y no en las
 // seis pantallas que usan `Fallo`: buscar, la ficha, el grupo, el escaner, el panel
 // y el panel de matching. Si se arreglara pantalla por pantalla, la septima
 // volveria a nacer en rojo.
 if (esSinRed(error)) {
 return (
 <Aviso tono="aviso" titulo="Sin cobertura">
 <p>No he podido traer esto: no hay conexion con casa.</p>
 {reintentar && (
 <>
 <p className="mt-1">Vuelve a intentarlo cuando tengas red.</p>
 <Boton variante="normal" className="mt-2" onClick={reintentar}>
 Volver a intentarlo
 </Boton>
 </>
 )}
 </Aviso>
 )
 }
 return (
 <Aviso tono="mal" titulo="No he podido traer esto">
 <p>{textoDeError(error)}</p>
 {reintentar && (
 <Boton variante="normal" className="mt-2" onClick={reintentar}>
 Volver a intentarlo
 </Boton>
 )}
 </Aviso>
 )
}

/** Un estado vacio: el titulo dice que pasa, y debajo va que hacer.
 *
 * `comoPagina` convierte el titulo en el `h1` de la pantalla. Se usa cuando el estado vacio
 * **es** la pantalla entera -- la direccion que no existe, o una puerta de sesion --: ahi el
 * titulo es el titulo de la pagina, y sin esto la pantalla se quedaba sin encabezado de nivel 1
 * (medido con `data/debug/accesibilidad.py` el 27 de septiembre de 2026, que encontro cinco
 * casos asi). Las clases son las mismas: cambia la etiqueta, no lo que se ve.
 */
export function Vacio({ titulo, children, comoPagina = false }: {
 titulo: ReactNode
 children?: ReactNode
 comoPagina?: boolean
}) {
 const Titulo = comoPagina ? 'h1' : 'p'
 return (
 <div className="rounded-tarjeta border border-dashed border-borde-fuerte px-4 py-8 text-center ">
 <Titulo className="font-medium">{titulo}</Titulo>
 {children && (
 <div className="mx-auto mt-2 max-w-prose text-cuerpo text-secundaria ">
 {children}
 </div>
 )}
 </div>
 )
}

// ------------------------------------------------------------ desplegable ---

/** El titulo de un `<details>`, con la flecha que dice que eso se abre.
 *
 * **Faltaba, y se vio mirando una captura, no leyendo el codigo.** La cabecera de la aplicacion
 * enseña «Estado de las cadenas» y no hay nada que diga que eso se abre: en las capturas del
 * 27 de septiembre de 2026 sale como una linea suelta con un hueco debajo, que es exactamente lo
 * que parece -- un encabezado sin nada. Y no es solo esa: **los diez desplegables de la
 * aplicacion** (los filtros del buscador, las columnas de la tabla, el porque de un
 * emparejamiento, los ingredientes, el detalle de una pasada...) tenian el mismo problema. En
 * `/buscar`, la caja de filtros parecia un segundo campo de texto.
 *
 * La causa es una linea de CSS que no se ve: el marcador nativo del `<summary>` **desaparece** en
 * cuanto se le pone `display: flex` (que hace falta para que mida 44 px), asi que el triangulo
 * que el navegador pondria solo no se pinta. Se pinta uno, y gira al abrirse (`estilos.css`,
 * `details[open]`).
 *
 * `ml-auto` deja la flecha al final de la linea cuando el resumen ocupa el ancho entero (la
 * cabecera), y no hace nada cuando el resumen mide lo que mide su texto.
 */
export function Resumen({ children, className }: {
 children: ReactNode
 className?: string
}) {
 return (
 <summary
 className={cx(
 // `list-none`: en Safari el triangulo tambien sale con `display: flex`, y esta es la
 // forma de quitarlo alli. El aria no lo necesita: `details`/`summary` ya lo anuncian.
 'flex min-h-[44px] cursor-pointer list-none items-center gap-1.5',
 className,
 )}
 >
 {children}
 {/* `text-entrada` y no el tamaño del texto de al lado: la flecha tiene que verse **cuando el
 resumen es pequeño** (los que van en `text-etiqueta`), que es donde mas falta hace. */}
 <span aria-hidden className="flecha ml-auto shrink-0 text-entrada leading-none opacity-70">
 ▾
 </span>
 </summary>
 )
}

// ------------------------------------------------------------------ tabla ---

/** Envoltorio de tabla: **en el móvil se apila, en pantalla ancha se desliza si hace falta**.
 *
 * Una tabla de precios con siete columnas no cabe en un móvil, y las tres salidas malas son:
 * aplastarla hasta que no se lee, esconder columnas (y que el dato que falta sea justo el que
 * se buscaba) o dejarla salirse de la pantalla. Hasta el 27 de septiembre de 2026 la salida
 * era scroll horizontal con la primera columna pegada y un aviso de que se podía deslizar, y
 * **el aviso era el sintoma de que la respuesta no se veía**: en un móvil de 390 px lo que
 * quedaba fuera era la columna del precio, medido en el buscador y en el panel. Ahora, por
 * debajo de 640 px, cada fila es una línea y las celdas fluyen debajo (lo hace `.tabla-scroll`
 * en `estilos.css`); de 640 px para arriba sigue la tabla de verdad, que es donde comparar
 * columnas tiene sentido.
 *
 * `minAncho` se queda para la tabla ancha, y en el móvil se anula: si no, el ancho mínimo
 * seguiría empujando la página en horizontal.
 */
export function TablaScroll({
 children,
 etiqueta,
 minAncho = '46rem',
}: {
 children: ReactNode
 etiqueta: string
 minAncho?: string
}) {
 return (
 <div
 className="tabla-scroll"
 role="region"
 aria-label={etiqueta}
 tabIndex={0}
 >
 <div style={{ minWidth: minAncho }}>{children}</div>
 </div>
 )
}

export function Th({
 children,
 ordenable,
 activo,
 direccion,
 onClick,
 className,
}: {
 children: ReactNode
 ordenable?: boolean
 activo?: boolean
 direccion?: 'asc' | 'desc' | false
 onClick?: (evento?: unknown) => void
 className?: string
}) {
 const contenido = (
 <span className="inline-flex items-center gap-1">
 {children}
 {activo && <span aria-hidden="true">{direccion === 'desc' ? '▾' : '▴'}</span>}
 </span>
 )
 return (
 <th
 scope="col"
 aria-sort={activo ? (direccion === 'asc' ? 'ascending' : 'descending') : 'none'}
 className={cx(
 'sticky top-0 z-10 border-b border-borde bg-marfil px-3 py-2 text-left text-etiqueta font-semibold uppercase tracking-wide text-secundaria',
 className,
 )}
 >
 {ordenable && onClick ? (
 <button
 type="button"
 // El manejador de TanStack espera un evento: se le pasa el del boton
 // tal cual, que es lo que necesita para el orden multiple con Shift.
 onClick={(e) => onClick(e)}
 className="inline-flex min-h-[44px] min-w-[44px] items-center gap-1 hover:text-tinta-fuerte dark:hover:text-white"
 >
 {contenido}
 </button>
 ) : (
 contenido
 )}
 </th>
 )
}

/** Una celda.
 *
 * `etiqueta` es **para el móvil**: por debajo de 640 px las tablas se apilan (una fila por
 * línea, con las celdas fluyendo en varias líneas) y ahí no hay cabecera de columna que diga
 * qué es cada número. Las celdas cuyo valor se explica solo («0,96 €/l», «−18 %», una fecha)
 * no necesitan etiqueta; las que son un número pelado («1.234»), sí, o el dato se queda sin
 * sujeto. Ver `.tabla-scroll` en `estilos.css`.
 *
 * La etiqueta es **texto de verdad y no un `::before` de CSS**, y eso importa: el contenido
 * de un pseudo-elemento no lo lee un lector de pantalla ni aparece en `innerText`, así que la
 * medida de la puerta («¿dice sobre cuántos productos?») no lo vería. Se comprobó el 27 de
 * septiembre de 2026: con `::before`, la comprobación del índice del panel se puso roja con la
 * etiqueta puesta y visible.
 */
export function Td({ children, className, etiqueta }: {
 children: ReactNode
 className?: string
 etiqueta?: string
}) {
 return (
 <td
 data-etiqueta={etiqueta}
 className={cx('border-b border-borde px-3 py-2 align-top ', className)}
 >
 {etiqueta && (
 // El espacio va **dentro del texto**, no solo en el margen: `mr-1` separa al mirarlo,
 // pero `innerText` -- y un lector de pantalla -- leian «precio1,95 €». Medido con
 // `data/debug/cifras.py` el 27 de septiembre de 2026.
 <span className="mr-1 text-etiqueta text-tinta-suave sm:hidden">{`${etiqueta} `}</span>
 )}
 {children}
 </td>
 )
}