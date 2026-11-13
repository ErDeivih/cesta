/** *** EL BUSCADOR DE PRODUCTO, SIN SALIR DE LA LISTA. *** *
 *
 *  *Hasta hoy, apuntar algo que no estaba en la lista obligaba a pulsar «Añadir producto» y
 *  salir a `/compra`: buscar era otra pantalla, y volver a la lista era otro viaje.*
 *
 *  Pieza de comportamiento: **`Combobox` de `@ui-sdk/react/combobox`** (combobox WAI-ARIA con
 *  `aria-expanded`, `aria-controls`, `aria-activedescendant`, flechas, Inicio/Fin, Enter y Escape)
 *  y **`useAsyncOptions` de `@ui-sdk/react/async-options`** para la búsqueda con retardo y el
 *  descarte de respuestas viejas.
 *
 *  *Las opciones se montan como partes (`ComboboxItem`), no como datos (`items`).* *Con `items`
 *  vacío al abrir y los resultados llegando después, el resaltado de las flechas no se movía —
 *  medido con la prueba de teclado—; montadas como partes, la lista se recorre igual que cuando
 *  los resultados vienen con la primera pintada.*
 *
 *  Tres estados, además del normal: **error** (no se pudo buscar, con reintentar), **sin
 *  conexión** (se busca en lo último que se trajo) y **solo lectura** (una lista compartida para
 *  mirar no ofrece apuntar).
 */
import { useId, useRef, useState } from 'react'
import {
  Combobox, ComboboxContent, ComboboxInput, ComboboxItem, ComboboxLabel, ComboboxList,
  ComboboxTrigger,
} from '@ui-sdk/react/combobox'
import { useAsyncOptions } from '@ui-sdk/react/async-options'

import { buscarProductos } from '../../api/buscar'
import { eurosUnidad } from '../../api/formato'
import { useSinConexion } from '../../estado/conexion'
import type { ResultadoBusqueda } from '../../tipos'

/** Lo que se enseña de una sugerencia: el nombre y su precio por unidad. */
function precioDe(producto: ResultadoBusqueda): string {
  return eurosUnidad(producto.precio_unidad_cent, producto.unidad)
}

