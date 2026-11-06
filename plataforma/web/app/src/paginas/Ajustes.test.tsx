/** **Tu perfil, montado.** *Lo que se prueba es lo que la pantalla promete: que la cuenta
 *  sale de la sesión, que lo que se toca se guarda donde ya se guardaba, y que lo que no
 *  tiene dónde guardarse no se pinta.*
 *
 *  *La versión anterior de este fichero medía la tarjeta de «Frescura y cobertura» de
 *  `Ajustes`. Esa tarjeta se ha ido a propósito: la cobertura del catálogo es diagnóstico
 *  (§8) y su sitio es `/panel`, no el perfil. El 6/11/2026 la prueba vieja se puso roja
 *  contra la pantalla nueva —era la señal de que el cambio era de verdad— y se reescribió
 *  para medir el perfil aprobado.*
 *
 *  *Lo que **no** se prueba aquí: que la API guarde. `guardarPreferencia` es la misma
 *  llamada que ya usa el resto de la aplicación (`PUT /api/preferencias`); lo que se mide
 *  es que la pantalla la use con la clave y el valor que toca.*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import type { Sesion } from '../tipos'

vi.mock('../api/cesta', () => ({
  yo: vi.fn(),
  salir: vi.fn(),
  borrarme: vi.fn(),
}))

vi.mock('../api/ajustes', async (importOriginal) => {
  const real = await importOriginal<typeof import('../api/ajustes')>()
  return { ...real, guardarPreferencia: vi.fn() }
})

import { borrarme, salir, yo } from '../api/cesta'
import { guardarPreferencia } from '../api/ajustes'
import { Ajustes } from './Ajustes'

const CON_SESION: Sesion = {
  usuario: { id: 'u1', usuario: 'david', nombre: 'David' },
  preferencias: {},
}

const SIN_SESION: Sesion = { usuario: null, preferencias: {} }

/** La fecha local, igual que la calcula la pantalla: el objetivo es de hoy. */
function hoy(): string {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

function monta() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/ajustes']}>
        <Ajustes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(yo).mockReset()
  vi.mocked(salir).mockReset()
  vi.mocked(borrarme).mockReset()
  vi.mocked(guardarPreferencia).mockReset()

  vi.mocked(yo).mockResolvedValue(CON_SESION)
  vi.mocked(salir).mockResolvedValue(undefined)
  vi.mocked(borrarme).mockResolvedValue({ listas_borradas: 0, lineas_conservadas: 0 })
  vi.mocked(guardarPreferencia).mockResolvedValue(undefined)
})

