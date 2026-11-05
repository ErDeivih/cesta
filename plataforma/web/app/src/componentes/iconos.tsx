/** Los iconos, a mano y en SVG.
 *
 *  Cinco trazos no justifican una libreria de iconos entera. Todos van con
 *  `aria-hidden`: el nombre lo lleva el boton, que es lo que lee un lector de
 *  pantalla. Un icono suelto no significa nada.
 */
import type { SVGProps } from 'react'

function Base({ children, ...resto }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...resto}
    >
      {children}
    </svg>
  )
}

export function IconoLupa(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </Base>
  )
}

/** La casa: el icono de **Inicio**, la pantalla que contesta las cuatro preguntas.
 *
 *  Se dibuja a mano como los demas. No lleva techo a dos aguas ni chimenea, que es lo que
 *  convierte una casa en un dibujo de una casa: el trazo tiene que leerse a 22 px en una
 *  barra de abajo, con el brillo bajo y de reojo. */
export function IconoCasa(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M4 10.5 12 4l8 6.5" />
      <path d="M6 10v10h12V10" />
      <path d="M10 20v-5h4v5" />
    </Base>
  )
}

export function IconoCodigoBarras(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M3 5v14M7 5v14M11 5v10M15 5v14M19 5v14M21 5v14" />
    </Base>
  )
}

export function IconoPanel(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
    </Base>
  )
}

export function IconoEnlace(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1" />
      <path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1" />
    </Base>
  )
}

export function IconoCamara(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M3 8a2 2 0 0 1 2-2h2l1.5-2h7L17 6h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <circle cx="12" cy="12.5" r="3.5" />
    </Base>
  )
}

export function IconoBalanza(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M12 4v16M6 20h12M5 8h14M5 8l-3 6h6zM19 8l-3 6h6z" />
    </Base>
  )
}

export function IconoGrafica(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M4 19h16M4 15l4-5 4 3 5-8" />
    </Base>
  )
}

/** El corazon de Favoritos. Se anade el 25 de septiembre de 2026, cuando Favoritos
 *  entra en la barra: hasta entonces no hacia falta, porque a la pantalla solo se
 *  llegaba escribiendo la direccion. */
export function IconoCorazon(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M12 20s-7-4.4-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 2.8C19 15.6 12 20 12 20z" />
    </Base>
  )
}

/** El carro: la lista de la compra. Sustituye a la grafica en la barra de abajo
 *  porque «Lista» con una grafica al lado se leia como «Panel». */
export function IconoCarro(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M3 5h2l2.4 10.2a1.5 1.5 0 0 0 1.5 1.2h7.8a1.5 1.5 0 0 0 1.5-1.2L20 8H6" />
      <circle cx="9.5" cy="19.5" r="1.4" />
      <circle cx="17" cy="19.5" r="1.4" />
    </Base>
  )
}

/* ======================= los tres del 15/10/2026 =======================
 *
 * *Los pide la FASE 3, y son **los tres que faltaban** para que **cada destino
 * tenga su icono**: *el **recetario**, *el **plan semanal** *y **Calorias**.* *
 *
 * *** Y hay una regla que hace que no hagan falta nueve iconos distintos. *** *
 * *`Suite.tsx` dice, de las subsecciones: *«*las de esta aplicacion. *** Nunca las
 * de otra ***»* *-- *solo se ven **las de la aplicacion activa** --.* *Asi que un
 * icono **solo tiene que distinguirse dentro de su aplicacion**, *y por eso el
 * **libro** vale para «Mi recetario» **y** para «Mi diario»: *son libros los dos,
 * *y **nunca se ven juntos.*** *
 *
 * *Y por eso mismo hacen falta **tres** y no nueve: *los de las subsecciones de
 * Compra ya existian *(-- lupa, carro, corazon, grafica --)*, *y los de Recetas y
 * Calorias son estos.* *
 *
 * *El trazo es el mismo que los otros diez: *`24`, *1,8 de grosor, *remates
 * redondos, *y **dos o tres piezas**, *porque tienen que leerse a 20 px en un
 * lateral, *de reojo y con el brillo bajo.* *
 */

