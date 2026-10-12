/** El modo cocina: por donde ibas, y el tiempo.
 *
 *  **Lo que esta pantalla tiene que decir bien, y es lo unico que importa aqui**: *el tiempo **se calcula**, no se
 *  cuenta.* *Un temporizador **que ya paso** se enseña diciendo **cuanto hace que paso** -- *«se paso hace 2
 *  minutos»* --, **y no desaparece**: *un temporizador que se paso **no es un temporizador que no existe**.*
 *
 *  **Y por eso esto sobrevive a la pantalla**: *si se recarga, o se apaga el movil, o se va la conexion, **al
 *  volver el numero es el correcto** -- *porque **no se estaba contando**, se estaba guardando cuando empezo.*
 */
import { useEffect, useState } from 'react'

import { useParams } from 'react-router-dom'

import { apuntaUsado, irAlPaso, ponTemporizador, useCocina, useEmpieza } from '../api/cocina'
import { textoDeError, useSeAtasca } from '../api/cliente'
import { Boton, Tarjeta } from '../componentes/ui'

/** **Segundos, en palabras.** *Y **negativo es «hace»**, que es informacion y no un error.* */
function cuantoTiempo(s: number): string {
  const abs = Math.abs(s)
  const m = Math.floor(abs / 60)
  const seg = abs % 60
  const dicho = m > 0 ? `${m} min ${seg} s` : `${seg} s`
  return s < 0 ? `se paso hace ${dicho}` : `quedan ${dicho}`
}

/** **Los segundos que quedan, calculados AQUI.** *Y esto es lo que hace que funcione sin conexion.*
 *
 *  *Antes se pintaba `queda_segundos`, que es el numero **ya calculado por el servidor** -- *y al cortar la red
 *  **no habia nada que recalcular: el numero se quedaba congelado** (medido el 12 de octubre de 2026: dos
 *  lecturas separadas veinte segundos dieron **`1799` y `1799`**).*
 *
 *  **Ahora se resta del instante que mando el servidor**, y **el reloj lo lleva el aparato** -- *que es lo que la
 *  decision de `core/cocina.py` decia desde el principio, y lo que **la costura no cumplia**.*
 */
function segundosQueQuedan(acabaEn: string): number {
  return Math.round((new Date(acabaEn).getTime() - Date.now()) / 1000)
}

