# 12 · Medir sin engañarse: los instrumentos que mienten

Este es el capítulo más importante del material y el que no está en ningún tutorial: **cómo saber
que tu medida está mal**. Un proyecto de datos no falla por no saber PySpark; falla por dar por
buena una cifra que medía otra cosa. Aquí hay diecisiete casos reales de este proyecto, agrupados
por el tipo de mentira, y cada uno con la señal que lo delata.

## 1. El instrumento mide el andamio, no la aplicación

**El caso.** La verificación de punta a punta medía «abrir la pantalla de avisos: 469 ms». Un
endpoint que **no hace nada** tardaba 409 ms en la misma prueba: los 469 ms eran el andamio
(httpx en el mismo proceso) midiéndose a sí mismo. La aplicación tardaba 47 ms en frío y 9-16 ms
en caliente.

**La señal.** Una cifra sospechosamente redonda y **el mismo orden de magnitud para cosas muy
distintas**. Si un endpoint trivial y uno complejo tardan parecido, estás midiendo el andamio.

**El arreglo.** Imprimir las dos cosas por separado (andamio y aplicación) y repetir la medida
cuatro veces.

## 2. El instrumento mira el objeto equivocado

**Los casos.** Tres en este proyecto, y los tres pasaron la prueba con el sistema bien o mal
indistintamente:

- **La prueba del sitio de documentación** miraba los objetos que el conversor deja en memoria;
  `recoge()` devuelve páginas **sin pintar** y las pinta `genera()` sobre otras. Las pruebas
  fallaban con el sitio bien y habrían pasado con el sitio roto.
- **La medida de la chapa de la barra** leía `innerText` del enlace, que **pega la cifra a la
  etiqueta**: leía `22` donde había un `2`. Había que leer el `span` con `aria-hidden`.
- **La medida de contraste** resolvía el fondo del elemento… y no miraba nada más: pasaba sin
  comprobar nada cuando el elemento no estaba pintado. Se arregló midiendo el texto **ya pintado,
  en los dos temas**, y con una trampa (un texto ilegible puesto a mano) para demostrar que la
  medida mira.

**La señal.** Una prueba que **nunca ha fallado** y una medida que no cambia cuando cambias el
sistema.

**El arreglo.** Una **trampa**: poner a mano un caso que tiene que fallar. Si la trampa no falla,
el instrumento no está mirando. Este proyecto tiene trampas en el contraste, en los porcentajes
imposibles, en los documentos mal codificados y en el número de la barra.

## 3. El instrumento lee antes de que el sistema se estabilice

**El caso.** Al abrir una pantalla con la API caída, la medida leía «Cargando…»: React Query
**reintenta** antes de darse por vencida (y hace bien: un 500 de un segundo no es un fallo). La
prueba leía el estado intermedio.

**La señal.** Un resultado distinto cada vez, o un texto de estado (`Cargando…`, `Entrando…`) en
la salida de una medida.

**El arreglo.** Esperar al **estado final observable** (el botón «Volver a intentarlo»), no a un
número de milisegundos.

## 4. El filtro que no filtra

**El caso.** La prueba de «cuando la API falla» interceptaba `**/api/alertas*` para devolver un
500. Ese patrón cogía también **`/src/api/alertas.ts`**, el módulo del front: el navegador recibía
un 500 por un módulo, la aplicación **no llegaba a montarse** y la pantalla salía en blanco. La
conclusión que se estaba a punto de escribir —«un 500 en los avisos deja la aplicación en blanco»—
era falsa: lo que pasaba es que no había aplicación.

**La señal.** El fallo aparece **en todas** las pantallas, no solo en la que estás probando.

**El arreglo.** Un filtro que mira **la ruta después del host**: `/api/...` es la API, `/src/...`
es el front, y no se pueden confundir.

**Y el mismo tipo de fallo, con `unroute`:** quitar una intercepción con una **función nueva** no la
quita (hay que pasar el mismo objeto), así que el 500 se quedaba puesto para el resto de la prueba.
La señal: **el siguiente caso también falla**, sin relación aparente.

## 5. Los ficheros de configuración, que no los mira nadie

**Los casos.** Tres, y los tres son la misma clase: el código está bien y **el despliegue está
roto**.

- **La interfaz servida era la vieja.** `docker-compose.yml` montaba una carpeta y el `dist`
  compilado estaba en otra. Caddy servía un `index.html` que existía, el navegador cargaba… y
  salía la interfaz antigua, **sin ningún error**. Se arregló con una prueba que lee **los dos**
  ficheros y comprueba que dicen lo mismo.
- **El contenedor no arrancaba por un montaje anidado.** El material de aprendizaje se montó en
  `/srv/aprende`, dentro de `/srv`, que ya estaba montado de **solo lectura**: Docker no puede
  crear el punto de montaje y el contenedor muere con `read-only file system`. No es código; se ve
  en `docker compose ps`.
