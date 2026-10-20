/**
 * *** LO QUE USAS Y LO QUE COMPRAS SON DOS NUMEROS, Y NO SIGNIFICAN LO MISMO. ***
 *
 * *`costeReceta.ts` lo dice en su cabecera:*
 *
 *   «La receta dice «200 g de arroz» y el catalogo «1 kg, 1,20 EUR». **Lo que usas cuesta 0,24 EUR; lo
 *    que compras cuesta 1,20 EUR.** Los dos numeros significan cosas distintas -- lo que cuesta hacer el
 *    plato, y lo que sale de tu bolsillo -- y dar uno solo como «el coste de la receta» es elegir por
 *    quien lee sin decírselo.»
 *
 *   «Y el caso que no se puede prorratear: «2 huevos». *Un huevo no tiene fraccion.*»
 *
 * *** Y no tenia pruebas. ***
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { costeDeReceta } from '../src/logica/costeReceta.ts'

/** *Un ingrediente con su envase.* */
const ing = (extra = {}) => ({
  nombre: 'Arroz',
  cantidad: 200,
  unidad: 'g',
  precio: { precioEnvaseCent: 120, cantidadEnvase: 1000, unidadEnvase: 'g' },
  ...extra,
})

// --------------------------------------- los dos numeros, y que son distintos ---

test('*** 200 g de un paquete de 1 kg a 1,20 EUR: usas 0,24 y compras 1,20 ***', () => {
  const r = costeDeReceta([ing()])
  assert.equal(r.ingredientes[0].costeUsadoCent, 24, '200 de 1000 g es una quinta parte de 120')
  assert.equal(r.ingredientes[0].costeEnvaseCent, 120, 'el envase entero cuesta 120')
  // *Y las dos sumas son las dos, no una.*
  assert.equal(r.usadoCent, 24)
  assert.equal(r.envaseCent, 120)
})

test('usar el envase entero hace que los dos numeros coincidan', () => {
  const r = costeDeReceta([ing({ cantidad: 1000 })])
  assert.equal(r.ingredientes[0].costeUsadoCent, 120)
  assert.equal(r.ingredientes[0].costeEnvaseCent, 120)
})

// -------------------------------------------------- lo que no se prorratea ---

test('*** «2 huevos» no se prorratea: lo usado ES el envase ***', () => {
  // *Un huevo no tiene fraccion: o compras el envase o no lo compras.*
  const huevos = ing({
    nombre: 'Huevos',
    cantidad: 2,
    unidad: 'ud',
    precio: { precioEnvaseCent: 180, cantidadEnvase: 6, unidadEnvase: 'ud' },
  })
  const r = costeDeReceta([huevos])
  // *Ni 60 (un tercio) ni nada inventado: 180, el envase.*
  assert.equal(r.ingredientes[0].costeUsadoCent, 180, 'lo usado es el envase entero')
  assert.equal(r.ingredientes[0].costeEnvaseCent, 180)
})

test('y `uds` en plural tampoco se prorratea', () => {
  const r = costeDeReceta([ing({ unidad: 'ud', cantidad: 1,
    precio: { precioEnvaseCent: 180, cantidadEnvase: 6, unidadEnvase: 'uds' } })])
  assert.equal(r.ingredientes[0].costeUsadoCent, 180)
})

// ------------------------------------------------------------- lo que falta ---

test('*** un ingrediente sin precio no entra en la suma, y se NOMBRA ***', () => {
  // *«Un total sobre la mitad no es el total»: el total existe, pero se dice que falta uno.*
  const r = costeDeReceta([
    ing(),
    ing({ nombre: 'Azafran', precio: null }),
  ])
  assert.equal(r.conDatos, 1)
  assert.deepEqual(r.sinDatos, ['Azafran'])
  assert.equal(r.completo, false, 'falta uno, luego no esta completo')
  // *Pero el total de lo que si se sabe existe: 24, no null.*
  assert.equal(r.usadoCent, 24)
})

test('*** sin ningun dato, el total es null y no cero ***', () => {
  const r = costeDeReceta([ing({ precio: null }), ing({ nombre: 'Sal', precio: null })])
  assert.equal(r.usadoCent, null, 'no saber no es cero')
  assert.equal(r.envaseCent, null)
  assert.equal(r.conDatos, 0)
  assert.deepEqual(r.sinDatos, ['Arroz', 'Sal'])
  assert.equal(r.completo, false)
})

test('con todos los datos, esta completo y no falta nadie', () => {
  const r = costeDeReceta([ing(), ing({ nombre: 'Leche', precio: { precioEnvaseCent: 100, cantidadEnvase: 1000, unidadEnvase: 'ml' } })])
  assert.equal(r.completo, true)
  assert.deepEqual(r.sinDatos, [])
  // *44 y no 124: `ing()` fija `cantidad: 200`, asi que la leche son 200 ml de un envase de 1000 a
  // 100 centimos -- 20 centimos, no 100.* *Lo cace porque la prueba fallo: 24 + 20 = 44.*
  assert.equal(r.usadoCent, 24 + 20)
  // *Y lo que se compra son los dos envases enteros.*
  assert.equal(r.envaseCent, 120 + 100)
})

