/**
 * *** ORDEN DE LOS HOOKS: LA REGLA QUE NI TYPESCRIPT NI RUFF VEN. ***
 *
 * *Esto no es estilo: es un fallo que deja la pantalla **en blanco** y no dice por que.*
 *
 * **El 18/10/2026 paso exactamente eso en la ficha de producto.** `filasOff` estaba escrito
 * con `useMemo` **detras de tres retornos condicionales** (`if (consulta.isPending) return
 * <Cargando/>`, `if (consulta.isError)`, `if (!producto)`). *Durante la carga ese hook no se
 * ejecutaba; al llegar el producto, si.* *Un hook mas que en el render anterior, y React lanza
 * el **error 310** y desmonta la raiz.*
 *
 * *Lo que se veia: el esqueleto de `Cargando`, y **al llegar el dato, la pantalla vacia** -- con el
 * armazon incluido. Sin mensaje, porque en produccion React da el 310 **minificado**.*
 *
 * *** Y no lo cazaba nada ***: *`tsc` compila, `ruff` solo mira Python, y las pruebas de interfaz
 * miran pixeles.* *La regla la vigila esta prueba, que **lee los fuentes**, igual que
 * `tests/test_titulos.py` lee `App.tsx`.*
 *
 * *La regla, corta:* **dentro de un componente, si hay un `return` temprano, despues NO puede
 * haber ningun hook.** *O se sube el hook por encima de todos los retornos, o no es un hook.*
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const RAIZ = new URL('../src/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')

/** Un hook: `use` + mayuscula. `user`, `usar` y `usaAlgo` no lo son. */
const HOOK = /\buse[A-Z][A-Za-z0-9]*\s*\(/

/** Un retorno temprano dentro del cuerpo de la funcion: `if (...) return ...`. */
const RETORNO_TEMPRANO = /^\s{2}if\s*\(.*\)\s*return\b/

/** Un hook llamado **al nivel del cuerpo** del componente (dos espacios, sin anidar). */
const HOOK_EN_CUERPO = /^\s{2}(?:const|let|var)\s+[A-Za-z0-9_]+\s*(?::[^=]+)?=\s*use[A-Z][A-Za-z0-9]*\s*\(/
const HOOK_SUELTO = /^\s{2}use[A-Z][A-Za-z0-9]*\s*\(/

function ficheros(dir, salida = []) {
  for (const nombre of readdirSync(dir)) {
    const p = join(dir, nombre)
    if (statSync(p).isDirectory()) ficheros(p, salida)
    else if (nombre.endsWith('.tsx') || nombre.endsWith('.ts')) salida.push(p)
  }
  return salida
}

/**
 * Los tramos que son cuerpo de un componente: desde `function X(` / `export function X(`
 * hasta la linea que cierra con `}` en la columna 0.
 */
function cuerposDeComponente(texto) {
  const lineas = texto.split('\n')
  const tramos = []
  for (let i = 0; i < lineas.length; i += 1) {
    if (!/^(?:export\s+)?function\s+[A-Z]/.test(lineas[i])) continue
    let fin = i + 1
    while (fin < lineas.length && !/^\}/.test(lineas[fin])) fin += 1
    tramos.push({ nombre: (lineas[i].match(/function\s+([A-Za-z0-9_]+)/) ?? [])[1] ?? '?', desde: i, hasta: fin, lineas })
  }
  return tramos
}

/** Devuelve las infracciones de un texto fuente. Vacio = cumple. */
export function infracciones(texto, etiqueta = '') {
  const malas = []
  for (const tramo of cuerposDeComponente(texto)) {
    let primerRetorno = -1
    for (let i = tramo.desde; i <= tramo.hasta; i += 1) {
      const linea = tramo.lineas[i]
      if (primerRetorno < 0 && RETORNO_TEMPRANO.test(linea)) primerRetorno = i
      if (primerRetorno < 0) continue
      if (HOOK_EN_CUERPO.test(linea) || HOOK_SUELTO.test(linea)) {
        malas.push({
          etiqueta,
          componente: tramo.nombre,
          linea: i + 1,
          retornoEn: primerRetorno + 1,
          texto: linea.trim().slice(0, 90),
        })
      }
    }
  }
  return malas
}

test('ningun componente llama a un hook despues de un retorno temprano', () => {
  const malas = []
  for (const f of ficheros(RAIZ)) {
    const texto = readFileSync(f, 'utf8')
    if (!HOOK.test(texto)) continue
    malas.push(...infracciones(texto, relative(RAIZ, f)))
  }
  assert.deepEqual(
    malas,
    [],
    'hay hooks despues de un retorno condicional (React lanza el error 310 y deja la pantalla ' +
      'vacia, sin mensaje en el build):\n' +
      malas.map((m) => `  ${m.etiqueta}:${m.linea} en ${m.componente} -- ${m.texto} (retorno en :${m.retornoEn})`).join('\n'),
  )
})

test('la comprobacion ve la infraccion de la ficha de producto, que dejo la pantalla en blanco', () => {
  // Este texto es el que tenia `filasOff` antes del 18/10/2026: un useMemo detras de tres retornos.
  const conElFallo = [
    'export function Producto() {',
    '  const consulta = useProducto(a, b)',
    '  if (consulta.isPending) return <Cargando />',
    '  if (!producto) {',
    '    return <Vacio />',
    '  }',
    '  const filasOff = useMemo(() => producto.campos.map((c) => c), [producto])',
    '  return <div>hola</div>',
    '}',
  ].join('\n')
  const malas = infracciones(conElFallo, 'ejemplo')
  assert.equal(malas.length, 1, 'la comprobacion TIENE que ver el hook detras del retorno')
  assert.equal(malas[0].componente, 'Producto')
  assert.equal(malas[0].linea, 7)
})

test('y no se queja cuando el hook esta por encima de los retornos', () => {
  const bien = [
    'export function Producto() {',
    '  const consulta = useProducto(a, b)',
    '  const filas = useMemo(() => 1, [])',
    '  if (consulta.isPending) return <Cargando />',
    '  return <div>hola</div>',
    '}',
  ].join('\n')
  assert.deepEqual(infracciones(bien, 'ejemplo'), [])
})

test('y no confunde con hooks los nombres que empiezan por use pero no lo son', () => {
  const bien = [
    'export function X() {',
    '  if (!a) return null',
    '  const usuario = datos.user',
    '  const usarlo = 3',
    '  return <div>{usuario}{usarlo}</div>',
    '}',
  ].join('\n')
  assert.deepEqual(infracciones(bien, 'ejemplo'), [])
})
