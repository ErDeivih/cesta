/** *** LA PUERTA DE SESIÓN, PANTALLA A PANTALLA, Y EL MENÚ SIN LO INTERNO. ***
 *
 *  *Lo que mide esto, y por qué hacía falta:* seis pantallas (Despensa, Recetario, RecetaDetalle,
 *  PlanSemanal, Diario y Tendencias) pedían datos que exigen sesión **sin preguntar antes si había
 *  alguien**.* A quien no ha entrado le salía el error de la petición —«La API ha contestado 401»—,
 *  que es texto de desarrollador (§8) y, además, una primera impresión rota.
 *
 *  *Se monta cada pantalla con `yo()` contestando «no hay nadie», que es lo que pasa de verdad sin
 *  cookie.* Con la puerta puesta, las consultas de datos **ni se montan**: si se montaran, el
 *  `fetch` no existiría en el test y la pantalla se caería, que es la señal de que la puerta no está
 *  delante.
 *
 *  *Y el menú:* «Gasto y ahorro» llevaba al panel interno de analítica y «Aprender» a un párrafo
 *  sobre el repositorio. Los dos salen del menú de consumo, y `/panel`, `/panel/matching` y
 *  `/compra/analisis` dejan de estar enlazados desde él.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// **Sin sesión.** `yo()` nunca falla: devuelve `usuario: null` (api/cesta.ts).
vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, yo: async () => ({ usuario: null, preferencias: {} }) }
})

// *El contador del menú pide datos con sesión; aquí no hay ninguna, así que no se pinta.*
vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, usePorCogerDeCasa: () => ({ tipo: 'oculto' }) }
})

import { Despensa } from '../paginas/Despensa'
import { Diario } from '../paginas/Diario'
import { PlanSemanal } from '../paginas/PlanSemanal'
import { RecetaDetalle } from '../paginas/RecetaDetalle'
import { Recetario } from '../paginas/Recetario'
import { Tendencias } from '../paginas/Tendencias'
import { APLICACIONES, SuiteSidebar } from '../componentes/Suite'

function monta(hijo: ReactNode, ruta = '/') {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[ruta]}>{hijo}</MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Lo que no puede leerse en una pantalla de consumo, con sesión o sin ella. */
const TECNICO = /401|403|500|\bAPI\b|servidor|endpoint|gold|parquet|docker|repositorio/i

const PANTALLAS: [string, ReactNode, string][] = [
  ['Despensa', <Despensa />, '/compra/despensa'],
  ['Recetario', <Recetario />, '/recetas'],
  ['RecetaDetalle', <RecetaDetalle />, '/recetas/1'],
  ['PlanSemanal', <PlanSemanal />, '/recetas/plan'],
  ['Diario', <Diario />, '/calorias'],
  ['Tendencias', <Tendencias />, '/calorias/tendencias'],
]

describe('sin sesión, las seis pantallas enseñan la puerta y no un error', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  for (const [nombre, pantalla, ruta] of PANTALLAS) {
    it(`${nombre}: dice «Entra para ver esto» y no enseña texto técnico`, async () => {
      monta(pantalla, ruta)
      expect(await screen.findByText('Entra para ver esto')).toBeInTheDocument()
      // *Un enlace de entrada de verdad, no una frase sin salida.*
      const enlaces = screen.getAllByRole('link').map((a) => a.getAttribute('href'))
      expect(enlaces).toContain('/cesta')
      // *Y nada en rojo: no es un fallo, es un estado.*
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      expect(document.body.textContent ?? '').not.toMatch(TECNICO)
    })
  }
})

describe('el menú de consumo no lleva a lo interno', () => {
  it('no ofrece «Gasto y ahorro» ni «Aprender»', () => {
    monta(<SuiteSidebar app={APLICACIONES[0]} />)
    expect(screen.queryByText('Gasto y ahorro')).not.toBeInTheDocument()
    expect(screen.queryByText('Aprender')).not.toBeInTheDocument()
  })

  it('no enlaza el panel interno ni el matching ni /compra/analisis', () => {
    monta(<SuiteSidebar app={APLICACIONES[0]} />)
    const internos = ['/panel', '/panel/matching', '/compra/analisis', '/aprender']
    const enlazados = [...document.querySelectorAll('a[href]')]
      .map((a) => a.getAttribute('href') ?? '')
      .filter((href) => internos.some((i) => href === i || href.startsWith(`${i}/`)))
    expect(enlazados).toEqual([])
  })
})
