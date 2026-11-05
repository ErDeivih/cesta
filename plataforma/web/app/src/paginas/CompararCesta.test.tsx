/** *** COMPARAR MI CESTA: LA PANTALLA, SUS CUATRO ESTADOS Y LA PUERTA DESDE LA LISTA. *** *
 *
 *  *Lo que mide esto, y por que hacia falta:* la casilla pide **total por cadena y donde
 *  conviene**, y el peligro concreto de esa pantalla es **coronar a la cadena equivocada**: una
 *  cadena a la que le faltan productos suma menos y sale «la mas barata» sin serlo.* *Eso no da
 *  error de compilacion ni se nota al mirar el codigo: hay que montar la pantalla con datos que
 *  tengan ese vicio y leer lo que dice.*
 *
 *  Se monta con `yo()` contestando segun el caso (hay sesion / no hay nadie) y con el reparto y la
 *  lista de verdad en la forma en que los manda la API (`api/cesta.py`): lo unico inventado es el
 *  contenido de los datos, no su forma.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/* ------------------------------------------------------------- los dobles --- */

const dobles = vi.hoisted(() => ({
  sesion: { usuario: { id: 'u1', usuario: 'ana', nombre: 'Ana' }, preferencias: {} } as unknown,
  listas: [] as unknown[],
  detalle: null as unknown,
  comparacion: null as unknown,
  fallo: null as unknown,
  reparto: null as unknown as { llamadas: number },
}))

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    yo: async () => dobles.sesion,
    misListas: async () => dobles.listas,
    verLista: async () => dobles.detalle,
    reparto: async () => {
      dobles.reparto.llamadas += 1
      if (dobles.fallo) throw dobles.fallo
      return dobles.comparacion
    },
  }
})

const porKilo = vi.hoisted(() => ({ llamadas: 0 }))

vi.mock('../api/consultas', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    useProducto: () => {
      porKilo.llamadas += 1
      return {
        isLoading: false,
        isError: false,
        data: {
          fecha_datos: '2026-11-05',
          producto: {
            producto_id: 'mercadona:1',
            fuente: 'mercadona',
            id_fuente: '1',
            nombre: 'Leche entera',
            unidad: 'l',
            precio_cent: 129,
            precio_unidad_cent: 129,
            comparable: true,
          },
          grupo: null,
        },
      }
    },
  }
})

import { CompararCesta } from './CompararCesta'
import { Cesta } from './Cesta'
import { tituloDe } from '../App'

/* ------------------------------------------------------------ los datos --- */

/** Una linea de la lista, como la manda `GET /listas/{id}`. */
function linea(id: string, nombre: string, cantidad = 1) {
  return {
    id,
    nombre_visto: nombre,
    cantidad,
    grupo_id: null,
    producto_id: null,
    tachado_en: null,
  }
}

/** Una linea resuelta en una cadena: `_serializa` de `api/cesta.py`. */
function precio(idLinea: string, nombre: string, cadena: string, coste: number, extra: {
  promo?: string | null
  sinOferta?: number
  autorizada?: boolean
} = {}) {
  return {
    producto_id: `${cadena}:${idLinea}`,
    nombre,
    cadena,
    unidades: 1,
    coste_cent: coste,
    coste_sin_oferta_cent: extra.sinOferta ?? coste,
    promo: extra.promo ?? null,
    sugerencia: null,
    linea_id: idLinea,
    autorizada: extra.autorizada !== false,
    identidad: 'exacto',
    motivo: null,
  }
}

/** Una cadena de `una_tienda`, con los campos que el reparto manda de verdad. */
function cadena(datos: {
  cadena: string
  total: number
  contadas: number
  faltan?: string[]
  productos: unknown[]
  pendientes?: unknown[]
}) {
  return {
    cadena: datos.cadena,
    total_cent: datos.total,
    total_sin_ofertas_cent: datos.total,
    encontrados: datos.productos.length,
    faltan: datos.faltan ?? [],
    contadas: datos.contadas,
    sin_autorizar: datos.pendientes?.length ?? 0,
    pendientes: datos.pendientes ?? [],
    productos: datos.productos,
  }
}

function comparacion(datos: { lineas: number; una_tienda: unknown[] }) {
  return {
    sublistas: [],
    sin_asignar: [],
    sin_encontrar: [],
    total_cent: 0,
    total_sin_ofertas_cent: 0,
    ahorro_cent: 0,
    lineas: datos.lineas,
    decididas: 0,
    sin_precio: 0,
    una_tienda: datos.una_tienda,
    repartido: null,
    fecha_datos: '2026-11-05',
  }
}

