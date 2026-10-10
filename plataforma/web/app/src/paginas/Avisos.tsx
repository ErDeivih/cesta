/** Los avisos: lo que ha bajado de lo tuyo, dicho por la aplicacion y no por ti.
 *
 *  Es la pantalla del punto 6 del encargo, y la mitad que faltaba: alli se arreglo que
 *  **la alerta salte sin que nadie abra nada** (el vigilante de la API, en cuanto cambia
 *  gold); esto es lo que se ve cuando salta. El encargo lo pedia asi: *"un punto en el
 *  icono, y al abrirlo **la frase entera** --«el aceite que sigues esta a 3,89 €/l en
 *  Alcampo, el mas barato en 90 dias»--, no un numero rojo sin contexto."*
 *
 *  Tres clases de fila, y dos de ellas **no se pueden mezclar**:
 *
 *    ha bajado         se cumple hoy: la frase la calcula el servidor al pedirla
 *    salto y ya no     hay frase **guardada del dia en que salto**, con su fecha
 *    esperando         existe la promesa y todavia no se ha cumplido
 *
 *  Las dos primeras son la respuesta a *"¿ha bajado algo de lo mio?"*; la tercera es lo
 *  que se ha pedido, y su frase es una promesa, no un hecho: escribirla como si hubiera
 *  pasado seria vender.
 *
 *  Y **la frase guardada no se recalcula nunca**: se midio contra el gold de ese dia, y
 *  gold es otro cada manana. Un aviso que cambia de texto al dia siguiente no es un
 *  aviso, es un rumor.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { borrarAlerta, marcarVistas } from '../api/alertas'
import { yo } from '../api/cesta'
import { useAlertas } from '../api/consultas'
import { euros, fecha, hace } from '../api/formato'
import { Aviso, Boton, Esqueleto, Fallo, Tarjeta, Vacio } from '../componentes/ui'
import type { Alerta } from '../tipos'

/** Lo que promete una alerta, en palabras. Es una promesa: no ha pasado todavia. */
export function promesa(a: Alerta): string {
  if (a.tipo === 'baja_de') {
    // `euros` y no `(umbral_cent / 100).toFixed(2)`: con `toFixed` la promesa se leia
    // «Te aviso si baja de 3.89 €», con el punto decimal en ingles, en una frase que se lee en
    // español y al lado de precios con coma. Medido el 27 de septiembre de 2026.
    return a.umbral_cent ? `Te aviso si baja de ${euros(a.umbral_cent)}` : 'Te aviso si baja'
  }
  if (a.tipo === 'minimo_90d') return 'Te aviso cuando esté en su precio más bajo de 90 días'
  return 'Te aviso si baja'
}

/** El nombre del producto, o algo que sea verdad cuando no llega.
 *
 *  **Cuidado con lo que se dice aqui.** Si la tarjeta no llega, pueden ser dos cosas y
 *  ninguna se puede afirmar: que el grupo ya no este en el catalogo (el emparejador se
 *  rehizo) **o que la API que corre sea mas vieja que esta pantalla** y todavia no mande
 *  el nombre. Escribir "ya no esta en el catalogo" seria mentir en el segundo caso, y
 *  encima sobre un producto que si existe. Se dice lo unico que sabemos -- que es un
 *  producto de los que sigues -- y el enlace lleva a la ficha, que si sabe la verdad.
 */
