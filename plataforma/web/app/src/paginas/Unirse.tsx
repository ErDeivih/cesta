/** `/unirme/<codigo>`: la pantalla del enlace que se manda por WhatsApp.
 *
 *  Esta ruta no es una idea del front: es la que devuelve la propia API al crear
 *  una invitacion (`main.py:500`, el campo `ruta`), asi que forma parte del
 *  contrato. La interfaz vieja hacia lo mismo, y en el mismo sitio (`app.js:144`
 *  y `1676-1695`).
 *
 *  El caso que manda es el de quien **no tiene cuenta**: le llega un enlace, lo
 *  abre en el movil y no esta dentro de nada. Por eso lo primero que sale es la
 *  puerta de entrada, la misma que la cesta (`Introducir`, importada y no
 *  copiada), con una frase que diga para que es. Pedirle a alguien que se
 *  registre con un error en la cara no es una forma de pedirle nada.
 *
 *  El codigo **no se guarda en ningun sitio**: vive en la barra de direcciones y
 *  ahi sigue mientras se entra o se crea la cuenta, porque esta pantalla no
 *  navega hasta que la invitacion se aplica. La interfaz vieja lo copiaba a
 *  `localStorage` y limpiaba la URL (`app.js:1678`) porque no tenia rutas de
 *  verdad; aqui guardarlo seria una segunda copia que puede quedar vieja, y un
 *  enlace caducado guardado se aplicaria solo la proxima vez que alguien abra la
 *  aplicacion.
 *
 *  Al aplicarse se va a la cesta **con esa lista abierta**. La lista que se
 *  acaba de aceptar casi nunca es la primera del desplegable (las de casa van
 *  delante, `almacen.py:219`), y aterrizar en otra lista parece que el enlace no
 *  ha hecho nada.
 */
import { useEffect, useRef } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { aceptarInvitacion, yo } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { Aviso, Cargando, Etiqueta, Tarjeta } from '../componentes/ui'
import { Introducir } from './Cesta'

export function Unirse() {
  // `:codigo` siempre viene en esta ruta; el valor por defecto es para que el
  // tipo sea `string` y no `string | undefined` en cada linea de abajo.
  const { codigo = '' } = useParams()
  const cliente = useQueryClient()
  const navega = useNavigate()

  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })

  const acepta = useMutation({
    mutationFn: () => aceptarInvitacion(codigo),
    onSuccess: (hecho) => {
      // La lista nueva no esta en el cache de `listas`: se acaba de entrar en
      // ella. Si no se pide otra vez, la cesta se abriria con las de antes.
      cliente.invalidateQueries({ queryKey: ['listas'] })
      navega('/cesta', {
        // Con `replace`: el boton de atras tiene que volver a donde estabas, no
        // a un enlace de invitacion ya gastado, que al reabrirlo daria un 404.
        replace: true,
        state: {
          listaId: hecho.lista_id,
          aviso: hecho.ya_estabas
            ? `Ya estabas en «${hecho.nombre}».`
            : `Ya estás en «${hecho.nombre}»: quien te la mandó te ha dejado ${
                hecho.papel === 'mira' ? 'mirarla' : 'escribir en ella'
              }.`,
        },
      })
    },
  })

  // Una guarda con `ref` y no con estado: en desarrollo React monta la pantalla
  // dos veces (`StrictMode`, main.tsx:36) y sin ella se mandarian dos peticiones
  // por abrir un enlace. La API es idempotente a proposito -- si ya estabas
  // dentro no gasta un uso (`almacen.py:493`) --, asi que el peor caso de un
  // envio doble es un mensaje repetido; aun asi, pedir dos veces lo mismo por
  // montar una pantalla no es correcto y se corta aqui.
  const lanzada = useRef(false)
  useEffect(() => {
    if (!sesion.data?.usuario || !codigo || lanzada.current) return
    lanzada.current = true
    acepta.mutate()
    // `acepta` no esta en la lista a proposito: la identidad de `mutate` cambia
    // en cada render y meterla aqui dejaria el efecto disparandose sin parar.
  }, [sesion.data?.usuario, codigo])

  if (sesion.isLoading) return <Cargando que="tu sesión" />

  if (!sesion.data?.usuario) {
    return (
      <div className="flex min-h-full flex-col gap-4">
        {/* Una `Tarjeta` de las de siempre: es lo unico que hay por encima de la
            puerta, y sin ella los dos formularios parecen salidos de la nada. */}
        <Tarjeta className="grow">
          <h2 className="text-lg font-semibold">Te han invitado a una lista</h2>
          <p className="mt-1 text-sm text-tinta-suave">
            Entra con tu cuenta —o créala, se tarda un momento— y te meto en la
            lista. El código del enlace no se pierde: sigue en la barra de
            direcciones.
          </p>
          <p className="mt-2 text-sm">
            <Etiqueta tono="info">quien te la manda ya está dentro</Etiqueta>
          </p>
        </Tarjeta>
        <Introducir
          alEntrar={() => {
            // Al entrar, `sesion` cambia y el efecto de arriba aplica el enlace:
            // no hace falta llevar el codigo a ningun sitio, esta en la ruta.
            cliente.invalidateQueries({ queryKey: ['yo'] })
          }}
        />
      </div>
    )
  }

  if (acepta.isError) {
    return (
      <div className="flex min-h-full flex-col gap-4">
        {/* **El titulo de la pagina.** `Aviso` pinta su titulo como un parrafo (es un aviso, no
            un titular), asi que esta pantalla se quedaba sin `h1`: quien llega desde un enlace
            caducado abria una pagina que no decia como se llama. Medido con
            `data/debug/accesibilidad.py` el 27 de septiembre de 2026. Oculta porque el aviso ya
            lo dice en voz alta, y repetirlo encima seria ruido. */}
        <h2 className="sr-only">Invitación a una lista</h2>
        <Aviso tono="mal" titulo="No he podido meterte en la lista">
          {/* El 404 de la API ya trae su frase entera ("caduca a los siete dias, y
              puede que ya lo hayan usado. Pidele otro a quien te lo mando"), y el
              401 suya. Aqui no se reescriben: se enseñan. */}
          <Etiqueta tono="mal">{textoDeError(acepta.error)}</Etiqueta>
          <p className="mt-1">
            Tus listas de siempre siguen donde estaban:{' '}
            <Link to="/cesta" className="underline">la cesta</Link>.
          </p>
        </Aviso>
      </div>
    )
  }

  return <Cargando que="la invitación" />
}
