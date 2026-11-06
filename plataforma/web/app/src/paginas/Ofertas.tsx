/** Las ofertas que anuncian hoy las cadenas: que hay, cuanto cuesta y que hace falta.
 *
 *  **Lo que esta pantalla es, y lo que no.** Es una lista **informativa**: el precio
 *  que se enseña es el que se cobra hoy por ese producto, y al lado va el texto de la
 *  cadena, el tipo de oferta y **la condicion** («Con Lidl Plus», «Con tarjeta DIA»,
 *  «Solo online»). No es una caja: no hay precio final ni «te ahorras tanto», porque
 *  un 3x2 no baja el precio de una unidad y un 25 % acumulado en la tarjeta no se
 *  descuenta en el ticket. *Enseñar esa resta seria inventarse una caja que no
 *  conocemos, y la regla de la casa es no inventar numeros.*
 *
 *  **Sin sesion.** Las ofertas son publicas: no se pregunta por la cuenta ni se
 *  esconden detras de una puerta. *Son de las pocas cosas que se pueden mirar sin
 *  entrar, y tiene sentido: es lo que se mira antes de decidir si entrar.*
 *
 *  **Los chips.** «Descuento», «2ª unidad», «Club» y «Solo online» son los cuatro
 *  cortes que se hacen al mirar una oferta: cuanto baja, cuantas hay que llevar, si
 *  pide tarjeta y donde se compra. *«2ª unidad» incluye el 3x2 y el 2x1 porque la
 *  pregunta es la misma -- cuantas unidades -- y la tarjeta de cada oferta dice cual
 *  es su mecanica; partirla en dos chips seria pedirle a quien compra que sepa la
 *  diferencia antes de pulsar.*
 *
 *  **El estado vacio no inventa.** Si el gold no trae ofertas, se dice; si el chip
 *  elegido no tiene ninguna, se dice cual es el caso. *Una lista vacia sin
 *  explicacion se lee como una pantalla rota.*
 *
 *  La consulta vive aqui y no en `api/consultas.ts` a proposito: esta pantalla es
 *  nueva y su contrato (`/api/ofertas`) tambien, asi que se cambia en un solo
 *  fichero sin tocar la capa compartida que usan las demas.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { pide } from '../api/cliente'
import { euros, fecha, nombreCadena } from '../api/formato'
import { Cargando, Fallo, Vacio, cx } from '../componentes/ui'

/** Una oferta de hoy, tal y como la devuelve `GET /api/ofertas`.
 *
 *  *`precio_cent` es el precio de hoy, el de la estanteria. `tipo` y `condicion` son
 *  lo que la pantalla necesita para no tener que interpretar `promo_txt`, que viene
 *  tal cual lo escribe la cadena.*
 */
export interface Oferta {
  grupo_id: number
  cadena: string
  nombre: string
  marca: string | null
  id_fuente: string
  imagen: string | null
  precio_cent: number
  /** La unidad de `precio_cent`: kg, l o ud. Sin ella, un numero no dice de que es. */
  unidad: string | null
  promo_txt: string
  /** `descuento`, `segunda_unidad`, `3x2`, `club`, `solo_online` u `otro`. */
  tipo: string
  /** La oferta solo existe con el club o la tarjeta de esa cadena. */
  exige_club: boolean
  /** La oferta solo existe comprando por internet. */
  solo_online: boolean
  /** Lo mismo que las dos banderas, en lenguaje de usuario. */
  condicion: string
  /** Ultimo dia de la oferta (`YYYY-MM-DD`), o `null` si no lo declara. */
  hasta: string | null
}

export interface RespuestaOfertas {
  fecha_datos: string
  resultados: Oferta[]
}

/** Los cinco cortes de la pantalla. `unidades` cubre 2ª unidad, 2x1 y 3x2. */
type Filtro = 'todas' | 'descuento' | 'unidades' | 'club' | 'online'

const FILTROS: { clave: Filtro; texto: string }[] = [
  { clave: 'todas', texto: 'Todas' },
  { clave: 'descuento', texto: 'Descuento' },
  { clave: 'unidades', texto: '2ª unidad' },
  { clave: 'club', texto: 'Club' },
  { clave: 'online', texto: 'Solo online' },
]

/** Cuantas ofertas se piden de una vez. *El servidor acota a 200; la pantalla pide 60,
 *  que llenan de sobra la primera pasada y no arrastran seis mil tarjetas al movil.* */
