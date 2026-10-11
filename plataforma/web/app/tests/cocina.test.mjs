import { test } from 'node:test'
import assert from 'node:assert/strict'
import { etiquetasDe, etiquetasDeUna, filtraRecetas, textoDelVacio } from '../src/logica/recetario.ts'
import { calcular, listaReceta, validarReceta } from '../src/estado/cocina.ts'
import { referenciaLinea } from '../src/estado/referenciaLinea.ts'
import { aMs, filasDeChispa, serieDeChispa } from '../src/logica/chispa.ts'
import { importeEnCentimos, textoDeLoQueFalta, textoDePeriodo, totalConocido } from '../src/logica/gasto.ts'
import { costeDeReceta } from '../src/logica/costeReceta.ts'
import { avisoDeTransporte, hayVariosViajes } from '../src/logica/transporte.ts'

const ingrediente = { nombre: 'Arroz crudo', cantidad: 200, base: '100g', kcal: 350, proteinas: null, hidratos: 80, grasas: 0 }
const receta = { version: 1, nombre: 'Prueba', raciones: 2, ingredientes: [ingrediente] }
test('la eleccion exacta gana al grupo y funciona sin grupo', () => {
  assert.deepEqual(referenciaLinea(42, 'dia:123'), { grupo_id: null, producto_id: 'dia:123' })
  assert.deepEqual(referenciaLinea(undefined, 'dia:123'), { grupo_id: null, producto_id: 'dia:123' })
  assert.deepEqual(referenciaLinea(42), { grupo_id: 42, producto_id: null })
  assert.throws(() => referenciaLinea())
})
test('raciones y cero real', () => {
  assert.equal(calcular(receta, 1).kcal.valor, 350)
  assert.equal(calcular(receta, 1).grasas.valor, 0)
  assert.equal(calcular(receta, 1).proteinas.valor, null)
  assert.equal(calcular(receta, 1).proteinas.faltantes, 1)
})
test('subtotal no convierte ausencias en ceros conocidos', () => {
  const r = { ...receta, ingredientes: [ingrediente, { ...ingrediente, kcal: null }] }
  assert.deepEqual(calcular(r, 2).kcal, { valor: 700, faltantes: 1 })
})
test('cantidades se escalan sin conversion implicita ml/g', () => {
  assert.equal(listaReceta({ ...receta, ingredientes: [{ ...ingrediente, base: '100ml' }] }, 4), 'Arroz crudo: 400.0 ml')
})
test('JSON ajeno, infinito, negativos y unidades no admitidas fallan', () => {
  for (const r of [null, {}, { ...receta, raciones: 0 }, { ...receta, raciones: Infinity },
    { ...receta, ingredientes: [{ ...ingrediente, cantidad: -1 }] },
    { ...receta, ingredientes: [{ ...ingrediente, base: 'porcion' }] },
    { ...receta, ingredientes: [{ ...ingrediente, kcal: '100' }] }]) assert.throws(() => validarReceta(r))
})
test('apunte calculado no depende de cambios posteriores', () => {
  const n = calcular(receta, 1).kcal.valor
  const r = { ...receta, ingredientes: [{ ...ingrediente, kcal: 400 }] }
  assert.equal(n, 350)
  assert.equal(calcular(r, 1).kcal.valor, 400)
})
// --- G05: la chispa no puede dibujar lo que no se observo --------------------
// Las tres reglas son del documento y se fijan aqui, porque `tsc` verde dice que compila y no que
// acierte. La primera es la que mas importa: **un hueco no se conecta**.
test('un hueco en la serie NO se conecta', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 100 },
    { fecha: '2026-01-02', valor: null },
    { fecha: '2026-01-03', valor: 120 },
  ])
  assert.deepEqual(s.ys, [100, null, 120])
  assert.equal(s.dibujados, 3, 'un hueco cuenta como punto: esta en la serie, sin valor')
  assert.equal(s.dibujable, true)
  assert.equal(s.sinFecha, 0)
})

test('una serie vacia NO dice «solo un dia»', () => {
  const s = serieDeChispa([])
  assert.equal(s.dibujable, false)
  assert.equal(s.total, 0)
  assert.equal(s.dibujados, 0)
})

test('una fecha ilegible no se coloca en 1970, se descarta', () => {
  assert.equal(aMs(''), null)
  assert.equal(aMs('no-es-una-fecha'), null)
  assert.equal(aMs('2026-01-01'), Date.parse('2026-01-01T00:00:00'))
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 100 },
    { fecha: 'no-es-una-fecha', valor: 999 },
  ])
  assert.equal(s.dibujados, 1)
  assert.equal(s.sinFecha, 1, 'y se cuenta: una ausencia se declara, no se disimula')
  assert.deepEqual(s.ys, [100])
})

