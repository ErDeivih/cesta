/** La explicacion del emparejamiento, **si el dato esta disponible**.
 *
 *  Hoy no lo esta: `/api/grupo` no manda ningun campo que diga por que dos
 *  productos acabaron en el mismo grupo (`core/matching.py` lo calcula, pero no
 *  viaja en la respuesta). Asi que esto no inventa una explicacion: busca los
 *  nombres plausibles del campo y, si no hay ninguno, **lo dice**.
 *
 *  Inventar aqui un "emparejado por nombre parecido" seria justo lo que este
 *  proyecto evita: un dato que no tenemos presentado como si lo tuvieramos.
 */
import type { Grupo } from '../tipos'
import { numero } from '../api/formato'
import { Aviso, Etiqueta } from './ui'

/** Los nombres que podria tener el campo el dia que se implemente. */
const POSIBLES_CAMPOS = [
  'matching',
  'explicacion',
  'explicacion_emparejamiento',
  'emparejado_por',
  'metodo_emparejamiento',
  'por_que',
  'parecido',
] as const

function busca(grupo: Grupo): { campo: string; valor: unknown } | null {
  const crudo = grupo as unknown as Record<string, unknown>
  for (const campo of POSIBLES_CAMPOS) {
    const valor = crudo[campo]
    if (valor !== undefined && valor !== null) return { campo, valor }
  }
  return null
}

/** Un valor suelto, en texto. Los booleanos en castellano: la explicacion se lee
 *  para decidir si el emparejamiento es de fiar, y `false` no es una palabra. */
function textoDe(valor: unknown): string | null {
  if (typeof valor === 'boolean') return valor ? 'sí' : 'no'
  // Los numeros con la coma decimal de aqui: la confianza es 0,59, no 0.59.
  if (typeof valor === 'number') return numero(valor, 2)
  if (typeof valor === 'string') return valor
  return null
}

/** Los pares de dentro de un texto que lleva un objeto JSON, o `null`.
 *
 *  `features` llega asi: `{"parecido": 0.58, "marca_igual": false}`. Ensenarlo
 *  tal cual es esconder el dato detras de su formato, y esta seccion existe justo
 *  para lo contrario: poder ver que ese 0,58 viene de que la marca no coincide y
 *  la cantidad si. */
function dentroDelTexto(texto: string): [string, string][] | null {
  const limpio = texto.trim()
  if (!limpio.startsWith('{') || !limpio.endsWith('}')) return null
  try {
    const salida: [string, string][] = []
    for (const [clave, valor] of Object.entries(JSON.parse(limpio) as Record<string, unknown>)) {
      const texto2 = textoDe(valor)
      if (texto2 !== null) salida.push([clave, texto2])
    }
    return salida.length > 0 ? salida : null
  } catch {
    // Un texto que empieza por `{` y no es JSON se ensena como lo que es: texto.
    return null
  }
}

function escalares(valor: unknown): [string, string][] {
  if (typeof valor !== 'object' || valor === null) return []
  const salida: [string, string][] = []
  for (const [k, v] of Object.entries(valor as Record<string, unknown>)) {
    if (v === null || v === undefined) continue
    const dentro = typeof v === 'string' ? dentroDelTexto(v) : null
    if (dentro) {
      // Las claves de dentro llevan delante de donde salen (`features.parecido`),
      // para que no se confundan con las de fuera.
      for (const [k2, v2] of dentro) salida.push([`${k}.${k2}`, v2])
      continue
    }
    const texto = textoDe(v)
    if (texto !== null) salida.push([k, texto])
  }
  return salida
}

export function ExplicacionEmparejamiento({ grupo }: { grupo: Grupo }) {
  const encontrado = busca(grupo)

  if (!encontrado) {
    return (
      <Aviso tono="info" titulo="Aquí todavía no hay nada que enseñar">
        <p>
          La API no manda la explicación del emparejamiento. El grupo existe y sus miembros están
          emparejados, pero no viaja el <em>por qué</em>: en <code>/api/grupo</code> no hay ningún
          campo con el método ni con la puntuación de parecido.
        </p>
        <p className="mt-1">
          Esta sección se rellena sola el día que la respuesta traiga uno de estos campos:{' '}
          {/* Cada nombre va en su propio `inline-block`: JSX se come el espacio
              entre elementos y siete `<code>` pegados son una sola palabra
              impartible de 800 px que revienta el ancho de la página en un
              móvil. Con `inline-block` vuelven a poder partirse de línea. */}
          {POSIBLES_CAMPOS.map((c) => (
            <span key={c} className="mr-1 inline-block">
              <code>{c}</code>
            </span>
          ))}
        </p>
      </Aviso>
    )
  }

  const { campo, valor } = encontrado
  const pares = escalares(valor)

  return (
    <div className="grid grid-cols-1 gap-2">
      <p className="text-sm">
        <Etiqueta tono="info">{campo}</Etiqueta>
      </p>
      {typeof valor === 'string' ? (
        <p className="text-sm">{valor}</p>
      ) : pares.length > 0 ? (
        <dl className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
          {pares.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2 border-b border-neutral-100 py-0.5 dark:border-neutral-700">
              <dt className="text-neutral-600 dark:text-neutral-400">{k}</dt>
              <dd className="cifra font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      <details>
        <summary className="cursor-pointer text-xs text-sky-800 dark:text-sky-400">
          Ver el dato en crudo
        </summary>
        <pre className="mt-1 overflow-x-auto rounded-lg bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
          {JSON.stringify(valor, null, 2)}
        </pre>
      </details>
    </div>
  )
}
