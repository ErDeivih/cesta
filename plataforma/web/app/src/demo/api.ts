/** *** LA API DE MENTIRA DE LA DEMO. *** *
 *
 *  *La demo publicada en GitHub Pages no tiene servidor ni base de datos: lleva **la muestra
 *  incrustada** (un catálogo pequeño de productos, una lista y su reparto) y aquí se responde a
 *  `/api/*` como si estuviera la API de verdad.*
 *
 *  Tres cosas, y las tres importan:
 *   - **La muestra es de datos reales** capturados de la API del proyecto (13/11/2026), no
 *     inventados: mismos nombres, precios y €/unidad.
 *   - **Los estados funcionan en la demo**: `#/compra/listas?demo=vacio`, `?demo=carga` y
 *     `?demo=error` sirven el estado vacío, la carga lenta y el error 500 de verdad, para poder
 *     enseñarlos sin servidor.
 *   - **Escribir se puede**: añadir, tachar, cambiar cantidad o cerrar la compra se aplican en
 *     memoria durante la visita (al recargar vuelve la muestra). No se promete persistencia: una
 *     demo estática no la tiene, y decirlo es parte de la demo.
 *
 *  *No sustituye a la app: la app de verdad sigue hablando con su API. Esto solo se instala en
 *  la compilación de la demo (`VITE_DEMO=1`).*
 */
import datos from './datos.json'
import {
  buscaCatalogo,
  cadenasDelCatalogo,
  FECHA_CATALOGO,
  grupoDelCatalogo,
  habitualesDelCatalogo,
  productoDelCatalogo,
  seccionesDelCatalogo,
} from './catalogo'
import {
  anadeFavorito,
  anadeLinea,
  borraLista,
  cambiaLinea,
  cierraCompra,
  creaLista,
  creaMuestra,
  detalleDe,
  dondeDe,
  misFavoritos,
  quitaFavorito,
  renombraLista,
  repartoDe,
  VERSION_MUESTRA,
  type Muestra,
} from './estadoMuestra'
import { RECETAS, recetaDe, resumenDe } from './recetas'
import { borra, guarda, lee } from './almacen'

type Cuerpo = Record<string, unknown>
type Respuesta = { estado: number; valor: unknown }

const ok = (valor: unknown): Respuesta => ({ estado: 200, valor })

const DEMO = datos as unknown as Record<string, any>
let estado: Muestra

const espera = (ms: number) => new Promise((listo) => setTimeout(listo, ms))

/** *El estado que se está enseñando, si se pidió uno por la URL.* */
function estadoForzado(): string {
  const hash = typeof window !== 'undefined' ? window.location.hash : ''
  const consulta = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : ''
  return new URLSearchParams(consulta).get('demo') ?? ''
}

/** *Los parámetros de la búsqueda, tal como los manda `useBuscar`.*

 *  *Se leen aquí y no en la pantalla porque el catálogo es de la demo: la app de verdad
 *  los manda a su API y no tiene por qué saber que existe este camino.* */
function filtrosDe(params: URLSearchParams) {
  const si = (clave: string) => params.get(clave) === 'true'
  return {
    q: params.get('q') ?? '',
    cadenas: (params.get('cadenas') ?? '').split(',').map((c) => c.trim()).filter(Boolean),
    seccion: params.get('seccion') ?? '',
    comparables: si('comparables'),
    conNutricion: si('con_nutricion'),
    ofertas: si('ofertas'),
    marcaPropia: si('marca_propia'),
    sinAlcohol: si('sin_alcohol'),
    sellos: (params.get('sellos') ?? '').split(',').map((s) => s.trim()).filter(Boolean),
    conservacion: params.get('conservacion') ?? '',
    limite: Number(params.get('limite') ?? 40),
    desplazamiento: Number(params.get('desplazamiento') ?? 0),
  }
}

function listaPorId(id: string) {
  return estado.listas.find((l) => l.id === id) ?? null
}

