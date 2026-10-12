/** Las rutas de la suite: lanzador, tres aplicaciones y las pantallas de siempre.
 *
 *  **`/` es un lanzador sobrio desde el 7 de octubre de 2026.** Antes era "Inicio", que contestaba
 *  cuatro preguntas del dia; esas respuestas viven ahora en **Compra**, que es la aplicacion a la que
 *  pertenecen. El lanzador no mezcla graficas ni datos privados: tres accesos y donde te quedaste.
 *
 *  **Las direcciones antiguas siguen funcionando, con su query.** Hay enlaces fuera del proyecto
 *  -- lectores de codigos pegados en el movil, invitaciones que manda la API -- y romperlos para
 *  dejar bonitas las rutas nuevas seria cambiar un problema de nombres por uno de enlaces rotos.
 *  Y perder la query es perder lo que el usuario acaba de escribir (`?q=leche&cadenas=dia,...`).
 *
 *  **Que no se ha hecho todavia, y se dice:** las secciones internas de Recetas y Calorias siguen
 *  servidas por la misma pantalla de cocina con un `modo`, que es lo que el encargo manda eliminar.
 *  Partirlas es S08 y S09, con su almacenamiento propio; aqui ya tienen armazon, menu y rutas, que
 *  es lo que S06 pide.
 */
import { useEffect } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import { APLICACIONES, LayoutSuite, aplicacionDe, tituloDeSeccion } from './componentes/Suite'
import { SUFIJO } from './componentes/Titulo'
import { Vacio } from './componentes/ui'
import { Ajustes } from './paginas/Ajustes'
import { Avisos } from './paginas/Avisos'
import { Buscar } from './paginas/Buscar'
import { Cesta } from './paginas/Cesta'
import { Cocina, CocinaProvider } from './paginas/Cocina'
import { Escaner } from './paginas/Escaner'
import { Diario } from './paginas/Diario'
import { Tendencias } from './paginas/Tendencias'
import { ImportarReceta } from './paginas/ImportarReceta'
import { CocinaModo } from './paginas/CocinaModo'
import { Despensa } from './paginas/Despensa'
import { Favoritos } from './paginas/Favoritos'
import { Grupo } from './paginas/Grupo'
import { Panel } from './paginas/Panel'
import { PanelMatching } from './paginas/PanelMatching'
import { Producto } from './paginas/Producto'
import { Recetario } from './paginas/Recetario'
import { RecetaDetalle } from './paginas/RecetaDetalle'
import { PlanSemanal } from './paginas/PlanSemanal'
import { Unirse } from './paginas/Unirse'

const CLAVE_ULTIMO = 'cesta.ultimo'

/** El lanzador: tres accesos y por donde ibas. Sin graficas ni datos de nadie. */
function Lanzador() {
  const navegar = useNavigate()
  const { search } = useLocation()
  const ultimo = typeof localStorage !== 'undefined' ? localStorage.getItem(CLAVE_ULTIMO) : null
  const aplicacion = ultimo ? aplicacionDe(ultimo) : null

  return (
    <div className="mx-auto flex min-h-screen max-w-app flex-col gap-10 px-5 py-10">
      <header className="border-b border-borde pb-6">
        <h1 className="font-serif text-[32px] leading-[38px] font-semibold text-tinta-fuerte">Cesta</h1>
        <p className="mt-1 text-[15px] text-secundaria">
          La compra de casa, las recetas y lo que comes. Tres aplicaciones, una casa.
        </p>
      </header>

      {aplicacion && (
        <button
          type="button"
          onClick={() => navegar(ultimo ?? aplicacion.raiz)}
          className="min-h-[44px] self-start rounded-md border border-borde-fuerte px-4 text-[15px] text-tinta-fuerte hover:bg-papel"
        >
          Continuar donde estaba: <strong>{aplicacion.nombre}</strong>
        </button>
      )}

      <nav aria-label="Aplicaciones" className="grid gap-4 sm:grid-cols-3">
        {APLICACIONES.map((app) => (
          <Link
            key={app.clave}
            to={`${app.raiz}${search}`}
            className="flex min-h-[120px] flex-col justify-between rounded-lg border border-borde bg-papel p-5 hover:border-bosque"
          >
            <span className="font-serif text-[24px] leading-8 font-semibold text-tinta-fuerte">
              {app.nombre}
            </span>
            <span className="text-[14px] leading-[22px] text-secundaria">
              {app.clave === 'compra' && 'Buscar, la lista, favoritos y lo que gastas.'}
              {app.clave === 'recetas' && 'Tu recetario, el modo cocina y el plan de la semana.'}
              {app.clave === 'calorias' && 'Tu diario, tus alimentos y las tendencias.'}
            </span>
          </Link>
        ))}
      </nav>

      <footer className="mt-auto border-t border-borde pt-4 text-[13px] text-secundaria">
        <Link to="/ajustes" className="underline">
          Cuenta y preferencias
        </Link>
      </footer>
    </div>
  )
}

