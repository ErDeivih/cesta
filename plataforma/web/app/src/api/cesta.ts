/** La lista de la compra y quien ha entrado.
 *
 *  Es la parte de la API que necesita **sesion**: las listas y los favoritos son
 *  de cada uno, y el backend la lleva con una cookie. Por eso este fichero no usa
 *  `pide()` tal cual: hace falta mandar `credentials` en las peticiones que
 *  escriben, y `pide()` ya lo hace (`same-origin`), asi que vale la misma puerta.
 *
 *  Un solo origen (Caddy) es lo que hace que la cookie funcione sin CORS. Con dos
 *  origenes habria que pelear con `SameSite` y esto no funcionaria.
 *
 *  `pide()` solo sabe de GET. Lo que escribe (anadir y cambiar lineas, crear la
 *  lista de casa, invitar, compartir con alguien, anular los enlaces) pasa por
 *  `escribe()`, que es la misma puerta con metodo y
 *  cuerpo, y el mismo trato del error: `ErrorApi` con el `detail` de la API para
 *  que la pantalla pueda decir QUE ha fallado y no solo que fallo.
 */
import { ErrorApi, pide } from './cliente'
import type { Donde, Estimacion, Linea, Lista, RepartoTiendas, Sesion } from '../tipos'

/** Entra con usuario y clave. La cookie la pone la API en la respuesta. */
export async function entrar(usuario: string, clave: string,
                             dispositivo = 'web'): Promise<void> {
  const respuesta = await fetch('/api/entrar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ usuario, clave, dispositivo }),
  })
  if (!respuesta.ok) {
    let detalle: string | null = null
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo?.detail === 'string') detalle = cuerpo.detail
    } catch {
      // Un 502 de Caddy no es JSON: el detalle se queda en null.
    }
    throw new ErrorApi(respuesta.status, detalle)
  }
}

/** Crea la cuenta y entra con ella, todo en la misma respuesta.
 *
 *  Va escrita a mano como `entrar()` y no con `escribe()`, que ya sabe hacer
 *  esto: son las dos unicas rutas que **abren sesion**, y tienen que leerse
 *  igual -- mismo `credentials`, mismo trato del error, mismo `detail` -- porque
 *  lo que se rompe si una se escribe distinto es justo lo que sostiene todo lo
 *  demas. `escribe()` se queda para lo que se escribe dentro de la cesta.
 *
 *  No devuelve quien eres aunque la API lo mande (`{"usuario": ...}`): el unico
 *  sitio donde vive ese dato es la consulta `yo()`, y copiarlo aqui seria un
 *  segundo sitio que puede quedar desfasado. Quien llama recarga `yo()` y ya.
 */
export async function registrarse(usuario: string, nombre: string, clave: string,
                                  dispositivo = 'web'): Promise<void> {
  const respuesta = await fetch('/api/registrarse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ usuario, nombre, clave, dispositivo }),
  })
  if (!respuesta.ok) {
    let detalle: string | null = null
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo?.detail === 'string') detalle = cuerpo.detail
    } catch {
      // Un 502 de Caddy no es JSON: el detalle se queda en null.
    }
    // El 403 (registro cerrado), el 409 (usuario cogido), el 422 (una regla) y
    // el 429 ya vienen con la frase escrita por la API. Aqui no se traducen ni
    // se resumen: se suben tal cual para que la pantalla las ensene.
    throw new ErrorApi(respuesta.status, detalle)
  }
}

