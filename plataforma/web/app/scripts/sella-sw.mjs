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

const version = new Date().toISOString().slice(0, 13).replace(/[-:T]/g, '')
const texto = readFileSync(ruta, 'utf8')
if (!texto.includes("'__VERSION__'")) {
  console.error('sella-sw: sw.js no trae __VERSION__; no se sella nada')
  process.exit(1)
}
writeFileSync(ruta, texto.replace("'__VERSION__'", `'${version}'`), 'utf8')
console.log(`sella-sw: ${ruta} -> version ${version}`)