/** El titulo de la pestana por ruta. Lo de dentro lo mejora si sabe mas. */
export function tituloDe(ruta: string): string {
  if (ruta === '/') return 'Cesta'
  // **Las rutas de siempre siguen teniendo su titulo**, porque siguen existiendo como
  // redirecciones: durante el salto, la pestana tiene que decir lo mismo que decia antes. Y el
  // contrato de `tests/test_titulos.py` lo vigila leyendo este fichero: con diez pestanas abiertas,
  // un titulo que falta no da error de compilacion, se nota cuando ya no sabes cual es cual.
  if (ruta === '/buscar' || ruta === '/compra') return 'Buscar'
  if (ruta.startsWith('/cesta') || ruta.startsWith('/compra/listas')) return 'La cesta'
  if (ruta.startsWith('/compra/despensa')) return 'Despensa'
  if (ruta.startsWith('/grupo/') || ruta.startsWith('/compra/comparar/')) return 'Comparar'
  if (ruta.startsWith('/producto/') || ruta.includes('/productos/')) return 'Producto'
  if (ruta.startsWith('/favoritos') || ruta.startsWith('/compra/favoritos')) return 'Favoritos'
  if (ruta.startsWith('/unirme/')) return 'Invitacion'
  if (ruta.startsWith('/panel/matching')) return 'Matching'
  if (ruta.startsWith('/panel')) return 'Panel'
  if (ruta.startsWith('/escaner')) return 'Escáner'
  if (ruta.startsWith('/avisos')) return 'Avisos'
  if (ruta.startsWith('/ajustes')) return 'Ajustes'
  if (ruta.startsWith('/aprender')) return 'Aprender'
  return tituloDeSeccion(ruta)
}

