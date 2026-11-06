/** LO DE SIEMPRE: la cuadricula de lo habitual, para anadirlo de un toque o de una vez.
 *
 *  Es la mejora de mas valor que le quedaba al buscador, y su razon esta en
 *  `docs/PANTALLAS.md:50-62`: anadir algo que compras siempre pasa de **escribir,
 *  elegir y anadir** a **un toque**. Esta pantalla se usa de pie y con una mano, asi
 *  que la diferencia entre dos pulsaciones y una no es comodidad: es que se use.
 *
 *  De donde sale: `GET /api/habituales`, con **cada tarjeta diciendo su `origen`**.
 *  Es la parte que no se puede saltar: la cuadricula puede tener cosas tuyas y cosas
 *  de la compra basica a la vez, y **no valen lo mismo**. Sin ese campo la pantalla
 *  ensenaria "lo que sueles comprar" con lo que compra otro.
 *
 *  Tres reglas que estan aqui dentro, y las tres son decisiones, no adornos:
 *
 *  1. **Sin historial, esto no se pinta: sale la tarjeta de la primera vez.**
 *     `LoQueSeCompra` ensena cuatro productos que compra todo el mundo **con su
 *     diferencia de hoy**, que es lo que hace entender para que sirve la aplicacion.
 *     Una cuadricula de 24 productos basicos no explica nada: son 24 recuadros sin
 *     una sola razon para mirarlos. Primero se entiende, despues se usa.
 *
 *     **Con una excepcion: `enUnaLista`** (se pinta dentro de la lista de casa). Ahi
 *     la cuadricula de la compra basica **si** tiene una razon: la pregunta que se trae
 *     a esa pantalla es *"¿que me falta?"*, y con la lista vacia la respuesta es
 *     "todo". 24 recuadros que se apuntan de un toque contestan eso; la tarjeta de la
 *     primera vez, no. Por eso `enUnaLista` quita el respaldo y **cambia el titulo**
 *     por el de verdad ("La compra basica", "Lo que compra la casa"): sin eso, una
 *     cuadricula de basicos se leeria como "lo que sueles comprar", que es mentira.
 *  2. **Si el endpoint no esta, no pasa nada.** El 404 de una API que todavia no se
 *     ha desplegado no es un fallo de nadie: se cae a la tarjeta de la primera vez,
 *     igual que si no hubiera historial. Un error rojo aqui seria culpar a quien
 *     acaba de abrir la aplicacion.
 *  3. **Un toque, sin dialogo.** No se pregunta la cantidad ni a que lista: se apunta
 *     en la de casa (se crea si no hay) con cantidad 1, y el cuanto se cambia en la
 *     cesta, que es donde se ve la lista entera y lo que va a costar. Y el boton de
 *     cada tarjeta dice si ya esta dentro, para que pulsar dos veces no sea el error
 *     facil de verdad.
 *
 *  Y una cuarta, que es la que anade «rellenar sola» (**WALL**, «aprender de las
 *  listas»): **la sugerencia se ve antes de entrar**.
 *
 *  - **«Rellenar de una vez» no adivina: ensena.** El boton abre una previa con
 *    **cuantos productos** son y **sus nombres**, y hasta que no se confirma no se
 *    guarda nada. Es la regla de `PegarEnLaLista`, y aqui importa mas: lo que se
 *    rellena sale del habito de esta persona, y anadir a escondidas cosas deducidas es
 *    justo lo que `INVESTIGACION-APP.md` §9.3 llama el «rellenar sola» fingido.
 *  - **Lo que ya esta no se ofrece.** `puestos` (lo anadido aqui) y `enLaLista` (los
 *    grupos que ya trae la lista que se esta mirando) se restan antes de contar, asi
 *    que la previa dice lo que va a pasar de verdad y no una lista con repetidos.
 *  - **Se anade con `useAnadeALaCesta`, uno por producto**: no hay endpoint de lote y
 *    no se inventa. Si falla a medias **se dice cuantos entraron y cuantos no**, que
 *    es la unica forma de que el siguiente intento no repita lo que ya esta.
 *  - **La sugerencia de «la siguiente» sale del orden de la API**, que ya viene pesado
 *    por el habito (`almacen.historial_de`). Aqui no se calcula ninguna frecuencia ni
 *    se dice «lo que mas compras»: se senala la primera que falta y se calla el resto.
 */
