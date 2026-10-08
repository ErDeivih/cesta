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

import { textoDeError } from '../api/cliente'
import { useApuntar, useBorrarEntrada, useDia } from '../api/diario'
import type { NuevaEntrada } from '../api/diario'
import { Boton, Tarjeta, Vacio } from '../componentes/ui'

const COMIDAS = ['desayuno', 'media manana', 'comida', 'merienda', 'cena', 'otras']
const FUENTES = ['etiqueta', 'ficha', 'estimado', 'desconocido']

function hoy(): string {
  const ahora = new Date()
  // Fecha local, no UTC: a las once de la noche el dia que se anota es el de casa.
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
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
          <label className="flex min-h-[44px] items-center gap-2 text-[14px] text-tinta-fuerte">
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
          className="min-h-[44px] text-[14px] text-secundaria underline"
        >
          Hoy
        </button>
      </div>

      {isPending && <p className="text-[16px] text-secundaria">Leyendo el diario...</p>}
      {error && <p className="text-[16px] text-error">{textoDeError(error)}</p>}

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
                      className="mt-1 min-h-[44px] text-[13px] text-secundaria underline"
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
