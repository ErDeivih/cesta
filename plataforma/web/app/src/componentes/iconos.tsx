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
