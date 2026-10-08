/** Editar una receta: guardar **crea una version nueva** y la anterior se conserva.

 *  No es un formulario de "guardar cambios" a secas, y por eso lo dice: el recetario guarda versiones para
 *  que el diario pueda citar una y que no se mueva, asi que editar **anade** una version en vez de
 *  reescribir. Quien edita tiene que saberlo antes de pulsar.
 *
 *  Lo que no se cambia se hereda **copiado** en el servidor: aqui solo se mandan los campos que se tocan.
 */
import { useState } from 'react'

import { textoDeError } from '../api/cliente'
import { useCambiarReceta } from '../api/recetas'
import type { Ingrediente, Receta } from '../api/recetas'
import { Boton, Tarjeta } from './ui'

/** Las lineas del area de texto, a ingredientes. "600 g patatas" o solo "sal". */
function aIngredientes(texto: string): Ingrediente[] {
  return texto
    .split('\n')
    .map((linea) => linea.trim())
    .filter((linea) => linea.length > 0)
    .map((linea) => {
      const trozos = linea.split(' ')
      const cantidad = Number(trozos[0]?.replace(',', '.'))
      if (Number.isFinite(cantidad) && trozos.length > 2) {
        return { texto: trozos.slice(2).join(' '), cantidad, unidad: trozos[1] }
      }
      // Sin cantidad no se inventa una: se guarda el texto y ya.
      return { texto: linea }
    })
}

function deIngredientes(ingredientes: Ingrediente[]): string {
  return ingredientes
    .map((i) => [i.cantidad ?? '', i.unidad ?? '', i.texto].filter(Boolean).join(' '))
    .join('\n')
}

export function FormularioReceta({ receta }: { receta: Receta }) {
  const [abierto, setAbierto] = useState(false)
  const [nombre, setNombre] = useState(receta.nombre)
  const [raciones, setRaciones] = useState(receta.raciones_receta ?? receta.raciones)
  const [preparacion, setPreparacion] = useState(receta.preparacion)
  const [minutos, setMinutos] = useState(receta.minutos ?? 0)
  const [ingredientes, setIngredientes] = useState(deIngredientes(receta.ingredientes))
  const cambiar = useCambiarReceta(receta.id)

  if (!abierto) {
    return <Boton onClick={() => setAbierto(true)}>Editar</Boton>
  }

  return (
    <Tarjeta>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          cambiar.mutate(
            {
              nombre,
              raciones,
              preparacion,
              minutos: minutos > 0 ? minutos : null,
              ingredientes: aIngredientes(ingredientes),
            },
            { onSuccess: () => setAbierto(false) },
          )
        }}
        className="flex flex-col gap-3"
      >
        <p className="text-[13px] leading-[18px] text-aviso">
          Al guardar se crea una <strong>version nueva</strong>. La que estas viendo se conserva tal como
          esta.
        </p>

        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Nombre
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
            className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
          />
        </label>

        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Raciones
            <input
              type="number"
              min={1}
              value={raciones}
              onChange={(e) => setRaciones(Number(e.target.value))}
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1 text-[13px] text-secundaria">
            Minutos
            <input
              type="number"
              min={0}
              value={minutos}
              onChange={(e) => setMinutos(Number(e.target.value))}
              className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
            />
          </label>
        </div>

        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Ingredientes, uno por linea
          <textarea
            value={ingredientes}
            onChange={(e) => setIngredientes(e.target.value)}
            rows={5}
            className="rounded-md border border-borde-fuerte bg-papel p-2 text-[16px] leading-[22px] text-tinta-fuerte"
          />
        </label>

        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Preparacion
          <textarea
            value={preparacion}
            onChange={(e) => setPreparacion(e.target.value)}
            rows={4}
            className="rounded-md border border-borde-fuerte bg-papel p-2 text-[16px] leading-[22px] text-tinta-fuerte"
          />
        </label>

        {cambiar.error && <p className="text-[14px] text-error">{textoDeError(cambiar.error)}</p>}

        <div className="flex gap-2">
          <Boton type="submit" disabled={cambiar.isPending}>
            {cambiar.isPending ? 'Guardando...' : 'Guardar como version nueva'}
          </Boton>
          <Boton onClick={() => setAbierto(false)}>Cancelar</Boton>
        </div>
      </form>
    </Tarjeta>
  )
}
