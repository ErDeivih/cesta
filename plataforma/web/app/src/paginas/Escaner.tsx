/** El escaner: lo que tienes en la mano, por su codigo de barras.
 *
 *  Es la pantalla que mas se usa de pie en el pasillo, asi que:
 *   - El campo se enfoca solo y acepta el codigo como lo lea el lector: con
 *     espacios, con guiones y con ceros de mas. Normaliza el servidor
 *     (`catalogo.normaliza_ean`); aqui no se reimplementa esa regla, porque dos
 *     normalizadores acaban discrepando.
 *   - Un 400 ("eso no es un codigo") se enseña como respuesta, no como fallo de
 *     red: el servidor manda una frase escrita para leerla una persona.
 *   - `comparacion: null` se dice **"no puedo comparar"**, que no es lo mismo
 *     que "he mirado y no hay nada más barato". Ese es el error que evita que
 *     `comparacion` sea una lista vacía.
 */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { useEan } from '../api/consultas'
import { esErrorApi, textoDeError } from '../api/cliente'
import { euros, eurosUnidad, fecha, nombreCadena, porcentajeConSigno } from '../api/formato'
import { SelloNutriscore } from '../componentes/Etiquetas'
import { IconoCamara } from '../componentes/iconos'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Resumen, TablaScroll, Tarjeta, Td, Th, Vacio } from '../componentes/ui'

/** `BarcodeDetector` no esta en los tipos del DOM: es una API de navegador que
 *  solo tienen algunos (Chrome y derivados; Firefox y Safari no). Se declara lo
 *  minimo que se usa, en vez de instalar tipos de toda la plataforma. */
interface Deteccion {
  rawValue: string
}
interface Detector {
  detect(fuente: HTMLVideoElement): Promise<Deteccion[]>
}
interface ConstructorDetector {
  new (opciones?: { formats?: string[] }): Detector
}

declare global {
  interface Window {
    BarcodeDetector?: ConstructorDetector
  }
}

/** Los formatos que puede leer un codigo de supermercado. */
const FORMATOS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128']