/** Sale: borra la cookie. */
export async function salir(): Promise<void> {
  await fetch('/api/salir', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
}

/** **Darse de baja**: se lleva la cuenta, sus listas y sus favoritos.
 *
 *  La API devuelve cuantas listas se llevo y cuantas lineas quedaron: lo que alguien anadio
 *  a listas de otras personas **se queda**, sin autor, porque borrarlo vaciaria la compra de
 *  quien no ha pedido nada. Eso cuenta la pantalla, que es lo que hace que el numero sea
 *  util y no un adorno.
 *
 *  Es la unica operacion de esta aplicacion que **no se puede deshacer**, asi que la pantalla
 *  la confirma escribiendo el propio usuario (`Ajustes.tsx`), como hacia la interfaz vieja
 *  (`app.js:1571-1603`): un boton de "¿seguro?" se pulsa sin leer.
 */
export async function borrarme(): Promise<{ listas_borradas: number;
                                           lineas_conservadas: number }> {
  return await escribe<{ listas_borradas: number; lineas_conservadas: number }>(
    '/yo', 'DELETE')
}

/** Quien esta dentro, si hay alguien. Nunca falla: sin sesion devuelve null. */
export async function yo(): Promise<Sesion> {
  try {
    return await pide<Sesion>('/yo')
  } catch {
    return { usuario: null, preferencias: {} }
  }
}

export async function misListas(): Promise<Lista[]> {
  const r = await pide<{ listas: Lista[] }>('/listas')
  return r.listas ?? []
}

/** Una lista nueva. Hace falta para la de casa: quien entra por primera vez no
 *  tiene ninguna y sin esto no habria donde anadir nada. */
export async function crearLista(nombre: string, esDeCasa = false): Promise<Lista> {
  return await escribe<Lista>('/listas', 'POST', { nombre, es_de_casa: esDeCasa })
}

/** Alguien que esta dentro de una lista. Lo manda `GET /listas/{id}`. */
export interface Persona {
  usuario: string
  /** El nombre de pila. `null` si quien se dio de alta no lo puso. */
  nombre: string | null
  /** `dueno` | `escribe` | `mira`. */
  papel: string
  /** Cuándo entró. **Viaja y no se pinta, y está mirado**: la columna admite NULL, pero hoy no
   *  lo escribe nadie -- los tres sitios que rellenan `lista_acceso` ponen `now()` (crear la
   *  lista, compartir por usuario y aceptar un enlace) --, así que no hay estado «invitada y
   *  todavía no ha entrado» que enseñar. Se probó a pintarlo el 30 de septiembre de 2026 y se
   *  quitó el mismo día: una etiqueta para un estado que la API no produce es código muerto. */
  aceptado_en: string
}

/** Algo que ha tocado otra persona desde tu ultima visita. Lo manda `GET /listas/{id}`. */
export interface Novedad {
  nombre_visto: string
  en_carrito: boolean
  anadido_en: string | null
  tachado_en: string | null
  anadido_por: string | null
  tachado_por: string | null
}

export interface DetalleLista {
  papel: string
  lineas: Linea[]
  estimacion: Estimacion
  personas: Persona[]
  fecha_datos: string
  /**
   * Lo que ha tocado la otra persona desde que miraste la lista. Vacio si no hay nada.
   *
   * **Llevaba desde el primer dia viajando en la respuesta y sin pintarse en ninguna pantalla.**
   * `docs/PANTALLAS.md` decia que estaba hecho («las dos secciones, el marcador, las novedades»)
   * y `docs/VEREDICTO.md` tambien, pero `novedades` no aparecia en `app/src`: la lista compartida
   * volvia a ser un sitio donde las cosas aparecen y desaparecen solas. Se pinta en `Cesta.tsx`.
   */
  novedades?: Novedad[]
}

/** **Lo que el plan meteria en la lista, sin tocar la lista.**
 *
 *  Contesta las dos preguntas que hacen falta para no duplicar: **que entraria** y **que ya esta**.
 *  El calculo es el mismo que el de la accion -- `_del_plan`, en el API -- porque una previa que
 *  miente es peor que no tener previa.
 */
export interface PreviaDelPlan {
  entrarian: { nombre: string; cantidad: number | null; unidad: string | null
               receta: string; version: number; fecha: string }[]
  ya_estaban: string[]
  /** **Los que NO pueden entrar**, con su nombre: un ingrediente escrito a mano no esta enlazado con
   *  el catalogo, y la tabla exige `linea_con_destino`. Antes se prometian igual y la accion
   *  reventaba con un 500. Medido el 13 de octubre de 2026. */
  sin_catalogo: string[]
  total: number
  desde: string
  hasta: string
}

export async function previaDelPlan(listaId: string, desde: string,
                                    hasta: string): Promise<PreviaDelPlan> {
  return await pide<PreviaDelPlan>(`/listas/${listaId}/desde-el-plan`, { desde, hasta })
}

/** **La vista previa de consumir**: que lineas de la ultima compra se podrian anotar en el diario.
 *
 *  `anotarian` son las que tienen datos; **`sin_dato`** las que no, con su nombre -- *anotar las que
 *  se puede y callar las demas convertiria un dato que falta en una comida que parece completa*.
 *  Y `cobertura` dice cuantas traen dato de cuantas, que es lo que hace que esto no mienta.
 */
export interface PreviaDeLaCompra {
  compra_id: string | null
  anotarian: { linea_id: string; nombre: string; kcal: number | null
               proteinas_g: number | null; grasas_g: number | null
               hidratos_g: number | null; cantidad: number | null }[]
  sin_dato: string[]
  cobertura: { con_dato: number; total: number }
}

export async function previaDeLaCompra(listaId: string,
                                       compraId?: string): Promise<PreviaDeLaCompra> {
  return await pide<PreviaDeLaCompra>(`/listas/${listaId}/desde-la-compra`,
                                      compraId ? { compra_id: compraId } : undefined)
}

export async function anotarDeLaCompra(listaId: string, fecha: string, comida: string,
                                       lineas: string[] = []): Promise<unknown> {
  return await escribe(`/listas/${listaId}/desde-la-compra`, 'POST',
                       { fecha, comida, lineas })
}

export async function traerDelPlan(listaId: string, desde: string, hasta: string): Promise<unknown> {
  const q = `desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`
  return await escribe(`/listas/${listaId}/desde-el-plan?${q}`, 'POST', {})
}

export async function verLista(id: string): Promise<DetalleLista> {
  return await pide<DetalleLista>(`/listas/${encodeURIComponent(id)}`)
}

/** Donde sale mas barata la lista entera. Con las ofertas puestas. */
export async function donde(id: string,
                            cadenas?: string[]): Promise<Donde> {
  return await pide<Donde>(`/listas/${encodeURIComponent(id)}/donde`, {
    cadenas: cadenas?.length ? cadenas.join(',') : undefined,
  })
}

/* --------------------------------------- la lista, partida por tiendas ------ */

/** Lo que se ha decidido: la lista agrupada por la tienda de cada cosa.
 *
 *  `donde()` contesta «¿donde sale mas barata la lista entera?» y esto contesta
 *  «¿que he decidido, y cuanto me cuesta asi?». Son dos preguntas distintas y las
 *  dos se enseñan juntas a proposito: una lista de la compra se decide mirando
 *  cuanto se paga por haberla decidido.
 */
export async function reparto(listaId: string, cadenas?: string[]): Promise<RepartoTiendas> {
  return await pide<RepartoTiendas>(`/listas/${encodeURIComponent(listaId)}/reparto`, {
    cadenas: cadenas?.length ? cadenas.join(',') : undefined,
  })
}

/** Poner (o quitar) la tienda de una linea, de varias o de toda la lista.
 *
 *  - `{cadena: 'dia', lineas: ['id']}` esas lineas se compran en DIA
 *  - `{cadena: 'dia'}` **toda** la lista se compra en DIA
 *  - `{cadena: null, lineas: [...]}` esas lineas vuelven a «sin decidir»
 *  - `{cadena: 'dia', borrar: true}` se borra la sublista de DIA del tiron
 */
export async function ponerTienda(listaId: string,
                                  cuerpo: { cadena: string | null; lineas?: string[]
                                            borrar?: boolean }): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}/tienda`, 'POST', cuerpo)
}

/** Pasar favoritos a una lista, de uno en uno o todos de golpe. */
export async function anadirDesdeFavoritos(listaId: string,
                                           cuerpo: { grupo_ids?: number[]
                                                     producto_ids?: string[] }): Promise<number> {
  const r = await escribe<{ anadidos: number }>(
    `/listas/${encodeURIComponent(listaId)}/desde-favoritos`, 'POST', cuerpo)
  return r.anadidos
}

/** Ponerle nombre a una lista: con varias, «Lista» y «Lista (2)» no se distinguen. */
export async function renombrarLista(listaId: string, nombre: string): Promise<{ nombre: string }> {
  return await escribe(`/listas/${encodeURIComponent(listaId)}`, 'PATCH', { nombre })
}

/** Borrar la lista entera. Se **archiva**: desaparece y se puede recuperar. */
export async function borrarLista(listaId: string): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}`, 'DELETE')
}

