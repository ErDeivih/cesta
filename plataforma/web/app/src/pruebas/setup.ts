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
