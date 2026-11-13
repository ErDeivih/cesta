/** *** EL BUSCADOR DE PRODUCTO DE LA LISTA. *** *
 *
 *  *Apuntar no puede obligar a salir de la lista: se escribe, se ve la sugerencia con su €/kg y
 *  se apunta sin soltar el campo.* *Lo que se mide aqui es el contrato del combobox: nombre
 *  accesible, red solo cuando hay que preguntar, teclado, foco que se queda, y los tres estados
 *  que no son «con resultados» (error, sin conexion y solo lectura).*
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'

import type { ResultadoBusqueda } from '../../tipos'
import { Typeahead } from './Typeahead'

/** Un resultado del buscador con la forma de `GET /api/buscar` (lo que pinta la sugerencia). */
function resultado(extra: Partial<ResultadoBusqueda> = {}): ResultadoBusqueda {
  return {
    grupo_id: 77,
    nombre: 'Leche entera 1 l',
    marca: 'Puleva',
    cadena_mas_barata: 'dia',
    precio_cent: 99,
    precio_unidad_cent: 66,
    precio_unidad_max_cent: 66,
    unidad: 'l',
    cadenas: 3,
    productos: 4,
    nutriscore: null,
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
    ahorro_pct: 0,
    ...extra,
  }
}

/** Sustituye `fetch` por la respuesta del buscador y devuelve las URLs pedidas. */
function conRed(resultados: ResultadoBusqueda[] = [resultado()]) {
  const pedidas: string[] = []
  const falso = vi.fn(async (url: string | URL) => {
    pedidas.push(String(url))
    return {
      ok: true,
      status: 200,
      json: async () => ({ fecha_datos: '2026-11-13', resultados }),
    } as unknown as Response
  })
  vi.stubGlobal('fetch', falso)
  return pedidas
}

function pinta(
  alElegir: Mock<(producto: ResultadoBusqueda) => Promise<void>> = vi.fn(async (_producto: ResultadoBusqueda) => {}),
  puedeEscribir = true,
) {
  return render(
    <Typeahead listaId="L1" alElegir={alElegir} puedeEscribir={puedeEscribir} />,
  )
}

beforeEach(() => {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, value: true })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Typeahead: el campo y la sugerencia', () => {
  it('es un combobox con nombre y pregunta a la API solo cuando se escribe', async () => {
    const pedidas = conRed()
    pinta()

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    expect(pedidas).toHaveLength(0)

    await userEvent.type(campo, 'leche')

    const opcion = await screen.findByRole('option', { name: /Leche entera/ })
    // *El €/kg en la sugerencia: es la decision de compra, no un adorno.*
    expect(opcion).toHaveTextContent('0,66')
    expect(pedidas.some((u) => /\/api\/buscar/.test(u) && /q=leche/.test(u))).toBe(true)
  })

  it('con teclado: flecha abajo y Enter eligen la sugerencia', async () => {
    conRed()
    const alElegir = vi.fn(async (_producto: ResultadoBusqueda) => {})
    pinta(alElegir)

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'leche')
    await screen.findByRole('option', { name: /Leche entera/ })

    await userEvent.keyboard('{ArrowDown}{Enter}')

    await waitFor(() => expect(alElegir).toHaveBeenCalledTimes(1))
    expect(alElegir.mock.calls[0][0]).toMatchObject({ grupo_id: 77, nombre: 'Leche entera 1 l' })
    // *Apuntar es seguir apuntando: el foco no se va del campo.*
    expect(campo).toHaveFocus()
  })

  it('Escape cierra la lista sin borrar lo escrito', async () => {
    conRed()
    pinta()

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'lech')
    await screen.findByRole('option', { name: /Leche entera/ })

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('option')).not.toBeInTheDocument()
    expect(campo).toHaveValue('lech')
  })
})

describe('Typeahead: los estados que no son «con resultados»', () => {
  it('si la busqueda falla lo dice y ofrece reintentar', async () => {
    let intentos = 0
    vi.stubGlobal('fetch', vi.fn(async () => {
      intentos += 1
      return { ok: false, status: 500, json: async () => ({}) } as unknown as Response
    }))
    pinta()

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'leche')

    expect(await screen.findByText(/No he podido buscar/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    await waitFor(() => expect(intentos).toBeGreaterThan(1))
  })

  it('sin conexión lo dice y no lanza peticiones', async () => {
    const pedidas = conRed()
    Object.defineProperty(window.navigator, 'onLine', { configurable: true, value: false })
    window.dispatchEvent(new Event('offline'))
    pinta()

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'leche')

    expect(await screen.findByText(/Sin conexión/)).toBeInTheDocument()
    expect(pedidas).toHaveLength(0)
  })

  it('en una lista de solo lectura no ofrece apuntar', async () => {
    const pedidas = conRed()
    pinta(vi.fn(async () => {}), false)

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    expect(campo).toHaveAttribute('aria-disabled', 'true')
    await userEvent.type(campo, 'leche')
    expect(pedidas).toHaveLength(0)
  })
})
