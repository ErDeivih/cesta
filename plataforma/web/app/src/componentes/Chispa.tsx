/** La chispa del historico: una serie de precio por unidad, sin ejes.
 *
 *  **Un hueco es un hueco.** Un `null` entre dos precios es un dia que no se observo, y la chispa
 *  **no lo conecta**: `spanGaps: false`. Lo pide G05 con estas palabras -- *«no conectar datos
 *  ausentes como si hubiera observaciones»* --, y antes de este cambio la linea recta entre dos
 *  puntos afirmaba un precio que nadie midio. **Lo que no se sabe se ve que no se sabe**, que es
 *  justo para lo que sirve un hueco en un adorno de 40 px.
 *
 *  uPlot y no Recharts: un solo trazo, 40 px de alto y cuarenta de ellos en una
 *  pantalla. uPlot son ~50 KB, pinta en canvas y no toca el DOM por punto.
 *  Recharts mete d3 y un SVG por grafica; con cuarenta en una lista, eso se
 *  nota al deslizar. La chispa es un adorno del dato, no el dato: los numeros
 *  (minimo, maximo, media) van siempre escritos al lado.
 */
import { useEffect, useRef, useState } from 'react'
import { filasDeChispa, serieDeChispa, type PuntoChispa } from '../logica/chispa'
import { Resumen } from './ui'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'

export type { PuntoChispa } from '../logica/chispa'

interface Props {
  puntos: PuntoChispa[]
  alto?: number
  color?: string
  /** Que se esta mirando, para el texto alternativo. */
  etiqueta: string
}


export function Chispa({ puntos, alto = 40, color = '#0369a1', etiqueta }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafica = useRef<uPlot | null>(null)
  const [ancho, setAncho] = useState(0)

  // El ancho se mide, no se supone: en el movil la columna de una cadena mide
  // 260 px y en el escritorio 380. Un canvas de ancho fijo se sale o deja un
  // hueco, y las dos cosas se ven.
  useEffect(() => {
    const el = contenedor.current
    if (!el) return
    const observa = new ResizeObserver((entradas) => {
      const caja = entradas[0]?.contentRect
      if (caja) setAncho(Math.max(60, Math.round(caja.width)))
    })
    observa.observe(el)
    return () => observa.disconnect()
  }, [])

  // La dependencia es una clave de texto y no el array: si el padre lo recrea
  // en cada pintada (que es lo normal), la grafica se destruiria y se volveria
  // a crear cuarenta veces por segundo y el raton no podria ni pasar por encima.
  const clave = puntos.map((p) => `${p.fecha}:${p.valor ?? ''}`).join('|')

  useEffect(() => {
    const el = contenedor.current
    if (!el || ancho < 20 || puntos.length === 0) return

    // **Que se dibuja lo decide `logica/chispa.ts`**, que es puro y esta probado: las reglas de
    // huecos, fechas ilegibles y series vacias son de G05 y no se deciden aqui.
    const serie = serieDeChispa(puntos)
    if (!serie.dibujable) return
    const { xs, ys } = serie

    const opciones: uPlot.Options = {
      width: ancho,
      height: alto,
      padding: [3, 3, 3, 3],
      legend: { show: false },
      cursor: { show: false, x: false, y: false },
      scales: {
        // `time: false` porque el eje no se pinta: solo se necesita el orden.
        x: { time: false },
        y: {
          // Un solo punto (o todos iguales) da un rango de cero y uPlot divide
          // por el. Se abre a mano alrededor del valor.
          range: (_u, min, max) => {
            if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1]
            if (max - min < 1e-9) return [min - 1, max + 1]
            const margen = (max - min) * 0.2
            return [min - margen, max + margen]
          },
        },
      },
      axes: [{ show: false }, { show: false }],
      series: [
        {},
        {
          stroke: color,
          width: 2,
          // **Un hueco se ve como hueco**: ver la cabecera del fichero.
          spanGaps: false,
          // Un unico punto sin `points` no dibuja nada y parece que no hay
          // historico, que es justo lo contrario de lo que pasa.
          points: { show: puntos.length <= 1, size: 5, width: 0, fill: color },
        },
      ],
    }

    const nueva = new uPlot(opciones, [xs, ys] as uPlot.AlignedData, el)
    grafica.current = nueva
    return () => {
      nueva.destroy()
      grafica.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clave, ancho, alto, color])

  // **Si la serie mezcla unidades, no se dibuja una linea que las junte.** Mismo criterio y las
  // mismas palabras que `logica/curva.ts`: un minimo sobre `kg` y `ud` juntos no es el minimo de
  // nada. *La chispa era la unica pieza del sistema que lo ignoraba.*
  const unidades = serieDeChispa(puntos)
  if (!unidades.dibujable && unidades.motivoUnidad) {
    return <p className="text-xs text-tinta-suave">{unidades.motivoUnidad}</p>
  }

  if (puntos.length === 0) {
    return (
      // **No se infiere nada de una serie vacia.** Antes decia «solo tenemos un dia de este
       // precio», que es una afirmacion sobre el catalogo sacada de **no tener datos**: un producto
       // con cuarenta dias de historico y una consulta que falla decia exactamente lo mismo. G05:
       // *«no inferir "solo un dia" de una serie vacia»*. Se dice lo que se sabe: que no hay serie.
      <p className="text-xs text-tinta-suave">
        Sin serie de precios que dibujar.
      </p>
    )
  }

  const filas = filasDeChispa(puntos)
  const huecos = filas.filter((f) => f.valor === null).length

  return (
    <div className="w-full">
      {/* La chispa es el adorno; **el dato esta aqui**, y en una tabla que se puede leer con un
          lector de pantalla y con el teclado. La aceptacion de G05 lo pide: *«tabla accesible de los
          mismos datos»*.
          **Los huecos van dentro**, y se leen «sin dato»: una tabla que los omitiera escondería
          justo lo que la chispa ha dejado de tapar al no conectar los puntos. */}
      <div
        ref={contenedor}
        className="w-full"
        role="img"
        aria-label={`${etiqueta}: ${puntos.length} días de histórico` +
          (huecos > 0 ? `, ${huecos} sin dato` : '')}
      />
      <details className="mt-1">
        {/* **`Resumen` y no un `<summary>` a mano**: con `display: flex` -- que hace falta para
            los 44 px de pulsar -- el navegador deja de pintar su triangulo, y un desplegable sin
            flecha parece un encabezado suelto. Lo vigila `test_ui_movil.py`, y con razon: *lo
            encontraron mirando una captura, no leyendo el codigo.* */}
        <Resumen className="text-xs text-tinta-suave">
          {`Ver los ${puntos.length} días como tabla` +
            (huecos > 0 ? ` (${huecos} sin dato)` : '')}
        </Resumen>
        <table className="mt-1 w-full text-xs tabular-nums">
          <caption className="sr-only">{`${etiqueta}: precio por día`}</caption>
          <thead>
            <tr>
              <th scope="col" className="text-left font-medium">Día</th>
              <th scope="col" className="text-right font-medium">Precio</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.fecha}>
                <td className="text-left">{f.fecha}</td>
                <td className={`text-right ${f.valor === null ? 'text-tinta-suave' : ''}`}>
                  {f.texto}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}
