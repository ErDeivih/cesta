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
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { onlineManager, QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { ErrorApi } from '../api/cliente'

/* ------------------------------------------------------------- los dobles --- */

const dobles = vi.hoisted(() => ({
  sesion: { usuario: { id: 'u1', usuario: 'ana', nombre: 'Ana' }, preferencias: {} } as unknown,
  listas: [] as unknown[],
  detalle: null as unknown,
  reparto: null as unknown,
  /** Lo que contesta `GET /listas/{id}/repetir-compra`. */
  previaRepetir: null as unknown,
  /** Lo que contesta `POST /listas/{id}/repetir-compra`. */
  reciboRepetir: null as unknown,
  /** Y lo que puede fallar el POST, cuando la prueba lo pide. */
  falloRepetir: null as unknown,
  fallo: null as unknown,
  /** Los argumentos de la ultima llamada a `anadirLinea`: es lo que se mide cuando se
   *  elige una sugerencia del buscador de producto. */
  anadida: null as unknown,
  llamadas: { detalle: 0, reparto: 0, previa: 0, repetir: 0 },
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
    previaDeRepetirCompra: async () => {
      dobles.llamadas.previa += 1
      if (dobles.fallo) throw dobles.fallo
      return dobles.previaRepetir
    },
    repetirCompra: async () => {
      dobles.llamadas.repetir += 1
      if (dobles.falloRepetir) throw dobles.falloRepetir
      return dobles.reciboRepetir
    },
    // *Nada de red en una prueba: los cambios no se pulsan, pero la mutacion se construye.*
    cambiarLinea: async () => ({}),
    anadirLinea: async (...args: unknown[]) => {
      dobles.anadida = args
      return {}
    },
    crearLista: async (nombre: string, esDeCasa = false) => ({
      id: 'L9', nombre, es_de_casa: esDeCasa, lineas: 0,
    }),
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
  // *Sin compra anterior: la tarjeta de repetir no se pinta, que es lo que se mide en las
  // demas pruebas de este fichero. Cada prueba que la necesita la rellena.*
  dobles.previaRepetir = previaDeCompra({ compra_id: null, fecha: null, lineas: [] })
  dobles.reciboRepetir = { anadidos: 0, ya_estaban: 0, sin_catalogo: 0, faltan: 0 }
  dobles.falloRepetir = null
  dobles.anadida = null
  dobles.llamadas = { detalle: 0, reparto: 0, previa: 0, repetir: 0 }
  // La red vuelve a estar en pie en cada prueba: la del «sin conexión» la apaga. Y se avisa con
  // el evento: React Query escucha `online` una vez para todo el proceso, así que cambiar solo
  // `navigator.onLine` dejaba la siguiente prueba con las consultas pausadas.
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, value: true })
  // *No basta con cambiar `navigator.onLine`: React Query guarda el estado de red en un gestor
  // global y, si una prueba anterior lo dejó en «sin conexión», las consultas se quedan
  // **pausadas** sin decirlo (y la pantalla pinta la salida de «entra»).*
  onlineManager.setOnline(true)
})

/* ============================================================== la cabecera === */

