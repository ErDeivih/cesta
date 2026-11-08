/** La lista se puede copiar o descargar sin conectarse a ninguna cadena.
 *
 *  La descarga real necesita un navegador; lo que se prueba aqui es que los botones existen, que
 *  la copia avisa, y que el texto de socorro aparece cuando el portapapeles no esta disponible.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { Linea } from '../tipos'
import { ExportarLista } from './ExportarLista'

const lineas: Linea[] = [
  {
    id: 'l1', nombre_visto: 'arroz', cantidad: 1, nota: 'el de siempre',
    grupo_id: null, producto_id: null, tachado_en: null,
  },
  {
    id: 'l2', nombre_visto: 'leche', cantidad: 2, nota: null,
    grupo_id: null, producto_id: null, tachado_en: null,
  },
]

describe('ExportarLista', () => {
  it('dice cuantas lineas lleva y ofrece copiar y descargar', () => {
    render(<ExportarLista lineas={lineas} nombreLista="Casa" />)
    expect(screen.getByText('2 lineas con su cantidad y su nota.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copiar lista' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descargar CSV' })).toBeInTheDocument()
    expect(screen.getByText(/No se conecta con ninguna cadena/)).toBeInTheDocument()
  })

  it('si no hay portapapeles, deja el texto para copiarlo a mano', async () => {
    render(<ExportarLista lineas={lineas} nombreLista="Casa" />)
    await userEvent.click(screen.getByRole('button', { name: 'Copiar lista' }))

    expect(await screen.findByLabelText('Texto de la lista')).toHaveValue(
      'arroz (el de siempre)\n2 x leche',
    )
  })

  it('sin lineas no se pinta', () => {
    const { container } = render(<ExportarLista lineas={[]} nombreLista="Casa" />)
    expect(container).toBeEmptyDOMElement()
  })
})