function respuesta(ruta: string, params: URLSearchParams, metodo: string, cuerpo: Cuerpo): Respuesta {
  const forzado = estadoForzado()

  // --- sesión y datos de la casa
  if (ruta === '/yo') return ok(estado.yo)
  if (ruta === '/entrar' || ruta === '/registrarse') return ok(estado.yo)
  if (ruta === '/estado') {
    // *Las cadenas del catálogo mandan: si una cadena no tiene ni una oferta, no puede
    // salir en el filtro como si la tuviera.*
    const cadenas = cadenasDelCatalogo()
    const suyas = (estado.estado.cadenas as { cadena: string }[] | undefined) ?? []
    return ok({
      ...estado.estado,
      cadenas: suyas.filter((c) => cadenas.includes(c.cadena)),
    })
  }
  if (ruta === '/secciones') return ok(seccionesDelCatalogo())
  if (ruta === '/habituales') {
    return ok(habitualesDelCatalogo(Number(params.get('limite') ?? 12)))
  }
  if (ruta === '/avisos/sin-ver') return ok({ sin_ver: 0 })
  if (ruta === '/alertas') return ok({ alertas: [] })
  if (ruta === '/buscar') {
    // *** LOS TRES ESTADOS DEL BUSCADOR, TAMBIÉN EN LA DEMO. *** *
    // *`?demo=vacio`, `?demo=carga` y `?demo=error` tienen que servir para enseñar la
    // pantalla sin servidor, igual que en la lista. Antes solo la lista los entendía y el
    // buscador se quedaba siempre en el caso normal.*
    if (forzado === 'error') {
      return { estado: 500, valor: { detail: 'No he podido buscar' } }
    }
    if (forzado === 'vacio') {
      return ok({ fecha_datos: FECHA_CATALOGO, resultados: [] })
    }
    return ok(buscaCatalogo(filtrosDe(params)))
  }

  // --- listas
  if (ruta === '/listas/importar' && metodo === 'POST') {
    const nombre = typeof cuerpo.nombre === 'string' ? cuerpo.nombre : 'Lista compartida'
    const lineas = Array.isArray(cuerpo.lineas) ? cuerpo.lineas : []
    const nueva = creaLista(estado, `${nombre} (compartida)`, false)
    for (const linea of lineas) {
      if (typeof linea !== 'object' || linea === null) continue
      const l = linea as Record<string, unknown>
      if (typeof l.nombre !== 'string') continue
      anadeLinea(estado, nueva.id, {
        nombre: l.nombre,
        grupoId: typeof l.grupo_id === 'number' ? l.grupo_id : null,
        productoId: typeof l.producto_id === 'string' ? l.producto_id : null,
        cantidad: typeof l.cantidad === 'number' ? l.cantidad : 1,
        nota: typeof l.nota === 'string' ? l.nota : null,
      })
    }
    return ok({ lista: nueva })
  }
  if (ruta === '/listas') {
    if (metodo === 'POST') {
      return ok(creaLista(
        estado,
        typeof cuerpo.nombre === 'string' ? cuerpo.nombre : 'Lista',
        cuerpo.es_de_casa === true,
      ))
    }
    if (forzado === 'vacio') return ok({ listas: [] })
    if (forzado === 'error') {
      return { estado: 500, valor: { detail: 'No he podido traer tus listas' } }
    }
    return ok({ listas: estado.listas })
  }

  const deLista = ruta.match(/^\/listas\/([^/]+)(?:\/(.*))?$/)
  if (deLista) {
    const [, id, resto = ''] = deLista
    const lista = listaPorId(id)
    if (!lista) return { estado: 404, valor: { detail: 'Esa lista no existe' } }

    if (resto === '') {
      if (metodo === 'DELETE') return ok({ borrada: borraLista(estado, id) })
      if (metodo === 'PATCH') {
        return ok({ nombre: renombraLista(estado, id, String(cuerpo.nombre ?? lista.nombre)) })
      }
      return ok(detalleDe(estado, id))
    }
    if (resto === 'donde') return ok(dondeDe(estado, id))
    if (resto === 'reparto') return ok(repartoDe(estado, id))
    if (resto === 'gasto') return ok(DEMO.gasto)
    if (resto === 'repetir-compra') {
      return metodo === 'GET'
        ? ok(DEMO.repetirCompra)
        : ok({ anadidos: 0, ya_estaban: 0, sin_catalogo: 0, faltan: 0 })
    }
    if (resto === 'cerrar') return ok(cierraCompra(estado, id))
    if (resto === 'sincronizar') return ok({ aplicados: 0, fallidos: [] })
    if (resto === 'tienda') return ok({})

    if (resto === 'desde-favoritos' && metodo === 'POST') {
      const grupos = Array.isArray(cuerpo.grupo_ids) ? cuerpo.grupo_ids : []
      let anadidos = 0
      for (const grupoId of grupos) {
        if (typeof grupoId !== 'number') continue
        const producto = grupoDelCatalogo(grupoId)
        if (!producto) continue
        anadeLinea(estado, id, {
          nombre: producto.nombre,
          grupoId,
          productoId: null,
        })
        anadidos += 1
      }
      return ok({ anadidos })
    }

    if (resto === 'lineas' && metodo === 'POST') {
      anadeLinea(estado, id, {
        // *El id lo manda el cliente para que reintentar actualice en vez de duplicar.*
        id: typeof cuerpo.id === 'string' ? cuerpo.id : undefined,
        nombre: typeof cuerpo.nombre === 'string' ? cuerpo.nombre : 'Producto',
        grupoId: typeof cuerpo.grupo_id === 'number' ? cuerpo.grupo_id : null,
        productoId: typeof cuerpo.producto_id === 'string' ? cuerpo.producto_id : null,
        cantidad: typeof cuerpo.cantidad === 'number' ? cuerpo.cantidad : 1,
        nota: typeof cuerpo.nota === 'string' ? cuerpo.nota : null,
      })
      return ok({})
    }

    const deLinea = resto.match(/^lineas\/([^/]+)(?:\/(.*))?$/)
    if (deLinea) {
      const [, idLinea, accion = ''] = deLinea
      // *Autorizar o aceptar una alternativa no existe en la demo: se contesta sin tocar
      // nada. Lo que sí se escribe es lo de abajo.*
      if (accion !== '') return ok({})
      const cambiado = cambiaLinea(estado, id, idLinea, {
        borrado: cuerpo.borrado === true,
        cantidad: typeof cuerpo.cantidad === 'number' ? cuerpo.cantidad : undefined,
        nota: 'nota' in cuerpo ? (typeof cuerpo.nota === 'string' ? cuerpo.nota : null) : undefined,
        tachado: typeof cuerpo.tachado === 'boolean' ? cuerpo.tachado : undefined,
        en_carrito: typeof cuerpo.en_carrito === 'boolean' ? cuerpo.en_carrito : undefined,
      })
      return cambiado ? ok({}) : { estado: 404, valor: { detail: 'Esa línea no existe' } }
    }
    return ok({})
  }

  // --- recetas
  // *`usePreviaDeCompra` llama a `/api/recetas/...` y `pide` ya pone `/api`: se aceptan las dos
  // formas para no romper la pantalla por un prefijo repetido.*
  const rutaRecetas = ruta.startsWith('/api/') ? ruta.slice('/api'.length) : ruta
  if (rutaRecetas === '/recetas' && metodo === 'GET') {
    return ok({ recetas: RECETAS.map(resumenDe) })
  }
  const deReceta = rutaRecetas.match(/^\/recetas\/(\d+)(?:\/(.*))?$/)
  if (deReceta) {
    const id = Number(deReceta[1])
    const resto = deReceta[2] ?? ''
    if (resto === 'versiones') return ok({ versiones: [1] })
    if (resto === 'a-la-lista') {
      if (metodo === 'GET') {
        const receta = recetaDe(id)
        if (!receta) return { estado: 404, valor: { detail: 'Esa receta no existe' } }
        return ok({
          version: 1,
          raciones: receta.raciones,
          lineas: receta.ingredientes.map((i) => ({
            texto: i.texto,
            cantidad: i.cantidad,
            unidad: i.unidad,
            grupo_id: i.grupo_id,
            producto_id: i.producto_id,
          })),
          sin_cantidad: [],
          sin_consolidar: [],
          nota: 'Se añadirán los ingredientes de la receta a la lista.',
        })
      }
      const listaId = typeof cuerpo.lista_id === 'string' ? cuerpo.lista_id : ''
      const receta = recetaDe(id)
      if (!receta || !listaPorId(listaId)) {
        return { estado: 404, valor: { detail: 'Esa receta o esa lista no existe' } }
      }
      for (const ingrediente of receta.ingredientes) {
        anadeLinea(estado, listaId, {
          nombre: ingrediente.texto,
          grupoId: ingrediente.grupo_id ?? null,
          productoId: ingrediente.producto_id ?? null,
          cantidad: 1,
        })
      }
      return ok({ anadidos: receta.ingredientes.length })
    }
    if (resto === '' && metodo === 'GET') {
      const receta = recetaDe(id, Number(params.get('raciones') ?? 0) || null)
      return receta
        ? ok(receta)
        : { estado: 404, valor: { detail: 'Esa receta no existe' } }
    }
  }

  // --- favoritos
  if (ruta === '/favoritos') {
    if (metodo === 'GET') {
      const dias = Number(params.get('dias') ?? 7)
      return ok(misFavoritos(estado, Number.isFinite(dias) ? dias : 7))
    }
    const grupoId = typeof cuerpo.grupo_id === 'number' ? cuerpo.grupo_id : null
    if (metodo === 'POST') {
      return ok({ hecho: grupoId !== null && anadeFavorito(estado, grupoId) })
    }
    if (metodo === 'DELETE') {
      return ok({ hecho: grupoId !== null && quitaFavorito(estado, grupoId) })
    }
  }

  const deGrupo = ruta.match(/^\/grupo\/(\d+)$/)
  if (deGrupo) {
    const grupo = grupoDelCatalogo(Number(deGrupo[1]))
    return grupo
      ? ok(grupo)
      : { estado: 404, valor: { detail: 'Ese producto no está en la muestra' } }
  }
  const deProducto = ruta.match(/^\/producto\/([^/]+)\/([^/]+)$/)
  if (deProducto) {
    const ficha = productoDelCatalogo(
      decodeURIComponent(deProducto[1]),
      decodeURIComponent(deProducto[2]),
    )
    return ficha
      ? ok(ficha)
      : { estado: 404, valor: { detail: 'Ese producto no está en la muestra' } }
  }

  // *Lo que la demo no trae (panel, avisos, recetas) no puede tumbar la app: se contesta vacío
  // y cada pantalla enseña su propio estado vacío.*
  return ok({})
}

