/** *** ELEGIR VARIAS LINEAS CON EL TECLADO, Y SABER CUANTAS VAN. *** *
 *
 *  *Tachar o quitar de una en una, sesenta veces, es el trabajo que hace que la lista se deje de
 *  usar. Lo que se mide aqui es la seleccion accesible: listbox multiple, `aria-selected`, Espacio
 *  que marca, Ctrl+A que marca todas, barra que dice cuantas van, Escape que sale y accion en lote
 *  que recibe exactamente las marcadas.*
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SeleccionMultiple } from './SeleccionMultiple'

const filas = [
  { id: 'l1', nombre: 'Leche entera 1,5 l', precioCent: 197 },
  { id: 'l2', nombre: 'Pan de molde', precioCent: 145 },
  { id: 'l3', nombre: 'Yogur natural', precioCent: 89 },
]

function pinta(alQuitar = vi.fn(), alSalir = vi.fn()) {
  return render(<SeleccionMultiple filas={filas} alQuitar={alQuitar} alSalir={alSalir} />)
}

describe('SeleccionMultiple: el listbox y la barra', () => {
  it('es un listbox multiple con nombre y una opcion por linea', () => {
    pinta()
    const lista = screen.getByRole('listbox', { name: 'Líneas de la compra' })
    expect(lista).toHaveAttribute('aria-multiselectable', 'true')
    expect(screen.getAllByRole('option')).toHaveLength(3)
  })

  it('Espacio marca la opcion enfocada y la barra lo dice con el número', async () => {
    pinta()
    const opciones = screen.getAllByRole('option')
    opciones[0].focus()

    await userEvent.keyboard(' ')
    expect(opciones[0]).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('1 línea seleccionada')).toBeInTheDocument()

    // *Y volver a pulsar la desmarca: marcar no es un viaje de ida.*
    await userEvent.keyboard(' ')
    expect(opciones[0]).toHaveAttribute('aria-selected', 'false')
    expect(screen.queryByText(/línea(s)? seleccionada/)).not.toBeInTheDocument()
  })

  it('Ctrl+A marca todas y la accion en lote recibe sus ids', async () => {
    const alQuitar = vi.fn()
    pinta(alQuitar)
    screen.getAllByRole('option')[0].focus()

    await userEvent.keyboard('{Control>}a{/Control}')
    expect(screen.getByText('3 líneas seleccionadas')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Quitar 3 líneas' }))
    await waitFor(() => expect(alQuitar).toHaveBeenCalledTimes(1))
    expect(alQuitar.mock.calls[0][0]).toEqual(['l1', 'l2', 'l3'])
  })

  it('Escape sale de la seleccion y avisa a la pantalla', async () => {
    const alSalir = vi.fn()
    pinta(vi.fn(), alSalir)
    screen.getByRole('listbox', { name: 'Líneas de la compra' }).focus()

    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(alSalir).toHaveBeenCalledTimes(1))
  })
})
