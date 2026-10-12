/**
 * A03 — Frescura por producto, con **reloj controlado**.
 *
 * **Por que existe.** `Grupo.tsx` decidia si un precio recomienda una tienda, y tenia tres defectos
 * medidos el 12 de octubre de 2026: *tomaba la fecha de la cadena en vez del producto, dejaba decidir a
 * un precio sin fecha, y medía la antiguedad contra el dia del catalogo.* **La decision se saco a
 * `logica/frescura.ts` para poder probarla con un reloj fijo** -- *que es lo que A03 pide por su
 * nombre.*
 *
 * **Y el criterio de aceptacion esta aqui, en la ultima prueba**: *dejar de ingerir cuatro dias quita
 * las recomendaciones vigentes **sin borrar ningun dato**.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'

import { diasDesde, juzgaPrecio } from '../src/logica/frescura.ts'

/** El reloj, fijo. *Sin esto, una prueba de fechas caduca sola.* */
const HOY = new Date(2026, 9, 12) // 12 de octubre de 2026

const ctx = (extra = {}) => ({
  hoy: HOY,
  diasValidos: 3,
  publicacionIncoherente: false,
  nombreCadena: (f) => f,
  fechaTexto: (iso) => iso,
  ...extra,
})

const precio = (extra = {}) => ({
  fuente: 'mercadona',
  precioUnidadCent: 95,
  ultimoDia: '2026-10-12',
  ...extra,
})

// --------------------------------------------------------------- diasDesde ---

test('diasDesde cuenta dias de calendario, no horas', () => {
  assert.equal(diasDesde('2026-10-12', HOY), 0)
  assert.equal(diasDesde('2026-10-11', HOY), 1)
  assert.equal(diasDesde('2026-10-08', HOY), 4)
  // *Y no le importa la hora del dia: `2026-10-12T23:59` sigue siendo hoy.*
  assert.equal(diasDesde('2026-10-12T23:59:00', HOY), 0)
})

test('diasDesde dice null cuando no hay fecha que leer', () => {
  assert.equal(diasDesde(null, HOY), null)
  assert.equal(diasDesde(undefined, HOY), null)
  assert.equal(diasDesde('', HOY), null)
  assert.equal(diasDesde('ayer', HOY), null)
})

// ============================================================ LOS TRES DEFECTOS ===

test('DEFECTO 1: un producto viejo no se salva porque su cadena tenga captura de hoy', () => {
  /* **Este es el defecto tal como estaba.** *Antes, `ultimoDiaDe` miraba
   * `cadenas.find(...).ultimo_dia` -- la ultima captura de la cadena -- y un producto con una semana de
   * antiguedad pasaba por fresco.*
   *
   * *Aqui la fecha que llega es **la del producto**, y es vieja: no decide.* **Y la prueba no necesita
   * saber nada de la cadena** -- *que es justo el punto: la fecha de la cadena no es evidencia sobre
   * este producto, y por eso ya no entra en la decision.*
   */
  const j = juzgaPrecio(precio({ ultimoDia: '2026-10-05' }), ctx())
  assert.equal(j.decide, false)
  assert.match(j.motivo, /7 días/)
  // *Y el motivo dice la fecha y los dias, para que se pueda comprobar a mano en pantalla.*
  assert.match(j.motivo, /2026-10-05/)
})

test('DEFECTO 2: un precio sin fecha NO decide', () => {
  /* *Antes decidia: «sin fecha no se puede decir que sea viejo, se deja decidir».* **Y eso es recomendar
   * una tienda con un dato del que no se sabe ni el dia.** */
  const j = juzgaPrecio(precio({ ultimoDia: null }), ctx())
  assert.equal(j.decide, false)
  assert.match(j.motivo, /No sabemos de qué día/)
  // *Y se dice que se enseña igual* -- **ocultarlo seria perder el dato; dejarlo decidir seria mentir.**
  assert.match(j.motivo, /Se enseña como dato/)
})

test('DEFECTO 3: la antiguedad se mide contra HOY, no contra el dia del catalogo', () => {
  /* **Este es el defecto que el criterio de aceptacion de A03 mide.** *Con la referencia en
   * `fecha_datos`, un catalogo congelado mantenia sus precios frescos indefinidamente: la resta siempre
   * daba cero.*
   *
   * *Y por eso `juzgaPrecio` **no recibe** el dia del catalogo*: **no hay forma de colarlo**, que es mas
   * fuerte que acordarse de no usarlo.
   */
  const joven = juzgaPrecio(precio({ ultimoDia: '2026-10-11' }), ctx())
  assert.equal(joven.decide, true)

  // *El mismo precio, un mes despues: deja de decidir.* **Sin que nadie haya borrado nada.**
  const unMesDespues = juzgaPrecio(
    precio({ ultimoDia: '2026-10-11' }),
    ctx({ hoy: new Date(2026, 10, 12) }),
  )
  assert.equal(unMesDespues.decide, false)
  assert.match(unMesDespues.motivo, /32 días/)
})

