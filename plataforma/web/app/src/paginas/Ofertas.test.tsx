/** Las ofertas de hoy: lo que la pantalla enseña y lo que no puede decir.
 *
 *  *Lo que se comprueba no es el aspecto -- eso se mira en una captura -- sino lo que no da
 *  error al incumplirlo:* que cada oferta salga con su cadena, su precio, su tipo y **su
 *  condición**; que los chips filtren de verdad; que sin ofertas o con un fallo se diga en
 *  vez de inventar; que todo lo que se pulsa llegue a 44 px; y que la pantalla **no cuente
 *  cómo está hecha** (§8).
 *
 *  *Los datos son los de la API, recortados:* si el componente inventara un precio o un
 *  descuento, la prueba lo vería, porque el precio sale de `precio_cent` y la condición de
 *  `condicion`, no de una constante de la pantalla.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/cliente', async (importOriginal) => {
  const real = await importOriginal<typeof import('../api/cliente')>()
  return { ...real, pide: vi.fn() }
})

import { pide } from '../api/cliente'
import { Ofertas } from './Ofertas'
import type { Oferta, RespuestaOfertas } from './Ofertas'

const YOGUR: Oferta = {
  grupo_id: 1, cadena: 'lidl', nombre: 'Yogur griego de fresa', marca: 'LIDL',
  id_fuente: '111', imagen: null, precio_cent: 135, unidad: 'kg',
  promo_txt: 'Precio condicionado a Lidl Plus', tipo: 'club',
  exige_club: true, solo_online: false, condicion: 'Con Lidl Plus', hasta: '2026-11-18',
}

const ANCHOA: Oferta = {
  grupo_id: 2, cadena: 'alcampo', nombre: 'Anchoa y boquerón al vinagre', marca: 'ALCAMPO',
  id_fuente: '222', imagen: null, precio_cent: 406, unidad: 'ud',
  promo_txt: '2ª ud -50%. Solo Online (05/11/26_18/11/26)', tipo: 'segunda_unidad',
  exige_club: true, solo_online: true,
  condicion: 'Solo online · con Club Alcampo, en tu tarjeta', hasta: null,
}

const PIZZA: Oferta = {
  grupo_id: 3, cadena: 'dia', nombre: 'Pizza 4 quesos 400 g', marca: 'DIA',
  id_fuente: '333', imagen: null, precio_cent: 207, unidad: 'kg',
  promo_txt: '20% DTO.', tipo: 'descuento',
  exige_club: true, solo_online: false, condicion: 'Con tarjeta DIA', hasta: null,
}

const CAPSULAS: Oferta = {
  grupo_id: 4, cadena: 'aldi', nombre: 'Cápsulas de café con leche', marca: 'ALDI',
  id_fuente: '444', imagen: null, precio_cent: 247, unidad: 'ud',
  promo_txt: '2ª ud al -50%', tipo: 'segunda_unidad',
  exige_club: false, solo_online: false, condicion: 'Sin club', hasta: null,
}

const TURRONES: Oferta = {
  grupo_id: 5, cadena: 'dia', nombre: 'Turrones y chocolates', marca: 'DIA',
  id_fuente: '555', imagen: null, precio_cent: 150, unidad: 'kg',
  promo_txt: '3X2 EN SELECCIÓN TURRONES Y CHOCOLATES', tipo: '3x2',
  exige_club: true, solo_online: false, condicion: 'Con tarjeta DIA', hasta: null,
}

const TODAS = [YOGUR, ANCHOA, PIZZA, CAPSULAS, TURRONES]

/** La respuesta de la API, filtrada como lo haría el servidor. */
function respuesta(filtros: Record<string, string | number | boolean> = {}): RespuestaOfertas {
  let resultados = [...TODAS]
  if (filtros.tipos) {
    const tipos = String(filtros.tipos).split(',')
    resultados = resultados.filter((o) => tipos.includes(o.tipo))
  }
  if (filtros.club) resultados = resultados.filter((o) => o.exige_club)
  if (filtros.solo_online) resultados = resultados.filter((o) => o.solo_online)
  return { fecha_datos: '2026-11-06', resultados }
}

function monta() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/compra/ofertas']}>
        <Ofertas />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(pide).mockReset()
  vi.mocked(pide).mockImplementation(async (_ruta, parametros) =>
    respuesta((parametros ?? {}) as Record<string, string | number | boolean>),
  )
})

describe('Ofertas · lo que enseña', () => {
  it('*** cada oferta sale con su cadena, su precio, su tipo y su condición ***', async () => {
    monta()

    expect(await screen.findByRole('heading', { name: 'Lo que hay esta semana' })).toBeInTheDocument()
    expect(await screen.findByText('Yogur griego de fresa')).toBeInTheDocument()
    expect(screen.getByText('Lidl')).toBeInTheDocument()
    expect(screen.getByText(/1,35\s*€/)).toBeInTheDocument()
    // *La condición es la del club y en lenguaje de usuario, no «promo_club=true».*
    expect(screen.getByText('Con Lidl Plus')).toBeInTheDocument()
    // *Y la de DIA y la de una oferta sin club.*
    expect(screen.getAllByText('Con tarjeta DIA').length).toBe(2)
    expect(screen.getByText('Sin club')).toBeInTheDocument()
    // *La online se dice como lo que es, y en la tarjeta de la oferta (el chip
    //  «Solo online» también se llama así: se busca dentro de la tarjeta). Y como
    //  además pide tarjeta, lo dice: «Solo online · con Club Alcampo…».*
    const anchoa = screen.getByText('Anchoa y boquerón al vinagre').closest('article')
    expect(within(anchoa as HTMLElement).getByText(/solo online/i)).toBeInTheDocument()
    expect(within(anchoa as HTMLElement).getByText(/con Club Alcampo/i)).toBeInTheDocument()
  })

  it('*** el nombre lleva a la ficha del producto ***', async () => {
    monta()
    const enlace = await screen.findByRole('link', { name: 'Yogur griego de fresa' })
    expect(enlace).toHaveAttribute('href', '/compra/productos/lidl/111')
  })

  it('*** enseña la fecha de fin cuando la oferta la trae ***', async () => {
    monta()
    // *La fecha sale de `hasta`, y solo cuando el dato existe. No se inventa.*
    expect(await screen.findByText(/hasta el 18 nov/i)).toBeInTheDocument()
  })

  it('*** sin sesión se ven: las ofertas son públicas ***', async () => {
    monta()
    await screen.findByText('Yogur griego de fresa')
    expect(screen.queryByText(/entra para ver/i)).not.toBeInTheDocument()
    // *La única petición es la de ofertas: la pantalla no pregunta por la cuenta.*
    expect(vi.mocked(pide).mock.calls.map(([ruta]) => ruta)).toEqual(['/ofertas'])
  })
})

