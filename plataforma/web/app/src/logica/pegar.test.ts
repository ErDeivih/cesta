/** Leer una lista pegada: texto de siempre, CSV con cabecera o JSON de una exportacion.
 *
 *  La regla que no cambia con el formato: **la cantidad va a la nota, no a un numero de envases**.
 */
import { describe, expect, it } from 'vitest'

import { leerPegado, parteLoPegado, resumenDeLaLectura } from './pegar'

describe('pegar una lista', () => {
  it('el texto libre de siempre sigue partiendo la cantidad a la nota', () => {
    const lectura = leerPegado('2 kg de arroz\nleche')
    expect(lectura.formato).toBe('texto')
    expect(lectura.pegadas).toEqual([
      { nombre: 'arroz', cantidad: '2', unidad: 'kg', nota: '2 kg' },
      { nombre: 'leche', cantidad: null, unidad: null, nota: '' },
    ])
    expect(parteLoPegado('leche')).toHaveLength(1)
  })

  it('un CSV con cabecera nombre,cantidad,nota se lee sin inventar envases', () => {
    const lectura = leerPegado('nombre,cantidad,nota\r\narroz,2 kg,el de siempre\r\nleche,1 l,')
    expect(lectura.formato).toBe('csv')
    expect(lectura.pegadas).toEqual([
      { nombre: 'arroz', cantidad: '2 kg', unidad: null, nota: '2 kg · el de siempre' },
      { nombre: 'leche', cantidad: '1 l', unidad: null, nota: '1 l' },
    ])
    expect(resumenDeLaLectura(lectura)).toContain('Leido de un CSV')
  })

  it('el CSV respeta comas dentro de comillas y las filas sin nombre se cuentan', () => {
    const lectura = leerPegado('nombre,nota\n"tomate, pera",para el martes\n,sin nombre')
    expect(lectura.pegadas).toEqual([
      { nombre: 'tomate, pera', cantidad: null, unidad: null, nota: 'para el martes' },
    ])
    expect(lectura.avisos.join(' ')).toMatch(/1 fila\(s\) sin nombre/)
  })

  it('un JSON de objetos con nombre, cantidad y nota se lee igual', () => {
    const lectura = leerPegado(JSON.stringify([
      { nombre: 'arroz', cantidad: '2 kg', nota: 'el de siempre' },
      { name: 'leche', quantity: 1, notes: 'entera' },
    ]))
    expect(lectura.formato).toBe('json')
    expect(lectura.pegadas).toEqual([
      { nombre: 'arroz', cantidad: '2 kg', unidad: null, nota: '2 kg · el de siempre' },
      { nombre: 'leche', cantidad: '1', unidad: null, nota: '1 · entera' },
    ])
  })

  it('un JSON envuelto en productos tambien vale', () => {
    const lectura = leerPegado(JSON.stringify({ productos: [{ nombre: 'pan' }] }))
    expect(lectura.formato).toBe('json')
    expect(lectura.pegadas[0]?.nombre).toBe('pan')
  })

  it('un JSON roto no se inventa: se trata como texto y se avisa', () => {
    const lectura = leerPegado('[{nombre: roto]')
    expect(lectura.formato).toBe('texto')
    expect(lectura.avisos.join(' ')).toContain('No se ha podido leer como JSON')
  })

  it('un CSV sin cabecera reconocible se trata como texto', () => {
    const lectura = leerPegado('leche,pan,huevos')
    expect(lectura.formato).toBe('texto')
    expect(lectura.pegadas[0]?.nombre).toBe('leche,pan,huevos')
  })
})
