/** *** EL MISMO PRODUCTO, CADA SUPERMERCADO Y SU PRECIO POR UNIDAD. *** *
 *
 *  *La lista enseña el precio más barato de cada producto y su €/kg; lo que no dice es **dónde
 *  está cada precio**. Este panel despliega el grupo entero: una fila por supermercado, con su
 *  precio de venta y su precio por unidad, ordenadas de menor a mayor €/unidad.*
 *
 *  *Se pide al abrir, no al pintar la fila: cuarenta grupos en una búsqueda son cuarenta
 *  peticiones que casi nadie mira. La respuesta queda en la caché de React Query (`staleTime` de
 *  cinco minutos), así que abrir y cerrar no repite la llamada.*
 *
 *  *El orden es por **precio por unidad**, no por precio de venta: un pack de 2 kg puede costar más
 *  y ser más barato por kilo, y esa es justo la comparación que la app existe para hacer.*
 */
import { useGrupo } from '../api/consultas'
import { euros, eurosUnidad, nombreCadena, porcentaje } from '../api/formato'
import type { Producto } from '../tipos'
import { Etiqueta } from './ui'

/** Los precios por supermercado de un grupo, ordenados por precio por unidad. */
export function OfertasDelProducto({ grupoId, nombre }: { grupoId: number; nombre: string }) {
  const grupo = useGrupo(grupoId)

  if (grupo.isPending) {
    return <p className="mt-1 text-etiqueta text-tinta-suave">Buscando precios por supermercado…</p>
  }
  if (grupo.isError) {
    return (
      <p className="mt-1 text-etiqueta text-tinta-suave">
        No he podido traer los precios.{' '}
        <button
          type="button"
          onClick={() => void grupo.refetch()}
          className="min-h-[44px] text-tinta-fuerte underline"
        >
          Reintentar
        </button>
      </p>
    )
  }

  // *Una fila por supermercado: si una cadena tiene dos formatos del mismo producto, se enseña su
  // opción más barata por unidad.* *Lo pidió la revisión sobre la captura: dos filas seguidas de
  // Carrefour con el mismo nombre parecían un duplicado. El detalle de todos los formatos está en
  // la ficha del grupo.*
  const porCadena = new Map<string, Producto & { precio_unidad_cent: number }>()
  for (const producto of grupo.data?.productos ?? []) {
    if (!producto.comparable || producto.precio_unidad_cent === null) continue
    const actual = porCadena.get(producto.fuente)
    if (!actual || producto.precio_unidad_cent < actual.precio_unidad_cent) {
      porCadena.set(producto.fuente, producto as Producto & { precio_unidad_cent: number })
    }
  }
  const productos = [...porCadena.values()].sort(
    (a, b) => a.precio_unidad_cent - b.precio_unidad_cent,
  )
  // *El más caro de los que se comparan: la referencia del ahorro de cada fila. Se coge
  // después de ordenar, así que es el último; con una sola cadena no hay ahorro que enseñar.*
  const masCaro = productos.length > 1
    ? productos[productos.length - 1].precio_unidad_cent
    : null

  if (productos.length === 0) {
    return (
      <p className="mt-1 text-etiqueta text-tinta-suave">
        No hay precios que se puedan comparar por unidad de este producto.
      </p>
    )
  }

  return (
    <div
      role="region"
      aria-label={`Precios de ${nombre} por supermercado`}
      className="mt-1 rounded-campo border border-borde bg-marfil p-2"
    >
      <p className="text-etiqueta text-tinta-suave">
        El más barato de cada supermercado ({productos.length}{' '}
        {productos.length === 1 ? 'cadena' : 'cadenas'}), de menor a mayor precio por unidad.
      </p>
      <ul className="mt-1 flex flex-col">
        {productos.map((producto) => (
          <li
            key={producto.producto_id}
            className="flex min-h-[44px] items-center justify-between gap-2 border-b border-borde py-1 last:border-0"
          >
            <span className="min-w-0">
              <span className="block text-cuerpo font-medium text-tinta-fuerte">
                {nombreCadena(producto.fuente)}
                {/* *La más barata, marcada. Con cinco cifras al lado, la marca ahorra la
                    comparación mental y dice cuál es la respuesta.* */}
                {producto.precio_unidad_cent === productos[0].precio_unidad_cent && (
                  <span className="ml-1 inline-block align-middle">
                    <Etiqueta tono="bien">más barata</Etiqueta>
                  </span>
                )}
              </span>
              <span className="block truncate text-etiqueta text-tinta-suave">
                {producto.nombre}
                {producto.marca ? ` · ${producto.marca}` : ''}
              </span>
            </span>
            <span className="cifra shrink-0 text-right text-etiqueta text-tinta-fuerte">
              {euros(producto.precio_cent)}
              <span className="block font-semibold text-tinta-suave">
                {eurosUnidad(producto.precio_unidad_cent, producto.unidad)}
              </span>
              {/* *** LO QUE TE AHORRAS FRENTE AL MÁS CARO, EN EUROS Y EN PORCENTAJE. *** *
               *Con solo el precio de cada cadena hay que restar a mano. La fila lo dice:
               *«ahorras 1,15 €/l (55,0 %)». En la más cara no se pinta, porque ahorra 0.* */}
              {masCaro !== null && producto.precio_unidad_cent < masCaro && (
                <span className="block font-normal text-tinta-tenue">
                  ahorras{' '}
                  {eurosUnidad(masCaro - producto.precio_unidad_cent, producto.unidad)} (
                  {porcentaje(((masCaro - producto.precio_unidad_cent) / masCaro) * 100)})
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      {(grupo.data?.ahorro_cent ?? 0) > 0 && (
        <p className="mt-1 text-etiqueta text-tinta-suave">
          Entre el más barato y el más caro hay{' '}
          {eurosUnidad(grupo.data?.ahorro_cent, grupo.data?.unidad)} de diferencia (
          {porcentaje(grupo.data?.ahorro_pct)}), siempre con la misma unidad.
        </p>
      )}
    </div>
  )
}