function Nombre({ a, deEntonces = false }: { a: Alerta; deEntonces?: boolean }) {
  // `min-h-[44px]` con `inline-flex`: medido en el navegador (23 sep 2026), estos enlaces
  // median **21 px de alto**, y son la forma de ir al producto del que habla el aviso.
  //
  // **`deEntonces`: el nombre que salto, no el de hoy.** En las tarjetas que enseñan una frase
  // guardada, el sujeto tiene que ser el mismo que el de la frase. Medido el 28 de septiembre de
  // 2026: «TWIX Barritas ... esta al precio mas bajo de los ultimos 90 dias: 0.96 EUR/l en
  // mercadona» -- la frase es de la leche entera, que es lo que ese grupo era el dia que salto.
  // Si la fila es de antes de que existiera la columna, se cae al nombre del grupo, que es lo que
  // se hacia hasta hoy: no se inventa nada.
  const mostrado = (deEntonces && a.salto_nombre) || a.nombre
  const cambiado = Boolean(deEntonces && a.salto_nombre && a.nombre
                           && a.salto_nombre !== a.nombre)
  if (!mostrado) {
    return (
      <Link to={`/grupo/${a.grupo_id}`}
            className="inline-flex min-h-[44px] min-w-[44px] flex-1 items-center text-tinta-suave underline">
        Un producto que sigues
      </Link>
    )
  }
  return (
    <span className="min-w-0 flex-1">
      <Link to={`/grupo/${a.grupo_id}`}
            className="inline-flex min-h-[44px] min-w-[44px] items-center font-medium underline">
        {mostrado}
      </Link>
      {cambiado && (
        <span className="block text-xs text-tinta-suave">
          ese número es hoy «{a.nombre}»
        </span>
      )}
    </span>
  )
}

