/** *** RELLENAR DE UNA VEZ: SE ENSEÑA, SE CONFIRMA Y SE CUENTA. *** *
 *
 *  *`WALL.md`, casilla «aprender de las listas»: «rellenar sola» como **sugerencia revisable**,
 *  «nunca añadiendo a escondidas» (`INVESTIGACION-APP.md` §9.2 y §9.3).* *Estas pruebas miden
 *  justo eso, y cada una porque se puede romper sin que nada avise:*
 *
 *   - **la previa existe y no guarda nada** *-- el fallo que convierte una sugerencia en un
 *     cambio hecho sin permiso;*
 *   - **dice cuántos son y cuáles**, *no una cifra que haya que creerse;*
 *   - **añade uno por producto, en el orden que ya trae la API** *-- `useAnadeALaCesta` no tiene
 *     lote y aquí no se inventa;*
 *   - **lo que ya está no se ofrece** *-- ni lo añadido en esta pantalla (`puestos`) ni lo que ya
 *     trae la lista (`enLaLista`): una lista con el mismo producto dos veces no es un relleno;*
 *   - **si falla a medias lo dice con las cuentas** *-- «se han añadido 1 de 2» es lo único que
 *     permite reintentar sin repetir;*
 *   - **sin historial (o solo con la compra básica fuera de una lista) no se ofrece** *-- el
 *     estado honesto que ya tenía, que no se toca.*
 *
 *  *Los datos son de mentira; su forma es la de `GET /api/habituales` (`api/habituales.py`).*
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'

/* ------------------------------------------------------------- los dobles --- */

const estado = vi.hoisted(() => ({
  habituales: { isPending: false, data: null as unknown },
  anade: {
    isPending: false,
    isError: false,
    error: null as unknown,
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
  },
}))

vi.mock('../api/consultas', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  useHabituales: () => estado.habituales,
  useAnadeALaCesta: () => estado.anade,
}))

// *La tarjeta de la primera vez pide cuatro búsquedas de verdad: aquí no hay red y no es lo
// que se mide.*
vi.mock('../api/cliente', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  pide: async () => ({ resultados: [] }),
}))

import { Mosaico } from './Mosaico'

/* ---------------------------------------------------------------- los datos --- */

/** Una tarjeta de `GET /api/habituales`, con su origen. */
function tarjeta(grupoId: number, nombre: string, origen: 'tuyo' | 'de todos' | 'basico' = 'tuyo') {
  return {
    grupo_id: grupoId,
    nombre,
    precio_unidad_cent: 100 + grupoId,
    unidad: 'kg',
    cadena_mas_barata: 'dia',
    fiable: true,
    origen,
  }
}

function conHabituales(tarjetas: unknown[], origenes: string[] = ['tuyo']) {
  estado.habituales = {
    isPending: false,
    data: { origenes, habituales: tarjetas, fecha_datos: '2026-11-06' },
  }
}

beforeEach(() => {
  estado.anade.isPending = false
  estado.anade.isError = false
  estado.anade.error = null
  estado.anade.mutate.mockReset()
  estado.anade.mutateAsync.mockReset()
  // *El «Añadir» de una tarjeta avisa por `onSuccess`, como la mutación de verdad.*
  estado.anade.mutate.mockImplementation((_x: unknown, opciones?: { onSuccess?: () => void }) => {
    opciones?.onSuccess?.()
  })
  estado.anade.mutateAsync.mockResolvedValue('L1')
  conHabituales([tarjeta(1, 'Leche entera'), tarjeta(2, 'Pan de molde'), tarjeta(3, 'Huevos')])
})

/** *La tarjeta de la primera vez usa `useQueries`: sin cliente no se puede montar.* */
function monta(ui: ReactElement) {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={cliente}>{ui}</QueryClientProvider>)
}

/* ================================================================ rellenar === */