- **El CSP mató el buscador.** El sitio de documentación funcionaba en local y en producción tenía
  el buscador muerto: Caddy sirve con `script-src 'self'` y el buscador iba en un `<script>`
  incrustado, que **no se ejecuta** y no da error visible. Se arregló moviéndolo a un fichero, y
  ahora hay una prueba que vigila que no vuelva a haber scripts en línea.

**La señal.** «En mi máquina funciona». Todo lo que solo se comprueba en el servidor de desarrollo
está sin comprobar.

**El arreglo.** Una comprobación **de lo que se sirve** (`plataforma/prueba_produccion.py`), no de
lo que se desarrolla.

## 6. La prueba que pasa y el sistema que falla

**El caso.** `tests/test_imagen_api.py` comprueba que la API no importe `polars` (que no está en su
imagen) y pasó. Pero alguien necesitaba una constante de un módulo que sí usa polars y la importó
**dentro de la función** que la usaba, que es lo que el propio mensaje de la prueba recomendaba.
La prueba estática mira solo los imports de arriba: no lo vio. La puerta del navegador tampoco,
porque corría contra el servidor local, **donde polars sí está**. En el contenedor:

    ModuleNotFoundError: No module named 'polars'
    GET /api/ofertas-dudosas 500 Internal Server Error

**La señal.** Un `TODO BIEN` en desarrollo con producción rota.

**El arreglo.** Dos cosas: la constante se mudó a un módulo que la API sí puede importar, y la
prueba ahora mira **todos** los imports, estén donde estén. Un import perezoso no es una excusa:
si la función se llama, el fallo es de producción.

## 7. Comparar dos cosas que no son la misma

**El caso.** Para comprobar el sesgo de encadenamiento del índice, la primera versión comparó el
índice encadenado con un «directo» calculado **sin recorte** y **con su propio SQL**: daba +8,2
puntos en Alcampo. La conclusión aparente —«hay un sesgo enorme»— era falsa. Repetido con el SQL
de la aplicación y el mismo recorte, el sesgo es **0,38 puntos**.

**La señal.** Una diferencia **demasiado grande** para el fenómeno que estás midiendo.

**El arreglo.** Los dos números tienen que salir del mismo filtro, la misma definición de par y el
mismo recorte. Si no, no estás midiendo el fenómeno: estás midiendo tu implementación.

## 8. Los datos cambian y tu instrumento no lo espera

**Los casos.** Dos, y son el pan de cada día en automatización:

- La prueba de punta a punta elegía un grupo **sin desempate** (`ORDER BY cadenas DESC`): con
  empate, la base devolvía cualquiera, y algunas noches elegía un grupo cuyo precio no estaba en su
  mínimo. La prueba se ponía roja **sola**.
- La comprobación de «tachar» en producción pulsaba la **primera** casilla de la lista. Si la
  cuenta venía de una pasada anterior con cosas ya tachadas, pulsarla **destacha**, y la
  comprobación fallaba con la aplicación bien.

**La señal.** Una prueba que falla de forma intermitente, o que falla «sola» después de un día
bueno.

**El arreglo.** Elecciones **deterministas** (con desempate explícito) y comprobaciones que
**preparan el estado** que necesitan en vez de suponerlo.

## 9. La medida que se mide a sí misma (el meta-caso)

En tres capítulos de este material aparece la misma frase: *«y el primer intento de medirlo estaba
mal»*. No es un accidente: es la propiedad más importante de un instrumento — **también hay que
auditarlo a él**. Las preguntas que lo hacen:

    ¿este numero cambia si cambio el sistema?     si no cambia, no lo estas midiendo
    ¿hay una trampa que tiene que fallar?         si no falla, el instrumento no mira
    ¿de donde sale exactamente este numero?       un comando, no un recuerdo
    ¿lo he medido en el sitio donde importa?      desarrollo no es produccion
    ¿estoy comparando lo mismo dos veces?         mismo filtro, misma definicion
    ¿el sistema estaba en el estado final?        no leas «Cargando…»

## 10. Lo que se aprende en este capítulo

- **Una medida que nunca ha fallado no es una buena medida: es una medida sin trampa.**
- Todo lo que se comprueba solo en desarrollo está sin comprobar: producción tiene CSP, contenedores,
  volúmenes y rutas que el portátil no tiene.
- Un import perezoso, un filtro demasiado ancho o un `unroute` mal hecho no dan error: dan
  resultados falsos con aspecto de buenos.
- Cuando un número sale **demasiado grande**, sospecha del instrumento antes que del mundo.
- Y la conclusión práctica: cada vez que se arregla un instrumento en este proyecto, se escribe
  **por qué mentía** —en el código, no en un correo— para que el siguiente no lo repita. Ese
  registro es, en sí mismo, el activo más valioso del repositorio.
