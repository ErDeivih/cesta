/**
 * *** LAS CIFRAS DE SALUD, PROBADAS SIN MONTAR LA PANTALLA. ***
 *
 * *`logica/salud.ts` hace dos cosas y las dos se pueden medir sin React: el reparto de
 * referencia (cifra, fuente y fecha) y la cuenta de la estimación. Lo que se vigila aquí:*
 *
 *   1. **La cuenta es la declarada.** *El caso del encargo —hombre de 35 años, 75 kg, 175 cm y
 *      actividad moderada— da 2.594,3 kcal; el rango, 2.330–2.850.*
 *   2. **El ajuste es el que se dice.** *Mantener 0; perder −400 (horquilla −300 a −500); ganar
 *      +400. Nunca se aplica solo: `calcularEstimacion` exige el objetivo elegido.*
 *   3. **Fuera de los límites no hay cifra.** *Ni con 13 años ni con 300 kg: `null`.*
 *   4. **Cada cifra tiene fuente, enlace y fecha.** *Las seis pautas, los tres macros, los cinco
 *      niveles de actividad y los tres objetivos. Un número sin de dónde sale es lo que se
 *      persigue.*
 *   5. **El «por qué» no lleva la cuenta dentro.** *Dice el gasto, el ajuste y para qué; no la
 *      fórmula.*
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  ACTIVIDAD,
  ACTIVIDADES,
  AJUSTES,
  AVISO_MEDICO,
  FUENTES,
  LIMITES,
  OBJETIVOS,
  PAUTAS_SALUD,
  RANGOS_MACROS,
  ajusteAplicado,
  calcularEstimacion,
  datosDentroDeRango,
  gastoConRango,
  gastoEstimado,
  gramosDeMacros,
  macrosDelObjetivo,
  porQueDelObjetivo,
  rangoEstimado,
} from '../src/logica/salud.ts'

/** El caso del encargo: hombre de 35, 75 kg, 175 cm, actividad moderada. */
const CASO = { sexo: 'hombre', edad: 35, peso: 75, altura: 175, actividad: 'moderado' }

// *Con `useGrouping` forzado: las cuatro cifras se leen «2.594» y no «2594», igual que en la
// pantalla. Sin él, el formateador de es-ES deja los cuatro dígitos sin separador.*
const cifra = (n) => new Intl.NumberFormat('es-ES', {
  maximumFractionDigits: 0,
  useGrouping: true,
}).format(n)

// ------------------------------------------------------------------ la cuenta ---

test('*** el caso del encargo da 2.594,3 kcal de gasto ***', () => {
  const gasto = gastoEstimado(CASO)
  assert.ok(gasto !== null)
  assert.ok(Math.abs(gasto - 2594.3125) < 1e-6, `salió ${gasto}`)
})

test('*** la misma persona con la variante de mujer baja de 1.507,8 a 2.337,0 ***', () => {
  const gasto = gastoEstimado({ ...CASO, sexo: 'mujer' })
  assert.ok(gasto !== null)
  assert.ok(Math.abs(gasto - 2337.0125) < 1e-6, `salió ${gasto}`)
})

test('*** a más actividad, más gasto; y siempre un número, no una caja ***', () => {
  const poco = gastoEstimado({ ...CASO, actividad: 'poco' })
  const mucho = gastoEstimado({ ...CASO, actividad: 'mucho' })
  assert.ok(poco !== null && mucho !== null)
  assert.ok(mucho > poco)
  // Los cinco niveles existen y suben.
  assert.equal(ACTIVIDADES.length, 5)
  for (let i = 1; i < ACTIVIDADES.length; i += 1) {
    assert.ok(ACTIVIDAD[ACTIVIDADES[i]].factor > ACTIVIDAD[ACTIVIDADES[i - 1]].factor)
  }
})

