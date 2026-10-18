/** *** EL COMPROBADOR OFICIAL DE LAS REGLAS DE HOOKS. ***
 *
 *  *La prueba textual de `tests/hooks.test.mjs` cubre el patron que fallo el 18/10/2026
 *  -- un `useMemo` detras de un retorno de una linea en un componente `function` --, pero
 *  **no es el comprobador**: no ve un retorno partido en varias lineas ni un componente
 *  escrito como funcion flecha.* *Eso lo ve `eslint-plugin-react-hooks`, y por eso esta
 *  aqui.*
 *
 *  *La prueba textual se queda, con su alcance dicho: protege el caso concreto sin
 *  depender de una instalacion.*
 *
 *  **Solo las reglas de hooks, de momento.** *No se activa `js.configs.recommended`
 *  entero: eso traeria cientos de avisos que no son de este encargo y taparia el que
 *  importa.* *El objetivo de M02 es que el fallo de hooks no pueda volver, no reescribir
 *  el estilo del proyecto de una vez.*
 */
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'

export default tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**', 'tests/**', '*.config.*', 'vite.config.ts'],
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { ecmaFeatures: { jsx: true }, sourceType: 'module' },
    },
    plugins: { 'react-hooks': reactHooks },
    rules: {
      // *Las dos que importan:* la de orden y la de dependencias.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
)
