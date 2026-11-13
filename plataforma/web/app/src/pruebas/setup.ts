/** *Lo minimo para que las pruebas de componente se lean bien.* */
import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// *Sin esto, un componente montado en una prueba sigue en el documento en la siguiente.*
afterEach(() => {
  cleanup()
})

// *** LO QUE JSDOM NO TRAE, *y el codigo de la app si usa***.
//
// *`matchMedia` lo pide cualquier consulta de tema o de preferencia de movimiento, y jsdom no lo
// implementa: sin esto la prueba revienta **antes de montar nada**, con «matchMedia is not a
// function», y no se aprende nada del componente.* *Se pone una version minima que dice siempre
// «no coincide», que es lo que hace un navegador sin esas preferencias.*
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (consulta: string) => ({
      matches: false,
      media: consulta,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  })
}

// *Y el observador de tamano, que usan las graficas: sin el, cualquier componente con `Chispa`
// revienta al montarse.*
if (!('ResizeObserver' in window)) {
  class ObservadorFalso {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  Object.defineProperty(window, 'ResizeObserver', { writable: true, value: ObservadorFalso })
}

// *** Y LAS ANIMACIONES DE LO QUE SE ABRE (`@ui-sdk`). ***
//
// *Las capas de `@ui-sdk` (combobox, dialogo) esperan a que terminen sus animaciones con
// `elemento.getAnimations()`, que jsdom no implementa. Sin esto, cada prueba que abre una capa
// termina con una **excepcion no capturada despues del test**: el test sale verde y el fichero
// rojo, que es peor que un fallo porque se lee como si fuera otra cosa.* *Vacio, que es lo que
// devuelve un elemento sin animaciones en un navegador.*
if (!Element.prototype.getAnimations) {
  Object.defineProperty(Element.prototype, 'getAnimations', {
    writable: true,
    value: () => [],
  })
}

// *** Y LAS CAPAS DE `@ui-sdk`, QUE JSDOM NO SABE ENFOCAR. ***
//
// *jsdom no implementa la API `popover`, pero **si trata `[popover]` como una capa cerrada**:
// dentro de ella no se puede enfocar nada (ni un `button`, ni un contenedor con `tabindex`), y
// los roles de dentro no cuentan como accesibles.*
//
// *`@ui-sdk` marca con `popover` sus dialogos y comboboxes, asi que sin quitarlo las pruebas
// montan la capa y **no pueden medir ni el foco ni el nombre**: el dialogo existe en el DOM pero
// la prueba no lo ve.* *En un navegador la capa se abre con `showPopover()`; aqui, que no hay API
// de popover, la marca no aporta nada y se quita: el elemento se comporta como un `div` normal,
// que es justo lo que se quiere medir (ARIA, foco, teclado).*
const quitarPopover = (raiz: ParentNode) => {
  raiz.querySelectorAll?.('[popover]').forEach((elemento) => elemento.removeAttribute('popover'))
  if (raiz instanceof HTMLElement && raiz.hasAttribute('popover')) raiz.removeAttribute('popover')
}

const observadorDeCapas = new MutationObserver((mutaciones) => {
  for (const mutacion of mutaciones) {
    if (mutacion.type === 'attributes' && mutacion.target instanceof HTMLElement) {
      quitarPopover(mutacion.target)
      continue
    }
    for (const nodo of Array.from(mutacion.addedNodes)) {
      if (nodo instanceof HTMLElement) {
        quitarPopover(nodo)
        nodo.querySelectorAll('[popover]').forEach((elemento) => elemento.removeAttribute('popover'))
      }
    }
  }
})
observadorDeCapas.observe(document, {
  subtree: true,
  childList: true,
  attributes: true,
  attributeFilter: ['popover'],
})
