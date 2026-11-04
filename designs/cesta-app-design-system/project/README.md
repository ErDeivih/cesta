## La dirección: **vivo y claro**, no un panel gris

Un **mercado a mediodía**: papel cálido, verde de huerta, tomate y lima. La app se usa de pie, con el
carro en una mano y el móvil en la otra; lo que se ve primero tiene que decir *«esto me sirve»* en un
vistazo, y el color es parte de esa respuesta. Los precios no son un cuadro de datos: son la razón por
la que alguien abre la app.

De dónde viene: el proyecto ya era **marfil, bosque y terracota**, con Fraunces para títulos e IBM Plex
Sans para la interfaz. Eso se queda. Lo que cambia es la intensidad: el marfil se aclara para que el
color destaque, el bosque se mantiene como superficie oscura de marca y el acento sube a dos (verde de
huerta y terracota), con lima reservado para el ahorro. No hay modo «panel de administración»: ninguna
pantalla se resuelve con grises y bordes grises.

Tres reglas que valen para todo lo que se construya con este sistema:

1. **El color dice algo.** El verde es «más barato», la terracota es «esto es de la casa», el lima es
   «te ahorras». Un color que no diga nada no se usa.
2. **La cifra manda.** El precio va en el sitio de mayor peso de la pantalla; todo lo demás lo explica.
   Las cifras van en IBM Plex con `tabular-nums` (clase `cifra`), nunca en Fraunces: comparar dos
   precios exige cifras alineadas.
3. **Cálido, nunca sucio.** Las sombras llevan el marrón del papel dentro; los grises puros sobre
   marfil se ven sucios y no se usan.

## El color

Cada token tiene su `usage` en `tokens.json`; aquí va el criterio para elegir entre ellos.

- **Superficies**, de abajo arriba: `marfil` (lienzo) → `papel` (tarjeta, campo, hoja) → `papel-alto`
  (lo que flota). En claro, más alto es más claro. **En oscuro, más alto es más claro también**: ahí la
  sombra no se ve y la profundidad la da la superficie, que es como se comporta la luz de verdad.
- **Tinta**: `tinta` para texto y precio actual, `tinta-suave` para lo secundario (€/kg, cadena, fecha),
  `tinta-tenue` para 13 px o menos. Nunca un gris de una escala ajena.
- **Marca**: `verde` es el color de la cifra buena y del enlace. `verde-fuerte` es el verde prensado
  (botón al pulsar, texto de sello). `bosque` es la superficie oscura de marca: la barra de abajo y la
  tarjeta grande de la cesta. `terracota` es el segundo acento: destino activo y marca de la casa.
- **Rellenos de significado**: `lavado-verde`, `lavado-terracota`, `lavado-aviso`, `lavado-error`. Un
  lavado es un fondo, y encima lleva **tinta**, no el color puro de su familia.
- **Estados**: `bien` (bajada, ahorro), `aviso` (dato condicionado o incompleto) y `error` (subida,
  fallo de una acción). `bien` es un verde **azulado** a propósito: el par baja/sube no se distingue
  solo por el eje rojo–verde. **Y además nunca va solo de color**: toda bajada y toda subida llevan su
  palabra («baja», «sube») y su flecha. La separación luminosa entre `bien` y `error` es solo 1,02:1 en
  claro y 1,17:1 en oscuro, así que la forma y la palabra son obligatorias, no un extra.
- **Etiquetado**: `nutri-a` … `nutri-e` y su texto (`nutri-texto-a`, `nutri-texto-b-e`, `nutri-texto-e`).
  Es la escala oficial del Nutri-Score, igual en los dos temas, con dos correcciones medidas: la **E**
  se oscurece a `#cf3a0f` porque el naranja oficial daba 4,15:1 con blanco, y la **B** lleva texto
  oscuro porque el blanco sobre `#85bb2f` no llega a 4,5:1. Un producto sin Nutri-Score **no es una E**:
  se escribe «sin Nutri-Score» (ver «Estados»).
- **Sellos**: `sello-fondo` + `sello-tinta` (verde sobre lavado). Un sello es una afirmación del
  producto, no una decoración: si el dato falta, no se pinta el hueco.

