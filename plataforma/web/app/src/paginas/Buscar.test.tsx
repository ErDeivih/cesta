/** *** EL LISTADO DE COMPRA A 390 PX: POCO CHROME Y LOS CUATRO DATOS. *** *
 *
 *  *La revisión de la primera pantalla decía tres cosas que se pueden medir aquí sin navegador:*
 *
 *   1. las cadenas y «Guardar estos filtros» **no** pueden estar siempre a la vista —van dentro
 *      del panel de filtros—, y los filtros puestos se ven como **chips** que se quitan;
 *   2. cada producto enseña **nombre, supermercado, precio y precio por unidad** (y nada más);
 *   3. la diferencia del grupo se dice **en euros** («0,66 €/l menos que el más caro»), no en un
 *      porcentaje;
 *   4. **«Ver ofertas por supermercado»** despliega el mismo producto cadena a cadena, ordenado
 *      por precio por unidad.
 */
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Grupo, ResultadoBusqueda } from '../tipos'

const dobles = vi.hoisted(() => ({
  resultados: [] as unknown[],
  grupo: null as unknown,
}))

vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useEstado: () => ({ data: { cadenas: [{ cadena: 'alcampo' }, { cadena: 'dia' }] } }),
    useBuscar: () => ({
      data: { fecha_datos: '2026-11-13', corregido: null, resultados: dobles.resultados },
      isPending: false,
      isError: false,
      isFetching: false,
      error: null,
      refetch: vi.fn(),
    }),
    useSecciones: () => ({ data: { secciones: [] } }),
    useGrupo: () => ({ data: dobles.grupo, isPending: false, isError: false, refetch: vi.fn() }),
  }
})

import { Buscar } from './Buscar'

/** Un resultado de `GET /api/buscar`, con la forma de la API de verdad. */
function fila(extra: Partial<ResultadoBusqueda> = {}): ResultadoBusqueda {
  return {
    grupo_id: 77,
    nombre: 'Leche entera Hacendado',
    marca: 'Hacendado',
    cadena_mas_barata: 'mercadona',
    precio_cent: 96,
    precio_unidad_cent: 96,
    precio_unidad_max_cent: 162,
    unidad: 'l',
    cadenas: 3,
    productos: 4,
    nutriscore: 'b',
    imagen: null,
    ecoscore: null,
    kcal_100g: null,
    hidratos_100g: null,
    proteinas_100g: null,
    grasas_100g: null,
    grasas_sat_100g: null,
    azucares_100g: null,
    sal_100g: null,
    con_oferta: false,
    con_oferta_club: false,
    con_retirada: false,
    comparable: true,
    dudoso: false,
    ahorro_pct: 68.8,
    ...extra,
  }
}

/** El grupo que devuelve `GET /api/grupo/{id}`: dos cadenas con otra unidad de precio. */
function grupo(): Grupo {
  return {
    grupo_id: 77,
    nombre: 'Leche entera',
    imagen: null,
    unidad: 'l',
    cadenas: 2,
    ahorro_pct: 68.8,
    ahorro_cent: 66,
    serie: [],
    productos: [
      {
        producto_id: 'carrefour:1',
        fuente: 'carrefour',
        id_fuente: '1',
        nombre: 'Leche entera Carrefour',
        marca: 'Carrefour',
        cantidad: 1,
        unidad: 'l',
        precio_cent: 105,
        precio_unidad_cent: 105,
        comparable: true,
        calidad: null,
        calidad_de: null,
        gama: null,
        nutriscore: 'b',
      },
      {
        // *Segundo formato de Carrefour, más caro por unidad: no debe pintar otra fila de Carrefour.*
        producto_id: 'carrefour:3',
        fuente: 'carrefour',
        id_fuente: '3',
        nombre: 'Leche entera Carrefour 2 l',
        marca: 'Carrefour',
        cantidad: 2,
        unidad: 'l',
        precio_cent: 240,
        precio_unidad_cent: 120,
        comparable: true,
        calidad: null,
        calidad_de: null,
        gama: null,
        nutriscore: 'b',
      },
      {
        producto_id: 'aldi:2',
        fuente: 'aldi',
        id_fuente: '2',
        nombre: 'Leche entera MILSANI',
        marca: 'MILSANI',
        cantidad: 1,
        unidad: 'l',
        precio_cent: 39,
        precio_unidad_cent: 39,
        comparable: true,
        calidad: null,
        calidad_de: null,
        gama: null,
        nutriscore: 'b',
      },
    ],
  } as unknown as Grupo
}

/** *Los resultados se miden a 390 px*, que es donde se juega la revisión: se responde que la
 *  pantalla es estrecha en la consulta de la fila compacta.* */
