/** El recetario: **lo que cocinas**, con sus recetas y sus versiones.
 *
 *  La composicion es la del artboard aprobado (`designs/cesta-app/project/Recetas.dc.html`):
 *  volver, el titulo, las pestanas, una tarjeta por receta con sus raciones y sus minutos, y
 *  «Crear una receta» al final. Los valores -- marfil, papel, bosque, tipos, radios y movimiento --
 *  son los del sistema «Cesta App», no se eligen aqui.
 *
 *  **Dos pestanas, y la segunda no es un adorno.** El artboard pinta «Recetario» y «Mis
 *  recetas»; en la aplicacion **todas las recetas son ya del usuario** (el almacen es por
 *  persona y no hay recetas de la casa), asi que dos pestanas con el mismo contenido serian
 *  una mentira. La segunda es **Archivadas**, que es la unica division real que existe: la
 *  receta archivada no se borra y se puede volver a mirar.
 *
 *  **El coste no se inventa.** La lista de recetas no trae ingredientes ni precios, asi que
 *  cada tarjeta dice «Faltan precios» en vez de un total que no se puede calcular. El coste,
 *  cuando lo hay, se ve en el detalle de la receta, que es donde llegan los precios.
 *
 *  Lo que no se pierde de la version anterior: la puerta de sesion, el buscador, el filtro por
 *  etiqueta, el alta, el error de archivar con su motivo, las archivadas y los estados de
 *  carga, vacio y error con reintento.
 */
import { useId, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { useArchivarReceta, useCrearReceta, useRecetas } from '../api/recetas'
import type { Ingrediente } from '../api/recetas'
import { textoDeError } from '../api/cliente'
import { yo } from '../api/cesta'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Vacio, cx } from '../componentes/ui'
import { EntraParaVer } from '../componentes/PuertaDeSesion'
import { etiquetasDe, filtraRecetas } from '../logica/recetario'

/* ================================================================ utilidades === */

/** Una linea del area de texto a ingrediente. **Sin cantidad no se inventa una.**
 *
 *  «600 g patatas» se guarda con su cantidad y su unidad; «sal» se guarda como texto y ya.
 *  Se acepta la coma decimal porque es como se escribe en una cocina en espanol.
 */
export function ingredientesDeTexto(texto: string): Ingrediente[] {
  return texto
    .split('\n')
    .map((linea) => linea.trim())
    .filter((linea) => linea.length > 0)
    .map((linea) => {
      const trozos = linea.split(' ')
      const cantidad = Number(trozos[0]?.replace(',', '.'))
      if (Number.isFinite(cantidad) && trozos.length > 2) {
        return { texto: trozos.slice(2).join(' '), cantidad, unidad: trozos[1] }
      }
      return { texto: linea }
    })
}

/** «4 raciones · 30 min» o «1 ración», sin dejar un « · » colgando. */
export function metaDeLaReceta(r: {
  raciones: number
  minutos: number | null
  archivada?: boolean
}): string {
  const trozos = [`${r.raciones} ${r.raciones === 1 ? 'ración' : 'raciones'}`]
  if (r.minutos != null && r.minutos > 0) trozos.push(`${r.minutos} min`)
  if (r.archivada) trozos.push('archivada')
  return trozos.join(' · ')
}

/** Lo que se dice cuando un filtro esconde todo. Con el filtro que lo causo, no un cero. */
function textoDelFiltro(texto: string, etiqueta: string, cuantas: number): string {
  const partes: string[] = []
  if (texto.trim()) partes.push(`«${texto.trim()}»`)
  if (etiqueta) partes.push(`la etiqueta «${etiqueta}»`)
  const cuantasTexto = cuantas === 1 ? '1 receta' : `${cuantas} recetas`
  if (partes.length === 0) return 'No hay nada que enseñar.'
  return `Ninguna receta coincide con ${partes.join(' y ')}. Hay ${cuantasTexto}.`
}

/* ==================================================================== la alta === */

/** El alta de una receta. **El formulario solo; quien lo abre es la pantalla.**
 *
 *  Asi el boton de «Crear una receta» y el vacio pueden abrir el mismo formulario sin
 *  duplicar el estado ni enseñar dos botones iguales.
 */