test('un valor no finito es un hueco, no un cero', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: Number.NaN },
    { fecha: '2026-01-02', valor: Number.POSITIVE_INFINITY },
  ])
  assert.deepEqual(s.ys, [null, null])
  assert.equal(s.dibujados, 2)
})
test('la tabla lista los huecos, y los lee como «sin dato»', () => {
  const filas = filasDeChispa([
    { fecha: '2026-01-01', valor: 1.5 },
    { fecha: '2026-01-02', valor: null },
    { fecha: '2026-01-03', valor: 1.8 },
  ], '€')
  assert.equal(filas.length, 3, 'el hueco es una fila, no se omite')
  assert.equal(filas[1].valor, null)
  assert.equal(filas[1].texto, 'sin dato')
  assert.equal(filas[0].texto, '1.5 €')
  assert.equal(filas[2].texto, '1.8 €')
})
test('una serie que mezcla unidades NO se dibuja como una sola linea', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: '2026-01-02', valor: 155, unidad: 'kg' },
    { fecha: '2026-01-03', valor: 90, unidad: 'ud' },
  ])
  assert.equal(s.dibujable, false, 'kg y ud no son la misma escala')
  assert.deepEqual(s.unidades, ['kg', 'ud'])
  assert.match(s.motivoUnidad, /cambió en el histórico \(kg, ud\)/)
})

test('una serie con una sola unidad SI se dibuja', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: '2026-01-02', valor: 155, unidad: 'kg' },
  ])
  assert.equal(s.dibujable, true)
  assert.deepEqual(s.unidades, ['kg'])
  assert.equal(s.motivoUnidad, null)
})

test('sin unidad, se dibuja: la API puede no mandarla y eso no rompe nada', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150 },
    { fecha: '2026-01-02', valor: 155 },
  ])
  assert.equal(s.dibujable, true)
  assert.deepEqual(s.unidades, [])
  assert.equal(s.motivoUnidad, null)
})

test('el punto descartado por fecha no decide que la serie mezcla', () => {
  const s = serieDeChispa([
    { fecha: '2026-01-01', valor: 150, unidad: 'kg' },
    { fecha: 'no-fecha', valor: 90, unidad: 'ud' },
  ])
  assert.equal(s.dibujable, true, 'el de ud no se dibuja, asi que no mezcla nada')
  assert.deepEqual(s.unidades, ['kg'])
})

// --- G05: el gasto, y la regla de que `null` no es `0` -----------------------

test('un periodo sin total conocido NO es un cero: no se sabe', () => {
  const fila = {
    periodo: '2026-10', total_cent: null, compras: 2,
    con_importe: 0, sin_importe: 2, lineas_sin_precio: 4, completo: false,
  }
  assert.equal(totalConocido(fila), false, 'y por eso se dice, no se pinta un 0')
  assert.equal(importeEnCentimos(fila), null)
  assert.equal(textoDeLoQueFalta(fila), 'faltan 4 lineas sin precio')
})

test('un cero SABIDO si es conocido: se pinta y no se avisa de nada', () => {
  const fila = {
    periodo: '2026-10', total_cent: 0, compras: 1,
    con_importe: 1, sin_importe: 0, lineas_sin_precio: 0, completo: true,
  }
  assert.equal(totalConocido(fila), true, 'algo que salio gratis es un cero sabido')
  assert.equal(importeEnCentimos(fila), 0)
  assert.equal(textoDeLoQueFalta(fila), null)
})

test('un total parcial se dice CON lo que le falta', () => {
  const fila = {
    periodo: '2026-10', total_cent: 15000, compras: 3,
    con_importe: 2, sin_importe: 1, lineas_sin_precio: 2, completo: false,
  }
  assert.equal(totalConocido(fila), true)
  assert.equal(importeEnCentimos(fila), 15000)
  assert.equal(textoDeLoQueFalta(fila), 'faltan 2 lineas sin precio',
    'el numero esta y se dice que no esta completo: las dos cosas')
})

test('una sola linea que falta se dice en singular', () => {
  const fila = {
    periodo: '2026-W41', total_cent: 500, compras: 1,
    con_importe: 1, sin_importe: 0, lineas_sin_precio: 1, completo: false,
  }
  assert.equal(textoDeLoQueFalta(fila), 'falta 1 linea sin precio')
})