// -------------------------------------------------- el €/unidad ya normalizado ---

test('*** `precioUnidadCent` es centimos por UNA unidad, no por cien ***', () => {
  // *Lo descubrio la prueba al fallar: con `precioUnidadCent: 12` y 200 g salian **2400** centimos
  // (24 EUR), no 24.* *El campo es el precio de **una** unidad en centimos -- 12 centimos el gramo --,
  // asi que la cuenta es `cantidad * precioUnidadCent`.*
  // *Es la tercera vez en dos rondas que mi expectativa era la equivocada y el codigo el correcto.*
  const caro = costeDeReceta([ing({ precio: { precioUnidadCent: 12 } })])
  assert.equal(caro.ingredientes[0].costeUsadoCent, 2400, '200 g a 12 centimos el gramo')

  // *Y el caso realista: 0,12 centimos el gramo son 24 centimos por 200 g.*
  const normal = costeDeReceta([ing({ precio: { precioUnidadCent: 0.12 } })])
  assert.equal(normal.ingredientes[0].costeUsadoCent, 24)
})

test('sin precio de envase ni por unidad, el motivo lo dice', () => {
  const r = costeDeReceta([ing({ precio: {} })])
  assert.equal(r.ingredientes[0].costeUsadoCent, null)
  assert.ok(r.ingredientes[0].motivo, 'tiene que haber un motivo legible')
})

// --------------------------------------------------- sin cantidad no hay coste ---

test('*** un ingrediente con cantidad 0 NO cuesta 0: es un ingrediente SIN DATOS ***', () => {
  // *Lo que pasaba: `cantidad: 0` daba `costeUsadoCent: 0`, `motivo: null` y **el total se declaraba
  // completo**. O sea que un ingrediente del que no se sabe cuanto lleva contaba como que no cuesta nada.*
  const r = costeDeReceta([
    ing({ nombre: 'Sal', cantidad: 0, precio: { precioUnidadCent: 0.5 } }),
    ing({ nombre: 'Arroz' }),
  ])
  const sal = r.ingredientes[0]
  assert.equal(sal.costeUsadoCent, null, 'sin cantidad, no hay coste')
  assert.ok(sal.motivo, 'y un motivo que dar')
  assert.match(sal.motivo, /cantidad/)
  // *Y el total lo dice: existe (24) pero **no esta completo**.*
  assert.equal(r.usadoCent, 24, 'el de los que si se saben')
  assert.equal(r.completo, false, 'y NO se declara completo')
  assert.deepEqual(r.sinDatos, ['Sal'], 'con su nombre')
})

test('*** y una cantidad negativa tampoco es un coste ***', () => {
  const r = costeDeReceta([ing({ cantidad: -5 })])
  assert.equal(r.ingredientes[0].costeUsadoCent, null)
  assert.equal(r.usadoCent, null)
})

// ------------------------------------- cuantos envases hacen falta de verdad ---

test('*** un envase de 131 g NO cubre 200 g: hacen falta DOS ***', () => {
  // *El caso que lo destapo, con numeros del gold: «ANA MARIA LAJUSTICIA Complemento alimenticio», envase de
  // 0,131 kg por 924 cent.* *Usar 200 g salia a 1410,69 cent y «comprar» decia 924 -- porque 200 g no caben
  // en 131.* *Lo que sale del bolsillo son **1.848** cent, dos envases.*
  const r = costeDeReceta([{
    nombre: 'Complemento', cantidad: 200, unidad: 'g',
    precio: { precioEnvaseCent: 924, cantidadEnvase: 131, unidadEnvase: 'g' },
  }])
  assert.equal(r.ingredientes[0].envasesQueHacenFalta, 2, 'dos envases de 131 g')
  assert.equal(r.envaseCent, 924, 'el de UN envase, como siempre')
  assert.equal(r.envasesCent, 1848, 'y lo que sale del bolsillo: dos')
})

test('*** con un envase que llega, es UNO ***', () => {
  const r = costeDeReceta([ing({ cantidad: 200 })])
  assert.equal(r.ingredientes[0].envasesQueHacenFalta, 1)
  assert.equal(r.envasesCent, 120, 'igual que `envaseCent`: el envase llega')
})

test('*** y la suma mezcla los dos casos ***', () => {
  const r = costeDeReceta([
    ing({ nombre: 'Complemento', cantidad: 200,
      precio: { precioEnvaseCent: 924, cantidadEnvase: 131, unidadEnvase: 'g' } }),
    ing({ nombre: 'Arroz', cantidad: 200 }),
  ])
  assert.equal(r.envasesCent, 924 * 2 + 120, 'dos del primero y uno del segundo')
})

test('*** en unidades, el envase es uno: o lo compras o no ***', () => {
  const r = costeDeReceta([ing({ unidad: 'ud', cantidad: 2,
    precio: { precioEnvaseCent: 180, cantidadEnvase: 6, unidadEnvase: 'ud' } })])
  assert.equal(r.ingredientes[0].envasesQueHacenFalta, 1)
})

test('*** y si falta el dato, `null`: no se inventa un envase ***', () => {
  const r = costeDeReceta([ing({ cantidad: 0 })])
  assert.equal(r.ingredientes[0].envasesQueHacenFalta, null)
})

