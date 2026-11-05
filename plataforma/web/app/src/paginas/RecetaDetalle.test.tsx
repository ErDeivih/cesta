/** El detalle montado: **coste con datos reales, o dicho sin inventarlo**.
 *
 *  Lo que se mide no es el aspecto -- eso se mira en una captura -- sino lo que la pantalla
 *  **afirma**: que el coste sale de los precios que trae la API (con sus unidades convertidas),
 *  que un ingrediente sin precio no se convierte en cero, que un total parcial se llama parcial,
 *  que los ingredientes y las cantidades reales se enseñan siempre, y que las acciones de
 *  añadir a la lista, cocinar y editar siguen existiendo.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import type { Receta } from '../api/recetas'
import type { Sesion } from '../tipos'

vi.mock('../api/recetas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useReceta: vi.fn(),
    usePasarALista: vi.fn(),
    usePreviaDeCompra: vi.fn(),
    useCambiarReceta: vi.fn(),
  }
})

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, yo: vi.fn(), misListas: vi.fn() }
})

vi.mock('../api/cliente', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, pide: vi.fn() }
})

import { useCambiarReceta, usePasarALista, usePreviaDeCompra, useReceta } from '../api/recetas'
import { misListas, yo } from '../api/cesta'
import { ErrorApi, pide } from '../api/cliente'
import {
  avisosDeCobertura,
  costeDeLaReceta,
  enEspanol,
  pasosDePreparacion,
  precioParaElCoste,
  RecetaDetalle,
} from './RecetaDetalle'
import type { IngredienteDeLaApi } from './RecetaDetalle'

const SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: null },
  preferencias: {},
}

/** Los precios son los que devuelve la API: euros por el envase y precio por la unidad canonica. */
const INGREDIENTES = [
  {
    texto: 'Huevos',
    cantidad: 6,
    unidad: 'ud',
    producto_id: 'dia:huevos-1',
    precio_cent: 180,
    precio_unidad_cent: 30,
    unidad_canon: 'ud',
    tamano_envase: 6,
    unidad_envase: 'ud',
  },
  {
    texto: 'Patatas',
    cantidad: 200,
    unidad: 'g',
    producto_id: 'dia:patatas-1',
    precio_cent: 120,
    precio_unidad_cent: 120,
    unidad_canon: 'kg',
    tamano_envase: 1,
    unidad_envase: 'kg',
  },
  {
    texto: 'Cebolla',
    cantidad: 1,
    unidad: 'ud',
    producto_id: 'dia:cebolla-1',
    precio_cent: 129,
    precio_unidad_cent: 129,
    unidad_canon: 'ud',
    tamano_envase: 1,
    unidad_envase: 'ud',
  },
  {
    texto: 'Aceite de oliva',
    cantidad: 200,
    unidad: 'ml',
    producto_id: 'dia:aceite-1',
    precio_cent: 243,
    precio_unidad_cent: 243,
    unidad_canon: 'l',
    tamano_envase: 1,
    unidad_envase: 'l',
  },
]

const RECETA = {
  id: 7,
  nombre: 'Tortilla de patatas',
  creada: '2026-11-01T10:00:00Z',
  archivada: false,
  version: 2,
  raciones: 4,
  raciones_receta: 4,
  escalada: false,
  preparacion: 'Pela y corta las patatas.\nPocha las patatas y la cebolla.\nCuaja la tortilla.',
  minutos: 30,
  etiquetas: '',
  ingredientes: INGREDIENTES,
} as unknown as Receta

