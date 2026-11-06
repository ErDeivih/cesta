/** *** LA LISTA DE LA COMPRA, TAL Y COMO LA MANDA EL ARTBOARD. *** *
 *
 *  *El artboard aprobado (`designs/cesta-app/project/Lista.dc.html`, 390 x 844) manda la
 *  jerarquia de esta pantalla:* **cabecera con volver y opciones**, **tarjeta del precio
 *  estimado sobre bosque**, **filas con casilla, nombre y precio por linea**, **«Añadir
 *  producto»** y **«Comparar mi cesta»**. Lo que se mide aqui es esa jerarquia y, sobre todo,
 *  **de donde sale cada cifra**:
 *
 *   - el total es el de la estimacion que manda la API (`estimacion.total_cent`), no una suma
 *     hecha en la pantalla;
 *   - el precio de una linea **solo se pinta si la API lo sabe**. La lista (`GET /listas/{id}`)
 *     no trae precio por linea: el unico sitio de donde sale el coste de una linea es el
 *     reparto (`GET /listas/{id}/reparto`), y por eso se comprueba que con reparto se ve y sin
 *     el **no se inventa**;
 *   - la cadena del total se dice **solo cuando se sabe** (todo decidido en una);
 *   - y si no hay precio de nada, se dice, en vez de un «0,00 €» que se lee como gratis.
 *
 *  *Los datos son de mentira; su forma es la de la API de verdad* (`api/cesta.py`: `estimacion`,
 *  `reparto_por_tienda`, `PendienteDeDecidir`, `FilaEnTienda`).
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
  reparto: null as unknown,
  fallo: null as unknown,
  llamadas: { detalle: 0, reparto: 0 },
}))

vi.mock('../api/cesta', async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>()
  return {
    ...real,
    yo: async () => dobles.sesion,
    misListas: async () => dobles.listas,
    verLista: async () => {
      dobles.llamadas.detalle += 1
      if (dobles.fallo) throw dobles.fallo
      return dobles.detalle
    },
    reparto: async () => {
      dobles.llamadas.reparto += 1
      if (dobles.fallo) throw dobles.fallo
      return dobles.reparto
    },
    // *Nada de red en una prueba: los cambios no se pulsan, pero la mutacion se construye.*
    cambiarLinea: async () => ({}),
    anadirLinea: async () => ({}),
    salir: async () => undefined,
  }
})

// *La cuadricula de lo usual tiene su propia pantalla y sus propias pruebas: aqui solo
// estorba (pinta seis tarjetas que no son de esta medida). Lo que si se mide aqui es **lo que
// la pantalla le manda**: que grupos ya estan en la lista y si es una lista donde se rellena.*
vi.mock('../componentes/Mosaico', () => ({
  Mosaico: (props: { enUnaLista?: boolean; enLaLista?: number[] }) => (
    <div
      data-testid="mosaico"
      data-enunalista={String(props.enUnaLista ?? false)}
      data-enlalista={JSON.stringify(props.enLaLista ?? [])}
    />
  ),
}))

import { Cesta } from './Cesta'

/* ------------------------------------------------------------ los datos --- */

/** Una linea de la lista, como la manda `GET /listas/{id}`. */
function linea(id: string, nombre: string, cantidad = 1, extra: Record<string, unknown> = {}) {
  return {
    id,
    nombre_visto: nombre,
    cantidad,
    nota: null,
    grupo_id: 10,
    producto_id: null,
    tachado_en: null,
    ...extra,
  }
}

/** Una linea resuelta en una tienda: `FilaEnTienda` de la API. */
function fila(lineaId: string, nombre: string, coste: number) {
  return {
    linea_id: lineaId,
    nombre,
    cantidad: 1,
    producto_id: `mercadona:${lineaId}`,
    coste_cent: coste,
    coste_sin_oferta_cent: coste,
    promo: null,
    sugerencia: null,
    identidad: 'exacto',
    autorizada: true,
    motivo: null,
    opciones: [],
    mas_barata: 'mercadona',
    elegida: 'mercadona',
  }
}

