/** **La leyenda y la tabla accesible de las tres series** -- registrado, previsto y objetivo.
 *
 * ***Y la leyenda dice CUANTAS series hay.*** *Si el objetivo no existe, son **dos**, y se dice con la
 * palabra `sin_objetivo` -- *no con una linea por el cero: **un dia sin objetivo no es un dia de 0 kcal.** *
 *
 * **La tabla no es un adorno.** `chispa.ts:93` ya lo dice: *«la aceptacion de G05 pide **«tabla accesible de
 * los mismos datos»**, y aqui "los mismos" incluye **lo que no hay**: una tabla que omitiera las fechas sin
 * precio haria invisible justo el hueco que la chispa ha dejado de tapar.» *
 *
 * **Y por eso cada fila lleva `dibujados` Y `total`**: ***sin las dos cifras, un hueco y una ausencia se ven
 * igual*** *-- *y es la misma regla de `Diario.tsx`: «las dos cifras van juntas».*
 */
import type { SerieDeChispa } from '../logica/chispa'

export type NombreDeSerie = 'registrado' | 'previsto' | 'objetivo'

export interface PropsDeLeyenda {
  registrado: SerieDeChispa
  previsto: SerieDeChispa
  objetivo: SerieDeChispa
  /** ***`sin_objetivo` cuando no lo hay*** -- *y entonces la grafica tiene DOS series, y lo dice.* */
  nota: 'tres_series' | 'sin_objetivo' | 'sin_nada'
}

const NOMBRE: Record<NombreDeSerie, string> = {
  registrado: 'Registrado',
  previsto: 'Previsto',
  objetivo: 'Objetivo',
}

/** *Lo que hay que decir de una serie, y **nada mas**.* */
function QueSeDibuja({ serie, s }: { serie: NombreDeSerie; s: SerieDeChispa }) {
  if (!s.dibujable) {
    // *Y **no se dice «0 puntos»**: se dice que **no hay serie** -- que es lo que `dibujable: false`
    // significa, y no «un solo dia».*
    return <span>sin serie</span>
  }
  return (
    <span>
      {s.dibujados} de {s.total}
      {s.sinFecha > 0 && <> · {s.sinFecha} sin fecha</>}
      {s.motivoUnidad && <> · {s.motivoUnidad}</>}
    </span>
  )
}

export function LeyendaDeSeries({ registrado, previsto, objetivo, nota }: PropsDeLeyenda) {
  const series: [NombreDeSerie, SerieDeChispa][] = [
    ['registrado', registrado],
    ['previsto', previsto],
    ['objetivo', objetivo],
  ]
  const dibujables = series.filter(([, s]) => s.dibujable).length

  return (
    <div>
      <p>
        {nota === 'sin_nada'
          ? 'No hay ninguna serie que dibujar: no hay datos en estas fechas.'
          : nota === 'sin_objetivo'
            ? `Dos series: ${dibujables} de 3. No hay objetivo puesto para estas fechas.`
            : `Tres series: ${dibujables} de 3.`}
      </p>

      {/* *La tabla, con los mismos datos que la grafica -- y con lo que NO hay.* */}
      <table>
        <caption>Lo que se dibuja en cada serie, y lo que se queda fuera</caption>
        <thead>
          <tr>
            <th scope="col">Serie</th>
            <th scope="col">Se dibuja</th>
          </tr>
        </thead>
        <tbody>
          {/* *Y el objetivo entra **aunque no se dibuje**: callarlo seria decir que no se pidio, y si se
              pidio y no hay, hay que poder verlo.* */}
          {series.map(([serie, s]) => (
            <tr key={serie}>
              <th scope="row">{NOMBRE[serie]}</th>
              <td>
                <QueSeDibuja serie={serie} s={s} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
