/** La lista se puede llevar: CSV para otra app y texto para pegar. */
import { describe, expect, it } from 'vitest'

import type { Linea } from '../tipos'
import { listaACSV, listaATexto, nombreDeFichero } from './exportarLista'

function linea(parcial: Partial<Linea>): Linea {
  return {
    id: 'l1',
    nombre_visto: 'arroz',
    cantidad: 1,
    nota: null,
    grupo_id: null,
    producto_id: null,
    tachado_en: null,
    ...parcial,
  }
}

describe('exportar la lista', () => {
  it('el CSV lleva nombre, cantidad y nota, y escapa comillas', () => {
    const csv = listaACSV([
      linea({ nombre_visto: 'tomate "pera"', cantidad: 2, nota: 'para el martes, si hay' }),
    ])
    expect(csv).toBe(
      'nombre,cantidad,nota\r\n"tomate ""pera""","2","para el martes, si hay"\r\n',
    )
  })

  it('el texto dice la cantidad cuando hace falta y la nota entre parentesis', () => {
    expect(listaATexto([
      linea({ nombre_visto: 'leche', cantidad: 2, nota: 'entera' }),
      linea({ nombre_visto: 'pan' }),
    ])).toBe('2 x leche (entera)\npan')
  })

  it('el nombre del fichero es seguro y no queda vacio', () => {
    expect(nombreDeFichero('Casa / finde')).toBe('cesta-casa-finde.csv')
    expect(nombreDeFichero('')).toBe('cesta-lista.csv')
  })
})
