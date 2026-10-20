/** El detalle de una receta: la receta de esa direccion, con sus versiones.

 *  **Lee la receta persistida de la ruta**, no un estado de la pantalla anterior: se puede abrir el enlace
 *  en otra pestana o recargar, y sigue enseñando lo mismo. Eso es lo que lo hace una pantalla y no un
 *  paso intermedio.
 *
 *  **Y tiene 404 de verdad.** Si la receta no existe -- o es de otra persona, que la API contesta igual para
 *  no decir cual existe -- se dice con esas palabras. Un 404 aqui no es un fallo: es una respuesta.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { textoDeError, esErrorApi } from '../api/cliente'
import { Fallo, Etiqueta } from '../componentes/ui'
import { usePasarALista, usePreviaDeCompra, useReceta } from '../api/recetas'
import { misListas } from '../api/cesta'
import { costeDeReceta, type IngredienteConPrecio } from '../logica/costeReceta'
import { FormularioReceta } from '../componentes/FormularioReceta'
import { Boton, Tarjeta, Vacio } from '../componentes/ui'

/**
 * **G12, punto 221: pasar la receta a la lista, enseñando antes lo que se va a comprar.**
 *
 * *Dos pasos a proposito*: se pide la previa -- que **no escribe nada** -- y solo despues se confirma.
 * **Y la previa enseña lo que NO se puede comprar**, que es la mitad de su valor: *saber que la sal no
 * entra porque no se sabe cuanto es mejor que ver una lista sin sal y no entender por que.*
 */
