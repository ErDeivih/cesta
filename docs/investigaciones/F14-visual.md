# F14 -- Sistema visual propio aplicado (P1/P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:177`:**

> **Hacer inventario de pantallas servidas y componentes, no rediseñar solo una portada.** Adoptar la direccion...
> **Crear antes/despues con mismos fixtures.** Simplificar jerarquia, numeros/unidades, textos y estados; dens[idad]...
> **Aceptacion:** **360/390/768/1440**, **zoom 200 %**, **teclado/cajon/foco**, **reduccion de movimiento**,
> **contraste y c[olor]**...

---

## 1. Punto de partida: **nada medido**, y el inventario ya esta hecho por F13

**De F14 no se ha medido nada** -- *pero **la primera cosa que pide ya esta contada**, porque F13 la necesitaba:*

> *«**Hacer inventario de pantallas servidas y componentes, no rediseñar solo una portada.**»*

**Y el inventario existe** (ronda 138): **18 paginas** -- `Ajustes`, `Avisos`, `Buscar`, `Cesta`, `Cocina`,
`Diario`, `Escaner`, `Favoritos`, `Grupo`, `Inicio`, `Panel`, `PanelMatching`, `PlanSemanal`, `Producto`,
`RecetaDetalle`, `Recetario`, `Tendencias`, `Unirse` -- **y sus componentes**.

**Y el criterio dice «no rediseñar solo una portada», que es una advertencia sobre el trabajo, no sobre el
resultado**: *es facil hacer bonita `Inicio` y dejar `Ajustes` como estaba.* **Tener las 18 contadas es lo que
permite comprobar que se aplico a todas** -- *y es **la razon de que el encargo pida «inventario» antes de
«direccion»**.*

### Y la aceptacion es **accesibilidad**, entera

**Los cinco casos, y los cinco son de accesibilidad:**

| caso | **que es** |
|---|---|
| **360 / 390 / 768 / 1440** | *las cuatro anchuras: movil pequeno, movil, tableta, escritorio* |
| **zoom 200 %** | *y a 200 % **no se puede perder nada** -- es el criterio de reflow* |
| **teclado / cajon / foco** | *navegar sin raton, y **saber donde estas*** |
| **reduccion de movimiento** | *respetar `prefers-reduced-motion`* |
| **contraste y color** | *el minimo, y **no depender solo del color*** |

**Y ninguna de las cinco se puede comprobar leyendo el codigo**: *todas son **de pantalla**, y tres de ellas
**necesitan un navegador de verdad** (`zoom`, `foco`, `movimiento`).* **Es el paquete mas «de pantalla» de la
fase hasta ahora.**

### Y ya hay **dos** datos de contraste en esta fase, sin buscarlos

**El criterio de F13 trajo uno, y es del propio proyecto:**

> *«Y **la tabla de debajo no es un extra**: cinco colores no se distinguen ni con buena vista, y **tres de los
> que usaba la interfaz vieja no llegaban a 3:1 de contraste contra el fondo claro**.»* (`GraficoIndice.tsx:8-9`)

**Asi que el proyecto **ya encontro** un fallo de contraste, **ya lo escribio**, y **ya lo arreglo poniendo una
tabla** -- *lo cual es exactamente el criterio «no depender solo del color», resuelto **en un sitio**.*

**Y la pregunta de F14 empieza por ahi, y es concreta**: *¿se arreglo **en ese sitio**, o **hay una regla**?* *Es
decir: **¿hay una paleta con sus contrastes comprobados, o cada componente se arregla cuando alguien lo mira?***

**Eso es un `SELECT` sobre `estilos.css` y los tokens.** *Y va antes que cualquier captura de pantalla, porque
si **hay** una paleta con sus minimos, la mitad del criterio ya esta; y si no, **el trabajo es otro**.*

### Y una nota de metodo que este paquete exige