describe('la cabecera dice dónde estás y deja volver', () => {
  it('tiene volver a la portada, el antetítulo y el nombre de la lista', async () => {
    monta()
    // *El nombre de la lista es lo unico que distingue esta pantalla de otra lista: el
    // `h1` del armazon ya dice «Lista», y repetirlo aqui no informaria de nada.*
    const titulo = await screen.findByRole('heading', { level: 2, name: 'La de casa' })
    expect(titulo).toBeInTheDocument()
    // *El antetítulo lleva la marca delante: la lista es la pantalla de entrada de la demo y
    // el nombre tiene que verse ahí, no solo en la pestaña.*
    expect(screen.getByText(/^Avío · Compra/)).toBeInTheDocument()
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

/* ================================================== el mínimo de un producto === */

/** El bloque `minimo` que la API añade a cada línea, tal y como está contratado.
 *
 *  *La API todavía no lo manda -- otro compañero lo está implementando en paralelo --, así que
 *  aquí se dobla a mano. Si no viene el campo, la línea se pinta como hoy: por eso las demás
 *  pruebas de este fichero (que no lo llevan) no cambian.* */
function minimoDe(extra: Record<string, unknown> = {}) {
  return {
    producto_id: 'mercadona:l1',
    cadena: 'mercadona',
    precio_cent: 83,
    precio_unidad_cent: 138,
    unidad: 'kg',
    minimo_cent: 83,
    minimo_fecha: '2026-10-12',
    vuelve_al_minimo: false,
    nuevo_minimo: false,
    ...extra,
  }
}

describe('el mínimo de un producto', () => {
  it('una línea que vuelve a su mínimo lo dice en una pastilla, con la fecha y sin diálogo', async () => {
    const alerta = vi.spyOn(window, 'alert').mockImplementation(() => {})
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Alubia blanca 1 kg', 1, { minimo: minimoDe({ vuelve_al_minimo: true }) }),
        linea('l2', 'Leche entera 1,5 l', 2),
      ],
    }
    dobles.reparto = repartoDe({
      sin_asignar: [pendiente('l1', 'Alubia blanca 1 kg', 245)],
    })
    monta()
    const dentro = within(await loQueFalta())
    const fila1 = (await dentro.findByText('Alubia blanca 1 kg')).closest('li') as HTMLElement
    // *La cifra es la del mínimo de la API (`minimo_cent`), no el precio de hoy de la línea.*
    expect(within(fila1).getByText(/En su mínimo · 0,83 €/)).toBeInTheDocument()
    // *Y la fecha se lee como texto: no un `title`, que solo lo ve quien pasa el ratón.*
    expect(within(fila1).getByText(/visto por primera vez el 12 oct/)).toBeInTheDocument()
    // *La marca es una pastilla dentro de la línea: ni modal, ni aviso del navegador.*
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(alerta).not.toHaveBeenCalled()
    alerta.mockRestore()
  })

  it('un mínimo nuevo usa la otra pastilla, no la de «En su mínimo»', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Alubia blanca 1 kg', 1, {
          minimo: minimoDe({ nuevo_minimo: true, minimo_cent: 79, precio_cent: 79 }),
        }),
      ],
    }
    dobles.reparto = repartoDe({
      sin_asignar: [pendiente('l1', 'Alubia blanca 1 kg', 245)],
    })
    monta()
    const dentro = within(await loQueFalta())
    const fila1 = (await dentro.findByText('Alubia blanca 1 kg')).closest('li') as HTMLElement
    expect(within(fila1).getByText(/Mínimo nuevo · 0,79 €/)).toBeInTheDocument()
    expect(within(fila1).queryByText(/En su mínimo/)).not.toBeInTheDocument()
  })

  it('sin una fecha legible, la pastilla se queda sola y no escribe «no lo sé» dentro de la frase', async () => {
    // *La fecha es opcional en el sentido de que un ISO roto no se puede escribir. Un «visto
    // por primera vez el no lo sé» no se lee: la frase se calla y la pastilla se queda.*
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [
        linea('l1', 'Alubia blanca 1 kg', 1, {
          minimo: minimoDe({ vuelve_al_minimo: true, minimo_fecha: '' }),
        }),
      ],
    }
    dobles.reparto = repartoDe({
      sin_asignar: [pendiente('l1', 'Alubia blanca 1 kg', 245)],
    })
    monta()
    const dentro = within(await loQueFalta())
    const fila1 = (await dentro.findByText('Alubia blanca 1 kg')).closest('li') as HTMLElement
    expect(within(fila1).getByText(/En su mínimo · 0,83 €/)).toBeInTheDocument()
    expect(within(fila1).queryByText(/visto por primera vez/)).not.toBeInTheDocument()
    expect(within(fila1).queryByText(/no lo sé/)).not.toBeInTheDocument()
  })

  it('una línea sin mínimo se pinta como siempre, con su nombre, su cantidad y su precio', async () => {
    monta()
    const dentro = within(await loQueFalta())
    // *La alubia no lleva `minimo`: ni pastilla ni nada nuevo. Y lo de siempre sigue ahí.*
    const fila1 = (await dentro.findByText('Alubia blanca 1 kg')).closest('li') as HTMLElement
    expect(within(fila1).queryByText(/En su mínimo|Mínimo nuevo/)).not.toBeInTheDocument()
    expect(within(fila1).getByRole('checkbox', { name: /Alubia blanca 1 kg/ })).toBeInTheDocument()
    // *2,45 € es el precio de la línea en el reparto, y se queda donde estaba.*
    expect(within(fila1).getByText('2,45 €')).toBeInTheDocument()
    // *Y la cantidad de dos unidades se sigue diciendo, aunque la línea no tenga mínimo.*
    const fila2 = (await dentro.findByText('Leche entera 1,5 l')).closest('li') as HTMLElement
    expect(within(fila2).getByText('2 ×')).toBeInTheDocument()
    expect(within(fila2).queryByText(/En su mínimo|Mínimo nuevo/)).not.toBeInTheDocument()
  })
})

