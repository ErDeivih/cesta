/** Las rutas de la suite: portada, tres aplicaciones y las pantallas de siempre.
 *
 *  **`/` es la Portada desde el 5 de noviembre de 2026.** Sustituye al lanzador del 7 de
 *  octubre, que repartia tres accesos y «por donde ibas»; la portada contesta lo que se
 *  viene a mirar al abrir la app: que cuesta la cesta, en que cadena esta mas barata, que
 *  se ha movido y por donde se empieza a buscar. El artboard esta aprobado en
 *  `designs/cesta-app/project/Portada.dc.html`.
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
import { Suspense, lazy, useEffect } from 'react'
import { ErrorBoundary } from './componentes/ErrorBoundary'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { LayoutSuite, tituloDeSeccion } from './componentes/Suite'
import { SUFIJO } from './componentes/Titulo'
import { Vacio } from './componentes/ui'
const Ajustes = lazy(() => import('./paginas/Ajustes').then((m) => ({ default: m.Ajustes })))
const Avisos = lazy(() => import('./paginas/Avisos').then((m) => ({ default: m.Avisos })))
const Buscar = lazy(() => import('./paginas/Buscar').then((m) => ({ default: m.Buscar })))
const Cesta = lazy(() => import('./paginas/Cesta').then((m) => ({ default: m.Cesta })))
const CompararCesta = lazy(() =>
  import('./paginas/CompararCesta').then((m) => ({ default: m.CompararCesta })))
const [Cocina, CocinaProvider] = [
  lazy(() => import('./paginas/Cocina').then((m) => ({ default: m.Cocina }))),
  lazy(() => import('./paginas/Cocina').then((m) => ({ default: m.CocinaProvider }))),
]
const Escaner = lazy(() => import('./paginas/Escaner').then((m) => ({ default: m.Escaner })))
const Diario = lazy(() => import('./paginas/Diario').then((m) => ({ default: m.Diario })))
const Tendencias = lazy(() => import('./paginas/Tendencias').then((m) => ({ default: m.Tendencias })))
const ImportarReceta = lazy(() => import('./paginas/ImportarReceta').then((m) => ({ default: m.ImportarReceta })))
const CocinaModo = lazy(() => import('./paginas/CocinaModo').then((m) => ({ default: m.CocinaModo })))
const Despensa = lazy(() => import('./paginas/Despensa').then((m) => ({ default: m.Despensa })))
const Favoritos = lazy(() => import('./paginas/Favoritos').then((m) => ({ default: m.Favoritos })))
const Grupo = lazy(() => import('./paginas/Grupo').then((m) => ({ default: m.Grupo })))
const Panel = lazy(() => import('./paginas/Panel').then((m) => ({ default: m.Panel })))
const PanelMatching = lazy(() => import('./paginas/PanelMatching').then((m) => ({ default: m.PanelMatching })))
const Producto = lazy(() => import('./paginas/Producto').then((m) => ({ default: m.Producto })))
const Recetario = lazy(() => import('./paginas/Recetario').then((m) => ({ default: m.Recetario })))
const RecetaDetalle = lazy(() => import('./paginas/RecetaDetalle').then((m) => ({ default: m.RecetaDetalle })))
const PlanSemanal = lazy(() => import('./paginas/PlanSemanal').then((m) => ({ default: m.PlanSemanal })))
const Unirse = lazy(() => import('./paginas/Unirse').then((m) => ({ default: m.Unirse })))
const Portada = lazy(() => import('./paginas/Portada').then((m) => ({ default: m.Portada })))

/** El titulo de la pestana por ruta. Lo de dentro lo mejora si sabe mas. */
export function tituloDe(ruta: string): string {
  if (ruta === '/') return 'Cesta'
  // **Las rutas de siempre siguen teniendo su titulo**, porque siguen existiendo como
  // redirecciones: durante el salto, la pestana tiene que decir lo mismo que decia antes. Y el
  // contrato de `tests/test_titulos.py` lo vigila leyendo este fichero: con diez pestanas abiertas,
  // un titulo que falta no da error de compilacion, se nota cuando ya no sabes cual es cual.
  if (ruta === '/buscar' || ruta === '/compra') return 'Buscar'
  // **Antes que `/compra/listas`, que se lleva por delante todo lo que cuelgue de ella.**
  // *Comparar la cesta es otra pantalla que la lista, y la pestana tiene que poder decirlo:
  // con «La cesta» en las dos, dos pestanas abiertas se llaman igual.*
  if (ruta.startsWith('/compra/listas/') && ruta.endsWith('/comparar')) return 'Comparar la cesta'
  if (ruta.startsWith('/cesta') || ruta.startsWith('/compra/listas')) return 'La cesta'
  if (ruta.startsWith('/compra/despensa')) return 'Despensa'
  if (ruta.startsWith('/compra/cocina')) return 'Cocina'
  if (ruta.startsWith('/compra/importar')) return 'Importar una receta'
  if (ruta.startsWith('/grupo/') || ruta.startsWith('/compra/comparar/')) return 'Comparar'
  if (ruta.startsWith('/producto/') || ruta.includes('/productos/')) return 'Producto'
  if (ruta.startsWith('/favoritos') || ruta.startsWith('/compra/favoritos')) return 'Favoritos'
  if (ruta.startsWith('/unirme/')) return 'Invitacion'
  if (ruta.startsWith('/panel/matching')) return 'Matching'
  if (ruta.startsWith('/panel')) return 'Panel'
  if (ruta.startsWith('/escaner')) return 'Escáner'
  if (ruta.startsWith('/avisos')) return 'Avisos'
  if (ruta.startsWith('/ajustes')) return 'Ajustes'
  return tituloDeSeccion(ruta)
}

