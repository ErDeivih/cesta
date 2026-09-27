import { useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'

import { Cabecera } from './componentes/Cabecera'
import { NavAbajo } from './componentes/Nav'
import { SUFIJO } from './componentes/Titulo'
import { Vacio } from './componentes/ui'
import { Ajustes } from './paginas/Ajustes'
import { Avisos } from './paginas/Avisos'
import { Buscar } from './paginas/Buscar'
import { Cesta } from './paginas/Cesta'
import { Escaner } from './paginas/Escaner'
import { Favoritos } from './paginas/Favoritos'
import { Grupo } from './paginas/Grupo'
import { Inicio } from './paginas/Inicio'
import { Panel } from './paginas/Panel'
import { PanelMatching } from './paginas/PanelMatching'
import { Producto } from './paginas/Producto'
import { Unirse } from './paginas/Unirse'

/** El titulo de la pestana por ruta. Lo de dentro lo mejora si sabe mas.
 *
 *  La ficha y el grupo ponen **el nombre del producto** cuando su dato llega
 *  (`useTitulo`), porque "Producto" y "Leche entera Hacendado" no se parecen en nada
 *  cuando hay diez pestanas abiertas. Aqui esta el titulo de arranque de cada ruta,
 *  que es el que se ve mientras el dato viaja.
 */
export function tituloDe(ruta: string): string {
  // `/` es **Inicio** desde el 27 de septiembre de 2026: la pantalla que contesta las cuatro
  // preguntas sin entrar en ninguna otra. El buscador sigue en `/buscar`.
  if (ruta === '/') return 'Inicio'
  if (ruta.startsWith('/buscar')) return 'Buscar'
  if (ruta.startsWith('/grupo/') || ruta.startsWith('/producto/')) return 'Producto'
  if (ruta.startsWith('/escaner')) return 'Escáner'
  if (ruta.startsWith('/cesta')) return 'La cesta'
  if (ruta.startsWith('/favoritos')) return 'Favoritos'
  if (ruta.startsWith('/ajustes')) return 'Ajustes'
  if (ruta.startsWith('/panel/matching')) return 'Matching'
  if (ruta.startsWith('/panel')) return 'Panel'
  if (ruta.startsWith('/avisos')) return 'Avisos'
  if (ruta.startsWith('/unirme/')) return 'Invitación'
  return 'Cesta'
}

/** El armazon de la app: cabecera pegada arriba, contenido y barra abajo.
 *
 *  `pb-24` en el main es el hueco de la barra de abajo en el movil: sin el, el
 *  ultimo resultado de una lista queda debajo de la barra y no se puede pulsar.
 */
export function App() {
  const { pathname } = useLocation()

  useEffect(() => {
    const nombre = tituloDe(pathname)
    document.title = nombre === 'Cesta' ? 'Cesta' : `${nombre} ${SUFIJO}`
  }, [pathname])

  return (
    <div className="flex min-h-screen flex-col">
      <Cabecera />
      <main className="mx-auto w-full max-w-app flex-1 px-4 pb-28 pt-4 lg:pb-10">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/buscar" element={<Buscar />} />
          <Route path="/grupo/:grupoId" element={<Grupo />} />
          <Route path="/producto/:fuente/:idFuente" element={<Producto />} />
          <Route path="/escaner" element={<Escaner />} />
          <Route path="/cesta" element={<Cesta />} />
          <Route path="/avisos" element={<Avisos />} />
          {/* La ruta que devuelve la API al crear una invitacion
              (`/unirme/<codigo>`, main.py:500). Caddy sirve `index.html` para
              cualquier ruta que no sea un fichero (`try_files {path}`,
              Caddyfile), asi que este enlace funciona tambien si se pega tal
              cual en el navegador, sin pasar por el buscador. */}
          <Route path="/unirme/:codigo" element={<Unirse />} />
          <Route path="/favoritos" element={<Favoritos />} />
          <Route path="/ajustes" element={<Ajustes />} />
          <Route path="/panel" element={<Panel />} />
          <Route path="/panel/matching" element={<PanelMatching />} />
          <Route
            path="*"
            element={
              <Vacio titulo="Esa pantalla no existe" comoPagina>
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