export function Escaner() {
  const [codigo, setCodigo] = useState('')
  const [buscado, setBuscado] = useState<string | null>(null)
  const [camara, setCamara] = useState(false)
  const [avisoCamara, setAvisoCamara] = useState<string | null>(null)

  const video = useRef<HTMLVideoElement>(null)
  const flujo = useRef<MediaStream | null>(null)

  const consulta = useEan(buscado)

  // El boton de la camara solo existe si el navegador sabe leer codigos de
  // barras. Un boton que abre una camara que no detecta nada es peor que no
  // tener boton: hace perder el tiempo en el pasillo.
  const hayDetector = typeof window !== 'undefined' && typeof window.BarcodeDetector === 'function'

  const cierraCamara = () => {
    flujo.current?.getTracks().forEach((t) => t.stop())
    flujo.current = null
    setCamara(false)
  }

  // Al salir de la pantalla se suelta la camara. Si no, el piloto se queda
  // encendido y la camara ocupada hasta recargar.
  useEffect(() => cierraCamara, [])

  useEffect(() => {
    if (!camara) return
    const el = video.current
    const stream = flujo.current
    const Detector = window.BarcodeDetector
    if (!el || !stream || !Detector) return

    el.srcObject = stream
    void el.play().catch(() => setAvisoCamara('La cámara no ha arrancado.'))

    let vivo = true
    let temporizador = 0
    const detector = new Detector({ formats: FORMATOS })

    const mira = async () => {
      if (!vivo) return
      try {
        const encontrados = await detector.detect(el)
        const primero = encontrados[0]
        if (primero?.rawValue) {
          setCodigo(primero.rawValue)
          setBuscado(primero.rawValue.trim())
          cierraCamara()
          return
        }
      } catch {
        // Un fotograma que aun no esta listo lanza. No es un fallo: se vuelve a
        // mirar. Tres veces por segundo es suficiente para un pulso humano.
      }
      if (vivo) temporizador = window.setTimeout(() => void mira(), 350)
    }
    temporizador = window.setTimeout(() => void mira(), 500)

    return () => {
      vivo = false
      window.clearTimeout(temporizador)
    }
  }, [camara])

  const abreCamara = async () => {
    setAvisoCamara(null)
    try {
      flujo.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      })
      setCamara(true)
    } catch {
      setAvisoCamara(
        'No he podido abrir la cámara. Puede que el navegador no dé permiso, o que la página no vaya por HTTPS: sin HTTPS no hay cámara.',
      )
    }
  }

  const error = consulta.error
  const es400 = esErrorApi(error) && error.estado === 400

  // Los dos casos se sacan a constantes: dentro de un `map` TypeScript ya no
  // sabe que `consulta.data.encontrado` es true, y con estas dos variables si.
  const hallado = consulta.data?.encontrado ? consulta.data : null
  const perdido = consulta.data && !consulta.data.encontrado ? consulta.data : null

  // La comparación marca como "el más barato" SOLO al de la diferencia mínima.
  // Con `<= 0` a secas, un empate o un negativo del servidor pintarían dos
  // cadenas como la más barata a la vez.
  const masBarato = hallado?.comparacion
    ? Math.min(...hallado.comparacion.map((c) => c.precio_unidad_cent ?? Infinity))
    : null

  return (
    <div className="grid grid-cols-1 gap-4">
      <h1 className="text-xl font-bold">Escáner</h1>

      <form
        className="grid grid-cols-1 gap-2 sm:flex sm:flex-wrap sm:items-end"
        onSubmit={(e) => {
          e.preventDefault()
          setBuscado(codigo.trim() || null)
        }}
      >
        {/* `min-w-0` en la columna y `w-full` en el campo: un `<input>` tiene un
            ancho intrínseco (el `size` por defecto, 20 caracteres) y, sin esto,
            en un móvil estira el formulario 200 px más allá de la pantalla y
            aparece scroll horizontal en toda la página. */}
        <div className="flex min-w-0 flex-col gap-1 sm:flex-1">
          <label htmlFor="ean" className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
            Código de barras
          </label>
          <input
            id="ean"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            // `numeric` saca el teclado de numeros en el movil. El servidor
            // acepta guiones y espacios, pero casi nadie los teclea.
            inputMode="numeric"
            autoComplete="off"
            autoFocus
            enterKeyHint="search"
            placeholder="8410655002410"
            className="w-full min-h-[48px] rounded-xl border border-neutral-300 bg-white px-4 py-2 font-mono text-lg tracking-wider dark:border-neutral-600 dark:bg-neutral-800"
          />
        </div>
        <Boton type="submit" variante="principal" disabled={!codigo.trim()}>
          Buscar
        </Boton>
        {hayDetector && !camara && (
          <Boton variante="normal" onClick={() => void abreCamara()}>
            <IconoCamara width={18} height={18} />
            Usar la cámara
          </Boton>
        )}
        {camara && (
          <Boton variante="peligro" onClick={cierraCamara}>
            Parar la cámara
          </Boton>
        )}
      </form>

      <p className="text-xs text-tinta-suave">
        Se acepta el código como lo lea el lector: con espacios, con guiones y con ceros de más
        (EAN-13 y UPC-12 son el mismo número escrito distinto).
        {!hayDetector && (
          <>
            {' '}
            Este navegador no tiene <code>BarcodeDetector</code>, así que no hay botón de cámara:
            teclea o pega el número.
          </>
        )}
      </p>

      {avisoCamara && <Aviso tono="aviso">{avisoCamara}</Aviso>}

      {camara && (
        <div className="overflow-hidden rounded-xl border border-neutral-300 dark:border-neutral-600">
          {/* El vídeo no lleva `autoPlay` en el JSX: se arranca a mano al
              conectar el flujo, que es cuando el elemento ya existe. */}
          <video ref={video} playsInline muted className="max-h-[60vh] w-full bg-black object-cover" />
          <p className="bg-white px-3 py-2 text-sm dark:bg-neutral-800">
            Apunta al código de barras. Cuando lo lea, se busca solo.
          </p>
        </div>
      )}

      {consulta.isFetching && <Cargando que="el código" />}

      {error !== null && es400 && (
        <Aviso tono="mal" titulo="Eso no es un código de barras">
          <p>{textoDeError(error)}</p>
          <p className="mt-1">
            Un código bueno que no conozcamos contesta otra cosa: «no lo tengo». Aquí el servidor
            dice que lo que ha llegado no es un código.
          </p>
        </Aviso>
      )}

      {error !== null && !es400 && (
        <Fallo error={error} reintentar={() => void consulta.refetch()} />
      )}

      {perdido && (
        <Vacio titulo="No tengo ese código">
          <p>
            <strong>Motivo:</strong> {perdido.motivo}
          </p>
          {perdido.sugerencia && <p className="mt-1">{perdido.sugerencia}</p>}
          <p className="mt-2 text-xs">
            Datos del {fecha(perdido.fecha_datos)}.{' '}
            {perdido.motivo === 'desconocido' &&
              'El motivo «sin_ean_en_esa_cadena» todavía no se da nunca: necesitaría un parámetro `cadena` que no está implementado.'}
          </p>
        </Vacio>
      )}

      {hallado && (
        <Tarjeta
          titulo="Esto es lo que tienes en la mano"
          sub={`Datos del ${fecha(hallado.fecha_datos)}`}
        >
          <div className="flex flex-wrap items-start gap-4">
            <div className="min-w-[16rem] flex-1">
              <p className="font-medium">{hallado.producto.nombre}</p>
              <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                <Etiqueta tono="info">{nombreCadena(hallado.producto.fuente)}</Etiqueta>
                {hallado.producto.marca && <span>{hallado.producto.marca}</span>}
                <span>
                  {hallado.producto.cantidad ?? '—'} {hallado.producto.unidad ?? ''}
                </span>
                <SelloNutriscore valor={hallado.producto.nutriscore} />
              </p>
              <p className="mt-2 flex flex-wrap items-baseline gap-3">
                <span className="cifra text-2xl font-bold">
                  {euros(hallado.producto.precio_cent)}
                </span>
                <span className="cifra text-sm text-neutral-700 dark:text-neutral-300">
                  {eurosUnidad(hallado.producto.precio_unidad_cent, hallado.producto.unidad)}
                </span>
              </p>
            </div>
            {hallado.grupo_id !== null ? (
              <Link
                to={`/grupo/${hallado.grupo_id}`}
                className="inline-flex min-h-[44px] items-center rounded-lg bg-sky-700 px-4 font-medium text-white hover:bg-sky-800 dark:bg-sky-700"
              >
                Ver el grupo y las otras cadenas
              </Link>
            ) : (
              <Aviso tono="aviso">
                Este producto no tiene grupo: no hay con qué compararlo.
              </Aviso>
            )}
          </div>

          <div className="mt-4">
            {hallado.comparacion === null ? (
              <Aviso tono="info" titulo="No puedo comparar">
                <p>
                  Solo tenemos este producto en una cadena, así que no hay con qué compararlo. No es
                  lo mismo que «he mirado y no hay nada más barato»: es que no hay comparación
                  posible.
                </p>
              </Aviso>
            ) : (
              <TablaScroll etiqueta="Comparación entre cadenas" minAncho="34rem">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      <Th>Cadena</Th>
                      <Th>Precio</Th>
                      <Th>Por unidad</Th>
                      <Th>Diferencia</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {hallado.comparacion.map((c) => (
                      <tr key={c.fuente}>
                        <Td>{nombreCadena(c.fuente)}</Td>
                        <Td className="cifra" etiqueta="precio">{euros(c.precio_cent)}</Td>
                        <Td className="cifra" etiqueta="por unidad">
                          {eurosUnidad(c.precio_unidad_cent, hallado.producto.unidad)}
                        </Td>
                        <Td className="cifra" etiqueta="diferencia">
                          {c.diferencia_pct === null
                            ? 'no lo sé'
                            : c.precio_unidad_cent !== null && c.precio_unidad_cent === masBarato
                              ? 'aquí es donde más barato está'
                              : porcentajeConSigno(c.diferencia_pct)}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TablaScroll>
            )}
            <p className="mt-1 text-xs text-tinta-suave">
              La diferencia se mide contra el precio por unidad más bajo de la comparación, no
              contra el precio del envase.
            </p>
          </div>

          {hallado.nota != null && (
            <details className="mt-3">
              <Resumen className="text-xs text-sky-800 dark:text-sky-400">
                La nota del producto (dato en crudo)
              </Resumen>
              <pre className="mt-1 overflow-x-auto rounded-lg bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
                {JSON.stringify(hallado.nota, null, 2)}
              </pre>
            </details>
          )}
        </Tarjeta>
      )}

      {!consulta.data && !consulta.isFetching && error === null && (
        <Vacio titulo="Escribe o pega un código">
          <p>
            Con el código de barras se contesta la pregunta del pasillo: <em>esto que tengo en la
            mano, ¿está más barato en otro sitio?</em>
          </p>
        </Vacio>
      )}
    </div>
  )
}