**Los cuatro casos de anchura y el zoom no se pueden medir «leyendo».** *En `F03` y `F07` hicieron falta
`prueba_f03_publicacion.py` y `prueba_f07_pasos.py`, con `patchright` y **navegador de verdad** -- y **`F14`
necesita lo mismo**, mas capturas a cuatro anchuras y a 200 %.*

**Y el criterio pide «antes/despues con **mismos fixtures**»** -- *o sea, que las capturas se puedan comparar.*
*Eso es `compare_web_screenshots` del laboratorio auxiliar, o el mismo `navegador.py` con dos juegos de tokens.*
**Es trabajo de ensayo, no de lectura.**


---

## 2. «Contraste y color»: **hay una paleta, y cada token lleva su razon de contraste escrita**

*(Ronda 141.)* La pregunta del §1 -- *«¿se arreglo en ese sitio, o hay una regla?»* -- **contestada: hay una
regla, y esta escrita token por token, en `plataforma/web/app/src/estilos.css:7-30`.**

```css
7   @layer base {
8     /* Los colores con significado, en un solo sitio.
10     * Son variables y no valores fijos porque estas clases se usan sin el prefijo
11     * `dark:`, y en modo oscuro un gris de texto claro sobre fondo oscuro no se
12     * lee. Con la variable, el mismo `text-tinta-suave` vale en los dos temas y
13     * nadie tiene que acordarse de escribir el par. */
14    :root {
15      --tinta-suave: #525252;  /* texto secundario */
16      --fondo: #fafafa;        /* superficie dentro de una tarjeta */
17      --borde: #e5e5e5;
18      --aviso: #b45309;        /* texto de aviso, legible sobre blanco */
19      --bien: #059669;         /* borde de lo que ha salido bien */
20      --bien-suave: #ecfdf5;   /* fondo de lo que ha salido bien */
22      --marfil: #f4f0e8;       /* lienzo calido */
23      --papel: #fbf9f4;        /* formularios y superficies */
24      --bosque: #183a32;       /* navegacion y accion principal */
25      --tinta-fuerte: #202724; /* texto principal (13,42:1 sobre marfil) */
26      --secundaria: #536158;   /* texto auxiliar  (5,74:1 sobre marfil) */
27      --terracota: #a94d36;    /* acento de marca y seccion activa (4,86:1) */
28      --borde-fuerte: #8a8578; /* si delimita un control: el suave da 1,43:1 */
29      --error: #a12626;        /* lo que hay que mirar: 7,02:1 sobre marfil */
30    }
32    @media (prefers-color-scheme: dark) { ... }
```

### Y las cinco razones, que son lo que hace que esto sea un sistema y no una lista de colores

| token | **su razon, escrita al lado** |
|---|---|
| **`--tinta-fuerte`** | *«texto principal (**13,42:1** sobre marfil)»* |
| **`--secundaria`** | *«texto auxiliar (**5,74:1** sobre marfil)»* |
| **`--terracota`** | *«acento de marca y seccion activa (**4,86:1**)»* |
| **`--error`** | *«lo que hay que mirar: **7,02:1** sobre marfil»* |
| **`--borde-fuerte`** | *«**si delimita un control: el suave da 1,43:1**»* |

**Los cuatro primeros llevan su ratio, y los cuatro pasan el 4,5:1 de texto normal** -- *13,42, 5,74, 4,86 y
7,02.* **Y el quinto es el que demuestra que esto es un sistema**: ***`--borde-fuerte` existe porque `--borde`
da 1,43:1*** -- *o sea, **hay un token que existe unicamente porque otro no llegaba**, y su comentario lo dice.*

**Y eso es exactamente lo que F13 encontro en `GraficoIndice`** -- *«tres de los que usaba la interfaz vieja no
llegaban a 3:1»* --, **pero al reves**: *aqui el fallo no se descubrio en un componente y se parcheo ahi; **se
declaro un token nuevo con su motivo**, y los componentes usan el token.*