const PREVIA = {
  version: 2,
  raciones: 4,
  lineas: [
    {
      clave: 'huevos',
      texto: 'Huevos',
      producto_id: 'dia:huevos-1',
      cantidad: 6,
      unidad: 'ud',
      envases: 1,
      tamano_envase: 6,
      sobrante: 0,
      de_donde: ['Huevos'],
    },
  ],
  sin_cantidad: [],
  sin_consolidar: [],
  nota: '',
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

function monta(ruta = '/recetas/7') {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path="/recetas/:recetaId" element={<RecetaDetalle />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(yo).mockResolvedValue(SESION)
  vi.mocked(useReceta).mockReturnValue(consulta(RECETA))
  vi.mocked(usePasarALista).mockReturnValue(mutacion() as never)
  vi.mocked(usePreviaDeCompra).mockReturnValue(consulta(PREVIA))
  vi.mocked(useCambiarReceta).mockReturnValue(mutacion() as never)
  vi.mocked(misListas).mockResolvedValue([{ id: 'l1', nombre: 'Casa', es_de_casa: true }])
  vi.mocked(pide).mockResolvedValue({ versiones: [1, 2] } as never)
})

describe('RecetaDetalle · ingredientes, coste y pasos', () => {
  it('*** el coste sale de los precios reales, con las unidades convertidas ***', async () => {
    monta()

    // *Huevos 1,80 + patatas 0,24 (200 g de 1 kg a 1,20) + cebolla 1,29 + aceite 0,49.*
    expect((await screen.findAllByText('3,82 €')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/0,96\s*€\s*\/\s*ración/)).toBeInTheDocument()
    // *La cadena sale del producto que puso el precio: no se inventa.*
    expect(screen.getByText('Precios de DIA')).toBeInTheDocument()
  })

  it('*** cada ingrediente lleva su coste, y los envases enteros van aparte ***', async () => {
    monta()
    await screen.findAllByText('3,82 €')

    expect(screen.getByText('1,80 €')).toBeInTheDocument()
    expect(screen.getByText('0,24 €')).toBeInTheDocument()
    expect(screen.getByText('1,29 €')).toBeInTheDocument()
    expect(screen.getByText('0,49 €')).toBeInTheDocument()
    expect(screen.getByText(/Comprando los envases enteros/)).toBeInTheDocument()
    expect(screen.getByText('6,72 €')).toBeInTheDocument()
  })

  it('*** los ingredientes y las cantidades que trae la receta se enseñan siempre ***', async () => {
    monta()

    expect(await screen.findByText('Huevos')).toBeInTheDocument()
    expect(screen.getByText('6 ud')).toBeInTheDocument()
    expect(screen.getByText('200 g')).toBeInTheDocument()
    expect(screen.getByText('200 ml')).toBeInTheDocument()
    expect(screen.getByText('1 ud')).toBeInTheDocument()
  })

  it('*** los pasos salen numerados, uno por linea ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Preparación' })

    const pasos = screen.getByRole('list', { name: /Preparación|pasos/i })
    expect(within(pasos).getAllByRole('listitem')).toHaveLength(3)
    expect(within(pasos).getByText('Pela y corta las patatas.')).toBeInTheDocument()
  })

  it('*** con todos los precios, el total se llama total y no parcial ***', async () => {
    monta()
    await screen.findAllByText('3,82 €')

    expect(screen.queryByText('Parcial')).not.toBeInTheDocument()
    expect(screen.getByText('Total')).toBeInTheDocument()
  })
})