describe('rellenar de una vez', () => {
  it('*** ofrece la siguiente y dice cuántos faltan, sin inventar frecuencias ***', () => {
    monta(<Mosaico enUnaLista />)
    // *La sugerencia sale del orden de la API (la primera que falta), y no de un «lo que más
    // compras» que esta pantalla no sabe.*
    expect(screen.getByText(/La siguiente sería/)).toBeInTheDocument()
    expect(screen.getByText('Leche entera', { selector: 'strong' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rellenar de una vez (3)' })).toBeInTheDocument()
  })

  it('*** la previa dice cuántos y cuáles, y NO guarda nada ***', async () => {
    monta(<Mosaico enUnaLista />)
    await userEvent.click(screen.getByRole('button', { name: 'Rellenar de una vez (3)' }))

    expect(screen.getByText('Se van a añadir 3 productos:')).toBeInTheDocument()
    const previa = screen.getByText('Se van a añadir 3 productos:').closest('div') as HTMLElement
    for (const nombre of ['Leche entera', 'Pan de molde', 'Huevos']) {
      expect(previa).toHaveTextContent(nombre)
    }
    // *La previa es previa: hasta que no se confirma no se ha pedido nada.*
    expect(estado.anade.mutateAsync).not.toHaveBeenCalled()
  })

  it('al confirmar, añade una vez por producto en el orden de la API', async () => {
    monta(<Mosaico enUnaLista />)
    await userEvent.click(screen.getByRole('button', { name: 'Rellenar de una vez (3)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Sí, añadir 3' }))

    expect(estado.anade.mutateAsync).toHaveBeenCalledTimes(3)
    expect(estado.anade.mutateAsync.mock.calls.map((c) => c[0])).toEqual([
      { grupoId: 1, nombre: 'Leche entera' },
      { grupoId: 2, nombre: 'Pan de molde' },
      { grupoId: 3, nombre: 'Huevos' },
    ])
    expect(await screen.findByText('Añadidos 3 productos a la lista.')).toBeInTheDocument()
  })

  it('*** lo que ya está en la lista no se ofrece ni se repite ***', async () => {
    // *El pan ya viene en la lista que se está mirando: la previa no puede contarlo.*
    monta(<Mosaico enUnaLista enLaLista={[2]} />)

    expect(screen.getByRole('button', { name: 'Rellenar de una vez (2)' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Rellenar de una vez (2)' }))
    const previa = screen.getByText('Se van a añadir 2 productos:').closest('div') as HTMLElement
    expect(previa).not.toHaveTextContent('Pan de molde')
    expect(previa).toHaveTextContent('Huevos')

    // *Y lo que se añade aquí (`puestos`) tampoco vuelve a la previa.*
    await userEvent.click(screen.getByRole('button', { name: 'No, déjalo' }))
    const anadir = screen.getAllByRole('button', { name: 'Añadir' })
    expect(anadir).toHaveLength(2)
    await userEvent.click(anadir[0] as HTMLElement)
    expect(screen.getByRole('button', { name: 'Rellenar de una vez (1)' })).toBeInTheDocument()
    // *El pan (que ya venía en la lista) y el que se acaba de añadir: los dos, dentro.*
    expect(screen.getAllByText('En la cesta')).toHaveLength(2)
  })

  it('*** si falla a medias, dice cuántos entraron y cuántos no ***', async () => {
    estado.anade.mutateAsync
      .mockResolvedValueOnce('L1')
      .mockRejectedValueOnce(new Error('sin red'))
    monta(<Mosaico enUnaLista />)

    await userEvent.click(screen.getByRole('button', { name: 'Rellenar de una vez (3)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Sí, añadir 3' }))

    // *Se para en el primero que falla: los dos últimos no se han pedido.*
    expect(estado.anade.mutateAsync).toHaveBeenCalledTimes(2)
    const aviso = await screen.findByRole('alert')
    expect(aviso).toHaveTextContent('Se han añadido 1 de 3')
    expect(aviso).toHaveTextContent('El resto no ha entrado')
    expect(aviso).toHaveTextContent('sin red')
    // *Y lo que sí entró se queda marcado: no se vuelve a ofrecer.*
    expect(screen.getByText('En la cesta')).toBeInTheDocument()
  })
})

/* ========================================================== el estado honesto === */

describe('el estado honesto que ya había', () => {
  it('sin historial y fuera de una lista, no ofrece rellenar', () => {
    conHabituales([tarjeta(1, 'Leche entera', 'basico')], ['basico'])
    monta(<Mosaico />)
    // *La tarjeta de la primera vez sustituye a la cuadrícula: primero se entiende, después se
    // usa. Y sin cuadrícula no hay «rellenar» que ofrecer.*
    expect(screen.queryByRole('button', { name: /Rellenar de una vez/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Añadir' })).not.toBeInTheDocument()
  })

  it('con la compra básica dentro de la lista, se dice de dónde sale y se puede rellenar', () => {
    conHabituales([tarjeta(1, 'Leche entera', 'basico')], ['basico'])
    monta(<Mosaico enUnaLista />)
    // *El título dice la verdad: es la compra básica, no «lo de siempre».*
    expect(screen.getByText('La compra básica')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rellenar de una vez (1)' })).toBeInTheDocument()
  })
})
