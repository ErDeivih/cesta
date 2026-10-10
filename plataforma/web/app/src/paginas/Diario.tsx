/** El diario del dia: lo que se comio, lo que se sabe y lo que falta por saber.
 *
 *  **Las dos cifras van juntas.** "Conocido: 1.250 kcal" sin decir cuantas entradas no traen dato es un
 *  numero que parece medido y no lo esta. Aqui se enseña el subtotal **y** cuantas faltan, y mientras
 *  falte alguna se dice en una linea entera, no en letra pequeña.
 *
 *  Y por eso el alta obliga a declarar **de donde sale el dato**: etiqueta, ficha, estimacion o
 *  desconocido. Es la unica manera de que el subtotal signifique algo.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { anotarDeLaCompra, misListas, previaDeLaCompra } from '../api/cesta'
import type { PreviaDeLaCompra } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { useApuntar, useBorrarEntrada, useDia } from '../api/diario'
import type { NuevaEntrada } from '../api/diario'
import { Boton, Tarjeta, Vacio } from '../componentes/ui'

const NOMBRE_NUTRIENTE: Record<string, string> = {
  kcal: 'energia',
  proteinas_g: 'proteinas',
  grasas_g: 'grasas',
  hidratos_g: 'hidratos',
}


const COMIDAS = ['desayuno', 'media manana', 'comida', 'merienda', 'cena', 'otras']
const FUENTES = ['etiqueta', 'ficha', 'estimado', 'desconocido']

function hoy(): string {
  const ahora = new Date()
  // Fecha local, no UTC: a las once de la noche el dia que se anota es el de casa.
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

/** **Lo que ya has comprado, al diario.** Hasta hoy el diario solo se podia llenar escribiendo a mano,
 *  y la compra que ya esta hecha no decia nada.
 *
 *  **La compra propone y la persona confirma**: la previa ense?a que se anotaria, **y aparte lo que no
 *  trae nutricion, con su nombre** -- *anotar las que se puede y callar las demas convertiria un dato
 *  que falta en una comida que parece completa*. Y **la cobertura** dice cuantas de cuantas.
 */
function DeLaCompra({ fecha }: { fecha: string }) {
  const cliente = useQueryClient()
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas })
  const listaId = listas.data?.find((l) => l.es_de_casa)?.id ?? listas.data?.[0]?.id ?? null
  const [comida, setComida] = useState('comida')
  const [previa, setPrevia] = useState<PreviaDeLaCompra | null>(null)
  const [anotadas, setAnotadas] = useState<number | null>(null)

  const ver = useMutation({
    mutationFn: () => previaDeLaCompra(listaId as string),
    onSuccess: (p) => { setPrevia(p); setAnotadas(null) },
  })
  const anotar = useMutation({
    mutationFn: () => anotarDeLaCompra(listaId as string, fecha, comida),
    onSuccess: () => {
      cliente.invalidateQueries({ queryKey: ['diario'] })
      setAnotadas(previa?.anotarian.length ?? 0)
      setPrevia(null)
    },
  })

  if (listaId === null) return null
  return (
    <Tarjeta>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[16px] text-tinta-fuerte">De la compra al diario</span>
        <Boton onClick={() => ver.mutate()} disabled={ver.isPending}>
          Ver que se puede anotar
        </Boton>
      </div>

      {anotadas !== null && (
        <p className="mt-2 text-[15px] text-tinta-fuerte">
          {anotadas === 1 ? 'Se ha anotado 1.' : `Se han anotado ${anotadas}.`}
        </p>
      )}

      {previa && (
        <div className="mt-2 flex flex-col gap-2">
          {previa.compra_id === null ? (
            <p className="text-[15px] text-secundaria">
              Esta lista todavia no tiene ninguna compra cerrada, asi que no hay nada que anotar.
            </p>
          ) : (
            <>
              <p className="text-[15px] text-tinta-fuerte">
                {previa.cobertura.total === 0
                  ? 'No hay nada que anotar.'
                  : `Se anotarian ${previa.anotarian.length} de ${previa.cobertura.total}:`}
              </p>
              <ul className="flex flex-col gap-1">
                {previa.anotarian.map((x) => (
                  <li key={x.linea_id} className="text-[15px] text-tinta-fuerte">
                    {x.nombre}
                    {x.kcal !== null && (
                      <span className="text-[13px] text-secundaria tabular-nums"> {x.kcal} kcal</span>
                    )}
                  </li>
                ))}
              </ul>
              {previa.sin_dato.length > 0 && (
                <p className="text-[14px] text-secundaria">
                  {previa.sin_dato.length === 1
                    ? 'Uno no trae nutricion en el catalogo, asi que se anotaria como ?sin dato?: '
                    : `${previa.sin_dato.length} no traen nutricion en el catalogo, asi que se anotarian como ?sin dato?: `}
                  {previa.sin_dato.join(', ')}.
                </p>
              )}
              {previa.anotarian.length > 0 && (
                <>
                  <label className="flex flex-col gap-1 text-[13px] text-secundaria">
                    Comida
                    <select
                      value={comida}
                      onChange={(e) => setComida(e.target.value)}
                      className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
                    >
                      {COMIDAS.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </label>
                  <Boton onClick={() => anotar.mutate()} disabled={anotar.isPending}>
                    Si, anotarlo
                  </Boton>
                </>
              )}
            </>
          )}
          {(ver.error || anotar.error) && (
            <p className="text-[14px] text-error">{textoDeError(ver.error ?? anotar.error)}</p>
          )}
        </div>
      )}
    </Tarjeta>
  )
}