describe('RecetaDetalle · el coste que no esta', () => {
  it('*** sin ningun precio dice «Coste no disponible» y no pinta un total falso ***', async () => {
    vi.mocked(useReceta).mockReturnValue(
      consulta({
        ...RECETA,
        ingredientes: INGREDIENTES.map((i) => ({ ...i, precio_cent: null, precio_unidad_cent: null })),
      } as unknown as Receta),
    )
    monta()

    expect(await screen.findByText('Coste no disponible')).toBeInTheDocument()
    expect(screen.getByText(/Faltan precios de/)).toBeInTheDocument()
    expect(screen.queryByText(/0,00\s*€/)).not.toBeInTheDocument()
    expect(screen.getAllByText('sin coste').length).toBeGreaterThanOrEqual(1)
  })

  it('*** un total incompleto se dice parcial, con lo que falta y la cadena ***', async () => {
    vi.mocked(useReceta).mockReturnValue(
      consulta({
        ...RECETA,
        ingredientes: [...INGREDIENTES, { texto: 'Sal', cantidad: 5, unidad: 'g' }],
      } as unknown as Receta),
    )
    monta()

    expect((await screen.findAllByText('3,82 €')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Parcial')).toBeInTheDocument()
    expect(screen.getByText('Falta el precio de Sal.')).toBeInTheDocument()
    expect(screen.getByText('Precios de DIA')).toBeInTheDocument()
    expect(screen.getByText('Total parcial')).toBeInTheDocument()
  })

  it('*** un ingrediente sin cantidad lo dice, en vez de contarlo como cero ***', async () => {
    vi.mocked(useReceta).mockReturnValue(
      consulta({
        ...RECETA,
        ingredientes: [
          ...INGREDIENTES,
          { texto: 'Sal', producto_id: 'dia:sal-1', precio_cent: 60, precio_unidad_cent: 60,
            unidad_canon: 'kg', tamano_envase: 1, unidad_envase: 'kg' },
        ],
      } as unknown as Receta),
    )
    monta()

    expect(await screen.findByText('Sal no dice cuánto lleva.')).toBeInTheDocument()
    expect(screen.getByText('sin cantidad')).toBeInTheDocument()
    expect(screen.getByText('Parcial')).toBeInTheDocument()
  })
})

describe('RecetaDetalle · las acciones y los estados', () => {
  it('*** se puede empezar a cocinar la version que se esta viendo ***', async () => {
    monta()

    expect(await screen.findByRole('link', { name: 'Empezar a cocinar' })).toHaveAttribute(
      'href',
      '/compra/cocina/7/2',
    )
  })

  it('*** añadir a la lista enseña la previa y confirma sobre la lista elegida ***', async () => {
    const pasar = mutacion()
    vi.mocked(usePasarALista).mockReturnValue(pasar as never)
    const usuario = userEvent.setup()
    monta()

    await usuario.click(await screen.findByRole('button', { name: 'Añadir a la lista' }))
    expect(await screen.findByText('Lo que habría que comprar')).toBeInTheDocument()
    await usuario.selectOptions(screen.getByLabelText('Lista de destino'), 'l1')
    await usuario.click(screen.getByRole('button', { name: 'Pasar a la lista' }))

    expect(pasar.mutate).toHaveBeenCalledWith('l1', expect.anything())
  })

  it('*** editar sigue estando, y la receta se pide con su identificador ***', async () => {
    monta()

    expect(await screen.findByRole('button', { name: 'Editar' })).toBeInTheDocument()
    expect(useReceta).toHaveBeenCalledWith(7, null, null)
  })

  it('*** se puede mirar una version anterior y se dice que lo es ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByRole('heading', { name: 'Tortilla de patatas' })

    await usuario.selectOptions(screen.getByLabelText('Versión'), '1')

    expect(screen.getByText('Estás viendo una versión anterior. La última es la 2.')).toBeInTheDocument()
    expect(useReceta).toHaveBeenLastCalledWith(7, 1, null)
  })

  it('*** se puede pedir para otras raciones y se mandan a la receta ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Tortilla de patatas' })

    fireEvent.change(screen.getByLabelText(/Para/), { target: { value: '6' } })

    expect(useReceta).toHaveBeenLastCalledWith(7, null, 6)
  })

  it('*** al escalar se dicen las dos cifras: la pedida y la de la receta ***', async () => {
    vi.mocked(useReceta).mockReturnValue(
      consulta({ ...RECETA, raciones: 6, raciones_receta: 4, escalada: true }),
    )
    monta()

    expect(await screen.findByText(/Calculado para 6; la receta es de 4/)).toBeInTheDocument()
  })

  it('*** un 404 no es un fallo: se dice que esa receta no existe ***', async () => {
    vi.mocked(useReceta).mockReturnValue(
      consulta(undefined, {
        data: undefined,
        error: new ErrorApi(404, 'no hay receta 7'),
      }),
    )
    monta()

    expect(await screen.findByText('Esa receta no existe')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Vuelve al recetario/ })).toHaveAttribute(
      'href',
      '/recetas',
    )
  })

  it('*** sin sesion se dice con la salida puesta, no con un error ***', async () => {
    vi.mocked(yo).mockResolvedValue({ usuario: null, preferencias: {} })
    monta()

    expect(await screen.findByText(/Entra para ver/)).toBeInTheDocument()
  })

  it('*** mientras carga reserva el sitio, no una linea de texto ***', () => {
    vi.mocked(useReceta).mockReturnValue(consulta(undefined, { data: undefined, isPending: true }))
    monta()

    expect(screen.getAllByRole('status').length).toBeGreaterThanOrEqual(1)
  })

  it('*** si falla, se dice y se puede volver a intentarlo ***', async () => {
    const refetch = vi.fn()
    vi.mocked(useReceta).mockReturnValue(
      consulta(undefined, { data: undefined, error: new Error('sin red'), refetch }),
    )
    const usuario = userEvent.setup()
    monta()

    expect(await screen.findByText('No he podido traer la receta')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Volver a intentarlo' }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Tortilla de patatas' })

    for (const objetivo of [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]) {
      expect(objetivo.className).toMatch(/min-h-\[(44|56|64)px\]/)
    }
  })

  it('*** habla de la receta, no de como esta hecha (§8) ***', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Tortilla de patatas' })

    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(
      /\bAPI\b|endpoint|token|caché|base de datos|scraper|gold|cálculo|se calcula/i,
    )
  })
})

