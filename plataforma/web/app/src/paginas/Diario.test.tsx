/** *** EL DIARIO, MONTADO: LA PANTALLA DEL ARTBOARD Y LO QUE NO SE PUEDE PERDER. ***
 *
 *  *Lo que se mide aquí no es el aspecto -- eso se mira en una captura -- sino lo que la pantalla
 *  **afirma**: que el día y las comidas salen de lo anotado, que sin objetivo no se inventa una
 *  cifra, que un alimento sin kcal dice «sin dato» y no cuenta como cero, y que añadir, quitar,
 *  navegar y la puerta de sesión siguen donde estaban.*
 *
 *  *El artboard es `designs/cesta-app/project/Calorias.dc.html` (390 x 844). Los datos de la prueba
 *  son los suyos: desayuno 321, comida 440, cena 314, objetivo 2.200.*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import type { Sesion } from '../tipos'
import type { Dia, Entrada } from '../api/diario'

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    yo: vi.fn(),
    misListas: vi.fn(),
    guardaPreferencia: vi.fn(),
    previaDeLaCompra: vi.fn(),
    anotarDeLaCompra: vi.fn(),
  }
})

vi.mock('../api/diario', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, useDia: vi.fn(), useBorrarEntrada: vi.fn() }
})

import {
  anotarDeLaCompra, guardaPreferencia, misListas, previaDeLaCompra, yo,
} from '../api/cesta'
import { useBorrarEntrada, useDia } from '../api/diario'
import { Diario } from './Diario'

const FECHA_LARGA = new Intl.DateTimeFormat('es-ES', {
  weekday: 'long',
  day: 'numeric',
  month: 'short',
})

/** El día que la pantalla pide por defecto, calculado como lo calcula ella. */
function hoyIso(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

const HOY = hoyIso()

const SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: 'David' },
  preferencias: {},
}

function entrada(
  id: number,
  comida: string,
  referencia: string,
  cantidad: number,
  kcal: number | null,
): Entrada {
  return {
    id,
    fecha: HOY,
    comida,
    tipo: 'alimento',
    referencia,
    version: null,
    cantidad_g: cantidad,
    kcal,
    proteinas_g: null,
    grasas_g: null,
    hidratos_g: null,
    fuente_dato: 'etiqueta',
    nota: '',
  }
}

const DESAYUNO = [
  entrada(1, 'desayuno', 'Pan de molde', 60, 164),
  entrada(2, 'desayuno', 'Tortilla', 100, 157),
]
const COMIDA = [
  entrada(3, 'comida', 'Arroz', 80, 278),
  entrada(4, 'comida', 'Pechuga de pollo', 150, 162),
]
const CENA = [
  entrada(5, 'cena', 'Atún en aceite', 80, 150),
  entrada(6, 'cena', 'Pan de molde', 60, 164),
]

/** El día del artboard: 321 + 440 + 314 = 1.075 kcal, todo con dato. */
function diaDelArtboard(): Dia {
  return {
    fecha: HOY,
    entradas: [...DESAYUNO, ...COMIDA, ...CENA],
    comidas: { desayuno: DESAYUNO, comida: COMIDA, cena: CENA },
    conocido: {
      entradas: 6,
      kcal: 1075,
      proteinas_g: null,
      grasas_g: null,
      hidratos_g: null,
    },
    cobertura: {
      kcal: { con_dato: 6, total: 6, completa: true },
      proteinas_g: { con_dato: 0, total: 6, completa: false },
      grasas_g: { con_dato: 0, total: 6, completa: false },
      hidratos_g: { con_dato: 0, total: 6, completa: false },
    },
    sin_dato: [],
    completo: true,
  }
}

/** Los datos que devuelve la consulta del día, con la forma que usa React Query. */
function consulta(datos: Dia | undefined, extra: Record<string, unknown> = {}) {
  return {
    data: datos,
    isPending: false,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...extra,
  } as never
}

function monta() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/calorias']}>
        <Diario />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(yo).mockResolvedValue(SESION)
  vi.mocked(misListas).mockResolvedValue([])
  vi.mocked(guardaPreferencia).mockResolvedValue(undefined)
  vi.mocked(previaDeLaCompra).mockResolvedValue(undefined as never)
  vi.mocked(anotarDeLaCompra).mockResolvedValue(undefined as never)
  vi.mocked(useBorrarEntrada).mockReturnValue({
    mutate: vi.fn(), isPending: false, variables: undefined, error: null,
  } as never)
  vi.mocked(useDia).mockReturnValue(consulta(diaDelArtboard()))
})

