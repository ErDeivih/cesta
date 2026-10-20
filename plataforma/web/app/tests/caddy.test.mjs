/**
 * *** LO QUE SIRVE LA APP: las cabeceras del `Caddyfile`. ***
 *
 * *Nada de esto da error si esta mal.* *Una CSP demasiado estrecha rompe la app **solo en produccion**; una
 * `Cache-Control` que falta hace que el navegador **nunca** vea la version nueva.*
 *
 * *Se comprueba sobre `plataforma/Caddyfile`, que es lo que se despliega.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const caddy = readFileSync(new URL('../../../Caddyfile', import.meta.url), 'utf8')

test('*** la CSP no abre la puerta de par en par ***', () => {
  // *`unsafe-inline` y `unsafe-eval` anulan la CSP: con ellos, la cabecera es decorativa.*
  const csp = caddy.match(/Content-Security-Policy\s+"([^"]+)"/)
  assert.ok(csp, 'no hay Content-Security-Policy')
  for (const peligro of ["'unsafe-inline'", "'unsafe-eval'"]) {
    assert.ok(!csp[1].includes(peligro), 'la CSP lleva ' + peligro)
  }
  // *Y los cuatro cierres que tienen que estar.*
  assert.match(csp[1], /default-src 'self'/, 'sin default-src self')
  assert.match(csp[1], /script-src 'self'/, 'sin script-src self')
  assert.match(csp[1], /base-uri 'none'/, 'sin base-uri none')
  assert.match(csp[1], /frame-ancestors 'none'/, 'sin frame-ancestors none')
})

test('*** el service worker NO se cachea ***', () => {
  // *** Sin esto, el navegador puede cachear el propio `sw.js` y no ver la version nueva NUNCA: la app se queda
  // clavada en el armazon viejo. *** *Es el fallo clasico de una PWA, y no se nota en desarrollo.*
  assert.match(caddy, /header \/sw\.js Cache-Control "no-cache/, 'sw.js sin Cache-Control: la app se quedaria clavada')
})

test('*** el index tampoco, y los trozos si ***', () => {
  // *`index.html` sin hash: si se cachea, apunta a trozos que ya no existen.*
  assert.match(caddy, /header \/index\.html Cache-Control "no-cache/, 'index.html sin no-cache')
  // *Los trozos SI llevan hash en el nombre, asi que son inmutables: pedirlos otra vez es gastar red sin motivo.*
  assert.match(caddy, /header \/assets\/\* Cache-Control "[^"]*immutable/, '/assets/* sin immutable')
})

test('*** los cierres que no cuestan nada ***', () => {
  assert.match(caddy, /X-Content-Type-Options nosniff/, 'sin nosniff')
  assert.match(caddy, /X-Frame-Options DENY/, 'sin X-Frame-Options DENY')
  assert.match(caddy, /Referrer-Policy strict-origin-when-cross-origin/, 'sin Referrer-Policy')
})