describe('RecetaDetalle · las piezas puras del coste', () => {
  const arroz = (extra: Partial<IngredienteDeLaApi> = {}): IngredienteDeLaApi => ({
    texto: 'Arroz',
    cantidad: 200,
    unidad: 'g',
    ...extra,
  })

  const conPrecio = arroz({
    precio_cent: 120,
    precio_unidad_cent: 120,
    unidad_canon: 'kg',
    tamano_envase: 1,
    unidad_envase: 'kg',
  })

  it('*** 200 g de un paquete de 1 kg a 1,20 € son 0,24 €, no 240 € ***', () => {
    const precio = precioParaElCoste(conPrecio)
    expect(precio).not.toBeNull()
    expect(precio?.precioEnvaseCent).toBe(120)
    expect(precio?.cantidadEnvase).toBe(1000)
    // *0,12 céntimos el gramo, no 120.*
    expect(precio?.precioUnidadCent).toBeCloseTo(0.12)

    const c = costeDeLaReceta([conPrecio])
    expect(c.usadoCent).toBe(24)
    expect(c.envasesCent).toBe(120)
    expect(c.completo).toBe(true)
    expect(c.sinPrecio).toEqual([])
    expect(c.cadenas).toEqual([])
  })

  it('*** y al revés: 0,2 kg de un envase de 1.000 g tampoco se equivoca ***', () => {
    const enKilos = arroz({
      cantidad: 0.2,
      unidad: 'kg',
      precio_cent: 120,
      precio_unidad_cent: 120,
      unidad_canon: 'kg',
      tamano_envase: 1000,
      unidad_envase: 'g',
    })
    const c = costeDeLaReceta([enKilos])
    expect(c.usadoCent).toBe(24)
    expect(c.completo).toBe(true)
  })

  it('*** un ingrediente sin precio no es un cero, y el total de todos es null ***', () => {
    expect(precioParaElCoste(arroz({ precio_cent: null, precio_unidad_cent: null }))).toBeNull()

    const c = costeDeLaReceta([
      arroz({ precio_cent: null, precio_unidad_cent: null }),
      arroz({ texto: 'Sal', cantidad: null, unidad: null }),
    ])
    expect(c.usadoCent).toBeNull()
    expect(c.envasesCent).toBeNull()
    expect(c.completo).toBe(false)
    expect(c.sinPrecio).toEqual(['Arroz', 'Sal'])
    expect(c.sinCantidad).toEqual(['Sal'])
  })

  it('*** un total a medias se llama parcial y dice de qué cadena sale ***', () => {
    const c = costeDeLaReceta([
      { ...conPrecio, producto_id: 'dia:arroz-1' },
      arroz({ texto: 'Sal', cantidad: 5, unidad: 'g' }),
    ])
    expect(c.usadoCent).toBe(24)
    expect(c.completo).toBe(false)
    expect(c.cadenas).toEqual(['DIA'])
    expect(avisosDeCobertura(c)).toContain('Falta el precio de Sal.')
  })

  it('*** los avisos nombran lo que falta, en singular y en plural ***', () => {
    const c = costeDeLaReceta([
      arroz({ texto: 'Arroz', precio_cent: null }),
      arroz({ texto: 'Sal', cantidad: null, unidad: null }),
    ])
    const avisos = avisosDeCobertura(c)
    expect(avisos).toContain('Faltan precios de Arroz y Sal.')
    expect(avisos).toContain('Sal no dice cuánto lleva.')
  })

  it('*** los pasos quitan la numeración que ya trajera el texto ***', () => {
    expect(pasosDePreparacion('1. Pela\n2) Corta\n\nCuaja')).toEqual([
      'Pela',
      'Corta',
      'Cuaja',
    ])
    expect(pasosDePreparacion('   ')).toEqual([])
  })

  it('*** las cadenas se enumeran como se leen ***', () => {
    expect(enEspanol(['Mercadona'])).toBe('Mercadona')
    expect(enEspanol(['Mercadona', 'DIA'])).toBe('Mercadona y DIA')
    expect(enEspanol(['Mercadona', 'DIA', 'Lidl'])).toBe('Mercadona, DIA y Lidl')
  })
})
