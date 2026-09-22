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
 *
 *  Y **reparte la lista**: quien la creo manda un enlace o mete a alguien por su
 *  usuario, y todo el mundo ve quien esta dentro. Sin esto una lista compartida
 *  es un sitio donde aparecen cosas que no has puesto tu.
 */
import { useRef, useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'

import {
  cambiarLinea, compartirCon, crearInvitacion, entrar, misListas, registrarse,
  revocarInvitaciones, salir, verLista, donde, yo,
} from '../api/cesta'
import type { CambioLinea, Invitacion, Persona } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { euros, hace } from '../api/formato'
import {
  Aviso, Boton, CampoTexto, Cargando, Casilla, Etiqueta, Selector, Tarjeta,
  Vacio, cx,
} from '../componentes/ui'
import type { Linea } from '../tipos'

/* ------------------------------------------------------ entrar, o crear ---
 *
 *  Entrar y crear la cuenta son la misma tarjeta con dos formularios, como en
 *  la interfaz vieja (`modoEntrar`, app.js:114). El motivo esta escrito en
 *  `api/registro.py`: quien llega con un enlace de lista casi nunca tiene
 *  cuenta, asi que el camino de crearla no puede estar escondido detras de una
 *  palabra pequena en una esquina. Aqui esta a un toque, debajo del otro.
 *
 *  Los campos de los dos formularios llevan `autocomplete` de verdad
 *  (`username`, `current-password`, `new-password`) para que el gestor de
 *  claves del movil sepa cuando guarda una nueva y cuando rellena la de
 *  siempre. Y ninguno lleva tamano de letra menor de 16 px: por debajo de eso
 *  Safari hace zoom al enfocar y deja la pantalla descolocada (estilos.css:35).
 */

/** El camino de quien ya tiene cuenta. */
function FormularioEntrar({ alEntrar }: { alEntrar: () => void }) {
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const entrar_ = useMutation({
    mutationFn: () => entrar(usuario.trim(), clave),
    onSuccess: alEntrar,
  })

  return (
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
          // El usuario se guarda en minusculas y sin tildes: la mayuscula
          // automatica del movil y el corrector solo escriben lo que la API va
          // a rechazar.
          autoCapitalize="none"
          spellCheck={false}
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
        <Aviso tono="mal">
          <p>{textoDeError(entrar_.error)}</p>
        </Aviso>
      )}
    </form>
  )
}

/** El camino de quien llega nuevo.
 *
 *  Tres cosas que se ven y estan decididas:
 *
 *  - **El nombre va antes que el usuario.** Es lo que se enseña en una lista
 *    compartida y la pregunta facil; el usuario es el que tiene reglas y puede
 *    estar cogido, asi que se pregunta despues. Mismo orden que la interfaz
 *    vieja (`index.html:32-41`) y por el mismo motivo.
 *  - **No hay paso intermedio.** La API entra sola al crear la cuenta: deja la
 *    cookie puesta en la misma respuesta (`main.py:112`), asi que esta pantalla
 *    NO dice "cuenta creada, ahora entra". Seria pedir dos veces lo mismo y una
 *    pantalla de mas. Si el alta sale bien se llama a `alEntrar`, exactamente
 *    igual que si se hubiera entrado.
 *  - **Las reglas viven en la API.** `minLength` es solo la pista del navegador
 *    para no escribir tres caracteres y enterarse despues; la verdad la dice
 *    `api/registro.py` y su 422 se enseña tal cual. Copiar aqui el minimo de la
 *    clave seria una segunda copia que se queda vieja el dia que cambie.
 */
