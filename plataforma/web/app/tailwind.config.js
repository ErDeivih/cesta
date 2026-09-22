/** Tailwind 3, config clasica en JS.
 *
 *  - `darkMode: 'media'`: el tema sale del sistema y no hay interruptor, igual
 *    que en la web vieja. Un boton de tema es una cosa mas que mantener y que
 *    nadie pulsa dos veces.
 *  - La paleta es corta a proposito. Los colores que significan algo (aviso,
 *    error, bien) se usan siempre con el mismo tono, para que un rojo en esta
 *    app siempre quiera decir lo mismo.
 */
export default {
  darkMode: 'media',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Fuente del sistema: la app se sirve desde casa y no quiero que la
        // primera pintada dependa de fonts.googleapis.com.
        sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      colors: {
        tinta: { claro: '#141618', oscuro: '#f1f2f3' },
        // Los nombres con significado. Los valores viven en estilos.css, porque
        // tienen que cambiar con el tema y estas clases se escriben sin `dark:`.
        // Si se anade uno aqui, hay que anadirlo tambien alli en los dos temas:
        // el test `test_interfaz.py::test_colores_conocidos` lo comprueba.
        'tinta-suave': 'var(--tinta-suave)',
        fondo: 'var(--fondo)',
        borde: 'var(--borde)',
        aviso: 'var(--aviso)',
        bien: 'var(--bien)',
        'bien-suave': 'var(--bien-suave)',
      },
      maxWidth: {
        // El ancho de la app: mas alla de esto, una fila de tabla obliga a
        // girar la cabeza para leerla.
        app: '78rem',
      },
    },
  },
  plugins: [],
}
