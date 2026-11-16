/** *** EL MISMO PRODUCTO, CADENA A CADENA. *** *
 *
 *  *La demo no puede limitarse a decir «5 cadenas»: tiene que enseñar el precio de cada
 *  una, con la misma unidad, y decir cuántas comparan. Esta prueba monta el panel con un
 *  producto real del catálogo embebido —Leche entera brik 1 l., grupo 11627— y exige las
 *  cinco cadenas y sus €/litro.*
 *
 *  *El panel es lo que contesta «¿dónde está más barato este mismo producto?», que es
 *  distinto de «¿dónde sale más barata la lista entera?». Por eso se prueba solo, sin
 *  montar la pantalla de búsqueda.*
 */
import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { grupoDelCatalogo } from '../demo/catalogo'

vi.mock('../api/consultas', async () => {
  const { grupoDelCatalogo: grupo } = await import('../demo/catalogo')
  const datos = grupo(11627)
  return {
    useGrupo: () => ({ isPending: false, isError: false, data: datos, refetch: vi.fn() }),
  }
})

import { OfertasDelProducto } from './OfertasDelProducto'

describe('la comparación de un mismo producto entre cadenas', () => {
  it('enseña las cinco cadenas con su precio por unidad y la diferencia', () => {
    render(<OfertasDelProducto grupoId={11627} nombre="Leche entera brik 1 l." />)

    // *El panel dice cuántas cadenas compara, no solo cuáles.*
    expect(screen.getByText(/5 cadenas/)).toBeInTheDocument()

    const lista = screen.getByRole('list')
    const filas = within(lista).getAllByRole('listitem')
    expect(filas).toHaveLength(5)

    // *Las cinco cadenas reales del grupo, de más barata a más cara por litro.*
    expect(filas[0]).toHaveTextContent('Carrefour')
    expect(filas[0]).toHaveTextContent('0,94 €/l')
    expect(filas[1]).toHaveTextContent('Aldi')
    expect(filas[1]).toHaveTextContent('0,96 €/l')
    expect(filas[2]).toHaveTextContent('Mercadona')
    expect(filas[2]).toHaveTextContent('0,96 €/l')
    expect(filas[3]).toHaveTextContent('DIA')
    expect(filas[3]).toHaveTextContent('1,09 €/l')
    expect(filas[4]).toHaveTextContent('Alcampo')
    expect(filas[4]).toHaveTextContent('2,09 €/l')

    // *La más barata va marcada: no hay que comparar cinco cifras para saber cuál es.*
    expect(filas[0]).toHaveTextContent('más barata')

    // *Y la distancia entre la más barata y la más cara, en euros **y en porcentaje**: un
    // euro y medio dice cuanto, el porcentaje dice cuanto pesa sobre el precio caro.*
    expect(screen.getByText(/1,15 €\/l de diferencia/)).toBeInTheDocument()
    // *El porcentaje y el ahorro por fila pueden quedar partidos en varios nodos, y el
    // formateador de euros usa espacio duro; se normaliza y se mira el texto del panel
    // entero, que es lo que lee una persona.*
    const texto = (screen.getByRole('region').textContent ?? '').replace(/\u00a0/g, ' ')
    expect(texto).toContain('ahorras 1,15 €/l (55 %)')
    expect(texto).toContain('(55 %)')
  })
})