function FormularioAlta({ alEntrar }: { alEntrar: () => void }) {
  const [nombre, setNombre] = useState('')
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const alta = useMutation({
    mutationFn: () => registrarse(usuario.trim(), nombre.trim(), clave),
    onSuccess: alEntrar,
  })

  return (
    <form
      className="grid gap-3 sm:max-w-sm"
      onSubmit={(e) => {
        e.preventDefault()
        if (nombre.trim() && usuario.trim() && clave) alta.mutate()
      }}
    >
      <label className="grid gap-1">
        <span className="text-sm font-medium">Tu nombre</span>
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          autoComplete="name"
          placeholder="Como quieres que te vean"
          className="rounded-md border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Usuario</span>
        <input
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="sin tildes ni espacios"
          className="rounded-md border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Contraseña</span>
        <input
          type="password"
          value={clave}
          onChange={(e) => setClave(e.target.value)}
          autoComplete="new-password"
          minLength={8}
          placeholder="ocho caracteres o más"
          className="rounded-md border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <Boton type="submit" disabled={alta.isPending}>
        {alta.isPending ? 'Creando…' : 'Crear cuenta'}
      </Boton>
      {/* El 403 (registro cerrado), el 409 (usuario cogido), el 422 (una regla
          que no se cumple) y el 429 traen su frase escrita por la API. Aqui no
          se traducen ni se resumen: se enseña lo que ha contestado. */}
      {alta.isError && (
        <Aviso tono="mal">
          <p>{textoDeError(alta.error)}</p>
        </Aviso>
      )}
    </form>
  )
}

/** La puerta, con los dos formularios y cual se esta viendo.
 *
 *  Se exporta porque la pantalla del enlace de invitacion (`/unirme/<codigo>`)
 *  enseña **esta misma**, y no una copia: quien llega por un enlace casi nunca
 *  tiene cuenta, y dos juegos de formularios serian dos sitios donde arreglar lo
 *  mismo el dia que cambie el alta. Aqui no se sabe de invitaciones: entra quien
 *  sea, y la pantalla que la usa decide que hacer despues.
 */
