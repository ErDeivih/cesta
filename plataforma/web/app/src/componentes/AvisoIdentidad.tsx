/** El aviso de que una linea se resuelve con otro producto, o con uno que no se puede confirmar.
 *
 *  **Solo aparece cuando hay algo que decir.** Con `exacto` o sin veredicto no pinta nada: un aviso
 *  que sale siempre deja de leerse.
 *
 *  **Y distingue los dos casos que importan.** `probable` es "parece el mismo, pero no tengo el codigo
 *  que lo confirme": pide prudencia. `alternativa`, `cuarentena` o `abstiene` es "esto no es lo que
 *  pediste": pide una decision. Juntarlos en un solo aviso naranja seria perder la unica distincion
 *  que el motor de identidad se ha molestado en calcular.
 *
 *  El encargo es explicito en esto: *elegir un producto concreto no autoriza a sustituirlo por otro mas
 *  barato*, y una sustitucion que no se ve es exactamente lo que hay que evitar.
 */
import { euros, nombreCadena } from '../api/formato'
import { cx } from './ui'

const CONFIRMADO = new Set(['exacto', null, undefined])

export function AvisoIdentidad({ identidad, motivo, alternativa, className }: {
  identidad?: string | null
  motivo?: string | null
  alternativa?: { nombre: string; coste_cent: number; fuente: string } | null
  className?: string
}) {
  if (CONFIRMADO.has(identidad)) return null
  const esSeguro = identidad === 'probable'
  return (
    <p
      role="note"
      className={cx(
        'mt-1 rounded-md border px-2 py-1 text-[13px] leading-[18px]',
        esSeguro ? 'border-aviso text-aviso' : 'border-error text-error',
        className,
      )}
    >
      {esSeguro
        ? 'Puede que sea el mismo producto, pero no hay codigo que lo confirme.'
        : 'Ojo: esta linea se resuelve con otro producto, no con el que pediste.'}
      {motivo && <span className="block text-secundaria">{motivo}</span>}
      {/* **Que se puede pedir en su lugar, y por cuanto.** Un aviso que dice "esto no es lo tuyo" y no
          ofrece nada deja a quien compra sin salida; con la alternativa delante, el aviso se convierte en
          una decision. El precio, con `euros`, y la cadena, con `nombreCadena`: son las dos reglas del
          proyecto para lo que se lee, y aqui se lee. */}
      {alternativa && (
        <span className="mt-1 block tabular-nums text-tinta-fuerte">
          En su lugar puedes pedir <strong>{alternativa.nombre}</strong> por{' '}
          {euros(alternativa.coste_cent)} en {nombreCadena(alternativa.fuente)}.
        </span>
      )}
    </p>
  )
}
