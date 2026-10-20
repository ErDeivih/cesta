/**
 * *** Sella el service worker con la version de este build. ***
 *
 * *`public/sw.js` lleva `__VERSION__` en el nombre de la cache.* *Si se quedara asi, todas las
 * publicaciones compartirian cache y una version nueva seguiria sirviendo el armazon viejo.*
 *
 * *Se sella **despues** de `vite build`, con la fecha en que se construyo: dos builds del mismo dia
 * comparten version, que es lo correcto -- el armazon es el mismo.*
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const destino = join(process.cwd(), '..', '..', '..', 'plataforma', 'web', 'dist', 'sw.js')
const sw = join(process.cwd(), 'dist', 'sw.js')
const ruta = existsSync(sw) ? sw : destino
if (!existsSync(ruta)) {
  console.error('sella-sw: no encuentro sw.js en el build; ¿se copio public/?')
  process.exit(1)
}

// *** Y la lista de trozos de la entrada, sacada del HTML construido. ***
// *Lo que hay que tener cacheado para que la primera pantalla se pinte: el `<script>` del modulo y los
// `<link rel="modulepreload">`. Se leen del `index.html` del build, asi que son los que existen de
// verdad y con su hash.*
// *Y **todos** los trozos, no solo los que salen en el `index.html`.*
// *Se probo con los del HTML y no bastaba: `CocinaProvider` es un trozo diferido que **no aparece** en
// el documento, y sin el la aplicacion se queda en el armazon -- 53 caracteres, medido.**
// *La causa es que el `Suspense` de `App.tsx` envuelve tambien ese provider: si su trozo no esta en la
// cache, la pantalla no resuelve nunca.*
// *Un service worker que solo guarda lo que viene en el HTML no sabe nada de los trozos que el propio
// JavaScript va a pedir despues.*
const dirAssets = join(ruta, '..', 'assets')
const ficheros = existsSync(dirAssets) ? readdirSync(dirAssets) : []
const precache = ficheros
  .filter((f) => f.endsWith('.js') || f.endsWith('.css'))
  .map((f) => '/assets/' + f)
  .sort()
if (!precache.length) {
  console.error('sella-sw: el index.html del build no trae trozos en /assets; no hay precache')
  process.exit(1)
}

const version = new Date().toISOString().slice(0, 13).replace(/[-:T]/g, '')
const texto = readFileSync(ruta, 'utf8')
if (!texto.includes("'__VERSION__'")) {
  console.error('sella-sw: sw.js no trae __VERSION__; no se sella nada')
  process.exit(1)
}
const sellado = texto
  .replace("'__VERSION__'", `'${version}'`)
  .replace('__PRECACHE__', JSON.stringify(precache))
if (sellado.includes('__PRECACHE__')) {
  console.error('sella-sw: sw.js no trae __PRECACHE__; no se sella nada')
  process.exit(1)
}
writeFileSync(ruta, sellado, 'utf8')
console.log(`sella-sw: version ${version}, ${precache.length} trozos precacheados`)