/** Cuatro productos, dos cadenas completas y una tercera mas barata **a la que le falta uno**. */
function juegoCompleto() {
  const productos = {
    aldi: [
      precio('l1', 'Leche entera', 'aldi', 129),
      precio('l2', 'Pan de molde', 'aldi', 180),
      precio('l3', 'Yogur natural', 'aldi', 90),
      precio('l4', 'Queso curado', 'aldi', 600),
    ],
    dia: [
      precio('l1', 'Leche entera', 'dia', 135),
      precio('l2', 'Pan de molde', 'dia', 190),
      precio('l3', 'Yogur natural', 'dia', 105),
      precio('l4', 'Queso curado', 'dia', 640),
    ],
    // *La trampa: es la de menor total y le falta el queso.*
    mercadona: [
      precio('l1', 'Leche entera', 'mercadona', 119, { promo: '2ª unidad al 50 %', sinOferta: 129 }),
      precio('l2', 'Pan de molde', 'mercadona', 175),
      precio('l3', 'Yogur natural', 'mercadona', 85),
    ],
    carrefour: [precio('l1', 'Leche entera', 'carrefour', 129)],
  }
  return comparacion({
    lineas: 4,
    una_tienda: [
      cadena({ cadena: 'mercadona', total: 379, contadas: 3, faltan: ['Queso curado'], productos: productos.mercadona }),
      cadena({ cadena: 'aldi', total: 999, contadas: 4, productos: productos.aldi }),
      cadena({ cadena: 'dia', total: 1070, contadas: 4, productos: productos.dia }),
      cadena({ cadena: 'carrefour', total: 129, contadas: 1, faltan: ['Pan de molde', 'Yogur natural', 'Queso curado'], productos: productos.carrefour }),
    ],
  })
}

/** Las dos pantallas de verdad, para que el enlace de la lista se pueda **pulsar**. */
function monta(ruta = '/compra/listas/L1/comparar') {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path="/compra/listas/:listaId/comparar" element={<CompararCesta />} />
          <Route path="/compra/listas/:listaId" element={<Cesta />} />
          <Route path="/compra/listas" element={<Cesta />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Lo que no puede leerse en una pantalla de consumo (§8 y la auditoria). */
const TECNICO = /401|403|500|\bAPI\b|servidor|endpoint|\bgold\b|parquet|docker|repositorio|reparto\b/i

beforeEach(() => {
  localStorage.clear()
  dobles.sesion = { usuario: { id: 'u1', usuario: 'ana', nombre: 'Ana' }, preferencias: {} }
  dobles.listas = [{ id: 'L1', nombre: 'La de casa', es_de_casa: true, lineas: 4 }]
  dobles.detalle = {
    papel: 'dueno',
    lineas: [
      linea('l1', 'Leche entera', 2),
      linea('l2', 'Pan de molde'),
      linea('l3', 'Yogur natural'),
      linea('l4', 'Queso curado'),
    ],
    estimacion: { total_cent: 0, en_carrito_cent: 0, por_recoger_cent: 0, lineas: 4, sin_precio: 0 },
    personas: [],
    fecha_datos: '2026-11-05',
  }
  dobles.comparacion = juegoCompleto()
  dobles.fallo = null
  dobles.reparto = { llamadas: 0 }
  porKilo.llamadas = 0
})

/* -------------------------------------------------------------- la puerta --- */

describe('la puerta de la lista lleva a comparar', () => {
  it('la cesta ofrece «Comparar mi cesta» y lleva a la pantalla nueva', async () => {
    dobles.comparacion = comparacion({
      lineas: 2,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 300,
          contadas: 2,
          productos: [precio('l1', 'Leche entera', 'aldi', 129), precio('l2', 'Pan de molde', 'aldi', 171)],
        }),
      ],
    })
    monta('/compra/listas/L1')

    expect(await screen.findByText('Dónde sale mejor tu cesta')).toBeInTheDocument()
    // *El enlace tiene que apuntar a la ruta de verdad, no a la lista: si apuntara a la lista,
    // pulsarlo no haria nada y la casilla seguiria sin puerta.*
    const enlace = screen.getByRole('link', { name: 'Comparar mi cesta' })
    expect(enlace).toHaveAttribute('href', '/compra/listas/L1/comparar')
    fireEvent.click(enlace)
    expect(await screen.findByRole('heading', { name: 'Comparar mi cesta' })).toBeInTheDocument()
  })
})