function Alta({ alCerrar }: { alCerrar: () => void }) {
  const [nombre, setNombre] = useState('')
  const [raciones, setRaciones] = useState(2)
  const [minutos, setMinutos] = useState(0)
  const [etiquetas, setEtiquetas] = useState('')
  const [preparacion, setPreparacion] = useState('')
  const [ingredientes, setIngredientes] = useState('')
  const crear = useCrearReceta()

  return (
    <section
      aria-labelledby="nueva-receta"
      className="rounded-tarjeta border border-borde bg-papel p-4 shadow-apoyado"
    >
      <h2 id="nueva-receta" className="font-display text-subtitulo font-semibold text-tinta">
        Nueva receta
      </h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          crear.mutate(
            {
              nombre: nombre.trim(),
              raciones: Math.max(1, raciones || 1),
              preparacion,
              minutos: Number.isFinite(minutos) && minutos > 0 ? minutos : null,
              etiquetas: etiquetas.trim(),
              ingredientes: ingredientesDeTexto(ingredientes),
            },
            {
              onSuccess: () => {
                setNombre('')
                setPreparacion('')
                setIngredientes('')
                setEtiquetas('')
                setMinutos(0)
                alCerrar()
              },
            },
          )
        }}
        className="mt-3 flex flex-col gap-3"
      >
        <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
          Nombre
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
            className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta"
          />
        </label>

        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Raciones
            <input
              type="number"
              min={1}
              value={raciones}
              onChange={(e) => setRaciones(Number(e.target.value))}
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] tabular-nums text-tinta"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Minutos
            <input
              type="number"
              min={0}
              value={minutos}
              onChange={(e) => setMinutos(Number(e.target.value))}
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] tabular-nums text-tinta"
            />
          </label>
        </div>

        <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
          Ingredientes, uno por línea
          <textarea
            value={ingredientes}
            onChange={(e) => setIngredientes(e.target.value)}
            rows={4}
            placeholder={'600 g patatas\n5 ud huevos'}
            className="rounded-campo border border-borde-fuerte bg-papel p-3 text-[16px] leading-6 text-tinta placeholder:text-tinta-tenue"
          />
        </label>

        <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
          Preparación
          <textarea
            value={preparacion}
            onChange={(e) => setPreparacion(e.target.value)}
            rows={3}
            className="rounded-campo border border-borde-fuerte bg-papel p-3 text-[16px] leading-6 text-tinta"
          />
        </label>

        <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
          Etiquetas, separadas por comas
          <input
            value={etiquetas}
            onChange={(e) => setEtiquetas(e.target.value)}
            placeholder="cena, rápida"
            className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta placeholder:text-tinta-tenue"
          />
        </label>

        {crear.error && (
          <Aviso tono="mal" titulo="No he podido guardarla">
            {textoDeError(crear.error)}
          </Aviso>
        )}

        <div className="flex flex-wrap gap-2">
          <Boton type="submit" variante="principal" disabled={crear.isPending || !nombre.trim()}>
            {crear.isPending ? 'Guardando…' : 'Guardar receta'}
          </Boton>
          <Boton onClick={alCerrar} disabled={crear.isPending}>
            Cancelar
          </Boton>
        </div>
      </form>
    </section>
  )
}

/* ================================================================== la tarjeta === */

/** Una receta en la lista: nombre, raciones y minutos. **El coste se dice, no se rellena.**
 *
 *  La lista de la API no trae ingredientes ni precios, asi que no hay forma de calcular un
 *  total aqui. «Faltan precios» es la verdad de esta pantalla; el coste, cuando exista, se ve
 *  al abrir la receta.
 */
function TarjetaDeReceta({ children, nombre, meta, archivada, alAbrir }: {
  children?: ReactNode
  nombre: string
  meta: string
  archivada: boolean
  alAbrir: string
}) {
  const id = useId()
  return (
    <li>
      <article className="rounded-tarjeta bg-papel shadow-apoyado">
        <Link
          to={alAbrir}
          aria-labelledby={id}
          className="flex min-h-[64px] flex-col gap-1 rounded-tarjeta p-4 transition-colors duration-rapida ease-suave hover:bg-marfil"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 id={id} className="break-words text-cuerpo-fuerte text-tinta">
                {nombre}
              </h3>
              <p className="mt-0.5 text-etiqueta text-tinta-tenue">{meta}</p>
            </div>
            <span className="shrink-0 text-right text-etiqueta text-tinta-tenue">
              {archivada ? 'Archivada' : 'Faltan precios'}
            </span>
          </div>
        </Link>
        {children}
      </article>
    </li>
  )
}

/* ================================================================ la pantalla === */

/** La puerta de sesion, **la pieza compartida**: el recetario se guarda con la cuenta. */
function Puerta() {
  return <EntraParaVer texto="El recetario se guarda con tu cuenta." />
}

export function Recetario() {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  if (sesion.isPending) return <Cargando que="tu recetario" filas={3} />
  if (!sesion.data?.usuario) return <Puerta />
  return <RecetarioConSesion />
}