function Alta({ fecha }: { fecha: string }) {
  const [comida, setComida] = useState('comida')
  const [texto, setTexto] = useState('')
  const [kcal, setKcal] = useState('')
  const [fuente, setFuente] = useState('etiqueta')
  const [esReceta, setEsReceta] = useState(false)
  const [version, setVersion] = useState('1')
  const apuntar = useApuntar()

  return (
    <Tarjeta>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          const datos: NuevaEntrada = {
            fecha, comida,
            tipo: esReceta ? 'receta' : 'alimento',
            referencia: esReceta ? texto.trim() || null : texto.trim() || null,
            version: esReceta ? version : null,
            cantidad_g: null,
            kcal: kcal === '' ? null : Number(kcal.replace(',', '.')),
            proteinas_g: null, grasas_g: null, hidratos_g: null,
            fuente_dato: fuente, nota: '',
          }
          apuntar.mutate(datos, {
            onSuccess: () => {
              setTexto('')
              setKcal('')
            },
          })
        }}
        className="flex flex-col gap-3"
      >
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Comida
            <select
              value={comida}
              onChange={(e) => setComida(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            >
              {COMIDAS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            {esReceta ? 'Receta (nombre o numero)' : 'Que has comido'}
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Energia (kcal)
            <input
              value={kcal}
              onChange={(e) => setKcal(e.target.value)}
              inputMode="decimal"
              className="min-h-[44px] w-28 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            De donde sale el dato
            <select
              value={fuente}
              onChange={(e) => setFuente(e.target.value)}
              className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
            >
              {FUENTES.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-h-[44px] min-w-[44px] items-center gap-2 text-[14px] text-tinta-fuerte">
            <input type="checkbox" checked={esReceta} onChange={(e) => setEsReceta(e.target.checked)} />
            Es una receta
          </label>
          {esReceta && (
            <label className="flex items-center gap-2 text-[13px] text-secundaria">
              Version
              <input
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="min-h-[44px] w-20 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
              />
            </label>
          )}
          <Boton type="submit" disabled={apuntar.isPending}>
            {apuntar.isPending ? 'Anotando...' : 'Anotar'}
          </Boton>
        </div>
        {esReceta && (
          <p className="text-[13px] text-secundaria">
            La version no es un detalle: es lo que permitira releer este dia dentro de un mes tal y como
            estaba, aunque la receta haya cambiado.
          </p>
        )}
        {apuntar.error && <p className="text-[14px] text-error">{textoDeError(apuntar.error)}</p>}
      </form>
    </Tarjeta>
  )
}

export function Diario() {
  const [fecha, setFecha] = useState(hoy())
  const { data, isPending, error } = useDia(fecha)
  const borrar = useBorrarEntrada(fecha)

  const conDato = data?.conocido.entradas ?? 0
  const total = data?.entradas.length ?? 0
  const faltan = data?.sin_dato.length ?? 0

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-[13px] text-secundaria">
          Dia
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
          />
        </label>
        <button
          type="button"
          onClick={() => setFecha(hoy())}
          className="min-h-[44px] min-w-[44px] text-[14px] text-secundaria underline"
        >
          Hoy
        </button>
      </div>

      {isPending && <p className="text-[16px] text-secundaria">Leyendo el diario...</p>}
      {error && <p className="text-[16px] text-error">{textoDeError(error)}</p>}

      <DeLaCompra fecha={fecha} />

      {data && (
        <Tarjeta>
          <div className="flex flex-wrap items-baseline gap-4">
            <p className="font-serif text-[28px] leading-[34px] font-semibold text-tinta-fuerte tabular-nums">
              {data.conocido.kcal === null ? 'sin dato' : `${data.conocido.kcal} kcal`}
            </p>
            <p className="text-[13px] text-secundaria tabular-nums">
              de {conDato} de {total} {total === 1 ? 'entrada' : 'entradas'}
            </p>
          </div>
          {/* La frase que impide leer el numero de arriba como "lo que comi hoy". */}
          {!data.completo && total > 0 && (
            <p className="mt-1 text-[14px] leading-[22px] text-aviso">
              Este dia <strong>no esta completo</strong>: falta el dato de {faltan}{' '}
              {faltan === 1 ? 'entrada' : 'entradas'}. Lo de arriba es lo que se sabe, no lo que comiste.
            </p>
          )}

          {/* **La cobertura, nutriente a nutriente.** El total de energia puede estar completo y faltar
              las proteinas: decir "3 de 4 entradas" es lo que impide leer el numero de arriba como si
              fuera el dia entero. Y un nutriente que no trae nadie se dice con la palabra, no con un 0. */}
          {data.cobertura && (
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
              {Object.entries(data.cobertura).map(([nutriente, c]) => (
                <li key={nutriente} className="text-[13px] text-secundaria tabular-nums">
                  {NOMBRE_NUTRIENTE[nutriente] ?? nutriente}:{' '}
                  {c.con_dato === 0 ? (
                    <span className="text-aviso">sin dato</span>
                  ) : (
                    <>
                      {c.con_dato} de {c.total}
                      {c.completa ? '' : ' entradas'}
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
          {data.completo && total > 0 && (
            <p className="mt-1 text-[14px] text-secundaria">
              Todas las entradas anotadas tienen calorías. El subtotal solo incluye lo registrado;
              comprueba que hayas anotado todas tus comidas.
            </p>
          )}
        </Tarjeta>
      )}

      <Alta fecha={fecha} />

      {data && total === 0 && (
        <Vacio titulo="Nada anotado este dia">
          <p>Anota lo primero arriba y aparecera aqui, agrupado por comidas.</p>
        </Vacio>
      )}

      {data &&
        Object.entries(data.comidas).map(([comida, entradas]) => (
          <section key={comida} className="flex flex-col gap-2">
            <h2 className="font-serif text-[19px] leading-7 text-tinta-fuerte">{comida}</h2>
            <ul className="flex flex-col gap-2">
              {entradas.map((e) => (
                <li key={e.id}>
                  <Tarjeta>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-[16px] text-tinta-fuerte">
                        {e.tipo === 'receta' ? `Receta ${e.referencia} (v${e.version})` : e.referencia || 'sin nombre'}
                      </span>
                      <span className="text-[13px] tabular-nums text-secundaria">
                        {e.kcal === null ? 'sin dato' : `${e.kcal} kcal`} · {e.fuente_dato}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => borrar.mutate(e.id)}
                      className="mt-1 min-h-[44px] min-w-[44px] text-[13px] text-secundaria underline"
                    >
                      Quitar
                    </button>
                  </Tarjeta>
                </li>
              ))}
            </ul>
          </section>
        ))}
    </div>
  )
}
