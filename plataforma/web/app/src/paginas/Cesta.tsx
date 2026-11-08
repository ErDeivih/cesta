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
import { useEffect, useRef, useState } from 'react'
import { listaDelDiario } from '../logica/listaDelDiario'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'

import {
  anadirLinea, borrarLista, cambiarLinea, cerrarCompra, compartirCon, crearInvitacion,
  crearLista, entrar, misListas, registrarse, renombrarLista, reparto as pedirReparto,
  revocarInvitaciones, salir, sincronizar, verLista, donde, yo,
} from '../api/cesta'
import type {
  CambioDeCola, CambioLinea, CierreDeCompra, Invitacion, Novedad, Persona,
} from '../api/cesta'
import { esSinRed, textoDeError } from '../api/cliente'
import { cotizacionDelConflicto } from '../logica/conflicto'
// **`fecha`, que es la que escribe las fechas en castellano.** *Sin ella esta pantalla
// ponia el ISO crudo -- «Datos del 2026-10-16» -- mientras el diario ponia «17/10/2026».
// *Medido en la revision visual del 17/10/2026.*
import { euros, fecha as fechaTexto, hace, nombreCadena } from '../api/formato'
import {
  apuntaCambio, leerCola, vaciaCola,
} from '../estado/cola'
import type { CambioPendiente } from '../estado/cola'
import { Mosaico } from '../componentes/Mosaico'
import { RepartoEnTiendas } from '../componentes/RepartoEnTiendas'
import {
  Aviso, Boton, CampoTexto, Cargando, Esqueleto, Etiqueta, Fallo, Selector,
  Tarjeta, Vacio, cx,
} from '../componentes/ui'
import { PegarEnLaLista } from '../componentes/PegarEnLaLista'
import { ExportarLista } from '../componentes/ExportarLista'
import type { Linea, Reparto, RepartoTiendas } from '../tipos'

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
        <span className="text-cuerpo font-medium">Usuario</span>
        <input
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="username"
          // El usuario se guarda en minusculas y sin tildes: la mayuscula
          // automatica del movil y el corrector solo escriben lo que la API va
          // a rechazar.
          autoCapitalize="none"
          spellCheck={false}
          className="rounded-campo border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-cuerpo font-medium">Clave</span>
        <input
          type="password"
          value={clave}
          onChange={(e) => setClave(e.target.value)}
          autoComplete="current-password"
          className="rounded-campo border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <Boton type="submit" disabled={entrar_.isPending}>
        {entrar_.isPending ? 'Entrando…' : 'Entrar'}
      </Boton>
      {entrar_.isError && (
        <Aviso tono="mal">
          <Etiqueta tono="mal">{textoDeError(entrar_.error)}</Etiqueta>
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
        <span className="text-cuerpo font-medium">Tu nombre</span>
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          autoComplete="name"
          placeholder="Como quieres que te vean"
          className="rounded-campo border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-cuerpo font-medium">Usuario</span>
        <input
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="sin tildes ni espacios"
          className="rounded-campo border border-borde bg-fondo px-3 py-2"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-cuerpo font-medium">Contraseña</span>
        <input
          type="password"
          value={clave}
          onChange={(e) => setClave(e.target.value)}
          autoComplete="new-password"
          minLength={8}
          placeholder="ocho caracteres o más"
          className="rounded-campo border border-borde bg-fondo px-3 py-2"
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
          <Etiqueta tono="mal">{textoDeError(alta.error)}</Etiqueta>
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
    <Tarjeta className="grow">
      <h2 className="mb-1 text-lg font-semibold">
        {creando ? 'Crea tu cuenta' : 'Entra para ver tu lista'}
      </h2>
      <p className="mb-4 text-cuerpo text-tinta-suave">
        {creando
          ? 'La cuenta hace que la lista tenga dueño: sin ella no se guarda ni se comparte.'
          : 'La lista es tuya y de quien la compartas; por eso hay que entrar.'}
      </p>
      {creando
        ? <FormularioAlta alEntrar={alEntrar} />
        : <FormularioEntrar alEntrar={alEntrar} />}
      <div className="mt-2 flex flex-wrap items-center gap-1 text-cuerpo text-tinta-suave">
        <span>{creando ? '¿Ya tienes cuenta?' : '¿No tienes cuenta?'}</span>
        <Boton variante="sutil" compacto className="px-2" onClick={() => setCreando(!creando)}>
          {creando ? 'Entra' : 'Créala'}
        </Boton>
      </div>
    </Tarjeta>
  )
}

/** El reparto entre varias tiendas, con **cuantas cosas se compran en cada una**.
 *
 *  El desglose ("7 en alcampo, 3 en dia") es lo que hace planificable el
 *  reparto: con el total y el ahorro solos no se sabe si la segunda parada es
 *  por una cosa o por veinte, y esa es justo la cuenta que se hace de pie en la
 *  tienda con el carro al lado. La interfaz vieja ya lo decia (`app.js:718`) y
 *  se perdio al reescribir la pantalla.
 *
 *  Las cuentas que se pintan son LINEAS de la lista, no unidades: "3 en dia"
 *  son tres cosas que coger. Es lo que cuenta `reparto`
 *  (`plataforma/api/cesta.py:195`: una entrada por linea resuelta), y decir
 *  "unidades" seria prometer una precision que el dato no tiene.
 *
 *  Una cadena que venga sin su cuenta **no se pinta**. Un "0 en dia" inventado
 *  se leeria como "no compras nada alli", que es exactamente lo contrario de lo
 *  que significa estar en la lista de cadenas del reparto.
 */