describe('Ofertas · los chips', () => {
  it('*** «2ª unidad» pide los dos mecanismos de varias unidades ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('Yogur griego de fresa')

    await usuario.click(screen.getByRole('button', { name: '2ª unidad' }))

    expect(await screen.findByText('Cápsulas de café con leche')).toBeInTheDocument()
    expect(screen.getByText('Anchoa y boquerón al vinagre')).toBeInTheDocument()
    // *Un 3x2 también es «cuántas unidades»: el chip lo pide junto, y la tarjeta lo llama por su nombre.*
    expect(screen.getByText('Turrones y chocolates')).toBeInTheDocument()
    expect(screen.queryByText('Yogur griego de fresa')).not.toBeInTheDocument()
    expect(screen.queryByText('Pizza 4 quesos 400 g')).not.toBeInTheDocument()

    const llamada = vi.mocked(pide).mock.calls.at(-1)
    expect(llamada?.[0]).toBe('/ofertas')
    expect(llamada?.[1]).toMatchObject({ tipos: 'segunda_unidad,3x2' })
  })

  it('*** «Club» filtra por condición y «Solo online» por dónde se compra ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('Yogur griego de fresa')

    await usuario.click(screen.getByRole('button', { name: 'Club' }))
    expect(await screen.findByText('Pizza 4 quesos 400 g')).toBeInTheDocument()
    expect(vi.mocked(pide).mock.calls.at(-1)?.[1]).toMatchObject({ club: 'true' })

    await usuario.click(screen.getByRole('button', { name: 'Solo online' }))
    expect(await screen.findByText('Anchoa y boquerón al vinagre')).toBeInTheDocument()
    expect(vi.mocked(pide).mock.calls.at(-1)?.[1]).toMatchObject({ solo_online: 'true' })
    // *Y la que no es online desaparece.*
    expect(screen.queryByText('Pizza 4 quesos 400 g')).not.toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Todas' }))
    expect(await screen.findByText('Yogur griego de fresa')).toBeInTheDocument()
  })
})

describe('Ofertas · los estados raros', () => {
  it('*** sin ofertas lo dice; no inventa una lista vacía con precio ***', async () => {
    vi.mocked(pide).mockResolvedValue({ fecha_datos: '2026-11-06', resultados: [] })
    monta()
    expect(await screen.findByText(/hoy no hay ofertas anunciadas/i)).toBeInTheDocument()
    expect(screen.queryByText(/€/)).not.toBeInTheDocument()
  })

  it('*** si la petición falla, lo dice con un botón para volver a intentarlo ***', async () => {
    const usuario = userEvent.setup()
    vi.mocked(pide).mockRejectedValueOnce(new Error('sin red'))
    monta()

    expect(await screen.findByText('sin red')).toBeInTheDocument()
    const reintentar = screen.getByRole('button', { name: /volver a intentarlo/i })
    await usuario.click(reintentar)
    expect(await screen.findByText('Yogur griego de fresa')).toBeInTheDocument()
  })

  it('*** mientras carga reserva el sitio, no una línea de texto ***', async () => {
    vi.mocked(pide).mockReturnValue(new Promise(() => {}) as never)
    monta()
    expect((await screen.findAllByRole('status')).length).toBeGreaterThanOrEqual(1)
  })
})

describe('Ofertas · las reglas de la casa', () => {
  it('*** todo lo que se pulsa llega a los 44 px ***', async () => {
    monta()
    await screen.findByText('Yogur griego de fresa')
    for (const objetivo of [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]) {
      expect(objetivo.className).toMatch(/min-h-\[44px\]/)
    }
  })

  it('*** habla de las ofertas, no de cómo está hecha la app (§8) ***', async () => {
    monta()
    await screen.findByText('Yogur griego de fresa')
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(
      /\bAPI\b|endpoint|caché|gold|base de datos|se calcula|cálculo|no se resta|scraper/i,
    )
  })

  it('*** el chip de tipo no repite la condición en la tarjeta ***', async () => {
    monta()
    await screen.findByText('Yogur griego de fresa')
    const tarjeta = screen.getByText('Yogur griego de fresa').closest('article')
    expect(tarjeta).not.toBeNull()
    // *En la tarjeta del club, el chip dice «Precio club» y la condición «Con Lidl Plus»: una vez cada cosa.*
    expect(within(tarjeta as HTMLElement).getByText('Precio club')).toBeInTheDocument()
    expect(within(tarjeta as HTMLElement).getByText('Con Lidl Plus')).toBeInTheDocument()
  })
})
