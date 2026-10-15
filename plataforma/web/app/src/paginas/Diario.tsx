/** El diario del dia: lo que se comio, lo que se sabe y lo que falta por saber.
 *
 *  **Las dos cifras van juntas.** "Conocido: 1.250 kcal" sin decir cuantas entradas no traen dato es un
 *  numero que parece medido y no lo esta. Aqui se enseña el subtotal **y** cuantas faltan, y mientras
 *  falte alguna se dice en una linea entera, no en letra pequeña.
 *
 *  Y por eso el alta obliga a declarar **de donde sale el dato**: etiqueta, ficha, estimacion o
 *  desconocido. Es la unica manera de que el subtotal signifique algo.
 */
import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { anotarDeLaCompra, misListas, previaDeLaCompra } from '../api/cesta'
import type { PreviaDeLaCompra, ReciboDeLaCompra } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { useApuntar, useBorrarEntrada, useDia } from '../api/diario'
import { resolver, type Pendiente } from '../logica/operacionPendiente'
import type { NuevaEntrada } from '../api/diario'
import { Boton, Tarjeta, Vacio, Fallo, Etiqueta } from '../componentes/ui'

const NOMBRE_NUTRIENTE: Record<string, string> = {
  kcal: 'energia',
  proteinas_g: 'proteinas',
  grasas_g: 'grasas',
  hidratos_g: 'hidratos',
}