/** Instala la API de la demo **antes** de que arranque React.
 *
 *  *Es asíncrona porque primero mira lo que quedó guardado en el dispositivo: la primera visita
 *  siembra la muestra y las siguientes parten de lo que la persona dejó. `?demo=reset` borra lo
 *  guardado y siembra de nuevo.*
 */
export async function instalaApiDemo(): Promise<void> {
  if (typeof window === 'undefined') return
  const ventana = window as unknown as Record<string, unknown>
  if (ventana.__cestaDemoApi) return
  ventana.__cestaDemoApi = true
  estado = creaMuestra()

  if (estadoForzado() === 'reset') await borra()
  const guardado = (await lee()) as { version?: number; datos?: Muestra } | null
  if (guardado && guardado.version === VERSION_MUESTRA && guardado.datos) {
    estado = guardado.datos
  } else {
    await guarda({ version: VERSION_MUESTRA, datos: estado })
  }

  const original = window.fetch.bind(window)
  window.fetch = async (recurso: RequestInfo | URL, opciones?: RequestInit) => {
    const url = typeof recurso === 'string'
      ? recurso
      : recurso instanceof URL
        ? recurso.toString()
        : recurso.url
    const destino = new URL(url, window.location.origin)
    if (!destino.pathname.startsWith('/api/')) return original(recurso, opciones)

    const metodo = String(
      opciones?.method ?? (recurso instanceof Request ? recurso.method : 'GET'),
    ).toUpperCase()
    let cuerpo: Cuerpo = {}
    if (typeof opciones?.body === 'string') {
      try {
        cuerpo = JSON.parse(opciones.body) as Cuerpo
      } catch {
        cuerpo = {}
      }
    }

    const ruta = destino.pathname.slice('/api'.length)
    // *La carga lenta se pide con `?demo=carga`; sin eso, un respiro corto para que se vean los
    // esqueletos.*
    if (estadoForzado() === 'carga' && (ruta === '/listas' || ruta === '/buscar')) {
      await espera(3500)
    } else {
      await espera(180)
    }

    const r = respuesta(ruta, destino.searchParams, metodo, cuerpo)
    // *Lo que se escribe se guarda en el dispositivo: al recargar sigue ahí.*
    if (metodo !== 'GET' && r.estado < 400) {
      void guarda({ version: VERSION_MUESTRA, datos: estado })
    }
    return new Response(JSON.stringify(r.valor), {
      status: r.estado,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  // *`?demo=reset` también desde la propia demo: al cambiar el hash se borra lo guardado y se
  // recarga para volver a sembrar la muestra (sin esto, cambiar solo el hash no reinstala nada).*
  window.addEventListener('hashchange', () => {
    if (estadoForzado() === 'reset') {
      void borra().then(() => window.location.reload())
    }
  })
}