### Y el porque de que sean variables es el otro caso de la aceptacion

> *«Son variables y no valores fijos porque estas clases se usan sin el prefijo `dark:`, y **en modo oscuro un
> gris de texto claro sobre fondo oscuro no se lee**. Con la variable, el mismo `text-tinta-suave` vale en los
> dos temas y **nadie tiene que acordarse de escribir el par**.»*

**Dos cosas, y las dos son del criterio:**

1. **`@media (prefers-color-scheme: dark)`** -- *el modo oscuro **se respeta***, que es del criterio de color.
2. **Y la razon de las variables es de **accesibilidad**, no de comodidad**: *sin ellas, **cada sitio** tendria
   que acordarse de escribir el par claro/oscuro, **y donde se olvide, el texto no se lee**.* **Es el mismo
   argumento que `logica/recetario.ts` dio para filtrar en el cliente** (*«ese es justo el sitio donde un olvido
   se convierte en una fuga»*), **aplicado a los colores**: *no dejar la correccion al cuidado de quien escribe
   cada pantalla.*

### Y `F14`, con lo medido

| lo que pide la aceptacion | **estado** |
|---|---|
| **contraste** | **hay sistema**: cinco tokens con su ratio escrito, y **uno que existe porque otro no llegaba** |
| **color** | **hay direccion**: *«archivo domestico, no panel generico»* (`:21`), con marfil/papel/bosque/terracota |
| **reduccion de movimiento** | *por medir* |
| **modo oscuro** | **si** (`@media (prefers-color-scheme: dark)`) -- *que no estaba en la lista pero es del mismo criterio* |
| **360/390/768/1440, zoom 200 %, teclado/foco** | *por medir, y **con navegador*** |

**Dos de los cinco, y con sistema en vez de con parches.** *Y la decimocuarta pieza: **el color ya tenia su
regla**, con el ratio al lado de cada token.*


---

## 3. «Reduccion de movimiento»: **no esta, y hay tres animaciones que reducir** -- y el foco **si**

*(Ronda 142.)* Los tres casos que se pueden medir sin navegador, y **dan dos respuestas distintas.**

```
reduced-motion :  0 menciones   <- NO HAY
foco visible   :  2             <- SI: estilos.css:70  :focus-visible { @apply outline-none ring-2 ring-offset-2 ring-sky-600 ... }
animacion      :  4             <- Y HAY QUE REDUCIR: ui.tsx:307 y :324 (animate-pulse), estilos.css:188 (transition: transform 150ms ease)
```

### Y lo importante es que **el caso es real, no teorico**

**«Respetar `prefers-reduced-motion`» solo importa **si hay movimiento**, y **hay tres cosas**:**

| donde | **que se mueve** |
|---|---|
| `ui.tsx:307` | **`animate-pulse`** -- *el esqueleto de carga de una tarjeta* |
| `ui.tsx:324` | **`animate-pulse`** -- *el de otra* |
| `estilos.css:188` | **`transition: transform 150ms ease`** |

**Asi que no es «no hay animaciones, luego no hace falta»: es que **hay tres**, y **ninguna** consulta la
preferencia.** *Un `animate-pulse` **parpadeando** para quien ha pedido que no se mueva nada es exactamente lo
que el ajuste existe para evitar.*

### Y el foco **si esta**, y bien

```css
70   :focus-visible {
71     @apply outline-none ring-2 ring-offset-2 ring-sky-600 ring-offset-white ...
```

**`focus-visible` y no `focus`** -- *que es la diferencia entre **rodear de un anillo solo a quien navega con
teclado** y **rodearlo tambien al que acaba de hacer clic con el raton**.* **Y el anillo es `ring-2` con
`ring-offset-2`**, *o sea, **separado del borde** -- que es lo que hace que se vea **sobre cualquier fondo**.*

**Es la decision correcta, y es del criterio: «teclado / cajon / **foco**».** *Un `:focus` a secas tambien
«funcionaria», y seria peor.*