const LIMITE = 60

/** Lo que se le pide a la API para cada chip.
 *
 *  *Los chips de tipo filtran por `tipos` en el servidor y no en el movil:* la lista
 *  viene recortada a 60 y filtrar despues dejaria el chip vacio aunque hubiera
 *  ofertas. Es la misma razon por la que `useBajadas` manda `solo_mios` al servidor.
 *  *`club` filtra por **condicion**, no por tipo:* quien pulsa «Club» busca las
 *  ofertas de su tarjeta, tengan el mecanismo que tengan.*
 */
export function parametrosDe(filtro: Filtro): Record<string, string | number> {
  switch (filtro) {
    case 'descuento':
      return { limite: LIMITE, tipos: 'descuento' }
    case 'unidades':
      return { limite: LIMITE, tipos: 'segunda_unidad,3x2' }
    case 'club':
      return { limite: LIMITE, club: 'true' }
    case 'online':
      return { limite: LIMITE, solo_online: 'true' }
    default:
      return { limite: LIMITE }
  }
}

const PORCENTAJE = /(\d{1,3})\s*%/
const NXM = /(\d)\s*[x*]\s*(\d)/

/** La fecha de la oferta se quita del texto: ya se enseña aparte, si existe. */
function sinFechas(texto: string): string {
  return texto.replace(/\([^)]*\)/g, ' ').replace(/\s+/g, ' ').trim()
}

/** **El chip de la tarjeta: lo que dice la cadena, o el tipo si el texto es largo.**
 *
 *  *Un texto corto se enseña tal cual -- «3x2», «-14%», «50% que vuelve» -- porque es
 *  lo que la cadena anuncia y no hay nada que resumir.* *Uno largo («2ª UD 50% DTO.
 *  EN SELECCIÓN BONDUELLE») se resume con el tipo y su porcentaje: el nombre del
 *  producto ya está en la tarjeta, y repetirlo en el chip no informa de nada.*
 *
 *  *Y lo que no encaja se llama «Oferta», nunca «Descuento»: un «5€ dto.» o un
 *  «Envío Gratis» no son un porcentaje, y ponerles el nombre de otro tipo seria
 *  decir algo que la cadena no ha dicho.*
 */
export function etiquetaDe(oferta: Oferta): string {
  const corto = sinFechas(oferta.promo_txt)
  if (corto && [...corto].length <= 20) return corto
  const porcentaje = PORCENTAJE.exec(oferta.promo_txt)?.[1]
  switch (oferta.tipo) {
    case 'descuento':
      return porcentaje ? `Descuento ${porcentaje} %` : 'Descuento'
    case 'segunda_unidad':
      return porcentaje ? `2ª unidad −${porcentaje} %` : '2ª unidad'
    case '3x2': {
      const nxm = NXM.exec(oferta.promo_txt)
      return nxm ? `${nxm[1]}x${nxm[2]}` : '3x2'
    }
    case 'club':
      return 'Precio club'
    case 'solo_online':
      return 'Solo online'
    default:
      return 'Oferta'
  }
}

/** *El color del chip dice el tipo, no el estado: verde para el descuento, terracota
 *  para las unidades, aviso para lo que pide algo (club u online).* *Son los pares del
 *  sistema aprobado y llevan texto siempre, asi que no dependen solo del color.* */
const TONO: Record<string, string> = {
  descuento: 'bg-lavado-verde text-verde-fuerte',
  segunda_unidad: 'bg-lavado-terracota text-terracota',
  '3x2': 'bg-lavado-terracota text-terracota',
  club: 'bg-lavado-aviso text-aviso',
  solo_online: 'bg-lavado-aviso text-aviso',
  otro: 'border border-borde bg-marfil text-tinta-suave',
}