export function App() {
  // **Y `state`, que es lo que se perdia.** *Las redirecciones de abajo mandaban
  // `search` pero no `state`, asi que al cruzar por ellas **se borraba lo que llevaba
  // la navegacion**: `Unirse` deja ahi el aviso de «Ya estas en <lista>» y el
  // `listaId` al que hay que entrar, y el redirect se los comia.* *Medido: la
  // puerta lo comprueba desde hace rondas y fallaba siempre.*
  const { pathname, search, state } = useLocation()

  useEffect(() => {
    const nombre = tituloDe(pathname)
    document.title = nombre === 'Cesta' ? 'Cesta' : `${nombre} ${SUFIJO}`
  }, [pathname])

  return (
    // **Y un solo `Suspense` por fuera, que es lo que hace falta.** *`CocinaProvider` tambien es
    // diferido, asi que el limite tiene que estar **por encima** de el* -- *ponerlo solo dentro no
    // cubriria la carga del propio provider.*
    //
    // *Y el texto de espera no es «Cargando...» a secas*: **dice que se esta abriendo la pantalla**,
    // que es lo que de verdad esta pasando y lo que hace que la espera se entienda.
        // *** Y LO QUE SE VE MIENTRAS LLEGA ES EL ARMAZON DE LA MARCA, NO UN PARRAFO. ***
        // *Antes esto era un `<p>` con «Abriendo la pantalla…»: una linea de texto gris en una
        // pantalla desnuda.* *Es lo primero que ve alguien que abre la app, y no se parecia a nada.*
        //
        // *Ahora se pinta **el marco**: el nombre, su sitio y una forma de carga con los colores de la
        // casa.* *No es adorno: es lo que hace que una espera parezca la aplicacion abriendose en vez
        // de una pagina rota.* *Y como es HTML y CSS, sale **antes** de que llegue ningun trozo.*
        //
        // *No lleva `aria-live` a proposito: no hay nada que anunciar, es una espera corta.* *Lo que
        // si lleva es `role="status"` para que un lector de pantalla sepa que la pagina esta en
        // marcha.*
        <Suspense fallback={<ArmazonDeLaMarca />}>
    <CocinaProvider>
      <ErrorBoundary que="esta pantalla"><Routes>
        <Route path="/" element={<Portada />} />

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
        {/* *** COMPARAR MI CESTA. *** *
            *La pantalla que contesta «donde me sale mejor esta lista»: el total de cada cadena
            con cuantos productos lo forman, y el desglose por producto.* *Va debajo de la lista
            porque se llega desde ella, y su ruta cuelga de la lista concreta: comparar es comparar
            **esta** lista, no una cualquiera.* */}
        <Route
          path="/compra/listas/:listaId/comparar"
          element={<LayoutSuite app="compra"><CompararCesta /></LayoutSuite>}
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
        {/* *** `/compra/analisis` YA NO EXISTE, *y es P0-2.* *** *
            *Esa ruta montaba `Panel` -- el cuadro de mando del catálogo -- y el menú la ofrecía
            como «Gasto y ahorro».* *Quien la abría esperaba lo que había pagado y encontraba diez
            pestañas de ingesta.* *El panel sigue vivo para diagnóstico en `/panel`, **sin enlace
            desde ninguna pantalla de consumo**; lo que se quita es la puerta que lo disfrazaba.* */}

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
        {/* *** `/aprender` SE VA, *y es P0-5.* *** *
            *En el menú había un destino llamado «Aprender» que llevaba a un párrafo: «el material
            didáctico vive en `docs/aprende/`… mientras tanto se lee en el repositorio».* *Una
            ruta del repositorio contada a quien compra.* *Cuando exista el índice navegable de
            verdad, se pone su pantalla y su entrada; mientras tanto, no hay nada que ofrecer.* */}
        {/* *** Y esta pantalla SE SALTABA EL ARMAZON. *** *
              *
              * *El 15/10/2026, *con la captura de `/unirme/CODIGO-MALO` delante, *se vio
              *que sus tarjetas iban *** de borde a borde de la pantalla *** *-- de x=0 a
              *x=1440 --,* *sin margen, *sin ancho maximo *y sin lateral.* *Y la causa era
              *esta linea: *la ruta **no envolvia en `LayoutSuite`**, *asi que **no habia
              *`main`**, *ni `mx-auto max-w-app`, *ni `px-4`.* *
              *
              * *Y `app={null}` **es lo correcto aqui**: *es una invitacion, *no una de las
              *tres aplicaciones* *-- *igual que `/escaner`, *`/panel` y `/ajustes`, *que
              *ya lo hacen asi --.* *Y el titulo tambien: *`tituloDeSeccion` ya devuelve
              *«Invitacion» para `/unirme/`.* *
              */}
            <Route path="/unirme/:codigo" element={<LayoutSuite app={null}><Unirse /></LayoutSuite>} />

        {/* Las direcciones de antes siguen funcionando, con su query. */}
        <Route path="/buscar" element={<Navigate to={`/compra${search}`} state={state} replace />} />
        <Route path="/cesta" element={<Navigate to={`/compra/listas${search}`} state={state} replace />} />
        <Route path="/favoritos" element={<Navigate to={`/compra/favoritos${search}`} state={state} replace />} />
        <Route path="/producto/:fuente/:idFuente" element={<RedirigeACompra base="productos" />} />
        <Route path="/grupo/:grupoId" element={<RedirigeACompra base="comparar" />} />

        <Route
          path="*"
          element={
            <Vacio titulo="Esa pantalla no existe" comoPagina className="grow">
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
      </Routes></ErrorBoundary>
    </CocinaProvider>
    </Suspense>
  )
}

/** Reenvia una ruta antigua con parametros a su sitio nuevo, conservando la query. */
function RedirigeACompra({ base }: { base: 'productos' | 'comparar' }) {
  const { search, pathname, state } = useLocation()
  const partes = pathname.split('/').filter(Boolean)
  return <Navigate to={`/compra/${base}/${partes.slice(1).join('/')}${search}`} state={state} replace />
}

/** *** Lo que se ve mientras llega la pantalla: el marco de la casa. ***
 *
 *  *Se pinta con HTML y CSS del trozo principal, asi que aparece **antes** de que llegue ningun trozo
 *  diferido.* *No depende de la sesion ni de la API: es el armazon, y por eso no puede quedarse en
 *  blanco aunque el servidor no conteste.*
 *
 *  *La forma de carga es una barra que se mueve despacio, en el verde de la marca, y **respeta
 *  `prefers-reduced-motion`**: quien haya pedido menos movimiento ve la barra quieta, que sigue
 *  diciendo «esto esta en marcha».*
 */
function ArmazonDeLaMarca() {
  return (
    <div
      className="min-h-screen bg-papel px-5 py-pagina text-tinta"
      role="status"
      aria-label="Abriendo Cesta"
    >
      <header className="border-b border-borde pb-bloque">
        <h1 className="font-serif text-portada font-semibold text-tinta-fuerte">Cesta</h1>
      </header>

      {/* *Tres formas del alto de una tarjeta, con la misma separacion que la portada de verdad.*
          *Y la primera con la barra de carga dentro.* */}
      <div className="mt-bloque grid gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="rounded-tarjeta border border-borde bg-papel-alto p-4">
            <div className="h-3 w-1/3 rounded-full bg-borde" />
            <div className="mt-2 h-2 w-2/3 rounded-full bg-borde opacity-70" />
            {i === 0 && (
              <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-borde opacity-60">
                <div className="h-full w-1/3 origin-left animate-[cargando_1.4s_ease-in-out_infinite] rounded-full bg-bien motion-reduce:animate-none motion-reduce:w-1/2" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