function PasarALista({ recetaId }: { recetaId: number }) {
  const [abierta, setAbierta] = useState(false)
  const [listaId, setListaId] = useState('')
  const [hecho, setHecho] = useState<string | null>(null)
  const previa = usePreviaDeCompra(abierta ? recetaId : null)
  const listas = useQuery({ queryKey: ['listas'], queryFn: misListas, enabled: abierta })
  const pasar = usePasarALista(recetaId)

  if (!abierta) {
    return (
      <Boton onClick={() => setAbierta(true)}>Pasar a la lista de la compra</Boton>
    )
  }

  // **`misListas` devuelve `Lista[]` directo**, no envuelto -- y suponer lo contrario fue el
  // error de tipo que `tsc` cazo, en la misma forma que en la ronda 230.
  const suyas = listas.data ?? []
  return (
    <Tarjeta titulo="Lo que habria que comprar">
      {previa.isPending && <p className="text-[16px] text-secundaria">Calculando...</p>}
      {previa.error && <Etiqueta tono="mal">{textoDeError(previa.error)}</Etiqueta>}
      {previa.data && (
        <div className="flex min-h-full flex-col gap-3">
          {previa.data.lineas.length === 0 && (
            <p className="text-[16px] text-secundaria">
              Nada que comprar: ningun ingrediente tiene cantidad.
            </p>
          )}
          <ul className="flex flex-col gap-1">
            {previa.data.lineas.map((ln) => (
              <li key={ln.clave} className="flex flex-wrap justify-between gap-2 text-[16px]">
                <span className="text-tinta-fuerte">{ln.texto}</span>
                <span className="tabular-nums text-secundaria">
                  {ln.cantidad} {ln.unidad}
                  {ln.envases !== null && ` · ${ln.envases} envase${ln.envases === 1 ? '' : 's'}`}
                  {ln.sobrante ? ` · sobran ${ln.sobrante}${ln.unidad}` : ''}
                </span>
              </li>
            ))}
          </ul>

          {/* **Y lo que no se puede comprar, con su motivo.** *Sin esto, una lista con menos lineas
              de las esperadas parece un fallo.* */}
          {previa.data.sin_cantidad.length > 0 && (
            <p className="text-[14px] text-secundaria">
              Sin cantidad, no se compra: {previa.data.sin_cantidad.join(', ')}.
            </p>
          )}
          {previa.data.sin_consolidar.length > 0 && (
            <p className="text-[14px] text-secundaria">
              No se pudieron juntar: {previa.data.sin_consolidar.join('; ')}.
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={listaId}
              onChange={(e) => setListaId(e.target.value)}
              aria-label="Lista de destino"
              className="min-h-[44px] rounded border border-borde bg-papel px-2 text-[16px]"
            >
              <option value="">Elige una lista...</option>
              {suyas.map((l: { id: string; nombre: string }) => (
                <option key={l.id} value={l.id}>{l.nombre}</option>
              ))}
            </select>
            <Boton
              onClick={() => pasar.mutate(listaId, {
                onSuccess: (r) => setHecho(
                  r && (r as { ya_estaba?: boolean }).ya_estaba
                    ? 'Ya estaba en la lista: no se ha duplicado.'
                    : 'Anadido a la lista.'),
              })}
              disabled={!listaId || pasar.isPending}
            >
              {pasar.isPending ? 'Pasando...' : 'Pasar a la lista'}
            </Boton>
            <Boton onClick={() => { setAbierta(false); setHecho(null) }}>Cerrar</Boton>
          </div>
          {hecho && <p className="text-[15px] text-tinta-fuerte">{hecho}</p>}
          {pasar.error && <Etiqueta tono="mal">{textoDeError(pasar.error)}</Etiqueta>}
        </div>
      )}
    </Tarjeta>
  )
}

export function RecetaDetalle() {
  const { recetaId } = useParams()
  const id = recetaId ? Number(recetaId) : null
  const [version, setVersion] = useState<number | null>(null)
  /** Para cuantas raciones se quieren los ingredientes. Vacio = las de la receta. */
  const [raciones, setRaciones] = useState<number | null>(null)
  const { data, isPending, error } = useReceta(id, version, raciones)

  if (isPending) {
    return <p className="text-[15px] text-secundaria">Leyendo la receta...</p>
  }

  if (error) {
    // **404 no es un fallo.** Se distingue del resto para no pintar en rojo algo que es una respuesta.
    if (esErrorApi(error) && error.estado === 404) {
      return (
        <Vacio titulo="Esa receta no existe" className="grow">
          <p>
            Puede que se haya archivado o que el enlace este mal. <Link to="/recetas" className="underline">
              Vuelve al recetario
            </Link>.
          </p>
        </Vacio>
      )
    }
    return <Fallo error={error} />
  }
  if (!data) return null

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-[24px] leading-8 font-semibold text-tinta-fuerte">
          {data.nombre}
        </h2>
        <Link to="/recetas/plan" className="min-h-[44px] min-w-[44px] text-[14px] text-secundaria underline">
          Planificar
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* **Para cuantas raciones.** El servidor ya escalaba; sin este campo, el trabajo estaba hecho y
            no se veia. A 16 px por el contrato de movil: por debajo, el navegador hace zoom al enfocar. */}
        <label className="flex items-center gap-2 text-[13px] text-secundaria" htmlFor="raciones">
          Para
          <input
            id="raciones"
            type="number"
            min={1}
            value={raciones ?? data.raciones_receta ?? data.raciones}
            onChange={(e) => {
              const cuantas = Number(e.target.value)
              // Vacio o cero es "las de la receta": no se manda una escala que no se ha pedido.
              setRaciones(cuantas >= 1 ? cuantas : null)
            }}
            className="min-h-[44px] w-20 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
          />
          raciones
        </label>
        {/* **Las dos cifras.** Sin esto, quien mira una receta escalada creeria que es de seis. */}
        {data.escalada && (
          <span className="text-[13px] text-aviso tabular-nums">
            Calculado para {data.raciones}; la receta es de {data.raciones_receta}.
          </span>
        )}
        <label className="text-[13px] text-secundaria" htmlFor="version">
          Version
        </label>
        <select
          id="version"
          value={version ?? data.version}
          onChange={(e) => setVersion(Number(e.target.value))}
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
        >
          {/* De la 1 a la ultima: la lista sale de la propia receta, sin inventar numeros. */}
          {Array.from({ length: data.version }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}
              {n === data.version ? ' (ultima)' : ''}
            </option>
          ))}
        </select>
        <span className="text-[13px] text-secundaria tabular-nums">
          {data.raciones} raciones{data.minutos ? ` · ${data.minutos} min` : ''}
        </span>
        {version !== null && version !== data.version && (
          <span className="text-[13px] text-aviso">
            Estas viendo una version anterior. La ultima es la {data.version}.
          </span>
        )}
      </div>

      <Tarjeta>
        {data.ingredientes.length === 0 ? (
          <p className="text-[13px] text-secundaria">Sin ingredientes apuntados.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {data.ingredientes.map((i, posicion) => (
              <li key={`${i.texto}-${posicion}`} className="text-[14px] leading-[22px] text-tinta-fuerte">
                {i.cantidad ? <span className="tabular-nums">{i.cantidad} </span> : null}
                {i.unidad ? <span>{i.unidad} </span> : null}
                {i.texto}
              </li>
            ))}
          </ul>
        )}
      </Tarjeta>

      {/* **Lo que cuesta, con sus dos numeros -- o dicho claro que no se puede.** G05: *«coste
          estimado, **distinguiendo cantidad usada de coste de comprar envases**; **indicar
          ingredientes sin datos**»*.
          **Hoy no hay ningun ingrediente enlazado con un producto**: el ingrediente de una receta
          tiene nombre, cantidad y nutrientes, y ningun `producto_id`. *Enlazarlo es el problema de
          identidad de G10*, y `cocina.ts:36` prohibe la salida facil -- «no fusionar por parecido de
          nombre: no demuestra que sean el mismo ingrediente». Asi que el coste **no se inventa**: se
          declara.
          Y no se pinta un «0,00 EUR»: **un cero se leeria como «esta receta es gratis»**, y lo que
          pasa es que no se sabe. Cuando G10 traiga el enlace, esta tarjeta ya calcula los dos numeros
          sin tocar el modulo. */}
      <Tarjeta titulo="Lo que cuesta">
        {(() => {
          // **El precio lo manda el servidor** cuando el ingrediente tiene producto elegido:
          // `core/recetas.py` guarda su `producto_id` y `api/recetas.py` lo enriquece con el precio
          // del catalogo. *Lo que falta no era el dato: era el cable.*
          const conPrecio: IngredienteConPrecio[] = data.ingredientes.map((i) => {
            const p = i as unknown as {
              precio_cent?: number | null; precio_unidad_cent?: number | null
            }
            const tiene = typeof p.precio_cent === 'number' || typeof p.precio_unidad_cent === 'number'
            return {
              nombre: i.texto,
              cantidad: i.cantidad ?? 0,
              unidad: i.unidad ?? '',
              // **Y sin producto elegido sigue sin precio.** No se busca por nombre: un nombre
              // parecido no demuestra que sea el mismo producto, y `cocina.ts` lo prohibe.
              precio: tiene
                ? { precioEnvaseCent: p.precio_cent ?? null,
                    precioUnidadCent: p.precio_unidad_cent ?? null }
                : null,
            }
          })
          const c = costeDeReceta(conPrecio)
          return (
            <>
              <ul className="flex flex-col gap-1 text-[13px] text-secundaria">
                <li>
                  Usando lo que dice la receta:{' '}
                  <strong className="text-tinta-fuerte">
                    {c.usadoCent === null ? 'no se puede calcular todavía' : `${c.usadoCent / 100} EUR`}
                  </strong>
                </li>
                <li>
                  Comprando los envases enteros:{' '}
                  <strong className="text-tinta-fuerte">
                    {c.envasesCent === null ? 'no se puede calcular todavía' : `${c.envasesCent / 100} EUR`}
                  </strong>
                </li>
              </ul>
              {!c.completo && (
                <p className="mt-2 text-[13px] text-aviso">
                  {c.sinDatos.length === 1
                    ? 'Un ingrediente no tiene precio: '
                    : `${c.sinDatos.length} ingredientes no tienen precio: `}
                  <strong className="font-medium">{c.sinDatos.join(', ')}</strong>. Los precios salen
                  del catálogo, y para eso cada ingrediente tiene que estar enlazado con su producto;
                  emparejarlos por el nombre no vale, porque un nombre parecido no demuestra que sea el
                  mismo producto.
                </p>
              )}
            </>
          )
        })()}
      </Tarjeta>

      {id !== null && <PasarALista recetaId={id} />}

      {data.preparacion && (
        <Tarjeta>
          <p className="whitespace-pre-line text-[14px] leading-[22px] text-tinta-fuerte">
            {data.preparacion}
          </p>
        </Tarjeta>
      )}
      <FormularioReceta receta={data} />
    </div>
  )
}
