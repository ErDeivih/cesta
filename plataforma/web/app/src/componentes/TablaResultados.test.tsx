/** *** LA FILA DEL MÓVIL: €/UNIDAD Y COMPARACIÓN, SIN ABRIR NADA. *** *
 *
 *  *La tabla de escritorio tiene columnas; en 390 px la fila se pinta en dos líneas. Lo que
 *  no puede pasar es que el precio por unidad o la comparación entre cadenas se queden
 *  detrás de un desplegable: es la pregunta que la app existe para contestar.*
 *
 *  *Esta prueba monta una fila real del catálogo de la demo (Leche entera, cinco cadenas) y
 *  exige ver el precio, el €/litro, cuántas cadenas lo tienen y la diferencia con la más
 *  cara. Con el contador de cadenas: antes solo salía la cadena más barata, y «Carrefour»
 *  sin decir que hay cuatro más no es una comparación.*
 */
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { TablaResultados } from './TablaResultados'
import { buscaCatalogo } from '../demo/catalogo'

/** *La fila compacta se elige con la misma consulta que usa la pantalla: 390 px.* */
beforeEach(() => {
  window.matchMedia = vi.fn().mockImplementation((media: string) => ({
    matches: /max-width:\s*639px/.test(media),
    media,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia
})

describe('la fila de resultados en el móvil', () => {
  it('enseña precio, €/unidad, cadena más barata y cuántas cadenas comparan', () => {
    const { resultados } = buscaCatalogo({ q: 'leche entera brik', limite: 1 })
    expect(resultados.length).toBe(1)
    const fila = resultados[0]
    expect(fila.cadenas).toBeGreaterThanOrEqual(5)

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter>
          <TablaResultados filas={[fila]} />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    // *El precio de venta y el precio por unidad, cada uno en su sitio.*
    expect(screen.getByText('0,94 €')).toBeInTheDocument()
    expect(screen.getByText('0,94 €/l')).toBeInTheDocument()
    // *La diferencia con la más cara, que es la comparación entre cadenas.*
    expect(screen.getByText(/menos que el más caro/)).toBeInTheDocument()
    // *Y cuántas cadenas entran en la comparación: sin esto, «Carrefour» parece la única.*
    expect(screen.getByText(/5 cadenas/)).toBeInTheDocument()
    // *El desplegable con los precios de cada cadena sigue ahí.*
    expect(screen.getByRole('button', { name: /Ver ofertas por supermercado/ })).toBeInTheDocument()
  })
})
