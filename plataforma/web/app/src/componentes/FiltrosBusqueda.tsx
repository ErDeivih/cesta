/** La barra de filtros del buscador.
 *
 *  En el movil van **plegados** salvo el buscador y las cadenas: la mayoria de
 *  las busquedas no usan filtros, y cada fila de filtros es una fila de
 *  resultados que no se ve. El boton dice cuantos hay puestos, para que nadie
 *  mire una lista corta sin saber por que es corta.
 *
 *  Un filtro que la API no aplicaria se desactiva en vez de mentir: la lista de
 *  sellos es la que acepta el backend (`SELLOS_FILTRABLES`). El backend ignora
 *  en silencio un sello que no conoce, asi que mandar uno inventado daria una
 *  lista sin filtrar y con pinta de filtrada.
 */
import { useId } from 'react'

import { useSecciones } from '../api/consultas'
import type { FiltrosBuscar } from '../api/consultas'
import { nombreCadena, selloLegible } from '../api/formato'
import { Casilla, Etiqueta, Resumen, Selector, cx } from './ui'

/** Los ocho que acepta `catalogo.SELLOS_FILTRABLES` (docs/API.md). */
export const SELLOS = [
  'sin-gluten',
  'sin-lactosa',
  'vegano',
  'vegetariano',
  'ecologico',
  'sin-azucar',
  'sin-sal',
  'sin-aceite-palma',
] as const

const CONSERVACIONES = [
  { valor: 'refrigerado', texto: 'Refrigerado' },
  { valor: 'congelado', texto: 'Congelado' },
  { valor: 'ambiente', texto: 'Ambiente' },
] as const

interface Props {
  filtros: FiltrosBuscar
  cadenasDisponibles: string[]
  onCambio: (f: FiltrosBuscar) => void
  cuantosPuestos: number
}