export interface CierreDeCompra {
  /** Cuantas lineas salieron de la lista (las que iban en el carro). */
  lineas: number
  /** De esas, cuantas se quedaron sin precio: van en la compra y **no** en el total. */
  sin_precio: number
  total_cent: number
  /** Cuantas siguen en la lista, que son las que no se cogieron. */
  quedan: number
}

/** «He terminado la compra»: lo del carro se guarda como compra y sale de la lista.
 *
 *  La API contesta 409 si no hay nada en el carro: pulsar el boton sin haber tachado nada
 *  no puede inventar una compra vacia, y el texto del error se pinta tal cual. */
export async function cerrarCompra(listaId: string): Promise<CierreDeCompra> {
  return await escribe<CierreDeCompra>(
    `/listas/${encodeURIComponent(listaId)}/cerrar`, 'POST')
}

/* ---------------------------------------------------------------- escribir -- */

/** Escribe en la API y devuelve el JSON. `pide()` es solo GET.
 *
 *  Esto ya existe dentro de `api/favoritos.ts` (`conCuerpo`). No se sube a
 *  `cliente.ts` en este encargo porque alli vive la funcion que usan todas las
 *  pantallas, y mover eso por dos llamadas es un cambio que hay que revisar en
 *  sitios que no tienen nada que ver con la cesta.
 *
 *  `DELETE` entra aqui en lugar de tener su propio ayudante: la unica llamada
 *  que lo usa -- anular los enlaces de una lista -- necesita exactamente lo
 *  mismo que las demas (la cookie, la misma puerta y el `detail` de la API
 *  subido tal cual). Copiar estas lineas para una sola llamada seria dos sitios
 *  donde arreglar el mismo fallo. El cuerpo es **opcional** por lo mismo:
 *  `DELETE /listas/{id}/invitacion` y `POST /invitacion/{codigo}` no llevan
 *  nada, y mandarles un `{}` seria decir que la peticion trae datos que nadie
 *  lee; sin cuerpo tampoco se pone `Content-Type`, que es lo mismo dicho al
 *  reves.
 */