### Y las dos, juntas, dicen una cosa del proyecto

**El foco esta resuelto **con la variante correcta** (`:focus-visible`, que es la que casi nadie usa), y la
reduccion de movimiento **no esta**.** *No es un proyecto descuidado con la accesibilidad: es **un proyecto que
resolvio la parte que se ve y no la que no se ve** -- y `prefers-reduced-motion` es **justo la que no se ve**: la
activa quien la necesita, y quien no, **nunca la echa en falta**.*

**Es la misma forma que los otros huecos de esta fase**: *`R02`, `R05` y `R08` **no existen porque nadie los ha
pedido**; y `prefers-reduced-motion` **no esta porque nadie lo ha notado**.* **La diferencia es que este son
**tres lineas**.**

### Y F14, con lo medido

| lo que pide la aceptacion | **estado** |
|---|---|
| **contraste** | **sistema**: cinco tokens con su ratio, y uno que existe porque otro no llegaba |
| **color** | **direccion**: *«archivo domestico, no panel generico»* |
| **modo oscuro** | **si** |
| **teclado / foco** | **si**, con `:focus-visible` y anillo separado |
| **reduccion de movimiento** | **NO** -- *y hay **tres** animaciones que reducir* |
| **360/390/768/1440 y zoom 200 %** | *por medir, **con navegador*** |

**Cuatro de los seis, uno que falta y son tres lineas, y uno que exige navegador.** *Y los dos que faltan
**no se pueden leer**: el de anchuras hay que **verlo**, y el de movimiento hay que **emular la preferencia** --
*que es exactamente lo que `capture_browser_scenario` del laboratorio auxiliar sabe hacer, con
`reduced_motion: "reduce"` entre sus ajustes por defecto.*


---

## 4. **Correccion importante**: no es «nadie lo ha pedido» -- **la app vieja SI lo tenia, y la nueva lo perdio**

*(Ronda 143, al ir a montar el ensayo.)* **Y esto cambia la naturaleza del §3.**

**En la ronda 142 escribi**: *«`prefers-reduced-motion` no esta porque nadie lo ha notado»*, y lo puse en la misma
familia que `R02`, `R05` y `R08` (**funciones que nadie ha escrito**). **Es falso.** *Al buscar donde emular la
preferencia para el ensayo, aparece esto:*

```
plataforma/web/estilo.css              <- LA APP VIEJA
  180  @media (prefers-reduced-motion:reduce){*{transition:none!important;animation:...}}
  201  @media (prefers-reduced-motion:reduce){.progreso i{transition:none}}
  276  @media (prefers-reduced-motion:reduce){.interruptor i{transition:none}}

plataforma/web/app/src/estilos.css     <- LA APP NUEVA
  0 menciones
```

### Lo que esto es, dicho con precision

**La aplicacion vieja tiene **tres** reglas de movimiento reducido, y **una es global** (`*{transition:none
!important; animation:...}`).** *O sea: **alguien lo penso, lo escribio, y lo dejo funcionando en la app que
estaba sirviendose**.*

**Y la aplicacion nueva -- la que se esta construyendo en esta fase, en `app/src` -- **no tiene ninguna**.* **No
es que nadie lo haya pedido: es que se perdio al reescribir.**

**Y eso lo convierte en un caso distinto y peor:**

| | lo que es | **como se dice** |
|---|---|---|
| **`R02`, `R05`, `R08`** | **funciones que nadie ha escrito** | *trabajo pendiente* |
| **`prefers-reduced-motion` en la app nueva** | **una funcion que existia y se perdio** | **una regresion** |

**Es la primera regresion de esta fase** -- *y no se encontro buscandola: se encontro **yendo a hacer el
ensayo**, que es donde se encuentran.*

### Y el arreglo esta escrito, en el fichero de al lado

