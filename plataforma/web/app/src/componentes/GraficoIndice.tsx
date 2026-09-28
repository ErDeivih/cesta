/** El índice de precios por cadena, con sus cinco series.
 *
 *  **SVG a mano y no uPlot, al revés que la chispa del histórico.** Son cinco series
 *  y catorce puntos que se pintan una vez al abrir la pestaña: uPlot se come 50 KB
 *  para esto y además la chispa va sin ejes (`Chispa.tsx`: `time: false`), así que
 *  no serviría sin reescribirla. Aquí hacen falta el eje de fechas, el 100 de
 *  referencia y las etiquetas del final.
 *
 *  Y **la tabla de debajo no es un extra**: cinco colores no se distinguen ni con
 *  buena vista, y tres de los que usaba la interfaz vieja no llegaban a 3:1 de
 *  contraste contra el fondo claro. El dibujo ayuda a ver la tendencia; el número
 *  que se lee es el de la tabla. Por eso este componente **no** decide nada: pinta
 *  lo que le dan y no calcula ni un dato.
 */
import { fecha as fechaLegible, nombreCadena, numero, porcentajeConSigno } from '../api/formato'
import type { SerieIndice } from '../tipos'

/** Los cinco colores de las cadenas, con nombre y no un índice al aire.
 *
 *  Están en la escala de 600/700 para que aguanten el fondo claro y el oscuro: el
 *  mismo tono que usa el resto de la aplicación para las etiquetas de cadena. */
const COLORES: Record<string, string> = {
  alcampo: '#b45309',
  aldi: '#1d4ed8',
  carrefour: '#0f766e',
  dia: '#be123c',
  mercadona: '#7e22ce',
}

const RESERVA = '#6b7280'

export function colorDeCadena(cadena: string): string {
  return COLORES[cadena] ?? RESERVA
}

interface Props {
  series: SerieIndice[]
  alto?: number
}