export async function escribe<T>(ruta: string, metodo: 'POST' | 'PATCH' | 'DELETE',
                                 cuerpo?: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: cuerpo === undefined
      ? { Accept: 'application/json' }
      : { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })
  let dato: unknown = null
  let detalle: string | null = null
  try {
    const json = await respuesta.json()
    dato = json
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON: el detalle se queda
    // en null y el codigo de estado ya cuenta lo que hay que contar.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  return dato as T
}

/** Un id de linea. Lo genera el cliente, no el servidor, y no es un capricho:
 *  la API hace `ON CONFLICT (id) DO UPDATE`, asi que el reintento actualiza la
 *  linea en vez de duplicarla. Sin eso, el pasillo con mala cobertura acaba con
 *  la leche tres veces en la lista.
 *
 *  `crypto.randomUUID` solo existe en **contexto seguro** (https o localhost), y
 *  esta aplicacion se sirve por http en el 8080, tambien por la IP de Tailscale:
 *  ahi no esta definido. El respaldo usa `getRandomValues`, que si existe en
 *  http, y saca los mismos 16 bytes con la version y la variante de un uuid v4.
 */
function idDeLinea(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const b = crypto.getRandomValues(new Uint8Array(16))
  b[6] = (b[6] & 0x0f) | 0x40
  b[8] = (b[8] & 0x3f) | 0x80
  const hex = [...b].map((x) => x.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** El cuerpo de `POST /listas/{id}/lineas`. Los nombres son los de la API. */
export interface NuevaLinea {
  nombre: string
  grupo_id: number | null
  producto_id: string | null
  cantidad?: number
  nota?: string | null
}

/** Anade una linea a la lista.
 *
 *  `id` se puede pasar para **resucitar** una linea que se acaba de quitar, y ese
 *  es el motivo de que sea un parametro: la API hace `ON CONFLICT (id) DO UPDATE`
 *  con `borrado_en = NULL` (`almacen.py:288`), asi que volver a anadir con **el
 *  mismo id** deshace el borrado en vez de crear otra linea. Es lo que hace
 *  posible un «Deshacer» de verdad y no un boton que duplica la compra.
 */
export async function anadirLinea(listaId: string, linea: NuevaLinea,
                                  id: string = idDeLinea()): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}/lineas`, 'POST', {
    id,
    // Cantidad 1 y sin nota es lo que hace la interfaz vieja (`anade`, app.js:614):
    // desde la ficha se dice QUE se compra, no cuanto. El cuanto se cambia en la
    // cesta, que es donde se ve la lista entera.
    cantidad: 1,
    nota: null,
    ...linea,
  })
}

/** El cuerpo de `PATCH /listas/{id}/lineas/{linea_id}`. Todo es opcional. */
export interface CambioLinea {
  tachado?: boolean
  en_carrito?: boolean
  /** 1..99: fuera de ahi la API contesta 422. */
  cantidad?: number
  nota?: string | null
  borrado?: boolean
  momento?: string
}

/** Cambia una linea: tacharla, cambiar la cantidad o borrarla. */
export async function cambiarLinea(listaId: string, lineaId: string,
                                   cambio: CambioLinea): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}/lineas/${encodeURIComponent(lineaId)}`,
    'PATCH', {
      // La hora del movil, no la de llegada: tachar sin cobertura a las 18:04 y
      // subirlo a las 18:20 tiene que contar como las 18:04, o el servidor se
      // inventa el orden de los hechos. Se manda en todos los cambios porque la
      // API solo la usa para decidir quien gano al tachar, y ahi hace falta.
      momento: new Date().toISOString(),
      ...cambio,
    })
}