function Repartido({ reparto }: { reparto: Reparto }) {
  const cuantas = reparto.reparto
  const desglose: { cadena: string; lineas: number }[] = []
  if (cuantas) {
    for (const cadena of reparto.cadenas) {
      const n = cuantas[cadena]
      if (typeof n === 'number') desglose.push({ cadena, lineas: n })
    }
  }

  return (
    <Tarjeta>
      <header className="mb-1 flex flex-wrap items-center gap-2">
        <h3 className="text-entrada font-semibold">
          Repartido entre {reparto.cadenas.length} tiendas
        </h3>
        {reparto.merece_la_pena === false && (
          <Etiqueta tono="aviso">no compensa</Etiqueta>
        )}
      </header>
      <p className="cifra text-2xl font-semibold">{euros(reparto.total_cent)}</p>
      <p className="mt-1 text-cuerpo text-tinta-suave">
        {reparto.cadenas.map(nombreCadena).join(' y ')}
        {reparto.ahorro_cent ? ` · ahorras ${euros(reparto.ahorro_cent)}` : ''}
      </p>
      {/* El desglose va en su propia linea y con la tinta normal, no en gris
          como las cadenas: es el dato que se mira al decidir el viaje, no un
          detalle al lado del total. */}
      {desglose.length > 0 && (
        <p className="mt-1 flex flex-wrap gap-x-3 text-cuerpo">
          {desglose.map((d) => (
            <span key={d.cadena}>
              <span className="cifra font-medium">{d.lineas}</span> en{' '}
              {nombreCadena(d.cadena)}
            </span>
          ))}
        </p>
      )}
      {reparto.merece_la_pena === false && (
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Una segunda parada por menos de 1,50 € no es un ahorro: es una
          molestia con un número delante.
        </p>
      )}
      {reparto.faltan.length > 0 && (
        <p className="mt-2 text-cuerpo text-tinta-suave">
          Sin encontrar: {reparto.faltan.join(' · ')}
        </p>
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
/** Las lineas de una seccion, agrupadas por pasillo y en el orden de la tienda.
 *
 *  El motivo no es de diseno, es de tienda: la lista se usa **de pie, en
 *  movimiento y con una mano**, y lo que hay que saber mientras se empuja el carro
 *  es en que pasillo se esta. Con nueve lineas de seis pasillos, leer el nombre de
 *  cada una para saber que queda aqui es trabajo que se hace andando.
 *
 *  **El pasillo viene de la API** (`catalogo.pasillo_de_grupos`, en
 *  `GET /api/listas/{id}`), con su posicion en el recorrido de la tienda. Esto solo
 *  ordena y corta: aqui no se decide que pasillo tiene un producto, que es un dato
 *  del catalogo y no de la pantalla.
 *
 *  Tres decisiones que estan en estas seis lineas:
 *
 *  1. **Las lineas sin pasillo van al final y sin encabezado**, no al principio ni
 *     repartidas por donde "parezca". Cuando gold no trae la columna `seccion`, o el
 *     grupo no esta en el catalogo, no sabemos de que pasillo es: eso no se
 *     rellena, se deja al final.
 *  2. **Dentro de un pasillo se respeta el orden que manda la API** (`en_carrito,
 *     anadido_en`): `sort` es estable, asi que las lineas sin pasillo y las del
 *     mismo pasillo mantienen el orden en que llegaron. Ordenarlas aqui otra vez
 *     daria dos ordenes peleandose en cada recarga.
 *  3. **Los pasillos se cortan por nombre, no por `seccion`**, para pintar lo que se
 *     lee. Dos tandas seguidas con el mismo nombre no pueden pasar: el nombre sale
 *     de la misma seccion (`NOMBRES_SECCIONES`), asi que van juntas.
 */
function porPasillo(lineas: Linea[]): [string, Linea[]][] {
  const sinPasillo = Number.MAX_SAFE_INTEGER
  const ordenadas = [...lineas].sort(
    (a, b) => (a.pasillo_orden ?? sinPasillo) - (b.pasillo_orden ?? sinPasillo),
  )
  const tandas: [string, Linea[]][] = []
  for (const l of ordenadas) {
    const nombre = l.pasillo ?? ''
    const ultima = tandas[tandas.length - 1]
    if (ultima && ultima[0] === nombre) ultima[1].push(l)
    else tandas.push([nombre, [l]])
  }
  return tandas
}

/** El precio de una linea, cuando la API lo sabe. */
interface PrecioDeLaLinea {
  coste_cent: number
  /** La cadena de la que es ese precio. `null` si el reparto no la dice. */
  cadena: string | null
}

/** Lo que cuesta cada linea, por su id, sacado del reparto (`GET /listas/{id}/reparto`).
 *
 *  **La lista no trae precio por linea, y esto no lo inventa.** `GET /listas/{id}` manda la
 *  estimacion entera (`estimacion`) y las lineas, pero no el coste de cada una; el unico sitio
 *  de la API de donde sale **el coste de UNA linea** es el reparto, que ya se pide para la
 *  tarjeta de «Donde compro cada cosa» -- misma `queryKey`, asi que esta pantalla **no anade
 *  una peticion**, solo lee lo que ya viene.
 *
 *  Y **cubre lo que cubre**: el reparto deja fuera las lineas que ya estan en el carro y las que
 *  apuntan a otro producto. Esas filas se quedan **sin cifra**, que es la verdad; el total de
 *  arriba sigue siendo el de toda la lista.
 */
function preciosPorLinea(reparto: RepartoTiendas | undefined): Map<string, PrecioDeLaLinea> {
  const precios = new Map<string, PrecioDeLaLinea>()
  if (!reparto) return precios
  for (const sublista of reparto.sublistas ?? []) {
    for (const deLaTienda of sublista.lineas ?? []) {
      if (!deLaTienda.linea_id) continue
      precios.set(deLaTienda.linea_id, {
        coste_cent: deLaTienda.coste_cent,
        cadena: sublista.cadena,
      })
    }
  }
  for (const sinDecidir of reparto.sin_asignar ?? []) {
    if (!sinDecidir.linea_id || sinDecidir.coste_cent == null) continue
    precios.set(sinDecidir.linea_id, {
      coste_cent: sinDecidir.coste_cent,
      cadena: sinDecidir.mas_barata,
    })
  }
  return precios
}

/** La cadena del total, **solo cuando se sabe**: cuando toda la lista esta decidida en una.
 *
 *  *No se corona la cadena «mas barata» de cada linea: eso no es una cadena, es un reparto, y
 *  decir «en Mercadona» cuando se compra en tres sitios es el tipo de mentira que hace
 *  desconfiar de la cifra. Cuando no hay una sola tienda, la tarjeta no lleva cadena.*
 */
function cadenaDelTotal(reparto: RepartoTiendas | undefined): string | null {
  if (!reparto) return null
  if ((reparto.sublistas ?? []).length !== 1) return null
  if ((reparto.sin_asignar ?? []).length > 0) return null
  if ((reparto.sin_encontrar ?? []).length > 0) return null
  return reparto.sublistas[0]?.cadena ?? null
}

/** Una linea, con la casilla de verdad delante y su precio al lado, como el artboard.
 *
 *  Lo que se ve, y por que:
 *
 *  - **La casilla es una casilla** (`input type=checkbox`, 22 px) dentro de un `label` que lleva
 *    el nombre: el gesto del pasillo es tocar la linea, no apuntar a un cuadrado pequeño, y
 *    quien no ve la pantalla oye el nombre del producto al llegar al control.
 *  - **El precio de la linea solo se pinta si la API lo sabe** (`preciosPorLinea`). Un precio
 *    repartido a ojo del total seria una cifra que nadie puede comprobar.
 *  - **La cadena va con el precio**, porque un precio sin decir de que tienda es no se puede
 *    comprobar. El **€/kg no se pinta**: la API no lo manda por linea, y esta pantalla no
 *    inventa una unidad que no tiene.
 *  - **Las tres acciones siguen donde estaban** -- cantidad, quitar y nota --, con los mismos
 *    `aria-label`: el diseno cambia, la funcion no.
 */
function UnaLinea({ linea, precio, guardando, cambiar }: {
  linea: Linea
  precio?: PrecioDeLaLinea
  guardando: boolean
  cambiar: (lineaId: string, cambio: CambioLinea) => void
}) {
  const tachada = linea.tachado_en !== null
  // La nota (tarea 5): el campo se abre **a peticion** porque la lista se lee de pie, y una
  // caja de texto en cada linea seria ruido. Y se guarda al pulsar «Guardar», no al escribir:
  // con una mano y en el pasillo, una peticion por letra es una cola de escrituras por una
  // nota que quiza no se termina.
  const [escribiendo, setEscribiendo] = useState(false)
  const [borrador, setBorrador] = useState(linea.nota ?? '')
  const idCasilla = `linea-${linea.id}`
  // **Una linea sin destino es legitima** desde la migracion 014 (paquete G02): se apunta lo
  // que no esta en el catalogo en vez de obligar a buscarlo. Pero **no es un producto**, y la
  // pantalla no puede hacer que lo parezca: no tiene precio y no entra en ninguna comparacion.
  const sinCatalogo = !linea.grupo_id && !linea.producto_id

  return (
    <li className="border-t border-borde first:border-t-0">
      <div className="flex items-start gap-3 px-4 pt-3">
        <label
          htmlFor={idCasilla}
          className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-start gap-3"
        >
          <input
            id={idCasilla}
            type="checkbox"
            checked={tachada}
            disabled={guardando}
            // El estado lo pone el servidor y `tachado` basta: la API mete en el carro y
            // tacha a la vez (`almacen.py:324`), asi que no son dos cosas que puedan
            // separarse.
            onChange={(e) => cambiar(linea.id, { tachado: e.target.checked })}
            className="mt-0.5 h-[22px] w-[22px] shrink-0 accent-verde"
          />
          <span className="min-w-0 flex-1">
            <span
              className={cx(
                'block break-words text-cuerpo-fuerte',
                tachada ? 'text-tinta-suave line-through' : 'text-tinta',
              )}
            >
              {linea.nombre_visto}
            </span>
            <span className="mt-0.5 flex flex-wrap items-center gap-x-2 text-etiqueta text-tinta-tenue">
              {linea.cantidad > 1 && <span className="cifra">{linea.cantidad} ×</span>}
              {precio?.cadena && <span>en {nombreCadena(precio.cadena)}</span>}
              {!precio && !tachada && !linea.producto_movido && <span>sin precio</span>}
              {sinCatalogo && (
                <span className="rounded-nota border border-borde px-1.5">
                  Sin producto del catálogo
                </span>
              )}
            </span>
            {linea.nota && !escribiendo && (
              <span className="mt-0.5 block break-words text-etiqueta text-tinta-suave">
                <span className="sr-only">Nota: </span>
                {linea.nota}
              </span>
            )}
          </span>
        </label>
        {precio && (
          <span className="cifra mt-0.5 shrink-0 text-precio-fila font-semibold text-tinta">
            {euros(precio.coste_cent)}
          </span>
        )}
      </div>

      {/* **La linea que apunta a otro producto, dicha.** El `grupo_id` es un numero que el
          emparejador renumera en cada pasada, asi que esta linea puede estar apuntando a un
          pintalabios cuando dice «leche entera»: medido el 28 de septiembre de 2026, la lista
          ponia esa linea en el pasillo de higiene y belleza y le ponia el precio del pintalabios.
          La API ya no la cuenta ni la reparte (`catalogo.lineas_movidas`), y aqui se dice por que
          y se da la salida: buscarla y volver a anadirla. */}
      {linea.producto_movido && (
        <p className="mt-1 px-4 text-etiqueta text-aviso">
          Este producto ha cambiado en el catálogo.{' '}
          <Link to={`/buscar?q=${encodeURIComponent(linea.nombre_visto)}`} className="underline">
            Búscalo y vuelve a añadirlo
          </Link>
          .
        </p>
      )}

      <div className="flex flex-wrap items-center gap-1 pb-3 pl-[50px] pr-4 pt-1">
        {/* La cantidad que acepta la API es 1..99: fuera de ahi contesta 422, y un 422 por
            pulsar de mas no es una forma de enterarse. */}
        <Boton
          compacto
          disabled={guardando || linea.cantidad <= 1}
          aria-label={`Menos ${linea.nombre_visto}`}
          onClick={() => cambiar(linea.id, { cantidad: linea.cantidad - 1 })}
        >
          −
        </Boton>
        <span className="cifra w-8 text-center text-cuerpo font-semibold">{linea.cantidad}</span>
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
        <Boton compacto variante="sutil" disabled={guardando} onClick={() => setEscribiendo(true)}>
          {linea.nota ? 'Cambiar la nota' : 'Añadir una nota'}
        </Boton>
      </div>

      {escribiendo && (
        <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
          <CampoTexto
            etiqueta={`Nota para ${linea.nombre_visto}`}
            value={borrador}
            autoFocus
            onChange={(e) => setBorrador(e.target.value)}
            maxLength={200}
            autoComplete="off"
            className="min-w-[12rem] flex-1"
          />
          <Boton
            compacto
            disabled={guardando}
            onClick={() => {
              cambiar(linea.id, { nota: borrador.trim() || null })
              setEscribiendo(false)
            }}
          >
            Guardar
          </Boton>
          <Boton
            compacto
            variante="sutil"
            onClick={() => {
              setBorrador(linea.nota ?? '')
              setEscribiendo(false)
            }}
          >
            Cancelar
          </Boton>
        </div>
      )}
    </li>
  )
}

/* ------------------------------------------------------------- las listas ---
 *
 *  Varias listas de la compra, y por que hacen falta: una para la semana, otra para
 *  la casa del pueblo, otra para una comida. El dueno lo pidio el 25 de septiembre de
 *  2026. La API las tiene desde el principio (`POST /api/listas`, `GET /api/listas`);
 *  lo que faltaba era poder **crear la segunda** desde la pantalla y poder borrarlas.
 */

function NuevaLista({ alCrear }: { alCrear: (id: string) => void }) {
  const [abierto, setAbierto] = useState(false)
  const [nombre, setNombre] = useState('')
  // **La PRIMERA lista es la de casa, y hasta hoy no lo era nunca.**
  //
  // *El 18/10/2026 se encontro el porque de un boton que nadie podia pulsar: «Ver que se puede
  // anotar», en el diario, estaba `disabled` **para todo el mundo**.* *La cadena era esta:*
  //
  //   `Diario.tsx:69`  const casa = listas.data?.find((l) => l.es_de_casa) ?? null
  //   `Diario.tsx:98`  const sinLista = listaId === null
  //   `Diario.tsx:103` disabled={sinLista || ver.isPending}
  //
  // *Y `es_de_casa` **no se ponia nunca**: esta pantalla llamaba `crearLista(nombre)` y el
  // segundo parametro vale `false` por defecto (`cesta.ts:118`).* *Asi que **ninguna lista creada
  // desde la interfaz era «de casa»**, `casa` era siempre `null`, y la funcion «de la compra al
  // diario» **no se podia usar**.*
  //
  // **Se marca la primera y solo la primera**: *el diseño habla de «la lista de casa», en
  // singular, y las demas son las otras (`:552`).* *Si ya hay una, la nueva no lo es.*
  //
  // *Y se corrige una afirmacion mia: **no era cierto que ninguna lista creada desde la interfaz
  // fuera de casa** -- *ya habia un camino que la creaba* --. *Lo que este cambio hace es que la
  // primera lista de `NuevaLista` tambien lo sea, que es el hueco real que quedaba.*
  //
  // *`useQuery` va **aqui arriba**, con los otros hooks y **antes** del `if (!abierto) return` de
  // abajo: es la misma regla que se acaba de arreglar en `Producto.tsx`.*
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas })
  // **Solo se marca «de casa» si se SABE que no hay ninguna.**
  // *Con `listas.data` sin cargar, `yaHayCasa` seria `false` y se intentaria crear una segunda
  // «de casa»: la base lo prohibe (`lista_de_casa_por_dueno`) y responderia 409.* *Asi que sin dato
  // **no se marca**, y la lista se crea como las demas.* *Antes de saberlo, no se decide.*
  const hayCasa = listas.data?.some((l) => l.es_de_casa)
  const crear = useMutation({
    mutationFn: () => crearLista(nombre.trim() || 'Lista', hayCasa === false),
    onSuccess: (l) => {
      setNombre('')
      setAbierto(false)
      alCrear(l.id)
    },
  })
  if (!abierto) {
    return (
      <button
        type="button"
        onClick={() => setAbierto(true)}
        className="inline-flex min-h-[44px] min-w-[44px] items-center text-cuerpo text-tinta-suave underline"
      >
        + Lista nueva
      </button>
    )
  }
  return (
    <span className="flex flex-wrap items-center gap-2">
      <CampoTexto
        etiqueta="Nombre de la lista"
        value={nombre}
        autoFocus
        onChange={(e) => setNombre(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') crear.mutate() }}
        placeholder="La del sábado"
        className="min-h-[44px] min-w-[44px]"
      />
      <Boton variante="principal" disabled={crear.isPending} onClick={() => crear.mutate()}>
        Crear
      </Boton>
      <button type="button" onClick={() => setAbierto(false)}
              className="min-h-[44px] px-2 text-cuerpo underline">
        Cancelar
      </button>
    </span>
  )
}

/** El nombre de la lista, con lo de renombrarla y borrarla.
 *
 *  Borrar la lista entera lo pidio el dueno con estas palabras: *"poder borrar sublista
 *  o lista del tiron"*. Se **archiva** (desaparece y se puede recuperar), y por eso el
 *  aviso lo dice en vez de dar a entender que se ha destruido: borrar de verdad una
 *  lista compartida le quita la compra a otra persona de un toque.
 */
/* --------------------------------------------------- la cabecera y el total ---
 *
 *  **La composicion la manda el artboard aprobado** (`designs/cesta-app/project/Lista.dc.html`,
 *  390 x 844): cabecera con volver y opciones, el precio estimado sobre bosque, las filas con su
 *  casilla y su precio, «Añadir producto» y «Comparar mi cesta». Los valores -- colores, tipos,
 *  radios, sombras y movimiento -- son los del sistema «Cesta App», no se eligen aqui.
 *
 *  Y una decision que se ve en el codigo: **el `h1` de esta pantalla lo pone el armazon**
 *  (`Suite.tsx`, con el titulo de la seccion). El artboard lo pinta porque es una pantalla
 *  suelta; en la aplicacion, un segundo `h1` es un fallo de accesibilidad que la puerta del
 *  navegador mide (`if (h1 !== 1)`). Asi que el titulo de aqui es `h2` y lleva **el nombre de
 *  la lista**, que es lo unico que distingue esta pantalla de otra lista: repetir «La lista»
 *  debajo de «Lista» no informa de nada.
 */

/** La cabecera: volver, donde estas y el nombre de la lista, con las opciones a la derecha. */
function CabeceraDeLaLista({ nombre, deCasa, opciones, alAlternar }: {
  nombre: string
  deCasa: boolean
  opciones: boolean
  alAlternar: () => void
}) {
  return (
    <header className="flex items-center gap-2">
      <Link
        to="/"
        aria-label="Volver a la portada"
        className="inline-flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
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
        <p className="text-micro uppercase text-tinta-tenue">
          Compra{deCasa ? ' · de casa' : ''}
        </p>
        <h2 className="truncate font-serif text-titulo font-semibold text-tinta">{nombre}</h2>
      </div>
      <button
        type="button"
        aria-label="Tu cuenta"
        aria-expanded={opciones}
        aria-controls="opciones-de-la-cuenta"
        onClick={alAlternar}
        className="inline-flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-suave transition-colors duration-rapida ease-suave hover:bg-papel hover:text-tinta"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true" focusable="false">
          <circle cx="5" cy="12" r="1.6" />
          <circle cx="12" cy="12" r="1.6" />
          <circle cx="19" cy="12" r="1.6" />
        </svg>
      </button>
    </header>
  )
}

/** Lo de la cuenta: a donde ir y como salir, detras del boton de opciones.
 *
 *  *No se pinta nada que se use en el pasillo: son tres puertas que se buscan una vez. Y el
 *  armazon ya las tiene en su menu, asi que aqui van recogidas para no competir con la lista.*
 */
function OpcionesDeLaCuenta({ alSalir }: { alSalir: () => void }) {
  return (
    <div
      id="opciones-de-la-cuenta"
      className="flex flex-wrap items-center gap-x-4 rounded-tarjeta border border-borde bg-papel px-4 py-1 shadow-apoyado"
    >
      <Link
        to="/compra/favoritos"
        className="inline-flex min-h-[44px] items-center text-cuerpo text-tinta-suave underline underline-offset-2"
      >
        Favoritos
      </Link>
      <Link
        to="/ajustes"
        className="inline-flex min-h-[44px] items-center text-cuerpo text-tinta-suave underline underline-offset-2"
      >
        Ajustes
      </Link>
      <button
        type="button"
        onClick={alSalir}
        className="inline-flex min-h-[44px] items-center text-cuerpo text-tinta-suave underline underline-offset-2"
      >
        Salir
      </button>
    </div>
  )
}

/** El precio estimado de la lista, sobre bosque: lo primero que se mira.
 *
 *  Tres cosas que se ven y estan decididas:
 *
 *  - **La cifra es la de la API** (`estimacion.total_cent`): no se suma aqui nada.
 *  - **La cadena solo se dice cuando se sabe** (`cadenaDelTotal`): cuando toda la lista esta
 *    decidida en una tienda. Si se compra en tres, no hay «una» cadena que poner.
 *  - **Si no hay precio de nada, no se pinta un cero.** «0,00 €» se lee como gratis, y lo que
 *    pasa es que no hay precios: la tarjeta lo dice con palabras y cuenta cuantas lineas se
 *    quedan fuera.
 */
function PrecioEstimado({ totalCent, productos, sinPrecio, cadena, fechaDatos }: {
  totalCent: number | null
  productos: number
  sinPrecio: number
  cadena: string | null
  fechaDatos: string
}) {
  const conPrecio = Math.max(0, productos - sinPrecio)
  const cuantos = `${productos} ${productos === 1 ? 'producto' : 'productos'}`
  // *La condicion de las ofertas se dice porque cambia lo que se paga: una oferta de club o de
  // cupon no esta en esta cifra. Y cuando falta el precio de alguna linea, eso manda: es lo que
  // explica por que el total no incluye todo.*
  const detalle = sinPrecio === 0
    ? `${cuantos} · no incluye ofertas condicionadas`
    : conPrecio === 0
      ? `${cuantos} · no tengo precio de ninguno`
      : `${cuantos} · no tengo precio de ${sinPrecio}`

  return (
    <section
      aria-labelledby="precio-estimado"
      className="rounded-tarjeta bg-bosque p-4 text-sobre-bosque shadow-alzado"
    >
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="precio-estimado" className="text-micro uppercase">Precio estimado</h2>
        {cadena && <span className="text-etiqueta opacity-80">en {nombreCadena(cadena)}</span>}
      </div>
      <p className="cifra mt-2 text-precio-grande font-semibold">
        {conPrecio > 0 && totalCent != null ? euros(totalCent) : 'Todavía sin precio'}
      </p>
      <p className="mt-1 text-etiqueta opacity-80">{detalle}</p>
      <p className="mt-0.5 text-etiqueta opacity-80">Precios del {fechaTexto(fechaDatos)}</p>
    </section>
  )
}

/** El nombre de la lista: cambiarlo o quitarla, sin repetir el titulo de la cabecera.
 *
 *  Borrar la lista entera lo pidio el dueno con estas palabras: *"poder borrar sublista
 *  o lista del tiron"*. Se **archiva** (desaparece y se puede recuperar), y por eso el aviso lo
 *  dice en vez de dar a entender que se ha destruido: borrar de verdad una lista compartida le
 *  quita la compra a otra persona de un toque.
 *
 *  *Vive en la barra de las listas, no detras del boton de opciones, y no es un descuido: la
 *  puerta de funciones pulsa «Cambiar el nombre» y «Quitar la lista» sin abrir nada. Lo que se
 *  guarda detras del boton son los enlaces de la cuenta.*
 */
function AccionesDelNombre({ lista, alHecho }: {
  lista: { id: string; nombre: string }
  alHecho: (id: string | null) => void
}) {
  const [renombrando, setRenombrando] = useState(false)
  const [nombre, setNombre] = useState(lista.nombre)
  const [confirmando, setConfirmando] = useState(false)
  const renombrar = useMutation({
    mutationFn: () => renombrarLista(lista.id, nombre.trim() || lista.nombre),
    onSuccess: () => { setRenombrando(false); alHecho(lista.id) },
  })
  const borrar = useMutation({
    mutationFn: () => borrarLista(lista.id),
    onSuccess: () => alHecho(null),
  })

  if (renombrando) {
    return (
      <span className="flex flex-1 flex-wrap items-center gap-2">
        <CampoTexto
          etiqueta="Nombre"
          value={nombre}
          autoFocus
          onChange={(e) => setNombre(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') renombrar.mutate() }}
          className="min-h-[44px] min-w-[10rem] flex-1"
        />
        <Boton compacto variante="principal" disabled={renombrar.isPending}
               onClick={() => renombrar.mutate()}>
          Guardar
        </Boton>
        <Boton compacto variante="sutil" onClick={() => setRenombrando(false)}>
          Cancelar
        </Boton>
      </span>
    )
  }

  return (
    <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <button
        type="button"
        onClick={() => { setNombre(lista.nombre); setRenombrando(true) }}
        className="inline-flex min-h-[44px] items-center text-etiqueta text-tinta-suave underline underline-offset-2"
      >
        Cambiar el nombre
      </button>
      {confirmando ? (
        <>
          <button
            type="button"
            disabled={borrar.isPending}
            onClick={() => borrar.mutate()}
            className="inline-flex min-h-[44px] items-center text-etiqueta text-error underline underline-offset-2"
          >
            Sí, quitar esta lista
          </button>
          <button
            type="button"
            onClick={() => setConfirmando(false)}
            className="inline-flex min-h-[44px] items-center text-etiqueta text-tinta-suave underline underline-offset-2"
          >
            No
          </button>
          <p className="w-full text-etiqueta text-tinta-suave">
            Desaparece de tu pantalla y de la de quien la comparta. No se borra de
            verdad: se puede recuperar.
          </p>
        </>
      ) : (
        <button
          type="button"
          onClick={() => setConfirmando(true)}
          className="inline-flex min-h-[44px] items-center text-etiqueta text-tinta-suave underline underline-offset-2"
        >
          Quitar la lista
        </button>
      )}
    </span>
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

/** «He terminado la compra»: lo del carro se guarda como compra y sale de la lista.
 *
 *  Es la mitad que le faltaba al bucle de la semana: hasta hoy la lista sabia lo que
 *  **falta** y no lo que **se compro**, asi que cada semana se empezaba de cero. Al
 *  cerrarla, las lineas marcadas (las que iban en el carro) se guardan con su precio y
 *  **lo que no se cogio se queda en la lista**: quien no encuentra el pan no quiere
 *  volver a apuntarlo.
 *
 *  Tres decisiones, y las tres son de la pantalla:
 *
 *  - **Sin nada en el carro no se dibuja el boton.** Un boton que solo puede contestar
 *    «no hay nada» es un boton que hace perder el tiempo justo cuando se esta de pie en
 *    la caja.
 *  - **Pregunta antes, y dice cuanto.** Que se van a quitar N cosas de la lista no se
 *    puede descubrir despues: es una accion que no se deshace de un toque (las lineas se
 *    archivan, y volver a apuntarlas es volver a apuntarlas).
 *  - **Y dice lo que ha pasado, con las cuentas**: cuantas salieron, cuanto costo y
 *    cuantas quedan. Las que se quedaron sin precio se dicen aparte, porque van en la
 *    compra y no en el total -- contarlas como cero seria mentir en la cifra que se
 *    acaba de guardar.
 */
function CerrarCompra({ listaId, enElCarro, papel, sello }: {
  listaId: string
  enElCarro: number
  papel: string
  /** *La revision de la cotizacion que se sirvio con la lista.* **Sin ella el cierre no es
   *  confirmado**: el servidor no puede saber si cambio algo desde que se miro. */
  sello?: string | null
}) {
  const cliente = useQueryClient()
  const [confirmando, setConfirmando] = useState(false)
  const [hecho, setHecho] = useState<CierreDeCompra | null>(null)

  const cerrar = useMutation({
    mutationFn: () => cerrarCompra(listaId, sello),
    onSuccess: (r) => {
      setHecho(r)
      setConfirmando(false)
      // Lo que cambia al cerrar: la lista (ya no estan esas lineas), el reparto y el
      // mosaico de «lo de siempre» (el historial cuenta las lineas archivadas).
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['donde', listaId] })
      cliente.invalidateQueries({ queryKey: ['reparto', listaId] })
      cliente.invalidateQueries({ queryKey: ['habituales'] })
    },
  })

  // Quien solo mira no cierra nada, y quien no lleva nada en el carro tampoco tiene nada
  // que cerrar.
  if (papel === 'mira' || (enElCarro === 0 && !hecho)) return null

  if (hecho) {
    return (
      <Aviso tono="bien" titulo={`Compra guardada: ${hecho.lineas} ${hecho.lineas === 1 ? 'cosa' : 'cosas'}, ${euros(hecho.total_cent)}`}>
        {hecho.quedan > 0
          ? `Te quedan ${hecho.quedan} por coger en la lista.`
          : 'La lista se ha quedado vacía.'}
        {hecho.sin_precio > 0 && (
          <> {hecho.sin_precio} sin precio conocido, contadas aparte del total.</>
        )}
        {/* *** SI EL TOTAL CAMBIO DESDE QUE MIRASTE LA LISTA, SE DICE. ***
            *El cierre lee el precio de ese momento, y lo que se paga es lo que se paga: eso no se
            toca. Lo que no puede pasar es que la pantalla dijera una cifra y el recibo guarde otra
            **sin decirlo** -- el precio de un super cambia, y quien cierra merece saber que la
            diferencia existe y de cuanto es.*
            *La cifra sale de la API, que la calcula con el mismo `cesta.estimacion` que pinta la
            lista: no es una tercera cuenta.* */}
        {hecho.diferencia_cent !== null && hecho.diferencia_cent !== 0 && (
          <>
            {' '}
            Desde que miraste la lista, el total ha cambiado en{' '}
            <strong>
              {hecho.diferencia_cent > 0 ? 'mas' : 'menos'} de{' '}
              {euros(Math.abs(hecho.diferencia_cent))}
            </strong>
            . Lo guardado es lo que costaba al cerrar.
          </>
        )}
      </Aviso>
    )
  }

  if (!confirmando) {
    return (
      <Boton variante="normal" onClick={() => setConfirmando(true)}>
        He terminado la compra
      </Boton>
    )
  }

  return (
    <Aviso tono="aviso" titulo={`¿Terminada? Se quitarán ${enElCarro} ${enElCarro === 1 ? 'cosa' : 'cosas'} de la lista`}>
      <p className="mt-1">
        Se guardan como compra, con su precio. Lo que no hayas cogido se queda en la lista.
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        <Boton variante="principal" disabled={cerrar.isPending}
               onClick={() => cerrar.mutate()}>
          {cerrar.isPending ? 'Guardando…' : 'Sí, he terminado'}
        </Boton>
        <Boton variante="sutil" onClick={() => setConfirmando(false)}>No, déjalo</Boton>
      </div>
      {cerrar.isError && (
        <Etiqueta tono="mal">{textoDeError(cerrar.error)}</Etiqueta>
      )}
    </Aviso>
  )
}

/** `dueno` | `escribe` | `mira`, dichos en castellano. */
function nombreDelPapel(papel: string): string {
  if (papel === 'dueno') return 'creó la lista'
  if (papel === 'mira') return 'solo mira'
  return 'puede escribir'
}

/** Quién está dentro de la lista.
 *
 *  `aceptado_en` viaja en `GET /listas/{id}` desde el primer día (`almacen.quienes_en`) y **no
 *  lo pinta nadie**, y está mirado por qué: **hoy nunca es NULL**. Los tres sitios que escriben
 *  en `lista_acceso` lo ponen a `now()` -- crear la lista (`almacen.py:287`), compartir por
 *  usuario (`:329`) y aceptar un enlace (`:1015`) --, así que no existe el estado «invitada y
 *  todavía no ha entrado» que parecía pedir este campo: invitar por usuario **es** meter, y el
 *  enlace se acepta al abrirlo (y si no se abre, no hay fila).
 *
 *  Se probó a pintarlo el 30 de septiembre de 2026 y se quitó el mismo día: una etiqueta para
 *  un estado que la API no produce es código muerto que además **afirma** que hay un caso que
 *  no hay. La decisión de fondo -- que invitar sea entrar -- está en `docs/AMIGOS.md`.
 */
function QuienEstaDentro({ personas }: { personas: Persona[] }) {
  return (
    <ul className="grid gap-1">
      {personas.map((q) => (
        <li key={q.usuario} className="flex flex-wrap items-center gap-2 text-cuerpo">
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

/** Lo que ha tocado otra persona desde tu ultima visita.
 *
 *  **Esto existia en la API desde el primer dia y no lo pintaba nadie.** `GET /listas/{id}`
 *  devuelve `novedades` (`almacen.novedades`), `docs/PANTALLAS.md` lo daba por hecho («las dos
 *  secciones, el marcador, las novedades») y `docs/VEREDICTO.md` tambien, pero la palabra
 *  `novedades` **no aparecia en `app/src`**: el campo llegaba y se tiraba. Sin esto, una lista
 *  compartida es un sitio donde las cosas aparecen y desaparecen solas, que son las palabras del
 *  propio documento: quien llega a la tienda no sabe si lo que falta lo cogio su madre o lo quito
 *  alguien, ni si el pan lo puso ella o se apunto por error.
 *
 *  Tres decisiones:
 *
 *  - **Se dice quien y que hizo**: «Mama cogio la leche», «Marta puso papel de cocina». El verbo
 *    sale de lo ultimo que se hizo con la linea (`tachado_en`), que es lo que se quiere saber.
 *  - **Solo lo de otra gente.** Una linea que apunte yo y tache yo no es una novedad, es lo que
 *    acabo de hacer: se filtra por quien lo hizo, que es para lo que el `yo` viaja hasta aqui.
 *  - **Cuatro y «y N mas».** La API manda hasta doce, y doce lineas de novedades tapan lo que se
 *    viene a mirar (la lista). Lo que no se enseña se cuenta, no se esconde.
 */
function Novedades({ novedades, yo }: { novedades: Novedad[]; yo: string | null }) {
  const deOtros = novedades.filter((n) => {
    const quien = n.tachado_en ? n.tachado_por : n.anadido_por
    return quien !== null && quien !== yo
  })
  if (!deOtros.length) return null
  const dichas = deOtros.slice(0, 4)
  const resto = deOtros.length - dichas.length
  return (
    <Aviso tono="info" titulo="Desde la última vez que miraste">
      <ul className="grid gap-0.5">
        {dichas.map((n, i) => (
          <li key={`${n.nombre_visto}-${i}`}>
            <strong>{n.tachado_en ? n.tachado_por : n.anadido_por}</strong>{' '}
            {n.tachado_en ? 'cogió' : 'puso'} {n.nombre_visto}
          </li>
        ))}
      </ul>
      {resto > 0 && <p className="mt-1 text-etiqueta">y {resto} más.</p>}
    </Aviso>
  )
}

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

      <h3 className="mt-4 text-cuerpo font-semibold">Mandar un enlace</h3>
      <p className="mt-1 text-cuerpo text-tinta-suave">
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
            <Etiqueta tono="mal">{textoDeError(invita.error)}</Etiqueta>
          </Aviso>
        </div>
      )}

      {enlace && (
        <>
          <p className="mt-3 text-cuerpo text-tinta-suave">
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
              className="min-h-[44px] min-w-[12rem] flex-1 rounded-campo border border-borde bg-fondo px-3 py-2"
            />
            <Boton variante="principal" onClick={copia}>
              {copiado ?? 'Copiar'}
            </Boton>
          </div>
          {sinPortapapeles && (
            <p className="mt-2 text-cuerpo text-aviso">
              Este navegador no deja copiar solo (el portapapeles necesita https,
              y esto va por http). El enlace ya está seleccionado: cópialo a mano.
            </p>
          )}
        </>
      )}

      <h3 className="mt-4 text-cuerpo font-semibold">Compartir con quien ya tiene cuenta</h3>
      <p className="mt-1 text-cuerpo text-tinta-suave">
        Si ya usa esta Cesta, con su usuario entra sin enlace. Un nombre de
        usuario se escribe mal con una facilidad pasmosa: si no existe nadie con
        ese, se avisa aquí mismo.
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
        <p className="mt-2 text-cuerpo">
          {/* **Compartir contigo mismo no te quita la lista, y ahora se dice.** Medido el 28 de
              septiembre de 2026: escribir tu propio usuario metia tu fila con papel «escribe»,
              la tarjeta se cerraba -- solo se pinta para el dueno -- y la lista se quedaba sin
              poder invitar ni borrar (403 en las dos). La base ya no deja bajar al dueno de su
              papel, y aqui se dice que no hacia falta: «Ya está dentro Fulano» sonaba a que
              habia pasado algo. */}
          {comparte.data.papel === 'dueno' ? (
            <Etiqueta tono="info">Esa lista ya es tuya, no hace falta compartirla</Etiqueta>
          ) : (
            <Etiqueta tono="bien">
              Ya está dentro {comparte.data.nombre || `@${comparte.data.usuario}`}
            </Etiqueta>
          )}
        </p>
      )}
      {comparte.isError && (
        <div className="mt-2">
          <Aviso tono="mal" titulo="No he podido compartirla">
            <Etiqueta tono="mal">{textoDeError(comparte.error)}</Etiqueta>
          </Aviso>
        </div>
      )}

      <h3 className="mt-4 text-cuerpo font-semibold">Quién está dentro</h3>
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
        <p className="mt-2 text-cuerpo text-tinta-suave">
          {revocadas ? `Anulados ${revocadas}.` : 'No había ninguno.'} A quien ya
          entró no le afecta: sigue en la lista.
        </p>
      )}
      {revoca.isError && (
        <Etiqueta tono="aviso">{textoDeError(revoca.error)}</Etiqueta>
      )}
    </Tarjeta>
  )
}

/** La lista, con lo que se ha tocado sin cobertura ya aplicado encima.
 *
 *  Es lo que hace que tachar **funcione** sin red en vez de solo guardarse: la linea
 *  sale tachada en el mismo toque, sin ruedecita y sin esperar a nadie. Y una linea
 *  quitada sin cobertura desaparece de la lista, que es lo que se acaba de pedir.
 *
 *  Gana **el ultimo cambio de cada linea**: tachar y destachar sin cobertura no son dos
 *  cambios que subir en orden, es el ultimo (y la API es idempotente, asi que da igual
 *  cuantas veces se haya tocado).
 */
function conPendientes(lineas: Linea[], cola: CambioPendiente[]): Linea[] {
  if (!cola.length) return lineas
  const porLinea = new Map(cola.map((c) => [c.lineaId, c]))
  const salida: Linea[] = []
  for (const linea of lineas) {
    const pendiente = porLinea.get(linea.id)
    if (!pendiente) {
      salida.push(linea)
      continue
    }
    const c = pendiente.cambio
    if (c.borrado) continue
    salida.push({
      ...linea,
      cantidad: c.cantidad ?? linea.cantidad,
      // La hora del movil, que es la que se mando y la que va a valer cuando suba.
      tachado_en: c.tachado === true ? (linea.tachado_en ?? pendiente.momento)
        : c.tachado === false ? null : linea.tachado_en,
    })
  }
  return salida
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
  // Lo que se toco sin cobertura y todavia no ha llegado al servidor.
  const [cola, setCola] = useState<CambioPendiente[]>([])
  // Dos frases para el mismo sitio: lo que se ha subido, o que la cola no se ha podido
  // guardar (modo privado del navegador). La segunda es un aviso de verdad.
  const [subidos, setSubidos] = useState<string | null>(null)
  const [sinGuardar, setSinGuardar] = useState(false)
  // Lo de la cuenta, detras del boton de opciones de la cabecera.
  const [opciones, setOpciones] = useState(false)

  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })

  const listaId = listaDelDiario(listas.data, elegida)
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
  /** **El reparto, para el precio de cada linea y para la cadena del total.**
   *
   *  `GET /listas/{id}` no manda el coste de cada linea; el reparto si (`coste_cent`). La
   *  misma `queryKey` que usa `RepartoEnTiendas` -- que se pinta mas abajo --, asi que React
   *  Query comparte la respuesta y **esto no anade una peticion**: solo lee lo que ya viene.
   *  Si falla, no se pinta un aviso mas: las filas se quedan sin precio y la tarjeta del
   *  reparto es la que cuenta lo que pasa.
   */
  const repartoDeLaLista = useQuery({
    queryKey: ['reparto', listaId],
    queryFn: () => pedirReparto(listaId as string),
    enabled: listaId != null,
  })

  /** La lista partida en dos, que es como se usa de pie en la tienda.
   *
   *  «Por coger» y «en el carro» no son dos estados de animo del mismo dato: son
   *  las dos mitades del trabajo que se esta haciendo. La marca es `tachado_en`
   *  porque la API tacha y mete en el carro **a la vez** (`almacen.py`), asi que no
   *  son dos cosas que puedan separarse: tachado = ya esta en el carro.
   *
   *  **Y se pintan con lo que hay sin subir aplicado encima**: si acabas de tachar sin
   *  cobertura, la linea tiene que salir tachada ya -- "que tachar funcione igual sin
   *  red" no es que se guarde, es que se vea. Los totales de abajo siguen siendo los del
   *  servidor, y por eso la linea de "N cambios sin subir" esta ahi: para que nadie
   *  compare un total que todavia no cuenta lo que acaba de tocar. */
  const lineas = conPendientes(detalle.data?.lineas ?? [], cola)
  const porCoger = lineas.filter((l) => l.tachado_en === null)
  const enElCarro = lineas.filter((l) => l.tachado_en !== null)
  /** **Los grupos que ya están en esta lista**, para que el mosaico no los vuelva a ofrecer.
   *
   *  *Es el dato que convierte «rellenar sola» en una sugerencia y no en un duplicado: se pasa a
   *  `Mosaico` y se resta antes de contar y de enseñar la previa. Sin él, el botón ofrecería
   *  añadir otra vez la leche que ya está apuntada. Se quitan los nulos (las líneas de texto
   *  libre no apuntan a ningún grupo) y los repetidos (dos líneas del mismo grupo son una).* */
  const gruposEnLaLista = [...new Set(
    lineas.map((l) => l.grupo_id).filter((g): g is number => g !== null),
  )]
  const precios = preciosPorLinea(repartoDeLaLista.data)
  const cambia = useMutation({
    // **`networkMode: 'always'` es la pieza que hace que la cola sirva.** Por defecto,
    // React Query *pausa* una mutacion cuando `navigator.onLine` es falso: no la manda,
    // no falla, no avisa, y la reintenta sola cuando vuelve la red. Eso suena bien y es
    // justo lo que no queremos: el cambio vive **en memoria**, asi que si se cierra la
    // pestaña en el pasillo se pierde, no hay nada que subir despues y **la pantalla no
    // puede decir que hay cambios sin subir** porque no sabe que los hay.
    //
    // Medido en un navegador de verdad (23 sep 2026, `plataforma/prueba_navegador.py`):
    // sin esto, tachar sin cobertura no pintaba nada, no encolaba nada, y el PATCH salia
    // al volver la red. Con esto, la peticion se intenta, falla con un `TypeError`, y el
    // cambio acaba donde tiene que acabar: en la cola del movil, con su hora, pintado y
    // diciendolo.
    networkMode: 'always',
    mutationFn: ({ lineaId, cambio }: { lineaId: string; cambio: CambioLinea;
      linea?: Linea | null }) =>
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
      cliente.invalidateQueries({ queryKey: ['reparto', listaId] })
    },
    onError: (error, variables) => {
      // **Sin cobertura no es un error: es un cambio que espera.** Se guarda en el
      // movil con la hora a la que se toco (§3.5 del encargo: *"que tachar funcione
      // igual sin red, sin ruedecita ni error"*) y se sube al volver la cobertura. Un
      // aviso rojo aqui seria decirle a alguien, de pie en el pasillo, que la
      // aplicacion se ha roto -- cuando lo unico que pasa es que no hay red.
      if (!esSinRed(error)) return
      const cola = apuntaCambio(listaId as string, {
        lineaId: variables.lineaId,
        cambio: variables.cambio,
        momento: variables.cambio.momento ?? new Date().toISOString(),
      })
      if (cola) setCola(cola)
      else setSinGuardar(true)
    },
  })

  /** Sube de golpe lo que espera. Se llama al volver la cobertura y al abrir la lista. */
  const sube = useMutation({
    // Y lo mismo al subir la cola: 'pausada' no sirve, porque entonces el fallo no llega
    // nunca y no se puede contar que no se ha podido.
    networkMode: 'always',
    mutationFn: (pendientes: CambioPendiente[]) =>
      sincronizar(listaId as string, pendientes.map((c): CambioDeCola => ({
        id: c.lineaId, momento: c.momento, ...c.cambio,
      }))),
    onSuccess: (r, pendientes) => {
      // La cola se vacia **solo cuando el servidor dice que los aplico**. Y lo que
      // fallo se queda: puede ser una linea que la otra persona ya borro, y eso hay que
      // poder contarlo en vez de perderlo en silencio.
      vaciaCola(listaId as string)
      setCola(leerCola(listaId as string))
      if (r.aplicados) {
        setSubidos('Ya se han guardado los cambios que hiciste sin conexión.')
      }
      if (r.fallidos.length) setSinGuardar(true)
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      cliente.invalidateQueries({ queryKey: ['donde', listaId] })
      cliente.invalidateQueries({ queryKey: ['reparto', listaId] })
      void pendientes
    },
  })

  // La cola se lee **de lo guardado en el movil**, no se hereda del estado: si se cierra
  // la pestaña en el pasillo, los cambios siguen ahi al volver a abrirla.
  useEffect(() => {
    setCola(listaId ? leerCola(listaId) : [])
    setSubidos(null)
  }, [listaId])

  // Y se sube solo **al volver la cobertura** -- y al abrir la lista, por si la pestaña
  // se cerro con la cola llena --, que es lo que pide el encargo: *"al volver, se suba
  // solo y se diga en una frase"*. Sin red no se intenta: subir desde el pasillo sin
  // cobertura es exactamente lo que no funciona.
  useEffect(() => {
    const alVolver = () => {
      const pendientes = listaId ? leerCola(listaId) : []
      if (!listaId || !pendientes.length || sube.isPending) return
      if (!navigator.onLine) return
      sube.mutate(pendientes)
    }
    window.addEventListener('online', alVolver)
    alVolver()
    return () => window.removeEventListener('online', alVolver)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listaId, cola.length])

  if (sesion.isLoading) return <Cargando que="tu lista" />
  if (!sesion.data?.usuario) {
    return (
      // *** Y la raiz de ESTA rama tambien lleva el patron, *y no es un detalle. *** *
      //
      // *Era `grid gap-4`: *un grid **sin `min-h-full`**, *y por eso la tarjeta de entrar
      // se quedaba **a un tercio de la pantalla** con cientos de pixeles vacios debajo.* *
      //
      // *Las dos salidas faciles se probaron antes de tocar esto: *`grow` en la
      // `Tarjeta` **no hizo nada** *(-- *el padre no era columna flexible --)*, *y
      // `min-h-full` en un envoltorio **tampoco**, *porque no resuelve contra un padre de
      // altura `auto`.* *Las dos medidas estan en `COMO-SE-MIDE.md`, *secciones 12 y 15.* *
      //
      // *Lo que si funciona es esto, *que es **el mismo patron de `Buscar`**: *raiz
      // `flex min-h-full flex-col`, *y el bloque que debe llenar con `grow`.* *
      <div className="flex min-h-full flex-col gap-4">
        {/* **El título de la página, sin sesión.** `Introducir` lleva su `h2` («Entra para ver
            tu lista»), así que la pantalla se quedaba sin `h1`: quien navega por encabezados
            abría una página que no decía cómo se llama. Va oculto porque el `h2` ya lo dice en
            voz alta. Medido con `data/debug/accesibilidad.py --sin-sesion` el 27 de septiembre
            de 2026, que es la cara que no había mirado nadie: el instrumento entraba siempre. */}
        <h2 className="sr-only">Lista</h2>
        <Introducir
          alEntrar={() => {
            // Al entrar hay que volver a preguntar quien soy y que listas tengo:
            // las de antes eran las de nadie.
            cliente.invalidateQueries({ queryKey: ['yo'] })
            cliente.invalidateQueries({ queryKey: ['listas'] })
          }}
        />
      </div>
    )
  }

  if (listas.isLoading) return <Cargando que="tus listas" />
  if (listas.isError) {
    // **`Fallo` y no un `Vacio` escrito aqui.** Es la unica pantalla que se lo escribia a
    // mano, y por eso era la unica sin «Volver a intentarlo»: medido en un navegador el 23
    // de septiembre de 2026, con `/api/listas` devolviendo 500, la cesta decia «No he podido
    // traer tus listas» **sin un solo boton** -- habia que recargar la pagina a mano, que en
    // el movil no es evidente. Ademas `Fallo` es quien decide el tono: sin cobertura no es
    // rojo, es un movil en un pasillo (`ui.tsx`), y esa decision tiene que estar en un sitio
    // y no repetida en seis pantallas.
    return <Fallo error={listas.error} reintentar={() => void listas.refetch()} />
  }
  if (!listas.data?.length) {
    // **Una lista vacia no puede ser un cartel que manda a otra pantalla.** El §2 del
    // encargo pone esto como el peor momento de la aplicacion: *"un amigo que se
    // registra ve un buscador vacio, **una cesta vacia** y un panel de indices que no
    // significa nada"*. Antes, esta pantalla decia "busca un producto, abre su ficha y
    // pulsa Añadir": tres pasos para volver al mismo sitio, y la aplicacion sin hacer
    // nada por quien acaba de llegar.
    //
    // Ahora se ensena **la aplicacion funcionando con datos reales** (`Mosaico`, con la
    // compra basica o lo que compra la casa segun lo que haya) y se apunta de un toque.
    // La lista de casa la crea el propio "Añadir" si no existe (`useAnadeALaCesta`).
    return (
      <div className="flex min-h-full flex-col gap-4">
        <Vacio titulo="No tienes ninguna lista" className="grow">
          <p>
            Todavía no hay listas guardadas. Busca un producto o toca uno de abajo: se
            apunta en la lista de casa, que se crea sola, y la cantidad se cambia aquí.
          </p>
        </Vacio>
        <Mosaico limite={6} enUnaLista />
      </div>
    )
  }

  const nombreDeLaLista = listas.data.find((l) => l.id === listaId)?.nombre ?? 'La lista'
  const esDeCasa = listas.data.find((l) => l.id === listaId)?.es_de_casa === true
  const puedeCambiarla = detalle.data != null && detalle.data.papel !== 'mira'

  return (
    <div className="flex min-h-full flex-col gap-bloque">
      <CabeceraDeLaLista
        nombre={nombreDeLaLista}
        deCasa={esDeCasa}
        opciones={opciones}
        alAlternar={() => setOpciones(!opciones)}
      />

      {/* **Lo de la cuenta, detras del boton de opciones.** Son tres puertas que se buscan una
          vez y no se usan en el pasillo; el armazon ya las tiene en su menu. Cerrado por
          defecto, porque lo primero que se lee tiene que ser la lista. */}
      {opciones && (
        <OpcionesDeLaCuenta
          alSalir={async () => {
            await salir()
            cliente.invalidateQueries()
          }}
        />
      )}

      {/* **La barra de las listas**: cual, crear otra, cambiarle el nombre y quitarla.
          *Sigue a la vista y no detras del boton de opciones a proposito: es la unica forma de
          cambiar de lista, y la puerta de funciones la pulsa sin abrir nada.* */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        {/* **El selector de listas, siempre.** Antes solo aparecia cuando habia mas de
            una, y eso hace que no se pueda **crear la segunda**: el boton de «nueva
            lista» vivia detras de un desplegable que no existia hasta que ya tuvieras
            dos. Con una sola lista, esto es un desplegable de una opcion y un boton. */}
        <select
          value={listaId ?? ''}
          onChange={(e) => setElegida(e.target.value)}
          aria-label="Lista"
          className="min-h-[44px] max-w-[11rem] rounded-campo border border-borde-fuerte bg-papel px-2 py-1"
        >
          {listas.data.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nombre}{l.lineas ? ` (${l.lineas})` : ''}
            </option>
          ))}
        </select>
        <NuevaLista alCrear={(id) => {
          cliente.invalidateQueries({ queryKey: ['listas'] })
          setElegida(id)
        }} />
        {puedeCambiarla && (
          <AccionesDelNombre
            lista={{ id: listaId as string, nombre: nombreDeLaLista }}
            alHecho={(id) => {
              cliente.invalidateQueries({ queryKey: ['listas'] })
              if (id === null) {
                setElegida('')
                cliente.invalidateQueries()
              }
            }}
          />
        )}
      </div>

      {/* De donde viene esta pantalla. Se dice una vez, al llegar del enlace:
          aterrizar en una lista que no has abierto tu, sin explicacion, parece
          un error de la aplicacion y no una invitacion aceptada. */}
      {/* **Con listas pero sin ninguna elegida, se dice.** `listaDelDiario` devuelve `null`
          cuando no hay lista de casa ni eleccion, y a proposito: elegir por quien no ha
          elegido es como una compra acaba anotada en la lista de otra persona. Antes esa
          cara era un desplegable en blanco y nada debajo; ahora se pide elegir, que es lo
          unico que se puede hacer. */}
      {listaId == null && !detalle.isLoading && !detalle.isError && (
        <Vacio titulo="Elige una lista">
          <p>
            Elige en el desplegable de arriba la lista que quieras ver, y aquí saldrá lo
            que te falta comprar.
          </p>
        </Vacio>
      )}

      {venida?.aviso && (
        <Aviso tono="bien">
          <p>{venida.aviso}</p>
        </Aviso>
      )}

      {/* El hueco de las lineas, con su forma: cinco filas del alto de una linea. Esta
          es la pantalla que se usa de pie y con una mano, y aqui un salto de
          maquetacion mueve el boton que el pulgar ya tenia camino de pulsar. */}
      {detalle.isLoading && <Esqueleto filas={5} alto="3.5rem" />}

      {/* Lo que se toco sin cobertura. **Una linea discreta, no un aviso rojo**: estar
          sin red en un supermercado no es un fallo de la aplicacion (§3.5 del encargo),
          y lo unico que hay que saber es que esos cambios no han llegado todavia. */}
      {cola.length > 0 && (
        <Aviso tono="info">
          <p>
            {cola.length === 1
              ? '1 cambio sin guardar. Se guardará cuando vuelva la conexión.'
              : `${cola.length} cambios sin guardar. Se guardarán cuando vuelva la conexión.`}
          </p>
        </Aviso>
      )}

      {/* Y cuando vuelve y sube, se dice en una frase y se va. */}
      {subidos && (
        <Aviso tono="bien">
          <p>{subidos}</p>
        </Aviso>
      )}

      {/* Este si es un aviso de verdad: la cola no se ha podido guardar (el navegador en
          modo privado deja leer y lanza al escribir). Un cambio que se pierde al cerrar
          la pestaña hay que decirlo. */}
      {sinGuardar && (
        <Aviso tono="aviso" titulo="No puedo guardar aquí">
          <p>Este cambio se perderá si cierras.</p>
        </Aviso>
      )}

      {/* **Cuando la API contesta que no** (un 403 de una lista de solo mirar, un 500):
          eso si hay que mirarlo, y va en rojo con lo que ha dicho. Que no haya red no
          entra aqui: eso ya no es un error, es un cambio que espera. */}
      {cambia.isError && !esSinRed(cambia.error) && (
        <Aviso tono="mal" titulo="No he podido guardar el cambio">
          <Etiqueta tono="mal">{textoDeError(cambia.error)}</Etiqueta>
          <p className="mt-1">
            La lista sigue como estaba.
          </p>
        </Aviso>
      )}

      {/* Y si lo que no llega es la propia lista -- abrir la aplicacion en el
          pasillo sin cobertura --, antes no se pintaba **nada**: el estado de
          carga desaparecia y quedaba el encabezado con la pantalla en blanco,
          que es lo que parece una aplicacion rota. */}
      {detalle.isError && (
        esSinRed(detalle.error) ? (
          <Aviso tono="aviso" titulo="Sin cobertura">
            <p>
              No he podido traer la lista ahora mismo. Vuelve a intentarlo cuando
              tengas red.
            </p>
          </Aviso>
        ) : (
          <Fallo error={detalle.error} reintentar={() => void detalle.refetch()} />
        )
      )}

      {detalle.data && (
        <>
          {/* **El precio estimado, sobre bosque y lo primero.** Es la cifra que se mira
              mientras se anade, y el artboard la pone por delante de la lista. */}
          {lineas.length > 0 && (
            <PrecioEstimado
              totalCent={detalle.data.estimacion?.total_cent
                ?? detalle.data.cotizacion_lista_cent ?? null}
              productos={lineas.length}
              sinPrecio={detalle.data.estimacion?.sin_precio ?? 0}
              cadena={cadenaDelTotal(repartoDeLaLista.data)}
              fechaDatos={detalle.data.fecha_datos}
            />
          )}

          {/* **Las novedades: lo que ha tocado la otra persona desde tu ultima visita.**
              La API las manda desde el primer dia (`GET /listas/{id}` → `novedades`) y
              `docs/PANTALLAS.md` decia que estaban hechas, pero **ninguna pantalla las
              pintaba**. Va antes de las dos secciones porque es una noticia: se lee al
              abrir y desaparece sola al recargar (la visita se marca al leer, en la misma
              peticion). */}
          <Novedades novedades={detalle.data.novedades ?? []}
                     yo={sesion.data?.usuario?.nombre
                         ?? sesion.data?.usuario?.usuario ?? null} />

          {lineas.length === 0 && (
            <Vacio titulo="La lista está vacía" className="grow">
              <p>
                Busca un producto o toca uno de abajo: se apunta en un toque, y la
                cantidad se cambia aquí.
              </p>
            </Vacio>
          )}

          {/* **Dos trozos, no una lista.** Es la unica pantalla que se usa de pie, en
              movimiento y con una mano, y con nueve lineas y cuatro ya cogidas hay que leer
              **nueve nombres** para saber cuales quedan. Con el encabezado se lee uno. Lo
              piden `docs/PANTALLAS.md` y `docs/UX-MOVIL.md`.

              El orden dentro de cada trozo es el de la API (`ORDER BY en_carrito,
              anadido_en`, almacen.py), y **dentro de un pasillo ese orden se respeta tal
              cual**: `porPasillo` solo reparte en tandas y las coloca en el orden del
              recorrido de la tienda. Los encabezados solo salen si su trozo tiene algo:
              un «0» es ruido, y el rato en que esta todo cogido es justo el que se mira. */}
          {porCoger.length > 0 && (
            <section
              aria-labelledby="lo-que-falta"
              className="rounded-tarjeta bg-papel shadow-apoyado"
            >
              <h2
                id="lo-que-falta"
                className="flex items-baseline gap-2 px-4 pt-3 text-micro uppercase text-tinta-tenue"
              >
                Lo que falta
                <span className="cifra text-tinta-suave">{porCoger.length}</span>
              </h2>
              {detalle.data.papel === 'mira' && (
                <div className="px-4 pt-2">
                  <Aviso tono="aviso">
                    <p>
                      Esta lista te la compartieron para mirar, así que no puedes
                      cambiarla: los botones están apagados por eso. Quien la creó
                      puede darte el papel de escribir cuando quiera.
                    </p>
                  </Aviso>
                </div>
              )}
              <ul className="mt-1">
                {porPasillo(porCoger).map(([pasillo, delPasillo]) => (
                  <li key={pasillo || 'sin-pasillo'}>
                    {/* **El pasillo, pegado arriba.** La lista se mira de pie, en
                        movimiento y con una mano, y lo que se necesita saber es en que
                        pasillo se esta. `top` sale de la altura real de la cabecera
                        (`--alto-cabecera`), no de un numero escrito: si la cabecera
                        envuelve en movil, un `top-14` acertaria hoy y fallaria mañana.
                        Las lineas sin pasillo van **las ultimas y sin encabezado**
                        (`porPasillo`), porque un dato que no tenemos no se coloca donde
                        tocaria: se deja al final, que es donde no estorba. */}
                    {pasillo && (
                      <h3 className="sticky top-[var(--alto-cabecera,0px)] z-10 bg-papel px-4 py-1 text-etiqueta font-semibold uppercase tracking-wide text-tinta-suave">
                        {pasillo}
                      </h3>
                    )}
                    <ul>
                      {delPasillo.map((l) => (
                        <UnaLinea
                          key={l.id}
                          linea={l}
                          precio={precios.get(l.id)}
                          guardando={cambia.isPending || detalle.data.papel === 'mira'}
                          cambiar={(lineaId, cambio) =>
                            cambia.mutate({ lineaId, cambio, linea: cambio.borrado ? l : null })}
                        />
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {enElCarro.length > 0 && (
            <section
              aria-labelledby="en-el-carro"
              className="rounded-tarjeta bg-papel shadow-apoyado"
            >
              <h2
                id="en-el-carro"
                className="flex items-baseline gap-2 px-4 pt-3 text-micro uppercase text-tinta-tenue"
              >
                En el carro
                <span className="cifra text-tinta-suave">{enElCarro.length}</span>
              </h2>
              <ul className="mt-1">
                {porPasillo(enElCarro).map(([pasillo, delPasillo]) => (
                  <li key={pasillo || 'sin-pasillo'}>
                    {pasillo && (
                      <h3 className="sticky top-[var(--alto-cabecera,0px)] z-10 bg-papel px-4 py-1 text-etiqueta font-semibold uppercase tracking-wide text-tinta-suave">
                        {pasillo}
                      </h3>
                    )}
                    <ul>
                      {delPasillo.map((l) => (
                        <UnaLinea
                          key={l.id}
                          linea={l}
                          precio={precios.get(l.id)}
                          guardando={cambia.isPending || detalle.data.papel === 'mira'}
                          cambiar={(lineaId, cambio) =>
                            cambia.mutate({ lineaId, cambio, linea: cambio.borrado ? l : null })}
                        />
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Deshacer en vez de confirmar: quitar una linea es la accion
              destructiva de esta pantalla. **El id es la llave**: la API hace
              ON CONFLICT (id) DO UPDATE con borrado_en = NULL (almacen.py:288),
              asi que reanadir con **el mismo id** resucita la linea en vez de
              crear otra. Por eso se manda l.id y no se deja que se genere uno.

              La linea quitada se lee de cambia.variables, que es la mutacion
              la que la guarda: asi no hace falta un useState aparte que se
              pueda quedar desincronizado con lo que se ve. Y desaparece sola en
              cuanto se hace cualquier otro cambio, porque las variables son las
              del ultimo.

              **Va fuera del trozo de las lineas** a proposito: al quitar la
              ultima, ese trozo no se pinta y el «Deshacer» desaparecia justo
              cuando mas falta hace. Lo encontro el navegador el 23 de septiembre
              de 2026 (`plataforma/prueba_navegador.py`). */}
          {cambia.variables?.linea && (
            <Aviso tono="info">
              <span className="flex flex-wrap items-center gap-3">
                Has quitado <strong>{cambia.variables.linea.nombre_visto}</strong>.
                <Boton
                  variante="sutil"
                  onClick={async () => {
                    const quitada = cambia.variables?.linea
                    if (!quitada || !listaId) return
                    await anadirLinea(
                      listaId,
                      {
                        nombre: quitada.nombre_visto,
                        grupo_id: quitada.grupo_id,
                        producto_id: quitada.producto_id,
                        cantidad: quitada.cantidad,
                      },
                      quitada.id,
                    )
                    cliente.invalidateQueries({ queryKey: ['lista', listaId] })
                    cliente.invalidateQueries({ queryKey: ['donde', listaId] })
                  }}
                >
                  Deshacer
                </Boton>
              </span>
            </Aviso>
          )}

          {lineas.length > 0 && (
            <>
              {/* El numero que se mira mientras se coge: al tachar algo, esto
                  es lo unico que confirma que el cambio ha llegado. */}
              <p className="px-1 text-etiqueta text-tinta-suave">
                <span className="cifra font-medium">
                  {euros(detalle.data.estimacion.por_recoger_cent)}
                </span>{' '}
                por coger ·{' '}
                <span className="cifra font-medium">
                  {euros(detalle.data.estimacion.en_carrito_cent)}
                </span>{' '}
                en el carro
              </p>

              {/* Y cuando ya esta todo cogido, cerrar: lo del carro se guarda y sale de
                  la lista. Va despues del numero que se mira al tachar, que es el orden
                  en que se hace. */}
              <CerrarCompra
                listaId={listaId as string}
                enElCarro={enElCarro.length}
                papel={detalle.data.papel}
                sello={detalle.data.cotizacion?.sello ?? null}
              />

              {/* *** AÑADIR PRODUCTO. *** *La puerta del artboard para buscar lo que no
                  esta en la cuadricula de abajo.* */}
              <Link
                to="/compra"
                className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-campo border border-dashed border-borde-fuerte px-4 text-cuerpo text-tinta-suave transition-colors duration-rapida ease-suave hover:text-tinta"
              >
                <span aria-hidden="true" className="text-entrada leading-none">+</span>
                Añadir producto
              </Link>
            </>
          )}

          {/* *** RELLENAR LO DE SIEMPRE, *con previa y sin añadir a escondidas*. *** *
              *WALL, «aprender de las listas»: la sugerencia se revisa antes de entrar
              (`INVESTIGACION-APP.md` §9.2-9.3). El componente `Mosaico` es quien la construye —
              «Se van a añadir N productos» con sus nombres— y aquí solo se monta donde tiene
              sentido:*
              *
              *  - **Solo en la lista de casa** (`useAnadeALaCesta` apunta ahí). Ofrecerlo mirando
              *    otra lista añadiría a escondidas a una lista que no es la que se tiene delante.
              *  - **También con la lista vacía**, que es donde la cuadricula de la compra básica
              *    contesta «¿qué me falta?» (regla 1 de `Mosaico.tsx`).
              *  - **Y con `enLaLista`**, para que no vuelva a ofrecer lo que ya está apuntado.
              *
              * *Va justo antes de «Dónde sale mejor tu cesta» a propósito: rellenar y comparar
              * son el mismo gesto, y la puerta a la comparación queda **al lado del relleno**,
              * sin una segunda pantalla ni un segundo enlace con la misma promesa.* */}
          {(esDeCasa || lineas.length === 0) && (
            <Mosaico limite={6} enUnaLista enLaLista={gruposEnLaLista} />
          )}

          {lineas.length > 0 && (
            <>
              {/* *** COMPARAR. *** *La unica puerta a esa pantalla: dos enlaces con la misma
                  promesa se contradicen el dia que una cambie.* */}
              <section aria-labelledby="comparar" className="flex flex-col gap-2">
                <h2
                  id="comparar"
                  className="font-serif text-titulo font-semibold text-tinta"
                >
                  Dónde sale mejor tu cesta
                </h2>
                <p className="text-etiqueta text-tinta-suave">
                  El total en cada cadena y lo que le falta a cada una.
                </p>
                <Link
                  to={`/compra/listas/${listaId}/comparar`}
                  className="inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-campo bg-verde px-4 text-cuerpo font-semibold text-sobre-verde shadow-apoyado transition-colors duration-rapida ease-suave hover:brightness-110"
                >
                  Comparar mi cesta
                  <svg
                    viewBox="0 0 24 24"
                    width="18"
                    height="18"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                    focusable="false"
                  >
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </Link>
              </section>
            </>
          )}

          {/* *** PEGAR UNA LISTA ENTERA, *viendola antes de guardar*. ***
              *M05: «pegar varias lineas con previa».* *La regla de que «2 kg» no son dos
              envases vive en `logica/pegar.ts`, y aqui solo se monta: el componente no
              tiene campo de envases, asi que no puede inventarlo.*
              *La nota lleva lo que la persona escribio; la cantidad de envases la pone
              ella en la lista, que es donde se ve.* */}
          <PegarEnLaLista
            alAnadir={async ({ nombre, nota, grupoId }) => {
              await anadirLinea(listaId as string, {
                nombre, nota, grupo_id: grupoId ?? null, producto_id: null,
              })
              cliente.invalidateQueries({ queryKey: ['lista', listaId] })
              cliente.invalidateQueries({ queryKey: ['reparto', listaId] })
            }}
          />

          <ExportarLista
            lineas={lineas}
            nombreLista={listas.data?.find((l) => l.id === listaId)?.nombre ?? 'cesta'}
          />
        </>
      )}

      {/* **Dónde compro cada cosa**: la lista partida por tiendas, con el total de cada
          sublista y el de todo.

          **Estaba justo debajo del total, y se ha bajado, y no es un capricho.** El 27 de
          septiembre de 2026 lo midió la puerta en un móvil de 390 x 844: esta tarjeta mide
          **592 px** y, con ella delante, la primera cosa que se puede tachar quedaba a
          **1.269 px** -- muy por debajo de la banda útil (109..787). Es decir: en la pantalla
          donde se tacha, no se veía nada que tachar sin desplazar. La pregunta «¿y dónde lo
          compro?» sigue contestada en la primera pantalla (`Inicio`, y sin desplazar), y aquí
          abajo sigue estando, antes de las tarjetas de cadena; pero la lista manda, que es lo
          que se mira veinte veces en el pasillo. `docs/PANTALLAS.md` ya lo decía así. */}
      {detalle.data && (
        <RepartoEnTiendas listaId={listaId as string} papel={detalle.data.papel} />
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
            sean cosas que ninguna cadena venda, o que ya no estén.
          </p>
        </Vacio>
      )}
      {compra.data && compra.data.repartido && <Repartido reparto={compra.data.repartido} />}
    </div>
  )
}
