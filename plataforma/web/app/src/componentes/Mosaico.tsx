/** LO DE SIEMPRE: la cuadricula de lo habitual, para anadirlo de un toque.
 *
 *  Es la mejora de mas valor que le quedaba al buscador, y su razon esta en
 *  `docs/PANTALLAS.md:50-62`: anadir algo que compras siempre pasa de **escribir,
 *  elegir y anadir** a **un toque**. Esta pantalla se usa de pie y con una mano, asi
 *  que la diferencia entre dos pulsaciones y una no es comodidad: es que se use.
 *
 *  De donde sale: `GET /api/habituales`, con **cada tarjeta diciendo su `origen`**.
 *  Es la parte que no se puede saltar: la cuadricula puede tener cosas tuyas y cosas
 *  de la compra basica a la vez, y **no valen lo mismo**. Sin ese campo la pantalla
 *  ensenaria "lo que sueles comprar" con lo que compra otro.
 *
 *  Tres reglas que estan aqui dentro, y las tres son decisiones, no adornos:
 *
 *  1. **Sin historial, esto no se pinta: sale la tarjeta de la primera vez.**
 *     `LoQueSeCompra` ensena cuatro productos que compra todo el mundo **con su
 *     diferencia de hoy**, que es lo que hace entender para que sirve la aplicacion.
 *     Una cuadricula de 24 productos basicos no explica nada: son 24 recuadros sin
 *     una sola razon para mirarlos. Primero se entiende, despues se usa.
 *
 *     **Con una excepcion: `vacia`** (la cesta sin nada dentro). Ahi la cuadricula de
 *     la compra basica **si** tiene una razon: la pregunta que se trae a esa pantalla es
 *     *"¿que me falta?"*, y con la lista vacia la respuesta es "todo". 24 recuadros que
 *     se apuntan de un toque contestan eso; la tarjeta de la primera vez, no. Por eso
 *     `vacia` quita el respaldo y **cambia el titulo** por el de verdad ("La compra
 *     basica", "Lo que compra la casa"): sin eso, una cuadricula de basicos se leeria
 *     como "lo que sueles comprar", que es mentira.
 *  2. **Si el endpoint no esta, no pasa nada.** El 404 de una API que todavia no se
 *     ha desplegado no es un fallo de nadie: se cae a la tarjeta de la primera vez,
 *     igual que si no hubiera historial. Un error rojo aqui seria culpar a quien
 *     acaba de abrir la aplicacion.
 *  3. **Un toque, sin dialogo.** No se pregunta la cantidad ni a que lista: se apunta
 *     en la de casa (se crea si no hay) con cantidad 1, y el cuanto se cambia en la
 *     cesta, que es donde se ve la lista entera y lo que va a costar. Y el boton de
 *     cada tarjeta dice si ya esta dentro, para que pulsar dos veces no sea el error
 *     facil de verdad.
 */
import { useState } from 'react'

import { useAnadeALaCesta, useHabituales } from '../api/consultas'
import { eurosUnidad, nombreCadena } from '../api/formato'
import { Boton, EsqueletoRejilla, Etiqueta, Tarjeta } from './ui'
import { LoQueSeCompra } from './LoQueSeCompra'

/** Lo que dice el titulo segun de donde salga lo que se esta viendo. */
const TITULO: Record<string, string> = {
  tuyo: 'Lo de siempre',
  'de todos': 'Lo que compra la casa',
  basico: 'La compra basica',
}

/** La cuadricula de lo habitual.
 *
 *  `vacia` se pone cuando se pinta dentro de una lista sin nada: ahi la compra basica
 *  **si** se ensena (ver la regla 1 del comentario de arriba). Por defecto no, que es lo
 *  que quieren el buscador y todo lo demas.
 */
