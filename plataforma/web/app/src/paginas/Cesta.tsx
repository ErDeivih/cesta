/** La cesta: la lista de la compra, comparada entre cadenas.
 *
 *  Es la pantalla que faltaba para tener paridad con la interfaz vieja, y es
 *  media aplicacion: lo que se hace en el pasillo es mirar la lista, no buscar
 *  productos sueltos.
 *
 *  Tres decisiones que se ven en la pantalla y no son casualidad:
 *
 *  - **Los que faltan se dicen por su nombre**, no como un numero. "Te faltan 3"
 *    obliga a buscar cuales; la lista de nombres se lee de un tiron.
 *  - **Repartir entre varias tiendas solo se propone si compensa** (`merece_la_pena`,
 *    que son 1,50 EUR): una segunda parada por 40 centimos no es un ahorro, es una
 *    molestia con un numero delante.
 *  - **Un precio de mas de `dias_precio_valido` dias no decide.** Se ensena con su
 *    fecha y se dice, pero no se usa para elegir tienda.
 *
 *  La pantalla tambien **escribe**: tachar, cambiar la cantidad y quitar lineas.
 *  Lo que NO se copia de la interfaz vieja es su cola de cambios sin conexion
 *  (`cola.anade` y `/sincronizar`, app.js:630): aqui se escribe contra la API y,
 *  si falla, se dice. Sin esa cola, pintar el cambio antes de que conteste el
 *  servidor seria ensenar una lista que no existe, y la lista de la compra es
 *  justo lo que no puede mentir.
 */
import { useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { cambiarLinea, entrar, misListas, salir, verLista, donde, yo } from '../api/cesta'
import type { CambioLinea } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { euros } from '../api/formato'
import { Aviso, Boton, Cargando, Casilla, Etiqueta, Tarjeta, Vacio, cx } from '../componentes/ui'
import type { Linea } from '../tipos'

function Introducir({ alEntrar }: { alEntrar: () => void }) {
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const entrar_ = useMutation({
    mutationFn: () => entrar(usuario.trim(), clave),
    onSuccess: alEntrar,
  })

  return (
    <Tarjeta>
      <h2 className="mb-1 text-lg font-semibold">Entra para ver tu lista</h2>
      <p className="mb-4 text-sm text-tinta-suave">
        La lista de la compra es tuya y de quien la compartas. Por eso hay que
        entrar: una lista sin dueño no se puede compartir ni recuperar.
      </p>
      <form
        className="grid gap-3 sm:max-w-sm"
        onSubmit={(e) => {
          e.preventDefault()
          if (usuario.trim() && clave) entrar_.mutate()
        }}
      >
        <label className="grid gap-1">
          <span className="text-sm font-medium">Usuario</span>
          <input
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoComplete="username"
            className="rounded-md border border-borde bg-fondo px-3 py-2"
          />
        </label>
        <label className="grid gap-1">
          <span className="text-sm font-medium">Clave</span>
          <input
            type="password"
            value={clave}
            onChange={(e) => setClave(e.target.value)}
            autoComplete="current-password"
            className="rounded-md border border-borde bg-fondo px-3 py-2"
          />
        </label>
        <Boton type="submit" disabled={entrar_.isPending}>
          {entrar_.isPending ? 'Entrando…' : 'Entrar'}
        </Boton>
        {entrar_.isError && (
          <p className="text-sm text-aviso">{textoDeError(entrar_.error)}</p>
        )}
      </form>
    </Tarjeta>
  )
}

function UnaTienda({ opcion, mejor }: {
  opcion: {
    cadena: string; total_cent: number; total_sin_ofertas_cent: number
    encontrados: number; faltan: string[]
  }
  mejor: number
}) {
  const ahorro = opcion.total_sin_ofertas_cent - opcion.total_cent
  return (
    <Tarjeta>
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold">{opcion.cadena}</h3>
        {opcion.total_cent === mejor && <Etiqueta tono="bien">la más barata</Etiqueta>}
        {ahorro > 0 && (
          <Etiqueta tono="dato">
            {euros(ahorro)} en ofertas
          </Etiqueta>
        )}
      </header>
      <p className="cifra text-2xl font-semibold">{euros(opcion.total_cent)}</p>
      <p className="mt-1 text-sm text-tinta-suave">
        {opcion.encontrados} de {opcion.encontrados + opcion.faltan.length} productos
      </p>
      {opcion.faltan.length > 0 && (
        <div className="mt-2">
          <p className="text-sm font-medium">No lo tiene:</p>
          <p className="text-sm text-tinta-suave">{opcion.faltan.join(' · ')}</p>
        </div>
      )}
    </Tarjeta>
  )
}

/** Una linea con lo que se hace con ella en el pasillo: tacharla, contarla y
 *  quitarla.
 *
 *  Tres cosas que se ven y estan decididas:
 *
 *  - **La casilla lleva el nombre del producto** dentro. Tocar el nombre para
 *    tachar la linea es el gesto que se hace con una mano y el carro en la otra;
 *    un cuadrado de 16 px al lado de un texto largo se falla.
 *  - **El menos no borra al llegar a 1.** La interfaz vieja si lo hacia
 *    (app.js:1641: `if (nueva < 1) return cambia(l.id, {borrado: true})`), y
 *    quitar una linea sin querer, cargada de bolsas, cuesta mas que un boton de
 *    mas. A 1 el boton se apaga y para quitarla esta "Quitar", que se ve.
 *  - **Sirve la misma mutacion para las tres cosas**: asi un solo cambio esta en
 *    vuelo a la vez y no se puede lanzar un tachado mientras se guarda una
 *    cantidad.
 */
function UnaLinea({ linea, guardando, cambiar }: {
  linea: Linea
  guardando: boolean
  cambiar: (lineaId: string, cambio: CambioLinea) => void
}) {
  const tachada = linea.tachado_en !== null

  return (
    <li className="flex flex-wrap items-center gap-2 rounded-lg border border-borde p-2">
      <Casilla
        etiqueta={
          <span className={cx(tachada && 'text-tinta-suave line-through')}>
            {linea.nombre_visto}
          </span>
        }
        checked={tachada}
        disabled={guardando}
        // El estado lo pone el servidor y `tachado` basta: la API mete en el
        // carro y tacha a la vez (`almacen.py:324`), asi que no son dos cosas
        // que puedan separarse.
        onChange={(e) => cambiar(linea.id, { tachado: e.target.checked })}
        className={cx('min-w-[12rem] flex-1', tachada && 'bg-bien-suave')}
      />

      <div className="flex items-center gap-1">
        {/* La cantidad que acepta la API es 1..99: fuera de ahi contesta 422, y
            un 422 por pulsar de mas no es una forma de enterarse. */}
        <Boton
          compacto
          disabled={guardando || linea.cantidad <= 1}
          aria-label={`Menos ${linea.nombre_visto}`}
          onClick={() => cambiar(linea.id, { cantidad: linea.cantidad - 1 })}
        >
          −
        </Boton>
        <span className="cifra w-8 text-center text-sm font-semibold">{linea.cantidad}</span>
        <Boton
          compacto
          disabled={guardando || linea.cantidad >= 99}
          aria-label={`Más ${linea.nombre_visto}`}
          onClick={() => cambiar(linea.id, { cantidad: linea.cantidad + 1 })}
        >
          +
        </Boton>
        <Boton
          compacto
          variante="peligro"
          disabled={guardando}
          aria-label={`Quitar ${linea.nombre_visto} de la lista`}
          onClick={() => cambiar(linea.id, { borrado: true })}
        >
          Quitar
        </Boton>
      </div>
    </li>
  )
}

export function Cesta() {
  const cliente = useQueryClient()
  const [elegida, setElegida] = useState<string | null>(null)

  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })

  const listaId = elegida ?? listas.data?.[0]?.id ?? null
  const detalle = useQuery({
    queryKey: ['lista', listaId],
    queryFn: () => verLista(listaId as string),
    enabled: listaId != null,
  })
  const compra = useQuery({
    queryKey: ['donde', listaId],
    queryFn: () => donde(listaId as string),
    enabled: listaId != null,
  })

  const cambia = useMutation({
    mutationFn: ({ lineaId, cambio }: { lineaId: string; cambio: CambioLinea }) =>
      cambiarLinea(listaId as string, lineaId, cambio),
    onSuccess: () => {
      // Se vuelve a pedir y se pinta lo que dice el servidor. El total, el
      // reparto entre cadenas y hasta el orden de las lineas cambian con cada
      // cambio, asi que adivinar el resultado seria inventarselo. Ademas, con
      // una lista compartida lo que conteste puede no ser lo que se pidio: si
      // los dos tachais a la vez gana el primero (`cambia_linea`, almacen.py:294),
      // y eso solo se ve recargando.
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      cliente.invalidateQueries({ queryKey: ['donde', listaId] })
    },
  })

  if (sesion.isLoading) return <Cargando que="tu sesión" />

  if (!sesion.data?.usuario) {
    return (
      <Introducir
        alEntrar={() => {
          // Al entrar hay que volver a preguntar quien soy y que listas tengo:
          // las de antes eran las de nadie.
          cliente.invalidateQueries({ queryKey: ['yo'] })
          cliente.invalidateQueries({ queryKey: ['listas'] })
        }}
      />
    )
  }

  if (listas.isLoading) return <Cargando que="tus listas" />
  if (listas.isError) {
    return <Vacio titulo="No he podido traer tus listas">
      <p>{textoDeError(listas.error)}</p>
    </Vacio>
  }
  if (!listas.data?.length) {
    return (
      <Vacio titulo="No tienes ninguna lista">
        <p>
          Todavía no hay listas guardadas. Busca un producto, abre su ficha y
          pulsa «Añadir a la cesta»: la lista de casa se crea sola.
        </p>
      </Vacio>
    )
  }

  const mejorTotal = compra.data?.una_tienda?.length
    ? Math.min(...compra.data.una_tienda.map((t) => t.total_cent))
    : null

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">La cesta</h1>
        {listas.data.length > 1 && (
          <select
            value={listaId ?? ''}
            onChange={(e) => setElegida(e.target.value)}
            className="rounded-md border border-borde bg-fondo px-2 py-1"
          >
            {listas.data.map((l) => (
              <option key={l.id} value={l.id}>{l.nombre}</option>
            ))}
          </select>
        )}
        <button
          className="ml-auto text-sm text-tinta-suave underline"
          onClick={async () => {
            await salir()
            cliente.invalidateQueries()
          }}
        >
          Salir
        </button>
      </header>

      {detalle.isLoading && <Cargando que="la lista" />}
      {cambia.isError && (
        <Aviso tono="mal" titulo="No he podido guardar el cambio">
          <p>{textoDeError(cambia.error)}</p>
          <p className="mt-1">
            La lista sigue como estaba. Sin la cola de cambios de la interfaz
            antigua, aquí no se pinta un cambio que el servidor no ha aceptado.
          </p>
        </Aviso>
      )}
      {detalle.data && (
        <>
          <Tarjeta>
            <h2 className="mb-1 text-base font-semibold">
              {listas.data.find((l) => l.id === listaId)?.nombre ?? 'Lista'}
            </h2>
            <p className="cifra text-2xl font-semibold">
              {euros(detalle.data.estimacion.total_cent)}
            </p>
            <p className="mt-1 text-sm text-tinta-suave">
              Lo que cuesta ahora mismo, comprando cada cosa donde está más barata.
              {detalle.data.estimacion.sin_precio > 0 && (
                <> De {detalle.data.estimacion.sin_precio} no tengo precio: no los
                  cuento.</>
              )}
            </p>
            <p className="mt-2 text-sm">
              {detalle.data.lineas.length} líneas
              {detalle.data.lineas.some((l) => l.tachado_en) && (
                <> · {detalle.data.lineas.filter((l) => l.tachado_en).length} ya
                  cogidas</>
              )}
            </p>
            <p className="mt-1 text-xs text-tinta-suave">
              Datos del {detalle.data.fecha_datos}
            </p>
          </Tarjeta>

          <Tarjeta
            titulo="Lo que hay que coger"
            sub="Marca lo que ya llevas en el carro. Lo tachado sigue contando en el total, pero sale de la cuenta de dónde comprarla."
          >
            {detalle.data.lineas.length === 0 ? (
              <Vacio titulo="La lista está vacía">
                <p>
                  Busca un producto, abre su ficha y pulsa «Añadir a la cesta».
                </p>
              </Vacio>
            ) : (
              <>
                {/* El orden es el de la API (`ORDER BY en_carrito, anadido_en`,
                    almacen.py:272): lo ya cogido se va al final solo. Ordenar
                    aqui otra vez daria dos ordenes distintos que se pelean en
                    cada recarga. */}
                <ul className="grid gap-2">
                  {detalle.data.lineas.map((l) => (
                    <UnaLinea
                      key={l.id}
                      linea={l}
                      guardando={cambia.isPending}
                      cambiar={(lineaId, cambio) => cambia.mutate({ lineaId, cambio })}
                    />
                  ))}
                </ul>
                {/* El numero que se mira mientras se coge: al tachar algo, esto
                    es lo unico que confirma que el cambio ha llegado. */}
                <p className="mt-3 text-sm text-tinta-suave">
                  <span className="cifra font-medium">
                    {euros(detalle.data.estimacion.por_recoger_cent)}
                  </span>{' '}
                  por coger ·{' '}
                  <span className="cifra font-medium">
                    {euros(detalle.data.estimacion.en_carrito_cent)}
                  </span>{' '}
                  en el carro
                </p>
              </>
            )}
          </Tarjeta>
        </>
      )}

      {compra.isLoading && <Cargando que="dónde comprarla" />}
      {compra.data && compra.data.una_tienda.length === 0 && (
        <Vacio titulo="No puedo decir dónde">
          <p>
            De esta lista no tengo ningún producto que se pueda comparar. Puede que
            sean cosas que ninguna de las cinco cadenas venda, o que ya no estén.
          </p>
        </Vacio>
      )}
      {compra.data && compra.data.una_tienda.length > 0 && (
        <>
          <h2 className="text-base font-semibold">La lista entera en una tienda</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {compra.data.una_tienda.slice(0, 6).map((t) => (
              <UnaTienda key={t.cadena} opcion={t} mejor={mejorTotal ?? t.total_cent} />
            ))}
          </div>

          {compra.data.repartido && (
            <Tarjeta>
              <header className="mb-1 flex flex-wrap items-center gap-2">
                <h3 className="text-base font-semibold">
                  Repartido entre {compra.data.repartido.cadenas.length} tiendas
                </h3>
                {compra.data.repartido.merece_la_pena === false && (
                  <Etiqueta tono="aviso">no compensa</Etiqueta>
                )}
              </header>
              <p className="cifra text-2xl font-semibold">
                {euros(compra.data.repartido.total_cent)}
              </p>
              <p className="mt-1 text-sm text-tinta-suave">
                {compra.data.repartido.cadenas.join(' y ')}
                {compra.data.repartido.ahorro_cent
                  ? ` · ahorras ${euros(compra.data.repartido.ahorro_cent)}`
                  : ''}
              </p>
              {compra.data.repartido.merece_la_pena === false && (
                <p className="mt-2 text-sm text-tinta-suave">
                  Una segunda parada por menos de 1,50 € no es un ahorro: es una
                  molestia con un número delante.
                </p>
              )}
              {compra.data.repartido.faltan.length > 0 && (
                <p className="mt-2 text-sm text-tinta-suave">
                  Sin encontrar: {compra.data.repartido.faltan.join(' · ')}
                </p>
              )}
            </Tarjeta>
          )}
        </>
      )}
    </div>
  )
}