export function Avisos() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const consulta = useAlertas()

  const vistas = useMutation({
    mutationFn: marcarVistas,
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })
  const quita = useMutation({
    mutationFn: borrarAlerta,
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })

  // **El orden importa, y aquí está el fallo que se arregló el 27 de septiembre de 2026.**
  // `useAlertas` tiene `enabled: hay usuario`, así que sin sesión la consulta **no se lanza
  // nunca** y se queda en `pending` para siempre: mirando `consulta.isPending` antes que la
  // sesión, la pantalla enseñaba **un esqueleto eterno** -- medido con
  // `data/debug/texto.py /avisos --sin-sesion`: «Cargando…» y nada más--, en un destino de la
  // barra de abajo. Primero la sesión, después la consulta.
  if (sesion.isLoading) return <Esqueleto filas={4} alto="4.25rem" />
  if (!sesion.data?.usuario) {
    return (
      <Vacio titulo="Entra para ver tus avisos" comoPagina>
        <p>
          Los avisos son de cada uno: se piden desde la ficha de un producto, con la campana,
          y salen aquí con la frase que los explica. Se entra desde{' '}
          <Link to="/cesta" className="underline">la cesta</Link>.
        </p>
      </Vacio>
    )
  }
  if (consulta.isPending) return <Esqueleto filas={4} alto="4.25rem" />
  if (consulta.isError) {
    return <Fallo error={consulta.error} reintentar={() => void consulta.refetch()} />
  }

  const alertas = consulta.data.alertas
  const saltan = consulta.data.saltan
  const conFrase = alertas.filter((a) => a.salto_en)
  const idsQueSalen = new Set(saltan.map((s) => s.alerta_id))
  // Lo que ya salto y hoy no se cumple: su frase es la del dia que salto.
  const yaNo = conFrase.filter((a) => !idsQueSalen.has(a.id))
  const sinVer = conFrase.filter((a) => !a.vista_en).map((a) => a.id)
  const esperando = alertas.filter((a) => !a.salto_en)

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-baseline gap-2">
        <h1 className="text-xl font-semibold">Avisos</h1>
        <span className="text-sm text-tinta-suave">
          de {alertas.length} {alertas.length === 1 ? 'producto' : 'productos'} que sigues
        </span>
      </header>

      {saltan.length > 0 && (
        <Tarjeta titulo="Ha bajado" sub="Con la frase que lo explica, no un número suelto.">
          <ul className="grid gap-3">
            {saltan.map((s) => (
              <li key={s.alerta_id} className="rounded-lg border border-borde p-3">
                <Link to={`/grupo/${s.grupo_id}`}
                      className="inline-flex min-h-[44px] min-w-[44px] items-center font-medium underline">
                  {s.nombre}
                </Link>
                <p className="mt-1 text-sm">{s.por_que}</p>
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      {yaNo.length > 0 && (
        <Tarjeta
          titulo="Salió y ya no está a ese precio"
          sub="La frase es la del día en que saltó: entonces era verdad."
        >
          <ul className="grid gap-2">
            {yaNo.map((a) => (
              <li key={a.id} className="flex flex-wrap items-start gap-2 rounded-lg border border-borde p-3">
                <div className="min-w-[12rem] flex-1">
                  {/* **El nombre que salto, no el de hoy.** Esta tarjeta enseña una frase
                      guardada; el sujeto tiene que ser el mismo que el de la frase. */}
                  <Nombre a={a} deEntonces />
                  <p className="mt-1 text-sm">{a.salto_texto ?? 'Saltó.'}</p>
                  <p className="mt-1 text-xs text-tinta-suave">
                    {a.salto_en && <>Saltó {hace(a.salto_en)} · {fecha(a.salto_en)}</>}
                  </p>
                </div>
                <Boton variante="sutil" onClick={() => quita.mutate(a.id)}>
                  Quitar
                </Boton>
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      {/* El punto del icono se apaga con esto, y **a mano**: abrir la pantalla en el
          autobus no puede dar por contado lo que no se ha leído. */}
      {sinVer.length > 0 && (
        <div>
          <Boton
            variante="normal"
            disabled={vistas.isPending}
            onClick={() => vistas.mutate(sinVer)}
          >
            Ya los he visto ({sinVer.length})
          </Boton>
        </div>
      )}

      {alertas.length === 0 && (
        <Tarjeta>
          <p className="text-base font-semibold">No sigues ningún producto</p>
          <p className="mt-2 text-sm text-tinta-suave">
            Esto sirve para que <strong>la aplicación te busque a ti</strong> en vez de que tú
            entres a mirar: te aviso cuando lo que sigues esté en su precio más bajo de 90 días,
            y sale aquí, con la frase que lo explica.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              to="/buscar"
              className="inline-flex min-h-[44px] items-center rounded-lg bg-sky-700 px-3 text-sm font-semibold text-white dark:bg-sky-500 dark:text-neutral-900"
            >
              Buscar un producto
            </Link>
            <Link
              to="/panel?pestana=bajadas"
              className="inline-flex min-h-[44px] items-center rounded-lg border border-neutral-300 px-3 text-sm dark:border-neutral-600"
            >
              Ver lo que ha bajado esta semana
            </Link>
          </div>
          <p className="mt-3 text-sm text-tinta-suave">
            En la ficha de un producto, el botón se llama «Avisarme si baja».
          </p>
        </Tarjeta>
      )}

      {/* **Sin nada que esperar no se pinta «Esperando».** Medido en la captura de un móvil el
          27 de septiembre de 2026, con una cuenta que no seguía ningún producto: la pantalla
          decía «Esperando · Todavía no se ha cumplido. Te aviso yo.» con **cero** avisos, y
          debajo, dentro de la misma tarjeta, la caja que decía «No sigues ningún producto».
          Dos cabeceras para un estado, y la primera contradecía a la segunda: una tarjeta que
          dice «esperando» cuando no se espera nada no informa, confunde. La tarjeta del caso
          vacío, arriba, **dice qué hacer y da por dónde** (buscar), que era lo que le faltaba:
          antes acababa en «abre la ficha de un producto», que es un callejón sin salida en la
          pantalla que está a un toque de la barra de abajo. */}
      {alertas.length > 0 && (
      <Tarjeta titulo="Esperando" sub="Todavía no se ha cumplido. Te aviso yo.">
        {esperando.length === 0 ? (
          <p className="text-sm text-tinta-suave">
            Ninguno esperando: los que sigues ya han saltado, y están arriba con su frase.
          </p>
        ) : (
          <ul className="grid gap-2">
            {esperando.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-borde p-2">
                <Nombre a={a} />
                <span className="text-sm text-tinta-suave">{promesa(a)}</span>
                <Boton variante="sutil" onClick={() => quita.mutate(a.id)}>
                  Quitar
                </Boton>
              </li>
            ))}
          </ul>
        )}
      </Tarjeta>
      )}

      {quita.isError && (
        <Aviso tono="aviso" titulo="No he podido quitar el aviso">
          <p>Vuelve a intentarlo.</p>
        </Aviso>
      )}
    </div>
  )
}
