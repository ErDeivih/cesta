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
import { eurosUnidad } from '../api/formato'
import { Etiqueta } from './ui'

const COLOR_NUTRI: Record<string, string> = {
  a: 'bg-bien text-papel',
  b: 'bg-bien text-tinta-fuerte',
  c: 'bg-aviso text-tinta-fuerte',
  d: 'bg-aviso text-papel',
  e: 'bg-error text-papel',
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
      className={`inline-flex h-6 w-6 items-center justify-center rounded font-bold ${color ?? 'bg-borde-fuerte text-papel'}`}
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
  a: 'bg-bien text-papel',
  'a-plus': 'bg-bien text-papel',
  b: 'bg-bien text-tinta-fuerte',
  c: 'bg-aviso text-tinta-fuerte',
  d: 'bg-aviso text-papel',
  e: 'bg-error text-papel',
  f: 'bg-error text-papel',
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
        COLOR_ECO[grado] ?? 'bg-borde-fuerte text-papel'
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
        titulo="Solo con tarjeta del supermercado"
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

/** *** LA DIFERENCIA CONCRETA, *en euros y con la misma unidad*. *** *
 *
 *  *Antes esto era «hasta un 117,7 % en el grupo»: un porcentaje que no dice cuánto dinero es y
 *  que se lee como «lo que te ahorras comprando este» cuando en realidad es la horquilla del
 *  grupo de equivalencias.* *Ahora se dice la diferencia en euros por unidad comparable: «0,45 €/l
 *  menos que el más caro».*
 *
 *  *Solo se afirma cuando el grupo es comparable y no dudoso (lo dice la API) y cuando el máximo
 *  por unidad viene en la misma unidad: comparar 2,09 €/l con 0,96 €/kg sería inventarse un
 *  número.* *Sin abanico (todos al mismo precio), no hay nada que decir y no se pinta.*
 */
export function DiferenciaDelGrupo({ precioUnidadCent, precioUnidadMaxCent, unidad, comparable, dudoso }: {
  precioUnidadCent: number | null
  precioUnidadMaxCent: number | null
  unidad: string | null
  comparable: boolean
  dudoso: boolean
}) {
  if (!comparable || dudoso) return null
  if (precioUnidadCent === null || precioUnidadMaxCent === null) return null
  const diferencia = precioUnidadMaxCent - precioUnidadCent
  if (diferencia <= 0) return null
  return (
    <span
      className="cifra text-etiqueta text-tinta-suave"
      title="Misma unidad: del miembro más barato al más caro del grupo de equivalentes"
    >
      {eurosUnidad(diferencia, unidad)} menos que el más caro
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
      titulo="Comparación poco fiable"
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
            ? 'Estimación de Open Food Facts: la tienda no publica los ingredientes de este producto.'
            : 'Leída de la lista de ingredientes que publica la tienda.'
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
      <Etiqueta tono="aviso">
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
    <Etiqueta tono="aviso">
      {letra} (gama)
    </Etiqueta>
  )
}