export function GraficoIndice({ series, alto = 240 }: Props) {
  const conPuntos = series.filter((s) => s.puntos.length > 0)
  if (conPuntos.length === 0) {
    return (
      <p className="text-sm text-tinta-suave">
        Todavía no hay dos capturas que comparar: el índice empieza a moverse en la segunda.
      </p>
    )
  }

  const ancho = 640
  const margen = { arriba: 12, derecha: 64, abajo: 26, izquierda: 44 }
  const fechas = [...new Set(conPuntos.flatMap((s) => s.puntos.map((p) => p.fecha)))].sort()
  const valores = conPuntos.flatMap((s) => s.puntos.map((p) => p.indice))
  // El 100 entra siempre en la escala: es la referencia, no una serie. Si se
  // recortara a los valores, "ha bajado" y "ha subido" se leerían al revés.
  let lo = Math.min(100, ...valores)
  let hi = Math.max(100, ...valores)
  const aire = Math.max(0.25, (hi - lo) * 0.18)
  lo -= aire
  hi += aire

  const x = (f: string) =>
    margen.izquierda +
    (fechas.indexOf(f) / Math.max(1, fechas.length - 1)) *
      (ancho - margen.izquierda - margen.derecha)
  const y = (v: number) =>
    margen.arriba + (1 - (v - lo) / (hi - lo)) * (alto - margen.arriba - margen.abajo)

  const rejilla = [0, 1, 2, 3, 4].map((k) => {
    const v = lo + ((hi - lo) * k) / 4
    return (
      <g key={`r${k}`}>
        <line
          x1={margen.izquierda}
          x2={ancho - margen.derecha}
          y1={y(v)}
          y2={y(v)}
          className="stroke-neutral-200 dark:stroke-neutral-700"
          strokeWidth={1}
        />
        <text x={margen.izquierda - 7} y={y(v) + 3.5} textAnchor="end" className="fill-current text-[9px]">
          {numero(v, 1)}
        </text>
      </g>
    )
  })

  /* Los eslabones que cubren mas de un dia, de todas las series: el indice esta encadenado dia a
     dia, y donde la cadena no se rastreo el eslabon salta. Se dicen **con sus dos fechas** -- «del
     11 al 13» --, que es lo unico que permite ir a mirar por que falta ese dia; decir solo el dia
     al que llega el eslabon deja la duda de cual es el que falta. */
  const saltos = conPuntos.flatMap((s) =>
    s.puntos.flatMap((p, i) =>
      (p.dias_del_salto ?? 1) > 1
        ? [{ cadena: s.cadena, dias: p.dias_del_salto, desde: s.puntos[i - 1]?.fecha ?? null,
             hasta: p.fecha }]
        : [],
    ),
  )

  const cadaCuanto = Math.ceil(fechas.length / 5)
  const ejeX = fechas.map((f, i) =>
    i % cadaCuanto === 0 || i === fechas.length - 1 ? (
      <text key={f} x={x(f)} y={alto - 8} textAnchor="middle" className="fill-current text-[9px]">
        {f.slice(8)}/{f.slice(5, 7)}
      </text>
    ) : null,
  )

  /* Las etiquetas del final se pisan entre ellas cuando cinco cadenas caen en dos
     décimas: se separan lo justo **manteniendo el orden**, que es como se lee cuál
     es cuál sin depender del color. */
  const finales = conPuntos
    .map((s) => {
      const u = s.puntos[s.puntos.length - 1]
      return { cadena: s.cadena, fecha: u.fecha, valor: u.indice, yReal: y(u.indice), yEtiqueta: y(u.indice) }
    })
    .sort((a, b) => a.yEtiqueta - b.yEtiqueta)
  const HUECO = 11
  for (let i = 1; i < finales.length; i++) {
    if (finales[i].yEtiqueta - finales[i - 1].yEtiqueta < HUECO) {
      finales[i].yEtiqueta = finales[i - 1].yEtiqueta + HUECO
    }
  }
  const exceso = finales.length ? finales[finales.length - 1].yEtiqueta - (alto - margen.abajo) : 0
  if (exceso > 0) finales.forEach((f) => (f.yEtiqueta -= exceso))

  const trazos = conPuntos.map((s) => {
    const color = colorDeCadena(s.cadena)
    const d = s.puntos
      .map((p, i) => `${i ? 'L' : 'M'}${x(p.fecha).toFixed(1)},${y(p.indice).toFixed(1)}`)
      .join('')
    const f = finales.find((z) => z.cadena === s.cadena)
    const ultimo = s.puntos[s.puntos.length - 1]
    const px = x(ultimo.fecha)
    const guia =
      f && Math.abs(f.yEtiqueta - f.yReal) > 2 ? (
        <line
          x1={px + 5}
          y1={f.yReal}
          x2={px + 9}
          y2={f.yEtiqueta - 3.5}
          stroke={color}
          strokeWidth={1}
          opacity={0.55}
        />
      ) : null
    return (
      <g key={s.cadena}>
        <path d={d} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {/* **El eslabón que cubre mas de un dia, marcado.** El indice esta encadenado dia a dia,
            y donde la cadena no se rastreo un dia el eslabon salta: el dibujo hacia como si
            hubiera visto todos los dias. La interfaz vieja lo decia (`app.js:1020`, «el eslabon
            cubre N dias» en un `title`) y la nueva no lo pintaba: `dias_del_salto` viajaba en
            `/api/indice` y se tiraba. Medido el 28 de septiembre de 2026: **cinco eslabones** de
            la serie (Alcampo el 13 y el 23, Carrefour el 13, el 19 y el 23), de 2 y 3 dias. */}
        {s.puntos
          .filter((p) => (p.dias_del_salto ?? 1) > 1)
          .map((p) => (
            <circle
              key={`salto-${p.fecha}`}
              cx={x(p.fecha)}
              cy={y(p.indice)}
              r={4.5}
              fill="none"
              stroke={color}
              strokeWidth={1.5}
            />
          ))}
        <circle cx={px} cy={y(ultimo.indice)} r={3.5} fill={color} />
        {guia}
        <text x={px + 10} y={(f?.yEtiqueta ?? y(ultimo.indice)) + 3.5} className="fill-current text-[9px]">
          {numero(ultimo.indice, 1)}
        </text>
      </g>
    )
  })

  return (
    <div className="grid grid-cols-1 gap-2">
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        className="h-auto w-full text-tinta-suave"
        role="img"
        aria-label={`Índice de precios por cadena, ${conPuntos.length} cadenas, base 100`}
      >
        {rejilla}
        <line
          x1={margen.izquierda}
          x2={ancho - margen.derecha}
          y1={y(100)}
          y2={y(100)}
          className="stroke-neutral-400 dark:stroke-neutral-500"
          strokeWidth={1}
          strokeDasharray="4 3"
        />
        {ejeX}
        {trazos}
      </svg>
      {/* La leyenda es el mapa entre color y cadena. Va con el nombre escrito
          porque un color solo no dice cuál es cuál. */}
      <ul className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {conPuntos.map((s) => (
          <li key={s.cadena} className="flex items-center gap-1.5">
            <i
              aria-hidden
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ background: colorDeCadena(s.cadena) }}
            />
            <span>
              {nombreCadena(s.cadena)} {porcentajeConSigno(s.variacion_pct)} ({s.capturas}{' '}
              {s.capturas === 1 ? 'captura' : 'capturas'})
            </span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-tinta-suave">
        Del {fechaLegible(fechas[0], true)} al {fechaLegible(fechas[fechas.length - 1], true)}. El
        dibujo ayuda a ver la tendencia; los números que se leen son los de la tabla.
        {saltos.length > 0 && (
          <>
            {' '}
            <strong className="font-medium">
              {saltos.length === 1
                ? 'Un eslabón cubre más de un día'
                : `${saltos.length} eslabones cubren más de un día`}
            </strong>{' '}
            (los del círculo hueco): esos días no se rastrearon, así que el índice se movió sin
            haberlos visto. Son{' '}
            {saltos
              .map((p) => `${nombreCadena(p.cadena)} ${p.desde
                ? `del ${fechaLegible(p.desde, true)} al `
                : ''}${fechaLegible(p.hasta, true)} (${numero(p.dias, 0)} días)`)
              .join(', ')}
            .
          </>
        )}
      </p>
    </div>
  )
}