test('el periodo se dice legible, y una fila sin periodo lo dice', () => {
  const base = { total_cent: 0, compras: 1, con_importe: 1, sin_importe: 0, completo: true }
  assert.equal(textoDePeriodo({ ...base, periodo: '2026-10' }, false), 'octubre de 2026')
  assert.equal(textoDePeriodo({ ...base, periodo: '2026-W41' }, true), '2026 · semana 41')
  assert.equal(textoDePeriodo({ ...base, periodo: null }, false), 'Sin fecha')
})

// --- G05: el coste de una receta -- lo que usas y lo que compras -------------

test('200 g de un paquete de 1 kg a 1,20 EUR: usado 24 centimos, envase 120', () => {
  const r = costeDeReceta([
    { nombre: 'Arroz', cantidad: 200, unidad: 'g',
      precio: { precioEnvaseCent: 120, cantidadEnvase: 1000, unidadEnvase: 'g' } },
  ])
  assert.equal(r.ingredientes[0].costeUsadoCent, 24, 'la quinta parte de 1,20')
  assert.equal(r.ingredientes[0].costeEnvaseCent, 120, 'y el envase entero es otro numero')
  assert.equal(r.usadoCent, 24)
  assert.equal(r.envaseCent, 120)
  assert.equal(r.completo, true)
  assert.deepEqual(r.sinDatos, [])
})

test('en unidades NO se prorratea: un huevo no tiene fraccion', () => {
  const r = costeDeReceta([
    { nombre: 'Huevos', cantidad: 2, unidad: 'ud',
      precio: { precioEnvaseCent: 210, cantidadEnvase: 12, unidadEnvase: 'ud' } },
  ])
  assert.equal(r.ingredientes[0].costeUsadoCent, 210,
    'lo que usas cuesta el envase: 2 de 12 no son 35 centimos, son el envase que compras')
  assert.equal(r.ingredientes[0].costeEnvaseCent, 210)
})

test('sin saber cuanto trae el envase, lo usado no se inventa', () => {
  const r = costeDeReceta([
    { nombre: 'Azafran', cantidad: 0.4, unidad: 'g',
      precio: { precioEnvaseCent: 350, cantidadEnvase: null, unidadEnvase: 'g' } },
  ])
  assert.equal(r.ingredientes[0].costeUsadoCent, null)
  assert.equal(r.ingredientes[0].costeEnvaseCent, 350, 'el envase si se sabe')
  assert.match(r.ingredientes[0].motivo, /cuánto trae/)
  assert.deepEqual(r.sinDatos, [], 'no es «sin datos»: se sabe el envase')
  assert.equal(r.usadoCent, null, 'y el total de lo usado NO es 0: no se sabe')
  assert.equal(r.envaseCent, 350)
})

test('un ingrediente sin precio se cuenta y se nombra', () => {
  const r = costeDeReceta([
    { nombre: 'Arroz', cantidad: 200, unidad: 'g',
      precio: { precioEnvaseCent: 120, cantidadEnvase: 1000, unidadEnvase: 'g' } },
    { nombre: 'Sal', cantidad: 5, unidad: 'g', precio: null },
  ])
  assert.deepEqual(r.sinDatos, ['Sal'])
  assert.equal(r.completo, false, 'un total sobre la mitad no es el total')
  assert.equal(r.usadoCent, 24, 'y lo que si se sabe se suma')
  assert.equal(r.conDatos, 1)
})

test('sin ningun dato, los dos totales son null y no cero', () => {
  const r = costeDeReceta([{ nombre: 'Sal', cantidad: 5, unidad: 'g', precio: null }])
  assert.equal(r.usadoCent, null)
  assert.equal(r.envaseCent, null)
  assert.equal(r.completo, false)
})

test('el €/unidad del catalogo manda, y el envase se sigue diciendo', () => {
  const r = costeDeReceta([
    { nombre: 'Leche', cantidad: 250, unidad: 'ml',
      precio: { precioEnvaseCent: 95, cantidadEnvase: 1000, unidadEnvase: 'ml',
                precioUnidadCent: 0.09 } },
  ])
  assert.equal(r.ingredientes[0].costeUsadoCent, 23, '0,0009 EUR/ml x 250 ml = 22,5 -> 23')
  assert.equal(r.ingredientes[0].costeEnvaseCent, 95)
})

// --- G05: lo que el total del reparto NO incluye -----------------------------

test('con dos tiendas, el aviso dice que son dos viajes', () => {
  const t = avisoDeTransporte(2)
  assert.match(t, /no incluye el transporte ni el tiempo/)
  assert.match(t, /2 tiendas hay 2 viajes/, 'y con mas de una tienda se nombra el viaje')
  assert.equal(hayVariosViajes(2), true)
})

