/**
 * *** EL CONTENEDOR DE LA API: no corre como root, y se para si no puede adoptar el volumen. ***
 *
 * *La API se sirve desde un contenedor.* *Que corra como **root** seria un fallo de seguridad que no da error en
 * ninguna parte: funciona igual, y con todos los privilegios.*
 *
 * *Y el arranque es delicado porque tiene que hacer **dos cosas incompatibles**: un `chown` (que necesita `root`) y
 * correr la API **sin** privilegios.* *El `chown` no llega al volumen porque el volumen se monta despues y tapa el
 * directorio, asi que el volumen nace de `root` y hay que adoptarlo en cada arranque.*
 *
 * *Se comprueba sobre `plataforma/Dockerfile` y `plataforma/entrar-api.sh`, que son lo que se despliega.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const LEER = new URL('../../../', import.meta.url)
const dockerfile = readFileSync(new URL('Dockerfile', LEER), 'utf8')
const entra = readFileSync(new URL('entrar-api.sh', LEER), 'utf8')

test('*** hay un usuario sin privilegios, con uid fijo ***', () => {
  // *`useradd -r -u 10001 cesta`: un uid fijo hace que los permisos del volumen sean predecibles entre
  // reconstrucciones.* *Sin uid fijo, cada build podria coger otro y el volumen dejaria de ser suyo.*
  assert.match(dockerfile, /useradd -r -u 10001 cesta/, 'no crea el usuario cesta con uid fijo')
})

test('*** NO hay `USER cesta` en el Dockerfile, y es a proposito ***', () => {
  // *Parece lo contrario de lo correcto, y esta documentado: el `chown` del arranque necesita `root`, y el guion
  // baja a `cesta`. Poner `USER cesta` aqui impediria adoptar el volumen, y el sintoma seria «readonly database».*
  assert.ok(!/^USER\s+cesta/m.test(dockerfile), 'poner USER cesta impediria adoptar el volumen')
  // *Pero si que tiene que haber quien baje de privilegios.*
  assert.match(dockerfile, /ENTRYPOINT \["\/app\/plataforma\/entrar-api\.sh"\]/, 'el arranque no pasa por el guion')
})

test('*** el guion baja de privilegios, y con `exec` ***', () => {
  // *`exec setpriv ...`: `exec` sustituye el proceso, asi que **no queda un `root` padre** esperando.* *Sin `exec`,
  // el root seguiria vivo como padre del proceso de la API.*
  assert.match(entra, /exec setpriv --reuid=cesta --regid=cesta/, 'no baja de privilegios con exec+setpriv')
  // *Y la comprobacion de que solo lo hace si arranco como root.*
  assert.match(entra, /if \[ "\$\(id -u\)" = "0" \]/, 'no distingue si arranco como root')
})

test('*** si no puede adoptar el volumen, SE PARA ***', () => {
  // *** Seguir como root para tapar el fallo seria peor: la API entera correria con privilegios. ***
  assert.match(entra, /exit 1/, 'no sale con error si el chown falla')
  // *Y lo dice, en vez de morir en silencio.*
  assert.match(entra, /No se pudo adoptar/, 'no dice que no pudo adoptar el volumen')
  assert.match(entra, /root/i, 'no explica por que no sigue como root')
})

test('*** `set -e`, y el healthcheck ***', () => {
  // *`set -e`: sin el, un fallo a medias seguiria adelante.*
  assert.match(entra, /^set -e$/m, 'el guion no lleva set -e')
  // *El healthcheck es lo que distingue «arrancado» de «sirviendo».*
  assert.match(dockerfile, /HEALTHCHECK/, 'sin healthcheck')
  assert.match(dockerfile, /\/api\/salud/, 'el healthcheck no mira /api/salud')
  // *Y el oro de solo lectura: el contenedor no escribe en gold nunca.*
  assert.match(dockerfile, /CESTA_GOLD=\/datos\/gold/, 'no fija CESTA_GOLD')
})