export function Ofertas() {
  const [filtro, setFiltro] = useState<Filtro>('todas')

  const consulta = useQuery({
    queryKey: ['ofertas', filtro],
    queryFn: ({ signal }) =>
      pide<RespuestaOfertas>('/ofertas', parametrosDe(filtro), signal),
    // Gold cambia una vez al dia: pedir lo mismo al cambiar de chip es barato
    // porque el servidor lo tiene cacheado por version, y aqui se guarda cinco
    // minutos para no repetir la peticion al volver a «Todas».
    staleTime: 5 * 60 * 1000,
  })

  const ofertas = consulta.data?.resultados ?? []
  const vacio = filtro === 'todas' ? 'Hoy no hay ofertas anunciadas' : 'No hay ofertas de este tipo hoy'

  return (
    <div className="flex min-h-full flex-col gap-4">
      <h2 className="font-serif text-titulo font-semibold text-tinta-fuerte">
        Lo que hay esta semana
      </h2>

      {/* *Los chips, con el borde del sistema y sin sombra: se pulsan, no se leen.*
          *`overflow-x-auto` porque en 390 px los cinco no caben de una vez, y es
          mejor deslizar que apretarlos por debajo de 44 px.* */}
      <div
        role="group"
        aria-label="Tipo de oferta"
        className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1"
      >
        {FILTROS.map((f) => {
          const activo = f.clave === filtro
          return (
            <button
              key={f.clave}
              type="button"
              aria-pressed={activo}
              onClick={() => setFiltro(f.clave)}
              className={cx(
                'inline-flex min-h-[44px] shrink-0 items-center rounded-pastilla px-4 text-etiqueta font-semibold',
                'transition-colors duration-rapida ease-suave',
                activo
                  ? 'bg-bosque text-sobre-bosque'
                  : 'border border-borde-fuerte bg-papel text-tinta-fuerte hover:bg-marfil',
              )}
            >
              {f.texto}
            </button>
          )
        })}
      </div>

      {consulta.isPending && <Cargando que="las ofertas" filas={6} />}

      {!consulta.isPending && consulta.error && (
        <Fallo
          error={consulta.error}
          reintentar={() => {
            void consulta.refetch()
          }}
        />
      )}

      {!consulta.isPending && !consulta.error && ofertas.length === 0 && (
        <Vacio titulo={vacio} className="grow">
          {filtro === 'todas' && (
            <p>Las cadenas no han publicado ninguna oferta para hoy.</p>
          )}
        </Vacio>
      )}

      {!consulta.isPending && !consulta.error && ofertas.length > 0 && (
        <ul className="flex flex-col gap-3">
          {ofertas.map((o) => (
            <li key={`${o.cadena}:${o.id_fuente}`}>
              <article className="rounded-tarjeta border border-borde bg-papel p-4 shadow-apoyado">
                <p className="text-micro uppercase tracking-wide text-tinta-tenue">
                  {nombreCadena(o.cadena)}
                </p>
                <div className="mt-1 flex items-start justify-between gap-3">
                  <h3 className="min-w-0 text-cuerpo-fuerte text-tinta-fuerte">
                    {/* *Si la oferta no trae identificador, el nombre se queda sin
                        enlace en vez de llevar a una ficha que no existe.* */}
                    {o.id_fuente ? (
                      <Link
                        to={`/compra/productos/${o.cadena}/${o.id_fuente}`}
                        className="inline-flex min-h-[44px] items-center hover:text-verde-fuerte"
                      >
                        {o.nombre}
                      </Link>
                    ) : (
                      <span className="inline-flex min-h-[44px] items-center">{o.nombre}</span>
                    )}
                  </h3>
                  <span className="shrink-0 text-precio-fila font-semibold tabular-nums text-tinta-fuerte">
                    {euros(o.precio_cent)}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span
                    className={cx(
                      'inline-flex min-h-[24px] items-center rounded-pastilla px-2 text-etiqueta font-semibold',
                      TONO[o.tipo] ?? TONO.otro,
                    )}
                  >
                    {etiquetaDe(o)}
                  </span>
                  {/* *La condicion, en las palabras de la calle: «Con Lidl Plus» dice
                      si la oferta es para ti; `promo_club=true` no dice nada.* */}
                  <span className="text-etiqueta text-tinta-suave">{o.condicion}</span>
                  {o.hasta && (
                    <span className="text-etiqueta text-tinta-tenue">
                      hasta el {fecha(o.hasta, true)}
                    </span>
                  )}
                </div>
                {/* *Cuando el chip se ha resumido, el texto de la cadena no se tira:
                    se enseña debajo, que es lo unico que hay para las ofertas raras.* */}
                {o.tipo === 'otro' && etiquetaDe(o) !== o.promo_txt && (
                  <p className="mt-1 text-etiqueta text-tinta-suave">{o.promo_txt}</p>
                )}
              </article>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
