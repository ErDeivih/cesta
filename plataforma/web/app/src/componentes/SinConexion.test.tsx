/** El aviso de sin conexión: aparece cuando no hay red y se va cuando vuelve.
 *
 *  Se prueba aquí y no en cada pantalla porque el dato es uno solo
 *  (`estado/conexion.ts`): si esta prueba pasa, las tres pantallas dicen lo mismo.
 */
import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { SinConexion } from './SinConexion'

/** jsdom da `navigator.onLine` siempre en `true`: se sustituye para el caso que se prueba. */
function ponRed(hay: boolean) {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    get: () => hay,
  })
}

describe('SinConexion', () => {
  afterEach(() => ponRed(true))

  it('con red no se pinta nada: un aviso que sale siempre no avisa de nada', () => {
    ponRed(true)
    const { container } = render(<SinConexion />)
    expect(container).toBeEmptyDOMElement()
  })

  it('sin red dice que se guarda en el móvil, no que se haya perdido', () => {
    ponRed(false)
    render(<SinConexion />)
    expect(screen.getByText('Sin conexión')).toBeInTheDocument()
    expect(screen.getByText(/se guarda en el móvil/i)).toBeInTheDocument()
  })

  it('cuando vuelve la red, el aviso se va sin recargar', () => {
    ponRed(false)
    render(<SinConexion />)
    expect(screen.getByText('Sin conexión')).toBeInTheDocument()

    act(() => {
      ponRed(true)
      window.dispatchEvent(new Event('online'))
    })

    expect(screen.queryByText('Sin conexión')).not.toBeInTheDocument()
  })

  it('y si se cae la red con la pantalla abierta, aparece', () => {
    ponRed(true)
    render(<SinConexion />)
    expect(screen.queryByText('Sin conexión')).not.toBeInTheDocument()

    act(() => {
      ponRed(false)
      window.dispatchEvent(new Event('offline'))
    })

    expect(screen.getByText('Sin conexión')).toBeInTheDocument()
  })
})
