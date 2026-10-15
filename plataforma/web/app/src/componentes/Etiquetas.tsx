/** Las etiquetas que significan algo, en un solo sitio.
 *
 *  Estan juntas porque cada una lleva una decision dentro y quiero poder leerlas
 *  de un vistazo sin buscarlas por las pantallas:
 *
 *   - `calidad` y `gama` NUNCA se pintan igual. La primera dice de donde sale;
 *     la segunda dice, con esas palabras, que sale de ordenar por precio y que
 *     no es calidad. El 77 % de las letras del catalogo son gama, y presentarlas
 *     como calidad empuja a la conclusion falsa de que lo barato es peor.
 *   - La letra que falta se dice ("sin letra"), no se pinta en gris bajito: un
 *     hueco se lee como un cero.
 *   - Una oferta de tarjeta no baja lo que pagas en caja, asi que no puede
 *     llevar el mismo verde que una oferta de verdad.
 */
import type { Letra, Nutriscore, Producto } from '../tipos'
import { porcentaje } from '../api/formato'
import { Etiqueta } from './ui'

const COLOR_NUTRI: Record<string, string> = {
  a: 'bg-bien text-white',
  b: 'bg-lime-500 text-tinta-fuerte',
  c: 'bg-aviso text-tinta-fuerte',
  d: 'bg-orange-500 text-white',
  e: 'bg-error text-white',
}

export function SelloNutriscore({ valor }: { valor: Nutriscore }) {
  if (!valor) {
    // Ausencia de dato, no dato malo. Por eso "sin Nutri-Score" y no una E.
    return (
      <Etiqueta tono="dato" titulo="No tenemos Nutri-Score ni tabla de la etiqueta para este producto">
        sin Nutri-Score
      </Etiqueta>
    )
  }
  const letra = String(valor).toLowerCase()
  const color = COLOR_NUTRI[letra]
  return (
    <span
      title={`Nutri-Score ${letra.toUpperCase()}`}
      className={`inline-flex h-6 w-6 items-center justify-center rounded font-bold ${color ?? 'bg-borde-fuerte text-white'}`}
    >
      {letra.toUpperCase()}
    </span>
  )
}

// **El Eco-Score, y no es el Nutri-Score con otro nombre.** Tiene siete valores, no cinco: de `a` a `f`
// --uno mas por abajo-- mas `a-plus`, que esta por encima de la A, y `not-applicable`. Los colores siguen
// la misma escala que el Nutri-Score para que se lean iguales, y `a-plus` es el unico mas oscuro que la A.
//
// Lo publica Open Food Facts -- es atribucion obligatoria de su licencia, y ademas es lo que hace creible
// el dato: quien lo lee puede saber de donde sale. Va en el `title`.
const COLOR_ECO: Record<string, string> = {
  a: 'bg-bien text-white',
  'a-plus': 'bg-bien text-white',
  b: 'bg-lime-500 text-tinta-fuerte',
  c: 'bg-aviso text-tinta-fuerte',
  d: 'bg-orange-500 text-white',
  e: 'bg-error text-white',
  f: 'bg-error text-white',
}


export function SelloEcoscore({ valor }: { valor: string | null | undefined }) {
  // Ausencia de dato, no dato malo -- y "no aplica" tampoco es una nota: es que a ese producto no se le
  // puede poner. En los dos casos se dice que no lo tenemos, en vez de pintar una letra que mentiria.
  if (!valor || valor === 'not-applicable') {
    return (
      <Etiqueta
        tono="dato"
        titulo="No tenemos Eco-Score de este producto: lo publica Open Food Facts y no todos lo traen"
      >
        sin Eco-Score
      </Etiqueta>
    )
  }
  const grado = String(valor).toLowerCase()
  return (
    <span
      title={`Eco-Score ${grado === 'a-plus' ? 'A+' : grado.toUpperCase()} (Open Food Facts)`}
      className={`inline-flex h-6 min-w-6 items-center justify-center rounded px-1 text-etiqueta font-bold ${
        COLOR_ECO[grado] ?? 'bg-borde-fuerte text-white'
      }`}
    >
      {grado === 'a-plus' ? 'A+' : grado.toUpperCase()}
    </span>
  )
}


export function SelloComparable({ cadenas }: { cadenas: number }) {
  if (cadenas >= 2) {
    return (
      <Etiqueta tono="bien" titulo="El grupo tiene precios por unidad en varias cadenas. Puede incluir marcas y formatos diferentes; no confirma un producto idéntico.">
        comparable · {cadenas} cadenas
      </Etiqueta>
    )
  }
  return (
    <Etiqueta
      tono="dato"
      titulo="Está en una sola cadena: se enseña, pero no hay con qué compararlo"
    >
      sin comparar
    </Etiqueta>
  )
}

export function SelloOferta({ texto, club, unidades }: {
  texto: string | null
  club: boolean | null
  /** Cuántas unidades pide la mecánica, cuando la cadena lo dice en número (Alcampo). */
  unidades?: number | null
}) {
  if (club) {
    return (
      <Etiqueta
        tono="aviso"
        titulo="Se acumula en un monedero: no baja lo que pagas en caja"
      >
        oferta solo con tarjeta
      </Etiqueta>
    )
  }
  if (texto) {
    // El texto completo de la promoción va en el `title`: en una fila de tabla
    // no cabe, y aquí lo que importa es "hay oferta de verdad o no".
    //
    // **Y si la mecánica exige comprar varias unidades, se dice en la etiqueta**, no solo en
    // el texto: «2ª unidad −50 %» es una condición del precio, y quien lee «oferta» sin eso
    // puede creer que el precio de una unidad ya está rebajado. La cadena lo publica en
    // número (`requiredProductQuantity`) y por eso se puede decir sin interpretarlo.
    const exigidas = unidades && unidades > 1 ? ` · ${unidades} ud` : ''
    return (
      <Etiqueta
        tono="bien"
        titulo={exigidas ? `${texto} (hay que comprar ${unidades} unidades)` : texto}
      >
        oferta{exigidas}
      </Etiqueta>
    )
  }
  return null
}

