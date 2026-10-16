/** **Lo que has pagado**, por mes o por semana, con su cobertura al lado.
 *
 *  G05 lo pide en Compra: *«Gasto pagado semanal/mensual a partir de compras guardadas e importes
 *  conocidos. **Separar fechas de compra y de precios. Cobertura de importes historicos `NULL`
 *  visible**»*.
 *
 *  **Las dos mitades, juntas y nunca una sin la otra.** Un total parcial sin su aviso es una mentira por
 *  omision; un aviso sin el total no informa. *Y cuando el total no se sabe, se dice «No se sabe»: un
 *  «0,00 €» se lee «ese mes no gaste nada», y el numero sale ademas mas bajo de lo real, redondo y
 *  creible.*
 *
 *  **La decision no se toma aqui**: `logica/gasto.ts` es puro, no importa nada y tiene sus pruebas.
 *  Este componente solo compone lo que aquel devuelve, y el «150,00 €» lo forma `numero`.
 *
 *  Y la tabla **no es un extra**: es donde se lee. *Es la misma razon que el panel escribe en el indice:
 *  el dibujo ayuda a ver la tendencia, el numero que se lee es el de la tabla.*
 */
import { useState } from 'react'

import { numero } from '../api/formato'
import { useGasto } from '../api/consultas'
import { misListas } from '../api/cesta'
import { importeEnCentimos, textoDeLoQueFalta, textoDePeriodo, totalConocido } from '../logica/gasto'
import { useQuery } from '@tanstack/react-query'

import { Cargando, Fallo, Tarjeta, TablaScroll, Td, Th, Vacio } from './ui'

export function LoQueHasPagado() {
  const [porSemana, setPorSemana] = useState(false)
  // **`misListas` es un `queryFn`, no un hook**: el mismo patron que `Diario.tsx:63`.
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas })
  // **El gasto es de la lista de casa**, que es la que tiene compras. *La misma regla que el puente del
  // diario: la lista de casa, y solo esa.*
  const casa = listas.data?.find((l) => l.es_de_casa) ?? null
  const periodo = porSemana ? 'semana' : 'mes'
  const gasto = useGasto(casa?.id ?? null, periodo)

  return (
    <Tarjeta
      titulo="Lo que has pagado"
      sub="De las compras que cerraste, agrupadas por la fecha en que las cerraste"
    >
      {/* **Y estos dos controles median 23 px de alto** *-- *el alto de la linea --.*
          Lo destapo la puerta al desbloquearse (ronda 64): **56x23 «Por mes» y
          79x23 «Por semana»**, *«no hay nada que pulsar por debajo de 44 px»*. Y son
          **dos botones que se pulsan de verdad**, *no adorno: cambian el periodo.*
          El minimo de la casa son **44 px** *-- *los del lateral lo cumplen
          (`Suite.tsx:206`), *los de la barra de abajo miden 56, *y estos se habian
          quedado en 23--.* *Y `inline-flex` para que el blanco sea **el texto**
          y no toda la linea, que aqui van los dos seguidos.* */}
      <div className="mb-3 flex items-center gap-2 text-cuerpo">
        <button
          type="button"
          onClick={() => setPorSemana(false)}
          aria-pressed={!porSemana}
          className={`inline-flex min-h-[44px] items-center px-2 ${
            porSemana ? 'underline' : 'font-semibold'}`}
        >
          Por mes
        </button>
        <span aria-hidden className="text-tinta-suave">
          ·
        </span>
        <button
          type="button"
          onClick={() => setPorSemana(true)}
          aria-pressed={porSemana}
          className={`inline-flex min-h-[44px] items-center px-2 ${
            porSemana ? 'font-semibold' : 'underline'}`}
        >
          Por semana
        </button>
      </div>

      {!casa && !listas.isLoading && (
        <Vacio titulo="Todavía no tienes lista de casa">
          <p>El gasto sale de las compras que cierras en ella, así que no hay nada que sumar.</p>
        </Vacio>
      )}
      {casa && listas.isLoading && <Cargando que="tus listas" />}
      {casa && gasto.isLoading && <Cargando que="lo que has pagado" />}
      {casa && gasto.isError && <Fallo error={gasto.error} reintentar={() => gasto.refetch()} />}

      {casa && gasto.data && gasto.data.filas.length === 0 && (
        <Vacio titulo="Todavía no has cerrado ninguna compra">
          <p>Cuando cierres una, aquí aparecerá lo que pagaste y lo que se quedó sin precio.</p>
        </Vacio>
      )}

      {casa && gasto.data && gasto.data.filas.length > 0 && (
        <TablaScroll etiqueta="Lo que has pagado por periodo" minAncho="30rem">
          <table className="w-full border-collapse text-cuerpo">
            <caption className="sr-only">
              {`Gasto pagado por ${porSemana ? 'semana' : 'mes'}, con cuántas líneas se quedaron sin precio`}
            </caption>
            <thead>
              <tr>
                <Th>{porSemana ? 'Semana' : 'Mes'}</Th>
                <Th className="text-right">Pagado</Th>
                <Th className="text-right">Compras</Th>
                <Th>Cobertura</Th>
              </tr>
            </thead>
            <tbody>
              {gasto.data.filas.map((fila) => {
                const falta = textoDeLoQueFalta(fila)
                const sabe = totalConocido(fila)
                const cent = importeEnCentimos(fila)
                return (
                  <tr key={fila.periodo ?? 'sin-fecha'}>
                    <Td>{textoDePeriodo(fila, porSemana)}</Td>
                    {/* **Un total que no se sabe NO es un cero.** Y el aviso va en la misma fila, no
                        en una nota al pie: *quien lee el numero tiene que leer lo que le falta.* */}
                    <Td
                      className={`cifra text-right ${sabe ? '' : 'text-tinta-suave'}`}
                      etiqueta={sabe ? 'pagado' : 'pagado, sin dato'}
                    >
                      {sabe ? `${numero((cent ?? 0) / 100, 2)} €` : 'No se sabe'}
                    </Td>
                    <Td className="cifra text-right" etiqueta="compras">
                      {numero(fila.compras, 0)}
                    </Td>
                    <Td className={falta ? 'text-aviso ' : 'text-tinta-suave'}>
                      {falta ?? 'completa'}
                    </Td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </TablaScroll>
      )}

      {casa && gasto.data && (
        <p className="mt-2 text-etiqueta text-tinta-suave">
          El gasto es de <strong className="font-medium">{casa.nombre}</strong>, sobre{' '}
          {numero(gasto.data.compras, 0)}{' '}
          {gasto.data.compras === 1 ? 'compra cerrada' : 'compras cerradas'}. Un total se suma solo con
          las líneas que tienen precio: cuando falta alguna, se dice cuántas, porque un número que
          parece completo y no lo está es peor que no dar número.
        </p>
      )}
    </Tarjeta>
  )
}