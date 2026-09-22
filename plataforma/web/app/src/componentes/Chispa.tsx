/** La chispa del historico: una serie de precio por unidad, sin ejes.
 *
 *  uPlot y no Recharts: un solo trazo, 40 px de alto y cuarenta de ellos en una
 *  pantalla. uPlot son ~50 KB, pinta en canvas y no toca el DOM por punto.
 *  Recharts mete d3 y un SVG por grafica; con cuarenta en una lista, eso se
 *  nota al deslizar. La chispa es un adorno del dato, no el dato: los numeros
 *  (minimo, maximo, media) van siempre escritos al lado.
 */
import { useEffect, useRef, useState } from 'react'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'

export interface PuntoChispa {
  fecha: string
  valor: number | null
}

interface Props {
  puntos: PuntoChispa[]
  alto?: number
  color?: string
  /** Que se esta mirando, para el texto alternativo. */
  etiqueta: string
}

function aMs(fecha: string): number {
  const t = new Date(fecha.length <= 10 ? `${fecha}T00:00:00` : fecha).getTime()
  return Number.isNaN(t) ? 0 : t
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

    const xs = puntos.map((p) => aMs(p.fecha))
    const ys = puntos.map((p) => (p.valor === null || !Number.isFinite(p.valor) ? null : p.valor))

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
          spanGaps: true,
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

  if (puntos.length === 0) {
    return (
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        Sin histórico: solo tenemos un día de este precio.
      </p>
    )
  }

  return (
    <div
      ref={contenedor}
      className="w-full"
      role="img"
      aria-label={`${etiqueta}: ${puntos.length} días de histórico`}
    />
  )
}