type Pestana = 'recetario' | 'archivadas'

function RecetarioConSesion() {
  const [pestana, setPestana] = useState<Pestana>('recetario')
  const [texto, setTexto] = useState('')
  const [etiqueta, setEtiqueta] = useState('')
  const [creando, setCreando] = useState(false)

  // **Una sola consulta con las archivadas**, no una por pestana: el recetario de una persona
  // es pequeño, y asi los dos contadores dicen la verdad sin pedir dos veces lo mismo.
  const recetas = useRecetas(true)
  const archivar = useArchivarReceta()

  const todas = recetas.data?.recetas ?? []
  const activas = todas.filter((r) => !r.archivada)
  const archivadas = todas.filter((r) => r.archivada)
  const deLaPestana = pestana === 'recetario' ? activas : archivadas
  // **La archivada no se esconde por estar archivada**: ya se ha elegido su pestana.
  const visibles = filtraRecetas(deLaPestana, {
    texto,
    etiqueta: etiqueta || null,
    incluirArchivadas: pestana === 'archivadas',
  })
  const etiquetas = etiquetasDe(deLaPestana)
  const hayFiltro = texto.trim().length > 0 || etiqueta.length > 0
  const cuantas = todas.length

  return (
    <div className="flex min-h-full flex-col gap-5">
      {/* ------------------------------------------ volver, donde estas y el titulo */}
      <header className="flex items-start gap-2">
        <Link
          to="/"
          aria-label="Volver a la portada"
          className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M19 12H5M11 18l-6-6 6-6" />
          </svg>
        </Link>
        <div className="min-w-0 flex-1">
          <p className="text-micro uppercase text-tinta-tenue">Recetas</p>
          <h2 className="mt-1 break-words font-display text-titulo font-semibold text-tinta">
            Qué cocinamos
          </h2>
        </div>
        {activas.length > 0 && (
          <span className="shrink-0 pt-2 text-right text-etiqueta text-tinta-tenue">
            {activas.length} {activas.length === 1 ? 'receta' : 'recetas'}
          </span>
        )}
      </header>

      {/* ------------------------------------------------------ las dos pestanas */}
      <div role="tablist" aria-label="Recetas" className="flex flex-wrap gap-2">
        <BotonDePestana
          activa={pestana === 'recetario'}
          cuantas={activas.length}
          onClick={() => setPestana('recetario')}
          id="pestana-recetario"
        >
          Recetario
        </BotonDePestana>
        <BotonDePestana
          activa={pestana === 'archivadas'}
          cuantas={archivadas.length}
          onClick={() => setPestana('archivadas')}
          id="pestana-archivadas"
        >
          Archivadas
        </BotonDePestana>
      </div>

      <div
        role="tabpanel"
        id="panel-recetas"
        aria-labelledby={pestana === 'recetario' ? 'pestana-recetario' : 'pestana-archivadas'}
        className="flex flex-col gap-3"
      >
        {recetas.isPending && <Cargando que="tu recetario" filas={3} />}

        {recetas.error && (
          <Fallo
            error={recetas.error}
            reintentar={() => void recetas.refetch()}
            titulo="No he podido traer tu recetario"
          />
        )}

        {!recetas.isPending && !recetas.error && cuantas === 0 && (
          <Vacio titulo="Todavía no hay recetas" className="grow">
            <p>Añade la primera y aparecerá aquí, con sus ingredientes y sus raciones.</p>
            {!creando && (
              <Boton
                variante="principal"
                className="mt-3"
                onClick={() => setCreando(true)}
              >
                Crear la primera receta
              </Boton>
            )}
          </Vacio>
        )}

        {!recetas.isPending && !recetas.error && cuantas > 0 && (
          <>
            {/* --------------------------------------------- buscar y filtrar */}
            <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
              <label htmlFor="buscar-receta" className="sr-only">
                Buscar recetas por nombre
              </label>
              <input
                id="buscar-receta"
                type="search"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Buscar por nombre…"
                className="min-h-[44px] w-full min-w-0 rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta placeholder:text-tinta-tenue sm:flex-1"
              />
              {etiquetas.length > 0 && (
                <>
                  <label htmlFor="filtrar-etiqueta" className="sr-only">
                    Filtrar por etiqueta
                  </label>
                  <select
                    id="filtrar-etiqueta"
                    value={etiqueta}
                    onChange={(e) => setEtiqueta(e.target.value)}
                    className="min-h-[44px] max-w-full rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-[16px] text-tinta"
                  >
                    <option value="">Todas las etiquetas</option>
                    {etiquetas.map((e) => (
                      <option key={e} value={e}>{e}</option>
                    ))}
                  </select>
                </>
              )}
            </div>

            {/* ------------------------------------------ el vacio de cada caso */}
            {visibles.length === 0 && hayFiltro && (
              <Vacio titulo="Ninguna receta coincide">
                <p>{textoDelFiltro(texto, etiqueta, deLaPestana.length)}</p>
                <Boton
                  variante="normal"
                  className="mt-3"
                  onClick={() => { setTexto(''); setEtiqueta('') }}
                >
                  Quitar los filtros
                </Boton>
              </Vacio>
            )}

            {visibles.length === 0 && !hayFiltro && pestana === 'archivadas' && (
              <Vacio titulo="No hay recetas archivadas">
                <p>Cuando archives una, aparecerá aquí. No se borra.</p>
                <Boton
                  variante="normal"
                  className="mt-3"
                  onClick={() => setPestana('recetario')}
                >
                  Ver el recetario
                </Boton>
              </Vacio>
            )}

            {visibles.length === 0 && !hayFiltro && pestana === 'recetario' && (
              <Vacio titulo="El recetario está vacío">
                <p>Tienes las recetas en «Archivadas». Se pueden volver a abrir.</p>
                <Boton
                  variante="normal"
                  className="mt-3"
                  onClick={() => setPestana('archivadas')}
                >
                  Ver las archivadas
                </Boton>
              </Vacio>
            )}

            {visibles.length > 0 && (
              <ul className="flex flex-col gap-3">
                {visibles.map((r) => (
                  <TarjetaDeReceta
                    key={r.id}
                    nombre={r.nombre}
                    meta={metaDeLaReceta(r)}
                    archivada={r.archivada}
                    alAbrir={`/recetas/${r.id}`}
                  >
                    {!r.archivada && (
                      <div className="flex flex-wrap items-center gap-2 border-t border-borde px-4 py-1">
                        <button
                          type="button"
                          onClick={() => archivar.mutate(r.id)}
                          disabled={archivar.isPending}
                          className="inline-flex min-h-[44px] items-center text-etiqueta text-tinta-suave underline underline-offset-2 transition-colors duration-rapida ease-suave hover:text-tinta disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {archivar.isPending && archivar.variables === r.id
                            ? 'Archivando…'
                            : 'Archivar'}
                        </button>
                        {/* **El error, en la receta que lo causo.** *Un aviso que sale en
                            todas las tarjetas a la vez no dice cual fallo.* */}
                        {archivar.error && !r.archivada && archivar.variables === r.id && (
                          <Etiqueta tono="mal">{textoDeError(archivar.error)}</Etiqueta>
                        )}
                      </div>
                    )}
                  </TarjetaDeReceta>
                ))}
              </ul>
            )}
          </>
        )}

        {/* ------------------------------------------------- crear e importar */}
        {!recetas.error && (
          <div className="mt-1 flex flex-col gap-2">
            {creando ? (
              <Alta alCerrar={() => setCreando(false)} />
            ) : (
              cuantas > 0 && (
                <button
                  type="button"
                  onClick={() => setCreando(true)}
                  className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-campo border border-dashed border-borde-fuerte px-4 text-cuerpo text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
                >
                  <span aria-hidden="true">+</span>
                  Crear una receta
                </button>
              )
            )}
            <Link
              to="/compra/importar"
              className="inline-flex min-h-[44px] items-center justify-center text-cuerpo text-terracota underline underline-offset-2 transition-colors duration-rapida ease-suave hover:text-tinta"
            >
              Importar desde una web
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

/** Una pestana, con su contador. 44 px y `aria-selected`: no es un adorno de color. */
function BotonDePestana({ activa, cuantas, onClick, id, children }: {
  activa: boolean
  cuantas: number
  onClick: () => void
  id: string
  children: ReactNode
}) {
  return (
    <button
      type="button"
      role="tab"
      id={id}
      aria-selected={activa}
      aria-controls="panel-recetas"
      onClick={onClick}
      className={cx(
        'inline-flex min-h-[44px] items-center gap-2 rounded-pastilla px-4 text-cuerpo font-semibold',
        'transition-colors duration-rapida ease-suave',
        activa
          ? 'bg-bosque text-sobre-bosque'
          : 'border border-borde-fuerte bg-papel text-tinta hover:bg-marfil',
      )}
    >
      {children}
      <span className={cx('cifra text-etiqueta', activa ? 'text-sobre-bosque' : 'text-tinta-tenue')}>
        {cuantas}
      </span>
    </button>
  )
}