/* --------------------------------------------------------------- la pestaña --- */

describe('la pestaña dice cuál es cuál', () => {
  it('comparar la cesta tiene su título, y la lista sigue teniendo el suyo', () => {
    // *Con dos pestañas abiertas -- la lista y su comparación -- las dos no pueden llamarse
    // «La cesta»: es el motivo por el que el mapa de títulos vive en `App.tituloDe`.*
    expect(tituloDe('/compra/listas/L1/comparar')).toBe('Comparar la cesta')
    expect(tituloDe('/compra/listas/L1')).toBe('La cesta')
    expect(tituloDe('/compra/listas')).toBe('La cesta')
  })
})

/* --------------------------------------------------------------- la pantalla --- */

describe('comparar mi cesta con datos', () => {
  it('dice que lista compara y cuantos productos se pueden comparar', async () => {
    monta()

    expect(await screen.findByRole('heading', { name: 'Comparar mi cesta', level: 2 })).toBeInTheDocument()
    expect(screen.getByText('La de casa')).toBeInTheDocument()
    // *Los productos de la lista, y cuantos de ellos entran en la comparacion.*
    expect(screen.getAllByText(/4 productos/).length).toBeGreaterThan(0)
    // *Tres productos estan en dos cadenas o mas; el yogur tambien. Ninguno se queda sin precio.*
    expect(screen.getByText(/4 se pueden comparar entre cadenas/)).toBeInTheDocument()
  })

  it('no corona a la cadena mas barata si le faltan productos', async () => {
    monta()

    // *La mas barata en bruto es mercadona (379), pero le falta el queso: no puede ganar.*
    const ganadora = await screen.findByText(/lo más barato es/i)
    expect(ganadora).toHaveTextContent('Aldi')
    expect(ganadora).toHaveTextContent('9,99 €')

    // *Y lo que le falta se dice con el nombre del producto, no con un numero.*
    expect(screen.getByText('No lo tiene: Queso curado')).toBeInTheDocument()
    expect(screen.getByText('con 3 de 4 productos')).toBeInTheDocument()
    expect(screen.getByText('la más barata')).toBeInTheDocument()
  })

  it('da la diferencia con la cadena mas cara que tiene la lista entera', async () => {
    monta()

    // *9,99 contra 10,70: la mas cara de las completas sale 0,71 mas.*
    const frase = await screen.findByText(/La más cara de las que también lo tienen todo/i)
    expect(frase).toHaveTextContent('DIA')
    expect(frase).toHaveTextContent('0,71 €')

    // *Y en la fila de DIA, que es la otra completa, se ve lo que cuesta de mas. En la de
    // mercadona no: su total es de 3 de 4, y restarlo seria comparar dos cosas distintas.*
    expect(screen.getByText('0,71 € más que la más barata')).toBeInTheDocument()
    const filaMercadona = screen
      .getByRole('heading', { name: 'Mercadona', level: 4 })
      .closest('li') as HTMLElement
    expect(filaMercadona.textContent).not.toMatch('más que la más barata')
  })

  it('una linea que solo esta en una cadena no se presenta como comparacion', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 129,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 129)],
        }),
      ],
    })
    monta()

    expect(await screen.findByText('1,29 € · solo en Aldi')).toBeInTheDocument()
  })

  it('enseña el precio de cada cadena y «no está» donde falta', async () => {
    monta()

    // *El desglose por linea: se abre el queso, que es al que le falta una cadena.*
    const resumen = await screen.findByText('Queso curado')
    const detalles = resumen.closest('details')
    expect(detalles).not.toBeNull()
    fireEvent.click(resumen)

    const dentro = within(detalles as HTMLElement)
    expect(await dentro.findByText('Mercadona')).toBeInTheDocument()
    expect(dentro.getAllByText('no está').length).toBeGreaterThan(0)
  })

  it('enseña la oferta como condicion y no como precio final', async () => {
    monta()

    const resumen = await screen.findByText('Leche entera')
    fireEvent.click(resumen)

    // *La del 2x1 con dos unidades: el numero dice que ya esta aplicada, y se dice cuanto baja.*
    expect(await screen.findByText(/Oferta: «2ª unidad al 50 %»/)).toBeInTheDocument()
    expect(screen.getByText(/Ya va aplicada: 0,10 € menos/)).toBeInTheDocument()
  })

  it('avisa de que una oferta de club no baja lo que se paga', async () => {
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'dia',
          total: 135,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'dia', 135, { promo: 'Club DIA 15 % dto en tu tarjeta' })],
        }),
        cadena({
          cadena: 'aldi',
          total: 129,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 129)],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    fireEvent.click(await screen.findByText('Leche entera'))
    expect(
      await screen.findByText('Solo con tarjeta o cupón del club: no baja lo que pagas en caja.'),
    ).toBeInTheDocument()
  })

  it('pide el precio por kilo al abrir la linea, no antes', async () => {
    monta()

    const resumen = await screen.findByText('Leche entera')
    expect(porKilo.llamadas).toBe(0)
    fireEvent.click(resumen)
    // *Y cuando llega, se enseña con su unidad: «1,29 €/l».*
    await waitFor(() => expect(porKilo.llamadas).toBeGreaterThan(0))
    expect(await screen.findByText(/1,29 €\/l en Mercadona/)).toBeInTheDocument()
  })

  it('si el detalle por producto no llega, enseña los totales y no afirma nada linea a linea', async () => {
    // *Un dato que no esta no se convierte en un cero: sin el detalle por linea, la tabla
    // estaria vacia y se leeria «no se puede comparar nada», que es falso.*
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        {
          cadena: 'aldi',
          total_cent: 129,
          total_sin_ofertas_cent: 129,
          encontrados: 1,
          faltan: [],
          contadas: 1,
          sin_autorizar: 0,
        },
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    expect(await screen.findByText(/lo más barato es/i)).toBeInTheDocument()
    expect(screen.queryByText('Producto a producto')).not.toBeInTheDocument()
    expect(screen.queryByText(/se pueden comparar entre cadenas/)).not.toBeInTheDocument()
    expect(screen.queryByText('no comparable')).not.toBeInTheDocument()
  })

  it('no dice nada tecnico ni de relleno', async () => {
    monta()
    await screen.findByRole('heading', { name: 'Comparar mi cesta' })
    expect(document.body.textContent ?? '').not.toMatch(TECNICO)
  })
})