/* ==================================== repetir la compra de la semana pasada === */

/** Una línea de la última compra cerrada, tal como la manda la previa de repetir.
 *
 *  `estado` es lo que la tarjeta tiene que saber decir en voz alta: `falta` (se va a
 *  añadir), `ya_estaba` (ya está en la lista) o `sin_catalogo` (no se puede repetir). */
function deLaCompraAnterior(
  nombre: string,
  estado: 'falta' | 'ya_estaba' | 'sin_catalogo',
  cantidad = 1,
  enCasa: boolean | null = null,
) {
  return {
    nombre,
    producto_id: estado === 'sin_catalogo' ? null : `mercadona:${nombre}`,
    grupo_id: estado === 'sin_catalogo' ? null : 10,
    cantidad,
    estado,
    en_casa: enCasa,
  }
}

/** Lo que contesta `GET /listas/{id}/repetir-compra`: la última compra cerrada de la lista. */
function previaDeCompra(datos: Record<string, unknown> = {}) {
  return {
    compra_id: 'c1',
    fecha: '2026-11-05',
    lineas: [],
    faltan: 0,
    ya_estaban: 0,
    sin_catalogo: 0,
    ...datos,
  }
}

/** La tarjeta de repetir, esperando a que la previa haya llegado. */
async function laTarjetaDeRepetir(): Promise<HTMLElement> {
  const titulo = await screen.findByRole(
    'heading', { name: 'Repetir la compra de la semana pasada' })
  const tarjeta = titulo.closest('section')
  expect(tarjeta).not.toBeNull()
  return tarjeta as HTMLElement
}

