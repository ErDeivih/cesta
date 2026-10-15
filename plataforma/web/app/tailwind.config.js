/** Tailwind 3, config clasica en JS.
 *
 *  - `darkMode: 'media'`: el tema sale del sistema y no hay interruptor, igual
 *    que en la web vieja. Un boton de tema es una cosa mas que mantener y que
 *    nadie pulsa dos veces.
 *  - La paleta es corta a proposito. Los colores que significan algo (aviso,
 *    error, bien) se usan siempre con el mismo tono, para que un rojo en esta
 *    app siempre quiera decir lo mismo.
 *
 *  ============================ LAS ESCALAS ============================
 *
 *  **Lo que faltaba, medido el 15/10/2026.** El tema tenia **paleta** y **una
 *  sola medida** (`maxWidth.app`), y nada mas: ni tipos, ni radios, ni sombras,
 *  ni movimiento, ni profundidad. *Y con eso, cada pantalla se inventaba sus
 *  numeros*, que es de donde salen **996 lineas de clases en linea** y una app
 *  que no se parece a si misma.
 *
 *  **Y todas las escalas de aqui abajo tienen la misma regla que los colores**:
 *  *si un nombre no esta en el tema, Tailwind **lo omite en silencio** y el
 *  estilo no se aplica.* Por eso hay una prueba que lo comprueba
 *  (`tests/test_interfaz.py::test_las_escalas_que_se_escriben_existen`), *y por
 *  eso son **extensiones con nombre** y no numeros sueltos por los ficheros.*
 *
 *  El porque de cada valor esta en `docs/ui/DIRECCION.md`.
 */
