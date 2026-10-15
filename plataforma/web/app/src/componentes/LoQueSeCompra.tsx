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
 *  y lo que tiene que quedar claro en dos segundos es que esto compara precios.
 *
 *  **Como se eligieron, y no fue a ojo.** Cada busqueda ensena solo su primer
 *  resultado, asi que ese primero tiene que ser un producto llano **cuyo nombre
 *  repita lo que se ha buscado**: si no, la tarjeta parece un error. Medido
 *  contra la API viva el 23 de septiembre de 2026:
 *
 *      /api/buscar?q=<lo de arriba>&limite=1
 *
 *      leche entera    -> «Leche entera»                        96 -> 167 cent
 *      pan de molde    -> «Pan de molde integral sin corteza»  233 -> 644 cent
 *      aceite de oliva -> «Aceite de oliva suave»              370 -> 519 cent
 *      agua mineral    -> «Agua mineral Dia 1,5 L»              18 ->  26 cent
 *
 *  Los cuatro salen `comparable: true`, que es lo que hace falta para poder
 *  decir una diferencia sin inventarla.
 *
 *  **`huevos` estuvo aqui y se quito**, por esto: su primer resultado es «Media
 *  tortilla de patata con cebolla», y una tarjeta que promete huevos y ensena
 *  una tortilla se lee como un fallo el primer dia, que es cuando mas caro
 *  sale. Que la busqueda de `huevos` ponga una tortilla la primera es un
 *  defecto de relevancia **aparte**, anotado en `docs/BACKLOG.md`, y no se
 *  tapa eligiendo otra palabra aqui.
 *
 *  Esto cambia con el dia, y esta bien: lo que se ensena es el catalogo de hoy,
 *  no una foto fija. Lo que **no** cambia es la regla de arriba -- y si un dia
 *  una de las cuatro deja de ser comparable, esa se cae sola y quedan tres. */
const BASICOS = ['leche entera', 'pan de molde', 'aceite de oliva', 'agua mineral']

/** La diferencia entre la cadena mas barata y la mas cara, en %. */
function diferencia(r: ResultadoBusqueda): number | null {
  const barato = r.precio_unidad_cent
  const caro = r.precio_unidad_max_cent
  if (barato == null || caro == null || barato <= 0 || caro <= barato) return null
  return Math.round((100 * (caro - barato)) / barato)
}

/** Sin tildes y en minusculas, para poder comparar un nombre con lo que se busco. */
function llano(texto: string): string {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

/** El primer resultado que **habla de lo que se ha buscado**.
 *
 *  No vale el primero a secas, y esto se vio en el navegador el 23 de septiembre de 2026:
 *  buscar "aceite de oliva" devolvia **«Picos sin gluten»** el primero, asi que la tarjeta
 *  de la primera vez -- lo unico que ve quien acaba de llegar -- ensenaba «Picos sin gluten
 *  13,90 €/kg · un 9 % menos» como ejemplo de comparar precios. Cualquiera que lo lea
 *  piensa que la aplicacion esta rota, y con razon.
 *
 *  La regla es la que ya estaba escrita para elegir los cuatro basicos: **el nombre tiene
 *  que repetir la palabra que se ha buscado** (la primera, que es el sustantivo: "leche",
 *  "pan", "aceite", "agua"). Se piden cinco resultados y se coge el primero que la cumpla;
 *  si ninguno la cumple, esa busqueda **no aporta nada** y se cae sola. Es la misma regla
 *  de siempre: un dato que no tenemos no se rellena con lo que haya al lado.
 */
function elQueHablaDe(r: ResultadoBusqueda, buscado: string): boolean {
  const palabra = llano(buscado).split(' ')[0] ?? ''
  return palabra.length >= 3 && llano(r.nombre).includes(palabra)
}

export function LoQueSeCompra() {
  const consultas = useQueries({
    queries: BASICOS.map((q) => ({
      queryKey: ['primera-vez', q],
      // Cinco y no uno: el primero puede no tener nada que ver (ver `elQueHablaDe`).
      queryFn: () => pide<RespuestaBuscar>('/buscar', { q, limite: 5 }),
      // Un dia entero: esto es una muestra de la aplicacion, no un dato que haya que
      // refrescar mientras alguien mira. Y asi cuatro busquedas no se repiten cada
      // vez que se vuelve al buscador.
      staleTime: 24 * 60 * 60 * 1000,
    })),
  })

  const ejemplos = BASICOS
    .map((q, i) => {
      const candidatos = consultas[i]?.data?.resultados ?? []
      return candidatos.find((r) => r.comparable && elQueHablaDe(r, q))
    })
    .filter((r): r is ResultadoBusqueda => Boolean(r))

  // Sin ejemplos no se pinta nada: mejor el buscador pelado que cuatro tarjetas
  // vacias o un ejemplo inventado.
  if (ejemplos.length === 0) return null

  return (
    <Tarjeta>
      <p className="text-cuerpo text-tinta-suave">
        Esto compara precios por unidad de grupos de productos entre supermercados.
        Los grupos pueden incluir marcas y formatos diferentes. Un
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
                  className="h-24 w-24 rounded-campo border border-borde bg-papel object-contain "
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              )}
              <span className="text-cuerpo font-medium leading-snug">{r.nombre}</span>
              <span className="cifra text-lg font-semibold">
                {eurosUnidad(r.precio_unidad_cent, r.unidad)}
              </span>
              <span className="text-cuerpo text-tinta-suave">
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