/** Una linea sin decidir: `PendienteDeDecidir`, con su precio mas barato al lado. */
function pendiente(lineaId: string, nombre: string, coste: number | null) {
  return {
    linea_id: lineaId,
    nombre,
    cantidad: 1,
    hay_precio: coste !== null,
    mas_barata: coste === null ? null : 'dia',
    coste_cent: coste,
    producto_id: coste === null ? null : `dia:${lineaId}`,
    opciones: [],
    autorizado: false,
    autorizado_producto: null,
    autorizado_cadena: null,
  }
}

/** La respuesta de `GET /listas/{id}/reparto`, con lo que se pinta aqui. */
function repartoDe(datos: {
  sublistas?: unknown[]
  sin_asignar?: unknown[]
  sin_encontrar?: unknown[]
}) {
  return {
    sublistas: datos.sublistas ?? [],
    sin_asignar: datos.sin_asignar ?? [],
    sin_encontrar: datos.sin_encontrar ?? [],
    total_cent: 0,
    total_sin_ofertas_cent: 0,
    ahorro_cent: 0,
    lineas: 3,
    decididas: 0,
    sin_precio: 0,
    una_tienda: [],
    repartido: null,
    fecha_datos: '2026-11-05',
  }
}

function monta() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/compra/listas/L1']}>
        <Routes>
          <Route path="/compra/listas/:listaId" element={<Cesta />} />
          <Route path="/compra/listas" element={<Cesta />} />
          <Route path="/compra" element={<p>El buscador</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Lo que no puede leerse en una pantalla de consumo (§8): ni API, ni codigos, ni «gold». */
const TECNICO = /401|403|500|\bAPI\b|servidor|endpoint|\bgold\b|parquet|docker|repositorio|reparto\b/i

/** La tarjeta del precio, esperando a que la lista haya llegado. */
async function laTarjetaDelTotal(): Promise<HTMLElement> {
  await screen.findByText('Precio estimado')
  const tarjeta = document.querySelector('section[aria-labelledby="precio-estimado"]')
  expect(tarjeta).not.toBeNull()
  return tarjeta as HTMLElement
}

/** El trozo de «Lo que falta», esperando a que la lista haya llegado. */
async function loQueFalta(): Promise<HTMLElement> {
  return await screen.findByRole('region', { name: /Lo que falta/ })
}

beforeEach(() => {
  localStorage.clear()
  dobles.sesion = { usuario: { id: 'u1', usuario: 'ana', nombre: 'Ana' }, preferencias: {} }
  dobles.listas = [{ id: 'L1', nombre: 'La de casa', es_de_casa: true, lineas: 3 }]
  dobles.detalle = {
    papel: 'dueno',
    // *Cuatro cosas, como el artboard, y con precios que suman 10,70 €.*
    lineas: [
      linea('l1', 'Alubia blanca 1 kg'),
      linea('l2', 'Leche entera 1,5 l', 2),
      linea('l3', 'Patatas malla 5 kg'),
      linea('l4', 'Cebolla 1 kg'),
    ],
    estimacion: { total_cent: 1070, en_carrito_cent: 0, por_recoger_cent: 1070, lineas: 4, sin_precio: 0 },
    personas: [],
    novedades: [],
    fecha_datos: '2026-11-05',
  }
  dobles.reparto = repartoDe({
    sin_asignar: [
      pendiente('l1', 'Alubia blanca 1 kg', 245),
      pendiente('l2', 'Leche entera 1,5 l', 197),
      pendiente('l3', 'Patatas malla 5 kg', 499),
      pendiente('l4', 'Cebolla 1 kg', 129),
    ],
  })
  dobles.fallo = null
  dobles.llamadas = { detalle: 0, reparto: 0 }
})

/* ============================================================== la cabecera === */

describe('la cabecera dice dónde estás y deja volver', () => {
  it('tiene volver a la portada, el antetítulo y el nombre de la lista', async () => {
    monta()
    // *El nombre de la lista es lo unico que distingue esta pantalla de otra lista: el
    // `h1` del armazon ya dice «Lista», y repetirlo aqui no informaria de nada.*
    const titulo = await screen.findByRole('heading', { level: 2, name: 'La de casa' })
    expect(titulo).toBeInTheDocument()
    expect(screen.getByText(/^Compra/)).toBeInTheDocument()
    const volver = screen.getByRole('link', { name: 'Volver a la portada' })
    expect(volver).toHaveAttribute('href', '/')
  })

  it('el botón de opciones abre la cuenta y la vuelve a cerrar', async () => {
    monta()
    const opciones = await screen.findByRole('button', { name: 'Tu cuenta' })
    expect(opciones).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('link', { name: 'Ajustes' })).not.toBeInTheDocument()
    fireEvent.click(opciones)
    expect(opciones).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('link', { name: 'Ajustes' })).toHaveAttribute('href', '/ajustes')
    expect(screen.getByRole('button', { name: 'Salir' })).toBeInTheDocument()
  })
})

