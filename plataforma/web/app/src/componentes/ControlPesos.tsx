/** El control de pesos de la pantalla de grupo.
 *
 *  Cuatro numeros y una frase que dice que hacen. Un control de pesos sin la
 *  explicacion al lado es un numero magico: quien mira ve cambiar el orden y no
 *  sabe por que, que es exactamente lo contrario de para lo que sirve esto.
 *
 *  Los pesos NO son porcentajes guardados: se normalizan al calcular (45/25/20/10
 *  es lo mismo que 9/5/4/2). Asi se puede subir uno a 100 sin tener que bajar
 *  los otros tres.
 */
import { PESOS_INICIALES, type Pesos } from '../logica/pesos'
import { Boton, cx } from './ui'

const CAMPOS: { clave: keyof Pesos; texto: string; ayuda: string }[] = [
  {
    clave: 'precio',
    texto: 'Precio por unidad',
    ayuda: 'Cuánto pesa que sea barato. El más barato del grupo se lleva el 100 % de esta parte.',
  },
  {
    clave: 'letra',
    texto: 'Letra (calidad o gama)',
    ayuda:
      'Cuánto pesa la letra A/B/C. Si sale de leer ingredientes es calidad; si sale de ordenar por precio es gama, y en ese caso la A es el MÁS CARO del grupo. Cada alternativa usa la que traiga y lo dice. Las dos no se suman nunca.',
  },
  {
    clave: 'cercania',
    texto: 'Cercanía al mejor precio',
    ayuda:
      'Cuánto pesa no alejarse del mejor. Vale 1 hasta un 5 % por encima del más barato y baja a 0 cuando llega al 50 % más caro.',
  },
  {
    clave: 'promo',
    texto: 'Promoción',
    ayuda:
      'Cuánto pesa que haya oferta que baje lo que pagas hoy en caja. Las de tarjeta cuentan la mitad: no bajan el precio, llenan un monedero.',
  },
]

interface Props {
  pesos: Pesos
  onCambio: (p: Pesos) => void
  explicacion: string
}

export function ControlPesos({ pesos, onCambio, explicacion }: Props) {
  const suma = pesos.precio + pesos.letra + pesos.cercania + pesos.promo
  const todosCero = suma <= 0

  return (
    <section
      aria-label="Pesos del orden"
      className="rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-700 dark:bg-neutral-800"
    >
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold">Qué te importa</h2>
        <div className="flex gap-2">
          <Boton variante="sutil" onClick={() => onCambio(PESOS_INICIALES)}>
            Volver a lo de siempre
          </Boton>
          <Boton
            variante="normal"
            onClick={() => onCambio({ precio: 100, letra: 0, cercania: 0, promo: 0 })}
            title="Ordena solo por precio por unidad"
          >
            Solo el precio
          </Boton>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        {CAMPOS.map((c) => (
          <div key={c.clave}>
            <div className="flex items-baseline justify-between gap-2">
              <label htmlFor={`peso-${c.clave}`} className="text-sm font-medium">
                {c.texto}
              </label>
              <output htmlFor={`peso-${c.clave}`} className="cifra text-sm text-neutral-600 dark:text-neutral-400">
                {pesos[c.clave]}
              </output>
            </div>
            <input
              id={`peso-${c.clave}`}
              type="range"
              min={0}
              max={100}
              step={5}
              value={pesos[c.clave]}
              onChange={(e) => onCambio({ ...pesos, [c.clave]: Number(e.target.value) })}
              aria-describedby={`ayuda-${c.clave}`}
              // El carril mide 44 px de alto para poder arrastrarlo con el dedo
              // sin acertarle a la bolita.
              className="h-11 w-full accent-sky-700 dark:accent-sky-500"
            />
            <p id={`ayuda-${c.clave}`} className="text-xs text-neutral-600 dark:text-neutral-400">
              {c.ayuda}
            </p>
          </div>
        ))}
      </div>

      <p
        className={cx(
          'mt-3 rounded-lg px-3 py-2 text-sm',
          todosCero
            ? 'bg-amber-50 text-amber-950 dark:bg-amber-950 dark:text-amber-100'
            : 'bg-neutral-100 text-neutral-800 dark:bg-neutral-900 dark:text-neutral-200',
        )}
      >
        {explicacion}
      </p>
    </section>
  )
}
