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
 *
 *  *** Y desde el 5/11/2026 la prueba mide tambien las respuestas de la ficha rehecha: ***
 *  el chip de «está caro / está bien», la ventana real del historico (nunca «90 días»), el estado
 *  sin serie, el 404 y el «no hay precio por kilo». *Son las cosas que la ficha **afirma**, y una
 *  afirmacion sin prueba es una promesa.*
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { ErrorApi } from '../api/cliente'

const REAL = JSON.parse(readFileSync('src/pruebas/fixtures/producto-147509.json', 'utf-8')) as {
  producto: Record<string, unknown>
  grupo: Record<string, unknown>
}

type Punto = { producto_id: string; fuente: string; fecha: string; precio_unidad_cent: number | null; unidad_canon: string }

/** *** Se controla la consulta desde fuera: pendiente, con dato, o con error. *** *
 *
 *  *Y `serie` y `producto` permiten cambiar **una parte** de la respuesta real sin inventarse la
 *  ficha entera: es la misma respuesta capturada, con el historico o el precio por unidad que pide
 *  cada caso.*
 */
const estado = vi.hoisted(() => ({
  modo: 'pendiente' as 'pendiente' | 'dato' | 'error',
  serie: null as unknown,
  producto: null as unknown,
  grupo: undefined as unknown,
  error: null as unknown,
}))

vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useProducto: () => {
      if (estado.modo === 'pendiente') return { isPending: true, isError: false, data: undefined }
      if (estado.modo === 'error')
        return {
          isPending: false,
          isError: true,
          error: estado.error ?? new Error('la API no contesta'),
          data: undefined,
        }
      return {
        isPending: false,
        isError: false,
        error: null,
        data: {
          ...REAL,
          producto: { ...REAL.producto, ...(estado.producto as object | null) },
          grupo:
            estado.grupo !== undefined
              ? estado.grupo
              : { ...REAL.grupo, serie: estado.serie ?? REAL.grupo.serie },
        },
      }
    },
    misListas: async () => [],
  }
})

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return { ...real, misListas: async () => [], yo: async () => ({ usuario: null }) }
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

/** La serie del azafran de DIA en tres dias: **plana y luego arriba**, que es el caso del chip. */
const SERIE_CARO: Punto[] = [
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-03', precio_unidad_cent: 600000, unidad_canon: 'kg' },
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-04', precio_unidad_cent: 600000, unidad_canon: 'kg' },
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-05', precio_unidad_cent: 687500, unidad_canon: 'kg' },
]

/** La misma serie al reves: **el precio de hoy es el mas bajo**. */
const SERIE_BARATO: Punto[] = [
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-03', precio_unidad_cent: 687500, unidad_canon: 'kg' },
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-04', precio_unidad_cent: 687500, unidad_canon: 'kg' },
  { producto_id: 'dia:147509', fuente: 'dia', fecha: '2026-11-05', precio_unidad_cent: 600000, unidad_canon: 'kg' },
]

