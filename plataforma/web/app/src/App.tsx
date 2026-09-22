import { Link, Route, Routes } from 'react-router-dom'

import { Cabecera } from './componentes/Cabecera'
import { NavAbajo } from './componentes/Nav'
import { Vacio } from './componentes/ui'
import { Buscar } from './paginas/Buscar'
import { Cesta } from './paginas/Cesta'
import { Escaner } from './paginas/Escaner'
import { Favoritos } from './paginas/Favoritos'
import { Grupo } from './paginas/Grupo'
import { Panel } from './paginas/Panel'
import { PanelMatching } from './paginas/PanelMatching'
import { Producto } from './paginas/Producto'

/** El armazon de la app: cabecera pegada arriba, contenido y barra abajo.
 *
 *  `pb-24` en el main es el hueco de la barra de abajo en el movil: sin el, el
 *  ultimo resultado de una lista queda debajo de la barra y no se puede pulsar.
 */
export function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Cabecera />
      <main className="mx-auto w-full max-w-app flex-1 px-4 pb-28 pt-4 lg:pb-10">
        <Routes>
          <Route path="/" element={<Buscar />} />
          <Route path="/grupo/:grupoId" element={<Grupo />} />
          <Route path="/producto/:fuente/:idFuente" element={<Producto />} />
          <Route path="/escaner" element={<Escaner />} />
          <Route path="/cesta" element={<Cesta />} />
          <Route path="/favoritos" element={<Favoritos />} />
          <Route path="/panel" element={<Panel />} />
          <Route path="/panel/matching" element={<PanelMatching />} />
          <Route
            path="*"
            element={
              <Vacio titulo="Esa pantalla no existe">
                <p>
                  Puede que el enlace esté mal escrito. <Link to="/" className="underline">Vuelve al
                  buscador</Link>.
                </p>
              </Vacio>
            }
          />
        </Routes>
      </main>
      <NavAbajo />
    </div>
  )
}