/* ------------------------------------------------- lo que no llego a subir -- */

/** Un cambio guardado en el movil, tal cual lo espera `/sincronizar`.
 *
 *  La API lo lee asi (`main.py::sincronizar`): sin `tipo` es un cambio de una linea
 *  existente -- `id`, la hora y los campos que cambian --, y con `tipo: "anadir"` es una
 *  linea nueva. Aqui solo se usan los de la primera clase: anadir desde la ficha necesita
 *  el catalogo, y la ficha sin red no tiene nada que ensenar.
 */
export interface CambioDeCola {
  id: string
  momento: string
  tachado?: boolean
  en_carrito?: boolean
  cantidad?: number
  nota?: string | null
  borrado?: boolean
}

/** Sube de golpe lo que se hizo sin cobertura.
 *
 *  **Es lo que hace que tachar sin red no sea un error**: el cambio se guarda en el
 *  movil con su hora, y al volver la cobertura se sube entero. La API contesta cuantos
 *  aplico y cuales fallaron -- un cambio puede referirse a una linea que la otra persona
 *  ya borro --, y no se para por uno malo.
 */
export async function sincronizar(listaId: string, cambios: CambioDeCola[]):
    Promise<{ aplicados: number; fallidos: { id: string; motivo: string }[] }> {
  return await escribe(`/listas/${encodeURIComponent(listaId)}/sincronizar`, 'POST',
                       cambios)
}