describe('Producto, montado con la respuesta real de la API', () => {
  beforeEach(() => {
    estado.modo = 'pendiente'
    estado.serie = null
    estado.producto = null
    estado.grupo = undefined
    estado.error = null
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

  it('*** el chip contesta «¿está caro?» con la serie y con la ventana que hay ***', () => {
    // **Es la respuesta que se viene a buscar**, y lleva su motivo: no basta con un color.
    estado.modo = 'dato'
    estado.serie = SERIE_CARO
    monta()
    expect(screen.getByText(/está caro/i)).toBeInTheDocument()
    expect(screen.getByText(/el máximo de los últimos 3 días/)).toBeInTheDocument()
    // *** Y NUNCA «90 días»: *** *la serie que tenemos es la que es.*
    expect(screen.queryByText(/90 d[ií]as/i)).not.toBeInTheDocument()
  })

  it('*** con el precio más bajo de la serie el chip dice «está bien» ***', () => {
    estado.modo = 'dato'
    estado.serie = SERIE_BARATO
    monta()
    expect(screen.getByText(/está bien/i)).toBeInTheDocument()
    expect(screen.getByText(/el mínimo de los últimos 3 días/)).toBeInTheDocument()
  })

  it('*** el histórico cuenta los días con precio, no los de la promesa ***', () => {
    estado.modo = 'dato'
    estado.serie = SERIE_CARO
    monta()
    // *La tarjeta dice cuántos días hay de verdad, y el gráfico se anuncia con su nombre.*
    expect(screen.getByText(/3 días · €\/kg/)).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /precio por día/i })).toBeInTheDocument()
  })

  it('*** sin serie no se dibuja una línea falsa: se dice que no hay histórico ***', () => {
    estado.modo = 'dato'
    estado.serie = []
    monta()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByText(/todavía no hay historial/i)).toBeInTheDocument()
    expect(screen.queryByText(/está caro|está bien/i)).not.toBeInTheDocument()
  })

  it('*** con un solo día no se dice si está caro o barato ***', () => {
    // *Un solo punto es un punto, no una racha: «el máximo de un día» no es una respuesta.* *Y el
    // gráfico sí lo pinta (un punto), porque el dato existe.*
    estado.modo = 'dato'
    estado.serie = [SERIE_CARO[0]]
    monta()
    expect(screen.getByText(/solo tenemos un día/i)).toBeInTheDocument()
    expect(screen.queryByText(/está caro|está bien/i)).not.toBeInTheDocument()
  })

  it('*** si no hay precio por unidad, se dice, y no se inventa ***', () => {
    estado.modo = 'dato'
    estado.producto = { precio_unidad_cent: null }
    monta()
    expect(screen.getByText(/no hay precio por kilo/i)).toBeInTheDocument()
  })

  it('con el mismo EAN y otra base lo DICE, y el otro articulo va aparte', () => {
    estado.modo = 'dato'
    monta()
    // *La regresion del propietario: si alguien vuelve a usar `producto` sin resolver la
    // identidad, Carrefour deja de reconocerse y esta linea falla.*
    //
    // **Y los dos titulos cambiaron el 5/11/2026 al rehacer la ficha**, porque «precio no
    // comparable» y «del grupo» son palabras de la base de datos, no de quien compra. Lo que se
    // mide sigue siendo lo mismo: el mismo artículo con otra base va por un lado y lo dice, y el
    // artículo distinto va por otro.
    expect(screen.getByText(/Mismo artículo, otra forma de medirlo/i)).toBeInTheDocument()
    expect(screen.getByText(/Otras opciones/i)).toBeInTheDocument()
    // *La frase enganosa del 41 % no se pinta.*
    expect(screen.queryByText(/Cuesta un \d+ % m.s que en/)).not.toBeInTheDocument()
  })

  it('*** dice por qué dos precios no se pueden restar, en lenguaje de usuario ***', () => {
    estado.modo = 'dato'
    monta()
    expect(screen.getByText(/se mide de otra forma/i)).toBeInTheDocument()
    expect(screen.getByText(/no se restan/i)).toBeInTheDocument()
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

  it('*** sin grupo no se inventa historial ni alternativas ***', () => {
    // *32.486 de los 51.781 productos no tienen grupo: el producto existe y se enseña, y lo que no
    // hay es con qué compararlo. Se dice en una línea, sin una tarjeta de histórico vacía ni una
    // lista de cadenas que no existe.*
    estado.modo = 'dato'
    estado.grupo = null
    monta()
    expect(screen.getByText(/sin historial/i)).toBeInTheDocument()
    expect(screen.getByText(/no hay otros productos parecidos/i)).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('si la API falla, se dice, no se queda en blanco', () => {
    estado.modo = 'error'
    monta()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('*** un 404 no es un fallo rojo: es que no tengo ese producto ***', () => {
    estado.modo = 'error'
    estado.error = new ErrorApi(404, null)
    monta()
    expect(screen.getByText(/no tengo ese producto/i)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
