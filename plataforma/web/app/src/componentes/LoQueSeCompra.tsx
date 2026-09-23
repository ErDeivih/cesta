/** La primera vez: la aplicacion funcionando, con datos de verdad.
 *
 *  Punto 1 del encargo, y el que Claude pone por delante de todos: *"Cuando un amigo
 *  se registra ve un buscador vacio, una cesta vacia y un panel de indices que no
 *  significa nada. Es el peor momento de la aplicacion y el unico que todo el mundo
 *  ve."*
 *
 *  **Se arregla ensenando la aplicacion funcionando**, no con una visita guiada: si
 *  lo primero que se ve son cuatro productos que compra todo el mundo **con la
 *  diferencia de hoy**, ya se entiende para que sirve esto sin que nadie lo explique.
 *  Una guia se lee una vez; cuatro precios reales se entienden solos.
 *
 *  De donde salen: de cuatro busquedas de cosas basicas contra `/api/buscar`, que es
 *  lo que **hoy funciona en produccion**. El dia que `/api/habituales` responda se
 *  puede usar su compra basica, que ya resuelve los nombres en el servidor; hasta
 *  entonces, esto no espera a nadie.
 *
 *  Dos reglas del proyecto que estan aqui dentro:
 *
 *  - **Nada de datos inventados.** Si una busqueda no devuelve nada --o devuelve algo
 *    que no se puede comparar-- ese hueco no se rellena: se ensenan los que haya, y
 *    si no hay ninguno, el componente **no pinta nada** y deja el buscador como
 *    estaba. Un ejemplo falso ensena a desconfiar de la aplicacion justo el primer
 *    dia, que es cuando mas caro sale.
 *  - **La diferencia es de verdad**: sale de restar el precio por unidad de la cadena
 *    mas barata al de la mas cara del grupo, no de un `ahorro` que venga sumado por
 *    otro sitio. Si el grupo no es comparable, no se anuncia ahorro.
 */
import { useQueries } from '@tanstack/react-query'

import { pide } from '../api/cliente'
import { eurosUnidad, nombreCadena } from '../api/formato'
import type { RespuestaBuscar, ResultadoBusqueda } from '../tipos'
import { Tarjeta } from './ui'

/** Lo que compra todo el mundo. Cuatro, no veinte: una cuadricula larga no se lee,
 *  y lo que tiene que quedar claro en dos segundos es que esto compara precios. */
const BASICOS = ['leche entera', 'pan de molde', 'huevos', 'aceite de oliva']

/** La diferencia entre la cadena mas barata y la mas cara, en %. */
function diferencia(r: ResultadoBusqueda): number | null {
  const barato = r.precio_unidad_cent
  const caro = r.precio_unidad_max_cent
  if (barato == null || caro == null || barato <= 0 || caro <= barato) return null
  return Math.round((100 * (caro - barato)) / barato)
}

export function LoQueSeCompra() {
  const consultas = useQueries({
    queries: BASICOS.map((q) => ({
      queryKey: ['primera-vez', q],
      queryFn: () => pide<RespuestaBuscar>('/buscar', { q, limite: 1 }),
      // Un dia entero: esto es una muestra de la aplicacion, no un dato que haya que
      // refrescar mientras alguien mira. Y asi cuatro busquedas no se repiten cada
      // vez que se vuelve al buscador.
      staleTime: 24 * 60 * 60 * 1000,
    })),
  })

  const ejemplos = consultas
    .map((c) => c.data?.resultados?.[0])
    .filter((r): r is ResultadoBusqueda => Boolean(r && r.comparable))

  // Sin ejemplos no se pinta nada: mejor el buscador pelado que cuatro tarjetas
  // vacias o un ejemplo inventado.
  if (ejemplos.length === 0) return null

  return (
    <Tarjeta>
      <p className="text-sm text-tinta-suave">
        Esto compara el precio del mismo producto entre cinco supermercados. Un
        ejemplo de hoy:
      </p>
      <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ejemplos.map((r) => {
          const pct = diferencia(r)
          return (
            <li key={r.grupo_id ?? r.nombre} className="flex flex-col gap-1">
              {r.imagen && (
                <img
                  src={r.imagen}
                  alt=""
                  width={96}
                  height={96}
                  loading="lazy"
                  className="h-24 w-24 rounded-lg border border-neutral-200 bg-white object-contain dark:border-neutral-700"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              )}
              <span className="text-sm font-medium leading-snug">{r.nombre}</span>
              <span className="cifra text-lg font-semibold">
                {eurosUnidad(r.precio_unidad_cent, r.unidad)}
              </span>
              <span className="text-sm text-tinta-suave">
                {r.cadena_mas_barata ? `en ${nombreCadena(r.cadena_mas_barata)}` : 'la mas barata'}
                {pct != null && pct > 0 && ` · un ${pct} % menos`}
              </span>
            </li>
          )
        })}
      </ul>
    </Tarjeta>
  )
}
