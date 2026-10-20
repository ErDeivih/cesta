/** Los favoritos: lo que se compra siempre, **por lo que se ha movido**.
 *
 *  Esta pantalla es de vigilancia, no un catalogo, y lo que se viene a saber es
 *  «¿se ha movido algo de lo que compro siempre?». Por eso el orden y la cifra que
 *  se enseña son el cambio: lo que ha bajado arriba (y lo que mas, primero),
 *  despues lo que ha subido, y al final lo que no se ha movido.
 *
 *  **Eso se decia aqui desde el primer dia y no se hacia.** El 30 de septiembre de
 *  2026, leyendo el codigo contra su propia documentacion: la API prometia ese orden
 *  y devolvia los favoritos en el orden en que se anadieron, y la pantalla enseñaba
 *  el precio de hoy sin decir si habia cambiado. Ahora el cambio lo mide
 *  `movimientos.cambios_de_grupos` (contra la captura anterior dentro de la
 *  ventana) y viene con lo que **no se puede comparar** dicho: `sin historico`,
 *  `cambio de formato` o `ya no esta en el catalogo`.
 *
 *  El diseño de la composicion es de Stitch (`.stitch/prompts/06-favoritos.txt`,
 *  pantalla «Cesta · Favoritos (Movil)», 30 de septiembre de 2026). Aqui se copia la
 *  composicion; los numeros, los tokens y las areas de 44 px los pone el codigo.
 *
 *  Necesita sesion, como la cesta: los favoritos son de cada uno.
 */
import { useState } from 'react'
import { listaDelDiario } from '../logica/listaDelDiario'
import { Link } from 'react-router-dom'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { verFavoritos, quitarFavorito } from '../api/favoritos'
import { anadirDesdeFavoritos, misListas } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { yo } from '../api/cesta'
import {
  eurosUnidad, fecha, nombreCadena, porcentaje, porcentajeConSigno,
} from '../api/formato'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Tarjeta, Vacio, cx } from '../componentes/ui'
import type { Favorito } from '../tipos'

/** Las ventanas que se pueden pedir. Siete dias es la que contesta «¿esta mas caro
 *  que la semana pasada?», que es la pregunta de la compra; treinta y noventa son
 *  para mirar una tendencia, y noventa solo tiene sentido porque el historico ya
 *  llega (24 capturas el 30 de septiembre de 2026). */
const VENTANAS = [7, 30, 90]

/** El desplegable de listas, con la ultima usada ya elegida.
 *
 *  Se guarda en el movil cual fue la ultima: quien pasa veinte favoritos a la lista
 *  de la semana no quiere elegir la misma lista veinte veces. */
function ElegirLista({ listas, valor, alCambiar, etiqueta }: {
  listas: { id: string; nombre: string }[]
  valor: string
  alCambiar: (id: string) => void
  etiqueta: string
}) {
  if (!listas.length) {
    return (
      <Link to="/cesta" className="text-cuerpo underline">
        Crea una lista para poder añadir
      </Link>
    )
  }
  return (
    <label className="flex items-center gap-2 text-cuerpo">
      <span className="text-tinta-suave">{etiqueta}</span>
      <select
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        className="min-h-[44px] rounded-campo border border-borde bg-papel px-2 "
      >
        {listas.map((l) => (
          <option key={l.id} value={l.id}>{l.nombre}</option>
        ))}
      </select>
    </label>
  )
}

/** El cambio, dicho con palabras y con la cifra.
 *
 *  **La palabra va con el color, no en lugar del color**: quien no distingue el verde del
 *  rojo tiene que poder leer «ha bajado». Y el porcentaje lleva siempre su ventana
 *  («en 7 dias»), porque un −8,7 % sin decir sobre cuanto no es un dato, es un adorno.
 *  Los dias que se dicen son los que hay **de verdad** (`dias_medidos`): un producto que
 *  lleva tres dias en el catalogo dice tres. */
