/** *** LA VENTANA DE LA LISTA: LO QUE SE PINTA, LO QUE SE ANUNCIA Y LO QUE SE DESPLAZA. *** *
 *
 *  *Con 60 lineas en el movil, pintar las 60 es lo que paga el primer pintado entero, y el
 *  lector de pantalla se queda sin saber cuantas hay si solo ve 12.* *Aqui se mide lo que la
 *  pieza promete y lo que se rompe callando:*
 *
 *   - **la ventana**: con 60 filas se pintan solo las visibles mas el overscan, ni una mas;
 *   - **la altura**: el hueco de las que no estan se reserva, o la barra de scroll mentiria;
 *   - **la posicion**: `aria-setsize`/`aria-posinset` dicen donde esta cada fila pintada;
 *   - **el teclado**: con el foco dentro, las flechas desplazan la ventana y el `aria-live`
 *     dice por donde va («linea 2 de 60»), que es lo unico que oye quien no ve la barra.
 */
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ListaVirtualizada } from './ListaVirtualizada'

/** Sesenta filas de texto, la lista del caso real (60 lineas en la comparativa). */
const filas = Array.from({ length: 60 }, (_, i) => `Fila ${i + 1}`)

/** La pieza montada como la usa la pantalla: filas de 50 px en una ventana de 300 px. */
function pinta() {
  return render(
    <ListaVirtualizada
      filas={filas}
      alturaFila={50}
      alto={300}
      overscan={3}
      etiqueta="Líneas de la lista"
      render={(fila, indice) => <li>{`${indice + 1}. ${fila}`}</li>}
    />,
  )
}

/** La ventana con scroll: es lo que recibe el foco y las teclas. */
function ventana(): HTMLElement {
  return screen.getByRole('group', { name: 'Líneas de la lista' })
}

describe('ListaVirtualizada: la ventana', () => {
  it('con 60 filas solo pinta las visibles mas el overscan, no las 60', () => {
    // *300 px de alto entre filas de 50 son 6 visibles; 6 + 2*3 de overscan = 12.* *Si
    // pintara 60, la pieza no serviria de nada y la prueba lo diria.*
    pinta()

    const pintadas = screen.getAllByRole('listitem')
    expect(pintadas).toHaveLength(12)
    expect(pintadas[0]).toHaveTextContent('1. Fila 1')
    expect(pintadas[11]).toHaveTextContent('12. Fila 12')
  })

  it('la ventana mide lo que se le pide y reserva la altura de las que no estan', () => {
    // *Una barra de scroll que ignore las 48 filas que no se pintan haria creer que la lista
    // acaba a las 12, y no se podria llegar al final deslizando.*
    pinta()

    const caja = ventana()
    expect(caja).toHaveStyle({ height: '300px' })
    // *El contenido total: 60 filas * 50 px = 3000 px.*
    expect(caja.firstElementChild as HTMLElement).toHaveStyle({ height: '3000px' })
  })

  it('cada fila pintada dice su posicion en la lista entera, no en la ventana', () => {
    // *El lector de pantalla tiene que oir «12 de 60» aunque en el DOM solo haya 12.*
    pinta()

    const pintadas = screen.getAllByRole('listitem')
    expect(pintadas[0]).toHaveAttribute('aria-posinset', '1')
    expect(pintadas[0]).toHaveAttribute('aria-setsize', '60')
    expect(pintadas[11]).toHaveAttribute('aria-posinset', '12')
    expect(pintadas[11]).toHaveAttribute('aria-setsize', '60')
  })

  it('al bajar por la lista, la ventana se mueve y el aria-live dice por donde va', () => {
    // *scrollTop 1000 son 20 filas de 50 px: la primera visible es la 21, y el overscan pinta
    // tres por encima -- la 18 --, que es justo lo que se comprueba con el posinset.*
    pinta()
    const caja = ventana()

    fireEvent.scroll(caja, { target: { scrollTop: 1000 } })

    const pintadas = screen.getAllByRole('listitem')
    expect(pintadas).toHaveLength(12)
    expect(pintadas[0]).toHaveAttribute('aria-posinset', '18')
    expect(pintadas[11]).toHaveAttribute('aria-posinset', '29')
    expect(screen.getByText('línea 21 de 60')).toBeInTheDocument()
  })
})

describe('ListaVirtualizada: el teclado con el foco dentro', () => {
  it('las flechas desplazan la ventana fila a fila', () => {
    pinta()
    const caja = ventana()
    caja.focus()
    expect(caja).toHaveFocus()

    fireEvent.keyDown(caja, { key: 'ArrowDown' })
    expect(caja.scrollTop).toBe(50)
    expect(screen.getByText('línea 2 de 60')).toBeInTheDocument()

    fireEvent.keyDown(caja, { key: 'ArrowUp' })
    expect(caja.scrollTop).toBe(0)
    expect(screen.getByText('línea 1 de 60')).toBeInTheDocument()
  })

  it('Fin e Inicio van al final y al principio de la lista entera', () => {
    // *Fin no es «una pantalla mas»: es la ultima fila, y el anuncio tiene que decirlo.*
    pinta()
    const caja = ventana()
    caja.focus()

    fireEvent.keyDown(caja, { key: 'End' })
    expect(caja.scrollTop).toBe(2700)
    expect(screen.getByText('línea 60 de 60')).toBeInTheDocument()

    fireEvent.keyDown(caja, { key: 'Home' })
    expect(caja.scrollTop).toBe(0)
    expect(screen.getByText('línea 1 de 60')).toBeInTheDocument()
  })

  it('Avanzar y Retroceder pagina saltan una ventana entera', () => {
    // *Con 6 visibles, PageDown desde el principio deja la fila 7 arriba.*
    pinta()
    const caja = ventana()
    caja.focus()

    fireEvent.keyDown(caja, { key: 'PageDown' })
    expect(caja.scrollTop).toBe(300)
    expect(screen.getByText('línea 7 de 60')).toBeInTheDocument()

    fireEvent.keyDown(caja, { key: 'PageUp' })
    expect(caja.scrollTop).toBe(0)
    expect(screen.getByText('línea 1 de 60')).toBeInTheDocument()
  })
})