/* ========================================================= el precio estimado === */

describe('el precio estimado', () => {
  it('enseña el total de la estimación y de qué está hecho', async () => {
    monta()
    const dentro = within(await laTarjetaDelTotal())
    // *La cifra es la de la API, tal cual: 1070 centimos.*
    expect(dentro.getByText('Precio estimado')).toBeInTheDocument()
    expect(dentro.getByText('10,70 €')).toBeInTheDocument()
    expect(dentro.getByText(/4 productos/)).toBeInTheDocument()
    expect(dentro.getByText(/no incluye ofertas condicionadas/)).toBeInTheDocument()
  })

  it('dice la cadena solo cuando todo va a la misma', async () => {
    dobles.reparto = repartoDe({
      sublistas: [
        {
          cadena: 'dia',
          lineas: [
            fila('l1', 'Alubia blanca 1 kg', 245),
            fila('l2', 'Leche entera 1,5 l', 197),
          ],
          unidades: 3,
          total_cent: 442,
          total_sin_ofertas_cent: 442,
          ahorro_cent: 0,
          ofertas: [],
          sin_encontrar: [],
        },
      ],
    })
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Alubia blanca 1 kg'), linea('l2', 'Leche entera 1,5 l')],
    }
    monta()
    expect(within(await laTarjetaDelTotal()).getByText('en DIA')).toBeInTheDocument()
  })

  it('no pone cadena cuando la compra esta repartida', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Alubia blanca 1 kg'), linea('l2', 'Leche entera 1,5 l')],
    }
    dobles.reparto = repartoDe({
      sublistas: [
        {
          cadena: 'dia',
          lineas: [fila('l1', 'Alubia blanca 1 kg', 245)],
          unidades: 1,
          total_cent: 245,
          total_sin_ofertas_cent: 245,
          ahorro_cent: 0,
          ofertas: [],
          sin_encontrar: [],
        },
        {
          cadena: 'mercadona',
          lineas: [fila('l2', 'Leche entera 1,5 l', 197)],
          unidades: 1,
          total_cent: 197,
          total_sin_ofertas_cent: 197,
          ahorro_cent: 0,
          ofertas: [],
          sin_encontrar: [],
        },
      ],
    })
    monta()
    // *Dos tiendas no son «una» cadena: la tarjeta no dice ninguna.*
    expect(within(await laTarjetaDelTotal()).queryByText(/^en /)).not.toBeInTheDocument()
  })

  it('no se inventa un cero cuando no hay precio de nada', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      estimacion: { total_cent: 0, en_carrito_cent: 0, por_recoger_cent: 0, lineas: 4, sin_precio: 4 },
    }
    dobles.reparto = repartoDe({
      sin_asignar: [pendiente('l1', 'Alubia blanca 1 kg', null)],
    })
    monta()
    const dentro = within(await laTarjetaDelTotal())
    expect(dentro.getByText('Todavía sin precio')).toBeInTheDocument()
    expect(dentro.queryByText('0,00 €')).not.toBeInTheDocument()
    expect(dentro.getByText(/no tengo precio de ninguno/)).toBeInTheDocument()
  })
})