export function Introducir({ alEntrar }: { alEntrar: () => void }) {
  const [creando, setCreando] = useState(false)

  return (
    <Tarjeta>
      <h2 className="mb-1 text-lg font-semibold">
        {creando ? 'Crea tu cuenta' : 'Entra para ver tu lista'}
      </h2>
      <p className="mb-4 text-sm text-tinta-suave">
        {creando
          ? 'La cuenta es lo que hace que la lista tenga dueño: sin ella no se guarda ni se puede compartir. Se queda en casa, en esta Cesta, y al crearla ya entras.'
          : 'La lista de la compra es tuya y de quien la compartas. Por eso hay que entrar: una lista sin dueño no se puede compartir ni recuperar.'}
      </p>
      {creando
        ? <FormularioAlta alEntrar={alEntrar} />
        : <FormularioEntrar alEntrar={alEntrar} />}
      <div className="mt-2 flex flex-wrap items-center gap-1 text-sm text-tinta-suave">
        <span>{creando ? '¿Ya tienes cuenta?' : '¿No tienes cuenta?'}</span>
        <Boton variante="sutil" compacto className="px-2" onClick={() => setCreando(!creando)}>
          {creando ? 'Entra' : 'Créala'}
        </Boton>
      </div>
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

/* ------------------------------------------------ compartir la lista ------ *
 *
 *  Lo unico que hacia falta para que una lista deje de ser de una sola persona:
 *  mandar un enlace, meter a alguien por su usuario, ver quien esta dentro y
 *  anular lo que ya no vale.
 *
 *  Dos cosas de la interfaz vieja que se mantienen a proposito:
 *
 *  - **Quien esta dentro lo ve todo el mundo**, tambien quien no creo la lista
 *    (`app.js:1365`). Saber con quien compartes la compra no es una herramienta
 *    de administracion; lo que es solo de quien la creo es invitar y anular.
 *  - **El papel se dice con palabras.** `mira` a secas se lee como una orden, y
 *    `dueno` dice que eres, no lo que hiciste.
 */

/** `dueno` | `escribe` | `mira`, dichos en castellano. */
function nombreDelPapel(papel: string): string {
  if (papel === 'dueno') return 'creó la lista'
  if (papel === 'mira') return 'solo mira'
  return 'puede escribir'
}

function QuienEstaDentro({ personas }: { personas: Persona[] }) {
  return (
    <ul className="grid gap-1">
      {personas.map((q) => (
        <li key={q.usuario} className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-medium">{q.nombre || q.usuario}</span>
          {q.nombre && <span className="text-tinta-suave">@{q.usuario}</span>}
          <Etiqueta tono={q.papel === 'dueno' ? 'dato' : 'info'}>
            {nombreDelPapel(q.papel)}
          </Etiqueta>
        </li>
      ))}
    </ul>
  )
}

/** Tres usos y siete dias: lo que pedia la interfaz vieja (`app.js:1376`) y lo
 *  que dice la frase que se enseña junto al enlace. Los dos numeros viven aqui
 *  para que la frase no pueda decir una cosa y la peticion otra. */
const USOS_DEL_ENLACE = 3
const DIAS_DEL_ENLACE = 7

/** Compartir: el enlace, quien esta dentro, quien entra por su usuario y anular.
 *
 *  Solo se pinta para quien creo la lista. La API contesta 403 a cualquier otro
 *  (`main.py:489`) y un boton que no puede funcionar es una promesa que no se
 *  puede cumplir: mejor decir quien puede, que es lo que hace la tarjeta de
 *  abajo.
 *
 *  Tres decisiones que se ven en la pantalla:
 *
 *  - **El enlace no se crea solo al abrir.** La interfaz vieja lo pedia nada mas
 *    abrir la hoja (`app.js:1375`). Aqui hay un boton, porque la API admite tres
 *    enlaces vivos a la vez y contesta 409 al cuarto: abrir la cesta tres veces
 *    dejaria la lista sin poder invitar a nadie, y sin haber querido invitar.
 *  - **El portapapeles se comprueba antes de usarlo.** `navigator.clipboard`
 *    solo existe en contexto seguro (https o `localhost`) y esto se sirve por
 *    http en el 8080, tambien por la IP de Tailscale: lo normal es que no este.
 *    Sin la comprobacion, un `try` no bastaria: el boton diria "Copiado" sin
 *    haber copiado nada y el enlace se perderia sin que nadie se entere. Cuando
 *    no hay portapapeles se hace lo de la interfaz vieja (`app.js:1550`): dejar
 *    el enlace seleccionado y decir que se copie a mano.
 *  - **Un solo papel para las dos vias.** El enlace y el usuario comparten el
 *    selector de arriba: dos selectores acabarian diciendo cosas distintas sin
 *    que nadie lo hubiera pretendido.
 */
function Compartir({ listaId, personas }: { listaId: string; personas: Persona[] }) {
  const cliente = useQueryClient()
  const [papel, setPapel] = useState('escribe')
  const [enlace, setEnlace] = useState<Invitacion | null>(null)
  const [copiado, setCopiado] = useState<string | null>(null)
  const [sinPortapapeles, setSinPortapapeles] = useState(false)
  const [revocadas, setRevocadas] = useState<number | null>(null)
  const [usuario, setUsuario] = useState('')
  const campo = useRef<HTMLInputElement>(null)

  const invita = useMutation({
    mutationFn: () => crearInvitacion(listaId, papel, USOS_DEL_ENLACE, DIAS_DEL_ENLACE),
    onSuccess: (nueva) => {
      setEnlace(nueva)
      setCopiado(null)
      setSinPortapapeles(false)
    },
  })

  const revoca = useMutation({
    mutationFn: () => revocarInvitaciones(listaId),
    onSuccess: (cuantas) => {
      // El enlace que estaba en pantalla acaba de morir: dejarlo ahi seria
      // mandarle a alguien uno que ya no vale.
      setRevocadas(cuantas)
      setEnlace(null)
      setCopiado(null)
    },
  })

  const comparte = useMutation({
    mutationFn: () => compartirCon(listaId, usuario, papel),
    onSuccess: () => {
      setUsuario('')
      // La lista de dentro cambia con esto, y esa la lleva el servidor.
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
    },
  })

  const url = enlace ? `${window.location.origin}${enlace.ruta}` : ''

  async function copia() {
    // Se selecciona siempre, tambien cuando el portapapeles funciona: es lo que
    // deja el respaldo listo y lo que confirma de un vistazo que el boton ha
    // hecho algo.
    campo.current?.select()
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url)
        setCopiado('Copiado')
        setSinPortapapeles(false)
        return
      } catch {
        // Existe y aun asi lo ha negado (permiso denegado, ventana sin foco).
        // Se cae al respaldo, que es lo mismo que si no estuviera.
      }
    }
    setCopiado('Cópialo')
    setSinPortapapeles(true)
  }

  return (
    <Tarjeta
      titulo="Compartir"
      sub="La lista es de quien la creó y de quien entre por aquí. Quien entre puede escribir en ella o solo mirarla, y eso se elige aquí abajo."
    >
      <Selector
        etiqueta="Quien entre podrá"
        value={papel}
        onChange={(e) => setPapel(e.target.value)}
        className="max-w-xs"
      >
        <option value="escribe">Escribir en la lista</option>
        <option value="mira">Solo mirarla</option>
      </Selector>

      <h3 className="mt-4 text-sm font-semibold">Mandar un enlace</h3>
      <p className="mt-1 text-sm text-tinta-suave">
        Pedirle a alguien su nombre de usuario es pedirle que se equivoque. El
        enlace se lo lleva puesto.
      </p>
      <div className="mt-2">
        <Boton
          variante="principal"
          disabled={invita.isPending}
          onClick={() => invita.mutate()}
        >
          {invita.isPending ? 'Creando…' : enlace ? 'Crear otro enlace' : 'Crear un enlace'}
        </Boton>
      </div>
      {/* El 403 (no eres quien la creo) y el 409 (ya hay tres enlaces vivos)
          traen su frase escrita por la API: se enseña tal cual, sin resumirla. */}
      {invita.isError && (
        <div className="mt-2">
          <Aviso tono="mal" titulo="No he podido crear el enlace">
            <p>{textoDeError(invita.error)}</p>
          </Aviso>
        </div>
      )}

      {enlace && (
        <>
          <p className="mt-3 text-sm text-tinta-suave">
            Mándale este enlace. Caduca {hace(enlace.expira_en)} y vale para las{' '}
            {USOS_DEL_ENLACE} primeras personas que lo abran.
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <input
              ref={campo}
              readOnly
              value={url}
              aria-label="Enlace de invitación"
              // Al enfocarlo se selecciona entero: el dedo en el movil no acierta
              // a seleccionar 60 caracteres de codigo.
              onFocus={(e) => e.target.select()}
              className="min-h-[44px] min-w-[12rem] flex-1 rounded-lg border border-borde bg-fondo px-3 py-2 text-sm"
            />
            <Boton variante="principal" onClick={copia}>
              {copiado ?? 'Copiar'}
            </Boton>
          </div>
          {sinPortapapeles && (
            <p className="mt-2 text-sm text-aviso">
              Este navegador no deja copiar solo (el portapapeles necesita https,
              y esto va por http). El enlace ya está seleccionado: cópialo a mano.
            </p>
          )}
        </>
      )}

      <h3 className="mt-4 text-sm font-semibold">Compartir con quien ya tiene cuenta</h3>
      <p className="mt-1 text-sm text-tinta-suave">
        Si ya usa esta Cesta, con su usuario entra sin enlace. Un nombre de
        usuario se escribe mal con una facilidad pasmosa, así que si no existe
        nadie con ese, la API lo dice y aquí se enseña.
      </p>
      <form
        className="mt-2 flex flex-wrap items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (usuario.trim()) comparte.mutate()
        }}
      >
        <CampoTexto
          etiqueta="Su usuario"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="sin la arroba"
          className="min-w-[12rem] flex-1"
        />
        <Boton type="submit" disabled={!usuario.trim() || comparte.isPending}>
          {comparte.isPending ? 'Compartiendo…' : 'Compartir'}
        </Boton>
      </form>
      {comparte.data && (
        <p className="mt-2 text-sm">
          <Etiqueta tono="bien">
            Ya está dentro {comparte.data.nombre || `@${comparte.data.usuario}`}
          </Etiqueta>
        </p>
      )}
      {comparte.isError && (
        <div className="mt-2">
          <Aviso tono="mal" titulo="No he podido compartirla">
            <p>{textoDeError(comparte.error)}</p>
          </Aviso>
        </div>
      )}

      <h3 className="mt-4 text-sm font-semibold">Quién está dentro</h3>
      <div className="mt-1">
        <QuienEstaDentro personas={personas} />
      </div>

      <div className="mt-4">
        <Boton
          // No es rojo: anular enlaces no borra nada de la lista ni echa a
          // nadie, solo mata los que aun no se han usado. El rojo se guarda para
          // quitar una linea, que si borra.
          disabled={revoca.isPending}
          onClick={() => revoca.mutate()}
        >
          Anular los enlaces que haya dado
        </Boton>
      </div>
      {revocadas !== null && (
        <p className="mt-2 text-sm text-tinta-suave">
          {revocadas ? `Anulados ${revocadas}.` : 'No había ninguno.'} A quien ya
          entró no le afecta: sigue en la lista.
        </p>
      )}
      {revoca.isError && (
        <p className="mt-2 text-sm text-aviso">{textoDeError(revoca.error)}</p>
      )}
    </Tarjeta>
  )
}

