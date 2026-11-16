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

/** *El grupo que devuelve cada prueba; el mock lo lee al pintar.* */
const dobles = vi.hoisted(() => ({ grupo: null as unknown }))

vi.mock('../api/consultas', async () => {
  const { grupoDelCatalogo: grupo } = await import('../demo/catalogo')
  return {
    useGrupo: () => ({
      isPending: false,
      isError: false,
      data: dobles.grupo ?? grupo(11627),
      refetch: vi.fn(),
    }),
  }
})

import { OfertasDelProducto } from './OfertasDelProducto'

describe('la comparación de un mismo producto entre cadenas', () => {
  it('enseña las cinco cadenas con su precio por unidad y la diferencia', () => {
    dobles.grupo = grupoDelCatalogo(11627)
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

  it('con dos cadenas: la más barata marcada y el ahorro en euros y porcentaje', () => {
    // *Un producto que solo está en dos cadenas: es el caso mínimo de comparación, y el
    // que tiene que seguir funcionando cuando no hay cinco precios que mirar.*
    dobles.grupo = grupoDelCatalogo(9375)
    render(<OfertasDelProducto grupoId={9375} nombre="ZARTA Lentejas con chorizo en conserva 430 g." />)

    expect(screen.getByText(/2 cadenas/)).toBeInTheDocument()
    const filas = within(screen.getByRole('list')).getAllByRole('listitem')
    expect(filas).toHaveLength(2)
    expect(filas[0]).toHaveTextContent('Alcampo')
    expect(filas[0]).toHaveTextContent('2,81 €/kg')
    expect(filas[0]).toHaveTextContent('más barata')
    expect(filas[1]).toHaveTextContent('DIA')
    expect(filas[1]).toHaveTextContent('3,14 €/kg')

    const texto = (screen.getByRole('region').textContent ?? '').replace(/\u00a0/g, ' ')
    expect(texto).toContain('ahorras 0,33 €/kg (10,4 %)')
    expect(texto).toContain('0,33 €/kg de diferencia (10,4 %)')
  })
})