export function FiltrosBusqueda({ filtros, cadenasDisponibles, onCambio, cuantosPuestos }: Props) {
  const secciones = useSecciones(filtros.cadenas)
  const idSeccion = useId()

  const alternaCadena = (cadena: string) => {
    const puestas = filtros.cadenas.includes(cadena)
      ? filtros.cadenas.filter((c) => c !== cadena)
      : [...filtros.cadenas, cadena]
    onCambio({ ...filtros, cadenas: puestas })
  }

  const alternaSello = (sello: string) => {
    const puestos = filtros.sellos.includes(sello)
      ? filtros.sellos.filter((s) => s !== sello)
      : [...filtros.sellos, sello]
    onCambio({ ...filtros, sellos: puestos })
  }

  return (
    <details
      open={cuantosPuestos > 0}
      className="rounded-tarjeta border border-borde bg-papel p-3 "
    >
      <Resumen className="text-cuerpo font-medium">
        Filtros
        {cuantosPuestos > 0 && <Etiqueta tono="info">{cuantosPuestos}</Etiqueta>}
        <span className="text-etiqueta font-normal text-tinta-suave">
          cadena, pasillo, dieta, ofertas…
        </span>
      </Resumen>

      <div className="mt-3 grid gap-4">
        <fieldset>
          <legend className="mb-1 text-etiqueta font-medium text-secundaria ">
            Cadena
          </legend>
          <div className="flex flex-wrap gap-2">
            {cadenasDisponibles.length === 0 && (
              <p className="text-cuerpo text-tinta-suave">
                No sé qué cadenas hay: `/api/estado` no ha contestado.
              </p>
            )}
            {cadenasDisponibles.map((c) => (
              <button
                key={c}
                type="button"
                aria-pressed={filtros.cadenas.includes(c)}
                onClick={() => alternaCadena(c)}
                className={cx(
                  'min-h-[44px] rounded-campo border px-3 py-1 text-cuerpo font-medium',
                  filtros.cadenas.includes(c)
                    ? 'border-terracota bg-terracota text-papel '
                    : 'border-borde bg-papel hover:bg-marfil dark:hover:bg-papel',
                )}
              >
                {/* `nombreCadena` y no `{c}`: el identificador viene en minusculas (`alcampo`)
                    y asi se veia -- «alcampo», «dia» -- en las cinco pantallas que tienen
                    estas pastillas, mientras la ficha del grupo decia «Aldi» y «DIA». */}
                {nombreCadena(c)}
              </button>
            ))}
          </div>
          {filtros.cadenas.length === 0 && cadenasDisponibles.length > 0 && (
            <p className="mt-1 text-etiqueta text-tinta-suave">
              Sin ninguna marcada se usan todas, o tus cadenas de casa si las tienes guardadas.
            </p>
          )}
        </fieldset>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label
              htmlFor={idSeccion}
              className="mb-1 block text-etiqueta font-medium text-secundaria "
            >
              Pasillo
            </label>
            <select
              id={idSeccion}
              value={filtros.seccion}
              onChange={(e) => onCambio({ ...filtros, seccion: e.target.value })}
              className="min-h-[44px] w-full rounded-campo border border-borde bg-papel px-3 py-2 "
            >
              <option value="">Todos</option>
              {secciones.data?.secciones.map((s) => (
                <option key={s.seccion} value={s.seccion}>
                  {s.nombre} ({s.productos})
                </option>
              ))}
            </select>
            {secciones.data && secciones.data.secciones.length === 0 && (
              <p className="mt-1 text-etiqueta text-tinta-suave">
                Todavía no hay pasillos en gold: falta que el scraper escriba la columna `seccion`.
                Explorar un pasillo se hace sin texto, así que en cuanto estén, esto funciona.
              </p>
            )}
          </div>

          <Selector
            etiqueta="Conservación"
            value={filtros.conservacion}
            onChange={(e) => onCambio({ ...filtros, conservacion: e.target.value })}
          >
            <option value="">Cualquiera</option>
            {CONSERVACIONES.map((c) => (
              <option key={c.valor} value={c.valor}>
                {c.texto}
              </option>
            ))}
          </Selector>

          <Selector
            etiqueta="Cuántos resultados"
            value={String(filtros.limite)}
            onChange={(e) => onCambio({ ...filtros, limite: Number(e.target.value) })}
          >
            <option value="40">40</option>
            <option value="80">80</option>
            <option value="120">120</option>
          </Selector>
        </div>

        <fieldset>
          <legend className="mb-1 text-etiqueta font-medium text-secundaria ">
            Dieta y sellos
          </legend>
          <div className="flex flex-wrap gap-2">
            {SELLOS.map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={filtros.sellos.includes(s)}
                onClick={() => alternaSello(s)}
                className={cx(
                  'min-h-[44px] rounded-campo border px-3 py-1 text-cuerpo',
                  filtros.sellos.includes(s)
                    ? 'border-terracota bg-terracota text-papel '
                    : 'border-borde bg-papel hover:bg-marfil dark:hover:bg-papel',
                )}
              >
                {selloLegible(s)}
              </button>
            ))}
          </div>
          <p className="mt-1 text-etiqueta text-tinta-suave">
            Los sellos se comprueban en cada producto que se enseña, no en el grupo: si un miembro
            del grupo no lo cumple, no sale.
          </p>
        </fieldset>

        <fieldset className="flex flex-wrap gap-2">
          <legend className="mb-1 text-etiqueta font-medium text-secundaria ">
            Otras
          </legend>
          <Casilla
            etiqueta="Solo comparables entre cadenas"
            checked={filtros.comparables}
            onChange={(e) => onCambio({ ...filtros, comparables: e.target.checked })}
          />
          <Casilla
            etiqueta="Solo con nutrición"
            checked={filtros.conNutricion}
            onChange={(e) => onCambio({ ...filtros, conNutricion: e.target.checked })}
          />
          <Casilla
            etiqueta="Solo ofertas de hoy"
            checked={filtros.ofertas}
            onChange={(e) => onCambio({ ...filtros, ofertas: e.target.checked })}
          />
          <Casilla
            etiqueta="Solo marca propia"
            checked={filtros.marcaPropia}
            onChange={(e) => onCambio({ ...filtros, marcaPropia: e.target.checked })}
          />
          <Casilla
            etiqueta="Sin alcohol"
            checked={filtros.sinAlcohol}
            onChange={(e) => onCambio({ ...filtros, sinAlcohol: e.target.checked })}
          />
        </fieldset>

        <p className="text-etiqueta text-tinta-suave">
          «Solo ofertas de hoy» deja fuera las de tarjeta y las de solo internet: ninguna de las dos
          baja lo que pagas en caja.
        </p>
      </div>
    </details>
  )
}