test('con una sola tienda, el aviso sigue estando', () => {
  const t = avisoDeTransporte(1)
  assert.match(t, /no incluye el transporte ni el tiempo/,
    'una tienda tambien es un viaje, aunque el aviso no tenga que comparar')
  assert.doesNotMatch(t, /viajes/)
  assert.equal(hayVariosViajes(1), false)
})

test('con cinco tiendas no se promete que el ahorro compense', () => {
  const t = avisoDeTransporte(5)
  assert.match(t, /5 tiendas hay 5 viajes/)
  assert.match(t, /puede ser menor/)
})

// --- G12, punto 218: el buscador del recetario ---------------------------------------------
//
// **Sin dependencias y sin servidor**: `filtraRecetas` es una funcion pura, y por eso se puede
// probar aqui en medio segundo. *La lista que llega ya viene filtrada por dueno desde el servidor, asi
// que filtrar en el cliente no puede enseñar nada que no fuera tuyo.*

const RECETAS = [
  { id: 1, nombre: 'Tortilla de patatas', etiquetas: ['cena', 'espanola'] },
  { id: 2, nombre: 'Tortilla francesa', etiquetas: ['cena'] },
  { id: 3, nombre: 'Ensalada de atun', etiquetas: ['comida', 'rapida'] },
  { id: 4, nombre: 'Guiso viejo', etiquetas: [], archivada: true },
]

test('el buscador encuentra por nombre y no le importan los acentos', () => {
  assert.equal(filtraRecetas(RECETAS, { texto: 'tortilla' }).length, 2)
  // «atun» encuentra «atún»: quien busca en la cocina no pone tildes.
  assert.deepEqual(filtraRecetas(RECETAS, { texto: 'atun' }).map((r) => r.id), [3])
})

test('todas las palabras tienen que aparecer, no una', () => {
  // **Y esto es a proposito**: buscar «tortilla patatas» y que salga cualquier tortilla es peor que
  // no encontrar nada, porque te hace leer la lista entera.
  assert.deepEqual(filtraRecetas(RECETAS, { texto: 'tortilla patatas' }).map((r) => r.id), [1])
  assert.equal(filtraRecetas(RECETAS, { texto: 'tortilla garbanzos' }).length, 0)
})

test('las archivadas no salen salvo que se pidan', () => {
  assert.equal(filtraRecetas(RECETAS, { texto: 'guiso' }).length, 0)
  assert.equal(filtraRecetas(RECETAS, { texto: 'guiso', incluirArchivadas: true }).length, 1)
})

test('el filtro por etiqueta, y las etiquetas que hay para elegir', () => {
  assert.deepEqual(filtraRecetas(RECETAS, { etiqueta: 'cena' }).map((r) => r.id), [1, 2])
  assert.deepEqual(etiquetasDe(RECETAS), ['cena', 'comida', 'espanola', 'rapida'])
})

test('el vacio dice que filtro lo causo, en vez de parecer que no hay recetas', () => {
  // *Un filtro que esconde todo sin decir por que es lo mismo que una lista vacia, y peor.*
  const texto = textoDelVacio({ texto: 'garbanzos' }, 4)
  assert.ok(texto.includes('garbanzos'), 'nombra lo que se busco')
  assert.ok(texto.includes('4 recetas'), 'y dice cuantas hay en total')
  assert.equal(textoDelVacio({}, 0), 'Todavia no hay recetas.')
})

test('el orden de la lista no se toca', () => {
  // Reordenar por parecido es lo que hace que una busqueda parezca que «encuentra» cosas.
  const ids = filtraRecetas(RECETAS, { etiqueta: 'cena' }).map((r) => r.id)
  assert.deepEqual(ids, [1, 2], 'el orden del servidor se respeta')
})

test('las etiquetas se leen vengan como lista o como la cadena que manda el servidor', () => {
  // **El servidor manda una `string`** -- la columna `etiquetas` de `version` es texto -- y declarar
  // solo la lista fue un error de tipo que `tsc` cazo. Se aceptan las dos.
  assert.deepEqual(etiquetasDeUna({ id: 1, nombre: 'x', etiquetas: 'cena,rapida' }), ['cena', 'rapida'])
  assert.deepEqual(etiquetasDeUna({ id: 1, nombre: 'x', etiquetas: ['cena'] }), ['cena'])
  assert.deepEqual(etiquetasDeUna({ id: 1, nombre: 'x', etiquetas: '' }), [])
  assert.deepEqual(etiquetasDeUna({ id: 1, nombre: 'x' }), [])
  // Y el filtro funciona igual con la forma del servidor.
  assert.deepEqual(
    filtraRecetas([{ id: 7, nombre: 'Guiso', etiquetas: 'cena,larga' }], { etiqueta: 'cena' }).map((r) => r.id),
    [7])
})
