/** Ajustes: lo poco que hay que configurar, y por que.
 *
 *  Una sola cosa cambia de verdad lo que se ve: **las cadenas que tienes a
 *  mano**. Con eso puesto, el buscador y el panel dejan de ofrecerte cosas de una
 *  cadena a la que no vas.
 *
 *  La fecha de los datos y el aviso de las cadenas con retraso **no** van aqui:
 *  estan en la cabecera, siempre a la vista. Esconderlos en una pantalla de
 *  ajustes seria justo lo contrario de lo que pide el proyecto.
 */
import { useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { cadenasCerca, guardarPreferencia } from '../api/ajustes'
import { textoDeError } from '../api/cliente'
import { borrarme, salir, yo } from '../api/cesta'
import { useEstado } from '../api/consultas'
import { nombreCadena } from '../api/formato'
import { Boton, CampoTexto, Cargando, Etiqueta, Tarjeta, Vacio } from '../componentes/ui'

export function Ajustes() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const estado = useEstado()
  const [guardado, setGuardado] = useState<string | null>(null)
  // Los dos estados de "darme de baja": si se ha pedido, y lo que se ha escrito. La
  // confirmacion es escribir **tu propio usuario**, no un "si": ver la tarjeta de abajo.
  const [baja, setBaja] = useState(false)
  const [texto, setTexto] = useState('')
  const quien = sesion.data?.usuario?.usuario ?? ''

  const borra = useMutation({
    mutationFn: borrarme,
    // Al darse de baja no queda sesion ni nada que mirar: se tira todo lo que hay en
    // pantalla y la aplicacion vuelve a su estado de "sin entrar" (`yo` contesta null).
    onSuccess: () => cliente.invalidateQueries(),
  })

  const prefs = sesion.data?.preferencias
  const puestas = cadenasCerca(prefs)

  const guarda = useMutation({
    mutationFn: (cadenas: string[]) => guardarPreferencia('cadenas_cerca', cadenas),
    onSuccess: (_r, cadenas) => {
      setGuardado(cadenas.length
        ? `Guardado: ${cadenas.join(', ')}`
        : 'Guardado: ninguna, se miran todas')
      cliente.invalidateQueries({ queryKey: ['yo'] })
    },
  })

  if (sesion.isLoading) return <Cargando que="tus ajustes" />

  if (!sesion.data?.usuario) {
    // **Con la puerta, no solo con el cartel.** Medido en un navegador el 24 de septiembre
    // de 2026: esta pantalla decia «Entra para cambiar tus ajustes» y **no habia ni un
    // enlace ni un boton** -- quien llegara aqui sin sesion (un marcador, un enlace de otro
    // sitio) se quedaba mirando una frase sin salida. La de favoritos ya lo hacia bien
    // (`Favoritos.tsx`): se entra desde la cesta, y se dice.
    return (
      <Vacio titulo="Entra para cambiar tus ajustes">
        <p>
          Los ajustes son de cada uno, así que hacen falta tus listas. Se entra desde{' '}
          <Link to="/cesta" className="underline">la cesta</Link>.
        </p>
      </Vacio>
    )
  }

  const cadenas = estado.data?.cadenas.map((c) => c.cadena) ?? []

  function alterna(cadena: string) {
    const nueva = puestas.includes(cadena)
      ? puestas.filter((c) => c !== cadena)
      : [...puestas, cadena]
    guarda.mutate(nueva)
  }

  return (
    <div className="grid gap-4">
      <header>
        <h1 className="text-xl font-semibold">Ajustes</h1>
        <p className="text-sm text-tinta-suave">
          Has entrado como <strong>{sesion.data.usuario.usuario}</strong>.
          <button
            className="ml-2 inline-flex min-h-[44px] min-w-[44px] items-center justify-center underline"
            onClick={async () => {
              await salir()
              cliente.invalidateQueries()
            }}
          >
            Salir
          </button>
        </p>
      </header>

      <Tarjeta>
        <h2 className="mb-1 text-base font-semibold">Las cadenas que tienes cerca</h2>
        <p className="mb-3 text-sm text-tinta-suave">
          Marca las que te pillan a mano. Con eso puesto, la búsqueda y el panel
          dejan de ofrecerte cosas de una cadena a la que no vas. Sin ninguna
          marcada se miran las cinco, que es lo que hace por defecto.
        </p>
        <div className="flex flex-wrap gap-2">
          {cadenas.map((c) => {
            const dentro = puestas.includes(c)
            return (
              <button
                key={c}
                onClick={() => alterna(c)}
                disabled={guarda.isPending}
                aria-pressed={dentro}
                className={
                  'inline-flex min-h-[44px] items-center rounded-full border px-3 py-1 text-sm ' +
                  (dentro
                    ? 'border-bien bg-bien-suave font-medium'
                    : 'border-borde')
                }
              >
                {nombreCadena(c)}
              </button>
            )
          })}
          {estado.isPending && <span className="text-sm text-tinta-suave">…</span>}
        </div>
        {puestas.length > 0 && (
          <Boton
            variante="sutil"
            className="mt-3"
            disabled={guarda.isPending}
            onClick={() => guarda.mutate([])}
          >
            Quitar todas
          </Boton>
        )}
        {guardado && <p className="mt-2 text-sm"><Etiqueta tono="bien">{guardado}</Etiqueta></p>}
        {guarda.isError && (
          <p className="mt-2 text-sm text-aviso">{textoDeError(guarda.error)}</p>
        )}
      </Tarjeta>

      {/* **Darme de baja.** Quien presta su ordenador para que otros guarden su lista de la
          compra tiene que darles la puerta de salida, y esta es la unica operacion de toda
          la aplicacion que **no se puede deshacer**: por eso no basta con un boton, hay que
          escribir el propio usuario. Un "¿seguro?" se pulsa sin leer -- lo hacia asi la
          interfaz vieja (`app.js:1571-1603`) y la razon sigue siendo la misma. */}
      <Tarjeta titulo="Darme de baja">
        <p className="text-sm text-tinta-suave">
          Se borran <strong>tus listas, tus favoritos y tu cuenta</strong>. Lo que añadiste
          a listas de otras personas se queda ahí, sin tu nombre, para no vaciarles la
          compra. Esto no se puede deshacer.
        </p>
        {!baja && (
          <Boton variante="sutil" className="mt-3" onClick={() => setBaja(true)}>
            Quiero darme de baja
          </Boton>
        )}
        {baja && (
          <div className="mt-3 grid gap-2">
            <CampoTexto
              etiqueta={`Escribe ${quien} para confirmarlo`}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              autoComplete="off"
              autoCapitalize="none"
              spellCheck={false}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Boton
                variante="peligro"
                disabled={texto.trim() !== quien || borra.isPending}
                onClick={() => borra.mutate()}
              >
                {borra.isPending ? 'Dándome de baja…' : 'Darme de baja'}
              </Boton>
              <Boton
                variante="sutil"
                onClick={() => {
                  setBaja(false)
                  setTexto('')
                }}
              >
                No, déjalo
              </Boton>
            </div>
            {borra.isError && (
              <p className="text-sm text-aviso">{textoDeError(borra.error)}</p>
            )}
          </div>
        )}
      </Tarjeta>
    </div>
  )
}