test('*** el rango es ±10 % redondeado a decenas, con el centro en medio ***', () => {
  assert.deepEqual(rangoEstimado(2594.3125), { bajo: 2330, alto: 2850, centro: 2590 })
  // Y redondea de verdad: 2.000 exactos se quedan en 2.000.
  assert.deepEqual(rangoEstimado(2000), { bajo: 1800, alto: 2200, centro: 2000 })
})

test('*** sin datos no hay gasto ni rango ***', () => {
  assert.equal(gastoEstimado({ ...CASO, edad: Number.NaN }), null)
  assert.equal(gastoConRango({ ...CASO, peso: 0 }), null)
  assert.equal(calcularEstimacion(null, 'mantener'), null)
})

// ------------------------------------------------ los límites de lo razonable ---

test('*** los límites son los declarados: 14-100, 30-250 y 120-230 ***', () => {
  assert.deepEqual(LIMITES, {
    edad: { min: 14, max: 100 },
    peso: { min: 30, max: 250 },
    altura: { min: 120, max: 230 },
  })
  assert.equal(datosDentroDeRango({ ...CASO, edad: 14, peso: 30, altura: 120 }), true)
  assert.equal(datosDentroDeRango({ ...CASO, edad: 100, peso: 250, altura: 230 }), true)
  assert.equal(datosDentroDeRango({ ...CASO, edad: 13 }), false)
  assert.equal(datosDentroDeRango({ ...CASO, edad: 101 }), false)
  assert.equal(datosDentroDeRango({ ...CASO, peso: 29 }), false)
  assert.equal(datosDentroDeRango({ ...CASO, peso: 251 }), false)
  assert.equal(datosDentroDeRango({ ...CASO, altura: 119 }), false)
  assert.equal(datosDentroDeRango({ ...CASO, altura: 231 }), false)
})

test('*** fuera de los límites no se calcula, aunque se elija objetivo ***', () => {
  assert.equal(calcularEstimacion({ ...CASO, edad: 13 }, 'perder'), null)
  assert.equal(calcularEstimacion({ ...CASO, peso: 251 }, 'ganar'), null)
  assert.equal(gastoConRango({ ...CASO, altura: 119 }), null)
})

// ------------------------------------------------------------ el objetivo ---

test('*** mantener no ajusta; perder baja 400; ganar sube 400 ***', () => {
  assert.equal(ajusteAplicado('mantener'), 0)
  assert.equal(ajusteAplicado('perder'), -400)
  assert.equal(ajusteAplicado('ganar'), 400)
  assert.equal(AJUSTES.perder.min, -500)
  assert.equal(AJUSTES.perder.max, -300)
  assert.equal(AJUSTES.ganar.min, 300)
  assert.equal(AJUSTES.ganar.max, 500)
  assert.deepEqual(OBJETIVOS, ['mantener', 'perder', 'ganar'])
})

test('*** el objetivo se enseña con su rango, y el rango es de la cifra ajustada ***', () => {
  const mantener = calcularEstimacion(CASO, 'mantener')
  assert.ok(mantener !== null)
  assert.equal(mantener.centro, 2590)
  assert.equal(mantener.bajo, 2330)
  assert.equal(mantener.alto, 2850)
  assert.equal(mantener.ajuste, 0)

  const perder = calcularEstimacion(CASO, 'perder')
  assert.ok(perder !== null)
  assert.equal(perder.gasto, 2594.3125)
  assert.equal(perder.ajuste, -400)
  assert.equal(perder.centro, 2190)
  assert.equal(perder.bajo, 1970)
  assert.equal(perder.alto, 2410)

  const ganar = calcularEstimacion(CASO, 'ganar')
  assert.ok(ganar !== null)
  assert.equal(ganar.centro, 2990)
  assert.equal(ganar.bajo, 2690)
  assert.equal(ganar.alto, 3290)
})

// --------------------------------------------------------------- los macros ---