const COMIDAS = ['desayuno', 'media manana', 'comida', 'merienda', 'cena', 'otras']
const FUENTES = ['etiqueta', 'ficha', 'estimado', 'desconocido']

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
  const casa = listas.data?.find((l) => l.es_de_casa) ?? null
  const listaId = casa?.id ?? null
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

      {sinLista && (
        <p className="mt-2 text-[15px] text-secundaria">
          {listas.isPending ? 'Mirando tu lista?' : 'Todavia no tienes ninguna lista.'}
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
                      <span className="text-[13px] text-secundaria tabular-nums"> {x.kcal} kcal</span>
                    )}
                  </li>
                ))}
              </ul>
              {previa.sin_dato.length > 0 && (
                <p className="text-[14px] text-secundaria">
                  {previa.sin_dato.length === 1
                    ? 'Uno no trae nutricion en el catalogo, asi que se anotaria como ?sin dato?: '
                    : `${previa.sin_dato.length} no traen nutricion en el catalogo, asi que se anotarian como ?sin dato?: `}
                  {previa.sin_dato.join(', ')}.
                </p>
              )}
              {previa.anotarian.length > 0 && (
                <>
                  <label className="flex flex-col gap-1 text-[13px] text-secundaria">
                    Comida
                    <select
                      value={comida}
                      onChange={(e) => setComida(e.target.value)}
                      className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
                    >
                      {COMIDAS.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </label>
                  <Boton onClick={() => anotar.mutate()} disabled={anotar.isPending}>
                    Si, anotarlo
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
    <Tarjeta>
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
        <p className="text-[13px] leading-5 text-secundaria">
          <strong className="text-tinta-fuerte">Lo que apuntes es lo que has comido</strong>, no los
          valores de 100 g. Si tienes la ficha del producto, anotalo desde ahí y la cuenta la hace
          el servidor. Deja en blanco lo que no sepas: <strong className="text-tinta-fuerte">no es
          cero</strong>, es que no se sabe.
        </p>
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Comida
            <select
              value={comida}
              onChange={(e) => setComida(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            >
              {COMIDAS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            {esReceta ? 'Receta (nombre o numero)' : 'Que has comido'}
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Energia (kcal)
            <input
              value={kcal}
              onChange={(e) => setKcal(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-28 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Cantidad (g)
            <input
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
              inputMode="decimal"
              placeholder="150"
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Proteinas (g)
            <input
              value={proteinas}
              onChange={(e) => setProteinas(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Grasas (g)
            <input
              value={grasas}
              onChange={(e) => setGrasas(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Hidratos (g)
            <input
              value={hidratos}
              onChange={(e) => setHidratos(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            De donde sale el dato
            <select
              value={fuente}
              onChange={(e) => setFuente(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            >
              {FUENTES.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-h-[44px] min-w-[44px] items-center gap-2 text-[14px] text-tinta-fuerte">
            <input type="checkbox" checked={esReceta} onChange={(e) => setEsReceta(e.target.checked)} />
            Es una receta
          </label>
          {esReceta && (
            <label className="flex items-center gap-2 text-[13px] text-secundaria">
              Version
              <input
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="min-h-[44px] w-20 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
              />
            </label>
          )}
          <Boton type="submit" disabled={apuntar.isPending}>
            {apuntar.isPending ? 'Anotando...' : 'Anotar'}
          </Boton>
        </div>
        {esReceta && (
          <p className="text-[13px] text-secundaria">
            La version no es un detalle: es lo que permitira releer este dia dentro de un mes tal y como
            estaba, aunque la receta haya cambiado.
          </p>
        )}
        {apuntar.error && <Etiqueta tono="mal">{textoDeError(apuntar.error)}</Etiqueta>}
      </form>
    </Tarjeta>
  )
}

export function Diario() {
  const [fecha, setFecha] = useState(hoy())
  const { data, isPending, error } = useDia(fecha)
  const borrar = useBorrarEntrada(fecha)

  const conDato = data?.conocido.entradas ?? 0
  const total = data?.entradas.length ?? 0
  const faltan = data?.sin_dato.length ?? 0

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-[13px] text-secundaria">
          Dia
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
          />
        </label>
        <button
          type="button"
          onClick={() => setFecha(hoy())}
          className="min-h-[44px] min-w-[44px] text-[14px] text-secundaria underline"
        >
          Hoy
        </button>
      </div>

      {isPending && <p className="text-[16px] text-secundaria">Leyendo el diario...</p>}
      {error && <Fallo error={error} />}

      <DeLaCompra fecha={fecha} />

      {data && (
        <Tarjeta>
          <div className="flex flex-wrap items-baseline gap-4">
            <p className="font-serif text-[28px] leading-[34px] font-semibold text-tinta-fuerte tabular-nums">
              {data.conocido.kcal === null ? 'sin dato' : `${data.conocido.kcal} kcal`}
            </p>
            <p className="text-[13px] text-secundaria tabular-nums">
              de {conDato} de {total} {total === 1 ? 'entrada' : 'entradas'}
            </p>
          </div>
          {/* La frase que impide leer el numero de arriba como "lo que comi hoy". */}
          {!data.completo && total > 0 && (
            <p className="mt-1 text-[14px] leading-[22px] text-aviso">
              Este dia <strong>no esta completo</strong>: falta el dato de {faltan}{' '}
              {faltan === 1 ? 'entrada' : 'entradas'}. Lo de arriba es lo que se sabe, no lo que comiste.
            </p>
          )}

          {/* **La cobertura, nutriente a nutriente.** El total de energia puede estar completo y faltar
              las proteinas: decir "3 de 4 entradas" es lo que impide leer el numero de arriba como si
              fuera el dia entero. Y un nutriente que no trae nadie se dice con la palabra, no con un 0. */}
          {data.cobertura && (
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
              {Object.entries(data.cobertura).map(([nutriente, c]) => (
                <li key={nutriente} className="text-[13px] text-secundaria tabular-nums">
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
          {data.completo && total > 0 && (
            <p className="mt-1 text-[14px] text-secundaria">
              Todas las entradas anotadas tienen calorías. El subtotal solo incluye lo registrado;
              comprueba que hayas anotado todas tus comidas.
            </p>
          )}
        </Tarjeta>
      )}

      <Alta fecha={fecha} />

      {data && total === 0 && (
        <Vacio titulo="Nada anotado este dia" className="grow">
          <p>Anota lo primero arriba y aparecera aqui, agrupado por comidas.</p>
        </Vacio>
      )}

      {data &&
        Object.entries(data.comidas).map(([comida, entradas]) => (
          <section key={comida} className="flex flex-col gap-2">
            <h2 className="font-serif text-[19px] leading-7 text-tinta-fuerte">{comida}</h2>
            <ul className="flex flex-col gap-2">
              {entradas.map((e) => (
                <li key={e.id}>
                  <Tarjeta>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-[16px] text-tinta-fuerte">
                        {e.tipo === 'receta' ? `Receta ${e.referencia} (v${e.version})` : e.referencia || 'sin nombre'}
                      </span>
                      <span className="text-[13px] tabular-nums text-secundaria">
                        {e.kcal === null ? 'sin dato' : `${e.kcal} kcal`} · {e.fuente_dato}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => borrar.mutate(e.id)}
                      className="mt-1 min-h-[44px] min-w-[44px] text-[13px] text-secundaria underline"
                    >
                      Quitar
                    </button>
                  </Tarjeta>
                </li>
              ))}
            </ul>
          </section>
        ))}
    </div>
  )
}
