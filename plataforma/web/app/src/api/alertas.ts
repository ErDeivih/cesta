/** Los avisos de precio: pedirlos, verlos y quitarlos.
 *
 *  `GET/POST/DELETE /api/alertas` y `POST /api/alertas/vistas`, que llevan sesion
 *  porque una alerta es de una persona.
 *
 *  **Lo importante de este fichero no es lo que pide, es lo que NO inventa.** La
 *  condicion la decide el servidor (`alertas.evalua`, que es el unico sitio que sabe de
 *  precios y de las cuatro condiciones que hacen que una bajada sea una bajada), y la
 *  fecha en que salto la pone el **vigilante** en cuanto cambia gold -- no cuando
 *  alguien abre esta pantalla. Aqui solo se pinta lo que llega: la frase que ya estaba
 *  guardada, o la que se calcula ahora mismo para las que acaban de cumplirse.
 *
 *  `escribe` se importa de `./cesta` y no se copia: es la misma puerta para todo lo que
 *  escribe (cookie, mismo origen, `detail` de la API subido tal cual), y tener dos
 *  puertas es tener dos sitios donde arreglar el mismo fallo.
 */
import { escribe } from './cesta'
import { pide } from './cliente'
import type { Alerta, RespuestaAlertas } from '../tipos'

/** Las mias, con lo que salta hoy y lo que salto sin que yo mirara. */
export function misAlertas(): Promise<RespuestaAlertas> {
  return pide<RespuestaAlertas>('/alertas')
}

/** Pide que te avisen de un grupo.
 *
 *  El tipo por defecto es `minimo_90d`, y no es un detalle: es el unico que **no exige
 *  saber cuanto deberia costar algo**, que es justo lo que casi nadie sabe hasta que ve
 *  la curva. `baja_de` existe para quien si lo sabe.
 */
export function crearAlerta(grupoId: number, tipo = 'minimo_90d',
                            umbralCent?: number): Promise<Alerta> {
  return escribe<Alerta>('/alertas', 'POST', {
    grupo_id: grupoId, tipo,
    ...(umbralCent ? { umbral_cent: umbralCent } : {}),
  })
}

export function borrarAlerta(alertaId: string): Promise<void> {
  return escribe<void>(`/alertas/${encodeURIComponent(alertaId)}`, 'DELETE')
}

/** Ya lo he visto. Es lo que apaga el punto del icono.
 *
 *  Va aparte de leerlas a proposito (`main.py`): abrir la pantalla en el autobus no
 *  puede dar por contado lo que no se ha leido.
 */
export function marcarVistas(ids: string[]): Promise<{ marcadas: number }> {
  return escribe<{ marcadas: number }>('/alertas/vistas', 'POST', { ids })
}