describe('Diario · la pantalla del artboard', () => {
  it('*** enseña la fecha, «Calorías» y el objetivo en la cabecera ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      ...SESION,
      preferencias: { [`objetivo:${HOY}`]: { kcal: 2200 } },
    })
    monta()

    expect(await screen.findByRole('heading', { name: 'Calorías' })).toBeInTheDocument()
    expect(screen.getByText(FECHA_LARGA.format(new Date(`${HOY}T00:00:00`)))).toBeInTheDocument()
    expect(screen.getByText('2.200 kcal')).toBeInTheDocument()
  })

  it('*** HOY: lo consumido, el objetivo y lo que queda ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      ...SESION,
      preferencias: { [`objetivo:${HOY}`]: { kcal: 2200 } },
    })
    monta()

    expect(await screen.findByRole('heading', { name: 'Hoy' })).toBeInTheDocument()
    expect(screen.getByText('1.075')).toBeInTheDocument()
    expect(screen.getByText('de 2.200 kcal')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.getByText('Te quedan 1.125 kcal')).toBeInTheDocument()
  })

  it('*** las comidas con sus alimentos, cantidades y kcal reales ***', async () => {
    monta()

    expect(await screen.findByRole('heading', { name: 'Desayuno' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Comida' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cena' })).toBeInTheDocument()
    expect(screen.getAllByText('Pan de molde')).toHaveLength(2)
    expect(screen.getAllByText(/60 g/)).toHaveLength(2)
    expect(screen.getAllByText('164 kcal').length).toBeGreaterThan(0)
    expect(screen.getByText('321 kcal')).toBeInTheDocument()
    expect(screen.getByText('440 kcal')).toBeInTheDocument()
    expect(screen.getByText('314 kcal')).toBeInTheDocument()
  })
})

describe('Diario · el objetivo, sin inventar', () => {
  it('*** sin objetivo: dice «Sin objetivo» y ofrece ponerlo ***', async () => {
    monta()

    expect(await screen.findByText('Sin objetivo')).toBeInTheDocument()
    expect(screen.queryByText(/de 2\.200 kcal/)).not.toBeInTheDocument()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Tu objetivo diario')).toBeInTheDocument()
  })

  it('*** guardar el objetivo escribe la preferencia del día ***', async () => {
    const usuario = userEvent.setup()
    monta()

    const campo = await screen.findByLabelText('Tu objetivo diario')
    await usuario.type(campo, '2000')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(guardaPreferencia).toHaveBeenCalled())
    const [clave, valor] = vi.mocked(guardaPreferencia).mock.calls[0]
    expect(clave).toMatch(/^objetivo:\d{4}-\d{2}-\d{2}$/)
    expect(valor).toEqual({ kcal: 2000 })
  })

  it('*** un objetivo guardado se puede cambiar y quitar ***', async () => {
    const usuario = userEvent.setup()
    vi.mocked(yo).mockResolvedValue({
      ...SESION,
      preferencias: { [`objetivo:${HOY}`]: { kcal: 2200 } },
    })
    monta()

    await usuario.click(await screen.findByRole('button', { name: 'Cambiar objetivo' }))
    await usuario.click(screen.getByRole('button', { name: 'Quitar' }))

    await waitFor(() => expect(guardaPreferencia).toHaveBeenCalledWith(
      `objetivo:${HOY}`, null,
    ))
  })
})

describe('Diario · lo que no se sabe no es cero', () => {
  it('*** un alimento sin kcal dice «sin dato» y el día avisa de lo que falta ***', async () => {
    const sinDato = entrada(2, 'desayuno', 'Pan sin etiqueta', 60, null)
    const conDato = entrada(1, 'desayuno', 'Arroz', 80, 200)
    vi.mocked(useDia).mockReturnValue(consulta({
      fecha: HOY,
      entradas: [conDato, sinDato],
      comidas: { desayuno: [conDato, sinDato] },
      conocido: {
        entradas: 1, kcal: 200, proteinas_g: null, grasas_g: null, hidratos_g: null,
      },
      cobertura: {
        kcal: { con_dato: 1, total: 2, completa: false },
        proteinas_g: { con_dato: 0, total: 2, completa: false },
        grasas_g: { con_dato: 0, total: 2, completa: false },
        hidratos_g: { con_dato: 0, total: 2, completa: false },
      },
      sin_dato: [2],
      completo: false,
    }))

    monta()

    expect(await screen.findByText('Pan sin etiqueta')).toBeInTheDocument()
    expect(screen.getAllByText('sin dato').length).toBeGreaterThan(0)
    expect(screen.getByText('Una entrada sin dato de energía.')).toBeInTheDocument()
    expect(screen.getByText(/no está completo/)).toBeInTheDocument()
  })
})