/* ================================================================ las filas === */

describe('las filas de producto', () => {
  it('cada casilla se anuncia con el nombre de su linea', async () => {
    monta()
    const dentro = within(await loQueFalta())
    const casilla = await dentro.findByRole('checkbox', { name: /Alubia blanca 1 kg/ })
    expect(casilla).not.toBeChecked()
  })

  it('enseña el precio de la linea cuando la API lo sabe', async () => {
    monta()
    const dentro = within(await loQueFalta())
    const nombre = await dentro.findByText('Alubia blanca 1 kg')
    const fila1 = nombre.closest('li') as HTMLElement
    // *2,45 € es el `coste_cent` del reparto para esa linea, no un reparto del total.*
    expect(within(fila1).getByText('2,45 €')).toBeInTheDocument()
    // *Y la cadena de la que es ese precio, para poder comprobarlo.*
    expect(within(fila1).getByText(/en DIA/)).toBeInTheDocument()
  })

  it('si no hay precio para una linea, la fila se queda sin cifra', async () => {
    dobles.reparto = repartoDe({
      // *La cebolla no esta en el reparto: la API no dice lo que cuesta.*
      sin_asignar: [pendiente('l1', 'Alubia blanca 1 kg', 245)],
    })
    monta()
    const dentro = within(await loQueFalta())
    const nombre = await dentro.findByText('Cebolla 1 kg')
    const filaCebolla = nombre.closest('li') as HTMLElement
    expect(within(filaCebolla).queryByText('€', { exact: false })).not.toBeInTheDocument()
    // *Y se dice, en vez de dejar un hueco que parece un precio que no ha cargado.*
    expect(within(filaCebolla).getByText('sin precio')).toBeInTheDocument()
  })

  it('mantiene cambiar la cantidad y quitar la linea, con su nombre', async () => {
    monta()
    await loQueFalta()
    expect(screen.getByRole('button', { name: 'Menos Alubia blanca 1 kg' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Más Alubia blanca 1 kg' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Quitar Alubia blanca 1 kg de la lista' }))
      .toBeInTheDocument()
    // *La cantidad tambien se lee, y la de dos unidades se dice.*
    expect(screen.getByText('2 ×')).toBeInTheDocument()
  })

  it('lo tachado va a «En el carro» y no se cuenta como lo que falta', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Alubia blanca 1 kg'),
        linea('l2', 'Leche entera 1,5 l', 1, { tachado_en: '2026-11-05T10:00:00Z' }),
      ],
    }
    monta()
    expect(await screen.findByRole('heading', { name: /En el carro/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Lo que falta/ })).toBeInTheDocument()
  })
})

/* ========================================================= añadir y comparar === */

describe('añadir y comparar', () => {
  it('deja añadir un producto y comparar la cesta, cada cosa en su sitio', async () => {
    monta()
    const anadir = await screen.findByRole('link', { name: 'Añadir producto' })
    expect(anadir).toHaveAttribute('href', '/compra')
    // *Una sola puerta a comparar: dos la misma promesa en dos sitios se contradicen el dia
    // que una cambie.*
    const comparar = screen.getAllByRole('link', { name: 'Comparar mi cesta' })
    expect(comparar).toHaveLength(1)
    expect(comparar[0]).toHaveAttribute('href', '/compra/listas/L1/comparar')
    expect(screen.getByText('Dónde sale mejor tu cesta')).toBeInTheDocument()
  })
})