/** **El recetario** *(-- y «Mi diario»: *un diario tambien es un libro --).*
 *
 * *Un libro cerrado visto de frente: *el bloque y **la costura del lomo**.* *
 * *Sin hojas ni canto, *que es lo que convierte un libro en **el dibujo de un
 * libro**: *a 20 px eso es ruido, *y el trazo tiene que decir «libro» de un
 * vistazo.* *
 */
export function IconoLibro(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M5 4a1 1 0 0 1 1-1h13v18H6a1 1 0 0 1-1-1z" />
      <path d="M8.5 3v18" />
    </Base>
  )
}

/** **El plan semanal**: *un calendario de la semana.* *
 *
 * *Va con **el lomo de arriba y las dos anillas**, *que es lo que lo distingue de
 * una tarjeta o de una ventana.* *
 */
export function IconoCalendario(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h13A1.5 1.5 0 0 1 20 6.5V19a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19z" />
      <path d="M4 10h16M8 3v4M16 3v4" />
    </Base>
  )
}

/** **Calorias**: *un plato.* *
 *
 * *No una llama, *que seria **lo que se gasta** y no **lo que se come**, *y esta
 * aplicacion es **el diario de lo que comes.*** *Y el plato se lee a cualquier
 * tamano: *dos circulos, *y ya esta.* *
 */
export function IconoPlato(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4" />
    </Base>
  )
}

/** **Cuenta y preferencias**: *una persona.* *
 *
 * *Es el cuarto que hizo falta, *y el ultimo: *«Cuenta» **no es** ni un panel, *ni
 * un enlace, *ni una camara*, *y **reutilizar cualquiera de los tres** habria
 * dicho algo falso.* *Asi que se dibuja, *que son **dos trazos**: *la cabeza y los
 * hombros.* *
 */
export function IconoPersona(props: SVGProps<SVGSVGElement>) {
  return (
    <Base {...props}>
      <circle cx="12" cy="7.5" r="3.5" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </Base>
  )
}

/* ==================== las tres flechas del precio ====================
 *
 * *Las pide la ficha del producto: el chip de «está caro / está bien» lleva **flecha y palabra**,
 * **no solo color**, y esa es una regla de accesibilidad de la casa -- *el par sube/baja no se
 * distingue de un vistazo para todo el mundo, y menos a pleno sol en la puerta de un supermercado.*
 *
 * *Tres y no una con `rotate`: el trazo de «igual» no es una flecha girada, es un trazo corto.*
 * *Y van con `strokeWidth` de 2, más grueso que el resto: se leen a 14 px, dentro de una píldora.*
 */

export function IconoPrecioArriba(props: SVGProps<SVGSVGElement>) {
  return (
    <Base strokeWidth="2" {...props}>
      <path d="M12 19V5M6 11l6-6 6 6" />
    </Base>
  )
}

export function IconoPrecioAbajo(props: SVGProps<SVGSVGElement>) {
  return (
    <Base strokeWidth="2" {...props}>
      <path d="M12 5v14M6 13l6 6 6-6" />
    </Base>
  )
}

export function IconoPrecioIgual(props: SVGProps<SVGSVGElement>) {
  return (
    <Base strokeWidth="2" {...props}>
      <path d="M5 12h14" />
    </Base>
  )
}

/** **La marca de «esto es lo más barato».** *Un trazo, como el resto.* */
export function IconoCheck(props: SVGProps<SVGSVGElement>) {
  return (
    <Base strokeWidth="2" {...props}>
      <path d="m5 13 4 4L19 7" />
    </Base>
  )
}

export function IconoCorazonLleno(props: SVGProps<SVGSVGElement>) {
  return (
    <Base fill="currentColor" {...props}>
      <path d="M12 20s-7-4.4-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 2.8C19 15.6 12 20 12 20z" />
    </Base>
  )
}
