/** *** PEGAR UNA LISTA ENTERA, *viendola antes de que se guarde nada*. ***
 *
 *  *M05: «Texto libre y pegar varias lineas con previa; no interpretar «2 kg» como dos envases sin
 *  base».*
 *
 *  **Este componente no decide nada.** *Parte el texto, lo enseña, y cuando la persona pulsa, llama a
 *  `alAnadir` una vez por linea.* *La regla de «2 kg no son dos envases» vive en
 *  `logica/pegar.ts`, y aqui solo se muestra: si el parser no tiene campo de envases, el boton
 *  tampoco puede inventarlo.*
 *
 *  *Se mantiene aparte de `Cesta.tsx` a proposito: ese fichero tiene mil quinientas lineas, y meter
 *  aqui una pantalla mas es la clase de cambio que rompe tres cosas sin que se vea.*
 */

import { useMemo, useState } from 'react'

import { parteLoPegado, resumenDeLaPrevia } from '../logica/pegar'
import type { Pegada } from '../logica/pegar'
import { Boton, Tarjeta } from './ui'

export function PegarEnLaLista({
  alAnadir,
}: {
  /** *Guarda una linea. `cantidad` **no** viaja: la nota es lo que la persona escribio.* */
  alAnadir: (linea: { nombre: string; nota: string | null }) => Promise<void>
}) {
  const [texto, setTexto] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [hecho, setHecho] = useState<string | null>(null)
  const [fallo, setFallo] = useState<string | null>(null)

  const pegadas: Pegada[] = useMemo(() => parteLoPegado(texto), [texto])
  const resumen = useMemo(() => resumenDeLaPrevia(pegadas), [pegadas])

  const anade = async () => {
    if (pegadas.length === 0) return
    setGuardando(true)
    setFallo(null)
    setHecho(null)
    try {
      for (const una of pegadas) {
        // *La nota es lo que la persona escribio («2 kg»), **no** un numero de envases.*
        await alAnadir({ nombre: una.nombre, nota: una.nota || null })
      }
      setHecho(
        pegadas.length === 1 ? 'Anadida 1 linea.' : `Anadidas ${pegadas.length} lineas.`,
      )
      setTexto('')
    } catch (exc) {
      // *Y si falla a medias, se dice: callarlo dejaria lineas sin anadir sin que se sepa.*
      setFallo(
        exc instanceof Error && exc.message
          ? exc.message
          : 'No se han podido anadir todas. Mira la lista antes de volver a pegarlas.',
      )
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Tarjeta
      titulo="Pegar una lista"
      sub="Una linea por renglon. Se enseña antes de guardar nada."
    >
      <label className="block text-[15px]" htmlFor="pegar-lista">
        <span className="sr-only">Lo que quieres pegar</span>
        <textarea
          id="pegar-lista"
          className="min-h-[7rem] w-full rounded-campo border border-borde bg-papel p-2"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder={'2 kg de arroz\nleche\n1 l de leche'}
        />
      </label>

      <p className="mt-2 text-cuerpo text-tinta-suave">{resumen}</p>

      {/* *** LA PREVIA. *** *Se ven las lineas tal como se van a guardar, con su nota al lado.* */}
      {pegadas.length > 0 && (
        <ul className="mt-3 grid gap-1 text-[15px]">
          {pegadas.map((una, i) => (
            <li key={`${una.nombre}-${i}`} className="flex flex-wrap items-baseline gap-2">
              <span className="text-tinta-fuerte">{una.nombre}</span>
              {una.nota && (
                <span className="text-tinta-suave">
                  queda anotado: {una.nota}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Boton onClick={() => void anade()} disabled={pegadas.length === 0 || guardando}>
          {guardando
            ? 'Anadiendo…'
            : pegadas.length === 1
              ? 'Anadir 1 linea'
              : `Anadir ${pegadas.length} lineas`}
        </Boton>
        <Boton variante="sutil" onClick={() => setTexto('')} disabled={!texto || guardando}>
          Vaciar
        </Boton>
      </div>

      {hecho && <p className="mt-2 text-[15px] text-bien">{hecho}</p>}
      {fallo && (
        <p className="mt-2 text-[15px] text-aviso" role="alert">
          {fallo}
        </p>
      )}
    </Tarjeta>
  )
}