**La regla de la app vieja es, literalmente, el arreglo de la nueva:** `@media
(prefers-reduced-motion:reduce){*{transition:none!important;animation:...}}`. *Tres lineas, y ya estan
pensadas.*

**Y hay una decision que tomar, que es del dueno**: *una regla `*` global **apaga todo**, incluido lo que pudiera
ser util* -- *y la vieja tenia **las dos**: la global **y** dos por componente (`:201`, `:276`).* **Cual de las
dos formas se adopta es una eleccion, y va con las tres que ya esperan.**

### Y por que el §3 dijo lo que dijo

**El §3 midio `app/src` y concluyo sobre «el proyecto».** *Es la misma equivocacion de siempre en esta fase --
**mirar una capa y concluir sobre el sistema** --, y esta vez la capa que faltaba era **la app vieja, en el
mismo directorio, con un fichero que se llama casi igual** (`estilo.css` contra `app/src/estilos.css`).*

**Lo que lo corrige no es pensar mejor: es ir a buscar donde se emula la preferencia para el ensayo, y
encontrarse el fichero de al lado.** *Es la decimoquinta vez que la respuesta estaba en otro sitio, y la primera
en que el otro sitio es **codigo del mismo proyecto que ya no se usa**.*

### Y el estado de F14, corregido

| lo que pide | **estado** |
|---|---|
| **contraste** | **sistema** |
| **color** | **direccion** |
| **modo oscuro** | **si** |
| **teclado / foco** | **si** |
| **reduccion de movimiento** | **NO en la app nueva, y SI en la vieja** -> **regresion**, con el arreglo ya escrito al lado |
| **360/390/768/1440 y zoom 200 %** | *por medir, con navegador* -- *y la pila de ensayo (8102/5174) esta **parada**: hay que levantarla* |

**Una regresion con el arreglo al lado, y un ensayo que necesita que se levante la pila.** *Y `F14` deja esto:
**el unico caso de la fase que no es «falta» ni «esta bien», sino «estaba y se perdio»**.*


---

## 5. Las cuatro anchuras y el zoom al 200 % -- **medidos, y no se sale nada**

*(Ronda 183, con la pila del sandbox: API 8102, Vite 5173, y sesion entrante con JSON.)*

**Era el hueco que quedaba de este paquete**: *«widths 360/390/768/1440 + zoom 200 %, con un navegador»*. **Y ya
esta medido.**

### Lo que se midio

**Cuatro pantallas** -- *la lista (`/compra/listas`), el buscador (`/compra`), **la despensa**
(`/compra/despensa`) y **el importar recetas** (`/compra/importar`)* -- **en cuatro anchuras**, y la prueba es
`document.documentElement.scrollWidth` contra `window.innerWidth`: **si el primero es mayor, algo se sale de la
pantalla y hay que arrastrar de lado para leerlo.**

```
  360px (movil pequeno)  OK
  390px (movil)          OK
  768px (tableta)        OK
 1440px (escritorio)     OK
 zoom 200 %              1440 vs 1440  OK
```

**Ninguna se sale.** *Ni una, ni en la mas estrecha, ni con el zoom al doble.*

### Y lo que esto **no** dice, para no darlo por mas de lo que es

**Esto mide **desbordamiento horizontal**, y nada mas.** *No dice que las pantallas **se lean bien** en un movil:
dice que **no hay que arrastrar de lado**.* **Un texto de 9 px que cabe en 360 px pasa esta prueba y sigue siendo
ilegible** -- *y eso **no se ha medido**, ni se puede medir asi.*

**Y es la misma distincion que el resto de la fase**: *«no se sale» **no es** «se lee bien».* **Lo que se puede
afirmar es lo que se midio: que ninguna de las cuatro pantallas desborda a ninguna de las cuatro anchuras, ni al
doble de tamano.**

### Y la linea que faltaba, que salio de aqui