/* ------------------------------------------- llegar desde una invitacion --- */

/** Lo que deja `Unirse` al llegar a la cesta. */
interface VenidaDeInvitacion {
  listaId: string
  aviso: string
}

/** Lo que `Unirse` puso en el `state` de la ruta, si es que viene de ahi.
 *
 *  Se comprueba el tipo en vez de fiarse: `state` es `any` en react-router y
 *  cualquiera puede abrir `/cesta` desde cualquier sitio. Un `listaId` que no
 *  sea texto se ignora y la cesta abre su lista de siempre. */
function venidaDeInvitacion(estado: unknown): VenidaDeInvitacion | null {
  if (typeof estado !== 'object' || estado === null) return null
  const { listaId, aviso } = estado as { listaId?: unknown; aviso?: unknown }
  if (typeof listaId !== 'string') return null
  return { listaId, aviso: typeof aviso === 'string' ? aviso : '' }
}

export function Cesta() {
  const cliente = useQueryClient()
  const ubicacion = useLocation()
  // Al aceptar una invitacion se llega aqui con esa lista en el `state` de la
  // ruta. Hace falta porque la lista que se acaba de aceptar casi nunca es la
  // primera del desplegable: las de casa van delante (`almacen.py:219`), y
  // entrar por un enlace para acabar viendo otra lista parece que el enlace no
  // ha hecho nada.
  const venida = venidaDeInvitacion(ubicacion.state)
  const [elegida, setElegida] = useState<string | null>(venida?.listaId ?? null)

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

      {/* De donde viene esta pantalla. Se dice una vez, al llegar del enlace:
          aterrizar en una lista que no has abierto tu, sin explicacion, parece
          un error de la aplicacion y no una invitacion aceptada. */}
      {venida?.aviso && (
        <Aviso tono="bien">
          <p>{venida.aviso}</p>
        </Aviso>
      )}

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
            {/* Con una invitacion de "solo mirar" los controles se apagan: la
                API contesta 403 a cualquier cambio (`main.py:369`), y dejar los
                botones puestos para que fallen uno a uno es peor que decir de
                entrada por que no se pueden pulsar. */}
            {detalle.data.papel === 'mira' && (
              <div className="mb-3">
                <Aviso tono="aviso">
                  <p>
                    Esta lista te la compartieron para mirar, así que no puedes
                    cambiarla: los botones están apagados por eso. Quien la creó
                    puede darte el papel de escribir cuando quiera.
                  </p>
                </Aviso>
              </div>
            )}
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
                      guardando={cambia.isPending || detalle.data.papel === 'mira'}
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

      {/* Compartir va antes de los precios a proposito: la comparacion entre
          cadenas son seis tarjetas largas, y lo que se hace una vez (mandar el
          enlace) no puede quedar debajo de lo que se mira cien veces. */}
      {detalle.data && detalle.data.papel === 'dueno' && (
        <Compartir listaId={listaId as string} personas={detalle.data.personas} />
      )}
      {detalle.data && detalle.data.papel !== 'dueno' && (
        <Tarjeta
          titulo="Quién está dentro"
          sub="Esta lista la creó otra persona, así que solo quien la creó puede invitar y anular enlaces."
        >
          <QuienEstaDentro personas={detalle.data.personas} />
        </Tarjeta>
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
