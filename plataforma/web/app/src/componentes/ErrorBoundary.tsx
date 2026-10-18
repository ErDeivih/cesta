/** *** CUANDO UNA PANTALLA REVIENTA, SE DICE: no se deja en blanco. ***
 *
 *  *El 18/10/2026 la ficha de producto se quedo **en blanco** por una infraccion de hooks: React
 *  desmonto la raiz entera, el armazon incluido, **y no habia donde leerlo**.* *Nos costo diecisiete
 *  rondas.* *La leccion no es solo «arregla el hook»: es que **una excepcion de render no puede
 *  dejar la aplicacion muda**.*
 *
 *  **Lo que hace este componente**:* atrapa el error, *enseña un mensaje que se puede leer*, *da un
 *  **identificador** para poder buscarlo en la consola, *y ofrece **reintentar**.*
 *
 *  **Lo que NO hace, y es a proposito**:
 *  - *no oculta el error: lo registra (`console.error`) y sigue siendo visible en las herramientas;*
 *  - *no finge exito: la pantalla dice que algo fallo, no «todo bien»;*
 *  - *no manda nada a ningun sitio: **privacidad**; el identificador es local.*
 *
 *  *Y una advertencia que el propio encargo pide:* **«no declarar exito porque ya no esta en
 *  blanco»**.* *Que se vea el mensaje no significa que la pantalla funcione: significa que el fallo
 *  es legible.*
 */
import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  /** *Que se estaba intentando pintar, en palabras: sale en el mensaje.* */
  que?: string
}

interface Estado {
  error: Error | null
  /** *Corto y local, para poder citarlo sin copiar la traza.* */
  id: string | null
  veces: number
}

/** *Un identificador legible y **sin datos de la persona**: solo el momento.* */
function identificador(): string {
  const ahora = Date.now().toString(36).toUpperCase()
  return `F-${ahora.slice(-6)}`
}

export class ErrorBoundary extends Component<Props, Estado> {
  state: Estado = { error: null, id: null, veces: 0 }

  static getDerivedStateFromError(error: Error): Partial<Estado> {
    return { error, id: identificador() }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // *A la consola, con el mismo id, para poder cruzar el mensaje con la traza.*
    console.error('[ErrorBoundary]', this.state.id, error, info.componentStack)
  }

  private reintentar = (): void => {
    // *Se vuelve a intentar montando de nuevo: el estado del arbol se pierde, y se dice.*
    this.setState((s) => ({ error: null, id: null, veces: s.veces + 1 }))
  }

  render(): ReactNode {
    const { error, id } = this.state
    if (!error) return this.props.children
    const que = this.props.que ?? 'esta pantalla'
    return (
      <div role="alert" className="m-3 rounded-lg border border-tinta-suave p-4">
        <h2 className="text-entrada font-semibold">No he podido mostrar {que}</h2>
        <p className="mt-2 text-cuerpo text-secundaria">
          Algo ha fallado al dibujarla. El resto de la aplicación sigue funcionando y puedes volver
          atrás.
        </p>
        <p className="mt-2 text-xs text-tinta-suave">
          Referencia: <code className="tabular-nums">{id}</code> -- sale también en la consola del
          navegador, junto a la traza.
        </p>
        <p className="mt-1 text-xs text-tinta-suave">
          Reintentar vuelve a montar la pantalla desde el principio: lo que estuvieras escribiendo sin
          guardar se pierde.
        </p>
        <button
          type="button"
          onClick={this.reintentar}
          className="mt-3 rounded-md border border-tinta-suave px-3 py-2 text-cuerpo hover:bg-marfil"
        >
          Reintentar
        </button>
      </div>
    )
  }
}