/* ========================================================= rellenar sola === */

describe('rellenar lo de siempre', () => {
  it('con la lista de casa, deja rellenar y comparar en el mismo sitio', async () => {
    monta()
    const mosaico = await screen.findByTestId('mosaico')
    // *La cuadricula de la lista se pinta como tal: la compra básica tiene su título de
    // verdad, no el de «lo de siempre».*
    expect(mosaico).toHaveAttribute('data-enunalista', 'true')
    // *Y se le dicen los grupos que ya están dentro: no se ofrece lo que ya está apuntado.*
    expect(JSON.parse(mosaico.getAttribute('data-enlalista') ?? '[]')).toEqual([10])

    // *** LA PUERTA A COMPARAR, JUNTO AL RELLENO. ***
    // *«Sugerir otro sitio» es la comparación que ya existe; aquí se comprueba que está
    // **después** del bloque de relleno, en el mismo flujo y sin abrir otra pantalla.*
    const comparar = screen.getByRole('link', { name: 'Comparar mi cesta' })
    expect(
      mosaico.compareDocumentPosition(comparar) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('en una lista que no es la de casa no ofrece rellenar', async () => {
    // *`useAnadeALaCesta` apunta a la lista de casa: ofrecer «rellenar» mirando otra lista
    // añadiría a escondidas a una lista que no es la que se tiene delante.*
    dobles.listas = [{ id: 'L1', nombre: 'La del pueblo', es_de_casa: false, lineas: 3 }]
    monta()
    const selector = await screen.findByRole('combobox', { name: 'Lista' })
    fireEvent.change(selector, { target: { value: 'L1' } })
    await screen.findByRole('heading', { name: 'La del pueblo' })
    expect(screen.queryByTestId('mosaico')).not.toBeInTheDocument()
  })
})

/* ========================================================== los otros estados === */

describe('los estados que no son «con datos»', () => {
  it('una lista vacía lo dice y ofrece la compra básica', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [],
      estimacion: { total_cent: 0, en_carrito_cent: 0, por_recoger_cent: 0, lineas: 0, sin_precio: 0 },
    }
    monta()
    expect(await screen.findByText('La lista está vacía')).toBeInTheDocument()
    expect(screen.getByTestId('mosaico')).toBeInTheDocument()
    // *Sin lineas no hay nada que estimar ni que comparar: no se pinta una tarjeta con un
    // cero ni una puerta que lleva a «esta lista no tiene nada que comparar».*
    expect(screen.queryByText('Precio estimado')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Comparar mi cesta' })).not.toBeInTheDocument()
  })

  it('sin una lista de casa y sin elegir, dice que elija una', async () => {
    // *Con listas pero ninguna de casa, `listaDelDiario` devuelve `null` a proposito: elegir
    // por quien no ha elegido es lo que hacia anadir una compra en la lista de otra persona.
    // La pantalla no puede quedarse en blanco: dice que elija, y el desplegable esta al lado.*
    dobles.listas = [{ id: 'L1', nombre: 'La del pueblo', es_de_casa: false, lineas: 2 }]
    monta()
    expect(await screen.findByText('Elige una lista')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Lista' })).toBeInTheDocument()
  })

  it('un fallo trae reintento y el reintento vuelve a pedirlo', async () => {
    dobles.fallo = new Error('se ha roto')
    monta()
    expect(await screen.findByRole('alert')).toHaveTextContent('No he podido traer esto')
    const antes = dobles.llamadas.detalle
    fireEvent.click(screen.getByRole('button', { name: 'Volver a intentarlo' }))
    await waitFor(() => expect(dobles.llamadas.detalle).toBeGreaterThan(antes))
  })

  it('no dice nada técnico ni de relleno', async () => {
    monta()
    await screen.findByRole('heading', { name: 'La de casa' })
    expect(document.body.textContent ?? '').not.toMatch(TECNICO)
  })
})
