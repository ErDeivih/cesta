/** *Lo minimo para que las pruebas de componente se lean bien.* */
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// *Sin esto, un componente montado en una prueba sigue en el documento en la siguiente.*
afterEach(() => {
  cleanup()
})