export function CocinaModo() {
  const { recetaId, version } = useParams()
  const id = Number(recetaId)
  const v = Number(version)
  const { data, isLoading, error } = useCocina(id, v)
  // **Y si la consulta se atasca, se dice** -- *ver `useSeAtasca`.*
  const atascada = useSeAtasca(isLoading)
  // **Y EL TIC, que es lo que hace que el numero BAJE.** *El calculo ya estaba en el sitio bueno -- `acaba_en -
  // Date.now()` --, **y el numero es correcto cuando se pinta**.* **Lo que faltaba es que se volviera a pintar**:
  // *React solo re-ejecuta el componente **cuando cambia algo de su estado**, y **sin conexion no llega ninguna
  // respuesta que cambie nada** -- asi que **el `Date.now()` no se volvia a evaluar*** (medido el 12 de octubre de
  // 2026: once segundos sin red y el numero seguia en `1799`).
  //
  // **Y este tic funciona SIN CONEXION por la misma razon que todo lo demas**: *`setInterval` **no pide nada a
  // nadie** -- *es el reloj del aparato, **igual que `Date.now()`**.* **Es la pieza que faltaba para que la
  // promesa del §2 se cumpla entera: el instante viaja desde el servidor, el tiempo lo calcula el aparato, y
  // ahora tambien lo repinta el aparato.**
  const [, setTic] = useState(0)
  useEffect(() => {
    const latido = setInterval(() => setTic((n) => n + 1), 1000)
    return () => clearInterval(latido)
  }, [])
  const empieza = useEmpieza(id, v)

  // **`isLoading` NO BASTA, y esta medido.** *React Query da `isLoading` mientras la consulta **no haya tenido
  // nunca `data`** y **siga intentando** -- *y con `refetchInterval: 15000`, **una consulta que falla se queda en
  // `isLoading` para siempre**.* **Y `if (isLoading)` va ANTES de mirar el error**, asi que **el error existe y
  // nadie lo lee**: *la pantalla dice «Cargando» donde deberia decir **que no se pudo preguntar**.*
  //
  // *Medido el 12 de octubre de 2026, con la API contestando `200`: la pantalla seguia en «Cargando la cocina...»
  // y el temporizador no aparecia.* **Y sin conexion tampoco, veinte segundos despues.**
  //
  // **La regla, entonces: `isLoading` solo mientras NO haya error.** *En cuanto hay error y no hay datos, **manda
  // el error** -- *que es lo unico que la persona necesita saber.*
  if (isLoading && !error && !atascada) return <p className="text-tinta-suave">Cargando la cocina...</p>
  // **Y el error NO se lleva la pantalla por delante cuando ya hay datos.** *Sin conexion, el refresco de cada 15
  // segundos falla -- y **`if (error)` a secas borraba la cocina entera y el temporizador con ella*** (medido el
  // 12 de octubre de 2026: sin red la pantalla no decia «quedan», decia el error). **Con datos en la mano, el
  // fallo del refresco se dice y se sigue** -- *que es lo que hace que el reloj del aparato pueda seguir.*
  // **«No pude preguntar» NO ES «no hay nada».** *Antes esta rama era `if (!data || data.paso === null)`, y
  // metia en el mismo saco dos cosas opuestas: con la red cortada, **la pantalla afirmaba «Esta receta no esta
  // empezada»** -- *cuando la receta **si** estaba empezada y lo que pasaba es que **no se habia podido
  // preguntar*** (medido el 12 de octubre de 2026).*
  //
  // *Es el pecado que esta fase lleva cazando desde `sin_precio`: **convertir «no se sabe» en una afirmacion**.*
  // **Y aqui la afirmacion desanima**: quien cocina sin cobertura lee que no ha empezado.
  if (!data) {
    // *Y aqui entra tambien **la consulta atascada**: `atascada` no se usa para decidir, sino para
    // **dejar de decir «Cargando»** -- que es lo unico que se puede hacer sin inventar datos.*
    return (
      <div className="space-y-3">
        <h1 className="text-xl font-semibold">Cocina</h1>
        <p className="text-amber-700">
          No se ha podido preguntar al servidor. Esto <strong>no</strong> quiere decir que la receta no este
          empezada.
        </p>
        {error ? <p className="text-sm text-tinta-suave">{textoDeError(error)}</p> : null}
      </div>
    )
  }

  // **Y si no hay cocina empezada, se dice** -- *no se inventa un paso.*
  // **Y esto si es «no hay nada».**, porque el servidor lo ha dicho.
  if (data.paso === null) {
    return (
      <div className="space-y-3">
        <h1 className="text-xl font-semibold">Cocina</h1>
        <p className="text-sm text-tinta-suave">Esta receta no esta empezada.</p>
        <Boton onClick={() => empieza.mutate()} disabled={empieza.isPending}>Empezar a cocinar</Boton>
        {empieza.error ? <p className="text-sm text-red-700">{textoDeError(empieza.error)}</p> : null}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Cocina</h1>
      <p className="text-sm text-tinta-suave">
        Vas por el paso <strong>{(data.paso ?? 0) + 1}</strong>. {data.hechos} ingredientes usados.
      </p>

      {data.paso_actual && (
        <Tarjeta>
          <p className="text-base">{data.paso_actual}</p>
        </Tarjeta>
      )}

      {data.temporizadores.length > 0 && (
        <Tarjeta>
          <ul className="divide-y divide-borde">
            {data.temporizadores.map((t, i) => (
              // **Un temporizador que ya paso se pinta distinto, y sigue estando.**
              <li key={i} className={`py-2 ${t.terminado ? 'text-amber-700' : ''}`}>
                {t.minutos} min — {cuantoTiempo(segundosQueQuedan(t.acaba_en))}
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      <div className="flex flex-wrap gap-2">
        <Boton onClick={() => irAlPaso(id, v, (data.paso ?? 0) + 1)}>Paso siguiente</Boton>
        <Boton onClick={() => ponTemporizador(id, v, 10)}>Temporizador de 10 min</Boton>
      </div>
    </div>
  )
}
