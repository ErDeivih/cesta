/** *** EL ENSAYO DE COMPONENTES, QUE NO EXISTIA. ***
 *
 *  *M02 pide «prueba del componente montado: carga -> dato valido -> ficha y armazon».* *Hasta el
 *  18/10/2026 el frontend solo tenia pruebas de funciones (`node --test`), y por eso **no se vio** que
 *  la ficha se quedaba en blanco: ninguna prueba montaba el componente.*
 *
 *  *Este fichero y `src/pruebas/setup.ts` son la infraestructura. Los `.test.tsx` van al lado del
 *  componente, y `node --test` sigue con lo suyo: los dos runners conviven.*
 */
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/pruebas/setup.ts'],
    include: ['src/**/*.test.tsx', 'src/**/*.test.ts'],
    // *Los .test.mjs de `tests/` son del runner de Node: no se mezclan.*
    exclude: ['tests/**', 'node_modules/**', 'dist/**'],
  },
})
