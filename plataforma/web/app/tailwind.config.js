/** Tailwind 3, config clasica en JS.
 *
 *  - `darkMode: 'media'`: el tema sale del sistema y no hay interruptor, igual
 *    que en la web vieja. Un boton de tema es una cosa mas que mantener y que
 *    nadie pulsa dos veces.
 *  - La paleta es la del sistema **Cesta App** aprobado por David
 *    (`designs/cesta-app-design-system/project/tokens.json` y `tokens.css`).
 *    Los valores se copiaron de alli, no se eligieron aqui. Los colores que
 *    significan algo (aviso, error, bien) se usan siempre con el mismo tono.
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
 *
 *  ========================= LOS 38 COLORES ============================
 *
 *  **Los 38 del sistema, con sus dos temas.** Los valores viven en
 *  `src/estilos.css` (variables), porque las clases se escriben sin `dark:` y
 *  tienen que cambiar solas: `text-tinta-suave` sirve de dia y de noche. Si se
 *  anade un color aqui, hay que anadirlo alli en los dos temas:
 *  `test_interfaz.py::test_los_colores_del_tema_tienen_valor_en_los_dos_temas`
 *  lo comprueba.
 *
 *  **Y se conservan los alias de la direccion anterior** (`tinta-fuerte`,
 *  `secundaria`, `fondo`, `terracota-suave`, `bien-suave`, `aviso-suave`), que
 *  es lo que usan las pantallas que ya existen. No son colores nuevos: apuntan
 *  al token aprobado que les corresponde, para que la app entera cambie de
 *  valores sin tocar cien ficheros y sin que ninguna clase se quede sin definir
 *  (Tailwind la omitiria en silencio).
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
        // *El mismo nombre que el token del sistema (`--font-display`), para que
        //  una pantalla pueda pedir `font-display` sin inventarse otra escala.*
        display: ['Fraunces', 'Georgia', 'Times New Roman', 'serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },

      /* ---------------------------------------------------- la tipografia ---
       *
       * **Los pasos del sistema, y ni uno mas.** *Antes cada pantalla elegia su
       * `text-lg`, `text-xl` o `text-2xl` a ojo, *y por eso dos titulos del
       * mismo rango salian de distinto tamano en dos pantallas.*
       *
       * *El `lineHeight` va **pegado al tamano**, no suelto: un titulo de 34 px
       * con el interlineado del cuerpo son dos lineas que se tocan.*
       *
       * *`antetitulo` se queda como **alias** de `micro`: lo usan las pantallas
       * de antes y significa lo mismo (versalitas de 12 px con 0,08 em).*
       */
      fontSize: {
        // *Antetitulo en versalitas: «MI CESTA», «SE HAN MOVIDO».*
        micro: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.08em' }],
        antetitulo: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.08em' }],
        // Etiquetas, metas y notas al pie.
        etiqueta: ['0.8125rem', { lineHeight: '1.125rem' }],
        'etiqueta-fuerte': ['0.8125rem', { lineHeight: '1.125rem', fontWeight: '600' }],
        // El cuerpo. *16 px y no 15: en el movil se lee de pie y a un brazo.*
        cuerpo: ['1rem', { lineHeight: '1.5625rem' }],
        'cuerpo-fuerte': ['1rem', { lineHeight: '1.5rem', fontWeight: '600' }],
        // El parrafo de entrada, el que explica de que va la pantalla.
        entrada: ['1.0625rem', { lineHeight: '1.625rem' }],
        // Titulo de seccion y de producto dentro de una tarjeta grande. *Serif.*
        titulo: ['1.5rem', { lineHeight: '1.8125rem' }],
        subtitulo: ['1.1875rem', { lineHeight: '1.5625rem' }],
        // El titulo de la pantalla. *Serif, uno por pantalla.*
        portada: ['2.125rem', { lineHeight: '2.375rem', letterSpacing: '-0.01em' }],
        // Las cifras. *Nunca en Fraunces: comparar precios pide cifras alineadas.*
        'precio-grande': ['1.875rem', { lineHeight: '2.125rem' }],
        precio: ['1.25rem', { lineHeight: '1.5rem' }],
        'precio-fila': ['1.0625rem', { lineHeight: '1.375rem' }],
      },

      /* --------------------------------------------------------- los radios ---
       *
       * *Cinco, y cada uno dice que es la superficie.* *Antes habia `rounded`,
       * `rounded-md`, `rounded-lg` y `rounded-full` mezclados sin criterio, *y
       * una tarjeta con el mismo radio que un boton no se lee como tarjeta.*
       */
      borderRadius: {
        nota: 'var(--radio-nota)',          // 4 px: una letra, una insignia
        campo: 'var(--radio-campo)',        // 10 px: lo que se pulsa o se escribe
        tarjeta: 'var(--radio-tarjeta)',    // 16 px: una superficie con contenido
        hoja: 'var(--radio-hoja)',          // 24 px: lo que flota por encima
        pastilla: 'var(--radio-pastilla)',  // 999 px: solo una pildora de verdad
      },

      /* ---------------------------------------------------- la profundidad ---
       *
       * **Tres niveles.** *En claro son sombras **calidas** (nunca gris puro, que
       * sobre marfil se ve sucio); en oscuro **una sombra casi no se ve**, asi que
       * alli la profundidad la da **el color de la superficie** (`papel-alto`) y la
       * sombra solo la remata.*
       */
      boxShadow: {
        // *Nivel 0 no es una clase: es **no poner nada**.*
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
        rapida: 'var(--movimiento-duracion-rapida)',  // 120 ms
        normal: 'var(--movimiento-duracion-normal)',  // 220 ms
      },
      transitionTimingFunction: {
        // *Sale rapido y frena largo. Es la curva de «esto ya ha llegado».*
        suave: 'var(--movimiento-curva-suave)',
      },

      /* ----------------------------------------------------------- el ritmo ---
       *
       * *El sistema aprueba la rejilla de **4, 8, 12, 16, 24, 32 y 48 px**, y
       * **esa es exactamente la escala numerica de Tailwind**: `1` son 4 px,
       * `2` son 8, `3` son 12, `4` son 16, `6` son 24, `8` son 32 y `12` son 48.
       * Por eso **no se redefinen los numeros** -- hacerlo convertiria cada
       * `p-4` de la app en 4 px -- y el ritmo con nombre apunta a los pasos
       * aprobados. `toque` es el minimo de 44 px para lo que se pulsa.*
       */
      spacing: {
        bloque: 'var(--space-24)',   // 24 px: entre dos cosas de la misma seccion
        seccion: 'var(--space-32)',  // 32 px: entre dos secciones
        pagina: 'var(--space-48)',   // 48 px: el aire de arriba y de abajo
        toque: 'var(--toque-minimo)',// 44 px: el alto minimo de lo que se pulsa
      },

      colors: {
        // ------- las superficies -------
        marfil: 'var(--marfil)',
        papel: 'var(--papel)',
        'papel-alto': 'var(--papel-alto)',
        // ------- los lavados: un fondo, y encima va tinta -------
        'lavado-verde': 'var(--lavado-verde)',
        'lavado-terracota': 'var(--lavado-terracota)',
        'lavado-aviso': 'var(--lavado-aviso)',
        'lavado-error': 'var(--lavado-error)',
        // ------- los limites -------
        borde: 'var(--borde)',
        'borde-fuerte': 'var(--borde-fuerte)',
        // ------- la tinta -------
        tinta: 'var(--tinta)',
        'tinta-suave': 'var(--tinta-suave)',
        'tinta-tenue': 'var(--tinta-tenue)',
        // ------- la marca -------
        verde: 'var(--verde)',
        'verde-fuerte': 'var(--verde-fuerte)',
        bosque: 'var(--bosque)',
        terracota: 'var(--terracota)',
        lima: 'var(--lima)',
        'sobre-lima': 'var(--sobre-lima)',
        'sobre-verde': 'var(--sobre-verde)',
        'sobre-bosque': 'var(--sobre-bosque)',
        'sobre-terracota': 'var(--sobre-terracota)',
        // ------- lo que significa algo -------
        bien: 'var(--bien)',
        aviso: 'var(--aviso)',
        error: 'var(--error)',
        // ------- los precios -------
        'precio-antes': 'var(--precio-antes)',
        'precio-unidad': 'var(--precio-unidad)',
        'precio-baja': 'var(--precio-baja)',
        'precio-sube': 'var(--precio-sube)',
        // ------- el Nutri-Score, con sus textos -------
        'nutri-a': 'var(--nutri-a)',
        'nutri-b': 'var(--nutri-b)',
        'nutri-c': 'var(--nutri-c)',
        'nutri-d': 'var(--nutri-d)',
        'nutri-e': 'var(--nutri-e)',
        'nutri-texto-a': 'var(--nutri-texto-a)',
        'nutri-texto-b-e': 'var(--nutri-texto-b-e)',
        'nutri-texto-e': 'var(--nutri-texto-e)',
        // ------- los sellos -------
        'sello-fondo': 'var(--sello-fondo)',
        'sello-tinta': 'var(--sello-tinta)',

        // ================= ALIAS DE LA DIRECCION ANTERIOR =================
        // *No son colores nuevos: son los nombres que ya escriben las pantallas,
        // apuntando al token aprobado que les toca. Asi el cambio de valores llega
        // a toda la app sin tocar cien ficheros y sin una clase huerfana.*
        'tinta-fuerte': 'var(--tinta)',
        secundaria: 'var(--tinta-suave)',
        fondo: 'var(--fondo)',
        'terracota-suave': 'var(--lavado-terracota)',
        'bien-suave': 'var(--lavado-verde)',
        'aviso-suave': 'var(--lavado-aviso)',
        // *Los dos unicos que admiten opacidad de verdad* (-- el velo de un dialogo
        //  y una cabecera pegada --). *`<alpha-value>` la pone **dentro del `rgb()`**;
        //  una variable con `#rrggbb` dentro no vale ahi y el navegador la ignora.*
        'papel-translucido': 'rgb(var(--papel-rgb) / <alpha-value>)',
        'tinta-translucida': 'rgb(var(--tinta-rgb) / <alpha-value>)',
      },
      maxWidth: {
        // El ancho de la app: mas alla de esto, una fila de tabla obliga a
        // girar la cabeza para leerla.
        app: '78rem',
        // *Y el ancho de **lectura**: un parrafo de 78 rem son 150 caracteres,
        // y a partir de 80 la vista se pierde de linea.*
        lectura: '42rem',
        // *La portada se compone a 390 px; en escritorio se queda en esa columna
        // centrada para no convertir el movil en una fila de 1400 px.*
        portada: '30rem',
      },
    },
  },
  plugins: [],
}