describe('Diario · los estados y lo que ya hacía', () => {
  it('*** cargando: enseña el hueco con su nombre para el lector ***', async () => {
    vi.mocked(useDia).mockReturnValue(consulta(undefined, { isPending: true }))
    monta()

    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/Cargando tu diario/)).toBeInTheDocument()
  })

  it('*** error: lo dice y deja reintentar ***', async () => {
    const reintentar = vi.fn()
    vi.mocked(useDia).mockReturnValue(consulta(undefined, {
      isError: true,
      error: new Error('No he podido leer tu diario.'),
      refetch: reintentar,
    }))
    monta()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('No he podido leer tu diario.')).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Volver a intentarlo' }))
    expect(reintentar).toHaveBeenCalled()
  })

  it('*** sin comidas: el vacío y la puerta para añadir ***', async () => {
    vi.mocked(useDia).mockReturnValue(consulta({
      ...diaDelArtboard(),
      entradas: [],
      comidas: {},
      conocido: {
        entradas: 0, kcal: null, proteinas_g: null, grasas_g: null, hidratos_g: null,
      },
      cobertura: {
        kcal: { con_dato: 0, total: 0, completa: false },
        proteinas_g: { con_dato: 0, total: 0, completa: false },
        grasas_g: { con_dato: 0, total: 0, completa: false },
        hidratos_g: { con_dato: 0, total: 0, completa: false },
      },
      sin_dato: [],
      completo: false,
    }))
    monta()

    expect(await screen.findByText('Nada anotado este día')).toBeInTheDocument()
    expect(screen.getAllByText('sin dato').length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: 'Añadir' })).toHaveAttribute('href', '#alta')
  })

  it('*** añadir y quitar siguen enteros ***', async () => {
    const usuario = userEvent.setup()
    const quitar = vi.fn()
    vi.mocked(useBorrarEntrada).mockReturnValue({
      mutate: quitar, isPending: false, variables: undefined, error: null,
    } as never)
    monta()

    await usuario.click((await screen.findAllByRole('button', { name: 'Quitar Pan de molde' }))[0])
    expect(quitar).toHaveBeenCalledWith(1)

    expect(screen.getByLabelText('Qué has comido')).toBeInTheDocument()
    expect(screen.getByLabelText('Energía (kcal)')).toBeInTheDocument()
    expect(screen.getByLabelText('Cantidad (g)')).toBeInTheDocument()
    expect(screen.getByLabelText('Proteínas (g)')).toBeInTheDocument()
    expect(screen.getByLabelText('De dónde sale el dato')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Es una receta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anotar' })).toBeInTheDocument()
    expect(screen.getByText('De la compra al diario')).toBeInTheDocument()
  })

  it('*** navegar por días sigue estando, y «Hoy» vuelve ***', async () => {
    const usuario = userEvent.setup()
    monta()

    const campo = await screen.findByLabelText('Día')
    expect(campo).toHaveValue(HOY)

    fireEvent.change(campo, { target: { value: '2026-11-05' } })
    await waitFor(() => expect(useDia).toHaveBeenCalledWith('2026-11-05'))

    await usuario.click(screen.getByRole('button', { name: 'Hoy' }))
    await waitFor(() => expect(vi.mocked(useDia).mock.calls.at(-1)?.[0]).toBe(HOY))
  })

  it('*** §8: habla del día, no de cómo está hecho ***', async () => {
    monta()

    await screen.findByRole('heading', { name: 'Hoy' })
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(
      /\bAPI\b|endpoint|token|caché|base de datos|scraper|gold|cálculo|se calcula|captura/i,
    )
  })

  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()

    await screen.findByRole('heading', { name: 'Hoy' })
    const objetivos = [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]
    for (const objetivo of objetivos) {
      expect(objetivo.className).toMatch(/min-h-\[(44|56|64)px\]/)
    }
    for (const campo of screen.getAllByRole('combobox')) {
      expect(campo.className).toMatch(/min-h-\[44px\]/)
    }
  })
})
