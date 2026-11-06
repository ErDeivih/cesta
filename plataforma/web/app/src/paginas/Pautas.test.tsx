/** *** PAUTAS, MONTADA: LO QUE ENSEÑA Y LO QUE NO PROMETE. ***
 *
 *  *Lo que se mide aquí no es el aspecto, sino lo que la pantalla **afirma**: que la estimación
 *  sale de los datos que se escriben, que sin datos no hay cifra, que el objetivo solo se guarda
 *  al pulsar y con la misma clave que lee Calorías, y que las fuentes se abren fuera con su
 *  `rel`. También que la pantalla no prescribe ni habla de cómo está hecha.*
 *
 *  *El caso conocido es el del encargo: hombre de 35 años, 75 kg y 175 cm con actividad
 *  moderada. La estimación es 2.594,3 kcal y el rango que se enseña, 2.330–2.850.*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, guardaPreferencia: vi.fn() }
})

import { guardaPreferencia } from '../api/cesta'
import { gastoEstimado, Pautas, rangoEstimado } from './Pautas'

function hoyIso(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

const HOY = hoyIso()

function monta() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/calorias/pautas']}>
        <Pautas />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function rellenaElCasoConocido(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.selectOptions(screen.getByLabelText('Sexo'), 'hombre')
  await usuario.type(screen.getByLabelText('Edad'), '35')
  await usuario.type(screen.getByLabelText('Peso (kg)'), '75')
  await usuario.type(screen.getByLabelText('Altura (cm)'), '175')
  await usuario.selectOptions(screen.getByLabelText('Actividad'), 'moderado')
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(guardaPreferencia).mockResolvedValue(undefined)
})

describe('Pautas · la estimación, con datos conocidos', () => {
  it('*** el cálculo y el rango del caso del encargo ***', () => {
    const centro = gastoEstimado({
      sexo: 'hombre', edad: 35, peso: 75, altura: 175, actividad: 'moderado',
    })
    expect(centro).toBeCloseTo(2594.3125, 4)
    expect(rangoEstimado(centro as number)).toEqual({ bajo: 2330, alto: 2850, centro: 2590 })
  })

  it('*** se enseña como rango, no como «tu gasto real» ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)

    expect(await screen.findByText('Entre 2.330 y 2.850 kcal')).toBeInTheDocument()
    expect(screen.getByText('Es una orientación, no una medida exacta.')).toBeInTheDocument()
    expect(screen.queryByText(/tu gasto real/i)).not.toBeInTheDocument()
  })

  it('*** sin datos no calcula y no ofrece guardar ***', () => {
    monta()

    expect(screen.getByLabelText('Edad')).toHaveValue('')
    expect(screen.getByLabelText('Peso (kg)')).toHaveValue('')
    expect(screen.getByLabelText('Altura (cm)')).toHaveValue('')
    expect(screen.queryByText(/Entre .* kcal/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Usar como objetivo' })).not.toBeInTheDocument()
    expect(screen.getByText(/Rellena los cinco datos/)).toBeInTheDocument()
    expect(screen.getByText(/personas adultas/i)).toBeInTheDocument()
  })

  it('*** con datos a medias tampoco calcula ***', async () => {
    const usuario = userEvent.setup()
    monta()

    await usuario.selectOptions(screen.getByLabelText('Sexo'), 'hombre')
    await usuario.type(screen.getByLabelText('Edad'), '35')
    await usuario.type(screen.getByLabelText('Peso (kg)'), '75')

    expect(screen.queryByText(/Entre .* kcal/)).not.toBeInTheDocument()
    expect(screen.queryByText('Gasto diario estimado')).not.toBeInTheDocument()
  })

  it('*** guarda el objetivo del día solo al pulsar, con la clave de Calorías ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)

    expect(screen.getByText('Si lo usas: 2.590 kcal para hoy.')).toBeInTheDocument()
    expect(guardaPreferencia).not.toHaveBeenCalled()
    await usuario.click(screen.getByRole('button', { name: 'Usar como objetivo' }))

    await waitFor(() => expect(guardaPreferencia).toHaveBeenCalledWith(
      `objetivo:${HOY}`, { kcal: 2590 },
    ))
    expect(await screen.findByText('Guardado: 2.590 kcal para hoy.')).toBeInTheDocument()
  })
})

describe('Pautas · las fuentes y lo que no dice', () => {
  it('*** las fuentes son externas y llevan rel ***', () => {
    monta()

    const enlaces = screen.getAllByRole('link')
      .filter((a) => a.getAttribute('target') === '_blank')
    expect(enlaces).toHaveLength(6)
    for (const enlace of enlaces) {
      expect(enlace).toHaveAttribute('rel', 'noopener noreferrer')
      expect(enlace.getAttribute('href')).toMatch(/^https:\/\//)
    }

    const hrefs = enlaces.map((a) => a.getAttribute('href'))
    expect(hrefs).toContain('https://www.who.int/news-room/fact-sheets/detail/healthy-diet')
    expect(hrefs).toContain('https://www.efsa.europa.eu/es/press/news/130110')
    expect(hrefs).toContain('https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2013.3005')
    expect(hrefs).toContain('https://www.fao.org/4/y5686e/y5686e00.htm')
    expect(hrefs).toContain(
      'https://cpage.mpr.gob.es/publicacion/recomendaciones-dieteticas-saludables-y-sostenibles-complementadas-con-recomendaciones-de-actividad-fisica-para-la-poblacion-espanola-2022-069220082-0001/',
    )
    expect(hrefs).toContain('https://europepmc.org/article/MED/2305711')
  })

  it('*** §8: no prescribe, no habla de la API ni de fórmulas ***', () => {
    monta()

    const texto = document.body.textContent ?? ''
    expect(texto).toMatch(/no es consejo médico/i)
    expect(texto).not.toMatch(
      /deber[ií]as|déficit|dieta\b|IMC|adelgazar|quema|objetivo automático|\bAPI\b|endpoint|fórmula|se calcula/i,
    )
  })

  it('*** todo lo que se pulsa y todos los campos llegan a 44 px ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)

    const objetivos = [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]
    for (const objetivo of objetivos) {
      expect(objetivo.className).toMatch(/min-h-\[44px\]/)
    }
    for (const campo of [...screen.getAllByRole('textbox'), ...screen.getAllByRole('combobox')]) {
      expect(campo.className).toMatch(/min-h-\[44px\]/)
    }
  })
})