describe('Perfil · la cuenta', () => {
  it('*** el nombre sale de la sesión; el correo no se inventa ***', async () => {
    monta()

    expect(await screen.findByText('David')).toBeInTheDocument()
    expect(screen.getByText('@david')).toBeInTheDocument()
    // *La API no manda correo, así que no hay línea de correo: ni una inventada ni enmascarada.*
    expect(screen.queryByText(/@[\w.-]+\.[a-z]{2,}/i)).not.toBeInTheDocument()

    // *Un solo nombre de sección para cada cosa, en el orden del artboard.*
    expect(screen.getByRole('heading', { name: 'Preferencias' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Avisos' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })

  it('*** sin nombre de pila se enseña el usuario, y no un nombre inventado ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      usuario: { id: 'u2', usuario: 'marta', nombre: null },
      preferencias: {},
    })
    monta()

    expect(await screen.findByText('marta')).toBeInTheDocument()
    expect(screen.getByText('@marta')).toBeInTheDocument()
    expect(screen.queryByText('Marta')).not.toBeInTheDocument()
  })

  it('*** sin sesión, la puerta compartida dice por dónde se entra ***', async () => {
    vi.mocked(yo).mockResolvedValue(SIN_SESION)
    monta()

    expect(await screen.findByText('Entra para ver esto')).toBeInTheDocument()
    const enlace = screen.getByRole('link', { name: 'la cesta' })
    expect(enlace).toHaveAttribute('href', '/cesta')
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('*** la cobertura del catálogo no se enseña: es diagnóstico ***', async () => {
    monta()
    await screen.findByText('David')

    expect(screen.queryByText(/frescura y cobertura/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/catálogo diario/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/cobertura/i)).not.toBeInTheDocument()
  })

  it('*** mientras llega la sesión hay un hueco con la forma del perfil, no una línea ***', () => {
    vi.mocked(yo).mockReturnValue(new Promise(() => {}))
    monta()

    expect(screen.getByText('Cargando tu perfil…')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('*** con la sesión caída hay un error y un reintento de verdad ***', async () => {
    vi.mocked(yo).mockRejectedValueOnce(new TypeError('sin conexión'))
    monta()

    expect(await screen.findByText('Sin cobertura')).toBeInTheDocument()
    vi.mocked(yo).mockResolvedValueOnce(CON_SESION)
    await userEvent.setup().click(screen.getByRole('button', { name: 'Volver a intentarlo' }))

    expect(await screen.findByText('David')).toBeInTheDocument()
  })
})

describe('Perfil · las preferencias', () => {
  it('*** la cadena habitual se guarda en `cadenas_cerca`, la preferencia que ya existe ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      ...CON_SESION,
      preferencias: { cadenas_cerca: ['mercadona'] },
    })
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('David')

    const resumen = screen.getByText('Cadena habitual').closest('summary') as HTMLElement
    expect(within(resumen).getByText('Mercadona')).toBeInTheDocument()

    await usuario.click(screen.getByText('Cadena habitual'))
    const casilla = screen.getByRole('checkbox', { name: 'Mercadona' })
    expect(casilla).toBeChecked()

    await usuario.click(casilla)
    await waitFor(() => {
      expect(guardarPreferencia).toHaveBeenCalledWith('cadenas_cerca', [])
    })
    expect(within(resumen).getByText('Todas')).toBeInTheDocument()
  })

  it('*** el objetivo de hoy se enseña y lleva a Calorías; sin objetivo no hay 2.200 ***', async () => {
    monta()
    await screen.findByText('David')

    const fila = screen.getByRole('link', { name: /Objetivo de calorías/ })
    expect(fila).toHaveAttribute('href', '/calorias')
    expect(within(fila).getByText('Sin objetivo')).toBeInTheDocument()
    expect(screen.queryByText(/2\.200/)).not.toBeInTheDocument()
  })

  it('*** con objetivo guardado enseña el de hoy, que es el que lee la gráfica ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      ...CON_SESION,
      preferencias: { [`objetivo:${hoy()}`]: { kcal: 2000 } },
    })
    monta()
    await screen.findByText('David')

    const fila = screen.getByRole('link', { name: /Objetivo de calorías/ })
    expect(within(fila).getByText('2000 kcal')).toBeInTheDocument()
  })
})

describe('Perfil · los avisos', () => {
  it('*** las casillas tienen los valores del artboard y guardan lo que se toca ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('David')

    const bajadas = screen.getByRole('checkbox', { name: 'Bajadas de tus favoritos' })
    const ofertas = screen.getByRole('checkbox', { name: 'Ofertas de tu club' })
    const compartida = screen.getByRole('checkbox', { name: 'Lista compartida' })
    expect(bajadas).toBeChecked()
    expect(ofertas).toBeChecked()
    expect(compartida).not.toBeChecked()

    await usuario.click(ofertas)
    await waitFor(() => {
      expect(guardarPreferencia).toHaveBeenCalledWith('avisos_ofertas_club', false)
    })
    expect(ofertas).not.toBeChecked()
  })

  it('*** lo guardado manda sobre el valor de partida ***', async () => {
    vi.mocked(yo).mockResolvedValue({
      ...CON_SESION,
      preferencias: { avisos_ofertas_club: false },
    })
    monta()
    await screen.findByText('David')

    expect(screen.getByRole('checkbox', { name: 'Ofertas de tu club' })).not.toBeChecked()
  })
})

describe('Perfil · las acciones de la cuenta', () => {
  it('*** cerrar sesión llama a salir y deja la puerta de entrada ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('David')

    vi.mocked(yo).mockResolvedValue(SIN_SESION)
    await usuario.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    await waitFor(() => expect(salir).toHaveBeenCalledTimes(1))
    expect(await screen.findByText('Entra para ver esto')).toBeInTheDocument()
  })

  it('*** darse de baja sigue pidiendo escribir el propio usuario ***', async () => {
    const usuario = userEvent.setup()
    monta()
    await screen.findByText('David')

    await usuario.click(screen.getByText('Dar de baja la cuenta'))
    await usuario.click(screen.getByRole('button', { name: 'Quiero darme de baja' }))

    const campo = screen.getByLabelText('Escribe david para confirmarlo')
    const boton = screen.getByRole('button', { name: 'Darme de baja' })
    expect(boton).toBeDisabled()

    await usuario.type(campo, 'david')
    expect(boton).toBeEnabled()
    await usuario.click(boton)
    await waitFor(() => expect(borrarme).toHaveBeenCalledTimes(1))
  })
})
