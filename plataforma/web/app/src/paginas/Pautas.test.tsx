/** *** PAUTAS, MONTADA: LO QUE ENSEÑA Y LO QUE NO PROMETE. ***
 *
 *  *Lo que se mide aquí no es el aspecto, sino lo que la pantalla **afirma**: que la estimación
 *  sale de los datos que se escriben, que sin datos no hay cifra, que **no hay objetivo hasta que
 *  se elige**, que el objetivo solo se guarda al pulsar y con la misma clave que lee Calorías, que
 *  cada pauta lleva su cifra con su fuente y su fecha, y que la pantalla no prescribe ni habla de
 *  cómo está hecha.*
 *
 *  *El caso conocido es el del encargo: hombre de 35 años, 75 kg y 175 cm con actividad
 *  moderada. El gasto estimado es 2.594,3 kcal; el rango que se enseña, 2.330–2.850. Al elegir
 *  «Perder», el objetivo es 2.190 kcal (1.970–2.410).*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, guardaPreferencia: vi.fn() }
})

import { guardaPreferencia } from '../api/cesta'
import { Pautas } from './Pautas'

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

function elige(usuario: ReturnType<typeof userEvent.setup>, nombre: string) {
  return usuario.click(screen.getByRole('radio', { name: nombre }))
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(guardaPreferencia).mockResolvedValue(undefined)
})

describe('Pautas · la estimación, con datos conocidos', () => {
  it('*** sin objetivo elegido se enseña el gasto estimado y su rango ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)

    expect(await screen.findByText('Entre 2.330 y 2.850 kcal')).toBeInTheDocument()
    expect(screen.getByText('Gasto diario estimado')).toBeInTheDocument()
    expect(screen.getByText('Es una estimación, no una medida exacta.')).toBeInTheDocument()
    expect(screen.queryByText(/tu gasto real/i)).not.toBeInTheDocument()
  })

  it('*** «Mantener» no ajusta: el objetivo es el gasto, con su rango ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Mantener')

    expect(await screen.findByText('2.590 kcal al día')).toBeInTheDocument()
    expect(screen.getByText('Entre 2.330 y 2.850 kcal al día.')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Partimos de tu gasto estimado (2.594 kcal al día). Para mantener, no ajustamos la cifra.',
      ),
    ).toBeInTheDocument()
    // El bloque del gasto suelto ya no está: lo explica el «por qué».
    expect(screen.queryByText('Gasto diario estimado')).not.toBeInTheDocument()
  })

  it('*** «Perder» ajusta 400 kcal y lo dice sin jerga ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    expect(await screen.findByText('2.190 kcal al día')).toBeInTheDocument()
    expect(screen.getByText('Entre 1.970 y 2.410 kcal al día.')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Partimos de tu gasto estimado (2.594 kcal al día) y, para perder, ajustamos −400 kcal al día.',
      ),
    ).toBeInTheDocument()
  })

  it('*** «Ganar» sube 400 kcal ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Ganar')

    expect(await screen.findByText('2.990 kcal al día')).toBeInTheDocument()
    expect(screen.getByText('Entre 2.690 y 3.290 kcal al día.')).toBeInTheDocument()
  })

  it('*** los macros, en gramos y en % con su horquilla ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    expect(await screen.findByText('Proteína')).toBeInTheDocument()
    expect(screen.getByText('68 g')).toBeInTheDocument()
    expect(screen.getByText('Entre 55 y 82 g · 10–15 % de la energía')).toBeInTheDocument()
    expect(screen.getByText('55 g')).toBeInTheDocument()
    expect(screen.getByText('Entre 37 y 73 g · 15–30 % de la energía')).toBeInTheDocument()
    expect(screen.getByText('287 g')).toBeInTheDocument()
    expect(screen.getByText('Entre 246 y 329 g · 45–60 % de la energía')).toBeInTheDocument()
  })

  it('*** sin datos no calcula, no ofrece objetivos y no ofrece guardar ***', () => {
    monta()

    expect(screen.getByLabelText('Edad')).toHaveValue('')
    expect(screen.getByLabelText('Peso (kg)')).toHaveValue('')
    expect(screen.getByLabelText('Altura (cm)')).toHaveValue('')
    expect(screen.queryByText(/Entre .* kcal/)).not.toBeInTheDocument()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Usar como objetivo' })).not.toBeInTheDocument()
    expect(screen.getByText(/Rellena los cinco datos/)).toBeInTheDocument()
    expect(screen.getByText(/a partir de 14 años/i)).toBeInTheDocument()
  })

  it('*** con datos a medias tampoco calcula ***', async () => {
    const usuario = userEvent.setup()
    monta()

    await usuario.selectOptions(screen.getByLabelText('Sexo'), 'hombre')
    await usuario.type(screen.getByLabelText('Edad'), '35')
    await usuario.type(screen.getByLabelText('Peso (kg)'), '75')

    expect(screen.queryByText(/Entre .* kcal/)).not.toBeInTheDocument()
    expect(screen.queryByText('Gasto diario estimado')).not.toBeInTheDocument()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })

  it('*** fuera de los límites avisa y no enseña ninguna cifra ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await usuario.clear(screen.getByLabelText('Edad'))
    await usuario.type(screen.getByLabelText('Edad'), '5')

    expect(await screen.findByText(/Revisa los datos/)).toBeInTheDocument()
    expect(screen.queryByText(/Entre .* kcal/)).not.toBeInTheDocument()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })

  it('*** no hay objetivo automático: sin elegir no se ofrece guardar ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)

    expect(await screen.findByText('Entre 2.330 y 2.850 kcal')).toBeInTheDocument()
    expect(screen.getByText(/Elige una opción/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Usar como objetivo' })).not.toBeInTheDocument()
    expect(guardaPreferencia).not.toHaveBeenCalled()
  })

  it('*** guarda el objetivo del día solo al pulsar, con la clave de Calorías ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    expect(await screen.findByText('Si lo usas: 2.190 kcal para hoy.')).toBeInTheDocument()
    expect(guardaPreferencia).not.toHaveBeenCalled()
    await usuario.click(screen.getByRole('button', { name: 'Usar como objetivo' }))

    await waitFor(() => expect(guardaPreferencia).toHaveBeenCalledWith(
      `objetivo:${HOY}`,
      {
        kcal: 2190,
        motivo: 'perder',
        ajuste: -400,
        macros: { proteina: 68, grasas: 55, hidratos: 287 },
      },
    ))
    expect(await screen.findByText('Guardado: 2.190 kcal para hoy.')).toBeInTheDocument()
  })

  it('*** cambiar de objetivo cambia lo que se guarda ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Ganar')
    await elige(usuario, 'Mantener')
    await usuario.click(await screen.findByRole('button', { name: 'Usar como objetivo' }))

    await waitFor(() => expect(guardaPreferencia).toHaveBeenCalledWith(
      `objetivo:${HOY}`,
      expect.objectContaining({ kcal: 2590, motivo: 'mantener', ajuste: 0 }),
    ))
  })
})

describe('Pautas · las cifras y sus fuentes', () => {
  it('*** las seis pautas, con su cifra y su fuente enlazada con fecha ***', () => {
    monta()

    expect(screen.getByText('25 g al día o más')).toBeInTheDocument()
    expect(screen.getByText('Menos del 10 % de la energía; mejor, menos del 5 %')).toBeInTheDocument()
    expect(screen.getByText('Menos de 5 g al día (2.000 mg de sodio)')).toBeInTheDocument()
    expect(
      screen.getByText('2,0 L al día en mujeres y 2,5 L en hombres'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('400 g al día o más, a partir de los 10 años'),
    ).toBeInTheDocument()
    expect(screen.getByText('Ningún nivel de consumo es sin riesgo')).toBeInTheDocument()

    // La fecha se lee al lado de la fuente, no escondida en un `title`.
    expect(screen.getAllByText('WHO · 26/01/2026').length).toBeGreaterThan(0)
    expect(screen.getByText('WHO · 11/05/2026')).toBeInTheDocument()
    expect(screen.getByText('WHO · 28/06/2024')).toBeInTheDocument()
    expect(screen.getAllByText('EFSA · 26/03/2010').length).toBeGreaterThan(0)
    expect(screen.getByText('AESAN · 2022')).toBeInTheDocument()
  })

  it('*** todos los enlaces son externos, con rel y https ***', async () => {
    const usuario = userEvent.setup()
    monta()
    // Con la estimación hecha están **las ocho** fuentes: las seis pautas, el contexto español y
    // las tres de la cuenta (gasto, actividad y ritmo).
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    const enlaces = screen.getAllByRole('link')
      .filter((a) => a.getAttribute('target') === '_blank')
    expect(enlaces.length).toBeGreaterThanOrEqual(8)
    for (const enlace of enlaces) {
      expect(enlace).toHaveAttribute('rel', 'noopener noreferrer')
      expect(enlace.getAttribute('href')).toMatch(/^https:\/\//)
    }
    const hrefs = enlaces.map((a) => a.getAttribute('href'))
    expect(hrefs).toContain('https://www.who.int/news-room/fact-sheets/detail/healthy-diet')
    expect(hrefs).toContain('https://www.efsa.europa.eu/en/press/news/nda100326')
    expect(hrefs).toContain('https://www.who.int/news-room/fact-sheets/detail/sodium-reduction')
    expect(hrefs).toContain('https://www.who.int/news-room/fact-sheets/detail/alcohol')
    expect(hrefs).toContain('https://www.aesan.gob.es/nutricion/recomendaciones-dieteticas')
    expect(hrefs).toContain('https://www.fao.org/4/y5686e/y5686e00.htm')
    expect(hrefs).toContain('https://europepmc.org/article/MED/2305711')
    expect(hrefs).toContain('https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html')
  })

  it('*** el «por qué» del objetivo enseña de dónde sale, con enlace ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    const resultado = await screen.findByRole('status', { name: 'Tu objetivo' })
    // Lo que se anuncia es la cifra con su por qué; las fuentes están en la misma ficha.
    expect(within(resultado).getByText(/Partimos de tu gasto estimado/)).toBeInTheDocument()
    expect(
      screen.getByText('Gasto en reposo · 1990').closest('a'),
    ).toHaveAttribute('href', 'https://europepmc.org/article/MED/2305711')
    expect(
      screen.getByText('FAO/WHO/UNU · 2004').closest('a'),
    ).toHaveAttribute('href', 'https://www.fao.org/4/y5686e/y5686e00.htm')
    expect(
      screen.getByText('CDC · 17/01/2025').closest('a'),
    ).toHaveAttribute('href', 'https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html')
  })

  it('*** §8: no prescribe, no habla de la API ni de fórmulas ***', () => {
    const { unmount } = monta()

    const texto = document.body.textContent ?? ''
    expect(texto).toMatch(/no es consejo médico/i)
    expect(texto).not.toMatch(
      /deber[ií]as|déficit|dieta\b|IMC|adelgazar|quema|objetivo automático|\bAPI\b|endpoint|fórmula|se calcula|Mifflin|\bPAL\b|\bTDEE\b/i,
    )
    unmount()
  })

  it('*** todo lo que se pulsa, se escribe o se elige llega a 44 px ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await rellenaElCasoConocido(usuario)
    await elige(usuario, 'Perder')

    const objetivos = [...screen.getAllByRole('link'), ...screen.getAllByRole('button')]
    for (const objetivo of objetivos) {
      expect(objetivo.className).toMatch(/min-h-\[44px\]/)
    }
    for (const campo of [...screen.getAllByRole('textbox'), ...screen.getAllByRole('combobox')]) {
      expect(campo.className).toMatch(/min-h-\[44px\]/)
    }
    for (const radio of screen.getAllByRole('radio')) {
      const etiqueta = radio.closest('label')
      expect(etiqueta?.className).toMatch(/min-h-\[44px\]/)
    }
  })

  it('*** si «Perder» cae por debajo del suelo, no se da la cifra ni se guarda ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await usuario.selectOptions(screen.getByLabelText('Sexo'), 'mujer')
    await usuario.type(screen.getByLabelText('Edad'), '70')
    await usuario.type(screen.getByLabelText('Peso (kg)'), '50')
    await usuario.type(screen.getByLabelText('Altura (cm)'), '155')
    await usuario.selectOptions(screen.getByLabelText('Actividad'), 'poco')
    await elige(usuario, 'Perder')

    expect(await screen.findByText(/por debajo de 1\.200 kcal al día/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Usar como objetivo/i })).not.toBeInTheDocument()
    expect(guardaPreferencia).not.toHaveBeenCalled()
  })
})
