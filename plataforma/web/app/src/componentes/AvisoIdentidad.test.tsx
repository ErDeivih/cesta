/** *** EL AVISO DE IDENTIDAD: SÓLO CUANDO HAY ALGO QUE DECIR, Y DISTINGUIENDO LOS DOS CASOS. ***
 *
 * *`AvisoIdentidad` lo dice en su cabecera:*
 *
 *   «**Solo aparece cuando hay algo que decir.** Con `exacto` o sin veredicto no pinta nada: un aviso que
 *    sale siempre deja de leerse.»
 *
 *   «**Y distingue los dos casos que importan.** `probable` es "parece el mismo, pero no tengo el codigo que
 *    lo confirme": pide prudencia. `alternativa`, `cuarentena` o `abstiene` es "esto no es lo que pediste":
 *    pide una decision. **Juntarlos en un solo aviso naranja seria perder la unica distincion que el motor
 *    de identidad se ha molestado en calcular.**»
 *
 * *** Y no tenia pruebas. ***
 *
 * *Es el componente que evita el fallo que el encargo nombra con palabras: **elegir un producto concreto no
 * autoriza a sustituirlo por otro mas barato**, y una sustitucion que no se ve es exactamente lo que hay que
 * evitar.*
 */

import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { AvisoIdentidad } from './AvisoIdentidad'

describe('AvisoIdentidad', () => {
  it('*** no pinta NADA cuando la identidad esta confirmada ***', () => {
    // *«Un aviso que sale siempre deja de leerse.»*
    for (const confirmado of ['exacto', null, undefined]) {
      const { container } = render(<AvisoIdentidad identidad={confirmado} />)
      expect(container).toBeEmptyDOMElement()
    }
  })

  it('*** `probable` pide prudencia, no alarma ***', () => {
    // *«Parece el mismo, pero no tengo el codigo que lo confirme.»*
    render(<AvisoIdentidad identidad="probable" />)
    const aviso = screen.getByRole('note')
    expect(aviso.textContent).toMatch(/puede que sea el mismo/i)
    expect(aviso.textContent).toMatch(/no hay c[oó]digo que lo confirme/i)
    // *Y no puede decir que es otro producto: no lo sabe.*
    expect(aviso.textContent).not.toMatch(/otro producto/i)
  })

  it('*** y `alternativa`, `cuarentena` y `abstiene` dicen que NO es el que pediste ***', () => {
    // *Los tres piden una decision, y el texto tiene que ser el mismo de los tres.*
    for (const estado of ['alternativa', 'cuarentena', 'abstiene']) {
      const { container, unmount } = render(<AvisoIdentidad identidad={estado} />)
      const aviso = container.querySelector('[role="note"]')
      expect(aviso).not.toBeNull()
      expect(aviso!.textContent).toMatch(/otro producto/i)
      expect(aviso!.textContent).toMatch(/no con el que pediste/i)
      // *Y al contrario que `probable`: aqui NO se dice «puede que sea el mismo».*
      expect(aviso!.textContent).not.toMatch(/puede que sea el mismo/i)
      unmount()
    }
  })

  it('*** los dos casos se distinguen por color, no solo por texto ***', () => {
    // *«Juntarlos en un solo aviso naranja seria perder la unica distincion que el motor se ha molestado en
    // calcular.»*
    const { container: prudencia } = render(<AvisoIdentidad identidad="probable" />)
    const clasePrudencia = prudencia.querySelector('[role="note"]')!.className
    expect(clasePrudencia).toMatch(/aviso/)

    const { container: decision } = render(<AvisoIdentidad identidad="alternativa" />)
    const claseDecision = decision.querySelector('[role="note"]')!.className
    expect(claseDecision).toMatch(/error/)
    expect(claseDecision).not.toMatch(/border-aviso/)
  })

  it('el motivo, si lo hay, se dice debajo', () => {
    render(<AvisoIdentidad identidad="cuarentena" motivo="el EAN no coincide con la ficha" />)
    expect(screen.getByText(/el EAN no coincide con la ficha/)).toBeInTheDocument()
  })

  it('*** y si hay alternativa, se ofrece con su precio y su cadena ***', () => {
    // *«Un aviso que dice "esto no es lo tuyo" y no ofrece nada deja a quien compra sin salida; con la
    // alternativa delante, el aviso se convierte en una decision.»*
    render(
      <AvisoIdentidad
        identidad="alternativa"
        alternativa={{ nombre: 'Arroz bomba', coste_cent: 245, fuente: 'mercadona' }}
      />,
    )
    const aviso = screen.getByRole('note')
    expect(aviso.textContent).toMatch(/Arroz bomba/)
    // *El precio, con `euros`, y la cadena, con `nombreCadena`: las dos reglas del proyecto.*
    expect(aviso.textContent).toMatch(/2,45/)
    expect(aviso.textContent).toMatch(/Mercadona/)
    expect(aviso.textContent).not.toMatch(/\bmercadona\b/)
  })

  it('*** sin alternativa, no se inventa una oferta ***', () => {
    render(<AvisoIdentidad identidad="alternativa" />)
    const aviso = screen.getByRole('note')
    expect(aviso.textContent).not.toMatch(/En su lugar puedes pedir/i)
  })
})
