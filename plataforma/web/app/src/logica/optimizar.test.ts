import { describe, expect, it } from 'vitest'

import { mejorCompra, type PrecioDeLinea } from './optimizar'

function precios(datos: Record<string, PrecioDeLinea[]>): Map<string, PrecioDeLinea[]> {
  return new Map(Object.entries(datos))
}

describe('la cesta en una o dos tiendas', () => {
  it('con dos tiendas que cubren todo, elige la pareja más barata y calcula el ahorro', () => {
    // *Leche y pan. En una tienda, la más barata es A (100 + 200 = 300). Repartiendo: leche en
    // B (80) y pan en A (200) = 280; ahorro 20.*
    const r = mejorCompra(['l1', 'l2'], precios({
      l1: [{ cadena: 'a', coste_cent: 100 }, { cadena: 'b', coste_cent: 80 }],
      l2: [{ cadena: 'a', coste_cent: 200 }, { cadena: 'b', coste_cent: 260 }],
    }))
    expect(r.una).toEqual({ cadena: 'a', total_cent: 300, lineas: 2 })
    expect(r.dos?.total_cent).toBe(280)
    expect(r.dos?.partes).toEqual([
      { cadena: 'a', total_cent: 200, lineas: 1 },
      { cadena: 'b', total_cent: 80, lineas: 1 },
    ])
    expect(r.ahorro_cent).toBe(20)
  })

  it('si una tienda no cubre la lista, no entra como 0 €', () => {
    // *B no tiene el pan: una compra entera en B no se propone; la pareja A+B sí, y el pan va a A.*
    const r = mejorCompra(['l1', 'l2'], precios({
      l1: [{ cadena: 'a', coste_cent: 100 }, { cadena: 'b', coste_cent: 80 }],
      l2: [{ cadena: 'a', coste_cent: 200 }],
    }))
    expect(r.una).toEqual({ cadena: 'a', total_cent: 300, lineas: 2 })
    expect(r.dos?.total_cent).toBe(280)
    expect(r.dos?.partes.find((p) => p.cadena === 'b')).toEqual({
      cadena: 'b', total_cent: 80, lineas: 1,
    })
  })

  it('si repartir no ahorra, no inventa un ahorro', () => {
    const r = mejorCompra(['l1'], precios({
      l1: [{ cadena: 'a', coste_cent: 100 }, { cadena: 'b', coste_cent: 120 }],
    }))
    expect(r.una?.total_cent).toBe(100)
    expect(r.dos?.total_cent).toBe(100)
    expect(r.ahorro_cent).toBeNull()
  })

  it('sin ninguna pareja que cubra la lista no propone nada', () => {
    const r = mejorCompra(['l1', 'l2'], precios({
      l1: [{ cadena: 'a', coste_cent: 100 }],
      l2: [{ cadena: 'b', coste_cent: 200 }],
    }))
    expect(r.una).toBeNull()
    expect(r.dos?.total_cent).toBe(300)
    expect(r.ahorro_cent).toBeNull()
  })
})
