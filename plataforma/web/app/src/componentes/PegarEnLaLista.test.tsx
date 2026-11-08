/** *** PEGAR: SE VE ANTES DE GUARDAR, Y «2 kg» NO SE CONVIERTE EN ENVASES. ***
 *
 *  *M05 pide dos cosas de esto, y las dos se prueban aqui:*
 *
 *    1. «pegar varias lineas **con previa**» -- que se vea lo que se va a guardar
 *    2. «no interpretar «2 kg» como dos envases **sin base**»
 *
 *  *La segunda esta en el tipo (`logica/pegar.ts`), pero aqui se comprueba **lo que llega a
 *  `alAnadir`**: nombre y nota. Si el componente pasara una `cantidad`, el alta la guardaria como
 *  numero de envases y el fallo volveria por la puerta de atras.*
 */

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { PegarEnLaLista } from './PegarEnLaLista'

describe('PegarEnLaLista', () => {
  it('enseña la previa antes de guardar nada, y no llama a alAnadir', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.type(screen.getByLabelText(/lo que quieres pegar/i), '2 kg de arroz{enter}pan')

    // *La previa esta:* las dos lineas, y la nota del arroz.
    expect(screen.getByText('arroz')).toBeInTheDocument()
    expect(screen.getByText('pan')).toBeInTheDocument()
    expect(screen.getByText(/queda anotado: 2 kg/)).toBeInTheDocument()
    // *Y NO se ha guardado nada: la previa es previa.*
    expect(alAnadir).not.toHaveBeenCalled()
  })

  it('el resumen dice cuantas lineas y cuantas con cantidad', async () => {
    render(<PegarEnLaLista alAnadir={vi.fn()} />)
    await userEvent.type(
      screen.getByLabelText(/lo que quieres pegar/i),
      '2 kg de arroz{enter}pan{enter}1 l de leche',
    )
    expect(screen.getByText(/3 lineas, 2 con cantidad/)).toBeInTheDocument()
    expect(screen.getByText(/no se convierte en envases/)).toBeInTheDocument()
  })

  it('*** un CSV con cabecera se enseña antes de guardar y no inventa envases ***', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.click(screen.getByLabelText(/lo que quieres pegar/i))
    await userEvent.paste('nombre,cantidad,nota\narroz,2 kg,el de siempre\nleche,1 l,')

    expect(screen.getByText('arroz')).toBeInTheDocument()
    expect(screen.getByText(/queda anotado: 2 kg · el de siempre/)).toBeInTheDocument()
    expect(screen.getByText(/Leido de un CSV/)).toBeInTheDocument()
    expect(alAnadir).not.toHaveBeenCalled()
  })

  it('*** un JSON con nombre, cantidad y nota se lee igual ***', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.click(screen.getByLabelText(/lo que quieres pegar/i))
    await userEvent.paste('[{"nombre":"pan","cantidad":"2","nota":"de barra"}]')

    expect(screen.getByText('pan')).toBeInTheDocument()
    expect(screen.getByText(/queda anotado: 2 · de barra/)).toBeInTheDocument()
    expect(screen.getByText(/Leido de un JSON/)).toBeInTheDocument()
    expect(alAnadir).not.toHaveBeenCalled()
  })

  it('*** subir un CSV lo deja en la previa, sin guardar todavia ***', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    const archivo = new File(['nombre,nota\npan,de barra'], 'compra.csv', { type: 'text/csv' })
    await userEvent.upload(screen.getByLabelText('Subir CSV o JSON'), archivo)

    expect(await screen.findByText('pan')).toBeInTheDocument()
    expect(screen.getByText(/Leido de compra.csv/)).toBeInTheDocument()
    expect(alAnadir).not.toHaveBeenCalled()
  })

  it('*** al anadir, la cantidad va en la NOTA y no como numero de envases ***', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.type(screen.getByLabelText(/lo que quieres pegar/i), '2 kg de arroz')
    await userEvent.click(screen.getByRole('button', { name: /anadir 1 linea/i }))

    expect(alAnadir).toHaveBeenCalledTimes(1)
    const [linea] = alAnadir.mock.calls[0]
    // *Lo que se guarda: el nombre limpio y la nota con lo que se escribio.*
    expect(linea).toEqual({ nombre: 'arroz', nota: '2 kg' })
    // *** Y NO hay campo de cantidad: es la regla, comprobada en lo que se envia. ***
    expect('cantidad' in linea).toBe(false)
    expect('envases' in linea).toBe(false)
  })

  it('anade todas las lineas, una por una', async () => {
    const alAnadir = vi.fn().mockResolvedValue(undefined)
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.type(screen.getByLabelText(/lo que quieres pegar/i), 'leche{enter}pan{enter}huevos')
    await userEvent.click(screen.getByRole('button', { name: /anadir 3 lineas/i }))

    expect(alAnadir).toHaveBeenCalledTimes(3)
    expect(alAnadir.mock.calls.map((c) => c[0].nombre)).toEqual(['leche', 'pan', 'huevos'])
    // *Y la nota va vacia (null) cuando no habia cantidad.*
    expect(alAnadir.mock.calls.map((c) => c[0].nota)).toEqual([null, null, null])
  })

  it('si falla, lo dice en vez de callarlo', async () => {
    const alAnadir = vi.fn().mockRejectedValue(new Error('sin red'))
    render(<PegarEnLaLista alAnadir={alAnadir} />)

    await userEvent.type(screen.getByLabelText(/lo que quieres pegar/i), 'leche')
    await userEvent.click(screen.getByRole('button', { name: /anadir 1 linea/i }))

    // *Un fallo a medias deja lineas sin anadir: callarlo es peor que el fallo.*
    expect(await screen.findByRole('alert')).toHaveTextContent(/sin red/)
  })

  it('sin nada pegado no se puede pulsar', () => {
    render(<PegarEnLaLista alAnadir={vi.fn()} />)
    const boton = screen.getByRole('button', { name: /anadir 0 lineas/i })
    expect(boton).toBeDisabled()
  })
})
