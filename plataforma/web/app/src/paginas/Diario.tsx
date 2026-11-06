/** El diario del dia: lo que se comio, lo que se sabe y lo que falta por saber.
 *
 *  **Las dos cifras van juntas.** "Conocido: 1.250 kcal" sin decir cuantas entradas no traen dato es un
 *  numero que parece medido y no lo esta. Aqui se enseña el subtotal **y** cuantas faltan, y mientras
 *  falte alguna se dice en una linea entera, no en letra pequeña.
 *
 *  Y por eso el alta obliga a declarar **de donde sale el dato**: etiqueta, ficha, estimacion o
 *  desconocido. Es la unica manera de que el subtotal signifique algo.
 */
import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { anotarDeLaCompra, guardaPreferencia, misListas, previaDeLaCompra, yo } from '../api/cesta'
import type { PreviaDeLaCompra, ReciboDeLaCompra } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { numero } from '../api/formato'
import { useApuntar, useBorrarEntrada, useDia } from '../api/diario'
import { resolver, type Pendiente } from '../logica/operacionPendiente'
import type { Dia, Entrada, NuevaEntrada } from '../api/diario'
import { Boton, Cargando, Tarjeta, Vacio, Fallo, Etiqueta } from '../componentes/ui'
import { EntraParaVer } from '../componentes/PuertaDeSesion'

const NOMBRE_NUTRIENTE: Record<string, string> = {
  kcal: 'energía',
  proteinas_g: 'proteínas',
  grasas_g: 'grasas',
  hidratos_g: 'hidratos',
}


const COMIDAS = ['desayuno', 'media manana', 'comida', 'merienda', 'cena', 'otras']
const FUENTES = ['etiqueta', 'ficha', 'estimado', 'desconocido']

/** **Las comidas, como se leen.** *La clave es la del servidor; el nombre, el de la mesa.* */
const NOMBRE_COMIDA: Record<string, string> = {
  desayuno: 'Desayuno',
  'media manana': 'Media mañana',
  comida: 'Comida',
  merienda: 'Merienda',
  cena: 'Cena',
  otras: 'Otras',
}

/** **De dónde sale un dato, dicho sin jerga.** *La clave viaja a la API; la etiqueta se lee.* */
const NOMBRE_FUENTE: Record<string, string> = {
  etiqueta: 'Etiqueta',
  ficha: 'Ficha del producto',
  estimado: 'Estimación',
  desconocido: 'No lo sé',
}

/** Un campo de texto a numero, o **`null` si esta vacio**. Dos cosas que importan:
 *
 *  - **Vacío es `null`, no `0`**: un cero es la afirmación «no lleva proteína», y no la tenemos.
 *  - **La coma decimal se acepta**, que es como se escribe en la cocina: `7,5` es `7.5`.
 *
 *  Y `Number('')` es `0` y `Number('abc')` es `NaN`: los dos se convierten en `null` por caminos
 *  distintos si no se mira. Aqui se mira.
 */
function aNumero(texto: string): number | null {
  const limpio = texto.trim().replace(',', '.')
  if (limpio === '') return null
  const valor = Number(limpio)
  return Number.isFinite(valor) ? valor : null
}