export function Typeahead({
  listaId,
  alElegir,
  etiqueta = 'Añadir a la lista',
  puedeEscribir = true,
  minimo = 2,
}: {
  /** La lista en la que se apunta. `null` es «todavía no hay lista»: la crea quien escucha. */
  listaId: string | null
  /** Apuntar el producto elegido. Puede fallar: la pantalla lo cuenta en una línea. */
  alElegir: (producto: ResultadoBusqueda) => Promise<void>
  etiqueta?: string
  /** En una lista compartida de solo mirar no se ofrece apuntar. */
  puedeEscribir?: boolean
  /** Letras mínimas antes de preguntar a la API. El buscador del catálogo pide dos. */
  minimo?: number
}) {
  const id = useId()
  const sinConexion = useSinConexion()
  const [consulta, setConsulta] = useState('')
  const [elegidos, setElegidos] = useState<string[]>([])
  const [errorAlApuntar, setErrorAlApuntar] = useState<string | null>(null)
  /** Lo último que trajo la red, para poder seguir apuntando sin cobertura. */
  const ultimos = useRef<ResultadoBusqueda[]>([])
  /** El producto de cada `value`: el combobox devuelve la identidad, no el objeto. */
  const porValor = useRef(new Map<string, ResultadoBusqueda>())
  /** Lo último que se escribió, para devolverlo al cerrar con Escape. */
  const ultimoTexto = useRef('')
  const restaurar = useRef(false)

  const red = useAsyncOptions<ResultadoBusqueda>(
    async (texto, { signal }) => {
      const limpio = texto.trim()
      if (limpio.length < minimo) return []
      const encontrados = await buscarProductos(limpio, 8, signal)
      ultimos.current = encontrados
      return encontrados
    },
    { debounce: 200 },
  )

  /** Sin red se busca donde se pueda: en lo último que se trajo, no en el vacío. */
  const resultados = sinConexion
    ? ultimos.current.filter((p) => {
        const aguja = consulta.trim().toLocaleLowerCase('es')
        return aguja.length >= minimo && (p.nombre ?? '').toLocaleLowerCase('es').includes(aguja)
      })
    : red.items

  porValor.current = new Map(resultados.map((p) => [String(p.grupo_id), p]))

  async function elegir(nuevos: string[]) {
    if (!nuevos.length) return
    const producto = porValor.current.get(nuevos[nuevos.length - 1])
    if (!producto) return
    // *Se vacía la selección para que el mismo producto se pueda volver a apuntar y para que el
    // campo quede limpio: apuntar es seguir apuntando, no cerrar y abrir.*
    setElegidos([])
    ultimoTexto.current = ''
    setErrorAlApuntar(null)
    try {
      await alElegir(producto)
    } catch {
      setErrorAlApuntar('No he podido apuntarlo. Vuelve a intentarlo.')
    }
  }

  if (!puedeEscribir) {
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={id} className="text-etiqueta font-medium text-secundaria">
          {etiqueta}
        </label>
        <input
          id={id}
          role="combobox"
          aria-disabled="true"
          aria-expanded="false"
          readOnly
          placeholder="Esta lista es de solo lectura"
          className="min-h-[44px] rounded-campo border border-borde bg-marfil px-3 py-2 text-tinta-suave"
        />
        <p className="text-etiqueta text-tinta-suave">
          Te la compartieron para mirar. Para apuntar, pide el papel de escribir.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      <Combobox
        multiple
        value={elegidos}
        onValueChange={(nuevos) => void elegir(nuevos as string[])}
        query={consulta}
        onQueryChange={(texto) => {
          if (texto !== '') ultimoTexto.current = texto
          if (texto === '' && restaurar.current) {
            // *Escape cierra la lista y **no borra lo escrito**: se vuelve a poner lo último que
            // se preguntó, que es lo que la persona tenía delante.*
            restaurar.current = false
            setConsulta(ultimoTexto.current)
            return
          }
          setConsulta(texto)
          // *Sin red no se pregunta: se busca en lo que ya está. Con red, la pregunta la
          // responde el catálogo con retardo y descartando respuestas viejas (`useAsyncOptions`).*
          if (!sinConexion) red.setQuery(texto)
        }}
        onOpenChange={(abierto) => {
          if (!abierto && ultimoTexto.current) {
            restaurar.current = true
            setConsulta(ultimoTexto.current)
          }
        }}
        filter={false}
        autoHighlight
        loop={false}
      >
        <ComboboxLabel>{etiqueta}</ComboboxLabel>
        <div className="flex items-center gap-2">
          <ComboboxInput
            placeholder="Escribe un producto…"
            className="min-h-[44px] min-w-0 flex-1 rounded-campo border border-borde-fuerte bg-papel px-3 py-2 text-tinta-fuerte"
          />
          <ComboboxTrigger
            aria-label="Mostrar sugerencias"
            className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-campo border border-borde-fuerte bg-papel text-tinta-suave"
          >
            <span aria-hidden="true">▾</span>
          </ComboboxTrigger>
        </div>
        <ComboboxContent className="max-h-[18rem] overflow-y-auto rounded-tarjeta border border-borde bg-papel p-1 shadow-hoja">
          <p role="status" className="px-3 py-2 text-etiqueta text-tinta-suave">
            {sinConexion ? (
              'Buscando en lo que ya tengo…'
            ) : red.status === 'error' ? (
              <span className="flex flex-wrap items-center gap-2">
                No he podido buscar.
                <button
                  type="button"
                  onClick={() => red.reload()}
                  className="min-h-[44px] text-tinta-fuerte underline"
                >
                  Reintentar
                </button>
              </span>
            ) : red.status === 'loading' ? (
              'Buscando…'
            ) : resultados.length > 0 ? (
              `${resultados.length} ${resultados.length === 1 ? 'resultado' : 'resultados'}`
            ) : null}
          </p>
          {resultados.length === 0 && red.status !== 'loading' && consulta.trim().length >= minimo && (
            <p className="px-3 py-2 text-etiqueta text-tinta-suave">
              Sin resultados para «{consulta.trim()}».
            </p>
          )}
          <ComboboxList className="flex flex-col">
            {resultados.map((producto) => (
              <ComboboxItem
                key={producto.grupo_id}
                value={String(producto.grupo_id)}
                label={producto.nombre}
                className="flex min-h-[44px] cursor-pointer items-center justify-between gap-3 rounded-campo px-3 py-1 data-[highlighted]:bg-marfil"
              >
                <span className="min-w-0">
                  <span className="block truncate text-cuerpo font-medium text-tinta-fuerte">
                    {producto.nombre}
                  </span>
                  {producto.marca && (
                    <span className="block text-etiqueta text-tinta-suave">{producto.marca}</span>
                  )}
                </span>
                <span className="cifra shrink-0 text-etiqueta font-medium text-tinta-fuerte">
                  {precioDe(producto)}
                </span>
              </ComboboxItem>
            ))}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>

      {errorAlApuntar && (
        <p role="alert" className="text-etiqueta text-error">
          {errorAlApuntar}
        </p>
      )}
      {sinConexion && (
        <p role="status" className="text-etiqueta text-tinta-suave">
          Sin conexión: busco en lo que ya tengo.
        </p>
      )}
      {listaId === null && (
        <p className="text-etiqueta text-tinta-suave">
          Se apunta en tu lista de casa, que se crea sola la primera vez.
        </p>
      )}
    </div>
  )
}
