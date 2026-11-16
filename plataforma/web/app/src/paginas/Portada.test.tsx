/** La portada: los cuatro estados, los datos reales y las reglas de movil.
 *
 *  *Lo que se comprueba no es el aspecto -- eso se mira en una captura -- sino
 *  lo que no da error al incumplirlo: que sin sesion no se inventen cifras, que
 *  el buscador navegue, que la barra marque donde estas, que todo lo que se
 *  pulsa llegue a 44 px y que la pantalla no cuente como esta hecha (§8).*
 *
 *  *Los datos son los de la API, recortados: `reparto`, `misListas`, `verLista`
 *  y `useBajadas`. Si el componente inventara un total, estas pruebas lo verian
 *  porque el total de la cadena mas barata sale de `una_tienda`, no de una
 *  constante.*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useLocation } from 'react-router-dom'

import type { Baja, Lista, RepartoTiendas, RespuestaBajadas, RespuestaSecciones, Sesion } from '../tipos'
import type { DetalleLista } from '../api/cesta'

vi.mock('../api/cesta', () => ({
  yo: vi.fn(),
  misListas: vi.fn(),
  verLista: vi.fn(),
  reparto: vi.fn(),
}))

vi.mock('../api/consultas', () => ({
  useBajadas: vi.fn(),
  useSecciones: vi.fn(),
}))

import { misListas, reparto, verLista, yo } from '../api/cesta'
import { useBajadas, useSecciones } from '../api/consultas'
import { Portada, fechaDeHoy } from './Portada'

const SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: null },
  preferencias: {},
}

const LISTA: Lista = { id: 'l1', nombre: 'Casa', es_de_casa: true }

const DETALLE: DetalleLista = {
  papel: 'dueno',
  lineas: [
    {
      id: 'linea-1', nombre_visto: 'Garbanzos', cantidad: 1, grupo_id: 7,
      producto_id: null, tachado_en: null,
    },
    {
      id: 'linea-2', nombre_visto: 'Leche', cantidad: 1, grupo_id: 8,
      producto_id: null, tachado_en: null,
    },
    {
      id: 'linea-3', nombre_visto: 'Pan', cantidad: 1, grupo_id: 9,
      producto_id: null, tachado_en: null,
    },
  ],
  estimacion: {
    total_cent: 1202, en_carrito_cent: 0, por_recoger_cent: 1202, lineas: 3, sin_precio: 0,
  },
  personas: [],
  fecha_datos: '2026-11-04',
}

const REPARTO: RepartoTiendas = {
  sublistas: [],
  sin_asignar: [],
  sin_encontrar: [],
  total_cent: 1202,
  total_sin_ofertas_cent: 1300,
  ahorro_cent: 98,
  lineas: 3,
  decididas: 3,
  sin_precio: 0,
  una_tienda: [
    {
      cadena: 'lidl', total_cent: 408, total_sin_ofertas_cent: 450,
      encontrados: 3, faltan: [],
    },
    {
      cadena: 'carrefour', total_cent: 794, total_sin_ofertas_cent: 850,
      encontrados: 3, faltan: [],
    },
  ],
  repartido: null,
  fecha_datos: '2026-11-04',
}

const BAJADA: Baja = {
  grupo_id: 7,
  nombre: 'Garbanzos Luengo 1 kg',
  marca: null,
  cadena: 'dia',
  imagen: null,
  unidad: 'kg',
  precio_cent: 419,
  precio_unidad_cent: 419,
  precio_unidad_antes_cent: 459,
  desde: '2026-09-26',
  variacion_pct: -8.7,
  promo_txt: null,
  solo_con_tarjeta: false,
  precio_antes_cent: 459,
}

const BAJADAS: RespuestaBajadas = {
  fecha_datos: '2026-11-04',
  dias: 7,
  sentido: 'bajadas',
  solo_mios: true,
  resultados: [BAJADA],
}

const SECCIONES: RespuestaSecciones = {
  fecha_datos: '2026-11-04',
  secciones: [
    { seccion: 'frutas-verduras', nombre: 'Frutas y verduras', productos: 1960, cadenas: 6, grupos: 400, comparable: true },
    { seccion: 'carniceria', nombre: 'Carnicería', productos: 2861, cadenas: 6, grupos: 500, comparable: true },
    { seccion: 'pescaderia', nombre: 'Pescadería', productos: 1825, cadenas: 6, grupos: 300, comparable: true },
    { seccion: 'lacteos-huevos', nombre: 'Lácteos y huevos', productos: 4327, cadenas: 6, grupos: 700, comparable: true },
    { seccion: 'panaderia', nombre: 'Panadería', productos: 2280, cadenas: 6, grupos: 300, comparable: true },
    { seccion: 'despensa', nombre: 'Despensa', productos: 7411, cadenas: 6, grupos: 1200, comparable: true },
    { seccion: 'bebidas', nombre: 'Bebidas', productos: 5903, cadenas: 6, grupos: 900, comparable: true },
  ],
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

function pendiente() {
  return {
    data: undefined,
    isPending: true,
    isLoading: true,
    isError: false,
    error: null,
    refetch: vi.fn(),
  } as never
}

function Donde() {
  const { pathname, search } = useLocation()
  return <p data-testid="ruta">{`${pathname}${search}`}</p>
}

function monta() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/']}>
        <Portada />
        <Donde />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(yo).mockResolvedValue(SESION)
  vi.mocked(misListas).mockResolvedValue([LISTA])
  vi.mocked(verLista).mockResolvedValue(DETALLE)
  vi.mocked(reparto).mockResolvedValue(REPARTO)
  vi.mocked(useBajadas).mockReturnValue(consulta(BAJADAS))
  vi.mocked(useSecciones).mockReturnValue(consulta(SECCIONES))
})

describe('Portada · la cabecera, el buscador y la barra de abajo', () => {
  it('*** la cabecera dice la fecha local en espanol, «Avío» y lleva la cuenta a ajustes ***', async () => {
    monta()

    // *El nombre nuevo se ve donde se mira al abrir: el `h1` de la portada. No basta con
    // proponerlo en un documento; la interfaz tiene que decirlo.*
    expect(screen.getByRole('heading', { level: 1, name: 'Avío' })).toBeInTheDocument()
    // *La fecha se pinta en versalitas; el texto sigue siendo el de `Intl`.*
    expect(screen.getByText(/^[a-záéíóúüñ]+,\s+\d{1,2}\s+[a-z]{3,4}$/i)).toBeInTheDocument()
    // *La sesion llega despues del primer pintado: se espera al dato.*
    await screen.findByText(/la más barata/i)
    expect(screen.getByRole('link', { name: 'Tu cuenta' })).toHaveAttribute('href', '/ajustes')
  })

  it('*** el buscador de verdad navega a /compra con lo que se escribe ***', async () => {
    const usuario = userEvent.setup()
    monta()

    await usuario.type(screen.getByLabelText('Buscar un producto'), 'leche entera')
    await usuario.keyboard('{Enter}')

    expect(screen.getByTestId('ruta')).toHaveTextContent('/compra?q=leche%20entera')
  })

  it('*** la barra de abajo tiene tres destinos reales y marca Compra con aria-current ***', () => {
    monta()
    const barra = screen.getByRole('navigation', { name: 'Secciones' })
    expect(within(barra).getByRole('link', { name: 'Compra' })).toHaveAttribute('aria-current', 'page')
    expect(within(barra).getByRole('link', { name: 'Recetas' })).toHaveAttribute('href', '/recetas')
    expect(within(barra).getByRole('link', { name: 'Calorías' })).toHaveAttribute('href', '/calorias')
    expect(within(barra).getAllByRole('link')).toHaveLength(3)
  })

  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()
    await screen.findByText(/la más barata/i)
    for (const objetivo of [...screen.getAllByRole('link'), ...screen.queryAllByRole('button')]) {
      expect(objetivo.className).toMatch(/min-h-\[(44|56|64)px\]/)
    }
  })

  it('*** habla de la compra, no de como esta hecha (§8) ***', async () => {
    monta()
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(/\bAPI\b|endpoint|token|caché|base de datos|scraper|gold|cálculo|se calcula|reparto/i)
  })
})

describe('Portada · «Mi cesta»', () => {
  it('*** con lista, enseña el total de la cadena mas barata, el ahorro y la comparacion ***', async () => {
    monta()

    // *La cifra sale dos veces: el total grande y la fila de Lidl. Es la misma
    //  comparacion, no dos datos distintos.*
    expect((await screen.findAllByText(/4,08\s*€/)).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/−48,6\s*%/)).toBeInTheDocument()
    expect(screen.getByText(/en Lidl, la más barata de 2 cadenas/i)).toBeInTheDocument()
    // *La comparacion es de la API: las dos cadenas y sus dos cifras.*
    expect(screen.getByText('Lidl')).toBeInTheDocument()
    expect(screen.getByText('Carrefour')).toBeInTheDocument()
    expect(screen.getByText(/7,94\s*€/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Ver las 2 cadenas/i })).toHaveAttribute(
      'href', '/compra/listas/l1',
    )
  })

  it('*** sin sesion no enseña ninguna cifra y dice como empezar ***', async () => {
    vi.mocked(yo).mockResolvedValue({ usuario: null, preferencias: {} })
    vi.mocked(misListas).mockResolvedValue([])
    vi.mocked(useBajadas).mockReturnValue(consulta({ ...BAJADAS, solo_mios: false, resultados: [] }))

    monta()

    expect(await screen.findByText(/entra para guardar tu lista/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /^Entrar$/i })).toHaveAttribute('href', '/compra/listas')
    expect(screen.queryByText(/€/)).not.toBeInTheDocument()
    // *Y la cuenta del boton de arriba tambien lleva a la entrada, no a ajustes.*
    expect(screen.getByRole('link', { name: 'Tu cuenta' })).toHaveAttribute('href', '/compra/listas')
  })

  it('*** con sesion y sin lista de casa, lo dice y ofrece crearla ***', async () => {
    vi.mocked(misListas).mockResolvedValue([])
    monta()

    expect(await screen.findByText(/todavía no tienes una lista de casa/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /crear mi lista/i })).toHaveAttribute('href', '/compra/listas')
  })

  it('*** con otras listas pero sin la de casa, manda elegir y no crear ***', async () => {
    vi.mocked(misListas).mockResolvedValue([
      { id: 'l2', nombre: 'Ideas', es_de_casa: false },
    ])
    monta()

    expect(await screen.findByText(/no has marcado una lista de casa/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /abrir mis listas/i })).toHaveAttribute('href', '/compra/listas')
  })

  it('*** con la lista vacia, lo dice sin inventar un cero con forma de respuesta ***', async () => {
    vi.mocked(verLista).mockResolvedValue({ ...DETALLE, lineas: [] })
    vi.mocked(reparto).mockResolvedValue({ ...REPARTO, lineas: 0, una_tienda: [] })
    monta()

    expect(await screen.findByText(/tu lista está vacía/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /buscar productos/i })).toHaveAttribute('href', '/compra')
    expect(screen.queryByText(/0,00\s*€/)).not.toBeInTheDocument()
  })

  it('*** con lineas pero sin ningun precio confirmado, no corona un 0,00 ***', async () => {
    // *El caso que se colo: `una_tienda` traia las cadenas con 0 encontrados, `lineas` era 0 y
    // el filtro las daba por «completas». La tarjeta coronaba «0,00 €» como la mas barata.*
    vi.mocked(reparto).mockResolvedValue({
      ...REPARTO,
      lineas: 0,
      una_tienda: [
        { cadena: 'lidl', total_cent: 0, total_sin_ofertas_cent: 0, encontrados: 0, faltan: [] },
        { cadena: 'carrefour', total_cent: 0, total_sin_ofertas_cent: 0, encontrados: 0, faltan: [] },
      ],
    })
    monta()

    expect(await screen.findByText(/ninguna línea con precio confirmado/i)).toBeInTheDocument()
    expect(screen.queryByText(/0,00\s*€/)).not.toBeInTheDocument()
    expect(screen.queryByText(/la más barata de/i)).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /ver mi lista/i })).toHaveAttribute(
      'href', '/compra/listas/l1',
    )
  })

  it('*** si la comparacion falla, lo dice con palabras y deja seguir a la lista ***', async () => {
    vi.mocked(misListas).mockRejectedValue(new Error('sin red'))
    monta()

    expect(await screen.findByText(/no he podido mirar los precios de tu lista/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /volver a intentarlo/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /abrir mi lista/i })).toHaveAttribute('href', '/compra/listas')
  })

  it('*** mientras carga reserva el sitio, no una linea de texto ***', async () => {
    vi.mocked(misListas).mockReturnValue(new Promise(() => {}) as never)
    vi.mocked(useBajadas).mockReturnValue(pendiente())
    vi.mocked(useSecciones).mockReturnValue(pendiente())
    monta()

    expect((await screen.findAllByRole('status')).length).toBeGreaterThanOrEqual(1)
  })
})

describe('Portada · «Se han movido» y los pasillos', () => {
  it('*** enseña la bajada real con su fecha y su diferencia ***', async () => {
    monta()

    expect(await screen.findByRole('heading', { name: 'Se han movido' })).toBeInTheDocument()
    expect(screen.getByText('Garbanzos Luengo 1 kg')).toBeInTheDocument()
    expect(screen.getByText(/26 sept · baja/i)).toBeInTheDocument()
    expect(screen.getByText(/−0,40\s*€/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Garbanzos Luengo/i })).toHaveAttribute(
      'href', '/compra/comparar/7',
    )
  })

  it('*** sin bajadas no inventa «4 cambios»: dice que no hay ***', async () => {
    vi.mocked(useBajadas).mockReturnValue(consulta({ ...BAJADAS, resultados: [] }))
    monta()

    expect(await screen.findByText(/nada ha bajado en los últimos 7 días/i)).toBeInTheDocument()
    expect(screen.queryByText(/cambios en total/i)).not.toBeInTheDocument()
  })

  it('*** los pasillos salen del endpoint y llevan a /compra con su seccion ***', async () => {
    monta()

    const enlace = await screen.findByRole('link', { name: 'Frutas y verduras' })
    expect(enlace).toHaveAttribute('href', '/compra?seccion=frutas-verduras')
    expect(screen.getByRole('link', { name: 'Despensa' })).toBeInTheDocument()
    // *Seis, los del recorrido de la tienda; no una lista de diecinueve chips.*
    expect(screen.queryByRole('link', { name: 'Bebidas' })).not.toBeInTheDocument()
  })
})

describe('Portada · la fecha', () => {
  it('*** se escribe en espanol y en local, no en ISO ***', () => {
    expect(fechaDeHoy(new Date('2026-11-04T12:00:00'))).toBe('miércoles, 4 nov')
  })
})
