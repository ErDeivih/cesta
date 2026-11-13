/** *** LO QUE SE ABRE ENCIMA DE LA PANTALLA, CON EL FOCO DONDE TIENE QUE ESTAR. *** *
 *
 *  *Un dialogo sin trampa de foco deja al teclado detras de la capa, y al cerrar no vuelve a
 *  quien lo abrio: la persona se queda en el principio de la pagina sin saber por que.* *Aqui se
 *  mide el contrato entero: nombre accesible, foco dentro, Tab que no se escapa, Escape que cierra
 *  y foco que vuelve.*
 */
import { useState } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { Dialogo } from './Foco'

/** La pieza montada como la usa la pantalla: un boton que abre y un dialogo que confirma. */
function pinta() {
  function Demo() {
    const [abierto, setAbierto] = useState(false)
    return (
      <>
        <button type="button" onClick={() => setAbierto(true)}>
          He terminado la compra
        </button>
        <Dialogo
          abierto={abierto}
          alCerrar={() => setAbierto(false)}
          titulo="Terminar la compra"
          descripcion="Se guardan como compra, con su precio."
        >
          <button type="button">Sí, he terminado</button>
          <button type="button">No, déjalo</button>
        </Dialogo>
      </>
    )
  }
  return render(<Demo />)
}

describe('Dialogo: nombre, foco y salida', () => {
  it('no pinta nada hasta que se abre, y al abrirse tiene nombre y el foco dentro', async () => {
    pinta()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'He terminado la compra' }))

    const dialogo = await screen.findByRole('dialog', { name: 'Terminar la compra' })
    expect(dialogo).toHaveAttribute('aria-modal', 'true')
    expect(dialogo.contains(document.activeElement)).toBe(true)
  })

  it('Tab no saca el foco del dialogo', async () => {
    pinta()
    await userEvent.click(screen.getByRole('button', { name: 'He terminado la compra' }))
    const dialogo = await screen.findByRole('dialog', { name: 'Terminar la compra' })

    for (let i = 0; i < 6; i += 1) {
      await userEvent.tab()
      expect(dialogo.contains(document.activeElement)).toBe(true)
    }
  })

  it('Escape cierra y devuelve el foco a quien lo abrió', async () => {
    pinta()
    const disparador = screen.getByRole('button', { name: 'He terminado la compra' })
    disparador.focus()
    await userEvent.click(disparador)
    await screen.findByRole('dialog', { name: 'Terminar la compra' })

    await userEvent.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(disparador).toHaveFocus()
  })
})