/** Lo que te ahorras comprando en la cadena más barata en vez de en la más cara.
 *
 *  Existe desde el 27 de septiembre de 2026, cuando la tabla de resultados se rehizo para el
 *  móvil: el ahorro era una columna de la tabla, y en las filas de dos líneas del móvil no
 *  cabía. Y es la respuesta corta a «¿esto está caro?», así que no se puede quedar fuera de la
 *  pantalla: aquí va pegada al nombre, en una línea.
 *
 *  **`0.0` no es un cero**: es el centinela de «no comparable» o «dudoso» (`tipos.ts`), y esas
 *  dos cosas se dicen, no se pintan como un 0 %.
 */
export function SelloAhorro({ pct, comparable, dudoso }: {
  pct: number
  comparable: boolean
  dudoso: boolean
}) {
  if (!comparable || dudoso || pct <= 0) {
    return (
      <Etiqueta tono="dato" titulo="Sin comparación fiable no hay ahorro que dar">
        no lo sé
      </Etiqueta>
    )
  }
  return (
    <span
      className="cifra text-etiqueta font-semibold text-bien "
      title="Lo que te ahorras comprándolo en la cadena más barata en vez de en la más cara"
    >
      ahorras un {porcentaje(pct)}
    </span>
  )
}

export function SelloRetirada({ retirado }: { retirado: boolean | null }) {
  if (!retirado) return null
  return (
    <Etiqueta tono="mal" titulo="Retirada del mercado: no lo compres">
      RETIRADO DEL MERCADO
    </Etiqueta>
  )
}

export function SelloDudoso({ dudoso }: { dudoso: boolean }) {
  if (!dudoso) return null
  return (
    <Etiqueta
      tono="aviso"
      titulo="Dentro del grupo hay precios que se contradicen por más del doble en la misma unidad. Sigue saliendo, pero no doy un ahorro que no se sostiene."
    >
      comparación dudosa
    </Etiqueta>
  )
}

/** La letra de un producto, con su procedencia dicha en voz alta.
 *
 *  `calidad` viene de leer ingredientes. `gama` viene de ordenar por precio y
 *  **A es el mas caro**, que es justo lo contrario de "mejor". Las dos son
 *  excluyentes por contrato: un producto trae una o la otra, nunca las dos.
 *
 *  **Y `calidad` sola no bastaba**, porque hay **dos procedencias distintas** y el sello las decia
 *  igual: *`ingredientes` son los que **publica la tienda**; `ingredientes_off` son los que **deduce
 *  Open Food Facts**.* *El caso medido*: **el President de Carrefour del grupo 11627 trae
 *  `ingredientes_off`, nota 100 y letra A, con su columna nativa de ingredientes VACIA** -- *y decir
 *  «leida de ingredientes» a secas **se lo atribuye a Carrefour, que no los publico**.*
 *
 *  *Por eso el sello cambia de texto, y no solo de tooltip*: **quien lee tiene que poder distinguir un
 *  dato del supermercado de una deduccion ajena sin abrir nada.**
 */
export function SelloLetra({
  producto,
}: {
  producto: Pick<Producto, 'calidad' | 'gama' | 'calidad_de'>
}) {
  const { calidad, gama, calidad_de } = producto
  if (calidad) {
    // *`calidad_de` puede no venir de una API vieja*: **si no viene, no se afirma la procedencia** y se
    // dice la parte que si consta. *Es la regla de siempre: lo que no se sabe no se rellena.*
    const esDeducida = calidad_de === 'ingredientes_off'
    return (
      <Etiqueta
        tono={esDeducida ? 'aviso' : 'info'}
        titulo={
          esDeducida
            ? 'Deducida por Open Food Facts: la tienda NO publica los ingredientes de este producto. Es una estimación de un tercero, no un dato del supermercado.'
            : 'Leída de la lista de ingredientes que publica la tienda: aditivos, aceite de palma, porcentaje del primero y longitud de la lista'
        }
      >
        {esDeducida
          ? `Calidad ${calidad} · deducida por Open Food Facts, no por la tienda`
          : `Calidad ${calidad} · leída de los ingredientes de la tienda`}
      </Etiqueta>
    )
  }
  if (gama) {
    return (
      <Etiqueta
        tono="aviso"
        titulo="Sale de ordenar por precio dentro del grupo, no de leer la etiqueta. Es gama, no calidad. En esta letra la A es el más caro del grupo."
      >
        Gama {gama} · por precio, no es calidad
      </Etiqueta>
    )
  }
  return (
    <Etiqueta tono="dato" titulo="Ni ingredientes publicados ni grupo suficiente para repartir letras">
      sin letra
    </Etiqueta>
  )
}

/** Una letra suelta, para las tablas. */
export function LetraSuelta({ letra, tipo }: { letra: Letra | null; tipo: 'calidad' | 'gama' }) {
  if (!letra) return <span className="text-tinta-suave">sin letra</span>
  if (tipo === 'calidad') {
    return (
      <Etiqueta tono="info" titulo="Leída de los ingredientes">
        {letra}
      </Etiqueta>
    )
  }
  return (
    <Etiqueta tono="aviso" titulo="Por precio dentro del grupo: A es el más caro. No es calidad.">
      {letra} (gama)
    </Etiqueta>
  )
}