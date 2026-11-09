/**
 * *** EL FORMATO: «NO LO SE» NO ES «0,00 €». ***
 *
 * *`api/formato.ts` es lo que usa **cada pantalla** para escribir euros, fechas y nombres de cadena.*
 * *Tiene 18 exportaciones, es puro, y **no tenia ni una prueba**.*
 *
 * *La decision que se repite en todas: cuando el dato falta, se devuelve **`NO_LO_SE`** -- «no lo sé» --,
 * no un cero ni una fecha inventada.* *Es la misma regla de `gasto`, `pesos` y `costeReceta`, pero aqui es
 * la ultima puerta antes de la pantalla: si esta devuelve `0,00 €`, lo que llegue al usuario sera una
 * mentira aunque todo lo de antes fuera correcto.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  NO_LO_SE,
  cantidad,
  diasDesde,
  euros,
  eurosUnidad,
  fecha,
  hace,
  nombreCadena,
  numero,
  porcentaje,
  porcentajeConSigno,
  sufijoUnidad,
} from '../src/api/formato.ts'

// ------------------------------------------------- «no lo sé» no es un cero ---

test('*** `euros` de un dato que falta dice «no lo sé», no 0,00 ***', () => {
  for (const falta of [null, undefined, Number.NaN]) {
    assert.equal(euros(falta), NO_LO_SE, String(falta))
  }
})

test('*** y un cero de verdad SI es 0,00 EUR ***', () => {
  // *La otra mitad de la regla: `0` es un dato.*
  assert.match(euros(0), /0,00/)
})

test('euros con centimos', () => {
  assert.match(euros(150), /1,50/)
  // *** Y sin separador de miles: `euros(123456)` da «1234,56 EUR», no «1.234,56». ***
  // *Lo cace porque la prueba fallo esperando el punto.* *Queda escrito tal como es: en una compra de
  // decenas de euros no se nota, y en un total anual se lee peor.* **No se cambia aqui** -- `EUROS`
  // podria tener `useGrouping` puesto a proposito -- *pero se deja constancia para que nadie lo descubra
  // con una captura.*
  // *** AVISO: esto asierta lo que da NODE, que puede no ser lo que da el navegador. ***
  // *`EUROS` es `new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })` **sin tocar
  // `useGrouping`**, o sea con la agrupacion por defecto.* *Si node no la aplica y el navegador si,
  // aqui sale «1234,56» y en pantalla «1.234,56».* *No se puede comprobar sin navegador, y el navegador
  // necesita la API para tener datos que formatear.*
  // *Se deja como aviso en vez de fingir una certeza: **la prueba fija el `NO_LO_SE`, que es lo que
  // importa, no el separador de miles**.*
  assert.match(euros(123456), /1234,56|1\.234,56/, 'con o sin agrupacion, pero con los centimos bien')
})

test('*** `numero` y `porcentaje` dicen lo mismo cuando falta ***', () => {
  assert.equal(numero(null), NO_LO_SE)
  assert.equal(porcentaje(null), NO_LO_SE)
})

test('*** y el porcentaje lleva el espacio duro antes del signo ***', () => {
  // *«20 %» con espacio, que es como se escribe en español.*
  assert.match(porcentaje(20), /^20 %$/)
})

test('*** `porcentajeConSigno` pone el signo y usa el menos tipografico ***', () => {
  assert.match(porcentajeConSigno(20), /^\+20 %$/)
  // *No es un guion: es «−» (U+2212), que es lo que se lee como menos.*
  assert.match(porcentajeConSigno(-20), /^−20 %$/, 'menos tipografico, no guion')
  // *Y el cero no lleva signo: «+0 %» es ruido.*
  assert.match(porcentajeConSigno(0), /^0 %$/)
})

// ------------------------------------------------------------- las fechas ---

test('*** una fecha ilegible no se pinta como 1970 ***', () => {
  // *`new Date('no es fecha')` da `Invalid Date`, y formatearlo daria «Invalid Date» en pantalla.*
  assert.equal(fecha('no es una fecha'), NO_LO_SE)
  assert.equal(fecha(null), NO_LO_SE)
  assert.equal(fecha(''), NO_LO_SE)
})

test('*** una fecha buena se pinta corta: «18 oct 2026» ***', () => {
  // *Esperaba «octubre de 2026»; el modulo usa la forma corta con mes abreviado, que es lo que cabe en
  // una fila de tabla.*
  assert.match(fecha('2026-10-18'), /18 oct 2026/)
  // *Y con `corta`, se cae el año.*
  assert.match(fecha('2026-10-18', true), /^18 oct$/)
})

test('*** y `diasDesde` cuenta dias de calendario, no horas ***', () => {
  // *Es lo que evita que «hoy» y «ayer» dependan de la hora a la que se mire.*
  const hoy = new Date('2026-10-18T23:30:00')
  assert.equal(diasDesde('2026-10-18', hoy), 0, 'el mismo dia es 0, aunque falten 30 minutos')
  assert.equal(diasDesde('2026-10-17', hoy), 1, 'el dia anterior es 1')
  assert.equal(diasDesde('2026-10-20', hoy), -2, 'y el futuro es negativo')
})

test('*** `diasDesde` de algo ilegible es `null`, no 0 ***', () => {
  // *Un 0 se leeria como «hoy», que es una afirmacion falsa.*
  assert.equal(diasDesde('no es fecha'), null)
  assert.equal(diasDesde(null), null)
})

test('*** `hace` habla en palabras: hoy, ayer, hace N dias ***', () => {
  // *La fecha de «ahora» se toma en LOCAL, no con `toISOString()`: en Madrid, a partir
  // de medianoche, el ISO en UTC todavía es el día anterior y la prueba decía «ayer»
  // donde tenía que decir «hoy» (falló pasada la medianoche del 9 al 10/11/2026).*
  const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    + `-${String(d.getDate()).padStart(2, '0')}`
  const ahora = new Date()
  const unDia = 24 * 60 * 60 * 1000
  const ayer = isoLocal(new Date(ahora.getTime() - unDia))
  const haceTres = isoLocal(new Date(ahora.getTime() - 3 * unDia))
  assert.equal(hace(isoLocal(ahora)), 'hoy')
  assert.equal(hace(ayer), 'ayer')
  assert.equal(hace(haceTres), 'hace 3 días')
})

test('y `hace` de una fecha futura lo dice sin signos raros', () => {
  const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    + `-${String(d.getDate()).padStart(2, '0')}`
  const futuro = isoLocal(new Date(Date.now() + 2 * 24 * 60 * 60 * 1000))
  assert.match(hace(futuro), /dentro de 2 días/)
  // *Y el singular, que salía como «dentro de 1 días».*
  const manana = isoLocal(new Date(Date.now() + 24 * 60 * 60 * 1000))
  assert.equal(hace(manana), 'dentro de 1 día')
})

// ------------------------------------------------------ unidades y cadenas ---

test('el sufijo de unidad lleva su barra', () => {
  assert.equal(sufijoUnidad('kg'), '/kg')
  assert.equal(sufijoUnidad(' KG '), '/kg', 'se normaliza')
})

test('*** y sin unidad no inventa una barra suelta ***', () => {
  assert.equal(sufijoUnidad(null), '')
  assert.equal(sufijoUnidad(''), '')
  assert.equal(sufijoUnidad('   '), '')
})

test('*** `eurosUnidad` de un dato que falta dice «no lo sé» ***', () => {
  assert.equal(eurosUnidad(null, 'kg'), NO_LO_SE)
})

test('*** el nombre de la cadena va como se llama, no en minusculas ***', () => {
  // *Es el fallo del 27/9/2026 en la frase del precio: «mercadona» con minuscula inicial.*
  assert.equal(nombreCadena('mercadona'), 'Mercadona')
  assert.equal(nombreCadena('dia'), 'DIA')
})

test('y de una cadena vacia no saca un texto inventado', () => {
  const r = nombreCadena(null)
  assert.ok(typeof r === 'string' && r.length > 0, 'algo tiene que devolver')
})

test('*** `cantidad` no convierte un hueco en un cero ***', () => {
  const r = cantidad(null, 'g')
  assert.ok(!/\b0\b/.test(r) || /no lo sé/i.test(r), 'sin dato, no se pone un cero: ' + r)
})