function pantallaEstrecha() {
  window.matchMedia = ((consulta: string) => ({
    matches: /max-width:\s*639px/.test(consulta),
    media: consulta,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia
}

beforeEach(() => {
  pantallaEstrecha()
})

function monta() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/compra?q=leche%20entera']}>
        <Routes>
          <Route path="/compra" element={<Buscar />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('el listado a 390 px', () => {
  it('las cadenas y «Guardar estos filtros» no están a la vista; aparecen al abrir Filtros', async () => {
    dobles.resultados = [fila()]
    dobles.grupo = grupo()
    monta()

    // *Cerrado: ni cadenas ni guardar.* El panel es lo único que se pinta.
    expect(screen.getByRole('button', { name: /Filtros/ })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('button', { name: 'DIA' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Guardar estos filtros' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Filtros/ }))

    expect(screen.getByRole('button', { name: /Filtros/ })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('button', { name: 'DIA' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar estos filtros' })).toBeInTheDocument()
  })

  it('un filtro puesto se ve como chip que se quita, sin abrir el panel', async () => {
    dobles.resultados = [fila()]
    dobles.grupo = grupo()
    monta()

    await userEvent.click(screen.getByRole('button', { name: /Filtros/ }))
    await userEvent.click(screen.getByRole('button', { name: 'DIA' }))

    const chip = screen.getByRole('button', { name: 'Quitar el filtro DIA' })
    expect(chip).toHaveTextContent('DIA')
    expect(screen.getByRole('button', { name: 'Quitar todos' })).toBeInTheDocument()

    await userEvent.click(chip)
    expect(screen.queryByRole('button', { name: 'Quitar el filtro DIA' })).not.toBeInTheDocument()
  })

  it('el producto enseña nombre, supermercado, precio y precio por unidad, con la diferencia en euros', () => {
    dobles.resultados = [fila()]
    dobles.grupo = grupo()
    monta()

    const lista = screen.getByRole('list', { name: 'Resultados de la búsqueda' })
    const filaPintada = within(lista).getAllByRole('listitem')[0]
    expect(within(filaPintada).getByText('Leche entera Hacendado')).toBeInTheDocument()
    expect(within(filaPintada).getByText('Mercadona')).toBeInTheDocument()
    // *Precio de venta y precio por unidad, **juntos**: no se toca esa pareja.*
    expect(within(filaPintada).getByText('0,96 €')).toBeInTheDocument()
    expect(within(filaPintada).getByText('0,96 €/l')).toBeInTheDocument()
    // *La diferencia, en euros y con unidad, en vez del porcentaje del grupo.*
    expect(within(filaPintada).getByText('0,66 €/l menos que el más caro')).toBeInTheDocument()
    expect(within(filaPintada).queryByText(/hasta un/)).not.toBeInTheDocument()
    // *Y lo que se va al detalle no ocupa la fila.*
    expect(within(filaPintada).queryByText(/nutri-score/i)).not.toBeInTheDocument()
  })

  it('«Ver ofertas por supermercado» despliega las cadenas ordenadas por precio por unidad', async () => {
    dobles.resultados = [fila()]
    dobles.grupo = grupo()
    monta()

    const boton = screen.getByRole('button', { name: 'Ver ofertas por supermercado' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(boton)

    expect(boton).toHaveAttribute('aria-expanded', 'true')
    const region = screen.getByRole('region', { name: /Precios de .* por supermercado/ })
    const filas = within(region).getAllByRole('listitem')
    // *Una fila por supermercado: el grupo tiene dos formatos de Carrefour y se enseña el más
    // barato por unidad, no dos filas que parecen un duplicado.*
    expect(filas).toHaveLength(2)
    // *0,39 €/l (Aldi) antes que 1,05 € (Carrefour): manda el precio por unidad, no el de venta.*
    expect(filas[0]).toHaveTextContent('Aldi')
    expect(filas[0]).toHaveTextContent('0,39 €/l')
    expect(filas[1]).toHaveTextContent('Carrefour')
    expect(filas[1]).toHaveTextContent('1,05 €/l')
    expect(filas[1]).not.toHaveTextContent('1,20 €/l')
  })

  it('sin diferencia comparable no se pinta porcentaje ni cero', () => {
    dobles.resultados = [fila({ comparable: false, precio_unidad_max_cent: null })]
    dobles.grupo = grupo()
    monta()

    const lista = screen.getByRole('list', { name: 'Resultados de la búsqueda' })
    const filaPintada = within(lista).getAllByRole('listitem')[0]
    expect(within(filaPintada).queryByText(/menos que el más caro/)).not.toBeInTheDocument()
    expect(within(filaPintada).queryByText(/hasta un/)).not.toBeInTheDocument()
  })
})
