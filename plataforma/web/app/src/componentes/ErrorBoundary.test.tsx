/** *** LA PRUEBA QUE FALTABA: un componente MONTADO que revienta. ***
 *
 *  *No comprueba una constante ni una funcion: monta un arbol de React de verdad, con jsdom, y mira
 *  lo que ve una persona.* *Es lo que M02 pide y lo que el 18/10/2026 no existia.*
 *
 *  *Y comprueba lo importante: que **un fallo de render no deja la pantalla muda**.*
 */
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from './ErrorBoundary'

function Explota(): never {
  throw new Error('fallo de prueba a proposito')
}

function Bien() {
  return <p>contenido que si funciona</p>
}

describe('ErrorBoundary', () => {
  it('monta a los hijos cuando no hay error', () => {
    render(
      <ErrorBoundary>
        <Bien />
      </ErrorBoundary>,
    )
    expect(screen.getByText('contenido que si funciona')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('cuando un hijo revienta, la pantalla DICE que algo fallo (no se queda en blanco)', () => {
    const silencio = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary que="la ficha">
        <Explota />
      </ErrorBoundary>,
    )
    const alerta = screen.getByRole('alert')
    expect(alerta).toBeInTheDocument()
    expect(alerta).toHaveTextContent('No he podido mostrar la ficha')
    // *Una referencia para poder cruzarla con la consola, sin datos de nadie.*
    expect(alerta.textContent).toMatch(/F-[A-Z0-9]{4,}/)
    silencio.mockRestore()
  })

  it('y ofrece un boton de reintentar que se puede pulsar', async () => {
    // *** LO QUE ESTA PRUEBA NO DEMUESTRA, *y por eso se dice***: *que el reintento **remonte** y
    // funcione.* *React 19, al fallar un render en modo concurrente, **reintenta en sincrono antes
    // de rendirse** -- «React was able to recover by instead synchronously rendering» --, asi que un
    // componente que falla solo la primera vez se recupera sin que la frontera llegue a verse, y la
    // prueba que escribi para eso medía el reintento de React, no el mio.*
    //
    // *Lo que si se comprueba aqui, y es el contrato que importa: **el boton existe, tiene nombre
    // accesible y se puede pulsar sin romper nada**.* *El remontaje hay que probarlo de otra forma
    // —con un componente que falle siempre y un doble que cuente los montajes—, y queda pendiente.*
    const silencio = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary que="la ficha">
        <Explota />
      </ErrorBoundary>,
    )
    const boton = screen.getByRole('button', { name: 'Reintentar' })
    expect(boton).toBeEnabled()
    await userEvent.click(boton)
    silencio.mockRestore()
  })

  it('NO finge exito: el mensaje no dice que todo va bien', () => {
    const silencio = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Explota />
      </ErrorBoundary>,
    )
    const texto = screen.getByRole('alert').textContent ?? ''
    expect(texto).not.toMatch(/todo (bien|correcto)/i)
    expect(texto).toMatch(/fall/i)
    silencio.mockRestore()
  })
})