/* --------------------------------------------------------------- los otros estados --- */

describe('los estados que no son «con datos»', () => {
  it('sin sesion enseña la puerta y no un error', async () => {
    dobles.sesion = { usuario: null, preferencias: {} }
    monta()

    expect(await screen.findByText('Entra para ver esto')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    const enlaces = screen.getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(enlaces).toContain('/cesta')
  })

  it('una lista sin lineas lo dice y lleva a la lista', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [],
    }
    dobles.comparacion = comparacion({ lineas: 0, una_tienda: [] })
    monta()

    expect(await screen.findByText('Esta lista no tiene nada que comparar')).toBeInTheDocument()
    const enlaces = screen.getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(enlaces).toContain('/compra/listas/L1')
  })

  it('si nada de la lista se puede comparar, lo dice', async () => {
    dobles.comparacion = comparacion({ lineas: 2, una_tienda: [] })
    monta()

    expect(await screen.findByText('Hoy no puedo comparar esta lista')).toBeInTheDocument()
  })

  it('con todas las cadenas incompletas no corona a ninguna y lo explica', async () => {
    dobles.comparacion = comparacion({
      lineas: 2,
      una_tienda: [
        cadena({ cadena: 'aldi', total: 200, contadas: 1, faltan: ['Pan de molde'], productos: [precio('l1', 'Leche entera', 'aldi', 200)] }),
        cadena({ cadena: 'dia', total: 210, contadas: 1, faltan: ['Pan de molde'], productos: [precio('l1', 'Leche entera', 'dia', 210)] }),
      ],
    })
    monta()

    expect(await screen.findByText(/Ninguna cadena tiene los 2 productos/)).toBeInTheDocument()
    expect(screen.queryByText('la más barata')).not.toBeInTheDocument()
  })

  it('un fallo trae reintento y el reintento vuelve a pedirlo', async () => {
    dobles.fallo = new Error('se ha roto')
    monta()

    expect(await screen.findByRole('alert')).toHaveTextContent('No he podido traer esto')
    const antes = dobles.reparto.llamadas
    fireEvent.click(screen.getByRole('button', { name: 'Volver a intentarlo' }))
    await waitFor(() => expect(dobles.reparto.llamadas).toBeGreaterThan(antes))
  })
})
