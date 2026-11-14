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

type Cuerpo = Record<string, unknown>
type Respuesta = { estado: number; valor: unknown }

const ok = (valor: unknown): Respuesta => ({ estado: 200, valor })

const DEMO = datos as unknown as Record<string, any>
let estado: Record<string, any>

const espera = (ms: number) => new Promise((listo) => setTimeout(listo, ms))

/** *El estado que se está enseñando, si se pidió uno por la URL.* */
function estadoForzado(): string {
  const hash = typeof window !== 'undefined' ? window.location.hash : ''
  const consulta = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : ''
  return new URLSearchParams(consulta).get('demo') ?? ''
}

function normaliza(texto: string): string {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

/** Busca en la muestra con las mismas reglas de andar por casa que la demo necesita. */
function busca(texto: string, limite: number) {
  const agujas = normaliza(texto).split(/\s+/).filter(Boolean)
  if (agujas.length === 0) return []
  return (estado.busquedas as Record<string, any>[])
    .filter((r) => {
      const heno = normaliza(`${r.nombre ?? ''} ${r.marca ?? ''}`)
      return agujas.every((a) => heno.includes(a))
    })
    .slice(0, limite)
}

function listaPorId(id: string) {
  return (estado.listas.listas as Record<string, any>[]).find((l) => l.id === id) ?? null
}

/** El detalle de la lista de la muestra; una lista recién creada nace vacía. */
function detalleDe(id: string) {
  const original = estado.detalle as Record<string, any>
  if (id === original.id) return original
  return {
    papel: 'dueno',
    lineas: [],
    estimacion: { total_cent: 0, en_carrito_cent: 0, por_recoger_cent: 0, lineas: 0, sin_precio: 0 },
    personas: [],
    novedades: [],
    fecha_datos: original.fecha_datos,
  }
}

function respuesta(ruta: string, params: URLSearchParams, metodo: string, cuerpo: Cuerpo): Respuesta {
  const forzado = estadoForzado()

  // --- sesión y datos de la casa
  if (ruta === '/yo') return ok(estado.yo)
  if (ruta === '/entrar' || ruta === '/registrarse') return ok(estado.yo)
  if (ruta === '/estado') return ok(estado.estado)
  if (ruta === '/secciones') return ok(estado.secciones)
  if (ruta === '/habituales') return ok(estado.habituales)
  if (ruta === '/avisos/sin-ver') return ok({ sin_ver: 0 })
  if (ruta === '/alertas') return ok({ alertas: [] })
  if (ruta === '/buscar') {
    const limite = Number(params.get('limite') ?? 40)
    return ok({
      fecha_datos: estado.estado?.fecha_datos ?? '2026-11-13',
      resultados: busca(params.get('q') ?? '', Number.isFinite(limite) ? limite : 40),
    })
  }

  // --- listas
  if (ruta === '/listas') {
    if (metodo === 'POST') {
      const nueva = {
        id: crypto.randomUUID(),
        nombre: typeof cuerpo.nombre === 'string' ? cuerpo.nombre : 'Lista',
        es_de_casa: cuerpo.es_de_casa === true,
        lineas: 0,
      }
      estado.listas.listas.push(nueva)
      return ok(nueva)
    }
    if (forzado === 'vacio') return ok({ listas: [] })
    if (forzado === 'error') {
      return { estado: 500, valor: { detail: 'No he podido traer tus listas' } }
    }
    return ok(estado.listas)
  }

  const deLista = ruta.match(/^\/listas\/([^/]+)(?:\/(.*))?$/)
  if (deLista) {
    const [, id, resto = ''] = deLista
    const lista = listaPorId(id)
    if (!lista) return { estado: 404, valor: { detail: 'Esa lista no existe' } }
    const detalle = detalleDe(id)

    if (resto === '') {
      if (metodo === 'DELETE') {
        estado.listas.listas = estado.listas.listas.filter((l: any) => l.id !== id)
        return ok({})
      }
      if (metodo === 'PATCH') {
        if (typeof cuerpo.nombre === 'string') lista.nombre = cuerpo.nombre
        return ok({})
      }
      return ok(detalle)
    }
    if (resto === 'donde') return ok(estado.donde)
    if (resto === 'reparto') return ok(estado.reparto)
    if (resto === 'gasto') return ok(estado.gasto)
    if (resto === 'repetir-compra') {
      return metodo === 'GET'
        ? ok(estado.repetirCompra)
        : ok({ anadidos: 0, ya_estaban: 0, sin_catalogo: 0, faltan: 0 })
    }
    if (resto === 'cerrar') {
      const tachadas = (detalle.lineas as any[]).filter((l) => l.tachado_en !== null)
      detalle.lineas = (detalle.lineas as any[]).filter((l) => l.tachado_en === null)
      lista.lineas = detalle.lineas.length
      return ok({
        lineas: tachadas.length,
        total_cent: 0,
        quedan: detalle.lineas.length,
        sin_precio: 0,
        diferencia_cent: null,
      })
    }
    if (resto === 'sincronizar') return ok({ aplicados: 0, fallidos: [] })
    if (resto === 'tienda') return ok({})

    if (resto === 'lineas' && metodo === 'POST') {
      const idLinea = typeof cuerpo.id === 'string' ? cuerpo.id : crypto.randomUUID()
      detalle.lineas.push({
        id: idLinea,
        nombre_visto: typeof cuerpo.nombre === 'string' ? cuerpo.nombre : 'Producto',
        cantidad: typeof cuerpo.cantidad === 'number' ? cuerpo.cantidad : 1,
        nota: typeof cuerpo.nota === 'string' ? cuerpo.nota : null,
        grupo_id: typeof cuerpo.grupo_id === 'number' ? cuerpo.grupo_id : null,
        producto_id: typeof cuerpo.producto_id === 'string' ? cuerpo.producto_id : null,
        tachado_en: null,
      })
      lista.lineas = detalle.lineas.length
      return ok({})
    }

    const deLinea = resto.match(/^lineas\/([^/]+)(?:\/(.*))?$/)
    if (deLinea) {
      const [, idLinea, accion = ''] = deLinea
      const cual = (detalle.lineas as any[]).find((l) => l.id === idLinea)
      if (!cual) return { estado: 404, valor: { detail: 'Esa línea no existe' } }
      if (accion !== '') return ok({})
      if (cuerpo.borrado === true) {
        detalle.lineas = (detalle.lineas as any[]).filter((l) => l.id !== idLinea)
      } else {
        if (typeof cuerpo.cantidad === 'number') cual.cantidad = cuerpo.cantidad
        if ('nota' in cuerpo) cual.nota = cuerpo.nota
        if (typeof cuerpo.tachado === 'boolean' || typeof cuerpo.en_carrito === 'boolean') {
          const dentro = cuerpo.tachado === true || cuerpo.en_carrito === true
          cual.tachado_en = dentro ? new Date().toISOString() : null
        }
      }
      lista.lineas = detalle.lineas.length
      return ok({})
    }
    return ok({})
  }

  if (ruta.startsWith('/grupo/')) {
    const grupo = estado.grupos[ruta.slice('/grupo/'.length)]
    return grupo ? ok(grupo) : { estado: 404, valor: { detail: 'Sin grupo' } }
  }
  if (ruta.startsWith('/producto/')) return ok({})

  // *Lo que la demo no trae (panel, avisos, recetas) no puede tumbar la app: se contesta vacío
  // y cada pantalla enseña su propio estado vacío.*
  return ok({})
}

/** Instala la API de la demo **antes** de que arranque React. */
export function instalaApiDemo(): void {
  if (typeof window === 'undefined') return
  const ventana = window as unknown as Record<string, unknown>
  if (ventana.__cestaDemoApi) return
  ventana.__cestaDemoApi = true
  estado = structuredClone(DEMO)

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
    if (estadoForzado() === 'carga' && ruta === '/listas') await espera(3500)
    else await espera(180)

    const r = respuesta(ruta, destino.searchParams, metodo, cuerpo)
    return new Response(JSON.stringify(r.valor), {
      status: r.estado,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
