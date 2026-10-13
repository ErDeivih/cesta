/** **La grafica de las tres series**: lo registrado, lo previsto y el objetivo, en los mismos dias.
 *
 * ***Compra no es consumo, y por eso son tres series distintas***: *el registrado es lo que **se comio**, el
 * previsto es lo que **se va** a comer, y el objetivo es **lo que la persona se ha puesto** -- *y las tres se
 * comparan, no se funden en un numero.*
 *
 * **Y las tres pueden tener huecos, y se ven.** *Un dia sin dato lleva **la palabra**, y no una barra de
 * longitud cero* -- *que diria «cero kcal», y **eso no es lo que paso**: es que no se anoto.* Y lo mismo con
 * el objetivo: **un dia sin objetivo no es un dia de 0 kcal**, *y si no hay ninguno, **la grafica tiene dos
 * series y lo dice**.*
 *
 * *La regla vive en `logica/chispa.ts` y en `logica/puntosDeLasTres.ts`; **aqui solo se pinta**.*
 */
import { useQuery } from '@tanstack/react-query'

import { useRango } from '../api/diario'
import { usePrevision } from '../api/recetas'
import { yo } from '../api/cesta'
import { LeyendaDeSeries } from './LeyendaDeSeries'
import { serieDeChispa } from '../logica/chispa'
import { puntosObjetivo, puntosPrevistos, puntosRegistrados } from '../logica/puntosDeLasTres'

export interface PropsDeGrafica {
  desde: string
  hasta: string
}

/** *Los dias del rango, para poder pedir el objetivo de cada uno **aunque no haya datos**.* */
function diasEntre(desde: string, hasta: string): string[] {
  const dias: string[] = []
  const fin = new Date(`${hasta}T00:00:00`).getTime()
  for (let t = new Date(`${desde}T00:00:00`).getTime(); t <= fin; t += 86_400_000) {
    dias.push(new Date(t).toISOString().slice(0, 10))
  }
  return dias
}

function Valor({ valor, unidad }: { valor: number | null; unidad: string }) {
  if (valor === null) {
    // ***Y el hueco, con la palabra.*** *Una barra de longitud cero diria «cero», y no es cero.*
    return <span>sin dato</span>
  }
  return (
    <span>
      {valor} {unidad}
    </span>
  )
}

export function GraficaDeLasTres({ desde, hasta }: PropsDeGrafica) {
  const rango = useRango(desde, hasta)
  const prevision = usePrevision(desde, hasta)
  // *Y **la misma consulta** que ya usa `useClaveDeCuenta`: la clave `['yo']` y la funcion `yo`.*
  const cuenta = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })

  const registrado = serieDeChispa(puntosRegistrados(rango.data?.dias ?? []))
  const previsto = serieDeChispa(puntosPrevistos(prevision.data?.comidas ?? []))
  const objetivo = serieDeChispa(
    puntosObjetivo(
      (cuenta.data as { preferencias?: Record<string, unknown> } | undefined)?.preferencias,
      diasEntre(desde, hasta),
    ),
  )
  const nota = objetivo.dibujable ? 'tres_series' : registrado.dibujable || previsto.dibujable ? 'sin_objetivo' : 'sin_nada'

  const cargando = rango.isPending || prevision.isPending || cuenta.isPending
  const fallo = rango.isError || prevision.isError
  if (cargando) return <p>Cargando…</p>
  if (fallo) return <p>No se han podido leer las series.</p>

  return (
    <div>
      {/* *Y los avisos del objetivo y de la prevision, que son los que evitan que la grafica mienta.* */}
      {prevision.data && prevision.data.sin_dato.length > 0 && (
        <p>
          Ingredientes sin producto en el catalogo: {prevision.data.sin_dato.join(', ')}. No se les
          atribuye ninguna nutricion.
        </p>
      )}

      <table>
        <caption>
          Registrado, previsto y objetivo, dia a dia. «Sin dato» quiere decir que no se sabe, y no cero.
        </caption>
        <thead>
          <tr>
            <th scope="col">Dia</th>
            <th scope="col">Registrado</th>
            <th scope="col">Previsto</th>
            <th scope="col">Objetivo</th>
          </tr>
        </thead>
        <tbody>
          {diasEntre(desde, hasta).map((fecha, i) => (
            <tr key={fecha}>
              <th scope="row">{fecha}</th>
              <td>
                <Valor valor={registrado.ys[i] ?? null} unidad="kcal" />
              </td>
              <td>
                <Valor valor={previsto.ys[i] ?? null} unidad="kcal" />
              </td>
              <td>
                <Valor valor={objetivo.ys[i] ?? null} unidad="kcal" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <LeyendaDeSeries
        registrado={registrado}
        previsto={previsto}
        objetivo={objetivo}
        nota={nota}
      />
    </div>
  )
}