test('*** los rangos de macros son los de las fuentes citadas ***', () => {
  const porClave = Object.fromEntries(RANGOS_MACROS.map((m) => [m.clave, m]))
  assert.equal(porClave.proteina.pctMin, 10)
  assert.equal(porClave.proteina.pctMax, 15)
  assert.equal(porClave.grasas.pctMin, 15)
  assert.equal(porClave.grasas.pctMax, 30)
  assert.equal(porClave.hidratos.pctMin, 45)
  assert.equal(porClave.hidratos.pctMax, 60)
})

test('*** los gramos del centro, con su horquilla, para 2.190 kcal ***', () => {
  const macros = macrosDelObjetivo(2190)
  assert.equal(macros.length, 3)
  const porClave = Object.fromEntries(macros.map((m) => [m.clave, m]))
  assert.deepEqual(
    {
      gramos: porClave.proteina.gramos,
      min: porClave.proteina.gramosMin,
      max: porClave.proteina.gramosMax,
    },
    { gramos: 68, min: 55, max: 82 },
  )
  assert.deepEqual(
    {
      gramos: porClave.grasas.gramos,
      min: porClave.grasas.gramosMin,
      max: porClave.grasas.gramosMax,
    },
    { gramos: 55, min: 37, max: 73 },
  )
  assert.deepEqual(
    {
      gramos: porClave.hidratos.gramos,
      min: porClave.hidratos.gramosMin,
      max: porClave.hidratos.gramosMax,
    },
    { gramos: 287, min: 246, max: 329 },
  )
})

test('*** el centro de cada macro cae dentro de su horquilla, a cualquier cifra ***', () => {
  for (const kcal of [1400, 1800, 2190, 2590, 3200]) {
    for (const macro of macrosDelObjetivo(kcal)) {
      assert.ok(macro.gramos >= macro.gramosMin, `${macro.clave} a ${kcal}`)
      assert.ok(macro.gramos <= macro.gramosMax, `${macro.clave} a ${kcal}`)
      // Y los gramos, pasados a energía, son una parte razonable del total: los tres rangos no
      // suman 100 %, pero tampoco pueden sumar el 40 % ni el 200 %.
      const energia = macro.gramos * (macro.clave === 'grasas' ? 9 : 4)
      assert.ok(energia > 0 && energia < kcal)
    }
  }
  // Sin energía no se inventan gramos.
  assert.deepEqual(macrosDelObjetivo(0), [])
  assert.deepEqual(macrosDelObjetivo(Number.NaN), [])
})

test('*** los gramos que se guardan son los del centro ***', () => {
  assert.deepEqual(gramosDeMacros(2190), { proteina: 68, grasas: 55, hidratos: 287 })
  assert.deepEqual(gramosDeMacros(2590), { proteina: 81, grasas: 65, hidratos: 340 })
})

// ------------------------------------------------------- fuente y fecha, una a una ---

