/** *** LA PRUEBA QUE HABRIA CAZADO EL BLANCO DEL 18/10/2026. ***
 *
 *  *`Producto` se montaba, esperaba, recibia el dato… y el arbol se quedaba **vacio**.* *No habia
 *  ninguna prueba que montara el componente: las del repo eran de funciones, y una funcion no tiene
 *  orden de hooks.*
 *
 *  *** Y LOS DATOS SON LOS DE VERDAD, CAPTURADOS DE `/api/producto/dia/147509` ***:*
 *  `src/pruebas/fixtures/producto-147509.json`, con las **13 claves** del objeto `producto` y las
 *  **55** de cada entrada del grupo.* *Escribirlos a mano fue un error de esta misma prueba: se me
 *  olvidaban campos, y el componente reventaba en un `.map` de un campo que mi fixture no tenia --
 *  **y eso no era un fallo del componente, era que mi dato no era el dato**.*
 *
 *  *La primera consecuencia, y es la que importa:* **`producto` NO trae `ean`** (13 claves, ninguna
 *  es esa) y **el grupo si**. *Asi que leer la identidad de `producto` rechaza **todo**, incluidas las
 *  coincidencias exactas.*
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const REAL = JSON.parse(readFileSync('src/pruebas/fixtures/producto-147509.json', 'utf-8')) as {
  producto: Record<string, unknown>
  grupo: Record<string, unknown>
}

// *** Se controla la consulta desde fuera: pendiente, con dato, o con error. ***
const estado = vi.hoisted(() => ({ modo: 'pendiente' as 'pendiente' | 'dato' | 'error' }))

vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useProducto: () => {
      if (estado.modo === 'pendiente') return { isPending: true, isError: false, data: undefined }
      if (estado.modo === 'error')
        return { isPending: false, isError: true, error: new Error('la API no contesta'), data: undefined }
      return { isPending: false, isError: false, data: REAL, error: null }
    },
    misListas: async () => [],
  }
})

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, misListas: async () => [] }
})

import { Producto } from './Producto'

function monta() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/compra/productos/dia/147509']}>
        <Routes>
          <Route path="/compra/productos/:fuente/:idFuente" element={<Producto />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Producto, montado con la respuesta real de la API', () => {
  beforeEach(() => {
    estado.modo = 'pendiente'
  })

  it('el fixture conserva la forma real: producto sin ean, grupo con ean', () => {
    expect(Object.keys(REAL.producto)).toHaveLength(13)
    expect('ean' in REAL.producto).toBe(false)
    const grupo = REAL.grupo as { productos: Record<string, unknown>[] }
    expect('ean' in grupo.productos[0]).toBe(true)
  })

  it('mientras carga hay esqueleto, y NO hay ficha', () => {
    estado.modo = 'pendiente'
    monta()
    expect(screen.queryByText(/Azafr.n en hebras Pote/)).not.toBeInTheDocument()
  })

  it('cuando llega el dato, la ficha se pinta (esta es la del 18)', () => {
    estado.modo = 'dato'
    monta()
    expect(screen.getAllByText(/Azafr.n en hebras Pote 0,4 g/).length).toBeGreaterThan(0)
    // *La cantidad pequeña se lee: 0,4 g, nunca «0 kg».*
    expect(screen.queryByText(/^0 kg$/)).not.toBeInTheDocument()
    expect(screen.getAllByText(/0,4 g/).length).toBeGreaterThan(0)
  })

  it('con el mismo EAN y otra base lo DICE, y el otro articulo va aparte', () => {
    estado.modo = 'dato'
    monta()
    // *La regresion del propietario: si alguien vuelve a usar `producto` sin resolver la
    // identidad, Carrefour deja de reconocerse y esta linea falla.*
    expect(screen.getByText(/Mismo articulo, precio no comparable/i)).toBeInTheDocument()
    expect(screen.getByText(/Otras opciones del grupo/i)).toBeInTheDocument()
    // *La frase enganosa del 41 % no se pinta.*
    expect(screen.queryByText(/Cuesta un \d+ % m.s que en/)).not.toBeInTheDocument()
  })

  it('no enseña la auditoría del emparejador ni habla de EAN', () => {
    // **§8 y P0-4.** *La ficha tenía una tarjeta «Por qué está emparejado con esos» que pintaba
    // los campos y el JSON del emparejador; y la frase de la horquilla hablaba de «otro EAN».*
    // *Ni lo uno ni lo otro le sirve a quien está decidiendo una compra, y el panel del
    // emparejador es una herramienta de ingeniería de `PanelMatching`.*
    estado.modo = 'dato'
    monta()
    expect(screen.queryByText(/Por qué está emparejado/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/EAN/)).not.toBeInTheDocument()
  })

  it('si la API falla, se dice, no se queda en blanco', () => {
    estado.modo = 'error'
    monta()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
