/** *** FAVORITOS, MONTADA: LA TARJETA DEL ARTBOARD Y LO QUE NO SE PUEDE PERDER. ***
 *
 *  *Lo que se mide aquí no es el aspecto -- eso se mira en una captura -- sino lo que la pantalla
 *  **afirma**: que el rango sale de la serie de ESE producto y de ninguna otra, que sin serie no se
 *  inventa, que el cambio dice los días que hay de verdad, que la ventana de 7/30/90 sigue viva y
 *  que quitar y pasar a la lista no han desaparecido.*
 *
 *  *`useGrupo` se sustituye para poder dar una serie distinta a cada favorito; el resto de la
 *  pantalla usa sus consultas de verdad contra los mocks de la API.*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import type { Favorito, Grupo, Lista, PuntoSerie, Sesion } from '../tipos'

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, yo: vi.fn(), misListas: vi.fn(), anadirDesdeFavoritos: vi.fn() }
})

vi.mock('../api/favoritos', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, verFavoritos: vi.fn(), quitarFavorito: vi.fn() }
})

vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, useGrupo: vi.fn() }
})

import { anadirDesdeFavoritos, misListas, yo } from '../api/cesta'
import { useGrupo } from '../api/consultas'
import { quitarFavorito, verFavoritos } from '../api/favoritos'
import { estadoDelRango, Favoritos, rangoDeLaSerie, textoDelCambio } from './Favoritos'

const SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: null },
  preferencias: {},
}

const LISTA: Lista = { id: 'l1', nombre: 'Casa', es_de_casa: true }

const FAV_BAJA: Favorito = {
  grupo_id: 7,
  producto_id: 'dia:7',
  nombre: 'Alubia blanca 1 kg',
  cadena: 'dia',
  unidad: 'kg',
  precio_cent: 199,
  precio_unidad_cent: 199,
  comparable: true,
  variacion_pct: -8.7,
  precio_unidad_antes_cent: 218,
  dias_medidos: 7,
  dias: 7,
}

const FAV_SUBE: Favorito = {
  grupo_id: 8,
  producto_id: 'dia:8',
  nombre: 'Garbanzos 1 kg',
  cadena: 'dia',
  unidad: 'kg',
  precio_cent: 215,
  precio_unidad_cent: 215,
  comparable: true,
  variacion_pct: 2.1,
  precio_unidad_antes_cent: 210,
  dias_medidos: 7,
  dias: 7,
}

const FAV_SIN: Favorito = {
  grupo_id: 9,
  producto_id: 'mercadona:9',
  nombre: 'Leche entera 1,5 l',
  cadena: 'mercadona',
  unidad: 'l',
  precio_cent: 189,
  precio_unidad_cent: 126,
  comparable: false,
  motivo: 'sin historico',
  dias: 7,
}

const SERIE_BAJA: PuntoSerie[] = [
  { producto_id: 'dia:7', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 439, unidad_canon: 'kg' },
  { producto_id: 'dia:7', fuente: 'dia', fecha: '2026-11-05', precio_unidad_cent: 199, unidad_canon: 'kg' },
]

const SERIE_SUBE: PuntoSerie[] = [
  { producto_id: 'dia:8', fuente: 'dia', fecha: '2026-11-03', precio_unidad_cent: 209, unidad_canon: 'kg' },
  { producto_id: 'dia:8', fuente: 'dia', fecha: '2026-11-05', precio_unidad_cent: 459, unidad_canon: 'kg' },
]

function grupo(id: number, serie: PuntoSerie[]): Grupo {
  return {
    grupo_id: id,
    nombre: 'Un grupo',
    imagen: null,
    unidad: 'kg',
    cadenas: 1,
    ahorro_pct: 0,
    ahorro_cent: 0,
    productos: [],
    serie,
  }
}

function consulta<T>(data: T) {
  return {
    data,
    isPending: false,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  } as never
}

function respuesta(favoritos: Favorito[], dias = 7) {
  return { favoritos, dias, fecha_datos: '2026-11-05' }
}

function monta() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/compra/favoritos']}>
        <Favoritos />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(yo).mockResolvedValue(SESION)
  vi.mocked(misListas).mockResolvedValue([LISTA])
  vi.mocked(verFavoritos).mockResolvedValue(respuesta([FAV_BAJA, FAV_SUBE, FAV_SIN]))
  vi.mocked(anadirDesdeFavoritos).mockResolvedValue(1)
  vi.mocked(quitarFavorito).mockResolvedValue({ hecho: true })
  vi.mocked(useGrupo).mockImplementation(((id: number | null) => {
    if (id === 7) return consulta(grupo(7, SERIE_BAJA))
    if (id === 8) return consulta(grupo(8, SERIE_SUBE))
    return consulta(grupo(Number(id ?? 0), []))
  }) as never)
})

describe('Favoritos · la tarjeta del artboard', () => {
  it('*** enseña nombre, cadena, precio y el estado del rango ***', async () => {
    monta()

    expect(await screen.findByText('Alubia blanca 1 kg')).toBeInTheDocument()
    expect(screen.getByText('3 productos')).toBeInTheDocument()
    expect(screen.getAllByText(/1,99\s*€\/kg/).length).toBeGreaterThan(0)
    expect(screen.getAllByText('DIA').length).toBeGreaterThan(0)
    expect(await screen.findByText('en el mínimo')).toBeInTheDocument()
    expect(screen.getByText('Historial de 5 días')).toBeInTheDocument()
    expect(screen.getAllByText(/4,39\s*€\/kg/).length).toBeGreaterThan(0)
  })

  it('*** el rango y el cambio salen de la serie real, sin inventar días ***', async () => {
    monta()

    await screen.findByText('Alubia blanca 1 kg')
    expect(screen.getByText(/ha bajado un 8,7\s*% en 7 días/)).toBeInTheDocument()
    expect(screen.getByText('cerca del mínimo')).toBeInTheDocument()
  })

  it('*** sin serie no hay barra ni estado de rango: queda el cambio real ***', async () => {
    vi.mocked(verFavoritos).mockResolvedValue(respuesta([FAV_BAJA]))
    vi.mocked(useGrupo).mockReturnValue(consulta(grupo(7, [])))

    monta()

    await screen.findByText('Alubia blanca 1 kg')
    expect(screen.queryByText(/Historial de/)).not.toBeInTheDocument()
    expect(screen.queryByText('en el mínimo')).not.toBeInTheDocument()
    expect(screen.getAllByText(/ha bajado un 8,7\s*% en 7 días/).length).toBeGreaterThan(0)
  })

  it('*** el corazón está puesto, quita, y lo dice ***', async () => {
    const usuario = userEvent.setup()
    monta()

    const corazones = await screen.findAllByRole('button', { name: 'Quitar de favoritos' })
    expect(corazones[0]).toHaveAttribute('aria-pressed', 'true')
    await usuario.click(corazones[0])

    expect(quitarFavorito).toHaveBeenCalledWith(7, 'dia:7')
    expect(await screen.findByText('Quitado de favoritos')).toBeInTheDocument()
  })

  it('*** pasar un favorito a la lista sigue estando ***', async () => {
    const usuario = userEvent.setup()
    monta()

    const botones = await screen.findAllByRole('button', { name: 'A la lista' })
    await usuario.click(botones[0])

    expect(anadirDesdeFavoritos).toHaveBeenCalledWith('l1', {
      grupo_ids: [7],
      producto_ids: [],
    })
    expect(await screen.findByText('Añadido a la lista')).toBeInTheDocument()
  })

  it('*** la ventana de 7/30/90 se mantiene y se dice con palabras ***', async () => {
    const usuario = userEvent.setup()
    monta()

    await screen.findByText('Alubia blanca 1 kg')
    expect(screen.getByText('Ventana activa: 7 días')).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: '30 días' }))

    await waitFor(() => expect(verFavoritos).toHaveBeenCalledWith(30))
    expect(await screen.findByText('Ventana activa: 30 días')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '30 días' })).toHaveAttribute(
      'aria-pressed', 'true',
    )
  })

  it('*** el orden de la API se respeta: primero lo que ha bajado ***', async () => {
    monta()

    await screen.findByText('Alubia blanca 1 kg')
    const sentidos = [...document.querySelectorAll('[data-cambio]')]
      .map((e) => e.getAttribute('data-cambio'))
    expect(sentidos).toEqual(['baja', 'sube'])
  })

  it('*** §8: habla de la compra, no de cómo está hecha ***', async () => {
    monta()

    await screen.findByText('Alubia blanca 1 kg')
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(
      /\bAPI\b|endpoint|token|caché|base de datos|scraper|gold|cálculo|se calcula|captura/i,
    )
  })

  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()

    await screen.findByText('Alubia blanca 1 kg')
    const objetivos = [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]
    for (const objetivo of objetivos) {
      expect(objetivo.className).toMatch(/min-h-\[(44|56|64)px\]/)
    }
    expect(screen.getByRole('combobox').className).toMatch(/min-h-\[44px\]/)
  })
})

describe('Favoritos · los estados', () => {
  it('*** vacío: dice que no sigue nada y da por dónde empezar ***', async () => {
    vi.mocked(verFavoritos).mockResolvedValue(respuesta([]))

    monta()

    expect(await screen.findByText('No sigues ningún producto')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Buscar un producto' })).toHaveAttribute(
      'href', '/compra',
    )
    expect(screen.getByRole('link', { name: 'Ver mi lista' })).toHaveAttribute(
      'href', '/compra/listas',
    )
  })

  it('*** error: lo dice y deja reintentar ***', async () => {
    vi.mocked(verFavoritos).mockRejectedValue(new Error('sin red'))

    monta()

    expect(await screen.findByText('No he podido traer esto')).toBeInTheDocument()
    expect(screen.getByText('sin red')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Volver a intentarlo' })).toBeInTheDocument()
  })

  it('*** sin sesión, la puerta de siempre ***', async () => {
    vi.mocked(yo).mockResolvedValue({ usuario: null, preferencias: {} })

    monta()

    expect(await screen.findByText('Entra para ver tus favoritos')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'la lista' })).toHaveAttribute(
      'href', '/compra/listas',
    )
  })

  it('*** un favorito que ya no está se dice en vez de desaparecer ***', async () => {
    vi.mocked(verFavoritos).mockResolvedValue(respuesta([
      {
        grupo_id: 99, producto_id: null, nombre: null, comparable: false,
        desconocido: true, que: 'grupo', motivo: 'ya no esta en el catalogo',
      },
    ]))

    monta()

    expect(await screen.findByText('ya no está')).toBeInTheDocument()
    expect(screen.getByText('Este producto ya no está en el catálogo.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument()
  })
})

describe('el rango, con la serie de verdad', () => {
  it('*** no mezcla productos: si no hay puntos de ESE producto, no hay rango ***', () => {
    expect(rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 100, unidad_canon: 'kg' },
      { producto_id: 'dia:2', fuente: 'dia', fecha: '2026-11-02', precio_unidad_cent: 200, unidad_canon: 'kg' },
    ], 'dia:1', 100, 'kg')).toBeNull()
  })

  it('*** no mezcla unidades: kg un día y l otro no tienen mínimo ***', () => {
    expect(rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 100, unidad_canon: 'kg' },
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-02', precio_unidad_cent: 200, unidad_canon: 'l' },
    ], 'dia:1', 150, 'kg')).toBeNull()
  })

  it('*** con un solo precio no hay rango ***', () => {
    expect(rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 100, unidad_canon: 'kg' },
    ], 'dia:1', 150, 'kg')).toBeNull()
  })

  it('*** el mínimo, el máximo y los días son los de la serie ***', () => {
    const r = rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 100, unidad_canon: 'kg' },
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-02', precio_unidad_cent: 200, unidad_canon: 'kg' },
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-03', precio_unidad_cent: 300, unidad_canon: 'kg' },
    ], 'dia:1', 150, 'kg')

    expect(r).toMatchObject({
      minimo: 100, maximo: 300, actual: 150, dias: 3, posicion: 25, unidad: 'kg',
    })
    expect(estadoDelRango(r as NonNullable<typeof r>).texto).toBe('ni mínimo ni máximo')
  })

  it('*** el precio de hoy entra en el rango aunque la serie no lo traiga ***', () => {
    const r = rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 250, unidad_canon: 'kg' },
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-02', precio_unidad_cent: 300, unidad_canon: 'kg' },
    ], 'dia:1', 200, 'kg')

    expect(r?.minimo).toBe(200)
    expect(r?.posicion).toBe(0)
  })

  it('*** un precio plano no se llama «mínimo»: es «sin cambios» ***', () => {
    const r = rangoDeLaSerie([
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-01', precio_unidad_cent: 250, unidad_canon: 'kg' },
      { producto_id: 'dia:1', fuente: 'dia', fecha: '2026-11-02', precio_unidad_cent: 250, unidad_canon: 'kg' },
    ], 'dia:1', 250, 'kg')

    expect(r && estadoDelRango(r).texto).toBe('sin cambios')
  })
})

describe('el cambio, dicho como se lee', () => {
  it('*** baja y sube con la ventana real ***', () => {
    expect(textoDelCambio({ ...FAV_BAJA, dias_medidos: 3 }, 7)).toMatch(
      /ha bajado un 8,7\s*% en 3 días/,
    )
    expect(textoDelCambio({ ...FAV_SUBE, dias_medidos: 7 }, 7)).toMatch(
      /ha subido un 2,1\s*% en 7 días/,
    )
  })

  it('*** un cero no es una bajada ***', () => {
    expect(textoDelCambio({ ...FAV_BAJA, variacion_pct: 0, dias_medidos: 7 }, 7)).toMatch(
      /sin cambios en 7 días/,
    )
  })

  it('*** sin cambio medido no se inventa un texto ***', () => {
    expect(textoDelCambio(FAV_SIN, 7)).toBeNull()
  })
})