function hoy(): string {
  const ahora = new Date()
  // Fecha local, no UTC: a las once de la noche el dia que se anota es el de casa.
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

/** **Lo que ya has comprado, al diario.** Hasta hoy el diario solo se podia llenar escribiendo a mano,
 *  y la compra que ya esta hecha no decia nada.
 *
 *  **La compra propone y la persona confirma**: la previa ense?a que se anotaria, **y aparte lo que no
 *  trae nutricion, con su nombre** -- *anotar las que se puede y callar las demas convertiria un dato
 *  que falta en una comida que parece completa*. Y **la cobertura** dice cuantas de cuantas.
 */
function DeLaCompra({ fecha }: { fecha: string }) {
  const cliente = useQueryClient()
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas })
  // **Solo la lista de casa, y sin elegir otra en silencio.** Antes esto era
  // `find(es_de_casa)?.id ?? listas.data?.[0]?.id`: si no habia lista de casa, anotaba en la primera
  // que hubiera, que puede ser la de otra persona del hogar o una lista de ideas. El documento lo
  // pide explicito: *no confundir esa eleccion con una decision del usuario*.
  // *** LA LISTA SE ELIGE, *y solo si hace falta*. ***
  // *Antes solo habia la de casa; si no habia, la pantalla decia «no tienes ninguna lista»
  // **aunque tuvieras tres sin casa**.* *M03 pide poder elegir una lista **autorizada**, y que
  // «sin casa» se diga como lo que es.*
  //
  // *Sin elegir, manda la de casa: el comportamiento de siempre no cambia.* *Y la eleccion es
  // de esta pantalla y de esta sesion: no se escribe una preferencia que luego decida por la
  // persona en otro sitio.*
  const [elegida, setElegida] = useState<string | null>(null)
  // *** LA ELECCION SE RECUERDA POR PERSONA, *no por navegador*. ***
  // *`/api/yo` devuelve `preferencias`, y las guarda el servidor por `usuario_id`.* *Asi que dos
  // personas en el mismo aparato no se pisan: lo que elige A no cambia lo que ve B.*
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const guardada = sesion.data?.preferencias?.lista_del_diario
  useEffect(() => {
    // *Solo se adopta lo guardado si la persona no ha elegido ya en esta pantalla.* *Al reves
    // se le pisaria la eleccion cada vez que `yo()` se refresque.*
    if (elegida === null && typeof guardada === 'string' && guardada) setElegida(guardada)
  }, [guardada, elegida])
  const casa = listas.data?.find((l) => l.es_de_casa) ?? null
  const listaId = elegida ?? casa?.id ?? null
  const [comida, setComida] = useState('comida')
  const [previa, setPrevia] = useState<PreviaDeLaCompra | null>(null)
  // **El recibo, no el numero de la previa.** `anotadas` era `previa?.anotarian.length`, es decir
  // lo que la previa DECIA que se anotaria: si alguna linea ya estaba o dejo de estar, el mensaje
  // mentia sobre lo que se habia guardado.
  const [recibo, setRecibo] = useState<ReciboDeLaCompra | null>(null)

  const ver = useMutation({
    mutationFn: () => previaDeLaCompra(listaId as string),
    onSuccess: (p) => { setPrevia(p); setRecibo(null) },
  })
  const anotar = useMutation({
    mutationFn: () => anotarDeLaCompra(listaId as string, fecha, comida),
    onSuccess: (r) => {
      // El dia **y los rangos**: las tendencias usan `['diario-rango', ...]`, que es otra clave.
      void cliente.invalidateQueries({ queryKey: ['diario'] })
      void cliente.invalidateQueries({ queryKey: ['diario-rango'] })
      setRecibo(r)
      setPrevia(null)
    },
  })

  // **No se esconde mientras carga.** Antes esto era `if (listaId === null) return null`, y la
  // tarjeta desaparecia entera hasta que llegara `['listas']`: desde fuera se ve igual que no
  // existir, y el recorrido del navegador se cayo esperandola veinte segundos. Medido el 13 de
  // octubre de 2026: la tarjeta SI se pinta -- con su boton y sin un solo error -- en cuanto la
  // consulta llega. Lo que no se puede hacer todavia se dice, como en el resto de la aplicacion.
  const sinLista = listaId === null
  return (
    <Tarjeta>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[16px] text-tinta-fuerte">De la compra al diario</span>
        <Boton onClick={() => listaId && ver.mutate()} disabled={sinLista || ver.isPending}>
          Ver que se puede anotar
        </Boton>
      </div>

      {/* *** TRES ESTADOS, *y no dos*. *** *Antes «cargando» y «no hay listas» se decian
          igual, y «no hay listas» se decia tambien cuando habia tres pero ninguna de casa.*
          *M03 pide separarlos: carga, ausencia y **sin casa pero con otras**.* */}
      {sinLista && listas.isPending && (
        <p className="mt-2 text-[15px] text-secundaria">Mirando tus listas…</p>
      )}

      {sinLista && !listas.isPending && (listas.data?.length ?? 0) === 0 && (
        <p className="mt-2 text-[15px] text-secundaria">
          Todavia no tienes ninguna lista. Crea una en Compra y aqui podras anotar lo que compres.
        </p>
      )}

      {/* *** CON LISTAS PERO SIN CASA: se dice, y se deja elegir. *** *Decir «no tienes ninguna
          lista» cuando tiene tres de casa ajena es falso; y dejarla sin salida es peor.* */}
      {sinLista && !listas.isPending && (listas.data?.length ?? 0) > 0 && (
        <div className="mt-2 flex flex-col gap-2">
          <p className="text-[15px] text-secundaria">
            No tienes una lista marcada como de casa. Elige con cual quieres anotar: la eleccion
            es tuya, y no cambia lo que hayan anotado los demas.
          </p>
          <label className="flex flex-wrap items-center gap-2 text-etiqueta text-tinta-suave">
            <span className="text-tinta">Lista</span>
            <select
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
              defaultValue=""
              onChange={(e) => {
                const id = e.target.value || null
                setElegida(id)
                // *** Y SE GUARDA, *por persona*. ***
                // *El servidor la guarda por `usuario_id` (`PUT /api/preferencias`), asi que lo
                // que elige A no lo ve B en el mismo aparato.*
                // *Si el guardado falla, la eleccion **sigue valiendo para esta pantalla**: no se
                // deshace lo que la persona acaba de elegir por un fallo de red. La proxima vez
                // que entre no la encontrara, y eso es lo peor que pasa.*
                if (id) void guardaPreferencia('lista_del_diario', id).catch(() => {})
              }}
            >
              <option value="">Elige una lista</option>
              {(listas.data ?? []).map((l) => (
                <option key={l.id} value={l.id}>
                  {l.nombre}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {/* *** SI LA PREVIA NO SE PUEDE DAR, SE DICE POR QUE. ***
          *`ver` tenia `onSuccess` y **ningun sitio donde enseñar el fallo**: si
          `previaDeLaCompra` devolvia un error -- por ejemplo **porque la compra no esta cerrada
          todavia** --, el boton no hacia nada y la pantalla se quedaba igual.* *Desde fuera, eso
          se lee como «la aplicacion no responde», que es peor que un mensaje.*
          *M03 lo pide con estas palabras: «una compra sin cerrar explica por que no propone
          contenido, no bloquea toda la app».* */}
      {ver.isError && (
        <p className="mt-2 text-[15px] text-secundaria">
          {ver.error instanceof Error && ver.error.message
            ? ver.error.message
            : 'No he podido mirar la compra. Vuelve a intentarlo en un momento.'}
        </p>
      )}

      {recibo && (
        <div className="mt-2 flex flex-col gap-1 text-[15px]">
          <p className="text-tinta-fuerte">
            {recibo.anotadas === 1 ? 'Se ha anotado 1.' : `Se han anotado ${recibo.anotadas}.`}
          </p>
          {/* **Lo que no entro tambien se dice**, y con su nombre: callarlo convertiria un dato que
              falta en una comida que parece completa. */}
          {recibo.ya_estaban.length > 0 && (
            <p className="text-secundaria">
              Ya estaban en el diario, asi que no se repiten: {recibo.ya_estaban.join(', ')}.
            </p>
          )}
          {recibo.sin_nutricion.length > 0 && (
            <p className="text-secundaria">
              Anotadas sin dato de nutricion: {recibo.sin_nutricion.join(', ')}.
            </p>
          )}
          {recibo.ajenas.length > 0 && (
            <p className="text-secundaria">
              No son de esa compra, asi que no se han tocado: {recibo.ajenas.join(', ')}.
            </p>
          )}
        </div>
      )}

      {previa && (
        <div className="mt-2 flex flex-col gap-2">
          {previa.compra_id === null ? (
            <p className="text-[15px] text-secundaria">
              Esta lista todavia no tiene ninguna compra cerrada, asi que no hay nada que anotar.
            </p>
          ) : (
            <>
              <p className="text-[15px] text-tinta-fuerte">
                {previa.cobertura.total === 0
                  ? 'No hay nada que anotar.'
                  : `Se anotarian ${previa.anotarian.length} de ${previa.cobertura.total}:`}
              </p>
              <ul className="flex min-h-full flex-col gap-1">
                {previa.anotarian.map((x) => (
                  <li key={x.linea_id} className="text-[15px] text-tinta-fuerte">
                    {x.nombre}
                    {x.kcal !== null && (
                      <span className="text-etiqueta text-tinta-suave tabular-nums"> {x.kcal} kcal</span>
                    )}
                  </li>
                ))}
              </ul>
              {previa.sin_dato.length > 0 && (
                <p className="text-[14px] text-secundaria">
                  {previa.sin_dato.length === 1
                    ? 'Uno no trae nutrición en el catálogo, así que se anotaría como «sin dato»: '
                    : `${previa.sin_dato.length} no traen nutrición en el catálogo, así que se anotarían como «sin dato»: `}
                  {previa.sin_dato.join(', ')}.
                </p>
              )}
              {previa.anotarian.length > 0 && (
                <>
                  <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
                    Comida
                    <select
                      value={comida}
                      onChange={(e) => setComida(e.target.value)}
                      className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
                    >
                      {COMIDAS.map((c) => (
                        <option key={c} value={c}>{NOMBRE_COMIDA[c] ?? c}</option>
                      ))}
                    </select>
                  </label>
                  <Boton onClick={() => anotar.mutate()} disabled={anotar.isPending}>
                    Sí, anotarlo
                  </Boton>
                </>
              )}
            </>
          )}
          {(ver.error || anotar.error) && (
            <Etiqueta tono="mal">{textoDeError(ver.error ?? anotar.error)}</Etiqueta>
          )}
        </div>
      )}
    </Tarjeta>
  )
}

function Alta({ fecha }: { fecha: string }) {
  const [comida, setComida] = useState('comida')
  const [texto, setTexto] = useState('')
  const [kcal, setKcal] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [proteinas, setProteinas] = useState('')
  const [grasas, setGrasas] = useState('')
  const [hidratos, setHidratos] = useState('')
  const [fuente, setFuente] = useState('etiqueta')
  const [esReceta, setEsReceta] = useState(false)
  const [version, setVersion] = useState('1')
  const apuntar = useApuntar()
  // **La operación que se está intentando, y su payload.** *Vive en un `ref` y no en un `estado`
  // porque no se pinta: sólo tiene que sobrevivir al repintado y al reintento.*
  const pendiente = useRef<Pendiente<NuevaEntrada> | null>(null)

  return (
    <section
      id="alta"
      aria-labelledby="alta-titulo"
      className="rounded-tarjeta border border-borde bg-papel p-4 shadow-apoyado"
    >
      <h2 id="alta-titulo" className="text-cuerpo-fuerte text-tinta">Añadir</h2>
      <p className="mt-1 text-etiqueta text-tinta-suave">
        Apunta lo que has comido, no los valores de 100 g. Deja en blanco lo que no sepas:{' '}
        <strong className="text-tinta">en blanco no es cero</strong>.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          // **El payload SIN la clave.** *La clave la decide `resolver`, que es lo único que sabe si
          // esto es un reintento — y por eso el sello no puede incluirla: si la llevara, comparar lo
          // pendiente con lo nuevo daría siempre distinto.*
          const campos: NuevaEntrada = {
            fecha, comida,
            tipo: esReceta ? 'receta' : 'alimento',
            referencia: esReceta ? texto.trim() || null : texto.trim() || null,
            version: esReceta ? version : null,
            // **Los valores son los de lo que se ha comido, no los de 100 g.** La pantalla lo
            // dice antes de los campos, para que nadie multiplique dos veces. Quien tenga los
            // valores por 100 g usa la ficha del producto, que hace la cuenta en el servidor
            // (`/api/diario/desde-ficha`).
            cantidad_g: aNumero(cantidad),
            kcal: aNumero(kcal),
            proteinas_g: aNumero(proteinas),
            grasas_g: aNumero(grasas),
            hidratos_g: aNumero(hidratos),
            fuente_dato: fuente, nota: '',
          }
          // **Misma operación, misma clave.** Si esto es reintentar lo de antes —porque la respuesta
          // se perdió— lleva **la clave de antes** y el servidor devuelve la entrada que ya creó en
          // vez de crear otra. Si cambió algo del formulario, es otra operación y lleva clave nueva:
          // *cambiar lo escrito es cancelar lo anterior, y no hace falta un botón para eso.*
          //
          // **Antes esto era `clave_operacion: crypto.randomUUID()` aquí dentro**, así que cada
          // pulsación —incluido el reintento— era una operación nueva y el servidor duplicaba. *La
          // clave existía, el índice único existía y el servidor deduplicaba; el cliente nunca
          // reenviaba la misma, así que no servía de nada.* Y de paso: `crypto.randomUUID` no existe
          // en contexto no seguro —por la IP de Tailscale, en http— y ahora lo resuelve el módulo.
          pendiente.current = resolver(pendiente.current, campos)
          apuntar.mutate({ ...campos, clave_operacion: pendiente.current.clave }, {
            onSuccess: () => {
              // **Se olvida la operación al confirmarla**, para que dos meriendas iguales de verdad
              // sigan siendo dos. Y se limpia sólo lo que se ha guardado: si el alta falla, el error
              // se ve y no se borra lo escrito — *volver a teclear una comida entera por un 500 es
              // lo que hace que alguien deje de usar esto.*
              pendiente.current = null
              setTexto('')
              setKcal('')
              setCantidad('')
              setProteinas('')
              setGrasas('')
              setHidratos('')
            },
          })
        }}
        className="flex flex-col gap-3"
      >
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Comida
            <select
              value={comida}
              onChange={(e) => setComida(e.target.value)}
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
            >
              {COMIDAS.map((c) => (
                <option key={c} value={c}>{NOMBRE_COMIDA[c] ?? c}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            {esReceta ? 'Receta (nombre o número)' : 'Qué has comido'}
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Energía (kcal)
            <input
              value={kcal}
              onChange={(e) => setKcal(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-28 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Cantidad (g)
            <input
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
              inputMode="decimal"
              placeholder="150"
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Proteínas (g)
            <input
              value={proteinas}
              onChange={(e) => setProteinas(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Grasas (g)
            <input
              value={grasas}
              onChange={(e) => setGrasas(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            Hidratos (g)
            <input
              value={hidratos}
              onChange={(e) => setHidratos(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
            De dónde sale el dato
            <select
              value={fuente}
              onChange={(e) => setFuente(e.target.value)}
              className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta"
            >
              {FUENTES.map((f) => (
                <option key={f} value={f}>{NOMBRE_FUENTE[f] ?? f}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-h-[44px] min-w-[44px] items-center gap-2 text-[14px] text-tinta-fuerte">
            <input type="checkbox" checked={esReceta} onChange={(e) => setEsReceta(e.target.checked)} />
            Es una receta
          </label>
          {esReceta && (
            <label className="flex items-center gap-2 text-etiqueta text-tinta-suave">
              Versión
              <input
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="min-h-[44px] w-20 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
              />
            </label>
          )}
          <Boton type="submit" disabled={apuntar.isPending}>
            {apuntar.isPending ? 'Anotando...' : 'Anotar'}
          </Boton>
        </div>
        {apuntar.error && <Etiqueta tono="mal">{textoDeError(apuntar.error)}</Etiqueta>}
      </form>
    </section>
  )
}

export function Diario() {
  // **La puerta.** *El diario es de cada uno: `/api/diario/{fecha}` contesta 401 sin sesión, y
  // antes eso se enseñaba como «La API ha contestado 401». Todo lo que pide datos —el día, la
  // compra— vive en el componente de dentro, así que sin sesión no se lanza ni una petición.*
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  if (sesion.isLoading) return <Cargando que="tu diario" />
  if (!sesion.data?.usuario) {
    return <EntraParaVer texto="El diario se guarda con tu cuenta." />
  }
  return <DiarioDelDia />
}

/** La fecha de la cabecera, en castellano y en local. Se lee, no se depura. */
const DIA_LARGO = new Intl.DateTimeFormat('es-ES', {
  weekday: 'long',
  day: 'numeric',
  month: 'short',
})

/** «jueves, 5 nov» para el día que se está mirando. */
export function diaDeLaCabecera(iso: string): string {
  const fecha = new Date(`${iso}T00:00:00`)
  return Number.isNaN(fecha.getTime()) ? iso : DIA_LARGO.format(fecha)
}

/** **Las kcal, con el separador de miles del artboard y la coma decimal de aquí.**
 *
 *  *El formateador de la casa (`numero`) deja «2200»: en castellano la agrupacion empieza a
 *  partir de cinco cifras. El artboard aprobado escribe «2.200», y una cifra de cuatro digitos
 *  sin separador se lee peor al lado de la barra. Se agrupa **siempre**, con `Intl`, que sigue
 *  decidiendo la coma decimal.*
 */
const CIFRA = new Intl.NumberFormat('es-ES', {
  maximumFractionDigits: 1,
  minimumFractionDigits: 0,
  useGrouping: true,
})

function cifra(n: number): string {
  return CIFRA.format(n)
}

/** **El objetivo de ESE día, si alguien lo puso.**
 *
 *  La preferencia es `objetivo:<fecha>` y su valor es `{kcal}`: la misma que leen las tendencias.
 *  **Un día sin objetivo no es un día de cero.** Devuelve `null`, y la pantalla no inventa una
 *  cifra que nadie ha declarado.
 */
export function objetivoDe(
  preferencias: Record<string, unknown> | null | undefined,
  fecha: string,
): number | null {
  const guardado = preferencias?.[`objetivo:${fecha}`]
  const valor = guardado && typeof guardado === 'object' && 'kcal' in guardado
    ? (guardado as { kcal: unknown }).kcal
    : guardado
  return typeof valor === 'number' && Number.isFinite(valor) && valor > 0 ? valor : null
}

function CabeceraDelDia({ fecha, objetivo }: { fecha: string; objetivo: number | null }) {
  return (
    <header className="flex items-center gap-2">
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
        <p className="text-micro uppercase text-tinta-tenue">{diaDeLaCabecera(fecha)}</p>
        <h2 className="mt-0.5 font-display text-titulo font-semibold text-tinta">Calorías</h2>
      </div>
      {objetivo !== null && (
        <span className="inline-flex min-h-[32px] shrink-0 items-center rounded-pastilla bg-lavado-verde px-2.5 text-etiqueta-fuerte text-verde-fuerte">
          {cifra(objetivo)} kcal
        </span>
      )}
    </header>
  )
}

/** *** La tarjeta HOY: lo consumido, el objetivo y lo que queda. *** *
 *
 *  **Sin objetivo no hay barra ni «te quedan 1.125»**: los dos serian una cifra inventada. Se dice
 *  «Sin objetivo» y se deja ponerlo. Y **sin dato de energia no hay cero**: la cifra grande dice
 *  «sin dato», que es lo mismo que dice cada alimento que no lo trae.
 */
function TarjetaDeHoy({
  data,
  objetivo,
  onGuardarObjetivo,
  guardandoObjetivo,
  errorObjetivo,
}: {
  data: Dia
  objetivo: number | null
  onGuardarObjetivo: (kcal: number | null) => void
  guardandoObjetivo: boolean
  errorObjetivo: string | null
}) {
  const consumido = data.conocido.kcal
  const conDato = data.conocido.entradas
  const total = data.entradas.length
  const faltan = data.sin_dato.length
  const restante = objetivo !== null && consumido !== null
    ? Math.round((objetivo - consumido) * 10) / 10
    : null
  const proporcion = objetivo !== null && consumido !== null && objetivo > 0
    ? Math.round(Math.min(100, Math.max(0, (consumido / objetivo) * 100)) * 10) / 10
    : null

  return (
    <section aria-labelledby="hoy" className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
      <h2 id="hoy" className="text-micro uppercase text-tinta-tenue">Hoy</h2>

      <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="cifra text-portada font-semibold text-tinta">
          {consumido === null ? 'sin dato' : cifra(consumido)}
        </span>
        {objetivo !== null ? (
          <span className="text-cuerpo text-tinta-suave">de {cifra(objetivo)} kcal</span>
        ) : consumido !== null ? (
          <span className="text-cuerpo text-tinta-suave">kcal</span>
        ) : null}
      </div>

      {/* **De cuantas entradas sale la cifra.** *Un subtotal sin decir sobre cuantas entradas
          esta hecho se lee como el dia entero, y no lo es.* */}
      {total > 0 && (
        <p className="mt-1 text-etiqueta text-tinta-suave">
          {conDato} de {total} {total === 1 ? 'entrada' : 'entradas'} con energía
        </p>
      )}

      {proporcion !== null && consumido !== null && objetivo !== null && (
        <>
          <div
            role="progressbar"
            aria-label="Consumido hoy"
            aria-valuemin={0}
            aria-valuemax={objetivo}
            aria-valuenow={Math.min(consumido, objetivo)}
            aria-valuetext={`${cifra(consumido)} de ${cifra(objetivo)} kcal`}
            className="mt-3 h-3 rounded-pastilla bg-lavado-verde"
          >
            <span
              className="block h-3 rounded-pastilla bg-verde"
              style={{ width: `${proporcion}%` }}
            />
          </div>
          {restante !== null && (
            <p className="mt-2 text-etiqueta text-tinta-suave">
              {restante > 0
                ? `Te quedan ${cifra(restante)} kcal`
                : restante === 0
                  ? 'Objetivo alcanzado'
                  : `${cifra(-restante)} kcal por encima del objetivo`}
            </p>
          )}
        </>
      )}

      {!data.completo && faltan > 0 && (
        <p className="mt-2 text-etiqueta leading-[1.125rem] text-aviso">
          Este día <strong>no está completo</strong>: falta el dato de {faltan}{' '}
          {faltan === 1 ? 'entrada' : 'entradas'}. Lo de arriba es lo que se sabe, no todo lo que
          comiste.
        </p>
      )}

      {/* **La cobertura, nutriente a nutriente.** El total de energia puede estar completo y faltar
          las proteinas: decir "3 de 4 entradas" es lo que impide leer el numero de arriba como si
          fuera el dia entero. Y un nutriente que no trae nadie se dice con la palabra, no con un 0. */}
      {data.cobertura && (
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {Object.entries(data.cobertura).map(([nutriente, c]) => (
            <li key={nutriente} className="text-etiqueta text-tinta-suave tabular-nums">
              {NOMBRE_NUTRIENTE[nutriente] ?? nutriente}:{' '}
              {c.con_dato === 0 ? (
                <span className="text-aviso">sin dato</span>
              ) : (
                <>
                  {c.con_dato} de {c.total}
                  {c.completa ? '' : ' entradas'}
                </>
              )}
            </li>
          ))}
        </ul>
      )}

      <ControlDeObjetivo
        key={data.fecha}
        objetivo={objetivo}
        onGuardar={onGuardarObjetivo}
        guardando={guardandoObjetivo}
      />

      {errorObjetivo && (
        <p role="alert" className="mt-1 text-etiqueta text-error">{errorObjetivo}</p>
      )}
    </section>
  )
}

/** El objetivo del día: se dice el que hay, y se deja poner, cambiar o quitar.
 *
 *  **No prescribe nada.** El texto es «Tu objetivo diario» y el número lo pone la persona; la app
 *  no propone una cantidad ni da consejos. Si no hay objetivo, se dice «Sin objetivo» en vez de
 *  inventar 2.200.
 */
function ControlDeObjetivo({
  objetivo,
  onGuardar,
  guardando,
}: {
  objetivo: number | null
  onGuardar: (kcal: number | null) => void
  guardando: boolean
}) {
  const [editando, setEditando] = useState(objetivo === null)
  const [texto, setTexto] = useState(objetivo === null ? '' : String(objetivo))
  const [error, setError] = useState<string | null>(null)

  if (!editando && objetivo !== null) {
    return (
      <button
        type="button"
        onClick={() => {
          setTexto(String(objetivo))
          setError(null)
          setEditando(true)
        }}
        className="mt-2 inline-flex min-h-[44px] items-center text-etiqueta text-tinta-suave underline underline-offset-2 hover:text-tinta"
      >
        Cambiar objetivo
      </button>
    )
  }

  return (
    <form
      className="mt-2 flex flex-col gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        const kcal = aNumero(texto)
        if (kcal === null || kcal <= 0) {
          setError('Escribe un número de kcal mayor que cero.')
          return
        }
        setError(null)
        onGuardar(kcal)
        setEditando(false)
      }}
    >
      {objetivo === null && <p className="text-etiqueta text-tinta-suave">Sin objetivo</p>}
      <div className="flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1 text-etiqueta text-tinta-suave">
          Tu objetivo diario
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            inputMode="numeric"
            className="min-h-[44px] w-28 rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
          />
        </label>
        <Boton type="submit" disabled={guardando}>
          {guardando ? 'Guardando…' : 'Guardar'}
        </Boton>
        {objetivo !== null && (
          <>
            <Boton
              variante="sutil"
              onClick={() => {
                setEditando(false)
                setError(null)
              }}
            >
              Cancelar
            </Boton>
            <Boton
              variante="sutil"
              onClick={() => {
                onGuardar(null)
                setTexto('')
                setError(null)
                setEditando(true)
              }}
            >
              Quitar
            </Boton>
          </>
        )}
      </div>
      {error && <p role="alert" className="text-etiqueta text-error">{error}</p>}
    </form>
  )
}

/** *** Una comida, con sus alimentos. *** *
 *
 *  Cada linea enseña **el nombre, la cantidad y las kcal reales de esa entrada**. Las kcal de la
 *  cabecera son el subtotal de las que traen dato; si alguna no lo trae, se dice aparte en vez de
 *  contarla como cero.
 */
function TarjetaComida({
  comida,
  entradas,
  onQuitar,
  quitandoId,
}: {
  comida: string
  entradas: Entrada[]
  onQuitar: (id: number) => void
  quitandoId: number | null
}) {
  const conDato = entradas.filter((e) => e.kcal !== null)
  const total = conDato.length
    ? Math.round(conDato.reduce((suma, e) => suma + (e.kcal ?? 0), 0) * 10) / 10
    : null
  const faltan = entradas.length - conDato.length

  return (
    <section className="rounded-tarjeta bg-papel p-4 shadow-apoyado">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-cuerpo-fuerte text-tinta">{NOMBRE_COMIDA[comida] ?? comida}</h3>
        <span className="cifra text-cuerpo text-tinta">
          {total === null ? 'sin dato' : `${cifra(total)} kcal`}
        </span>
      </div>

      <ul className="mt-1 flex flex-col">
        {entradas.map((e) => (
          <li
            key={e.id}
            className="flex min-h-[44px] items-center gap-2 border-b border-borde last:border-0"
          >
            <span className="min-w-0 flex-1 break-words py-2 text-cuerpo text-tinta-suave">
              <span>{e.referencia || 'sin nombre'}</span>
              {e.cantidad_g !== null && <> · {numero(e.cantidad_g)} g</>}
            </span>
            <span className="cifra shrink-0 text-etiqueta text-tinta-suave">
              {e.kcal === null ? 'sin dato' : `${cifra(e.kcal)} kcal`}
            </span>
            <button
              type="button"
              onClick={() => onQuitar(e.id)}
              disabled={quitandoId === e.id}
              aria-label={`Quitar ${e.referencia || 'esta entrada'}`}
              title="Quitar"
              className="inline-flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-pastilla text-tinta-tenue transition-colors duration-rapida ease-suave hover:bg-lavado-error hover:text-error disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                aria-hidden="true"
                focusable="false"
              >
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </li>
        ))}
      </ul>

      {faltan > 0 && (
        <p className="mt-1 text-etiqueta text-aviso">
          {faltan === 1
            ? 'Una entrada sin dato de energía.'
            : `${faltan} entradas sin dato de energía.`}
        </p>
      )}
    </section>
  )
}

function DiarioDelDia() {
  const [fecha, setFecha] = useState(hoy())
  const { data, isPending, error, refetch } = useDia(fecha)
  const borrar = useBorrarEntrada(fecha)
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const objetivo = objetivoDe(sesion.data?.preferencias, fecha)

  const guardaObjetivo = useMutation({
    mutationFn: (kcal: number | null) =>
      guardaPreferencia(`objetivo:${fecha}`, kcal === null ? null : { kcal }),
    onSuccess: () => {
      // La misma clave que leen la cabecera y las tendencias: se repinta con el objetivo nuevo.
      void cliente.invalidateQueries({ queryKey: ['yo'] })
    },
  })

  const total = data?.entradas.length ?? 0

  return (
    <div className="flex min-h-full flex-col gap-4">
      <CabeceraDelDia fecha={fecha} objetivo={objetivo} />

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-etiqueta text-tinta-suave">
          Día
          <input
            type="date"
            value={fecha}
            onChange={(e) => {
              // Un campo vacio no es un dia: no se pide el diario de la nada.
              if (e.target.value) setFecha(e.target.value)
            }}
            className="min-h-[44px] rounded-campo border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta tabular-nums"
          />
        </label>
        <button
          type="button"
          onClick={() => setFecha(hoy())}
          className="inline-flex min-h-[44px] min-w-[44px] items-center text-cuerpo text-verde underline underline-offset-2"
        >
          Hoy
        </button>
      </div>

      {isPending && <Cargando que="tu diario" filas={3} />}
      {error && (
        <Fallo
          error={error}
          reintentar={() => void refetch()}
          titulo="No he podido leer tu diario"
        />
      )}

      {data && (
        <>
          <TarjetaDeHoy
            data={data}
            objetivo={objetivo}
            onGuardarObjetivo={(kcal) => guardaObjetivo.mutate(kcal)}
            guardandoObjetivo={guardaObjetivo.isPending}
            errorObjetivo={guardaObjetivo.error ? textoDeError(guardaObjetivo.error) : null}
          />

          <section aria-labelledby="comidas" className="flex flex-col gap-2">
            <div className="flex items-baseline justify-between gap-2">
              <h2 id="comidas" className="text-cuerpo-fuerte text-tinta">
                Comidas
              </h2>
              <a
                href="#alta"
                className="inline-flex min-h-[44px] items-center text-cuerpo-fuerte font-semibold text-verde underline-offset-2 hover:underline"
              >
                Añadir
              </a>
            </div>

            {total === 0 ? (
              <Vacio titulo="Nada anotado este día">
                <p>Usa «Añadir» para apuntar lo primero; aparecerá aquí por comidas.</p>
              </Vacio>
            ) : (
              Object.entries(data.comidas).map(([comida, entradas]) => (
                <TarjetaComida
                  key={comida}
                  comida={comida}
                  entradas={entradas}
                  onQuitar={(id) => borrar.mutate(id)}
                  quitandoId={borrar.isPending ? borrar.variables ?? null : null}
                />
              ))
            )}
          </section>

          {borrar.error && <Etiqueta tono="mal">{textoDeError(borrar.error)}</Etiqueta>}
        </>
      )}

      <Alta fecha={fecha} />

      <DeLaCompra fecha={fecha} />

      <nav aria-label="Más de calorías" className="flex flex-wrap gap-x-4">
        <Link
          to="/calorias/tendencias"
          className="inline-flex min-h-[44px] items-center text-cuerpo text-verde underline underline-offset-2"
        >
          Tendencias
        </Link>
        <Link
          to="/calorias/alimentos"
          className="inline-flex min-h-[44px] items-center text-cuerpo text-verde underline underline-offset-2"
        >
          Mis alimentos
        </Link>
      </nav>
    </div>
  )
}
