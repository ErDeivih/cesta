/** *** «MIS ALIMENTOS» ABRE CON LO GUARDADO, NO EN BLANCO. *** *
 *
 *  *El fallo (P0-3):* `/calorias/alimentos` guardaba la receta y los apuntes **solo en memoria**, y
 *  al recargar se quedaban vacíos.* *Era la única pantalla de la app que perdía lo que la persona
 *  escribía.*
 *
 *  *Esto monta la pantalla de verdad con el cuaderno ya guardado en el aparato —como en una
 *  recarga— y comprueba dos cosas:* que **lo escrito está ahí**, y que **ya no se avisa de que se
 *  pierde**.
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { Cocina, CocinaProvider } from './Cocina'

function monta() {
  return render(
    <MemoryRouter>
      <CocinaProvider>
        <Cocina modo="calorias" />
      </CocinaProvider>
    </MemoryRouter>,
  )
}

describe('Mis alimentos, con el cuaderno del aparato', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('lo guardado vuelve a la pantalla al abrirla (recarga)', () => {
    // **La fecha del apunte tiene que ser HOY, no una escrita a mano.** *La pantalla filtra
    // por su día local (`hoyLocal`, la misma regla que el resto del cuaderno); con un
    // `2026-11-05` fijo, el test pasaba el 5 de noviembre y fallaba al día siguiente sin que
    // nadie hubiera tocado la pantalla. Se construye igual que en `Cocina.tsx`.*
    const d = new Date()
    const hoy = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    localStorage.setItem('cesta.cocina', JSON.stringify({
      receta: {
        version: 1,
        nombre: 'Arroz con verduras',
        raciones: 2,
        ingredientes: [{
          nombre: 'arroz', cantidad: 200, base: '100g', kcal: 354,
          proteinas: null, hidratos: null, grasas: null,
        }],
      },
      diario: [{
        id: 'a1', fecha: hoy, nombre: 'Arroz con verduras',
        raciones: 1, kcal: 320, incompleto: false,
      }],
    }))
    monta()
    expect(screen.getByText(/Receta preparada:/).textContent).toContain('Arroz con verduras')
    // *Y el apunte del día, con su cifra (sale también en el resumen de la receta).*
    expect(screen.getAllByText(/320 kcal/).length).toBeGreaterThan(0)
  })

  it('no promete nada que no cumpla: ya no dice que se pierde al recargar', () => {
    monta()
    expect(document.body.textContent).not.toMatch(/se pierde al recargar|sin sincronización/i)
    expect(screen.getByText('Se guarda en este aparato.')).toBeInTheDocument()
  })
})
