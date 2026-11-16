/** *** EL FLUJO DE LA COMPRA EN LA DEMO, DE PRINCIPIO A FIN. *** *
 *
 *  *Las pruebas de `catalogo.test.ts` y `estadoMuestra.test.ts` prueban las piezas por
 *  separado. Esta es la que las usa como las usa una persona: **busca** «leche», **añade** lo
 *  que encuentra, mira **la lista** con su total y **compara** el mismo producto entre
 *  cadenas. Si una pieza cambia de forma y las otras no, aquí se ve.*
 *
 *  *Es el flujo que la demo publicada tenía roto: encontraba la búsqueda, pero no había
 *  producto que añadir con precio, ni lista que sumara, ni comparación detrás.*
 */
import { describe, expect, it } from 'vitest'

import { buscaCatalogo, grupoDelCatalogo } from './catalogo'
import { anadeLinea, creaMuestra, detalleDe, repartoDe } from './estadoMuestra'

describe('búsqueda → añadir → lista → comparación', () => {
  it('el recorrido entero, con el catálogo y la lista de la semana', () => {
    const muestra = creaMuestra()
    const semana = muestra.listas.find((l) => l.es_de_casa)!
    expect(semana).toBeTruthy()

    // 1. BUSCAR: lo que se teclea en el buscador o en el typeahead.
    const busqueda = buscaCatalogo({ q: 'leche', limite: 8 })
    expect(busqueda.resultados.length).toBeGreaterThan(0)
    const elegido = busqueda.resultados[0]

    // 2. AÑADIR: lo que hace el botón de la ficha o la sugerencia del typeahead.
    const antes = detalleDe(muestra, semana.id).estimacion.total_cent
    anadeLinea(muestra, semana.id, {
      nombre: elegido.nombre,
      grupoId: elegido.grupo_id,
      productoId: null,
    })

    // 3. LA LISTA: la línea está, con su nombre y su precio, y el total ha subido lo que vale.
    const detalle = detalleDe(muestra, semana.id)
    const linea = detalle.lineas.find(
      (l) => l.grupo_id === elegido.grupo_id && l.nombre_visto === elegido.nombre,
    )
    expect(linea, 'la línea añadida no está en la lista').toBeTruthy()
    expect(detalle.estimacion.total_cent).toBe(antes + (elegido.precio_cent as number))
    expect(detalle.estimacion.sin_precio).toBe(0)

    // 4. COMPARAR: el mismo producto, cadena a cadena, con su precio por unidad.
    const reparto = repartoDe(muestra, semana.id)
    const enLaLista = reparto.sin_asignar.find((l) => l.linea_id === linea!.id)!
    expect(enLaLista.hay_precio).toBe(true)
    expect(enLaLista.opciones.length).toBeGreaterThanOrEqual(2)
    expect(enLaLista.mas_barata).toBeTruthy()

    const grupo = grupoDelCatalogo(elegido.grupo_id as number)!
    const unidades = grupo.productos.map((p) => p.precio_unidad_cent as number)
    expect(Math.min(...unidades)).toBe(elegido.precio_unidad_cent as number)
    for (const producto of grupo.productos) {
      expect(producto.fuente).toBeTruthy()
      expect(producto.precio_cent).toBeGreaterThan(0)
      expect(producto.precio_unidad_cent).toBeGreaterThan(0)
    }
  })

  it('el recorrido también con una búsqueda de las que antes daban cero', () => {
    // *«arroz» era la prueba del fallo publicado: 0 resultados el 16/11/2026. Ahora
    // encuentra, se añade y la lista lo suma.*
    const muestra = creaMuestra()
    const semana = muestra.listas.find((l) => l.es_de_casa)!
    const { resultados } = buscaCatalogo({ q: 'arroz', limite: 8 })
    expect(resultados.length).toBeGreaterThan(0)
    const arroz = resultados[0]
    anadeLinea(muestra, semana.id, {
      nombre: arroz.nombre,
      grupoId: arroz.grupo_id,
      productoId: null,
    })
    const detalle = detalleDe(muestra, semana.id)
    expect(detalle.lineas.some((l) => l.nombre_visto === arroz.nombre)).toBe(true)
    expect(detalle.estimacion.total_cent).toBeGreaterThan(1706)
  })
})