test('*** cada pauta lleva su cifra, su fuente y su enlace ***', () => {
  assert.equal(PAUTAS_SALUD.length, 6)
  const claves = new Set()
  for (const pauta of PAUTAS_SALUD) {
    assert.ok(pauta.titulo.length > 0, `sin título: ${pauta.clave}`)
    assert.ok(pauta.cifra.length > 0, `sin cifra: ${pauta.clave}`)
    assert.ok(pauta.fuentes.length >= 1, `sin fuente: ${pauta.clave}`)
    assert.ok(!claves.has(pauta.clave), `repetida: ${pauta.clave}`)
    claves.add(pauta.clave)
    for (const fuente of pauta.fuentes) {
      assert.match(fuente.url, /^https:\/\//, `enlace roto en ${pauta.clave}`)
      assert.ok(fuente.fecha.length > 0, `sin fecha en ${pauta.clave}`)
      assert.ok(fuente.nombre.length > 0, `sin nombre en ${pauta.clave}`)
    }
  }
})

test('*** las cifras de las pautas son las de las fuentes, no unas parecidas ***', () => {
  const porClave = Object.fromEntries(PAUTAS_SALUD.map((p) => [p.clave, p]))
  assert.match(porClave.fibra.cifra, /25 g/)
  assert.match(porClave.azucar.cifra, /10 %/)
  assert.match(porClave.azucar.cifra, /5 %/)
  assert.match(porClave.sal.cifra, /5 g/)
  assert.match(porClave.sal.cifra, /2\.000 mg/)
  assert.match(porClave.agua.cifra, /2,0 L/)
  assert.match(porClave.agua.cifra, /2,5 L/)
  assert.match(porClave.frutaVerdura.cifra, /400 g/)
  assert.match(porClave.alcohol.cifra, /[Nn]ingún nivel/)
})

test('*** cada macro, cada nivel y cada objetivo tienen fuente con enlace y fecha ***', () => {
  const fuentes = [
    ...RANGOS_MACROS.map((m) => m.fuente),
    ...ACTIVIDADES.map((a) => ACTIVIDAD[a].fuente),
    ...OBJETIVOS.map((o) => AJUSTES[o].fuente),
    ...Object.values(FUENTES),
  ]
  for (const fuente of fuentes) {
    assert.match(fuente.url, /^https:\/\//, `enlace roto: ${fuente.nombre}`)
    assert.ok(fuente.fecha.length > 0, `sin fecha: ${fuente.nombre}`)
    assert.ok(fuente.documento.length > 0, `sin documento: ${fuente.nombre}`)
  }
  // Y son las que se han verificado: ni una de más, ni una de menos.
  assert.equal(Object.keys(FUENTES).length, 8)
})

// ------------------------------------------------------------- el «por qué» ---

test('*** el «por qué» dice el gasto y el ajuste, y no la cuenta ***', () => {
  const perder = calcularEstimacion(CASO, 'perder')
  assert.ok(perder !== null)
  const texto = porQueDelObjetivo(perder, cifra)
  assert.equal(
    texto,
    'Partimos de tu gasto estimado (2.594 kcal al día) y, para perder, ajustamos −400 kcal al día.',
  )
  assert.ok(!texto.includes('10 *'), 'la cuenta no se enseña')
  assert.ok(!/fórmula|déficit|Mifflin|PAL|TDEE/i.test(texto))

  const mantener = calcularEstimacion(CASO, 'mantener')
  assert.ok(mantener !== null)
  assert.match(porQueDelObjetivo(mantener, cifra), /no ajustamos la cifra/)

  const ganar = calcularEstimacion(CASO, 'ganar')
  assert.ok(ganar !== null)
  assert.match(porQueDelObjetivo(ganar, cifra), /\+400 kcal/)
})

test('*** por debajo del suelo de seguridad no hay objetivo para perder ***', () => {
  // Mujer de 70 años, 50 kg, 155 cm y actividad ligera: el gasto es bajo y un déficit de 400
  // dejaría el «objetivo» por debajo del suelo. No se enseña ni se guarda.
  const pequena = { sexo: 'mujer', edad: 70, peso: 50, altura: 155, actividad: 'poco' }
  const perder = calcularEstimacion(pequena, 'perder')
  assert.ok(perder !== null)
  assert.equal(perder.bajoSuelo, true)
  assert.ok(perder.centro < 1200)

  // Mantener sí se puede enseñar: es el gasto estimado, no una prescripción.
  const mantener = calcularEstimacion(pequena, 'mantener')
  assert.ok(mantener !== null)
  assert.equal(mantener.bajoSuelo, false)

  // El caso del encargo no se toca.
  const normal = calcularEstimacion(CASO, 'perder')
  assert.ok(normal !== null)
  assert.equal(normal.bajoSuelo, false)
})

test('*** el aviso médico es el texto acordado, ni más ni menos ***', () => {
  assert.equal(
    AVISO_MEDICO,
    'No es consejo médico. Si tienes una condición de salud, consulta con un profesional.',
  )
})
