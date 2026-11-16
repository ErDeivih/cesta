/** *** EL ENLACE DE COMPARTIR LLEVA LA LISTA DENTRO. *** *
 *
 *  *No hay servidor que guarde la lista compartida, así que lo que se prueba es el viaje de ida y
 *  vuelta: la lista → base64url → lista. Y que un enlace roto no importe media lista.*
 */
import { describe, expect, it } from 'vitest'

import { codificaLista, decodificaLista } from './compartirLista'
import type { Linea } from '../tipos'

function linea(extra: Partial<Linea> = {}): Linea {
  return {
    id: 'l1',
    nombre_visto: 'Atún en aceite de oliva',
    cantidad: 2,
    nota: 'el grande',
    grupo_id: 18112,
    producto_id: null,
    tachado_en: null,
    ...extra,
  }
}

describe('compartir una lista por enlace', () => {
  it('la lista vuelve igual después de codificarla y decodificarla', () => {
    const codigo = codificaLista('La semana', [linea(), linea({ id: 'l2', nombre_visto: 'Arroz basmati', grupo_id: 7077 })])
    expect(codigo).toMatch(/^[A-Za-z0-9_-]+$/)
    const vuelta = decodificaLista(codigo)!
    expect(vuelta.nombre).toBe('La semana')
    expect(vuelta.lineas).toHaveLength(2)
    expect(vuelta.lineas[0].nombre).toBe('Atún en aceite de oliva')
    expect(vuelta.lineas[0].cantidad).toBe(2)
    expect(vuelta.lineas[0].nota).toBe('el grande')
    expect(vuelta.lineas[1].grupo_id).toBe(7077)
  })

  it('un enlace roto no importa nada, en vez de importar a medias', () => {
    expect(decodificaLista('no-es-base64')).toBeNull()
    expect(decodificaLista(codificaLista('', []))).toBeNull()
    const basura = btoa(JSON.stringify({ v: 9, nombre: 'x', lineas: [] }))
      .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
    expect(decodificaLista(basura)).toBeNull()
  })

  it('limita cantidades y textos para que un enlace no traiga una lista imposible', () => {
    const codigo = codificaLista('x', [linea({ cantidad: 500 })])
    const vuelta = decodificaLista(codigo)!
    expect(vuelta.lineas[0].cantidad).toBe(99)
  })
})
