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
function linea(id: string, nombre: string, cantidad = 1, extra: { minimo?: unknown } = {}) {
  return {
    id,
    nombre_visto: nombre,
    cantidad,
    grupo_id: null,
    producto_id: null,
    tachado_en: null,
    // *El minimo **solo cuando se pide**: si la clave no viene, la linea se pinta como
    // siempre, que es el caso que hay que probar.*
    ...(extra.minimo ? { minimo: extra.minimo } : {}),
  }
}

/** El minimo historico de una linea, en la forma que manda la API (`tipos.ts`). */
function minimoDe(cambios: Record<string, unknown> = {}) {
  return {
    producto_id: 'mercadona:1',
    cadena: 'mercadona',
    precio_cent: 83,
    precio_unidad_cent: 83,
    unidad: 'kg',
    minimo_cent: 83,
    minimo_fecha: '2026-10-12',
    vuelve_al_minimo: false,
    nuevo_minimo: false,
    ...cambios,
  }
}

/** Una linea resuelta en una cadena: `_serializa` de `api/cesta.py`. */
function precio(idLinea: string, nombre: string, cadena: string, coste: number, extra: {
  promo?: string | null
  sinOferta?: number
  autorizada?: boolean
  /** El contrato nuevo del reparto: precio por unidad de medida y su unidad. */
  precioUnidad?: number | null
  unidad?: string | null
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
    precio_unidad_cent: extra.precioUnidad ?? null,
    unidad: extra.unidad ?? null,
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

  it('la cifra grande de ahorro dice el importe, el porcentaje y entre que cadenas', async () => {
    monta()

    // *La tarjeta va arriba de los totales de las completas: 9,99 contra 10,70 son 0,71 €,
    // que sobre los 10,70 de la mas cara es un 7 %.*
    const titulo = await screen.findByRole('heading', { name: 'Lo que te ahorras' })
    const tarjeta = titulo.closest('section') as HTMLElement
    expect(within(tarjeta).getByText('0,71 €')).toBeInTheDocument()
    expect(within(tarjeta).getByText('−7 %')).toBeInTheDocument()
    expect(tarjeta).toHaveTextContent('Comprando en Aldi en vez de en DIA')

    // *Y va **antes** de «Total en cada cadena», que es lo que pide el encargo: primero la
    // respuesta y detras el desglose que la sostiene.*
    const totales = screen.getByRole('heading', { name: 'Total en cada cadena' })
    expect(
      titulo.compareDocumentPosition(totales) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()

    // *La letra pequeña de este caso **no** habla de equivalentes: la resta entre totales solo
    // usa lo autorizado, y decir que los incluye seria mentir en la propia nota.*
    expect(tarjeta).toHaveTextContent(
      'Con los precios de hoy. Las ofertas que piden tarjeta, cupón o comprar por internet no están restadas.',
    )
    expect(tarjeta).not.toHaveTextContent('equivalentes que aún no has confirmado')
  })

  it('un empate entre las cadenas completas no es un ahorro y no pinta la cifra', async () => {
    // *Dos completas con el mismo total: la resta es cero, y «ahorras 0,00 €» no se anuncia.*
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 129,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 129)],
        }),
        cadena({
          cadena: 'dia',
          total: 129,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'dia', 129)],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    expect(await screen.findByText(/lo más barato es/i)).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Lo que te ahorras' })).not.toBeInTheDocument()
  })

  it('con un ahorro que redondea al 0 % no se enseña el porcentaje', async () => {
    // *Un centimo sobre una cesta grande es un ahorro de verdad, pero «−0 %» diria que no hay
    // ahorro: se calla el porcentaje y se queda el importe, que es el dato que no miente.*
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 5000,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 5000)],
        }),
        cadena({
          cadena: 'dia',
          total: 5001,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'dia', 5001)],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    const titulo = await screen.findByRole('heading', { name: 'Lo que te ahorras' })
    const tarjeta = titulo.closest('section') as HTMLElement
    expect(within(tarjeta).getByText('0,01 €')).toBeInTheDocument()
    expect(tarjeta).not.toHaveTextContent('−0 %')
  })

  it('sin dos cadenas completas, suma el ahorro de comprar cada cosa donde esta mas barata', async () => {
    // *El caso real: la autorizacion de equivalentes es **una por linea**, asi que casi nunca
    // hay dos cadenas completas a la vez. Aqui solo aldi esta completa; la tarjeta suma, linea a
    // linea, lo que separa al precio mas caro del mas barato de las lineas con dos precios.*
    dobles.comparacion = comparacion({
      lineas: 4,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 1000,
          contadas: 4,
          productos: [
            precio('l1', 'Leche entera', 'aldi', 100),
            precio('l2', 'Pan de molde', 'aldi', 200),
            precio('l3', 'Yogur natural', 'aldi', 300),
            precio('l4', 'Queso curado', 'aldi', 400),
          ],
        }),
        // *Tres de las cuatro: no es completa, pero sus tres lineas si valen para el ahorro.*
        cadena({
          cadena: 'dia',
          total: 590,
          contadas: 3,
          faltan: ['Queso curado'],
          productos: [
            precio('l1', 'Leche entera', 'dia', 120),
            precio('l2', 'Pan de molde', 'dia', 220),
            precio('l3', 'Yogur natural', 'dia', 250),
          ],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Leche entera'),
        linea('l2', 'Pan de molde'),
        linea('l3', 'Yogur natural'),
        linea('l4', 'Queso curado'),
      ],
    }
    monta()

    // *De las tres lineas con dos precios: 20 + 20 + 50 = 0,90 €, sobre la suma de los maximos
    // 120 + 220 + 300 = 6,40 €, un 14 %.* *La cuarta linea (solo en aldi) **no suma**: si su
    // maximo entrara en el divisor, el porcentaje seria otro -- por eso se comprueba el 14 %.*
    const titulo = await screen.findByRole('heading', { name: 'Lo que te ahorras' })
    const tarjeta = titulo.closest('section') as HTMLElement
    expect(within(tarjeta).getByText('0,90 €')).toBeInTheDocument()
    expect(within(tarjeta).getByText('−14 %')).toBeInTheDocument()
    expect(tarjeta).toHaveTextContent(
      'Comprando cada cosa donde está más barata, frente a comprarla toda en la cadena más cara.',
    )
    // *Y el aviso de con que precios se ha hecho la cuenta, sin popups: los de hoy, incluidos
    // los equivalentes sin confirmar, y con las ofertas condicionadas sin restar.*
    expect(tarjeta).toHaveTextContent(
      'Con los precios de hoy, incluidos los equivalentes que aún no has confirmado (esos no suman en los totales de abajo). Las ofertas que piden tarjeta, cupón o comprar por internet no están restadas.',
    )
  })

  it('un precio por confirmar cuenta para el ahorro posible, pero no para los totales', async () => {
    // *La autorizacion de un equivalente es **una por linea**, asi que en uso real una linea
    // nunca tiene dos celdas autorizadas.* *El ahorro posible si cuenta ese precio -- es lo que
    // costaria hoy el equivalente --, pero los totales de abajo siguen sin sumarlo: son dos cosas
    // distintas, y la nota de la tarjeta lo dice.*
    dobles.comparacion = comparacion({
      lineas: 2,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 300,
          contadas: 2,
          productos: [
            precio('l1', 'Leche entera', 'aldi', 100),
            precio('l2', 'Pan de molde', 'aldi', 200),
          ],
        }),
        cadena({
          cadena: 'dia',
          total: 0,
          contadas: 0,
          faltan: ['Leche entera', 'Pan de molde'],
          productos: [],
          pendientes: [{ linea_id: 'l1', nombre: 'Leche entera', coste_cent: 120 }],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera'), linea('l2', 'Pan de molde')],
    }
    monta()

    // *Leche entera: 100 en aldi y 120 en DIA (por confirmar) -> 0,20 €; el maximo es 120, un 17 %.*
    const titulo = await screen.findByRole('heading', { name: 'Lo que te ahorras' })
    const tarjeta = titulo.closest('section') as HTMLElement
    expect(within(tarjeta).getByText('0,20 €')).toBeInTheDocument()
    expect(within(tarjeta).getByText('−17 %')).toBeInTheDocument()
    expect(tarjeta).toHaveTextContent(
      'incluidos los equivalentes que aún no has confirmado (esos no suman en los totales de abajo)',
    )

    // *Y el total de DIA sigue sin contar ese precio: la fila dice «sin precio» y 0 de 2.*
    const filaDia = screen.getByRole('heading', { name: 'DIA', level: 4 }).closest('li') as HTMLElement
    expect(within(filaDia).getByText('sin precio')).toBeInTheDocument()
    expect(filaDia).toHaveTextContent('con 0 de 2 productos')
  })

  it('sin ninguna linea con precio en dos cadenas no pinta tarjeta de ahorro', async () => {
    // *Una sola cadena con todo: ni dos completas ni una linea con dos precios, asi que no hay
    // ahorro que anunciar y no se pinta ni un hueco.*
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
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera'), linea('l2', 'Pan de molde')],
    }
    monta()

    expect(await screen.findByText(/lo más barato es/i)).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Lo que te ahorras' })).not.toBeInTheDocument()
  })

  it('explica de dónde sale la cifra de ahorro, sin tecnicismos', async () => {
    // *La cifra grande no se sostiene sola: el desplegable dice qué suma cada total, cómo se
    // calcula el ahorro y qué ofertas no se restan. Es lo que la hace explicable.*
    monta()
    const resumen = await screen.findByText('¿Cómo se calcula?')
    fireEvent.click(resumen)
    expect(screen.getByText(/diferencia entre sus totales/)).toBeInTheDocument()
    expect(screen.getByText(/no se resta/)).toBeInTheDocument()
    expect(screen.getByText(/€\/kg y el €\/l/)).toBeInTheDocument()
  })

  it('cada cadena lleva una barra proporcional al total mas caro', async () => {
    monta()

    // *La barra se mide contra el total mas caro (DIA, 10,70 €): DIA llega al 100 % y Aldi,
    // con 9,99 €, al 93 %. La longitud dice de un vistazo cuanto se separan.*
    const filaDia = (await screen.findByRole('heading', { name: 'DIA', level: 4 })).closest('li') as HTMLElement
    expect(filaDia.querySelector('[aria-hidden="true"] > div')).toHaveStyle({ width: '100%' })

    const filaAldi = screen.getByRole('heading', { name: 'Aldi', level: 4 }).closest('li') as HTMLElement
    expect(filaAldi.querySelector('[aria-hidden="true"] > div')).toHaveStyle({ width: '93%' })
  })

  it('al abrir la linea, cada cadena enseña su precio por unidad de medida', async () => {
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 125,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 125, { precioUnidad: 125, unidad: 'l' })],
        }),
        cadena({
          cadena: 'dia',
          total: 131,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'dia', 131, { precioUnidad: 66, unidad: 'ud' })],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    const resumen = await screen.findByText('Leche entera')
    fireEvent.click(resumen)
    const detalles = resumen.closest('details') as HTMLElement
    // *Coste y, al lado, lo que cuesta la unidad de medida de **ese** formato en **esa**
    // cadena: el litro de leche de Aldi y la unidad de DIA, cada uno con su dato.*
    const filaAldi = within(detalles).getByText('Aldi').closest('li') as HTMLElement
    expect(filaAldi).toHaveTextContent('1,25 € · 1,25 €/l')
    const filaDia = within(detalles).getByText('DIA').closest('li') as HTMLElement
    expect(filaDia).toHaveTextContent('1,31 € · 0,66 €/ud')
  })

  it('el resumen de la linea ya dice el precio por unidad, sin abrirla', async () => {
    // *«Desde 1,25 €» a secas compara importes de formatos distintos; el €/l o €/kg del
    // formato más barato va en el resumen para que la comparación sea honesta de un vistazo.*
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 125,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'aldi', 125, { precioUnidad: 125, unidad: 'l' })],
        }),
        cadena({
          cadena: 'dia',
          total: 131,
          contadas: 1,
          productos: [precio('l1', 'Leche entera', 'dia', 131, { precioUnidad: 66, unidad: 'ud' })],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera')],
    }
    monta()

    const resumen = await screen.findByText('Leche entera')
    const summary = resumen.closest('details')?.querySelector('summary') as HTMLElement
    // *El importe y el €/unidad van juntos en el resumen, pero en dos lineas: el nombre
    // largo de un producto no puede dejar el precio en una columna de una letra.*
    expect(within(summary).getByText('desde 1,25 €')).toBeInTheDocument()
    expect(within(summary).getByText('1,25 €/l')).toBeInTheDocument()
  })

  it('ordena los productos por lo que se ahorra y lo dice bajo el nombre', async () => {
    // *Antes se pintaban en el orden en que se añadieron; el producto con 0,50 € de diferencia
    // podía quedar detrás de diez que cuestan lo mismo en todas las cadenas.*
    dobles.comparacion = comparacion({
      lineas: 3,
      una_tienda: [
        cadena({ cadena: 'aldi', total: 800, contadas: 3, productos: [
          precio('l1', 'Leche entera', 'aldi', 100),
          precio('l2', 'Pan de molde', 'aldi', 500),
          precio('l3', 'Yogur natural', 'aldi', 200),
        ] }),
        cadena({ cadena: 'dia', total: 860, contadas: 3, productos: [
          precio('l1', 'Leche entera', 'dia', 110),
          precio('l2', 'Pan de molde', 'dia', 500),
          precio('l3', 'Yogur natural', 'dia', 250),
        ] }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera'), linea('l2', 'Pan de molde'), linea('l3', 'Yogur natural')],
    }
    monta()
    await screen.findByText('Yogur natural')

    const resumenes = [...document.querySelectorAll('details')]
      .map((d) => d.querySelector('summary')?.textContent ?? '')
      .filter((t) => /Leche entera|Pan de molde|Yogur natural/.test(t))
    expect(resumenes.map((t) => t.includes('Yogur') ? 'yogur' : t.includes('Leche') ? 'leche' : 'pan'))
      .toEqual(['yogur', 'leche', 'pan'])
    // *Y el motivo del orden, en la línea: 0,50 € de diferencia en el yogur y 0,10 € en la leche.*
    expect(resumenes[0]).toMatch(/hasta 0,50\s*€ de diferencia/)
    expect(resumenes[1]).toMatch(/hasta 0,10\s*€ de diferencia/)
    expect(resumenes[2]).not.toContain('de diferencia')
  })

  it('sin detalle y con todos los totales a cero, lo dice como estado vacío', async () => {
    dobles.comparacion = comparacion({
      lineas: 2,
      una_tienda: [
        cadena({ cadena: 'aldi', total: 0, contadas: 0, productos: [] }),
        cadena({ cadena: 'dia', total: 0, contadas: 0, productos: [] }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Leche entera'), linea('l2', 'Pan de molde')],
    }
    monta()

    expect(await screen.findByText(/todavía no hay precios de esta lista/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /volver a la lista/i })).toBeInTheDocument()
  })

  it('sin precio por unidad en el reparto, la fila enseña solo el coste', async () => {
    // *Dos formas de que el dato no se pueda enseñar: que no venga ninguno de los dos campos
    // (una API vieja) o que llegue el precio sin la unidad. En las dos, el coste de siempre.*
    dobles.comparacion = comparacion({
      lineas: 1,
      una_tienda: [
        cadena({
          cadena: 'aldi',
          total: 600,
          contadas: 1,
          productos: [precio('l1', 'Queso curado', 'aldi', 600, { precioUnidad: 600, unidad: null })],
        }),
        cadena({
          cadena: 'dia',
          total: 640,
          contadas: 1,
          productos: [precio('l1', 'Queso curado', 'dia', 640)],
        }),
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Queso curado')],
    }
    monta()

    const resumen = await screen.findByText('Queso curado')
    const detalles = resumen.closest('details') as HTMLElement
    // *Si el contrato nuevo no llega, no se inventa un €/unidad: queda el coste de siempre.*
    expect(within(detalles).queryByText(/€\/l|€\/kg|€\/ud/)).not.toBeInTheDocument()
    expect(within(detalles).getByText('6,00 €')).toBeInTheDocument()
    expect(within(detalles).getByText('6,40 €')).toBeInTheDocument()
  })

  it('una linea con minimo nuevo lleva su pastilla en el resumen', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        // *Las dos banderas a la vez: un minimo nuevo tambien esta «en su minimo», y se enseña
        // solo la fuerte para no repetir la misma noticia con dos pastillas.*
        linea('l1', 'Leche entera', 2, {
          minimo: minimoDe({ nuevo_minimo: true, vuelve_al_minimo: true, minimo_cent: 79 }),
        }),
        linea('l2', 'Pan de molde'),
        linea('l3', 'Yogur natural'),
        linea('l4', 'Queso curado'),
      ],
    }
    monta()

    const fila = (await screen.findByText('Leche entera')).closest('li') as HTMLElement
    expect(within(fila).getByText('Mínimo nuevo · 0,79 €')).toBeInTheDocument()
    // *La fuerte manda: no se dicen las dos, que seria la misma noticia dos veces.*
    expect(within(fila).queryByText(/En su mínimo/)).not.toBeInTheDocument()
  })

  it('una linea que vuelve a su minimo lleva la otra pastilla', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Leche entera', 2, { minimo: minimoDe({ vuelve_al_minimo: true, minimo_cent: 83 }) }),
        linea('l2', 'Pan de molde'),
        linea('l3', 'Yogur natural'),
        linea('l4', 'Queso curado'),
      ],
    }
    monta()

    const fila = (await screen.findByText('Leche entera')).closest('li') as HTMLElement
    expect(within(fila).getByText('En su mínimo · 0,83 €')).toBeInTheDocument()
    expect(within(fila).queryByText(/Mínimo nuevo/)).not.toBeInTheDocument()
  })

  it('sin minimo en la linea no pinta ninguna pastilla', async () => {
    monta()

    const fila = (await screen.findByText('Pan de molde')).closest('li') as HTMLElement
    expect(within(fila).queryByText(/Mínimo nuevo|En su mínimo/)).not.toBeInTheDocument()
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