// ================================================= el criterio de aceptacion ===

test('ACEPTACION: cuatro dias sin ingerir quitan las recomendaciones, sin borrar datos', () => {
  /* **El criterio, palabra por palabra**: *«dejar de ingerir cuatro dias elimina recomendaciones
   * vigentes sin borrar datos».*
   *
   * *Se simula con el reloj, que es lo unico que hace falta*: **el mismo catalogo**, con la misma ultima
   * captura, mirado desde dos dias distintos. *El 12 de octubre el precio del 12 decide; el 16, ese
   * mismo precio ya no.* **Y el precio sigue ahi** -- *lo que cambio es si recomienda, no si existe.*
   */
  const p = precio({ ultimoDia: '2026-10-12', precioUnidadCent: 95 })

  const elMismoDia = juzgaPrecio(p, ctx({ hoy: new Date(2026, 9, 12) }))
  assert.equal(elMismoDia.decide, true, 'el dia de la captura, decide')

  const tresDias = juzgaPrecio(p, ctx({ hoy: new Date(2026, 9, 15) }))
  assert.equal(tresDias.decide, true, 'a los 3 dias todavia esta dentro del limite')

  const cuatroDias = juzgaPrecio(p, ctx({ hoy: new Date(2026, 9, 16) }))
  assert.equal(cuatroDias.decide, false, 'a los 4 dias ya no recomienda tienda')
  assert.match(cuatroDias.motivo, /4 días/)

  // *Y el precio sigue siendo el mismo objeto: no se ha borrado ni mutado nada.*
  assert.equal(p.precioUnidadCent, 95)
  assert.equal(p.ultimoDia, '2026-10-12')
})

// ============================================================ los otros cortes ===

test('un catalogo incoherente no recomienda nada, ni el precio que parece bueno', () => {
  // *Corta antes que todo lo demas, y es lo que la revision anadio a la ficha.* **El orden importa**:
  // si este corte fuera el ultimo, un precio fresquisimo pasaria por bueno en un catalogo que no cuadra.
  const j = juzgaPrecio(precio(), ctx({ publicacionIncoherente: true }))
  assert.equal(j.decide, false)
  assert.match(j.motivo, /no son coherentes/)
})

test('sin precio por unidad no se compara, y el motivo lo dice', () => {
  assert.equal(juzgaPrecio(precio({ precioUnidadCent: null }), ctx()).decide, false)
  assert.equal(juzgaPrecio(precio({ precioUnidadCent: 0 }), ctx()).decide, false)
  assert.match(juzgaPrecio(precio({ precioUnidadCent: null }), ctx()).motivo, /no entra en la comparación/)
})

test('un precio con fecha en el futuro tampoco decide', () => {
  /* *Y esto no es un caso de laboratorio*: **el catalogo incoherente del 12 de octubre tiene precios del
   * 11 en una version fechada el 7**, asi que las fechas que no cuadran **ya han pasado una vez.** *Una
   * fecha por delante de hoy es un dato que no cuadra, y no se recomienda una tienda con el.*
   */
  const j = juzgaPrecio(precio({ ultimoDia: '2026-10-20' }), ctx())
  assert.equal(j.decide, false)
  assert.match(j.motivo, /todavía no ha llegado/)
})

test('una fecha ilegible se trata como no tenerla, no como estar bien', () => {
  // *Es la misma regla que en todo el proyecto: lo que no se sabe se dice, y no se deja pasar.*
  const j = juzgaPrecio(precio({ ultimoDia: 'sin-fecha' }), ctx())
  assert.equal(j.decide, false)
  assert.match(j.motivo, /no se puede leer/)
})

test('el limite es configurable y su borde es exacto', () => {
  // *`diasValidos` sale de `/api/estado` y su valor por defecto en el cliente es 3.* **El borde importa**:
  // *«mas de N» deja pasar N y corta N+1.*
  const p = precio({ ultimoDia: '2026-10-09' }) // 3 dias
  assert.equal(juzgaPrecio(p, ctx({ diasValidos: 3 })).decide, true, '3 dias con limite 3: pasa')
  assert.equal(juzgaPrecio(p, ctx({ diasValidos: 2 })).decide, false, '3 dias con limite 2: corta')
})
