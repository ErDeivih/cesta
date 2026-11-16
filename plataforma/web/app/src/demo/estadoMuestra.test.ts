/** *** LA LISTA DE LA SEMANA Y LOS FAVORITOS, SIN BACKEND. *** *
 *
 *  *La demo publicada guarda su estado en IndexedDB, pero las cuentas —cuánto cuesta la
 *  lista, qué línea va a qué cadena, qué favoritos hay— no pueden vivir en el parche de
 *  `fetch`: tienen que poder probarse sin navegador. Eso es `estadoMuestra.ts`, y esto es su
 *  puerta.*
 *
 *  *Lo que se prueba es lo que se rompió de verdad: añadir una línea y que el total no se
 *  mueva, tachar y que el dinero no cambie de sitio, o guardar un favorito y que al volver
 *  no esté.*
 */
import { describe, expect, it } from 'vitest'

import { CATALOGO } from './catalogo'
import {
  anadeFavorito,
  anadeLinea,
  cambiaLinea,
  creaMuestra,
  detalleDe,
  misFavoritos,
  quitaFavorito,
  repartoDe,
} from './estadoMuestra'

const SEMANA = () => creaMuestra()

function idDeLaSemana(muestra: ReturnType<typeof creaMuestra>): string {
  const semana = muestra.listas.find((l) => l.es_de_casa)
  expect(semana, 'no hay lista de casa').toBeTruthy()
  return semana!.id
}