export default {
  darkMode: 'media',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Fuente del sistema: la app se sirve desde casa y no quiero que la
        // primera pintada dependa de fonts.googleapis.com.
        sans: ['IBM Plex Sans', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto',
               'Helvetica', 'Arial', 'sans-serif'],
        // Fraunces 600 para titulos cortos; Georgia mientras no se sirva el WOFF2 local.
        serif: ['Fraunces', 'Georgia', 'Times New Roman', 'serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },

      /* ---------------------------------------------------- la tipografia ---
       *
       * **Seis pasos y ni uno mas.** *Antes cada pantalla elegia su `text-lg`,
       * `text-xl` o `text-2xl` a ojo, *y por eso dos titulos del mismo rango
       * salian de distinto tamano en dos pantallas.*
       *
       * *El `lineHeight` va **pegado al tamano**, no suelto: un titulo de 36 px
       * con el interlineado del cuerpo son dos lineas que se tocan.*
       */
      fontSize: {
        // El antetitulo: *versalitas pequeñas que dicen en que seccion estas.*
        // *Ya existia en las capturas y **es lo unico con caracter que habia**: se conserva.
        antetitulo: ['0.6875rem', { lineHeight: '1rem', letterSpacing: '0.08em' }],
        // Etiquetas, metas y notas al pie.
        etiqueta: ['0.8125rem', { lineHeight: '1.15rem' }],
        // El cuerpo. *15 px y no 16: en una tabla de precios, 16 obliga a menos columnas.*
        cuerpo: ['0.9375rem', { lineHeight: '1.45rem' }],
        // El parrafo de entrada, el que explica de que va la pantalla.
        entrada: ['1.0625rem', { lineHeight: '1.6rem' }],
        // Titulo de seccion. *Serif.*
        titulo: ['1.5rem', { lineHeight: '1.9rem' }],
        // El titulo de la pantalla. *Serif.*
        portada: ['2.25rem', { lineHeight: '2.6rem' }],
      },

      /* --------------------------------------------------------- los radios ---
       *
       * *Tres niveles y una pastilla.* *Antes habia `rounded`, `rounded-md`,
       * `rounded-lg` y `rounded-full` mezclados sin criterio, *y una tarjeta con
       * el mismo radio que un boton no se lee como tarjeta.*
       */
      borderRadius: {
        nota: '4px',      // *lo mas pequeño: una etiqueta dentro de una linea*
        campo: '8px',     // *lo que se pulsa o se escribe: botones y campos*
        tarjeta: '14px',  // *una superficie con contenido dentro*
        hoja: '20px',     // *lo que flota por encima: dialogos y menus*
      },

      /* ---------------------------------------------------- la profundidad ---
       *
       * **Es lo que hoy no existe, y es la mitad de por que la app parece un
       * wireframe.** *Tres niveles, y en claro son sombras **calidas** (nunca
       * gris puro, que sobre marfil se ve sucio); en oscuro **una sombra casi no
       * se ve**, asi que alli la profundidad la da **el color de la superficie**
       * (`--papel-alto`) y la sombra solo la remata.*
       */
      boxShadow: {
        // *Nivel 0 no es una clase: es **no poner nada**. Se deja escrito en la direccion.*
        apoyado: 'var(--sombra-apoyado)',
        alzado: 'var(--sombra-alzado)',
        flotante: 'var(--sombra-flotante)',
      },

      /* ------------------------------------------------------- el movimiento ---
       *
       * **Dos duraciones y una curva, y ninguna mas.** *Quien elige «300 ms» o
       * «ease-in-out» a ojo esta inventando un idioma por pantalla.*
       *
       * *Y `prefers-reduced-motion` **ya esta resuelto globalmente** en
       * `estilos.css`: no hay que repetirlo en cada sitio.*
       */
      transitionDuration: {
        rapida: '120ms',  // *lo que responde al dedo: hover, foco, un boton*
        normal: '220ms',  // *lo que cambia de estado o entra en pantalla*
      },
      transitionTimingFunction: {
        // *Sale rapido y frena largo. Es la curva de «esto ya ha llegado».*
        suave: 'cubic-bezier(0.2, 0, 0, 1)',
      },

      /* ----------------------------------------------------------- el ritmo ---
       *
       * *El hueco **vertical** entre bloques, que es el que no existia: *por eso
       * el contenido flotaba arriba y el 60 % de la pantalla quedaba vacio.*
       */
      spacing: {
        bloque: '1.5rem',   // *entre dos cosas de la misma seccion*
        seccion: '2.5rem',  // *entre dos secciones*
        pagina: '3.5rem',   // *el aire de arriba y de abajo de una pantalla*
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
        // Direccion visual de SUPERAPP-01 (valores en estilos.css, en los dos temas).
        marfil: 'var(--marfil)',
        papel: 'var(--papel)',
        // *** Y LA TERCERA SUPERFICIE ***: *lo que flota por encima del papel.*
        // *Sin ella, en modo oscuro un dialogo y una tarjeta son **el mismo
        // color**, y la profundidad no se puede ver por mucho que se sombree.*
        'papel-alto': 'var(--papel-alto)',
        bosque: 'var(--bosque)',
        'tinta-fuerte': 'var(--tinta-fuerte)',
        secundaria: 'var(--secundaria)',
        terracota: 'var(--terracota)',
        // *El acento cuando es **fondo** y no linea: *un lavado del mismo tono,
        // para la seccion activa y los avisos suaves.*
        'terracota-suave': 'var(--terracota-suave)',
        'borde-fuerte': 'var(--borde-fuerte)',
        error: 'var(--error)',
        aviso: 'var(--aviso)',
        bien: 'var(--bien)',
        'bien-suave': 'var(--bien-suave)',
      },
      maxWidth: {
        // El ancho de la app: mas alla de esto, una fila de tabla obliga a
        // girar la cabeza para leerla.
        app: '78rem',
        // *Y el ancho de **lectura**: un parrafo de 78 rem son 150 caracteres,
        // y a partir de 80 la vista se pierde de linea.*
        lectura: '42rem',
      },
    },
  },
  plugins: [],
}
