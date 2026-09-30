/** El microfono del buscador: lo que dices se escribe en el campo. **No es un asistente.**
 *
 *  La tarea 3 del encargo, y la regla que la define esta en `docs/PANTALLAS.md` §2:
 *
 *  > `SpeechRecognition` del navegador. Rellena el campo de busqueda y ya. **No es un
 *  > asistente.** Si el navegador no lo soporta, **el boton no se dibuja**. No se dibuja y
 *  > falla al pulsarlo: no se dibuja.
 *
 *  Eso ultimo es una regla del proyecto, no un detalle: un boton que al pulsarlo pide algo que
 *  el navegador no tiene es una promesa que no se puede cumplir **de pie y con una mano**. Es
 *  la misma decision que la del escaner sin camara y la del corazon sin sesion.
 *
 *  Y de donde viene el texto: del **reconocedor del navegador**, que en Chrome y Safari se
 *  llama distinto (`SpeechRecognition` y `webkitSpeechRecognition`) y en Firefox no existe.
 *  Aqui no hay ninguna llamada a un servicio: no sale audio de este ordenador.
 */
import { useEffect, useRef, useState } from 'react'

import { Boton, cx } from './ui'

/** Lo minimo que se usa del reconocedor del navegador.
 *
 *  Se declara a mano porque `SpeechRecognition` no esta en los tipos del DOM de TypeScript
 *  (es un borrador): pedir `@types/dom-speech-recognition` por un boton es una dependencia
 *  mas, y lo que se usa son cinco cosas. */
type ReconocedorDeVoz = {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  start: () => void
  stop: () => void
  abort: () => void
  onresult: ((evento: EventoDeVoz) => void) | null
  onerror: ((evento: { error?: string }) => void) | null
  onend: (() => void) | null
}

type EventoDeVoz = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>
}

function constructorDeVoz(): (new () => ReconocedorDeVoz) | undefined {
  const w = window as unknown as {
    SpeechRecognition?: new () => ReconocedorDeVoz
    webkitSpeechRecognition?: new () => ReconocedorDeVoz
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition
}

/** **Sin soporte no se dibuja**: por eso se mira el constructor antes de pintar nada. */
export function hayMicrofono(): boolean {
  return typeof window !== 'undefined' && constructorDeVoz() !== undefined
}

export function Microfono({ alDictar, className }: {
  /** Lo que se ha entendido. Se llama con el texto **tal cual**, sin corregirlo: de
   *  corregir se encarga el buscador, que ya sabe arreglar faltas de ortografia. */
  alDictar: (texto: string) => void
  className?: string
}) {
  const [escuchando, setEscuchando] = useState(false)
  const [fallo, setFallo] = useState<string | null>(null)
  const reconocedor = useRef<ReconocedorDeVoz | null>(null)

  // Al desmontarse (cambiar de pantalla) se para: un microfono abierto detras de otra
  // pantalla es lo ultimo que espera nadie.
  useEffect(() => () => reconocedor.current?.abort(), [])

  if (!hayMicrofono()) return null

  const para = () => {
    reconocedor.current?.stop()
    setEscuchando(false)
  }

  const empieza = () => {
    const Constructor = constructorDeVoz()
    if (!Constructor) return
    const voz = new Constructor()
    voz.lang = 'es-ES'
    // Una sola frase por pulsacion: esto rellena un campo de busqueda, no transcribe una
    // conversacion. Con `continuous` el microfono se queda abierto y hay que acordarse de
    // cerrarlo, que es justo lo que no se puede pedir con una mano.
    voz.continuous = false
    voz.interimResults = true
    voz.maxAlternatives = 1
    voz.onresult = (evento) => {
      const ultimo = evento.results[evento.results.length - 1]
      const dicho = ultimo?.[0]?.transcript ?? ''
      if (dicho) alDictar(dicho)
    }
    voz.onerror = (evento) => {
      // Los dos casos que se pueden contar sin mentir: no hay permiso, o no se oyo nada.
      setFallo(evento.error === 'not-allowed' || evento.error === 'service-not-allowed'
        ? 'No me has dado permiso para el micrófono.'
        : 'No te he oído. Prueba otra vez o escribe.')
      setEscuchando(false)
    }
    voz.onend = () => setEscuchando(false)
    reconocedor.current = voz
    setFallo(null)
    setEscuchando(true)
    try {
      voz.start()
    } catch {
      // Llamar a `start()` dos veces seguidas lanza: se dice y se sigue, sin dejar el boton
      // encendido mintiendo.
      setEscuchando(false)
      setFallo('El micrófono ya estaba escuchando.')
    }
  }

  return (
    <div className={cx('flex flex-wrap items-center gap-2', className)}>
      <Boton
        compacto
        variante={escuchando ? 'principal' : 'normal'}
        aria-pressed={escuchando}
        aria-label={escuchando ? 'Parar de escuchar' : 'Buscar hablando'}
        onClick={() => (escuchando ? para() : empieza())}
      >
        {/* Un icono dibujado con texto, como los demas de la aplicacion: nada de fuentes ni
            de imagenes de internet (la CSP no las deja). */}
        <span aria-hidden="true" className="text-lg leading-none">🎤</span>
      </Boton>
      {/* **Lo que pasa se dice con palabras.** Un boton que se pone de otro color al pulsarlo
          no dice si esta escuchando o si no ha entendido nada. */}
      <span role="status" aria-live="polite" className="text-xs text-tinta-suave">
        {escuchando ? 'Escuchando… habla y se escribe en el campo' : (fallo ?? '')}
      </span>
    </div>
  )
}