export function App() {
  const { pathname, search } = useLocation()

  useEffect(() => {
    const nombre = tituloDe(pathname)
    document.title = nombre === 'Cesta' ? 'Cesta' : `${nombre} ${SUFIJO}`
    // **Donde estabas**, para el lanzador. Se guarda la ruta de la aplicacion, no la busqueda de
    // ayer: lo que se ofrece al volver es la aplicacion, no una consulta que ya no vale.
    if (typeof localStorage !== 'undefined' && aplicacionDe(pathname)) {
      localStorage.setItem(CLAVE_ULTIMO, pathname)
    }
  }, [pathname, search])

  return (
    <CocinaProvider>
      <Routes>
        <Route path="/" element={<Lanzador />} />

        {/* Compra: la lista, el buscador, la ficha y el gasto. */}
        <Route path="/compra" element={<LayoutSuite app="compra"><Buscar /></LayoutSuite>} />
        <Route path="/compra/listas" element={<LayoutSuite app="compra"><Cesta /></LayoutSuite>} />
        <Route path="/compra/despensa" element={<LayoutSuite app="compra"><Despensa /></LayoutSuite>} />
        <Route path="/compra/cocina/:recetaId/:version" element={<LayoutSuite app="compra"><CocinaModo /></LayoutSuite>} />
        <Route path="/compra/importar" element={<LayoutSuite app="recetas"><ImportarReceta /></LayoutSuite>} />
        <Route
          path="/compra/listas/:listaId"
          element={<LayoutSuite app="compra"><Cesta /></LayoutSuite>}
        />
        <Route
          path="/compra/favoritos"
          element={<LayoutSuite app="compra"><Favoritos /></LayoutSuite>}
        />
        <Route
          path="/compra/productos/:fuente/:idFuente"
          element={<LayoutSuite app="compra"><Producto /></LayoutSuite>}
        />
        <Route
          path="/compra/comparar/:grupoId"
          element={<LayoutSuite app="compra"><Grupo /></LayoutSuite>}
        />
        <Route
          path="/compra/analisis"
          element={<LayoutSuite app="compra"><Panel /></LayoutSuite>}
        />

        {/* Recetas y Calorias: armazon, menu y rutas. Sus secciones internas, en S08 y S09. */}
        <Route
          path="/recetas"
          element={<LayoutSuite app="recetas"><Recetario /></LayoutSuite>}
        />
        <Route
          path="/recetas/plan"
          element={<LayoutSuite app="recetas"><PlanSemanal /></LayoutSuite>}
        />
        <Route
          path="/recetas/:recetaId"
          element={<LayoutSuite app="recetas"><RecetaDetalle /></LayoutSuite>}
        />
        <Route
          path="/calorias"
          element={<LayoutSuite app="calorias"><Diario /></LayoutSuite>}
        />
        <Route
          path="/calorias/alimentos"
          element={<LayoutSuite app="calorias"><Cocina modo="calorias" /></LayoutSuite>}
        />
        <Route
          path="/calorias/tendencias"
          element={<LayoutSuite app="calorias"><Tendencias /></LayoutSuite>}
        />

        {/* Pantallas transversales: no son de ninguna de las tres aplicaciones. */}
        <Route path="/escaner" element={<LayoutSuite app={null}><Escaner /></LayoutSuite>} />
        <Route path="/avisos" element={<LayoutSuite app={null}><Avisos /></LayoutSuite>} />
        <Route
          path="/panel/matching"
          element={<LayoutSuite app={null}><PanelMatching /></LayoutSuite>}
        />
        <Route path="/panel" element={<LayoutSuite app={null}><Panel /></LayoutSuite>} />
        <Route path="/ajustes" element={<LayoutSuite app={null}><Ajustes /></LayoutSuite>} />
        <Route
          path="/aprender"
          element={
            <LayoutSuite app={null}>
              <Vacio titulo="Aprender">
                <p>
                  El material didactico vive en <code>docs/aprende/</code>. Aqui llegara el indice
                  navegable; mientras tanto se lee en el repositorio.
                </p>
              </Vacio>
            </LayoutSuite>
          }
        />
        <Route path="/unirme/:codigo" element={<Unirse />} />

        {/* Las direcciones de antes siguen funcionando, con su query. */}
        <Route path="/buscar" element={<Navigate to={`/compra${search}`} replace />} />
        <Route path="/cesta" element={<Navigate to={`/compra/listas${search}`} replace />} />
        <Route path="/favoritos" element={<Navigate to={`/compra/favoritos${search}`} replace />} />
        <Route path="/producto/:fuente/:idFuente" element={<RedirigeACompra base="productos" />} />
        <Route path="/grupo/:grupoId" element={<RedirigeACompra base="comparar" />} />

        <Route
          path="*"
          element={
            <Vacio titulo="Esa pantalla no existe" comoPagina>
              <p>
                Puede que el enlace este mal escrito.{' '}
                <Link to="/" className="underline">
                  Vuelve al inicio
                </Link>
                .
              </p>
            </Vacio>
          }
        />
      </Routes>
    </CocinaProvider>
  )
}

/** Reenvia una ruta antigua con parametros a su sitio nuevo, conservando la query. */
function RedirigeACompra({ base }: { base: 'productos' | 'comparar' }) {
  const { search, pathname } = useLocation()
  const partes = pathname.split('/').filter(Boolean)
  return <Navigate to={`/compra/${base}/${partes.slice(1).join('/')}${search}`} replace />
}