describe('repetir la compra de la semana pasada', () => {
  it('con compra anterior enseña la fecha, el resumen, los estados y el botón', async () => {
    dobles.previaRepetir = previaDeCompra({
      lineas: [
        deLaCompraAnterior('Alubia blanca 1 kg', 'ya_estaba'),
        deLaCompraAnterior('Leche entera 1,5 l', 'ya_estaba', 2),
        deLaCompraAnterior('Patatas malla 5 kg', 'falta'),
        deLaCompraAnterior('Pan del pueblo', 'sin_catalogo'),
      ],
      faltan: 1,
      ya_estaban: 2,
      sin_catalogo: 1,
    })
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    // *La fecha de la compra, en castellano: nunca el ISO crudo.*
    expect(dentro.getByText(/Del 5 nov 2026/)).toBeInTheDocument()
    // *El resumen, con las tres cuentas de la previa.*
    expect(dentro.getByText(/4 productos · 2 ya están en la lista · 1 sin catálogo/))
      .toBeInTheDocument()
    // *Cada línea con su estado, en texto visible: lo lee también el lector de pantalla.*
    expect(dentro.getByText('Alubia blanca 1 kg')).toBeInTheDocument()
    expect(dentro.getAllByText('ya está en la lista')).toHaveLength(2)
    expect(dentro.getByText('falta')).toBeInTheDocument()
    expect(dentro.getByText('sin catálogo')).toBeInTheDocument()
    // *Y el botón dice cuántos se van a añadir, que es el número que decide pulsarlo.*
    expect(dentro.getByRole('button', { name: 'Añadir los que faltan (1)' }))
      .toBeInTheDocument()
  })

  it('sin compra anterior no pinta la tarjeta ni deja un hueco', async () => {
    monta()
    await loQueFalta()
    // *La previa se pide siempre (es la única forma de saber si hay compra anterior)...*
    await waitFor(() => expect(dobles.llamadas.previa).toBeGreaterThan(0))
    // *...y como no la hay, la pantalla se queda como estaba: ni tarjeta ni hueco.*
    expect(screen.queryByRole('heading', { name: 'Repetir la compra de la semana pasada' }))
      .not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Añadir los que faltan/ }))
      .not.toBeInTheDocument()
  })

  it('marca lo que ya está en casa y lo que falta en casa', async () => {
    // *Repetir reproduce la compra, pero la despensa dice qué no hace falta comprar. Se marca
    // solo en las que se van a añadir: en una que ya está en la lista no hay nada que decidir.*
    dobles.previaRepetir = previaDeCompra({
      lineas: [
        deLaCompraAnterior('Leche entera 1,5 l', 'falta', 1, true),
        deLaCompraAnterior('Patatas malla 5 kg', 'falta', 1, false),
        deLaCompraAnterior('Alubia blanca 1 kg', 'ya_estaba', 1, true),
      ],
      faltan: 2,
      ya_estaban: 1,
      sin_catalogo: 0,
      en_casa: 2,
      faltan_en_casa: 1,
    })
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    expect(dentro.getByText(/En casa: 2 · Falta en casa: 1/)).toBeInTheDocument()
    expect(dentro.getByText('en casa')).toBeInTheDocument()
    expect(dentro.getByText('falta en casa')).toBeInTheDocument()
    const alubia = dentro.getByText('Alubia blanca 1 kg').closest('li') as HTMLElement
    expect(within(alubia).queryByText('en casa')).not.toBeInTheDocument()
  })

  it('al pulsar añade de verdad y lo cuenta en la propia tarjeta', async () => {
    dobles.previaRepetir = previaDeCompra({
      lineas: [
        deLaCompraAnterior('Patatas malla 5 kg', 'falta'),
        deLaCompraAnterior('Alubia blanca 1 kg', 'ya_estaba'),
      ],
      faltan: 1,
      ya_estaban: 1,
    })
    dobles.reciboRepetir = { anadidos: 1, ya_estaban: 1, sin_catalogo: 0, faltan: 1 }
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    fireEvent.click(dentro.getByRole('button', { name: 'Añadir los que faltan (1)' }))
    // *El aviso va dentro de la tarjeta: sin popup ni notificación del navegador.*
    expect(await screen.findByText(/Añadidas 1 · 1 ya estaban · 0 sin catálogo/))
      .toBeInTheDocument()
    expect(dobles.llamadas.repetir).toBe(1)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('con una fecha ilegible no escribe «Del no lo sé»: enseña el resumen y ya', async () => {
    // *Una fecha rota no se convierte en «no lo sé» dentro de una frase: se calla la frase
    // y el resumen sigue, que es el dato que importa aquí.*
    dobles.previaRepetir = previaDeCompra({
      fecha: 'no-es-una-fecha',
      lineas: [deLaCompraAnterior('Patatas malla 5 kg', 'falta')],
      faltan: 1,
    })
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    expect(dentro.queryByText(/Del no lo sé/)).not.toBeInTheDocument()
    expect(dentro.getByText(/1 producto · 0 ya están en la lista · 0 sin catálogo/))
      .toBeInTheDocument()
    expect(dentro.getByRole('button', { name: 'Añadir los que faltan (1)' }))
      .toBeInTheDocument()
  })

  it('en una lista de solo mirar, el botón está apagado y los estados se ven igual', async () => {
    // *Un botón que la API va a contestar 403 no se ofrece como si funcionara; la pantalla ya
    // dice arriba que quien la creó puede dar el papel de escribir.*
    dobles.detalle = { ...(dobles.detalle as Record<string, unknown>), papel: 'mira' }
    dobles.previaRepetir = previaDeCompra({
      lineas: [
        deLaCompraAnterior('Patatas malla 5 kg', 'falta'),
        deLaCompraAnterior('Alubia blanca 1 kg', 'ya_estaba'),
      ],
      faltan: 1,
      ya_estaban: 1,
    })
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    expect(dentro.getByRole('button', { name: 'Añadir los que faltan (1)' })).toBeDisabled()
    // *Y lo que se puede hacer mirando -- saber qué falta -- se sigue viendo.*
    expect(dentro.getByText('falta')).toBeInTheDocument()
    expect(dentro.getByText('ya está en la lista')).toBeInTheDocument()
  })

  it('si no falta ninguna, lo dice y no hay botón', async () => {
    dobles.previaRepetir = previaDeCompra({
      lineas: [deLaCompraAnterior('Alubia blanca 1 kg', 'ya_estaba')],
      faltan: 0,
      ya_estaban: 1,
    })
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    expect(dentro.getByText('Ya tienes todo lo de esa compra.')).toBeInTheDocument()
    expect(dentro.queryByRole('button', { name: /Añadir los que faltan/ }))
      .not.toBeInTheDocument()
  })

  it('si el servidor dice que no, se cuenta en un aviso y la tarjeta sigue en pie', async () => {
    dobles.previaRepetir = previaDeCompra({
      lineas: [deLaCompraAnterior('Patatas malla 5 kg', 'falta')],
      faltan: 1,
    })
    dobles.falloRepetir = new ErrorApi(403, 'Esta lista es de solo mirar.')
    monta()
    const dentro = within(await laTarjetaDeRepetir())
    fireEvent.click(dentro.getByRole('button', { name: 'Añadir los que faltan (1)' }))
    expect(await screen.findByText('Esta lista es de solo mirar.')).toBeInTheDocument()
    // *El texto de la API, sin números ni nombres de endpoint (§8 de la doctrina).*
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
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

/* ==================================== apuntar sin salir de la lista === */

/** Una respuesta de `GET /api/buscar`, con la forma de la API de verdad.
 *
 *  *La pantalla no inventa el producto: lo pide. Lo que se mide aqui es que el campo de la
 *  lista pregunta, ensena la sugerencia con su €/kg y la apunta donde toca sin salir.* */
function respuestaBuscar(nombre = 'Leche entera 1 l') {
  return {
    fecha_datos: '2026-11-13',
    resultados: [
      {
        grupo_id: 77,
        nombre,
        marca: 'Puleva',
        cadena_mas_barata: 'dia',
        precio_cent: 99,
        precio_unidad_cent: 66,
        precio_unidad_max_cent: 66,
        unidad: 'l',
        cadenas: 3,
        productos: 4,
        nutriscore: null,
        imagen: null,
        ecoscore: null,
        kcal_100g: null,
        hidratos_100g: null,
        proteinas_100g: null,
        grasas_100g: null,
        grasas_sat_100g: null,
        azucares_100g: null,
        sal_100g: null,
        con_oferta: false,
        con_oferta_club: false,
        con_retirada: false,
        comparable: true,
        dudoso: false,
        ahorro_pct: 12.5,
      },
    ],
  }
}

/** Sustituye `fetch` por la respuesta del buscador y devuelve las URLs pedidas.
 *
 *  *Solo contesta `/api/buscar`: el resto de la pantalla ya va por los dobles de `api/cesta`, y
 *  devolverle a cualquier URL el JSON del buscador haría que una consulta real leyera un dato con
 *  otra forma (medido: `donde` acabó sin `una_tienda` y tumbó la pantalla).* Sin red, como en el
 *  pasillo: `TypeError`, que la app sabe contar.*
 */
function conRed(respuesta: unknown = respuestaBuscar()) {
  const pedidas: string[] = []
  const falso = vi.fn(async (url: string | URL) => {
    pedidas.push(String(url))
    if (!/\/api\/buscar/.test(String(url))) throw new TypeError('sin red')
    return { ok: true, status: 200, json: async () => respuesta } as unknown as Response
  })
  vi.stubGlobal('fetch', falso)
  return pedidas
}

describe('apuntar sin salir de la lista', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('el buscador de producto está en la lista y apunta al elegir sin salir de la pantalla', async () => {
    const pedidas = conRed()
    monta()
    await screen.findByRole('heading', { name: 'La de casa' })

    const campo = screen.getByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'leche')

    const opcion = await screen.findByRole('option', { name: /Leche entera/ })
    // *Con €/kg: es la decision de compra, y en la sugerencia tiene que estar.*
    expect(opcion).toHaveTextContent('0,66')
    expect(pedidas.some((u) => /\/api\/buscar/.test(u) && /q=leche/.test(u))).toBe(true)

    await userEvent.click(opcion)
    await waitFor(() => expect(dobles.anadida).not.toBeNull())
    const [listaId, nueva] = dobles.anadida as [string, { nombre: string; grupo_id: number }]
    expect(listaId).toBe('L1')
    expect(nueva.grupo_id).toBe(77)
    expect(nueva.nombre).toBe('Leche entera 1 l')
    // El foco se queda donde estaba: apuntar es seguir apuntando, no volver a buscar el campo.
    expect(campo).toHaveFocus()
  })

  it('sin ninguna lista, apunta en la de casa que se crea sola', async () => {
    conRed()
    dobles.listas = []
    monta()

    const campo = await screen.findByRole('combobox', { name: 'Añadir a la lista' })
    await userEvent.type(campo, 'leche')
    await userEvent.click(await screen.findByRole('option', { name: /Leche entera/ }))

    await waitFor(() => expect(dobles.anadida).not.toBeNull())
    expect((dobles.anadida as [string])[0]).toBe('L9')
  })

  it('sin conexión lo avisa, dice qué pasa con lo apuntado y deja seguir apuntando', async () => {
    conRed()
    Object.defineProperty(window.navigator, 'onLine', { configurable: true, value: false })
    monta()
    fireEvent(window, new Event('offline'))

    expect(await screen.findByText('Sin conexión')).toBeInTheDocument()
    expect(screen.getByText(/se guarda en el móvil/i)).toBeInTheDocument()
    // El aviso no tapa la pantalla: el buscador sigue en pie.
    expect(screen.getByRole('combobox', { name: 'Añadir a la lista' })).toBeInTheDocument()
  })

  it('la confirmación de terminar la compra es un diálogo que atrapa el foco y lo devuelve', async () => {
    dobles.detalle = {
      ...(dobles.detalle as Record<string, unknown>),
      lineas: [linea('l1', 'Alubia blanca 1 kg', 1, { tachado_en: '2026-11-13T10:00:00' })],
    }
    monta()
    const terminar = await screen.findByRole('button', { name: 'He terminado la compra' })
    terminar.focus()
    fireEvent.click(terminar)

    const dialogo = await screen.findByRole('dialog', { name: /Terminar la compra/ })
    expect(dialogo.contains(document.activeElement)).toBe(true)

    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    // Escape cierra y el foco vuelve a quien lo abrió.
    expect(terminar).toHaveFocus()
  })
})
