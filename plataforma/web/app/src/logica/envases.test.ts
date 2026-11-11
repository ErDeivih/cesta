import { describe, expect, it } from 'vitest'

import { envasesPara } from './envases'

describe('envases enteros', () => {
  it('calcula el pack del ejemplo: 6 x 125 g a 2,40 EUR para 1 kg', () => {
    // *Un pack de 6 x 125 g son 0,75 kg y cuesta 2,40 EUR (3,20 EUR/kg). Para 1 kg no se compra
    // 1,33 packs: se compran 2, se pagan 4,80 EUR y sobran 0,50 kg.*
    expect(envasesPara(1, 'kg', 0.75, 'kg', 240)).toEqual({
      envases: 2, coste_cent: 480, sobra: 0.5, unidad: 'kg',
    })
  })

  it('con el pedido justo no sobra nada', () => {
    expect(envasesPara(1.5, 'kg', 0.75, 'kg', 240)).toEqual({
      envases: 2, coste_cent: 480, sobra: 0, unidad: 'kg',
    })
  })

  it('convierte gramos y kilos, y mililitros y litros', () => {
    expect(envasesPara(750, 'g', 0.125, 'kg', 100)?.envases).toBe(6)
    expect(envasesPara(0.5, 'l', 250, 'ml', 90)?.envases).toBe(2)
  })

  it('no mezcla masa con volumen ni inventa con datos que faltan', () => {
    expect(envasesPara(1, 'kg', 1, 'l', 200)).toBeNull()
    expect(envasesPara(0, 'kg', 0.75, 'kg', 240)).toBeNull()
    expect(envasesPara(1, 'kg', 0, 'kg', 240)).toBeNull()
    expect(envasesPara(1, 'docena', 0.75, 'kg', 240)).toBeNull()
  })

  it('un precio negativo no es un precio', () => {
    expect(envasesPara(1, 'ud', 1, 'ud', -1)).toBeNull()
  })
})
