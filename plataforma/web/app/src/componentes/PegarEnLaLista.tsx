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
 *  **Vincular al catalogo es opcional y revisable.** Cada linea puede buscar hasta tres candidatos
 *  y la persona elige uno o la deja como texto. No hay vinculo automatico: una lista importada que
 *  se enlaza sola al producto equivocado seria peor que una lista sin precios.
 */

import { useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'

import { buscarProductos } from '../api/buscar'
import { euros, nombreCadena } from '../api/formato'
import { leerPegado, resumenDeLaLectura } from '../logica/pegar'
import type { Pegada } from '../logica/pegar'
import type { ResultadoBusqueda } from '../tipos'
import { Boton, Tarjeta } from './ui'

export interface LineaImportada {
  nombre: string
  nota: string | null
  /** El grupo del catálogo elegido a mano; `null` si la línea se queda como texto. */
  grupoId?: number | null
}

export function PegarEnLaLista({
  alAnadir,
}: {
  /** *Guarda una linea. `cantidad` **no** viaja: la nota es lo que la persona escribio.* */
  alAnadir: (linea: LineaImportada) => Promise<void>
}) {
  const [texto, setTexto] = useState('')
  const [nombreArchivo, setNombreArchivo] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [hecho, setHecho] = useState<string | null>(null)
  const [fallo, setFallo] = useState<string | null>(null)
  const [candidatos, setCandidatos] = useState<Record<number, ResultadoBusqueda[]>>({})
  const [buscando, setBuscando] = useState<Record<number, boolean>>({})
  const [elegidos, setElegidos] = useState<Record<number, ResultadoBusqueda | null>>({})
  const [errores, setErrores] = useState<Record<number, string>>({})
  const [buscandoTodas, setBuscandoTodas] = useState(false)

  const lectura = useMemo(() => leerPegado(texto), [texto])
  const pegadas: Pegada[] = lectura.pegadas
  const resumen = useMemo(() => resumenDeLaLectura(lectura), [lectura])

  function limpiaCoincidencias() {
    setCandidatos({})
    setBuscando({})
    setElegidos({})
    setErrores({})
  }

  function cambiaTexto(limpio: string) {
    setTexto(limpio)
    setNombreArchivo(null)
    limpiaCoincidencias()
  }

  function cargaArchivo(evento: ChangeEvent<HTMLInputElement>) {
    const archivo = evento.target.files?.[0]
    if (!archivo) return
    setFallo(null)
    setHecho(null)
    limpiaCoincidencias()
    const lector = new FileReader()
    lector.onload = () => {
      setTexto(String(lector.result ?? ''))
      setNombreArchivo(archivo.name)
    }
    lector.onerror = () => setFallo('No se ha podido leer el archivo.')
    lector.readAsText(archivo)
    evento.target.value = ''
  }

  async function buscaCandidatos(indice: number, nombre: string) {
    if (buscando[indice]) return
    setBuscando((x) => ({ ...x, [indice]: true }))
    setErrores((x) => ({ ...x, [indice]: '' }))
    try {
      const encontrados = await buscarProductos(nombre, 3)
      setCandidatos((x) => ({ ...x, [indice]: encontrados }))
    } catch (exc) {
      setErrores((x) => ({
        ...x,
        [indice]: exc instanceof Error && exc.message
          ? exc.message
          : 'No se ha podido buscar en el catálogo.',
      }))
    } finally {
      setBuscando((x) => ({ ...x, [indice]: false }))
    }
  }

  /** Busca las líneas que aún no tienen candidatos ni vínculo. **Sigue siendo una sugerencia**:
   *  llena las mismas tarjetas de candidatos, no elige ninguna. */
  async function buscaTodas() {
    if (buscandoTodas || guardando) return
    setBuscandoTodas(true)
    try {
      for (const [i, una] of pegadas.entries()) {
        if (elegidos[i] || candidatos[i] || buscando[i]) continue
        await buscaCandidatos(i, una.nombre)
      }
    } finally {
      setBuscandoTodas(false)
    }
  }

  const anade = async () => {
    if (pegadas.length === 0) return
    setGuardando(true)
    setFallo(null)
    setHecho(null)
    try {
      for (const [i, una] of pegadas.entries()) {
        // *La nota es lo que la persona escribio («2 kg»), **no** un numero de envases.*
        const elegido = elegidos[i]
        await alAnadir({
          nombre: elegido?.nombre ?? una.nombre,
          nota: una.nota || null,
          ...(elegido?.grupo_id != null ? { grupoId: elegido.grupo_id } : {}),
        })
      }
      setHecho(
        pegadas.length === 1 ? 'Anadida 1 linea.' : `Anadidas ${pegadas.length} lineas.`,
      )
      setTexto('')
      setNombreArchivo(null)
      limpiaCoincidencias()
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
      sub="Una linea por renglon, o un CSV/JSON. Se enseña antes de guardar nada."
    >
      <label className="block text-[15px]" htmlFor="pegar-lista">
        <span className="sr-only">Lo que quieres pegar</span>
        <textarea
          id="pegar-lista"
          className="min-h-[7rem] w-full rounded-campo border border-borde bg-papel p-2"
          value={texto}
          onChange={(e) => cambiaTexto(e.target.value)}
          placeholder={'2 kg de arroz\nleche\n1 l de leche'}
        />
      </label>

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
        <label className="inline-flex min-h-[44px] cursor-pointer items-center text-etiqueta text-verde underline underline-offset-2">
          Subir CSV o JSON
          <input
            type="file"
            accept=".csv,.json,.txt,text/csv,application/json,text/plain"
            aria-label="Subir CSV o JSON"
            className="sr-only"
            onChange={cargaArchivo}
          />
        </label>
        {nombreArchivo && (
          <span className="text-etiqueta text-tinta-suave">Leido de {nombreArchivo}</span>
        )}
      </div>

      <p className="mt-2 text-cuerpo text-tinta-suave">{resumen}</p>
      {lectura.avisos.map((aviso) => (
        <p key={aviso} role="status" className="mt-1 text-etiqueta text-aviso">
          {aviso}
        </p>
      ))}

      {pegadas.length > 1 && (
        <div className="mt-2">
          <Boton
            variante="sutil"
            compacto
            onClick={() => void buscaTodas()}
            disabled={buscandoTodas || guardando}
          >
            {buscandoTodas ? 'Buscando coincidencias…' : 'Buscar coincidencias en todas'}
          </Boton>
        </div>
      )}

      {/* *** LA PREVIA. *** *Se ven las lineas tal como se van a guardar, con su nota al lado.* */}
      {pegadas.length > 0 && (
        <ul className="mt-3 grid gap-2 text-[15px]">
          {pegadas.map((una, i) => {
            const elegido = elegidos[i]
            const encontrados = candidatos[i]
            return (
              <li
                key={`${una.nombre}-${i}`}
                className="rounded-campo border border-borde p-2"
              >
                <div className="flex flex-wrap items-baseline gap-2">
                  <span className="text-tinta-fuerte">{elegido?.nombre ?? una.nombre}</span>
                  {una.nota && (
                    <span className="text-tinta-suave">
                      queda anotado: {una.nota}
                    </span>
                  )}
                </div>

                {elegido ? (
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-etiqueta text-verde-fuerte">
                    <span>Vinculado al catálogo.</span>
                    <Boton
                      compacto
                      variante="sutil"
                      onClick={() => setElegidos((x) => ({ ...x, [i]: null }))}
                    >
                      Quitar vínculo
                    </Boton>
                  </div>
                ) : encontrados ? (
                  <div className="mt-1">
                    <p className="text-etiqueta text-tinta-suave">
                      ¿Es alguno de estos? Si no, se guarda tal como está.
                    </p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {encontrados.map((c) => (
                        <Boton
                          key={c.grupo_id}
                          compacto
                          variante="sutil"
                          onClick={() => setElegidos((x) => ({ ...x, [i]: c }))}
                        >
                          {c.nombre} · {euros(c.precio_cent)}
                          {c.cadena_mas_barata ? ` · ${nombreCadena(c.cadena_mas_barata)}` : ''}
                        </Boton>
                      ))}
                      {encontrados.length === 0 && (
                        <span className="text-etiqueta text-tinta-suave">
                          Sin coincidencias: se guarda como texto.
                        </span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Boton
                      compacto
                      variante="sutil"
                      onClick={() => void buscaCandidatos(i, una.nombre)}
                      disabled={Boolean(buscando[i])}
                    >
                      {buscando[i] ? 'Buscando…' : 'Buscar en el catálogo'}
                    </Boton>
                    {errores[i] && (
                      <span role="alert" className="text-etiqueta text-aviso">
                        {errores[i]}
                      </span>
                    )}
                  </div>
                )}
              </li>
            )
          })}
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
        <Boton
          variante="sutil"
          onClick={() => {
            setTexto('')
            setNombreArchivo(null)
            limpiaCoincidencias()
          }}
          disabled={!texto || guardando}
        >
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
