/**
 * *** Sella el service worker con la version de este build. ***
 *
 * *`public/sw.js` lleva `__VERSION__` en el nombre de la cache.* *Si se quedara asi, todas las
 * publicaciones compartirian cache y una version nueva seguiria sirviendo el armazon viejo.*
 *
 * *Se sella **despues** de `vite build`, con la fecha en que se construyo: dos builds del mismo dia
 * comparten version, que es lo correcto -- el armazon es el mismo.*
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
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
const html = readFileSync(join(ruta, '..', 'index.html'), 'utf8')
const urls = new Set()
for (const m of html.matchAll(/<(?:script|link)\b[^>]*?(?:src|href)="([^"]+)"/g)) {
  const u = m[1]
  if (u.startsWith('/assets/') && (u.endsWith('.js') || u.endsWith('.css'))) urls.add(u)
}
const precache = [...urls].sort()
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
