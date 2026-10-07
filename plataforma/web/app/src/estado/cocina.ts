export type Nutriente = 'kcal' | 'proteinas' | 'hidratos' | 'grasas'
export const nutrientes: Nutriente[] = ['kcal', 'proteinas', 'hidratos', 'grasas']
export type Ingrediente = { nombre: string; cantidad: number; base: '100g' | '100ml';
  kcal: number | null; proteinas: number | null; hidratos: number | null; grasas: number | null }
export type Receta = { version: 1; nombre: string; raciones: number; ingredientes: Ingrediente[] }

export function validarReceta(d: unknown): Receta {
  if (!d || typeof d !== 'object') throw new Error('El archivo no contiene una receta.')
  const r = d as Receta
  if (r.version !== 1 || typeof r.nombre !== 'string' || !r.nombre.trim() || r.nombre.length > 200 ||
      !Number.isFinite(r.raciones) || r.raciones <= 0 || r.raciones > 1000 ||
      !Array.isArray(r.ingredientes) || r.ingredientes.length > 100) throw new Error('Revisa nombre, raciones y formato del archivo.')
  for (const i of r.ingredientes) {
    if (!i || typeof i.nombre !== 'string' || !i.nombre.trim() || i.nombre.length > 200 ||
        !Number.isFinite(i.cantidad) || i.cantidad <= 0 || i.cantidad > 1000000 ||
        !['100g', '100ml'].includes(i.base) || nutrientes.some(k => i[k] !== null &&
          (typeof i[k] !== 'number' || !Number.isFinite(i[k]) || i[k]! < 0 || i[k]! > 100000))) {
      throw new Error('Cada ingrediente necesita nombre, cantidad positiva y nutrientes válidos o vacíos.')
    }
  }
  return r
}

export function calcular(r: Receta, raciones = r.raciones) {
  validarReceta(r)
  if (!Number.isFinite(raciones) || raciones <= 0 || raciones > 1000) throw new Error('Indica raciones válidas.')
  return Object.fromEntries(nutrientes.map(k => {
    const conocidos = r.ingredientes.filter(i => i[k] !== null)
    return [k, { valor: conocidos.length ? conocidos.reduce((s, i) => s + i.cantidad * i[k]! / 100, 0) * raciones / r.raciones : null,
      faltantes: r.ingredientes.length - conocidos.length }]
  })) as Record<Nutriente, {valor: number | null; faltantes: number}>
}

export function listaReceta(r: Receta, raciones: number) {
  calcular(r, raciones)
  // No fusionar por parecido de nombre: no demuestra que sean el mismo ingrediente.
  return r.ingredientes.map(i => `${i.nombre}: ${(i.cantidad * raciones / r.raciones).toFixed(1)} ${i.base === '100g' ? 'g' : 'ml'}`).join('\n')
}
