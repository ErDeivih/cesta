import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { numero } from '../api/formato'
import { calcular, listaReceta, nutrientes, validarReceta } from '../estado/cocina'
import type { Ingrediente, Receta } from '../estado/cocina'

const vacia: Receta = { version: 1, nombre: 'Mi receta', raciones: 2, ingredientes: [] }
type Apunte = { id: string; fecha: string; nombre: string; raciones: number; kcal: number | null; incompleto: boolean }
const Contexto = createContext<{
  receta: Receta; guardar: (r: Receta) => void; diario: Apunte[]; setDiario: (d: Apunte[]) => void
} | null>(null)
export function CocinaProvider({ children }: { children: ReactNode }) {
  const [receta, guardar] = useState<Receta>(vacia)
  const [diario, setDiario] = useState<Apunte[]>([])
  return <Contexto.Provider value={{ receta, guardar, diario, setDiario }}>{children}</Contexto.Provider>
}
const campo = 'min-h-[44px] w-full rounded-campo border border-borde bg-papel p-2 text-tinta-fuerte dark:text-white'
const boton = 'inline-flex min-h-[44px] items-center justify-center rounded-campo bg-terracota px-4 py-2 font-medium text-white hover:bg-terracota'
function descargar(nombre: string, texto: string, tipo: string) {
  const url = URL.createObjectURL(new Blob([texto], { type: tipo }))
  const a = document.createElement('a'); a.href = url; a.download = nombre; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function hoyLocal() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function Cocina({ modo }: { modo: 'recetas' | 'calorias' }) {
  const { receta, guardar, diario, setDiario } = useContext(Contexto)!
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [porciones, setPorciones] = useState(1)
  const [fecha, setFecha] = useState(hoyLocal)
  const [ingrediente, setIngrediente] = useState({ nombre: '', cantidad: '', base: '100g', kcal: '', proteinas: '', hidratos: '', grasas: '' })
  const porcionesValidas = Number.isFinite(porciones) && porciones > 0 && porciones <= 1000
  const resumen = calcular(receta, porcionesValidas ? porciones : 1)
  const apuntes = diario.filter(a => a.fecha === fecha)
  const completos = apuntes.filter(a => a.kcal !== null)
  async function cargar(file?: File) {
    if (!file) return
    try {
      if (file.size > 200000) throw new Error('El archivo es demasiado grande.')
      guardar(validarReceta(JSON.parse(await file.text())))
      setError(''); setMensaje('Receta cargada en esta sesión.')
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo leer el archivo.') }
  }
  return <section className="mx-auto max-w-3xl space-y-6">
    <div><p className="text-cuerpo font-semibold text-terracota ">Cocina y alimentación · versión inicial</p>
      <h1 className="mt-1 text-3xl font-bold">{modo === 'recetas' ? 'Mis recetas' : 'Calorías de mis comidas'}</h1>
      <p className="mt-2 text-tinta-suave">Prepara cantidades y anota lo que comes. Comprar un producto no significa haberlo consumido.</p></div>
    <nav aria-label="Cocina" className="flex flex-wrap gap-3"><Link className={boton} to="/recetas">Recetas</Link><Link className={boton} to="/calorias">Calorías</Link></nav>
    <p className="rounded-tarjeta border border-aviso bg-marfil p-4 text-cuerpo text-aviso">Cuaderno de esta pestaña, sin sincronización con tu cuenta. Se pierde al recargar o cerrar: descarga lo que quieras conservar. Los datos nutricionales se introducen desde la etiqueta; aún no se completan desde el catálogo.</p>
    {error && <p role="alert" className="text-error ">{error}</p>}
    {mensaje && <p role="status">{mensaje}</p>}
    {modo === 'recetas' ? <>
      <div className="grid gap-4 sm:grid-cols-2"><label>Nombre de la receta<input className={campo} maxLength={200} value={receta.nombre} onChange={e => guardar({ ...receta, nombre: e.target.value.trim() ? e.target.value : 'Mi receta' })} /></label>
        <label>Raciones de la receta<input className={campo} type="number" min="1" max="1000" value={receta.raciones} onChange={e => { const n = Number(e.target.value); if (n > 0 && n <= 1000) guardar({ ...receta, raciones: n }) }} /></label></div>
      <form className="space-y-4 rounded-tarjeta border border-borde p-4 " onSubmit={e => {
        e.preventDefault()
        try {
          const i: Ingrediente = { nombre: ingrediente.nombre.trim(), cantidad: Number(ingrediente.cantidad), base: ingrediente.base as '100g' | '100ml',
            kcal: ingrediente.kcal.trim() ? Number(ingrediente.kcal) : null, proteinas: ingrediente.proteinas.trim() ? Number(ingrediente.proteinas) : null,
            hidratos: ingrediente.hidratos.trim() ? Number(ingrediente.hidratos) : null, grasas: ingrediente.grasas.trim() ? Number(ingrediente.grasas) : null }
          guardar(validarReceta({ ...receta, ingredientes: [...receta.ingredientes, i] }))
          setIngrediente({ nombre: '', cantidad: '', base: '100g', kcal: '', proteinas: '', hidratos: '', grasas: '' }); setError('')
        } catch (e) { setError(e instanceof Error ? e.message : 'Revisa los datos.') }
      }}>
        <h2 className="text-xl font-semibold">Añadir ingrediente</h2>
        <label className="block">Ingrediente y variante<input required maxLength={200} className={campo} value={ingrediente.nombre} onChange={e => setIngrediente({ ...ingrediente, nombre: e.target.value })} placeholder="Por ejemplo: arroz integral, en crudo" /></label>
        <div className="grid gap-3 sm:grid-cols-2"><label>Cantidad para toda la receta ({ingrediente.base === '100g' ? 'g' : 'ml'})<input required className={campo} type="number" min="0.1" step="any" value={ingrediente.cantidad} onChange={e => setIngrediente({ ...ingrediente, cantidad: e.target.value })} /></label>
          <label>Base de la etiqueta<select className={campo} value={ingrediente.base} onChange={e => setIngrediente({ ...ingrediente, base: e.target.value })}><option value="100g">Por 100 g</option><option value="100ml">Por 100 ml</option></select></label></div>
        <p className="text-cuerpo text-tinta-suave">Valores por 100, no por envase. Deja vacío lo desconocido. No conviertas peso cocinado en crudo ni gramos en mililitros sin equivalencia.</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{nutrientes.map(k => <label key={k}>{k === 'kcal' ? 'Energía (kcal)' : `${k[0].toUpperCase() + k.slice(1)} (g)`}<input className={campo} type="number" min="0" step="any" value={ingrediente[k]} onChange={e => setIngrediente({ ...ingrediente, [k]: e.target.value })} /></label>)}</div>
        <button className={boton}>Añadir a la receta</button>
      </form>
      <ul className="space-y-2">{receta.ingredientes.map((i, n) => <li key={n} className="flex items-center justify-between gap-3 rounded-campo border p-3"><span>{i.nombre} · {i.cantidad} {i.base === '100g' ? 'g' : 'ml'}</span><button className="min-h-[44px] px-3 underline" aria-label={`Quitar ${i.nombre}`} onClick={() => guardar({ ...receta, ingredientes: receta.ingredientes.filter((_, j) => j !== n) })}>Quitar</button></li>)}</ul>
      {!receta.ingredientes.length && <p>Todavía no hay ingredientes. Añade el primero para calcular.</p>}
      <div className="flex flex-wrap gap-3"><button className={boton} onClick={() => descargar('receta-cesta.json', JSON.stringify(receta, null, 2), 'application/json')}>Descargar receta</button>
        <label className="block">Abrir receta guardada<input className={campo} type="file" accept=".json" onChange={e => void cargar(e.target.files?.[0])} /></label></div>
    </> : <>
      <p>Receta preparada: <strong>{receta.nombre}</strong>. <Link className="underline" to="/recetas">Editar ingredientes</Link></p>
      <label className="block">Fecha de consumo<input type="date" className={campo} value={fecha} onChange={e => setFecha(e.target.value)} /></label>
    </>}
    <section className="space-y-3 rounded-tarjeta bg-marfil p-4 text-tinta-fuerte ">
      <h2 className="text-xl font-semibold">{modo === 'recetas' ? 'Cantidades y nutrición' : 'Registrar una comida'}</h2>
      <label className="block">Raciones {modo === 'recetas' ? 'que quiero preparar' : 'que he comido'}<input className={campo} type="number" min="0.1" max="1000" step="any" value={porciones} onChange={e => setPorciones(Number(e.target.value))} /></label>
      {!porcionesValidas ? <p role="alert">Introduce unas raciones mayores que cero y hasta 1000.</p> : <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">{nutrientes.map(k => <div key={k}><dt>{k === 'kcal' ? 'Calorías' : k}</dt><dd className="text-xl font-bold">{resumen[k].valor === null ? 'Sin datos' : `${numero(resumen[k].valor)} ${k === 'kcal' ? 'kcal' : 'g'}`}</dd>{resumen[k].faltantes > 0 && <p className="text-cuerpo">Datos incompletos: {resumen[k].faltantes} sin valor</p>}</div>)}</dl>}
      {modo === 'recetas' ? <button disabled={!receta.ingredientes.length || porciones <= 0 || porciones > 1000} className={boton + ' disabled:opacity-50'} onClick={() => descargar('ingredientes-compra.txt', listaReceta(receta, porciones), 'text/plain')}>Descargar ingredientes para comprar</button> :
        <button className={boton + ' disabled:opacity-50'} disabled={!receta.ingredientes.length || !fecha || porciones <= 0 || porciones > 1000} onClick={() => { setDiario([...diario, { id: crypto.randomUUID(), fecha, nombre: receta.nombre, raciones: porciones, kcal: resumen.kcal.valor, incompleto: resumen.kcal.faltantes > 0 }]); setMensaje('Comida anotada en esta pestaña. No cambia tu lista de compra.') }}>Anotar comida</button>}
    </section>
    {modo === 'calorias' && <section className="space-y-3"><h2 className="text-xl font-semibold">Lo anotado para ese día</h2>
      <p>{apuntes.length ? `Subtotal conocido: ${numero(completos.reduce((s, a) => s + a.kcal!, 0))} kcal · ${apuntes.length} ${apuntes.length === 1 ? 'comida' : 'comidas'}` : 'No has anotado comidas en esta fecha.'}</p>
      {apuntes.some(a => a.incompleto || a.kcal === null) && <p className="text-aviso ">El día está incompleto: faltan datos nutricionales. No es tu consumo total.</p>}
      <ul>{apuntes.map(a => <li key={a.id} className="flex items-center justify-between border-b py-2"><span>{a.nombre} · {numero(a.raciones)} {a.raciones === 1 ? 'ración' : 'raciones'} · {a.kcal === null ? 'Sin calorías conocidas' : `${numero(a.kcal)} kcal${a.incompleto ? ' parciales' : ''}`}</span><button className="min-h-[44px] px-3 underline" onClick={() => setDiario(diario.filter(x => x.id !== a.id))}>Deshacer</button></li>)}</ul>
      <button className={boton} onClick={() => descargar('comidas-cesta.json', JSON.stringify(diario, null, 2), 'application/json')}>Descargar registro de comidas</button>
    </section>}
    <p className="text-cuerpo text-tinta-suave">Cálculos orientativos a partir de lo que introduces. No se fijan objetivos de peso ni recomendaciones médicas. La lista descargada aún no se añade a la cesta ni escoge productos automáticamente.</p>
  </section>
}