/* ------------------------------------------------- invitaciones y gente -- */

/** Un enlace de invitacion recien creado. `ruta` es relativa a proposito
 *  (`/unirme/<codigo>`): el origen lo pone el navegador al construir el enlace
 *  que se manda, y asi el mismo codigo vale igual por `localhost` que por la IP
 *  de Tailscale, que es como se abre esto de verdad. */
export interface Invitacion {
  codigo: string
  papel: string
  expira_en: string
  ruta: string
}

/** Crea un enlace para mandar por WhatsApp. Solo quien creo la lista (403).
 *
 *  Tres usos y siete dias, que es lo que pedia la interfaz vieja (`app.js:1376`)
 *  y lo que dice su frase: "caduca en 7 dias y sirve para 3 personas". Un enlace
 *  de un solo uso se queda muerto al reenviarlo a la segunda persona, y uno sin
 *  caducar acaba en un grupo que no era (`almacen.py:455`). Con tres enlaces
 *  vivos a la vez, la API contesta 409 y su frase se enseña tal cual.
 */
export async function crearInvitacion(listaId: string, papel = 'escribe',
                                      usos = 3, dias = 7): Promise<Invitacion> {
  return await escribe<Invitacion>(`/listas/${encodeURIComponent(listaId)}/invitacion`,
    'POST', { papel, usos, dias })
}

/** Anula los enlaces vivos de esa lista y devuelve cuantos eran. */
export async function revocarInvitaciones(listaId: string): Promise<number> {
  const r = await escribe<{ revocadas: number }>(
    `/listas/${encodeURIComponent(listaId)}/invitacion`, 'DELETE')
  return r?.revocadas ?? 0
}

/** Lo que contesta la API cuando el enlace valia. */
export interface InvitacionAceptada {
  lista_id: string
  nombre: string
  papel: string
  /** Ya estabas dentro: el enlace no ha gastado un uso. */
  ya_estabas: boolean
}

/** Aplica el enlace. **Necesita sesion**: sin ella la API contesta 401.
 *
 *  Ese 401 es la razon de que la pantalla `/unirme/:codigo` ensene la puerta de
 *  entrada en vez de llamar aqui: quien llega por un enlace casi nunca tiene
 *  cuenta, y un error no es una forma de pedirle que se registre.
 */
export async function aceptarInvitacion(codigo: string): Promise<InvitacionAceptada> {
  return await escribe<InvitacionAceptada>(
    `/invitacion/${encodeURIComponent(codigo)}`, 'POST')
}

/** Mete en la lista a alguien que **ya tiene cuenta**, por su usuario.
 *
 *  El usuario se manda en minusculas y sin espacios porque es como lo guarda la
 *  API (`almacen.py:250`): mandarlo tal cual se escribio convertiria un
 *  "Marta " en un 404 que parece un error de la otra persona.
 *
 *  Devuelve el nombre de verdad y no lo que se tecleo: es lo que confirma que
 *  la persona que ha entrado es la que se queria, y no otra con un usuario
 *  parecido.
 */
export async function compartirCon(listaId: string, usuario: string,
                                   papel = 'escribe'): Promise<Compartido> {
  return await escribe<Compartido>(`/listas/${encodeURIComponent(listaId)}/compartir`,
    'POST', {
      usuario: usuario.trim().toLowerCase(),
      papel,
    })
}

/** Quien acaba de entrar en la lista.
 *
 *  `papel` es **el que quedo en la base**, no el que se pidio: si le das a alguien que ya es el
 *  dueno, la API contesta `dueno` y no cambia nada (ver `almacen.comparte`), y la pantalla lo
 *  dice con otras palabras en vez de «Ya está dentro».
 */
export interface Compartido {
  usuario: string
  nombre: string | null
  papel: string
}
