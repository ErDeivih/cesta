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
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { borrarAlerta, marcarVistas } from '../api/alertas'
import { useAlertas } from '../api/consultas'
import { fecha, hace } from '../api/formato'
import { Aviso, Boton, Cargando, Fallo, Tarjeta, Vacio } from '../componentes/ui'
import type { Alerta } from '../tipos'

/** Lo que promete una alerta, en palabras. Es una promesa: no ha pasado todavia. */
export function promesa(a: Alerta): string {
  if (a.tipo === 'baja_de') {
    return a.umbral_cent
      ? `Te aviso si baja de ${(a.umbral_cent / 100).toFixed(2)} €`
      : 'Te aviso si baja'
  }
  if (a.tipo === 'minimo_90d') return 'Te aviso cuando esté en su precio más bajo de 90 días'
  return 'Te aviso si baja'
}

/** El nombre del producto, o la verdad: ya no está en el catálogo. */
function Nombre({ a }: { a: Alerta }) {
  if (!a.nombre) {
    return <span className="flex-1 text-tinta-suave">Un producto que ya no está en el catálogo</span>
  }
  return (
    <Link to={`/grupo/${a.grupo_id}`} className="flex-1 font-medium underline">
      {a.nombre}
    </Link>
  )
}

export function Avisos() {
  const cliente = useQueryClient()
  const consulta = useAlertas()

  const vistas = useMutation({
    mutationFn: marcarVistas,
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })
  const quita = useMutation({
    mutationFn: borrarAlerta,
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })

  if (consulta.isPending) return <Cargando que="tus avisos" />
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
                <Link to={`/grupo/${s.grupo_id}`} className="font-medium underline">
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
                  <Nombre a={a} />
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

      <Tarjeta titulo="Esperando" sub="Todavía no se ha cumplido. Te aviso yo.">
        {esperando.length === 0 ? (
          <Vacio titulo="No sigues ningún producto">
            <p>
              Esto sirve para que <strong>la aplicación te busque a ti</strong> en vez de
              que tú entres a mirar. Abre la ficha de un producto y pulsa «Avisarme si
              baja»: te aviso cuando esté en su precio más bajo de 90 días.
            </p>
          </Vacio>
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

      {quita.isError && (
        <Aviso tono="aviso" titulo="No he podido quitar el aviso">
          <p>Vuelve a intentarlo.</p>
        </Aviso>
      )}
    </div>
  )
}
