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
import { Suspense, lazy, useEffect } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import { APLICACIONES, LayoutSuite, aplicacionDe, tituloDeSeccion } from './componentes/Suite'
import { SUFIJO } from './componentes/Titulo'
import { Vacio } from './componentes/ui'
const Ajustes = lazy(() => import('./paginas/Ajustes').then((m) => ({ default: m.Ajustes })))
const Avisos = lazy(() => import('./paginas/Avisos').then((m) => ({ default: m.Avisos })))
const Buscar = lazy(() => import('./paginas/Buscar').then((m) => ({ default: m.Buscar })))
const Cesta = lazy(() => import('./paginas/Cesta').then((m) => ({ default: m.Cesta })))
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

const CLAVE_ULTIMO = 'cesta.ultimo'

/** El lanzador: tres accesos y por donde ibas. Sin graficas ni datos de nadie. */
function Lanzador() {
  const navegar = useNavigate()
  const { search } = useLocation()
  const ultimo = typeof localStorage !== 'undefined' ? localStorage.getItem(CLAVE_ULTIMO) : null
  const aplicacion = ultimo ? aplicacionDe(ultimo) : null

  return (
    // *** El lanzador, compuesto para que LLENE. *** *
    //
    // *Y esto arregla el «60 % vacio» de `docs/ui/capturas/01-inicio.png`, *que no
    // era un fallo de contenido: *la pantalla **no tiene mas que decir** *-- tres
    // accesos y por donde ibas --, *y el problema era que **el contenido se
    // apinaba arriba y no se repartia.** *
    //
    // *La solucion **no es inventar datos** *(-- *ni cifras, *ni atajos que nadie
    // ha pedido --)*: *es **composicion.** *El `my-auto` de la rejilla **la lleva
    // al centro vertical** del hueco que queda entre la cabecera y el pie, *y asi
    // **el vacio no sobra: *rodea.*** *
    <div className="mx-auto flex min-h-screen max-w-app flex-col px-5 py-pagina">
      <header className="border-b border-borde pb-bloque">
        {/* *Los tamanos, a la escala: **`portada`** y **`cuerpo`**, *no
            `[32px]` y `[15px]` a ojo.* */}
        <h1 className="font-serif text-portada font-semibold text-tinta-fuerte">Cesta</h1>
        <p className="mt-1 text-cuerpo text-secundaria">
          La compra de casa, las recetas y lo que comes. Tres aplicaciones, una casa.
        </p>
      </header>

      {aplicacion && (
        <button
          type="button"
          onClick={() => navegar(ultimo ?? aplicacion.raiz)}
          className="mt-bloque min-h-[44px] self-start rounded-campo border border-borde-fuerte px-4 text-cuerpo text-tinta-fuerte transition-colors duration-rapida ease-suave hover:bg-papel"
        >
          Continuar donde estaba: <strong>{aplicacion.nombre}</strong>
        </button>
      )}

      {/* *`my-auto`: *esto es lo que reparte el alto.* */}
      <nav aria-label="Aplicaciones" className="my-auto grid gap-4 sm:grid-cols-3">
        {APLICACIONES.map((app) => (
          <Link
            key={app.clave}
            to={`${app.raiz}${search}`}
            // *** Y cada tarjeta lleva SU icono, *que es lo que la hace
            // reconocible **antes de leerla.** *** *
            //
            // *El dato ya estaba desde la FASE 3: *`APLICACIONES` tiene `Icono`, *y
            // **aqui no se usaba.*** *Y el movimiento es el de la direccion: *`normal`
            // porque **cambia de estado**, *no `rapida`* *-- *que es para lo que
            // responde al dedo.* *
            className="group flex min-h-[150px] flex-col justify-between gap-bloque rounded-tarjeta border border-borde bg-papel p-5 shadow-apoyado transition duration-normal ease-suave hover:border-bosque hover:shadow-alzado"
          >
            <span
              aria-hidden="true"
              className="text-bosque transition-transform duration-normal ease-suave group-hover:-translate-y-0.5"
            >
              <app.Icono width={26} height={26} />
            </span>
            <span className="flex flex-col gap-1">
              <span className="font-serif text-titulo font-semibold text-tinta-fuerte">
                {app.nombre}
              </span>
              <span className="text-etiqueta text-secundaria">
                {app.clave === 'compra' && 'Buscar, la lista, favoritos y lo que gastas.'}
                {app.clave === 'recetas' && 'Tu recetario, el modo cocina y el plan de la semana.'}
                {app.clave === 'calorias' && 'Tu diario, tus alimentos y las tendencias.'}
              </span>
            </span>
          </Link>
        ))}
      </nav>

      <footer className="mt-bloque border-t border-borde pt-4 text-etiqueta text-secundaria">
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
    // **Y un solo `Suspense` por fuera, que es lo que hace falta.** *`CocinaProvider` tambien es
    // diferido, asi que el limite tiene que estar **por encima** de el* -- *ponerlo solo dentro no
    // cubriria la carga del propio provider.*
    //
    // *Y el texto de espera no es «Cargando...» a secas*: **dice que se esta abriendo la pantalla**,
    // que es lo que de verdad esta pasando y lo que hace que la espera se entienda.
    <Suspense fallback={<p className="p-6 text-neutral-600 dark:text-neutral-400">Abriendo la pantalla…</p>}>
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
    </Suspense>
  )
}

/** Reenvia una ruta antigua con parametros a su sitio nuevo, conservando la query. */
function RedirigeACompra({ base }: { base: 'productos' | 'comparar' }) {
  const { search, pathname } = useLocation()
  const partes = pathname.split('/').filter(Boolean)
  return <Navigate to={`/compra/${base}/${partes.slice(1).join('/')}${search}`} replace />
}