### Contraste AA, medido

Medido con la fórmula de WCAG 2.1 (luminancia relativa y `(L1+0,05)/(L2+0,05)`), no estimado. Las
parejas de abajo son las que este sistema permite; **cualquier pareja nueva se mide antes de usarla**.
Mínimos: 4,5:1 para texto, 3:1 para texto ≥24 px, bordes de control, anillo de foco e iconos que
significan algo.

#### Tema claro

| pareja texto / fondo | medido | mínimo | pasa | para qué |
|---|---|---|---|---|
| `tinta` sobre `marfil` | 15,20:1 | 4,5:1 | sí | texto principal sobre el lienzo |
| `tinta` sobre `papel` | 15,88:1 | 4,5:1 | sí | texto principal sobre tarjeta |
| `tinta` sobre `papel-alto` | 16,27:1 | 4,5:1 | sí | texto principal sobre lo que flota |
| `tinta` sobre `lavado-verde` | 14,36:1 | 4,5:1 | sí | texto principal sobre fondo de ahorro |
| `tinta` sobre `lavado-terracota` | 13,96:1 | 4,5:1 | sí | texto principal sobre lavado de marca |
| `tinta` sobre `lavado-aviso` | 14,68:1 | 4,5:1 | sí | texto principal sobre lavado de aviso |
| `tinta` sobre `lavado-error` | 13,94:1 | 4,5:1 | sí | texto principal sobre lavado de error |
| `tinta-suave` sobre `marfil` | 7,16:1 | 4,5:1 | sí | texto secundario sobre el lienzo |
| `tinta-suave` sobre `papel` | 7,48:1 | 4,5:1 | sí | texto secundario sobre tarjeta |
| `tinta-suave` sobre `papel-alto` | 7,66:1 | 4,5:1 | sí | texto secundario sobre lo que flota |
| `tinta-suave` sobre `lavado-verde` | 6,76:1 | 4,5:1 | sí | texto secundario sobre ahorro |
| `tinta-suave` sobre `lavado-terracota` | 6,57:1 | 4,5:1 | sí | texto secundario sobre lavado de marca |
| `tinta-tenue` sobre `marfil` | 4,97:1 | 4,5:1 | sí | texto de 13 px sobre el lienzo |
| `tinta-tenue` sobre `papel` | 5,20:1 | 4,5:1 | sí | texto de 13 px sobre tarjeta |
| `verde` sobre `marfil` | 5,05:1 | 4,5:1 | sí | verde como texto sobre el lienzo |
| `verde` sobre `papel` | 5,27:1 | 4,5:1 | sí | verde como texto sobre tarjeta |
| `verde` sobre `papel-alto` | 5,40:1 | 4,5:1 | sí | verde como texto sobre lo que flota |
| `verde` sobre `lavado-verde` | 4,77:1 | 4,5:1 | sí | verde como texto sobre ahorro |
| `verde-fuerte` sobre `marfil` | 7,37:1 | 4,5:1 | sí | verde prensado sobre el lienzo |
| `verde-fuerte` sobre `lavado-verde` | 6,96:1 | 4,5:1 | sí | texto de sello sobre su fondo |
| `terracota` sobre `marfil` | 5,26:1 | 4,5:1 | sí | terracota como texto sobre el lienzo |
| `terracota` sobre `papel` | 5,50:1 | 4,5:1 | sí | terracota como texto sobre tarjeta |
| `terracota` sobre `lavado-terracota` | 4,83:1 | 4,5:1 | sí | terracota como texto sobre su lavado |
| `bien` sobre `marfil` | 5,98:1 | 4,5:1 | sí | bajada de precio sobre el lienzo |
| `bien` sobre `papel` | 6,25:1 | 4,5:1 | sí | bajada de precio sobre tarjeta |
| `bien` sobre `lavado-verde` | 5,65:1 | 4,5:1 | sí | bajada de precio sobre su lavado |
| `aviso` sobre `marfil` | 5,54:1 | 4,5:1 | sí | aviso sobre el lienzo |
| `aviso` sobre `papel` | 5,78:1 | 4,5:1 | sí | aviso sobre tarjeta |
| `aviso` sobre `lavado-aviso` | 5,35:1 | 4,5:1 | sí | aviso sobre su lavado |
| `error` sobre `marfil` | 6,11:1 | 4,5:1 | sí | subida y error sobre el lienzo |
| `error` sobre `papel` | 6,38:1 | 4,5:1 | sí | subida y error sobre tarjeta |
| `error` sobre `lavado-error` | 5,60:1 | 4,5:1 | sí | error sobre su lavado |
| `sobre-verde` sobre `verde` | 5,40:1 | 4,5:1 | sí | texto del botón de acción |
| `sobre-bosque` sobre `bosque` | 12,60:1 | 4,5:1 | sí | texto de la barra y de la tarjeta de la cesta |
| `sobre-terracota` sobre `terracota` | 5,63:1 | 4,5:1 | sí | texto del botón de marca |
| `sobre-lima` sobre `lima` | 11,20:1 | 4,5:1 | sí | texto de la insignia de ahorro |
| `nutri-texto-a` sobre `nutri-a` | 4,98:1 | 4,5:1 | sí | la letra A del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-b` | 7,09:1 | 4,5:1 | sí | la letra B del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-c` | 10,66:1 | 4,5:1 | sí | la letra C del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-d` | 6,09:1 | 4,5:1 | sí | la letra D del Nutri-Score |
| `nutri-texto-e` sobre `nutri-e` | 4,92:1 | 4,5:1 | sí | la letra E del Nutri-Score |
| `borde-fuerte` sobre `marfil` | 3,63:1 | 3:1 | sí | borde de control sobre el lienzo |
| `borde-fuerte` sobre `papel` | 3,80:1 | 3:1 | sí | borde de control sobre tarjeta |
| `verde` sobre `papel` | 5,27:1 | 3:1 | sí | anillo de foco sobre tarjeta |
| `verde` sobre `marfil` | 5,05:1 | 3:1 | sí | anillo de foco sobre el lienzo |
| `bien` sobre `papel` | 6,25:1 | 3:1 | sí | trazo de la gráfica de precio |

#### Tema oscuro

| pareja texto / fondo | medido | mínimo | pasa | para qué |
|---|---|---|---|---|
| `tinta` sobre `marfil` | 16,63:1 | 4,5:1 | sí | texto principal sobre el lienzo |
| `tinta` sobre `papel` | 15,07:1 | 4,5:1 | sí | texto principal sobre tarjeta |
| `tinta` sobre `papel-alto` | 13,21:1 | 4,5:1 | sí | texto principal sobre lo que flota |
| `tinta` sobre `lavado-verde` | 12,42:1 | 4,5:1 | sí | texto principal sobre fondo de ahorro |
| `tinta` sobre `lavado-terracota` | 13,24:1 | 4,5:1 | sí | texto principal sobre lavado de marca |
| `tinta` sobre `lavado-aviso` | 12,38:1 | 4,5:1 | sí | texto principal sobre lavado de aviso |
| `tinta` sobre `lavado-error` | 13,61:1 | 4,5:1 | sí | texto principal sobre lavado de error |
| `tinta-suave` sobre `marfil` | 9,96:1 | 4,5:1 | sí | texto secundario sobre el lienzo |
| `tinta-suave` sobre `papel` | 9,03:1 | 4,5:1 | sí | texto secundario sobre tarjeta |
| `tinta-suave` sobre `papel-alto` | 7,91:1 | 4,5:1 | sí | texto secundario sobre lo que flota |
| `tinta-suave` sobre `lavado-verde` | 7,44:1 | 4,5:1 | sí | texto secundario sobre ahorro |
| `tinta-suave` sobre `lavado-terracota` | 7,93:1 | 4,5:1 | sí | texto secundario sobre lavado de marca |
| `tinta-tenue` sobre `marfil` | 7,41:1 | 4,5:1 | sí | texto de 13 px sobre el lienzo |
| `tinta-tenue` sobre `papel` | 6,72:1 | 4,5:1 | sí | texto de 13 px sobre tarjeta |
| `verde` sobre `marfil` | 9,25:1 | 4,5:1 | sí | verde como texto sobre el lienzo |
| `verde` sobre `papel` | 8,38:1 | 4,5:1 | sí | verde como texto sobre tarjeta |
| `verde` sobre `papel-alto` | 7,34:1 | 4,5:1 | sí | verde como texto sobre lo que flota |
| `verde` sobre `lavado-verde` | 6,91:1 | 4,5:1 | sí | verde como texto sobre ahorro |
| `verde-fuerte` sobre `marfil` | 12,18:1 | 4,5:1 | sí | verde prensado sobre el lienzo |
| `verde-fuerte` sobre `lavado-verde` | 9,09:1 | 4,5:1 | sí | texto de sello sobre su fondo |
| `terracota` sobre `marfil` | 7,41:1 | 4,5:1 | sí | terracota como texto sobre el lienzo |
| `terracota` sobre `papel` | 6,71:1 | 4,5:1 | sí | terracota como texto sobre tarjeta |
| `terracota` sobre `lavado-terracota` | 5,90:1 | 4,5:1 | sí | terracota como texto sobre su lavado |
| `bien` sobre `marfil` | 9,27:1 | 4,5:1 | sí | bajada de precio sobre el lienzo |
| `bien` sobre `papel` | 8,40:1 | 4,5:1 | sí | bajada de precio sobre tarjeta |
| `bien` sobre `lavado-verde` | 6,92:1 | 4,5:1 | sí | bajada de precio sobre su lavado |
| `aviso` sobre `marfil` | 11,17:1 | 4,5:1 | sí | aviso sobre el lienzo |
| `aviso` sobre `papel` | 10,12:1 | 4,5:1 | sí | aviso sobre tarjeta |
| `aviso` sobre `lavado-aviso` | 8,31:1 | 4,5:1 | sí | aviso sobre su lavado |
| `error` sobre `marfil` | 7,94:1 | 4,5:1 | sí | subida y error sobre el lienzo |
| `error` sobre `papel` | 7,20:1 | 4,5:1 | sí | subida y error sobre tarjeta |
| `error` sobre `lavado-error` | 6,50:1 | 4,5:1 | sí | error sobre su lavado |
| `sobre-verde` sobre `verde` | 9,33:1 | 4,5:1 | sí | texto del botón de acción |
| `sobre-bosque` sobre `bosque` | 13,54:1 | 4,5:1 | sí | texto de la barra y de la tarjeta de la cesta |
| `sobre-terracota` sobre `terracota` | 7,31:1 | 4,5:1 | sí | texto del botón de marca |
| `sobre-lima` sobre `lima` | 11,20:1 | 4,5:1 | sí | texto de la insignia de ahorro |
| `nutri-texto-a` sobre `nutri-a` | 4,98:1 | 4,5:1 | sí | la letra A del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-b` | 7,09:1 | 4,5:1 | sí | la letra B del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-c` | 10,66:1 | 4,5:1 | sí | la letra C del Nutri-Score |
| `nutri-texto-b-e` sobre `nutri-d` | 6,09:1 | 4,5:1 | sí | la letra D del Nutri-Score |
| `nutri-texto-e` sobre `nutri-e` | 4,92:1 | 4,5:1 | sí | la letra E del Nutri-Score |
| `borde-fuerte` sobre `marfil` | 6,11:1 | 3:1 | sí | borde de control sobre el lienzo |
| `borde-fuerte` sobre `papel` | 5,53:1 | 3:1 | sí | borde de control sobre tarjeta |
| `verde` sobre `papel` | 8,38:1 | 3:1 | sí | anillo de foco sobre tarjeta |
| `verde` sobre `marfil` | 9,25:1 | 3:1 | sí | anillo de foco sobre el lienzo |
| `bien` sobre `papel` | 8,40:1 | 3:1 | sí | trazo de la gráfica de precio |

## La tipografía

Dos familias, con papeles que no se mezclan:

- **Fraunces 600** (`--font-display`, `fonts/Fraunces-600.woff2`): el título de la pantalla y el nombre
  de producto. Nada más. Es la voz de la casa, y pierde fuerza si se usa en todo.
- **IBM Plex Sans 400 y 600** (`--font-sans`, `fonts/IBMPlexSans-400-600.woff2`): todo lo demás, cifras
  incluidas. Se sirve en local: la primera pintada no depende de ninguna CDN.

Los pasos, y ninguno más (clases de `tokens.css`): `portada` 34/38 · `titulo` 24/29 · `subtitulo` 19/25 ·
`entrada` 17/26 · `cuerpo` 16/25 · `cuerpo-fuerte` 16/24 · `etiqueta` 13/18 · `etiqueta-fuerte` 13/18 ·
`micro` 12/16 en versalitas · y para precios `precio-grande` 30/34, `precio` 20/24, `precio-fila` 17/22.

- El interlineado va **pegado** al tamaño; un título de 34 px con el interlineado del cuerpo son dos
  líneas que se tocan.
- **Todo precio lleva `cifra`** (`font-variant-numeric: tabular-nums`). Sin eso, la columna de precios
  baila y comparar cuesta más.
- No se baja de 12 px, ni siquiera en el pie de una tarjeta. Por debajo, en el pasillo no se lee.
- El texto va en 16 px, no en 15: en el móvil se lee de pie y a un brazo de distancia.

## El espacio, el radio y la profundidad

- **Espacio**: 4, 8, 12, 16, 24, 32, 48 (`space-4` … `space-48`). Todo lo que se separa, se separa con
  uno de esos. Y `toque-minimo` = 44 px: es el alto mínimo de **cualquier cosa que se pulse** con el
  pulgar, incluido el enlace de texto dentro de una fila.
- **Radio**: `nota` 4 (una letra del Nutri-Score, una insignia dentro de una línea), `campo` 10 (botón,
  campo, chip), `tarjeta` 16 (una superficie con contenido), `hoja` 24 (lo que flota) y `pastilla` 999
  (solo lo que es una píldora de verdad: la insignia de ahorro, el punto de un aviso).
- **Profundidad**: `apoyado` para una tarjeta pulsable, `alzado` para lo que está en primer plano,
  `flotante` para lo que interrumpe. En claro las sombras son cálidas (llevan el marrón del papel). En
  oscuro la sombra no se ve: allí la profundidad la da `papel-alto`, y la sombra solo remata.
- **Móvil primero**: se compone a 390 px con margen de 16 px. Si algo no cabe a 390, no se encoge la
  letra: se quita de la fila o se pone debajo.

## El movimiento

Dos duraciones y una curva, y ninguna más:

- `duracion-rapida` = **120 ms** — lo que responde al dedo: hover, foco, pulsar un botón.
- `duracion-normal` = **220 ms** — lo que cambia de estado o entra en pantalla: una tarjeta, una hoja,
  el aviso de un precio.
- `curva-suave` = **cubic-bezier(0.2, 0, 0, 1)** — sale rápido y frena largo. Es la curva de «esto ya
  ha llegado».
- `quieto-por-ajuste` = **0,01 ms** — lo que dura todo cuando el sistema pide
  `prefers-reduced-motion: reduce`.

Reglas: el movimiento **explica**, no decora. Se anima `opacity` y `transform`, nunca `height`,
`width` ni `top` (obligan a recalcular en cada fotograma y en un móvil de gama baja se ven como un
tirón). Nada tarda más de 220 ms. Y `prefers-reduced-motion` **se resuelve en global**, en
`tokens.css`: no se repite por componente y no se deja nada moviéndose — quien activa el ajuste lo hace
porque el movimiento le hace daño o le marea, así que el error caro es dejar algo encendido.

> La página de este sistema **no pinta** la familia `movimiento`: la lee el código de la app, que es
> quien anima. Está en `tokens.json` para que las dos partes hablen de los mismos 120 y 220 ms.

## Los estados, que son parte del sistema

Toda pantalla de esta app tiene cuatro estados, y no se inventan por pantalla:

- **Vacío**: dice qué falta y cómo se llena, con una acción al lado. Nunca un hueco con un icono triste.
- **Cargando**: una barra fina o una tarjeta con la forma del contenido, con movimiento de 220 ms y
  apagado por `prefers-reduced-motion`. Texto corto: «buscando…».
- **Error de pantalla** (la consulta que llena la pantalla falló): un panel con título, frase y
  **«Volver a intentarlo»**, y va donde iría el contenido, porque no hay contenido.
- **Error de acción** (falló una operación concreta y el resto sigue en pie): **una línea**, en
  `lavado-error` con texto `error`, al lado de lo que se pulsó. **No** un panel de ancho completo: eso
  dice algo más grave de lo que pasa.
- **Sin permiso**: `lavado-aviso` con texto `aviso` y qué hacer para tenerlo. No se pinta un candado.

Y la regla de contenido que más se nota: **lo que no se sabe se dice**. Un dato que falta va como
«no lo sé», «sin Nutri-Score» o «—»; un hueco no se rellena con un cero, ni con una E, ni con un 0 %.

## Los componentes

- **`Precio`** — la cifra actual, el precio anterior tachado y el €/kg. El actual en `precio-grande` o
  `precio`, el anterior en `precio-antes` y el €/kg en `precio-unidad`. Una bajada va en `precio-baja`
  con flecha y palabra; una subida, en `precio-sube`. Si un dato falta, «—».
- **`ChipEtiqueta`** — la letra del Nutri-Score (`nutri-a` … `nutri-e`) y los sellos del producto
  (`sello-fondo` + `sello-tinta`). La letra va en un cuadrado de `radio-nota`; el sello, en una pastilla
  baja. Un producto sin dato dice «sin Nutri-Score», no pinta una letra gris.
- **`Tarjeta`** — la superficie de contenido: `papel`, `radio-tarjeta`, `space-16` de relleno, sombra
  `apoyado` si se puede pulsar. La variante `destacada` es `bosque` con texto `sobre-bosque`; ahí va el
  dato que hay que ver primero.
- **`FilaComparacion`** — una cadena en una línea: nombre, precio actual, €/kg y cuál es la mejor. La
  mejor fila lleva `lavado-verde`, texto `verde` y la palabra «la más barata»: **el color solo no
  basta**. Alto mínimo 44 px, un `<a>` o un `<button>` real, nunca un `div` clicable.
- **`Boton`** — `primario` (relleno `verde`, texto `sobre-verde`), `secundario` (`papel` con borde
  `borde-fuerte`), `fantasma` (sin fondo, texto `verde`). Alto 44 px, `radio-campo`, transición de
  120 ms en el fondo y en la sombra. El foco es un anillo de 2 px en `verde`.

Este sistema **no trae bundle de JavaScript**: cada componente es una pieza de HTML y CSS, y su
contrato son las clases de `tokens.css` (`precio-grande`, `cuerpo-fuerte`, `micro`…) y las variables
(`--tinta`, `--radio-tarjeta`, `--space-16`). Se consume copiando `tokens.css` y los dos `.woff2`, o
traduciendo los tokens a lo que use la app (en este proyecto, Tailwind: cada token es una extensión con
nombre, nunca un número suelto en una pantalla).

## La iconografía

Iconos **SVG en línea**, de trazo, nunca emoji: `viewBox="0 0 24 24"`, `stroke="currentColor"`,
grosor 1,8, extremos redondeados, 20 px de tamaño (22 px en la barra de abajo). Heredan el color de su
texto, así que un icono activo es `terracota` y uno en reposo `tinta-suave` sin más.

Los iconos de este proyecto están dibujados a mano en `plataforma/web/app/src/componentes/iconos.tsx`
(casa, carro, corazón, código de barras, lupa). Al añadir uno, se copia ese estilo. Todo icono va con
`aria-hidden="true"`: el nombre lo lleva el botón, que es lo que lee un lector de pantalla. Un icono
suelto no significa nada.

## Las palabras

- Español de España, en segunda persona y en minúscula: «tu cesta», «lo más barato».
- Se dice **«la más barata»**, no «la mejor»: en esta app, «mejor» es una afirmación sobre calidad.
- Las cifras, con coma y su espacio: «1,99 €/kg», «−0,40 €», «+6,3 %». El signo menos es «−» (−), no un
  guion.
- Nada de signos de exclamación, de mayúsculas a gritos ni de emoji en la interfaz.
- Una frase que no se puede sostener con un dato no se escribe. Si falta, se dice que falta.