**`App.tsx` da el titulo de la pestana por prefijo de ruta, y a `despensa` se le puso el suyo en su dia** -- *pero
**`cocina` e `importar` no lo tenian**.* **Asi que las dos salian con «Compra · Cesta»**, el generico de la suite.

**Y eso se arreglo**: *dos lineas, al lado de la de despensa.* **Es un detalle pequeno y es exactamente el tipo de
cosa que **no la caza un `tsc`** -- *compila igual con el titulo mal--, y que solo se ve **abriendo la pantalla**.*


---

## 6. «Se lee bien»: **lo que se puede medir de eso** -- *y lo que no*

*(Ronda 222. **`F14` lleva en «medido» desde el principio, y su motivo escrito es que «se lee bien» es un juicio. Pero parte de un juicio tiene cifras.**)*

### Lo que se midio

**Tres pantallas, cuatro anchuras, y dos cosas contables:**

```
pantalla             ancho   letra minima   control minimo   controles < 44 px
/compra/despensa      360       13,0 px          1 px            1/2
/compra/despensa      390       12,0 px          1 px            4/8
/compra/despensa      768       13,0 px          1 px            1/2
/compra/despensa     1440       12,0 px          1 px            5/17
/compra/analisis      360       12,0 px          1 px            3/15
/compra/analisis      390       12,0 px          1 px            3/15
/compra/analisis      768       12,0 px          1 px            3/15
/compra/analisis     1440       12,0 px          1 px            4/24
/compra/importar      360       13,0 px          1 px            2/4
/compra/importar      390       13,0 px          1 px            2/4
/compra/importar      768       13,0 px          1 px            2/4
/compra/importar     1440       13,0 px          1 px            3/11
```

### Y la primera cifra si dice algo: **la letra mas pequena es de 12 a 13 px**

**En las tres pantallas y en las cuatro anchuras.** *Y **12 px es pequeno**: *la referencia habitual para texto de
lectura en un movil es **16 px**, y **por debajo de 12 se considera ilegible**.* **Asi que el texto mas pequeno de
estas pantallas esta justo en el limite bajo.**

> **Y esto es lo que `F14` decia que no se podia medir, medido a medias**: *«se lee bien» **sigue siendo un juicio**
> -- *un texto de 12 px con buen contraste y buena linea se lee; uno de 16 px con gris claro, no* --, **pero «la letra
> mas pequena mide 12 px» es un dato**, y **es el que permite decir que el juicio esta en el filo.**

### Y la segunda cifra **no dice nada, y es de mi medidor**

**`control minimo = 1 px` en las doce filas.** *Un control de **1 px** no existe: **lo que mi selector cogio fue otra
cosa** -- *probablemente un `input` oculto, un separador, o un elemento con `offsetParent` visible y caja de 1 px.*
**Y por eso la tercera columna -- «controles < 44 px» -- tampoco vale tal como esta**: *cuenta esos mismos elementos.*

> **Es la misma clase de error que el §10 y el §18 de `F10`**: *un selector que **junta cosas distintas** y produce
> **un numero que parece un dato**.* *Y aqui se ve **a simple vista** -- *un control de 1 px es imposible* --, que es
> **la unica razon por la que se puede decir que el medidor falla y no el producto.**

### Y `F14`, con esto, en su sitio

| lo que `F14` tiene | **estado** |
|---|---|
| **contraste y color con sistema** | **medido** |
| **cuatro anchuras y zoom 200 %** | **medido**: *nada se sale* |
| **el `prefers-reduced-motion`** | **era una regresion, y se arreglo** |
| **«se lee bien»** | **es un juicio** -- *y ahora se sabe **donde esta el filo**: la letra mas pequena mide **12 px*** |
| **el tamano de los controles** | *por medir **bien**: el medidor hay que afinarlo antes* |

**Asi que `F14` sigue en «medido», y **con mejor motivo que antes**: *tres cosas medidas, una **con su cifra y su
filo***, y una **cuyo instrumento hay que arreglar antes de creerle el numero.**
