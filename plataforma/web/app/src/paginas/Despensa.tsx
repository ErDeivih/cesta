/** La despensa: lo que hay en casa.
 *
 *  **Lo que esta pantalla tiene que decir bien, y es lo unico que importa aqui**: *«no se sabe cuanto» **no es
 *  «cero»**.* Una existencia **sin cantidad** se enseña **como lo que es** -- *no con un `0`, que afirmaria que no
 *  queda nada* --, y el total de las que no se sabe **se dice arriba**, para que no parezca que la lista esta
 *  completa.
 *
 *  **Y no hay ningun boton de «he comprado».** *No es un olvido:* **la ruta no existe**, porque *«compra no
 *  acredita consumo ni stock restante»* (`R08`). *Lo que hay es **declarar** lo que hay -- que sobrescribe -- y
 *  **gastar**.
 */
import { useState } from 'react'

import { declara, consume, useDespensa } from '../api/despensa'
import { textoDeError, useSeAtasca } from '../api/cliente'
import { Fallo, Cargando } from '../componentes/ui'
import { Boton, Tarjeta, Vacio } from '../componentes/ui'

/** **Como se lee una cantidad.** *Y `null` **no** es `0`: es «no se sabe».* */
function cuanto(e: { cantidad: number | null; unidad: string }): string {
  if (e.cantidad === null) return 'no se sabe cuanto'
  return `${e.cantidad}${e.unidad ? ' ' + e.unidad : ''}`
}

export function Despensa() {
  const { data, isLoading, error } = useDespensa()
  const atascada = useSeAtasca(isLoading)
  const [texto, setTexto] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [unidad, setUnidad] = useState('')
  const [aviso, setAviso] = useState<string | null>(null)
  const [gastado, setGastado] = useState<string | null>(null)

  const mete = async () => {
    setAviso(null)
    const n = cantidad.trim() === '' ? null : Number(cantidad.replace(',', '.'))
    if (n !== null && !Number.isFinite(n)) {
      setAviso('Esa cantidad no es un numero.')
      return
    }
    try {
      await declara({ texto: texto.trim(), cantidad: n, unidad: unidad.trim() })
      setTexto(''); setCantidad(''); setUnidad('')
    } catch (e) {
      setAviso(textoDeError(e))
    }
  }

  const gasta = async (t: string) => {
    setAviso(null); setGastado(null)
    try {
      const r = await consume({ texto: t, cantidad: 1, unidad: '' })
      // **El motivo se enseña tal cual.** *«Queda menos, y no se sabe cuanto» es una respuesta, no un fallo.*
      if (r.motivo) setGastado(`${t}: ${r.motivo}`)
    } catch (e) {
      setAviso(textoDeError(e))
    }
  }

  // **Y «Cargando» no puede ser para siempre.** *Si la consulta se atasca, se dice -- ver `useSeAtasca`.*
  if (isLoading && !atascada) return <Cargando que="la despensa" />
  if (isLoading && atascada) {
    return (
      <div className="space-y-3">
        <h2 className="text-xl font-semibold">La despensa</h2>
        <p className="text-aviso">
          No se ha podido preguntar al servidor. Esto <strong>no</strong> quiere decir que la despensa este vacia.
        </p>
      </div>
    )
  }
  // *** Y esto era un `<p>` CRUDO, *no la pieza `Fallo`. *** *
  //
  // *Y no es un detalle de estilo: *la **misma** pantalla de error estaba escrita
  // *a mano aqui, *y en `RecetaDetalle:140`, *`Recetario:248`, *`Tendencias:73`,
  // *`PlanSemanal:336`, *`Diario:411`, *`CocinaModo:96`, *`Escaner:218` y
  // *`Ajustes:140` -- *con *** cuatro tamanos de letra distintos *** *(-- 13, 14, 15
  // *y 16 px --)*, *y **sin** titulo, *sin boton de reintentar y sin llenar el alto.* *
  //
  // *`Fallo` ya hace **las cuatro cosas**, *y su propio comentario dice que se arregla
  // *en un sitio y no en las seis pantallas que lo usan: *«*si se arreglara pantalla por
  // *pantalla, *la septima volveria a nacer en rojo*»*.* *Asi que se usa la pieza.* *
  if (error) return <Fallo error={error} />

  const existencias = data?.existencias ?? []

  return (
    <div className="flex min-h-full flex-col gap-4">
      <h2 className="text-xl font-semibold">La despensa</h2>
      <p className="text-cuerpo text-tinta-suave">
        Lo que hay en casa. <strong>Se declara</strong>, no se deduce de lo que se ha comprado:
        comprar algo no quiere decir que quede.
      </p>

      {data && data.sin_saber_cuanto > 0 && (
        <p className="text-cuerpo text-aviso">
          {data.sin_saber_cuanto === 1
            ? 'Hay 1 cosa de la que no se sabe cuanto queda.'
            : `Hay ${data.sin_saber_cuanto} cosas de las que no se sabe cuanto queda.`}
        </p>
      )}

      {aviso && <p className="text-cuerpo text-error">{aviso}</p>}
      {gastado && <p className="text-cuerpo text-tinta-suave">{gastado}</p>}

      {existencias.length === 0 ? (
        <Vacio titulo="La despensa esta vacia" className="grow">
          Declara lo que tengas en casa, y ve descontandolo.
        </Vacio>
      ) : (
        <Tarjeta>
          <ul className="divide-y divide-borde">
            {existencias.map((e) => (
              <li key={e.texto} className="flex items-center justify-between gap-3 py-2">
                <span>{e.texto}</span>
                <span className={e.se_sabe ? 'text-tinta-suave' : 'text-aviso'}>
                  {cuanto(e)}
                </span>
                <Boton onClick={() => gasta(e.texto)}>Gastar uno</Boton>
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      <Tarjeta>
        <h2 className="text-cuerpo font-semibold">Declarar lo que hay</h2>
        <div className="mt-2 flex flex-wrap items-end gap-2">
          <label className="flex flex-col text-cuerpo">
            Que
            <input className="min-h-11 rounded border border-borde px-2 py-1" value={texto}
                   onChange={(ev) => setTexto(ev.target.value)} placeholder="harina" />
          </label>
          <label className="flex flex-col text-cuerpo">
            Cuanto <span className="text-etiqueta text-tinta-suave">(vacio = no se sabe)</span>
            <input className="min-h-11 rounded border border-borde px-2 py-1" value={cantidad}
                   onChange={(ev) => setCantidad(ev.target.value)} placeholder="1" />
          </label>
          <label className="flex flex-col text-cuerpo">
            Unidad
            <input className="min-h-11 rounded border border-borde px-2 py-1" value={unidad}
                   onChange={(ev) => setUnidad(ev.target.value)} placeholder="kg" />
          </label>
          <Boton onClick={mete} disabled={!texto.trim()}>Declarar</Boton>
        </div>
      </Tarjeta>
    </div>
  )
}