/** *** COMPARTIR UNA LISTA POR ENLACE, SIN SERVIDOR. *** *
 *
 *  *La demo no tiene backend, así que el enlace lleva la lista dentro: se serializa a JSON, se
 *  pasa a base64url y viaja en `#/compra/listas?compartir=...`. Al abrirlo, la demo crea una
 *  lista local con esas líneas.*
 *
 *  *No viaja el precio ni el nombre de la cadena: el que lo abre recalcula con su catálogo. Lo
 *  que viaja es lo que hay que comprar y cuánto, que es lo que se comparte.*
 */
import type { Linea } from '../tipos'

export interface ListaCompartida {
  v: 1
  nombre: string
  lineas: {
    nombre: string
    cantidad: number
    nota: string | null
    grupo_id: number | null
    producto_id: string | null
  }[]
}

/** *El JSON a base64url. `btoa` trabaja con bytes; el texto va en UTF-8 para que «Atún» no se
 *  rompa al pasar por el enlace.* */
function aBase64Url(texto: string): string {
  const bytes = new TextEncoder().encode(texto)
  let binario = ''
  for (const byte of bytes) binario += String.fromCharCode(byte)
  return btoa(binario).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function deBase64Url(texto: string): string {
  const normal = texto.replace(/-/g, '+').replace(/_/g, '/')
  const relleno = normal + '='.repeat((4 - (normal.length % 4)) % 4)
  const binario = atob(relleno)
  const bytes = new Uint8Array(binario.length)
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i)
  return new TextDecoder().decode(bytes)
}

export function codificaLista(nombre: string, lineas: Linea[]): string {
  const datos: ListaCompartida = {
    v: 1,
    nombre: nombre.trim() || 'Lista compartida',
    lineas: lineas.map((l) => ({
      nombre: l.nombre_visto,
      cantidad: l.cantidad,
      nota: l.nota ?? null,
      grupo_id: l.grupo_id,
      producto_id: l.producto_id,
    })),
  }
  return aBase64Url(JSON.stringify(datos))
}

/** *Lo que viene de un enlace, si es una lista válida. Cualquier cosa rara devuelve `null`: no se
 *  importa a medias un enlace roto.* */
export function decodificaLista(texto: string): ListaCompartida | null {
  try {
    const datos = JSON.parse(deBase64Url(texto)) as Partial<ListaCompartida>
    if (datos.v !== 1 || typeof datos.nombre !== 'string' || !Array.isArray(datos.lineas)) {
      return null
    }
    const lineas = datos.lineas
      .filter((l): l is ListaCompartida['lineas'][number] =>
        typeof l === 'object' && l !== null && typeof l.nombre === 'string')
      .map((l) => ({
        nombre: l.nombre.slice(0, 200),
        cantidad: Math.max(1, Math.min(99, Math.round(Number(l.cantidad) || 1))),
        nota: typeof l.nota === 'string' ? l.nota.slice(0, 200) : null,
        grupo_id: typeof l.grupo_id === 'number' ? l.grupo_id : null,
        producto_id: typeof l.producto_id === 'string' ? l.producto_id : null,
      }))
    if (lineas.length === 0 || lineas.length > 200) return null
    return { v: 1, nombre: datos.nombre.slice(0, 120), lineas }
  } catch {
    return null
  }
}
