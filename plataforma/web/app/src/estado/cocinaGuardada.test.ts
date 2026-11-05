/** *** EL CUADERNO DE «MIS ALIMENTOS» TIENE QUE SOBREVIVIR A UN RECARGADO. ***
 *
 *  *`/calorias/alimentos` era el único sitio de la app que perdía lo que la persona escribía:*
 *  *todo vivía en `useState` y al recargar se quedaba vacío, sin avisar de nada.*
 *
 *  *Lo que se guarda y dónde:* en este aparato, porque **la API no tiene una ruta para el cuaderno**
 *  *(-- el diario real es `/api/diario` y es otra cosa --)*. *El test mide lo que la pantalla
 *  *necesita: lo escrito vuelve tal cual, un cuaderno de una versión anterior no revienta, y un
 *  *navegador que no deja escribir (modo privado) no tumba la pantalla.*
 */
import { beforeEach, describe, expect, it } from 'vitest'

import { CUADERNO_VACIO, guardaCuaderno, leeCuaderno } from '../estado/cocinaGuardada'

describe('el cuaderno de la pestaña se guarda en el aparato', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('lo que escribes vuelve al recargar, con sus ingredientes y sus apuntes', () => {
    const receta = {
      version: 1 as const,
      nombre: 'Arroz con verduras',
      raciones: 2,
      ingredientes: [{
        nombre: 'arroz', cantidad: 200, base: '100g' as const, kcal: 354,
        proteinas: null, hidratos: null, grasas: null,
      }],
    }
    const diario = [{
      id: 'a1', fecha: '2026-11-05', nombre: 'Arroz con verduras',
      raciones: 1, kcal: 320, incompleto: false,
    }]
    guardaCuaderno({ receta, diario })
    expect(leeCuaderno()).toEqual({ receta, diario })
  })

  it('sin nada guardado devuelve el cuaderno vacío, no un error', () => {
    expect(leeCuaderno()).toEqual(CUADERNO_VACIO)
  })

  it('un cuaderno de otra versión, o roto, no tumba la pantalla', () => {
    localStorage.setItem('cesta.cocina', '{esto no es json')
    expect(leeCuaderno()).toEqual(CUADERNO_VACIO)
    localStorage.setItem('cesta.cocina', JSON.stringify({ receta: 7, diario: 'nada' }))
    expect(leeCuaderno()).toEqual(CUADERNO_VACIO)
  })

  it('si el navegador no deja escribir, no revienta: se puede seguir usando la pestaña', () => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = () => {
      throw new Error('modo privado')
    }
    try {
      expect(() => guardaCuaderno({ receta: null, diario: [] })).not.toThrow()
    } finally {
      Storage.prototype.setItem = original
    }
  })
})