function ElCambio({ f }: { f: Favorito }) {
  if (!f.comparable) return null
  // *** Y si no hay variacion, tampoco: `SinMedida` es quien lo explica. ***
  // *`?? 0` convertiria «no hay con que compararlo» en «no ha cambiado» -- y el propio
  // `SinMedida` dice, tres lineas mas abajo, que un «0 %» ahi es MENTIRA.*
  if (f.variacion_pct === null || f.variacion_pct === undefined) return null
  const pct = f.variacion_pct
  const dias = f.dias_medidos ?? f.dias ?? 7
  const sentido = pct < 0 ? 'baja' : pct > 0 ? 'sube' : 'igual'
  return (
    /* `data-cambio` es el gancho que usa la puerta para comprobar **el orden** sin depender de
       que hoy haya bajado algo: el sentido esta en el DOM como dato, no solo como color (que
       es justo lo que no puede distinguir quien no lo distingue). */
    <span data-cambio={sentido}>
      <Etiqueta tono={pct < 0 ? 'bien' : pct > 0 ? 'mal' : 'dato'}>
        {sentido === 'igual' ? 'igual' : `ha ${sentido === 'baja' ? 'bajado' : 'subido'}`}{' '}
        {pct === 0 ? '(0,0 %' : porcentajeConSigno(pct, 1)}
        {` en ${dias} ${dias === 1 ? 'día' : 'días'}`}
        {pct === 0 ? ')' : ''}
      </Etiqueta>
    </span>
  )
}

/** Por que no se puede decir cuanto ha cambiado.
 *
 *  Un «0 %» aqui seria mentira: no es que no se haya movido, es que no hay con que
 *  compararlo. Cada motivo se dice con su frase, y el del catalogo lleva ademas la salida
 *  (quitarlo), que es lo unico que se puede hacer con el. */
