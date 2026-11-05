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
    ayuda: 'Cuánto te importa el precio.',
  },
  {
    clave: 'letra',
    texto: 'Letra (calidad o gama)',
    // *** AQUÍ HABÍA UNA EXPLICACIÓN DE CÓMO SE CALCULA LA LETRA. *** *
    // *Ocupaba cinco líneas y contaba que si sale de los ingredientes es calidad y si sale de
    // ordenar por precio es gama, y que las dos no se suman.* *Eso se lee en el sello de cada
    // producto, que ya dice cuál es la suya; aquí no cabía y no cambia qué se pulsa.*
    ayuda: '',
  },
  {
    clave: 'cercania',
    texto: 'Cercanía al mejor precio',
    ayuda: 'Cuánto te importa no alejarte del más barato.',
  },
  {
    clave: 'promo',
    texto: 'Promoción',
    ayuda: 'Cuánto te importan las ofertas que bajan lo que pagas hoy.',
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
      className="rounded-tarjeta border border-borde bg-papel p-4 "
    >
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-entrada font-semibold">Qué te importa</h2>
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

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {CAMPOS.map((c) => (
          <div key={c.clave}>
            <div className="flex items-baseline justify-between gap-2">
              <label htmlFor={`peso-${c.clave}`} className="text-cuerpo font-medium">
                {c.texto}
              </label>
              <output htmlFor={`peso-${c.clave}`} className="cifra text-cuerpo text-secundaria ">
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
              className="h-11 w-full accent-terracota "
            />
            {c.ayuda && (
              <p id={`ayuda-${c.clave}`} className="text-etiqueta text-secundaria ">
                {c.ayuda}
              </p>
            )}
          </div>
        ))}
      </div>

      <p
        className={cx(
          'mt-3 rounded-campo px-3 py-2 text-cuerpo',
          todosCero
            ? 'bg-marfil text-aviso '
            : 'bg-marfil text-tinta-fuerte ',
        )}
      >
        {explicacion}
      </p>
    </section>
  )
}