import { useId, useState } from 'react'

import { esSinRed, textoDeError } from '../api/cliente'
import { useAnadeALaCesta, useHabituales } from '../api/consultas'
import { eurosUnidad, nombreCadena } from '../api/formato'
import { Aviso, Boton, EsqueletoRejilla, Etiqueta, Tarjeta } from './ui'
import { LoQueSeCompra } from './LoQueSeCompra'

/** Lo que dice el titulo segun de donde salga lo que se esta viendo. */
const TITULO: Record<string, string> = {
  tuyo: 'Lo de siempre',
  'de todos': 'Lo que compra la casa',
  basico: 'La compra básica',
}

/** La cuadricula de lo habitual.
 *
 *  `enUnaLista` se pone cuando se pinta dentro de la lista: ahi la compra basica **si**
 *  se ensena (ver la regla 1 del comentario de arriba). Por defecto no, que es lo que
 *  quieren el buscador y todo lo demas.
 *
 *  `enLaLista` son los `grupo_id` que ya estan en la lista que se esta mirando. No se
 *  pintan como «Añadir» ni entran en la previa: una lista de la compra con el mismo
 *  producto dos veces no es un relleno, es un error.
 */
export function Mosaico({ limite = 12, enUnaLista = false, enLaLista = [] }: {
  limite?: number
  enUnaLista?: boolean
  enLaLista?: number[]
}) {
  const habituales = useHabituales(limite)
  const anade = useAnadeALaCesta()
  const [puestos, setPuestos] = useState<number[]>([])
  /** La previa de «rellenar de una vez», abierta a peticion. */
  const [previa, setPrevia] = useState(false)
  const [rellenando, setRellenando] = useState(false)
  /** El resultado del ultimo relleno: cuantos entraron de cuantos, y el fallo si lo hubo. */
  const [resultado, setResultado] = useState<{ anadidos: number; total: number } | null>(null)
  const [fallo, setFallo] = useState<unknown>(null)
  /** El id de la previa, para que el boton diga que abre y cierra **que** (`aria-controls`). */
  const idPrevia = useId()

  // Mientras se sabe, **el hueco de la cuadricula**: seis recuadros del tamaño de una
  // tarjeta, para que lo que llegue no empuje nada. Un hueco que aparece y desaparece
  // es peor que esperar medio segundo.
  if (habituales.isPending) return <EsqueletoRejilla tarjetas={6} />

  // El 404 (la ruta todavia no esta desplegada) y un historial que no da ni una
  // tarjeta llevan al mismo sitio: la tarjeta de la primera vez.
  const tarjetas = habituales.data?.habituales ?? []
  const soloBasico = (habituales.data?.origenes ?? []).every((o) => o === 'basico')
  if (tarjetas.length === 0 || (soloBasico && !enUnaLista)) return <LoQueSeCompra />

  // Si la cuadricula mezcla escalones, se dice: una tarjeta basica y una tuya no
  // valen lo mismo, y el titulo solo puede hablar de uno.
  const mezcla = new Set(tarjetas.map((h) => h.origen)).size > 1
  // Y cuando **no** mezcla, el titulo dice de donde sale de verdad. En la lista importa:
  // una cuadricula de la compra basica titulada "Lo de siempre" seria una mentira dicha
  // con un titulo.
  const titulo = enUnaLista && !mezcla
    ? (TITULO[tarjetas[0]?.origen] ?? 'Lo de siempre')
    : 'Lo de siempre'

  // Lo que la lista que se mira ya tiene. Se consulta con un `Set` porque se pregunta
  // una vez por tarjeta y por nombre en la previa.
  const enLaListaYa = new Set(enLaLista)
  const estaDentro = (grupoId: number) => puestos.includes(grupoId) || enLaListaYa.has(grupoId)
  // **La previa y el contador salen de aqui**: solo lo que de verdad falta.
  const pendientes = tarjetas.filter((h) => !estaDentro(h.grupo_id))

  /** Rellena de una vez, **una peticion por producto** y parando en el primer fallo.
   *
   *  Parar y contarlo es lo que permite decir «se han anadido 3 de 6»: seguir a ciegas
   *  despues de un fallo dejaria un resultado que no se puede comprobar, y reintentar
   *  sin saber cuantos entraron repetiria productos.
   */
  async function rellena() {
    if (rellenando || pendientes.length === 0) return
    const cuales = pendientes
    setRellenando(true)
    setFallo(null)
    setResultado(null)
    let anadidos = 0
    let ultimo: unknown = null
    for (const h of cuales) {
      try {
        await anade.mutateAsync({ grupoId: h.grupo_id, nombre: h.nombre })
        anadidos += 1
        setPuestos((x) => [...x, h.grupo_id])
      } catch (exc) {
        ultimo = exc
        break
      }
    }
    setRellenando(false)
    setPrevia(false)
    setResultado({ anadidos, total: cuales.length })
    setFallo(ultimo)
  }

  return (
    <Tarjeta>
      <p className="text-cuerpo font-semibold">{titulo}</p>
      <p className="mt-0.5 text-cuerpo text-tinta-suave">
        Un toque y a la lista. Lo tocado se cambia en la cesta.
      </p>

      {/* Tres columnas, como el diseno de `docs/PANTALLAS.md:57-62`: en el movil
          caben tres fotos de 80 px y el boton de debajo sigue teniendo sus 44 px de
          alto, que es el minimo que se puede pulsar andando. */}
      <ul className="mt-3 grid grid-cols-3 gap-2">
        {tarjetas.map((h) => {
          const dentro = estaDentro(h.grupo_id)
          return (
            <li key={h.grupo_id}
                className="flex flex-col gap-1 rounded-tarjeta border border-borde p-2">
              {h.imagen ? (
                <img
                  src={h.imagen}
                  alt=""
                  width={80}
                  height={80}
                  loading="lazy"
                  className="mx-auto h-20 w-20 rounded-campo border border-borde bg-papel object-contain "
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              ) : (
                // Sin foto no se inventa una: se deja el hueco del mismo tamano,
                // que mantiene la cuadricula alineada sin ensenar nada falso.
                <div className="mx-auto h-20 w-20 rounded-campo bg-marfil " />
              )}

              <span className="line-clamp-2 text-cuerpo font-medium leading-snug">
                {h.nombre}
              </span>
              <span className="cifra text-entrada font-semibold">
                {eurosUnidad(h.precio_unidad_cent, h.unidad)}
              </span>
              {h.cadena_mas_barata && (
                <span className="text-etiqueta text-tinta-suave">
                  en {nombreCadena(h.cadena_mas_barata)}
                </span>
              )}

              {/* El origen solo se dice cuando la cuadricula mezcla escalones: si
                  todas son tuyas, decirlo en las doce es ruido. */}
              {mezcla && (
                <Etiqueta tono={h.origen === 'tuyo' ? 'dato' : 'neutro'}>
                  {TITULO[h.origen] ?? h.origen}
                </Etiqueta>
              )}

              <Boton
                variante={dentro ? 'sutil' : 'normal'}
                className="mt-auto min-h-[44px] min-w-[44px]"
                disabled={anade.isPending || rellenando}
                title={dentro ? 'Ya esta en la lista: la cantidad se cambia en la cesta.' : undefined}
                onClick={() => {
                  if (dentro) return
                  // *Un relleno anterior ya no es el resultado de este toque: dejarlo en
                  // pantalla contaria algo que no acaba de pasar.*
                  setResultado(null)
                  setFallo(null)
                  anade.mutate(
                    { grupoId: h.grupo_id, nombre: h.nombre },
                    { onSuccess: () => setPuestos((x) => [...x, h.grupo_id]) },
                  )
                }}
              >
                {dentro ? 'En la cesta' : 'Añadir'}
              </Boton>
            </li>
          )
        })}
      </ul>

      {/* *** RELLENAR DE UNA VEZ. *** *
          *La sugerencia se ensena antes de que se guarde nada: cuantos son y sus nombres.
          Se confirma a proposito y no se anade al abrir, porque esto no es un carrito que
          se vacia: es la lista de la compra de una casa, y lo que entra sin permiso se
          queda.* */}
      <div className="mt-3 border-t border-borde pt-3">
        {pendientes.length > 0 ? (
          <>
            {/* La siguiente **sale del orden que ya trae la API**: la primera que falta.
                No se calcula ninguna frecuencia ni se dice «lo que mas compras»: eso no
                lo sabe esta pantalla. */}
            <p className="text-cuerpo text-tinta-suave">
              La siguiente sería <strong className="text-tinta">{pendientes[0].nombre}</strong>.
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Boton
                variante="principal"
                className="min-h-[44px]"
                disabled={rellenando}
                aria-expanded={previa}
                aria-controls={previa ? idPrevia : undefined}
                onClick={() => setPrevia((abierta) => !abierta)}
              >
                {rellenando ? 'Añadiendo…' : `Rellenar de una vez (${pendientes.length})`}
              </Boton>
            </div>
          </>
        ) : (
          <p className="text-cuerpo text-tinta-suave">
            Ya están todas en la lista.
          </p>
        )}

        {/* La previa, con los nombres: es la unica forma de que «6 productos» no sea una
            cifra que hay que creerse. */}
        {previa && !rellenando && pendientes.length > 0 && (
          <div id={idPrevia} className="mt-2 rounded-campo border border-borde-fuerte bg-fondo p-3">
            <p className="text-cuerpo font-medium">
              Se van a añadir {pendientes.length}{' '}
              {pendientes.length === 1 ? 'producto' : 'productos'}:
            </p>
            <ul className="mt-1 grid gap-0.5 text-cuerpo">
              {pendientes.map((h) => (
                <li key={h.grupo_id}>{h.nombre}</li>
              ))}
            </ul>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Boton
                variante="principal"
                className="min-h-[44px]"
                disabled={rellenando}
                onClick={() => void rellena()}
              >
                Sí, añadir {pendientes.length}
              </Boton>
              <Boton
                variante="sutil"
                className="min-h-[44px]"
                disabled={rellenando}
                onClick={() => setPrevia(false)}
              >
                No, déjalo
              </Boton>
            </div>
          </div>
        )}

        {/* El resultado, con las cuentas. Si falla a medias se dice **cuantos entraron**:
            callarlo dejaria productos sin anadir y un reintento a ciegas. */}
        {resultado && (
          fallo ? (
            <div className="mt-2">
              <Aviso
                tono="mal"
                titulo={resultado.anadidos > 0
                  ? `Se han añadido ${resultado.anadidos} de ${resultado.total}`
                  : 'No se ha añadido ninguno'}
              >
                <p>
                  {resultado.anadidos > 0
                    ? 'El resto no ha entrado. Vuelve a intentarlo.'
                    : 'Vuelve a intentarlo.'}
                </p>
                <p className="mt-1 text-etiqueta">
                  {esSinRed(fallo)
                    ? 'Sin conexión: no se ha podido seguir.'
                    : textoDeError(fallo)}
                </p>
              </Aviso>
            </div>
          ) : (
            <div className="mt-2">
              <Aviso tono="bien">
                {resultado.total === 1
                  ? 'Añadido 1 producto a la lista.'
                  : `Añadidos ${resultado.anadidos} productos a la lista.`}
              </Aviso>
            </div>
          )
        )}
      </div>

      {/* Un fallo al anadir **suelto** se dice, pero **fuera de la tarjeta**: si cada
          recuadro pudiera pintar su error, doce tarjetas con el mismo texto rojo taparian
          la cuadricula entera por un fallo que es el mismo en todas. El de rellenar tiene
          su propio aviso arriba, con las cuentas. */}
      {anade.isError && !rellenando && !resultado && (
        <p className="mt-3 text-cuerpo">
          <Etiqueta tono="aviso">
            No he podido añadirlo a la lista. Vuelve a intentarlo.
          </Etiqueta>
        </p>
      )}
    </Tarjeta>
  )
}