describe('la lista de la semana en la demo', () => {
  it('nace con la lista de la semana como lista de casa y con líneas de verdad', () => {
    const muestra = SEMANA()
    const semana = muestra.listas.find((l) => l.es_de_casa)
    expect(semana?.nombre).toBe('La semana')
    const detalle = detalleDe(muestra, semana!.id)
    expect(detalle.lineas.length).toBeGreaterThanOrEqual(8)
    for (const linea of detalle.lineas) {
      expect(linea.grupo_id, `${linea.nombre_visto} sin grupo`).toBeTypeOf('number')
      expect(CATALOGO.some((p) => p.grupo_id === linea.grupo_id)).toBe(true)
    }
  })

  it('el total es la suma de lo que cuesta cada línea, no un número aparte', () => {
    const muestra = SEMANA()
    const detalle = detalleDe(muestra, idDeLaSemana(muestra))
    const reparto = repartoDe(muestra, idDeLaSemana(muestra))
    const suma = reparto.sin_asignar.reduce((total, l) => total + (l.coste_cent ?? 0), 0)
    expect(detalle.estimacion.total_cent).toBe(suma)
    expect(detalle.estimacion.total_cent).toBeGreaterThan(0)
    expect(detalle.estimacion.sin_precio).toBe(0)
  })

  it('añadir una línea sube el total exactamente lo que cuesta el producto', () => {
    const muestra = SEMANA()
    const id = idDeLaSemana(muestra)
    const antes = detalleDe(muestra, id).estimacion.total_cent
    const producto = CATALOGO[0]
    anadeLinea(muestra, id, {
      nombre: producto.nombre,
      grupoId: producto.grupo_id,
      productoId: null,
    })
    const despues = detalleDe(muestra, id).estimacion.total_cent
    expect(despues - antes).toBe(producto.precio_cent)
    expect(detalleDe(muestra, id).lineas.length).toBeGreaterThan(8)
  })

  it('cambiar la cantidad multiplica el coste de esa línea', () => {
    const muestra = SEMANA()
    const id = idDeLaSemana(muestra)
    const detalle = detalleDe(muestra, id)
    // *Una línea de cantidad 1: con una de cantidad 2 el cambio a 2 no suma nada y la
    // prueba estaría midiendo otra cosa.*
    const linea = detalle.lineas.find((l) => l.cantidad === 1)!
    const antes = detalle.estimacion.total_cent
    const producto = CATALOGO.find((p) => p.grupo_id === linea.grupo_id)!
    cambiaLinea(muestra, id, linea.id, { cantidad: 2 })
    expect(detalleDe(muestra, id).estimacion.total_cent).toBe(antes + producto.precio_cent)
  })

  it('tachar mueve el dinero de «por recoger» a «en el carro» sin cambiar el total', () => {
    const muestra = SEMANA()
    const id = idDeLaSemana(muestra)
    const detalle = detalleDe(muestra, id)
    const linea = detalle.lineas.find((l) => l.cantidad === 1)!
    const producto = CATALOGO.find((p) => p.grupo_id === linea.grupo_id)!
    const antes = detalle.estimacion
    cambiaLinea(muestra, id, linea.id, { tachado: true })
    const despues = detalleDe(muestra, id).estimacion
    expect(despues.total_cent).toBe(antes.total_cent)
    expect(despues.en_carrito_cent).toBe(antes.en_carrito_cent + producto.precio_cent)
    expect(despues.por_recoger_cent).toBe(antes.por_recoger_cent - producto.precio_cent)
  })

  it('quitar una línea la saca de la lista y del total', () => {
    const muestra = SEMANA()
    const id = idDeLaSemana(muestra)
    const detalle = detalleDe(muestra, id)
    const linea = detalle.lineas.find((l) => l.cantidad === 1)!
    const producto = CATALOGO.find((p) => p.grupo_id === linea.grupo_id)!
    const antes = detalle.estimacion.total_cent
    cambiaLinea(muestra, id, linea.id, { borrado: true })
    const despues = detalleDe(muestra, id)
    expect(despues.lineas.some((l) => l.id === linea.id)).toBe(false)
    expect(despues.estimacion.total_cent).toBe(antes - producto.precio_cent)
  })

  it('el reparto enseña el mismo producto en varias cadenas, con su precio', () => {
    const muestra = SEMANA()
    const reparto = repartoDe(muestra, idDeLaSemana(muestra))
    const conOpciones = reparto.sin_asignar.filter((l) => l.opciones.length >= 2)
    expect(conOpciones.length).toBeGreaterThan(0)
    for (const linea of conOpciones) {
      expect(linea.hay_precio).toBe(true)
      expect(linea.coste_cent).toBeGreaterThan(0)
      for (const opcion of linea.opciones) {
        expect(opcion.cadena).toBeTruthy()
        expect(opcion.coste_cent).toBeGreaterThan(0)
      }
    }
  })

  it('el estado sobrevive a guardarlo y volverlo a leer como JSON', () => {
    const muestra = SEMANA()
    const copia = JSON.parse(JSON.stringify(muestra))
    const detalle = detalleDe(copia, idDeLaSemana(muestra))
    expect(detalle.lineas.length).toBeGreaterThan(0)
    expect(detalle.estimacion.total_cent).toBeGreaterThan(0)
  })
})

describe('los favoritos en la demo', () => {
  it('se guardan, no se duplican y se quitan', () => {
    const muestra = SEMANA()
    const producto = CATALOGO[0]
    anadeFavorito(muestra, producto.grupo_id)
    anadeFavorito(muestra, producto.grupo_id)
    const dentro = misFavoritos(muestra).favoritos
    expect(dentro.filter((f) => f.grupo_id === producto.grupo_id)).toHaveLength(1)
    expect(dentro[0].nombre).toBe(producto.nombre)
    expect(dentro[0].precio_unidad_cent).toBe(producto.precio_unidad_cent)
    quitaFavorito(muestra, producto.grupo_id)
    expect(misFavoritos(muestra).favoritos.some((f) => f.grupo_id === producto.grupo_id)).toBe(false)
  })

  it('un favorito que no está en el catálogo no se guarda a medias', () => {
    const muestra = SEMANA()
    anadeFavorito(muestra, 999999999)
    expect(misFavoritos(muestra).favoritos).toHaveLength(0)
  })
})