function SinMedida({ f, alQuitar, quitando }: {
  f: Favorito
  alQuitar: () => void
  quitando: boolean
}) {
  const frase = f.desconocido
    ? f.que === 'grupo'
      ? 'Este grupo ya no está en el catálogo: puede que sus productos hayan desaparecido o que el emparejador los haya separado.'
      : 'Este producto ya no está en el catálogo de su cadena.'
    : f.motivo === 'cambio de formato'
      ? 'Cambió el formato (la unidad o la cantidad), así que comparar el precio de hoy con el de antes no diría nada.'
      : 'Todavía no hay dos capturas que comparar: se añadió hace poco.'
  return (
    <Tarjeta>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-medium">
            {f.nombre ?? <span className="text-tinta-suave">Un producto que seguías</span>}
          </p>
          {f.marca && <p className="text-cuerpo text-tinta-suave">{f.marca}</p>}
        </div>
        <Etiqueta tono={f.desconocido ? 'aviso' : 'dato'}>
          {f.desconocido ? 'ya no está' : 'sin comparar'}
        </Etiqueta>
      </div>
      <p className="mt-2 text-cuerpo text-tinta-suave">{frase}</p>
      {f.precio_unidad_cent != null && (
        <p className="cifra mt-2 text-lg font-semibold">
          {eurosUnidad(f.precio_unidad_cent, f.unidad)}
        </p>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        {!f.desconocido && (
          <Link
            to={f.grupo_id != null ? `/grupo/${f.grupo_id}` : '/buscar'}
            className="inline-flex min-h-[44px] items-center rounded-campo border border-borde px-3 text-cuerpo "
          >
            {f.grupo_id != null ? 'Ver la ficha' : 'Buscar otro'}
          </Link>
        )}
        <Boton variante="sutil" disabled={quitando} onClick={alQuitar}>
          Quitar
        </Boton>
      </div>
    </Tarjeta>
  )
}

export function Favoritos() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const [ventana, setVentana] = useState(7)
  const favoritos = useQuery({
    queryKey: ['favoritos', ventana],
    queryFn: () => verFavoritos(ventana),
    enabled: sesion.data?.usuario != null,
  })
  // La lista a la que se pasan. Empieza por la primera que haya y se queda con lo
  // que elija la persona, sin volver a preguntarlo en cada tarjeta.
  const [destino, setDestino] = useState<string>('')
  const [dicho, setDicho] = useState<string | null>(null)
  const elegida = listaDelDiario(listas.data, destino) ?? ''

  const quitar = useMutation({
    mutationFn: (f: { grupo_id: number | null; producto_id?: string | null }) =>
      quitarFavorito(f.grupo_id, f.producto_id ?? null),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['favoritos'] }),
  })

  const pasar = useMutation({
    mutationFn: (f: { grupo_id?: number | null; producto_id?: string | null
                      todos?: Favorito[] }) => {
      const grupo_ids: number[] = []
      const producto_ids: string[] = []
      if (f.todos) {
        for (const x of f.todos) {
          if (x.grupo_id != null) grupo_ids.push(x.grupo_id)
          else if (x.producto_id) producto_ids.push(x.producto_id)
        }
      } else {
        if (f.grupo_id != null) grupo_ids.push(f.grupo_id)
        else if (f.producto_id) producto_ids.push(f.producto_id)
      }
      return anadirDesdeFavoritos(elegida, { grupo_ids, producto_ids })
    },
    onSuccess: (cuantos) => {
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', elegida] })
      cliente.invalidateQueries({ queryKey: ['reparto', elegida] })
      setDicho(cuantos === 1 ? 'Añadido a la lista' : `Añadidos ${cuantos} a la lista`)
      setTimeout(() => setDicho(null), 4000)
    },
  })

  if (sesion.isLoading || favoritos.isLoading) return <Cargando que="tus favoritos" />

  if (!sesion.data?.usuario) {
    // **El titulo de `Vacio` es el `h1`** (`comoPagina`): sin sesion esta pantalla **es** la
    // puerta, asi que el titulo es el titulo de la pagina. Antes llevaba un `h1` oculto al lado
    // para que la pagina no se quedara sin encabezado de nivel 1.
    return (
      <Vacio titulo="Entra para ver tus favoritos" comoPagina className="grow">
        <p>
          Los favoritos son tuyos, así que hacen falta tus listas. Se entra desde{' '}
          <Link to="/cesta" className="underline">la lista</Link>.
        </p>
      </Vacio>
    )
  }

  if (favoritos.isError) {
    // **`Fallo` y no un `Vacio` escrito aquí**, que es el mismo fallo que tenía la cesta y que
    // se arregló allí el 23 de septiembre de 2026: un cartel que dice «No he podido traerlos» y
    // **no deja volver a intentarlo** obliga a recargar la página a mano, que en el móvil no es
    // evidente. Además `Fallo` es quien decide el tono: sin cobertura no es rojo. Medido con la
    // puerta el 27 de septiembre de 2026, al ampliar la prueba de errores de cuatro pantallas a
    // doce: era la única sin botón.
    return <Fallo error={favoritos.error} reintentar={() => void favoritos.refetch()} />
  }

  const lista = favoritos.data?.favoritos ?? []
  const fechaDatos = favoritos.data?.fecha_datos
  const nombreDeDestino = listas.data?.find((l) => l.id === elegida)?.nombre
  // Los que se pueden ordenar por su cambio y los que no. La API ya los manda en el orden
  // bueno; aqui solo se parten para poder decir **por que** los de abajo no tienen cifra.
  const conCambio = lista.filter((f) => f.comparable)
  const sinCambio = lista.filter((f) => !f.comparable)

  if (!lista.length) {
    return (
      /* **El caso vacío da por dónde empezar, y esto es lo mismo que se arregló en los avisos.**
         Antes decía dónde se añaden («desde la ficha de un producto, con el corazón») y no daba
         forma de llegar: en la pantalla que está a un toque de la barra de abajo, un callejón
         sin salida. Medido en una captura de un móvil el 27 de septiembre de 2026. */
      <Tarjeta>
        {/* `h1` y no `p`: en el caso vacio esta tarjeta **es** la pantalla, y sin encabezado la
            pagina se quedaba sin titulo (lo midio `data/debug/accesibilidad.py`). El estilo es
            el mismo: lo que cambia es lo que oye quien navega por encabezados. */}
        <h2 className="text-entrada font-semibold">No sigues ningún producto</h2>
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Aquí van los pocos que compras siempre, para ver si se mueven sin tener que
          buscarlos. Se añaden desde la ficha de un producto, con el corazón.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link
            to="/buscar"
            className="inline-flex min-h-[44px] items-center rounded-campo bg-terracota px-3 text-cuerpo font-semibold text-papel "
          >
            Buscar un producto
          </Link>
          <Link
            to="/cesta"
            className="inline-flex min-h-[44px] items-center rounded-campo border border-borde px-3 text-cuerpo "
          >
            Ver mi lista
          </Link>
        </div>
      </Tarjeta>
    )
  }

  return (
    <div className="grid gap-4">
      <header className="grid gap-2">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-xl font-semibold">Favoritos</h2>
          {fechaDatos && <Etiqueta tono="dato">datos del {fecha(fechaDatos)}</Etiqueta>}
        </div>
        <p className="text-cuerpo text-tinta-suave">
          Ordenados por lo que se han movido: primero lo que ha bajado, después lo que ha
          subido, y al final lo que no se ha movido. Los precios son por unidad, que es lo
          único comparable entre formatos.
        </p>

        {/* La ventana, dicha con palabras y no con una flecha: «7 días» puesto y «Ventana
            activa: 7 días» debajo, porque un botón pulsado se distingue por el color y el
            color no puede ser la única señal. */}
        <div
          role="group"
          aria-label="Ventana para medir el cambio"
          className="flex flex-wrap gap-2"
        >
          {VENTANAS.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={ventana === d}
              onClick={() => setVentana(d)}
              className={cx(
                'min-h-[44px] rounded-campo border px-3 text-cuerpo font-medium tabular-nums',
                ventana === d
                  ? 'border-terracota bg-terracota text-papel '
                  : 'border-borde ',
              )}
            >
              {d} días
            </button>
          ))}
        </div>
        <p className="text-etiqueta text-tinta-suave" aria-live="polite">
          Ventana activa: {ventana} días
        </p>

        {/* Lo que hace util tener favoritos: pasarlos a la lista de la compra. */}
        <div className="flex flex-wrap items-center gap-3">
          <ElegirLista listas={listas.data ?? []} valor={elegida}
                       alCambiar={setDestino} etiqueta="Añadir a" />
          <Boton
            variante="principal"
            disabled={!elegida || pasar.isPending}
            onClick={() => pasar.mutate({ todos: lista })}
          >
            {pasar.isPending ? 'Añadiendo…' : `Añadir los ${lista.length} a la lista`}
          </Boton>
          <Link to="/cesta" className="text-cuerpo underline">
            {nombreDeDestino ? `Ver «${nombreDeDestino}»` : 'Ver la lista'}
          </Link>
        </div>
        {dicho && <Aviso tono="bien" titulo={dicho}>Se puede cambiar de tienda dentro de la lista.</Aviso>}
        {pasar.isError && (
          <Aviso tono="mal" titulo="No he podido añadirlos">
            {textoDeError(pasar.error)}
          </Aviso>
        )}
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {conCambio.map((f, n) => {
          const clave = f.producto_id ?? `g${f.grupo_id ?? n}`
          const cadena = f.cadena ?? f.fuente ?? null
          return (
            <Tarjeta key={clave}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  {f.grupo_id != null ? (
                    <Link to={`/grupo/${f.grupo_id}`} className="font-medium underline">
                      {f.nombre}
                    </Link>
                  ) : (
                    <span className="font-medium">{f.nombre}</span>
                  )}
                  {f.marca && (
                    <p className="text-cuerpo text-tinta-suave">{f.marca}</p>
                  )}
                </div>
                <ElCambio f={f} />
              </div>

              <p className="cifra mt-2 text-lg font-semibold">
                {eurosUnidad(f.precio_unidad_cent, f.unidad)}
                {/* El de antes, tachado: es lo que hace legible la cifra del cambio -- de un
                    −8,7 % no se sabe si es mucho o poco hasta que se ve de cuanto a cuanto. */}
                {f.precio_unidad_antes_cent != null
                  && f.precio_unidad_antes_cent !== f.precio_unidad_cent && (
                  <span className="ml-2 text-cuerpo font-normal text-tinta-suave line-through">
                    antes {eurosUnidad(f.precio_unidad_antes_cent, f.unidad)}
                  </span>
                )}
              </p>
              <p className="text-cuerpo text-tinta-suave">
                {cadena && <>en {nombreCadena(cadena)}</>}
                {f.ahorro_pct != null && f.ahorro_pct > 0 && (
                  // *La diferencia es **del grupo**, no de este articulo: puede ser otra marca con su
                  // propio EAN. Se dice «del grupo» para que no se lea como el ahorro de este.*

                  <> · −{porcentaje(f.ahorro_pct, 0)} frente a la más cara del grupo</>
                )}
                {f.n_cadenas != null && f.n_cadenas > 1 && (
                  <> · {f.n_cadenas} cadenas</>
                )}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                <Boton
                  variante="principal"
                  disabled={!elegida || pasar.isPending}
                  onClick={() => pasar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                >
                  A la lista
                </Boton>
                <Boton
                  variante="sutil"
                  disabled={quitar.isPending}
                  onClick={() => quitar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                >
                  Quitar
                </Boton>
              </div>
            </Tarjeta>
          )
        })}
      </div>

      {/* **El grupo de los que no se pueden comparar, al final y con su motivo.** Antes esto
          no existia: un favorito sin historico se pintaba igual que los demas, con su precio y
          sin decir nada del cambio, y eso se lee como «no se ha movido». */}
      {sinCambio.length > 0 && (
        <section className="grid gap-3" aria-label="Sin cambio que medir todavía">
          <div>
            <h2 className="text-entrada font-semibold">Sin cambio que medir todavía</h2>
            <p className="text-cuerpo text-tinta-suave">
              Estos no se pueden comparar en la ventana de {ventana} días, y se dice por qué
              en vez de enseñar un cero.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sinCambio.map((f, n) => (
              <SinMedida
                key={f.producto_id ?? `g${f.grupo_id ?? n}`}
                f={f}
                quitando={quitar.isPending}
                alQuitar={() => quitar.mutate({
                  grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                })}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}