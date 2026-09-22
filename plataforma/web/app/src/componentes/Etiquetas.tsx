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
import { Etiqueta } from './ui'

const COLOR_NUTRI: Record<string, string> = {
  a: 'bg-emerald-600 text-white',
  b: 'bg-lime-500 text-neutral-900',
  c: 'bg-amber-400 text-neutral-900',
  d: 'bg-orange-500 text-white',
  e: 'bg-red-600 text-white',
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
      className={`inline-flex h-6 w-6 items-center justify-center rounded font-bold ${color ?? 'bg-neutral-400 text-white'}`}
    >
      {letra.toUpperCase()}
    </span>
  )
}

export function SelloComparable({ cadenas }: { cadenas: number }) {
  if (cadenas >= 2) {
    return (
      <Etiqueta tono="bien" titulo="El mismo producto está en más de una cadena: se puede comparar">
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

export function SelloOferta({ texto, club }: { texto: string | null; club: boolean | null }) {
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
    return (
      <Etiqueta tono="bien" titulo={texto}>
        oferta
      </Etiqueta>
    )
  }
  return null
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
 */
export function SelloLetra({ producto }: { producto: Pick<Producto, 'calidad' | 'gama'> }) {
  const { calidad, gama } = producto
  if (calidad) {
    return (
      <Etiqueta
        tono="info"
        titulo="Leída de la lista de ingredientes: aditivos, aceite de palma, porcentaje del primero y longitud de la lista"
      >
        Calidad {calidad} · leída de ingredientes
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
