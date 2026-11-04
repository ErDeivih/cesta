/** *** LA FRESCURA Y LA COBERTURA SE VEN EN AJUSTES, CADENA A CADENA. ***
 *
 *  *El BACKLOG lo pide por su nombre (M18): «cobertura medida en Ajustes → Fuentes».* *No es una
 *  pantalla de administracion: es donde cualquiera puede comprobar **contra que se esta midiendo** el
 *  catalogo que ve, sin tener que fiarse de la portada.*
 *
 *  *Y el fallo que evita es el de siempre: un `mercadona 4226` sin su cobertura al lado se lee como
 *  «Mercadona tiene 4 226 productos» y como si eso fuera todo su catalogo. La frase trae las filas
 *  medidas, el `%` contra su referencia y lo que se ha movido -- y si falta un campo, no se inventa.*
 *
 *  *Se monta la pantalla de verdad (con `yo` y `useEstado` simulados, que es lo unico que no esta en
 *  el test) porque lo que hay que comprobar es que la frase **llega a la pantalla**, no solo que la
 *  funcion pura sepa formatearla (eso lo prueba `tests/cobertura.test.mjs`).*
 */

import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/cesta', () => ({
  yo: vi.fn().mockResolvedValue({
    usuario: { id: 'u1', usuario: 'david', nombre: null },
    preferencias: {},
  }),
  salir: vi.fn().mockResolvedValue(undefined),
  borrarme: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../api/ajustes', () => ({
  cadenasCerca: vi.fn().mockReturnValue([]),
  guardarPreferencia: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../api/consultas', () => ({ useEstado: vi.fn() }))

import { useEstado } from '../api/consultas'
import { Ajustes } from './Ajustes'

/** El estado del 4 de noviembre de 2026, recortado a lo que pinta esta tarjeta. */
const ESTADO = {
  fecha_datos: '2026-11-04',
  dias_precio_valido: 3,
  cadenas: [
    {
      cadena: 'mercadona',
      productos: 4226,
      ultimo_dia: '2026-11-04',
      al_dia: true,
      cobertura: {
        fuente: 'mercadona',
        cobertura: 'catalogo_diario',
        etiqueta: 'catálogo diario medido',
        fecha: '2026-11-04',
        filas: 4272,
        referencia: 4321,
        referencia_fecha: '2026-10-05',
        pct: 98.9,
        veredicto: 'ok',
        novedad: { vs: '2026-11-03', nuevos: 4, cambiados: 71, desaparecen: 9 },
      },
    },
    {
      cadena: 'lidl',
      productos: 91,
      ultimo_dia: '2026-11-04',
      al_dia: true,
      cobertura: {
        fuente: 'lidl',
        cobertura: 'ofertas_semanales_parcial',
        fecha: '2026-11-04',
        fichas_leidas: 91,
        con_precio: 91,
      },
    },
    // *Una cadena sin fichero de cobertura: la tarjeta no puede inventarle una linea.*
    { cadena: 'aldi', productos: 2499, ultimo_dia: '2026-11-03', al_dia: false, cobertura: undefined },
  ],
}

function monta() {
  vi.mocked(useEstado).mockReturnValue({
    data: ESTADO,
    isPending: false,
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useEstado>)
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={cliente}>
      <Ajustes />
    </QueryClientProvider>,
  )
}

describe('Ajustes · frescura y cobertura de los precios', () => {
  it('*** la tarjeta enseña la cobertura medida de cada cadena, con sus cifras ***', async () => {
    monta()

    // *La tarjeta existe y se llama por su nombre.*
    expect(await screen.findByRole('heading', { name: /frescura y cobertura/i })).toBeInTheDocument()

    // *Mercadona: filas, `%` de su referencia y precios cambiados, de los datos que manda la API.*
    expect(screen.getByText(/catálogo diario · 4272 filas capturadas · 98,9 % de su referencia del 5 oct · 71 precios cambiados/)).toBeInTheDocument()

    // *Y Lidl con su frase de siempre: ofertas, no el catalogo entero.*
    expect(screen.getByText(/ofertas semanales, no el catálogo entero · 91 de 91 con precio/)).toBeInTheDocument()
  })

  it('*** y no enseña ningún código crudo ni inventa cifras donde no hay medición ***', async () => {
    monta()
    const tarjeta = (await screen.findByRole('heading', { name: /frescura y cobertura/i }))
      .closest('section') as HTMLElement

    // *Una linea por cadena, ni una mas: no se inventan coberturas para quien no las manda.*
    const filas = within(tarjeta).getAllByRole('listitem')
    expect(filas).toHaveLength(3)

    // *Aldi no trae cobertura: se queda con su fecha y sin frase.*
    const aldi = filas.find((f) => f.textContent?.includes('Aldi')) as HTMLElement
    expect(aldi.textContent).toMatch(/del 3 nov/)
    expect(aldi.textContent).not.toMatch(/catálogo diario|ofertas semanales/)

    // *`catalogo_diario` y `ofertas_semanales_parcial` son claves de fichero, no algo que se lea.*
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(/catalogo_diario/)
    expect(texto).not.toMatch(/ofertas_semanales_parcial/)
  })
})