export function Mosaico({ limite = 12, vacia = false }: { limite?: number; vacia?: boolean }) {
  const habituales = useHabituales(limite)
  const anade = useAnadeALaCesta()
  const [puestos, setPuestos] = useState<number[]>([])

  // Mientras se sabe, **el hueco de la cuadricula**: seis recuadros del tamaño de una
  // tarjeta, para que lo que llegue no empuje nada. Un hueco que aparece y desaparece
  // es peor que esperar medio segundo.
  if (habituales.isPending) return <EsqueletoRejilla tarjetas={6} />

  // El 404 (la ruta todavia no esta desplegada) y un historial que no da ni una
  // tarjeta llevan al mismo sitio: la tarjeta de la primera vez.
  const tarjetas = habituales.data?.habituales ?? []
  const soloBasico = (habituales.data?.origenes ?? []).every((o) => o === 'basico')
  if (tarjetas.length === 0 || (soloBasico && !vacia)) return <LoQueSeCompra />

  // Si la cuadricula mezcla escalones, se dice: una tarjeta basica y una tuya no
  // valen lo mismo, y el titulo solo puede hablar de uno.
  const mezcla = new Set(tarjetas.map((h) => h.origen)).size > 1
  // Y cuando **no** mezcla, el titulo dice de donde sale de verdad. En la cesta vacia
  // importa: una cuadricula de la compra basica titulada "Lo de siempre" seria una
  // mentira dicha con un titulo.
  const titulo = vacia && !mezcla
    ? (TITULO[tarjetas[0]?.origen] ?? 'Lo de siempre')
    : 'Lo de siempre'

  return (
    <Tarjeta>
      <p className="text-sm font-semibold">{titulo}</p>
      <p className="mt-0.5 text-sm text-tinta-suave">
        Un toque y a la lista. Lo tocado se cambia en la cesta.
      </p>

      {/* Tres columnas, como el diseno de `docs/PANTALLAS.md:57-62`: en el movil
          caben tres fotos de 80 px y el boton de debajo sigue teniendo sus 44 px de
          alto, que es el minimo que se puede pulsar andando. */}
      <ul className="mt-3 grid grid-cols-3 gap-2">
        {tarjetas.map((h) => {
          const dentro = puestos.includes(h.grupo_id)
          return (
            <li key={h.grupo_id}
                className="flex flex-col gap-1 rounded-xl border border-borde p-2">
              {h.imagen ? (
                <img
                  src={h.imagen}
                  alt=""
                  width={80}
                  height={80}
                  loading="lazy"
                  className="mx-auto h-20 w-20 rounded-lg border border-neutral-200 bg-white object-contain dark:border-neutral-700"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              ) : (
                // Sin foto no se inventa una: se deja el hueco del mismo tamano,
                // que mantiene la cuadricula alineada sin ensenar nada falso.
                <div className="mx-auto h-20 w-20 rounded-lg bg-neutral-100 dark:bg-neutral-700" />
              )}

              <span className="line-clamp-2 text-sm font-medium leading-snug">
                {h.nombre}
              </span>
              <span className="cifra text-base font-semibold">
                {eurosUnidad(h.precio_unidad_cent, h.unidad)}
              </span>
              {h.cadena_mas_barata && (
                <span className="text-xs text-tinta-suave">
                  en {nombreCadena(h.cadena_mas_barata)}
                </span>
              )}

              {/* El origen solo se dice cuando la cuadricula mezcla escalones: si
                  todas son tuyas, decirlo en las doce es ruido. */}
              {mezcla && (
                <Etiqueta tono={h.origen === 'tuyo' ? 'dato' : 'neutro'}>
                  {TITULO[h.origen] ?? h.origen}
                </Etiqueta>
              )}

              <Boton
                variante={dentro ? 'sutil' : 'normal'}
                className="mt-auto min-h-[44px] min-w-[44px]"
                disabled={anade.isPending}
                title={dentro ? 'Ya esta en la lista: la cantidad se cambia en la cesta.' : undefined}
                onClick={() => {
                  if (dentro) return
                  anade.mutate(
                    { grupoId: h.grupo_id, nombre: h.nombre },
                    { onSuccess: () => setPuestos((x) => [...x, h.grupo_id]) },
                  )
                }}
              >
                {dentro ? 'En la cesta' : 'Añadir'}
              </Boton>
            </li>
          )
        })}
      </ul>

      {/* Un fallo al anadir se dice, pero **fuera de la tarjeta**: si cada recuadro
          pudiera pintar su error, doce tarjetas con el mismo texto rojo taparian la
          cuadricula entera por un fallo que es el mismo en todas. */}
      {anade.isError && (
        <p className="mt-3 text-sm">
          <Etiqueta tono="aviso">
            No he podido anadirlo a la lista. Vuelve a intentarlo.
          </Etiqueta>
        </p>
      )}
    </Tarjeta>
  )
}
