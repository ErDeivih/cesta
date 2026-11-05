/** El recetario montado: **las dos pestanas, las tarjetas y el coste que no se inventa**.
 *
 *  Lo que se mide no es el aspecto -- eso se mira en una captura -- sino lo que la pantalla
 *  **afirma**: que la lista no pinta un total que no tiene, que la pestana de archivadas
 *  enseña las archivadas y no las demas, que el alta sigue enviando lo que se escribe, que
 *  archivar sigue teniendo su error y que todo lo que se pulsa llega a 44 px.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import type { Sesion } from '../tipos'

vi.mock('../api/recetas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useRecetas: vi.fn(),
    useCrearReceta: vi.fn(),
    useArchivarReceta: vi.fn(),
  }
})

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, yo: vi.fn() }
})

import { yo } from '../api/cesta'
import { useArchivarReceta, useCrearReceta, useRecetas } from '../api/recetas'
import { ingredientesDeTexto, metaDeLaReceta, Recetario } from './Recetario'

const SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: null },
  preferencias: {},
}

const TORTILLA = {
  id: 1,
  nombre: 'Tortilla de patatas',
  creada: '2026-11-01T10:00:00Z',
  archivada: false,
  version: 1,
  raciones: 4,
  minutos: 30,
  etiquetas: 'cena',
}

const ARROZ = {
  id: 2,
  nombre: 'Arroz con tomate',
  creada: '2026-11-02T10:00:00Z',
  archivada: false,
  version: 1,
  raciones: 4,
  minutos: 25,
  etiquetas: '',
}

const LENTEJAS = {
  id: 3,
  nombre: 'Lentejas',
  creada: '2026-10-01T10:00:00Z',
  archivada: true,
  version: 2,
  raciones: 4,
  minutos: 40,
  etiquetas: 'invierno',
}

function consulta<T>(data: T, extra: Record<string, unknown> = {}) {
  return {
    data,
    isPending: false,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...extra,
  } as never
}

function mutacion(extra: Record<string, unknown> = {}) {
  return {
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    ...extra,
  }
}

function monta() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/recetas']}>
        <Recetario />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(yo).mockResolvedValue(SESION)
  vi.mocked(useRecetas).mockReturnValue(consulta({ recetas: [TORTILLA, ARROZ, LENTEJAS] }))
  vi.mocked(useCrearReceta).mockReturnValue(mutacion() as never)
  vi.mocked(useArchivarReceta).mockReturnValue(mutacion() as never)
})

describe('Recetario · la cabecera, las pestanas y las tarjetas', () => {
  it('*** pinta las recetas reales con sus raciones y sus minutos ***', async () => {
    monta()

    expect(await screen.findByRole('heading', { name: 'Qué cocinamos' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tortilla de patatas' })).toHaveAttribute(
      'href',
      '/recetas/1',
    )
    expect(screen.getByText('4 raciones · 30 min')).toBeInTheDocument()
    expect(screen.getByText('4 raciones · 25 min')).toBeInTheDocument()
    // *La consulta pide tambien las archivadas: es lo que permite contar las dos pestanas.*
    expect(useRecetas).toHaveBeenCalledWith(true)
  })

  it('*** sin coste en la lista no pinta ningun total: lo dice ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    expect(screen.getAllByText('Faltan precios')).toHaveLength(2)
    // *Ni un 0,00 ni un total inventado: la lista no trae precios.*
    expect(screen.queryByText(/€/)).not.toBeInTheDocument()
  })

  it('*** «Archivadas» enseña las archivadas y esconde las demas ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    await usuario.click(screen.getByRole('tab', { name: /Archivadas/ }))

    expect(screen.getByRole('link', { name: 'Lentejas' })).toHaveAttribute(
      'href',
      '/recetas/3',
    )
    expect(screen.queryByRole('link', { name: 'Tortilla de patatas' })).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Archivadas/ })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    // *La archivada no se presenta como si tuviera precio: se dice que esta archivada.*
    expect(screen.getByText('4 raciones · 40 min · archivada')).toBeInTheDocument()
    expect(screen.getByText('Archivada')).toBeInTheDocument()
  })

  it('*** el buscador filtra por nombre sin inventarse resultados ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    await usuario.type(screen.getByLabelText('Buscar recetas por nombre'), 'arroz')

    expect(screen.getByRole('link', { name: 'Arroz con tomate' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Tortilla de patatas' })).not.toBeInTheDocument()
  })

  it('*** un filtro que no encuentra nada lo dice con el filtro delante ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    await usuario.type(screen.getByLabelText('Buscar recetas por nombre'), 'cebolla')

    expect(screen.getByText(/Ninguna receta coincide con «cebolla»/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Quitar los filtros' })).toBeInTheDocument()
  })

  it('*** con recetas, «Importar desde una web» lleva a la pantalla de importar ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    expect(screen.getByRole('link', { name: 'Importar desde una web' })).toHaveAttribute(
      'href',
      '/compra/importar',
    )
  })
})

describe('Recetario · crear y archivar', () => {
  it('*** «Crear una receta» abre el alta y manda lo que se escribe ***', async () => {
    const crear = mutacion()
    vi.mocked(useCrearReceta).mockReturnValue(crear as never)
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    await usuario.click(screen.getByRole('button', { name: /Crear una receta/ }))
    expect(screen.getByRole('heading', { name: 'Nueva receta' })).toBeInTheDocument()

    await usuario.type(screen.getByLabelText('Nombre'), 'Tortilla')
    const raciones = screen.getByLabelText('Raciones')
    await usuario.clear(raciones)
    await usuario.type(raciones, '4')
    await usuario.type(screen.getByLabelText('Minutos'), '30')
    fireEvent.change(screen.getByLabelText('Ingredientes, uno por línea'), {
      target: { value: '600 g patatas\n5 ud huevos\nsal' },
    })
    fireEvent.change(screen.getByLabelText('Preparación'), {
      target: { value: 'Pela y corta.\nCuaja.' },
    })
    await usuario.type(screen.getByLabelText('Etiquetas, separadas por comas'), 'cena')
    await usuario.click(screen.getByRole('button', { name: 'Guardar receta' }))

    expect(crear.mutate).toHaveBeenCalledTimes(1)
    expect(crear.mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        nombre: 'Tortilla',
        raciones: 4,
        minutos: 30,
        preparacion: 'Pela y corta.\nCuaja.',
        etiquetas: 'cena',
        ingredientes: [
          { cantidad: 600, unidad: 'g', texto: 'patatas' },
          { cantidad: 5, unidad: 'ud', texto: 'huevos' },
          { texto: 'sal' },
        ],
      }),
      expect.anything(),
    )
  })

  it('*** archivar llama a su mutacion con la receta que se pulsa ***', async () => {
    const archivar = mutacion()
    vi.mocked(useArchivarReceta).mockReturnValue(archivar as never)
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    await usuario.click(screen.getAllByRole('button', { name: 'Archivar' })[0])

    expect(archivar.mutate).toHaveBeenCalledWith(1)
  })

  it('*** y si archivar falla, se dice en la receta que fallo ***', async () => {
    vi.mocked(useArchivarReceta).mockReturnValue(
      mutacion({ error: new Error('No se pudo archivar'), variables: 1 }) as never,
    )
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    expect(screen.getByText('No se pudo archivar')).toBeInTheDocument()
  })

  it('*** sin recetas, el vacio ofrece crearla y no enseña tarjetas ***', async () => {
    vi.mocked(useRecetas).mockReturnValue(consulta({ recetas: [] }))
    const usuario = userEvent.setup()
    monta()

    expect(await screen.findByText('Todavía no hay recetas')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Crear la primera receta' }))
    expect(screen.getByRole('heading', { name: 'Nueva receta' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Tortilla de patatas' })).not.toBeInTheDocument()
  })
})

describe('Recetario · los estados de verdad', () => {
  it('*** sin sesion se dice con la salida puesta, no con un error ***', async () => {
    vi.mocked(yo).mockResolvedValue({ usuario: null, preferencias: {} })
    monta()

    expect(await screen.findByText('Entra para ver esto')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'la cesta' })).toHaveAttribute('href', '/cesta')
  })

  it('*** mientras carga reserva el sitio, no una linea de texto ***', () => {
    vi.mocked(useRecetas).mockReturnValue(consulta(undefined, { data: undefined, isPending: true }))
    monta()

    expect(screen.getAllByRole('status').length).toBeGreaterThanOrEqual(1)
  })

  it('*** si la consulta falla, se dice y se puede volver a intentarlo ***', async () => {
    const refetch = vi.fn()
    vi.mocked(useRecetas).mockReturnValue(
      consulta(undefined, { data: undefined, error: new Error('sin red'), refetch }),
    )
    const usuario = userEvent.setup()
    monta()

    expect(await screen.findByText('No he podido traer tu recetario')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Volver a intentarlo' }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    for (const objetivo of [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]) {
      expect(objetivo.className).toMatch(/min-h-\[(44|56|64)px\]/)
    }
  })

  it('*** habla de recetas, no de como esta hecha (§8) ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Qué cocinamos' })

    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(
      /\bAPI\b|endpoint|token|caché|base de datos|scraper|gold|cálculo|se calcula/i,
    )
  })
})

describe('Recetario · las piezas puras', () => {
  it('*** una linea con cantidad y unidad se guarda; una sin cantidad no la gana ***', () => {
    expect(ingredientesDeTexto('600 g patatas\nsal\n\n5 ud huevos')).toEqual([
      { cantidad: 600, unidad: 'g', texto: 'patatas' },
      { texto: 'sal' },
      { cantidad: 5, unidad: 'ud', texto: 'huevos' },
    ])
    // *La coma decimal es como se escribe en una cocina en espanol.*
    expect(ingredientesDeTexto('1,5 l leche')[0]).toEqual({
      cantidad: 1.5,
      unidad: 'l',
      texto: 'leche',
    })
  })

  it('*** la meta no deja un « · » colgando ***', () => {
    expect(metaDeLaReceta({ raciones: 1, minutos: null })).toBe('1 ración')
    expect(metaDeLaReceta({ raciones: 4, minutos: 0 })).toBe('4 raciones')
    expect(metaDeLaReceta({ raciones: 4, minutos: 30, archivada: true })).toBe(
      '4 raciones · 30 min · archivada',
    )
  })
})
