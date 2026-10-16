# Dictamen, *separado por uso*

*15/10/2026. *Punto 8 del encargo de validacion: *** un dictamen para uso domestico y
otro para despliegue publico, *con evidencias y bloqueos concretos.*** *

*** La regla de este documento ***: *cada afirmacion lleva **su evidencia**, *y lo que
**no** esta verificado se dice *** como no verificado***. *Y las tres etiquetas no se
mezclan: *** implementado *** *(esta escrito), *** verificado *** *(se ha visto) *y
*** limitado *** *(no se ha podido ver, *y que haria falta).* *

---

# PARTE 1 · *PARA USO DOMESTICO*

## 1.1 *Lo que esta verificado, *y como*

| *que* | *evidencia* |
|---|---|
| *UI: fases 1, 2, 3, 4 y 6* | *`ruff` limpio; *18 de interfaz y contraste; *81 del frontend* |
| *El color: de 611 clases de fabrica a 6* | *censo, *y el trinquete `test_la_paleta_de_fabrica_no_crece`* |
| *El error de pantalla, *en una pieza* | *visto en `Despensa`, `Panel`, `Tendencias`, `Recetario`, `Diario`, `PlanSemanal`, `Producto`* |
| *** El error de accion *** | *** pulsado de verdad ***: *se relleno `/unirme` y se pulso «Entrar»* |
| *El movil a 390 px* | *** medido ***: *sin desbordamiento, *y la barra de abajo funciona* |
| *** La version servida *** | *** verificado ***: *`cesta-web-1` monta el `dist` local, *y los 8 chunks llevan los cambios. *Ver `docs/ui/VERSION-SERVIDA.md`* |
| *Los datos publicados* | *** medidos ***: *`data/gold/actual.json` = `20261015-123403`, *del 15/10, *con **huellas SHA-256*** |
| *** La frescura por cadena *** | *** medida ***: *alcampo al *** 14 ***, *y las demas al *** 15*** |
| *** La cobertura de Lidl *** | *** cuantificada ***: *** 230 filas y 3 dias *** *frente a 730.860 de alcampo* |

## 1.2 *Lo que esta limitado, *y por que*

| *que* | *que haria falta* |
|---|---|
| *Las ramas que dependen de datos: *`Grupo`, *`Panel` con datos, *`Ajustes`/`Avisos`/`Cesta` sin listas* | *API con datos controlados* |
| *** El recorrido completo ***: *5 recetas → plan → lista → compra → consumo → diario* | *** API *** |
| *Comparaciones, *ofertas y graficas* | *API, *y datos de varias fuentes* |
| *Que lo servido *** se comporte bien *** | *API; *hoy solo se sabe que *** el codigo esta*** |

*** Y el limite es UNO, *y no es de herramientas ***: *** el acceso a datos.*** *
*Las dos cosas que parecian imposibles -- pulsar y medir a 390 px -- *** se hicieron.*** *

## 1.3 *Y el rechazo de Alcampo, *que parecia un fallo y no lo es*

```
*** El 15/10 alcampo quedo `ok=False` con 1 error, *y su ultimo dia publicado es el 14 *** *
*** -> *y eso *** NO es un fallo ***: *es *** el sistema funcionando por TRES capas *** ✓
   *-- *el WAF impidio completar la captura *
   *-- *`core/cobertura.py` detecto las ramas caidas *(-- -67%, -58%, -89% --)*
   *-- *la publicacion NO publico alcampo *y *** conservo el del 14 *** ✓✓✓
*** -> *** el rechazo es el acierto *** ✓
```

*** Y el merito no es mio ***: *`core/cobertura.py` **ya existia**, *y nacio del **mismo
fallo*** *(-- *18 de septiembre: *20.571 en vez de 23.573, *dado por **completo con cero
errores**, *y detectado **a mano** --).* *

## 1.4 *Los dos defectos demostrados, *que NO he tocado*

```
*** 1 ***. *** `data/publicado/` son dos artefactos MUERTOS *** *
   *-- *`grupos.json` (1,9 MB) *y `stats.json` (865 B), *los dos del *** 16/09 *** *
      *con 16 segundos de diferencia ✓
   *-- *`git grep` *** no encuentra ni quien los escribe ni quien los lee *** ✓
   *-- *el mecanismo real es `core/publicacion.py` + `data/gold/actual.json` ✓
   *-- *** POR QUE NO LOS BORRO ***: *son *** datos del propietario***, *
      *y *** no puedo saber si algo FUERA del codigo los lee *** *
      *(-- *un panel, *una tarea, *un documento --).* *Es *** una decision suya*** ✓
*** 2 ***. *** La cobertura de Alcampo no esta declarada *** *
   *-- *`data/cobertura/` solo tiene `lidl-*.json` ✓
   *-- *y *** la ausencia se lee como «alcampo esta completo»***, *que es falso ✓
   *-- *** POR QUE NO LO ARREGLO ***: *donde declararla es *** una decision de diseño***, *
      *y hacerlo a ciegas seria inventarme el sitio ✓✓✓
```

---

# PARTE 2 · *PARA DESPLIEGUE PUBLICO*

## 2.1 *Lo que hace falta y NO esta*

| *que* | *estado* |
|---|---|
| *** Validar la aplicacion con datos *** | *** NO HECHO ***: *nunca se ha visto `Grupo` ni `Panel` con datos* |
| *** El recorrido completo *** | *** NO HECHO *** |
| *** Que lo servido se comporte *** | *** NO VERIFICADO ***: *se verifico que el *** codigo *** esta, *y no que *** funcione*** |
| *Comparaciones y graficas con cobertura declarada* | *** NO VERIFICADO *** |
| *Que la cobertura parcial este declarada para TODAS las cadenas* | *** NO HECHO *** |

## 2.2 *Los bloqueos, *concretos*

```
*** BLOQUEO 1 ***. *** RESUELTO EL 15/10/2026: *EL PROPIETARIO AUTORIZO LA BASE DESECHABLE *** *
   *-- *sin ella no se puede validar nada de lo de arriba ✓
   *-- *y la restriccion vigente es «solo frontend» ✓
   *-- *** la peticion esta hecha y espera respuesta *** ✓
*** BLOQUEO 2 ***. *** El rechazo de Alcampo depende de interaccion humana *** *
   *-- *el reto de AWS WAF, *cuando con ventana tampoco pasa, *
      *** pide interaccion humana *** ✓
   *-- *y el encargo prohibe *** eludir CAPTCHA/WAF *** ✓
   *-- *** o sea que no es un defecto: *es un limite de la fuente *** ✓
*** BLOQUEO 3 ***. *** Dos decisiones que son del propietario *** *
   *-- *si `data/publicado/` es muerto o lo lee algo de fuera ✓
   *-- *y donde se declara la cobertura de las cadenas que no son Lidl ✓
```

## 2.3 *Y una advertencia que va con el despliegue publico*

*** Lo que si esta verificado es la UI y la publicacion, *NO el comportamiento con datos.** *
*Para uso domestico eso es aceptable: *el propietario ve la aplicacion a diario.* *
*Para despliegue publico *** no lo es***: *nadie ha recorrido el flujo completo, *y **no
se puede afirmar que funcione** con datos reales y con dos usuarios distintos.* *

---

# PARTE 3 · *Lo que he hecho en este encargo, *y lo que no*

```
*** HECHO ***: *punto 1 (documento consolidado, *4 contradicciones fuera); *
   *punto 6 *** ENTERO *** (causa, *tres cosas separadas, *Lidl cuantificado, *
   *y dos defectos acotados); *y punto 7 primera mitad (version servida) ✓
*** NO HECHO, *con su motivo ***: *puntos 3, 4 y 5, *** bloqueados por el 2 ***; *
   *y punto 7 segunda mitad, *que necesita datos ✓
*** Y NO SE HA CREADO NINGUN DEFECTO NUEVO ***: *todo lo tocado lleva sus puertas, *
   *y los dos defectos hallados *** no se han tocado a proposito *** ✓
```

---

# PARTE 4 · *** Y ESTO CAMBIA EL PLAN: *la API ya esta detras del Caddy ***

*15/10/2026, ronda 8. *No estaba comprobado antes, *y cambia **el punto 2 entero.*** *

```
*** `plataforma/Caddyfile` ***: *`:8080 { handle /api/* { reverse_proxy api:8000 } }` *** ✓
*** -> *** el 8080 sirve la API EN EL MISMO ORIGEN ***, *y su comentario lo dice: *
   *«asi que no hay lios de *** CORS *** ni cookies que se pierden entre puertos» ✓
*** -> *y comprobado EN VIVO: *`/api/salud` *** HTTP 200 ***, *`/api/yo` *** 200 ***, *
   *y `/api/recetas` y `/api/alertas` *** 401 *** *(-- piden sesion --)* ✓✓✓
*** -> *** la API esta viva y accesible en 127.0.0.1:8080 *** ✓
*** -> *y el 8080 *** ya estaba publicado ***: *** no hay que abrir ningun puerto *
   *ni reconstruir nada *** *-- *las dos prohibiciones del encargo ✓✓✓
```

## Y la distincion que hay que hacer, *que no estaba en el plan*

```
*** el `/api` del 8080 apunta a `cesta-db-1` *** *(-- casa 5432 --)* ⚠️
*** -> *** PUNTO 3 ***, *ver las ramas con datos: *se puede hacer *** LEYENDO *** ✓
   *-- *y *** NO necesita autorizacion nueva ***, *porque *** no modifica nada *** ✓✓✓
*** -> *** PUNTO 4 ***, *el recorrido completo: *** SI necesita autorizacion *** ⚠️
   *-- *porque *** crearia *** recetas, *listas y diario *** en la base domestica *** ✓
*** -> *y el encargo dice *** «sin modificar cuentas ni bases domesticas» *** ✓✓✓
```

*** O sea que la autorizacion del punto 2 es MAS PEQUEÑA de lo que yo creia ***: *
*para el punto 3 **no hace falta**, *y para el punto 4 *** si***. *Lo que hay que
autorizar no es «un entorno aislado»: *es *** escribir en la base domestica ***,
*o montar una copia para escribir en ella.* *

---

# PARTE 5 · *** LO VERIFICADO CON DATOS REALES, *rondas 9 a 17 ***

*Y esto **no** estaba en la parte 1 cuando se escribio: *entonces creia que hacia falta
un entorno nuevo.* *** No hacia falta: *la aplicacion servida en 127.0.0.1:8080 ya*
***tenia la API detras, *y no se abrio ningun puerto ni se levanto nada.*** *

| *pantalla* | *que se vio, *con datos reales* | *veredicto* |
|---|---|---|
| *** `Panel` *** | *la tabla «Que entro por cadena» con PRODUCTOS, COMPARABLES, NUTRI-SCORE y EAN; *y la etiqueta «datos del 15 oct 2026»* | *** confirma mis mediciones de fichero, *cifra por cifra *** |
| *** `Buscar` *** | *40 resultados; *precio y **precio por unidad** (EUR/l y EUR/kg); *«comparable · 5 cadenas»; *«oferta solo con tarjeta»; *ahorro en % y «hasta X»* | *** valida el punto 5 *** |
| *** `Comparar` *** *(«Grupo»)* | *los pesos 45/25/20/10 **explicados**; *«Las letras salen de LEER INGREDIENTES, no del precio»; *«los de mas de 3 dias no cuentan»; *«Calidad A deducida por Open Food Facts, **no por la tienda**»* | *** explica su algoritmo y declara el origen del dato *** |
| *** `Comparar` a 390 px *** | *el rail desaparece, *sale la barra de abajo, *las metricas pasan a una columna, *y **no hay desbordamiento horizontal*** | *** cumple el criterio de legibilidad *** |
| *** el foco con teclado *** | *tras tres Tab el foco esta en «Compra» y **se ve**, *con un anillo **terracota*** | *no hay `outline: none` sin sustituto* |
| *** el umbral del buscador *** | *con 1 letra avisa; *con 5 busca de verdad* | *el mensaje no enganya* |

## 5.1 *Y las tres cosas que la pantalla desmintio, *y que yo habia anotado*

```
*** 1 ***. *«la cobertura de Alcampo no esta declarada»* *** ERA FALSO ***: *
   *esta *** en la tabla de `Panel` ***, *con 22.905 productos y 0 con nutri-score ✓
*** 2 ***. *«la frescura no se declara»* *** ERA FALSO ***: *«datos del 15 oct 2026» *
   *sale en `Panel`, *`Buscar` *y `Comparar`; *y ademas *** se aplica al calculo *** ✓
*** 3 ***. *«`Cargando` no sustituye al vacio»* *** ERA FALSO ***: *con 2 letras *
   *** no hay busqueda que sustituir ***; *las peticiones son de los *** cuatro ejemplos *** ✓
*** -> *las tres las saque *** mirando un fichero o una captura, *no la pantalla entera *** ✓
```

## 5.2 *Y lo que sigue SIN verificar, *dicho sin adornos*

```
*** `Cargando` el esqueleto ***: *tres intentos. *Con 1 letra no hay peticion; *
   *con 2 letras tampoco (son los ejemplos); *y con 5 *** la captura termina antes
   *de que se pinte*** *(-- `completeness: incomplete` --)*. *** NO LO HE VISTO. ***
*** *** Contenido largo ***: *la busqueda devuelve 40 con paginacion *
   *(`limite=40&desplazamiento=0`), *pero *** no he medido la tabla con 40 filas ***. *
*** *** Errores ***: *no he provocado un fallo de la API, *y *** NO VOY A PROVOCARLO *** *
   *en un servicio que el propietario usa. *Queda sin verificar, *con su motivo. *
*** *** Las pantallas con sesion ***: *`Recetario`, *`PlanSemanal`, *`Diario`, *
   *`Cesta` sin listas, *`Ajustes`, *`Avisos`, *`Favoritos` -- *dan *** 401 *** *
   *sin sesion, *y verlas con datos exige *** crear datos ***, *que es el punto 4. *
```

## 5.3 *Y las cinco veces que el instrumento enganyo*

```
*** 1 ***. *la rama equivocada *(-- *rondas 29, 31, 33 --)*
*** 2 ***. *el `<p>` de `Escaner` contado sin mirar lo que lo envolvia *(-- ronda 38 --)*
*** 3 ***. *el `grow` que di por inutil y llevaba funcionando desde la ronda 30 *(-- 44 --)*
*** 4 ***. *el defecto 2 del punto 6, *«cobertura no declarada», *que la pantalla desmiente*
*** 5 ***. *«no hay ninguna peticion con `q=le`», *leido del final de una traza de 200 KB*
   *-- *y la peticion *** estaba ***, *mas arriba *(-- ronda 17 --)*
*** -> *las cinco son *** la misma cosa ***: *mirar una parte y concluir del conjunto ✓
*** -> *y las cinco se corrigieron *** mirando mas, *no razonando mas *** ✓✓✓
```

---

# PARTE 6 · *** LAS SEIS PUERTAS: *ESTABAN ROJAS POR EL ENTORNO, *Y CON LA BASE LEVANTADA ESTAN VERDES (rondas 19 y 20) ***

*** Esto **no** se habia corrido en este objetivo ***, *y el propietario ya lo aviso:
*«las 2.081 de Python y el build *** no se repitieron *** en esa comprobacion».* *

## 6.1 *El estado real de las seis, *medido hoy*

```
*** ruff check . *** *** limpio *** ✓
*** npm test *** *** 81 pass, *0 fail *** ✓
*** tsc --noEmit *** *** limpio *** ✓
*** npm run build *** *** ✓ built in 28.51s *** ✓
*** pytest -q (CESTA_POSTGRES al 5434) *** *** 1 failed, 2048 passed, *** *
   *** 17 skipped, *32 errors *** ⚠️⚠️⚠️
*** plataforma.prueba_e2e *** *** NO CORRIDA *** ⚠️
```

*** Cuatro de seis verdes. *Y la que el encargo nombra en segundo lugar *** NO lo esta.*** *

## 6.2 *Y de que son los 32 errores, *que es lo que importa*

| *fichero* | *errores* | *de que es* |
|---|---|---|
| *`test_revision_a09_compra_hogar.py`* | *** 7 *** | *la compra del **hogar*** |
| *`test_fase2_f07_otro_hogar.py`* | *** 6 *** | *** otro hogar *** |
| *`test_revision_a09_sustitucion.py`* | *5* | *la sustitucion* |
| *`test_fase2_f07_dos_sesiones.py`* | *** 5 *** | *** dos sesiones *** |
| *`test_b07_la_ruta_de_importar_y_sus_guardas.py`* | *5* | *importar* |
| *`test_la_lista_acumula.py`* | *4* | *la lista que acumula* |

*** Y los nombres de los tests que fallan son, *literalmente, *el punto 4 ***: *

```
*** `test_las_dos_personas_anaden_lineas_y_las_dos_aparean` *** -> *dos personas ✓
*** `test_b_ve_la_lista_de_a_despues_de_compartirla` *** -> *la lista compartida ✓
*** `test_el_historico_queda_y_lo_ven_las_dos_personas` *** -> *el historico ✓
*** `test_al_cerrar_la_compra_las_lineas_salen_de_la_lista` *** -> *cerrar la compra ✓
*** `test_dos_operaciones_distintas_sobre_lo_mismo_COEXISTEN` *** -> *idempotencia ✓
```

## 6.3 *Y lo que esto significa, *dicho sin rodeos*

```
*** el punto 4 *** NO SOLO NO ESTA VERIFICADO ***: *
   *** hay 1 fallo y 32 errores en las pruebas que lo cubren *** ⚠️⚠️⚠️
*** -> *y cubren *** exactamente *** *lo que el encargo pide comprobar: *
   *** cantidades, *persistencia, *IDEMPOTENCIA *** *
   *y *** AISLAMIENTO ENTRE USUARIOS *** ✓
*** -> *** o sea que el punto 4 empieza por un rojo, *no por un blanco *** ✓✓✓
*** Y NO LO HE TOCADO ***, *y digo por que: *
   *-- *no se si los 32 errores son *** de montaje *** *(-- *fixtures, *base, *sesion --)* *
      *o *** fallos reales *** ⚠️
   *-- *y arreglar esto *** sin saber cual de las dos cosas es *** seria *
      *exactamente el error que llevo cinco veces cometiendo ✓
*** -> *** lo siguiente es leer UNA traza entera ***, *no el recuento ✓
```

## 6.4 *Y LA CONCLUSION, *que corrige lo que yo mismo escribi en la 6.3 (ronda 20)*

*** En la parte 6.3 escribi que «el punto 4 empieza por un ROJO». *** Era una lectura
correcta del recuento, *y *** la causa era otra.*** *

```
*** `AJUSTES.postgres` *** sale de `os.environ.get(...)` *y su valor por defecto es *
   *** `postgresql://cesta:cesta@localhost:5432/cesta` *** *-- *LA BASE DOMESTICA ✓
*** -> *y habia *** un mensaje escrito justo para esto ***: *
   *«no puede apuntarle. *Usa el 5434: *CESTA_POSTGRES=...» ✓
*** -> *y lo decisivo: *** `5434 NO ESCUCHA` ***, *y *** no habia contenedor
   *`cesta-prueba-db` *** ✓
*** -> *** los 32 errores eran `psycopg.errors.ConnectionTimeout` EN EL SETUP *** *
   *-- *`ERROR at setup of ...` -> `almacen.arranca()` -> `psycopg.connect(...)` ✓
*** -> *** NO ERA UN DEFECTO DE LA APLICACION: *ERA QUE NO HABIA BASE *** ✓✓✓
```

## 6.5 *Y con la base desechable levantada, *las seis estan verdes*

*El comando esta en `docs/BACKLOG.md:1909`, *y el propio encargo lo cita: *`docker run
--rm -d` en el *** 5434 ***, *«que no es el de casa»*. *Se levanto, *se corrieron las dos
puertas rojas, *y *** se desmonto***. *

```
*** pytest -q *** *** 2081 passed, *17 skipped, *0 failed, *0 errors *** *
   *en 204,49 s ✓✓✓ *-- *** exactamente los 2.081 que no se habian corrido *** ✓
*** plataforma.prueba_e2e *** *** «== TODO BIEN» *** ✓✓✓
*** -> *y su salida dice, *literalmente: *
   *** «la misma operacion dos veces -> el mismo id (74)» *** *
      *** = la IDEMPOTENCIA *** ✓
   *** «y otra operacion distinta -> otro apunte» *** ✓
   *** «tras recargar: 23 lineas (antes 23)» *** *** = la PERSISTENCIA *** ✓
   *** «el diario trae 2 apuntes · kcal_conocida=None · completo=False» *** *
      *** = y declara LOS DATOS DESCONOCIDOS *** ✓✓✓
```

## 6.6 *Y las seis, *medidas*

| *puerta* | *estado* |
|---|---|
| *`uv run ruff check .`* | *** limpio *** |
| *** `uv run pytest -q` (5434) *** | *** 2081 passed, *0 failed, *0 errors *** |
| *`npm test`* | *** 81 pass, *0 fail *** |
| *`npx tsc --noEmit`* | *** limpio *** |
| *`npm run build`* | *** OK en 28,51 s *** |
| *** `plataforma.prueba_e2e` *** | *** «TODO BIEN» *** |

## 6.7 *Y la leccion, *que es la SEXTA de la misma familia*

```
*** escribi «el punto 4 empieza por un ROJO» leyendo el RECUENTO *** ⚠️
*** -> *y la causa era *** que no habia base ***, *no la aplicacion ✓
*** -> *** sexta vez: *mirar una parte (el recuento) *y concluir del conjunto *** ✓
*** -> *y se corrigio *** leyendo UNA traza entera ***, *no razonando ✓✓✓
*** -> *y las seis se han corregido *** mirando mas *** ✓
```

---

# PARTE 7 · *** LA AUTORIZACION, *Y EL PLAN EXACTO (ronda 21) ***

*** El propietario respondio el 15/10/2026 ***: *«Si, *con base desechable en el 5434».* *
*Y con eso *** el bloqueo 1 deja de ser un bloqueo***, *y el punto 4 se puede hacer
***sin escribir nada en la base domestica.*** *

## 7.1 *La peticion, *tal como se hizo*

*** Que se necesita ***: *una API en un *** puerto libre *** apuntando a una
*** base NUEVA y desechable en el 5434 *** *(-- *libre: *5432 *y *5433 estan ocupados --)*,
*con *** usuarios de prueba***. *Todo lo que se capture sale de ahi.* *

*** Que NO se toca ***: *`casa 5432`, *`facylf 5433`, *las pruebas compartidas 5434
*(-- *no hay: *estan libres --)*, *ninguna cuenta domestica, *
*** y no se despliega ni se abre ningun puerto al exterior.*** *

## 7.2 *Y el precedente, *que es lo que hace que la peticion sea creible*

```
*** en la ronda 20 se hizo YA, *en pequeño: *
   *-- *se levanto `cesta-prueba-db` *(-- *`docker run --rm -d` en el 5434 --)* ✓
   *-- *se corrieron las seis puertas: *2081 passed, *0 failed, *0 errors, *
      *y `prueba_e2e` *** «== TODO BIEN» *** ✓
   *-- *** y se desmonto *** *(-- *`docker rm -f` --)* ✓
   *-- *y 5432, *5433 *y 8080 *** siguieron arriba todo el tiempo *** ✓✓✓
*** -> *** el patron esta probado ***: *se crea, *se usa, *y se destruye ✓
```

## 7.3 *Y lo que queda por hacer, *en orden, y con lo que prueba cada cosa*

| *paso* | *que se hace* | *que prueba* |
|---|---|---|
| *1* | *base desechable en el 5434 + migraciones* | *--* |
| *2* | *API en puerto libre apuntando ahi* | *--* |
| *3* | *** pantallas con sesion *** | *** punto 3 ***: *`Recetario`, *`PlanSemanal`, *`Diario`, *`Cesta` sin listas, *`Ajustes`, *`Avisos`, *`Favoritos` |
| *4* | *** el recorrido ***: *5 recetas -> plan -> lista -> compra -> consumo -> diario* | *** punto 4 *** |
| *5* | *** dos usuarios *** | *** el aislamiento entre usuarios *** |
| *6* | *** cerrar la compra *** | *** que comprar NO registra consumo automaticamente *** |
| *7* | *`Cargando` con una busqueda lenta* | *lo que llevo tres intentos sin ver* |
| *8* | *contenido largo: *40 filas* | *el punto 3* |
| *9* | *** desmontar la base *** | *--* |

*** Y EN CADA CAPTURA SE DIRA QUE PRUEBA Y QUE NO ***, *que es la regla del encargo. *

## 7.4 *Y los pasos 1 y 2, *HECHOS Y VERIFICADOS (ronda 22)*

```
*** PASO 1 *** *** HECHO ***:*
   *-- *`docker run --rm -d --name cesta-prueba-db ... -p 127.0.0.1:5434:5432 postgres:16-alpine` ✓
   *-- *y las migraciones por *** la funcion del propio proyecto *** *
      *(-- *`almacen.arranca()` -> `migra()`, *`almacen.py:137` --)* ✓
   *-- *** 14 tablas ***: *alerta, *cocina, *compra, *compra_linea, *despensa, *
      *favorito, *invitacion, *lista, *lista_acceso, *lista_linea, *preferencia, *sesion... ✓
*** PASO 2 *** *** HECHO ***:*
   *-- *`uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099` ✓
   *-- *`/api/salud` -> *** 200 ***: *`{"vivo":true,"fecha_datos":"2026-10-15"}` ✓
   *-- *`/api/yo` -> *** 200 ***: *`{"usuario":null,"preferencias":{}}` ✓
```

*** Y LA GUARDA DEL PROYECTO, *que es lo que hace esto seguro ***: *

```
*** `plataforma/prueba_e2e.py` llama a *** `comprueba_que_es_una_prueba(CESTA_POSTGRES)` *** *
*** -> *y su comentario: *«No basta con que el script se ponga su propio DSN si viene *
   *uno de fuera: *hay que *** RECHAZARLO***» ✓
*** -> *al arrancar salio *** «la guarda ACEPTA el DSN: es de prueba» *** ✓✓✓
*** -> *** el codigo YA impide que estas pruebas toquen la base domestica *** ✓
```

*** ESTADO AL CERRAR LA RONDA 22 ***: *la base desechable y la API del 8099 estan
*** levantadas***, *y 8080, *5432 *y *5433 *** siguen intactos.*** *
*Los pasos *** 3 a 9 *** quedan pendientes: *pantallas con sesion, *el recorrido, *
*dos usuarios, *cerrar la compra, *`Cargando`, *contenido largo, *y desmontar.* *

## 7.5 *Y el entorno esta COMPLETO, *y no lo invente yo (ronda 23)*

*** La pieza que faltaba era *como apuntar el frontend a MI API*, *porque el 8080
proxya `/api` a `cesta-api-1`, *o sea *** a la base domestica***. *Y la respuesta estaba
*** escrita en el proyecto ***, *en `plataforma/prueba_navegador.py`: *

```
*** `cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev` *** ✓
*** -> *** `CESTA_API` *** hace que el frontend en *** dev *** hable con la API que le digas ✓
*** -> *y su propio comentario avisa: *«la imagen que corre en el 8080 *** puede ser
   *mas vieja***» ✓
```

*** Y LOS TRES PISOS DEL ENTORNO, *verificados ***: *

| *pieza* | *donde* | *verificado con* |
|---|---|---|
| *base desechable* | *** 5434 *** | *14 tablas, *y la guarda acepta el DSN* |
| *API* | *** 8099 *** | *`/api/salud` -> **200**, *`vivo true`* |
| *frontend en dev* | *** 5173 *** | *HTTP **200**, *** `title: Cesta` ***, *y *`/api/salud` responde por ahi* |

*** Y 8080, *5432 *y *5433 *** siguen intactos.*** *

## 7.6 *Y lo que encontro el proyecto, *que yo iba a hacer a mano y peor*

```
*** `prueba_navegador.py` define *** DOS CUENTAS FIJAS ***: *
   *** `USUARIO = "prueba-navegador"` *** *y *** `USUARIO_INVITADA = "prueba-invitada"` *** ✓
*** -> *y explica por que son fijas y no nuevas: *«la API limita las altas por hora» ✓
*** -> *y por que son dos: *«tiene que ser *** otra persona***, *porque el caso que manda *
   *es el de quien recibe el enlace y no estaba dentro» ✓✓✓
*** -> *y usa un movil de *** 390 x 844 *** *con `has_touch`, *«de pie y con una mano» ✓
*** -> *** o sea que el punto 4 YA TIENE su puerta mecanica escrita *** *
   *-- *y lo que yo iba a montar a mano con REA *** ya existe, *y mejor *** ✓✓✓
```

## 7.7 *Y LA PUERTA DEL PUNTO 4 **ESTA ROTA**, *y se sabe desde cuando (ronda 24)*

*** Se corrio `plataforma/prueba_navegador.py` contra el entorno aislado. *** Y pasa
muchisimo ***, *y falla en un sitio concreto.* *

```
*** ok *** *la portada dice que hay tres aplicaciones*
*** ok *** *el buscador se ve en la primera pantalla, sin buscar el boton*
*** ok *** *escribir busca: los resultados salen debajo, sin pulsar nada*
*** ok *** *y la fecha de los precios va CON ellos, que es donde hace falta*
*** ok *** *sin escribir nada hay algo que leer, no una pantalla vacia*
*** ok *** *y no es una visita guiada: no hay pasos que pasar*
*** ok *** *la tarjeta ensena ejemplos (4)*
*** ok *** *los CUATRO ejemplos hablan de lo que se busca*
*** ok *** *sin sesion la lista pide entrar, y lo explica*
*** ok *** *el alta pide nombre, usuario y clave*
*** ok *** *la cuenta prueba-navegador entra*
*** FALLO *** *** sin sesion sale la tarjeta de la primera vez (no un esqueleto) *** ***
```

### 7.8 *Y WHAT falla, *exactamente*

```
*** el test exige *** `"Esto compara el precio" in main` *** en `/buscar` ✓
*** -> *y la frase *** NO EXISTE ***: *`git grep` en `src` da *** CERO ***, *
   *y tampoco esta en el bundle ni en `index` ✓
*** -> *y `git log -S` dice que *** existio ***: *escrita el *** 23/09 *** en `783fcc9`, *
   *y *** quitada *** en *** `21c48a5` *** *(-- «REVISION INDEPENDIENTE DEL 12 DE
   *OCTUBRE: *se conserva el trabajo del dueno, *que estaba SIN COMMITEAR» --)* ✓
*** -> *** la frase se quito, *y el test no se actualizo *** ✓
```

### 7.9 *Y por que esto importa mas que el fallo en si*

```
*** `prueba_navegador.py` *** es la puerta mecanica del punto 4 *** *
   *-- *y el propio fichero lo dice: *«lo que este script no pase, *
      *** no se le puede pedir a una persona» *** ✓
*** -> *** y se CORTA en el primer fallo ***: *todo lo que venia despues *** no corre *** ⚠️
*** -> *** o sea que el punto 4 no esta sin verificar porque falte entorno: *
   *** esta sin verificar porque su puerta no llega al final *** ✓✓✓
*** -> *y eso explica tambien por que el encargo pide «verificar» y no «confiar» ✓
```

*** Y NO SE HA TOCADO EL TEST ***, *y se dice por que ***: *no se si la frase se quito
a proposito y el test quedo viejo, *o si se perdio sin querer. *Eso *** es del
propietario***, *y las dos salidas son distintas: *si se quito a proposito, *
*el test hay que actualizarlo; *si se perdio, *la pantalla hay que arreglarla.* *

## 7.10 *Y LA PUERTA DEL PUNTO 4, *ARRANCADA Y CORRIDA ENTERA (ronda 25)*

*** El fallo de la frase *** se resolvio leyendo el diff del commit que la quito ***: *

```
*** el commit `21c48a5` dice: *«se conserva el trabajo del dueno, *que estaba SIN *
   *** COMMITEAR» ***, *y *** «El commit es suyo: *aqui solo se preserva» *** ✓
*** -> *y el diff ***: *
   *** - Esto compara el precio del mismo producto entre cinco supermercados. ***
   *** + Esto compara precios por unidad de grupos de productos entre supermercados. *** ✓
*** -> *** LA FRASE SE REESCRIBIO A PROPOSITO, *Y POR EL PROPIETARIO *** ✓
*** -> *y la nueva es *** MAS PRECISA***: *dice «por unidad» (EUR/kg, *EUR/l) *
   *y «de grupos de productos», *que es lo que la aplicacion hace ✓
*** -> *** la PRUEBA estaba vieja, *no la pantalla *** ✓✓✓
```

*** Y el arreglo, *una linea, *con el texto viejo citado en un comentario para que
nadie vuelva a dudar de cual era la buena ***: *

```
*** antes ***: *`comprueba("Esto compara el precio" in primera, ...)`*
*** ahora ***: *`comprueba("Esto compara precios por unidad" in primera, ...)`*
*** -> *y se comprueba un *** PREFIJO *** *a proposito: *para que otra reescritura *
   *de la cola de la frase *** no la vuelva a romper *** ✓
*** -> *LF conservado *(-- *2146 lineas, *CRLF=0 --)*, *y el diff *** 10/1 *** ✓
```

### 7.11 *Y EL RESULTADO: *86 COMPROBACIONES PASAN, *CERO FALLOS*

```
*** *** 86 ok ***, *0 FALLO *** ✓✓✓
*** -> *y llega a *** LA ULTIMA SECCION *** del script: *
   *«cuantos toques hay desde la primera pantalla hasta cada respuesta» ✓
*** -> *y el unico error que queda es un `TimeoutError` al buscar *
   *** `nav a[href='/cesta']` ***, *que es *** OTRO asunto *** ✓
```

*** Y entre los 86 hay comprobaciones que son *** literalmente *el punto 5 ***: *

| *lo que comprueba la puerta* | *que es del encargo* |
|---|---|
| *«el indice contesta con una frase, no solo con un dibujo»* | *** las graficas dicen lo que son *** |
| *«y ensena sobre cuantos productos y cuantas capturas lo dice»* | *** PERIODO y COBERTURA *** |
| *«cada oferta acusada dice en que unidad esta su precio»* | *** la UNIDAD *** |
| *«lo que no se juzga se cuenta por motivo»* | *** los DATOS DESCONOCIDOS *** |
| *«filtrar por una cadena deja una sola serie en el indice»* | *** la comparacion exacta *** |
| *«el panel de posicion contesta 'En que es cara cada cadena'»* | *** las alternativas *** |

## 7.12 *Y EL SEGUNDO ASUNTO, *que es del MISMO tipo (ronda 26)*

*** El unico error que quedaba era `TimeoutError` buscando `nav a[href='/cesta']`. ***
*Y la causa es la misma clase de cosa:* *

```
*** la ruta *** `/cesta` NO EXISTE *** en `App.tsx` ✓
*** -> *y el test espera *** `BARRA = {"Cesta": "/cesta", "Avisos": "/avisos", *
   *"Panel": "/panel", ...}` *** ⚠️
*** -> *y las rutas reales son *** `/compra/...` *** ✓
*** -> *** la prueba de los TOQUES usa rutas que ya no existen *** ✓✓✓
*** -> *y por eso el timeout: *no hay ningun `nav a[href='/cesta']` ✓
```

*** O sea que hay *** DOS pruebas desactualizadas ***, *y del mismo tipo: *
*una frase reescrita y unas rutas movidas. *Y las dos *** cortan el script antes
del final.*** *Ninguna de las dos es un defecto de la aplicacion.* *

## 7.13 *Y EL DESMONTAJE, *hecho y verificado (paso 9)*

```
*** `job_kill` a los dos jobs propios *** *(-- *el frontend dev y la API --)* ✓
*** `docker rm -f cesta-prueba-db` *** ✓
*** -> *** 5173: cerrado *** · *** 8099: cerrado *** · *** 5434: cerrado *** ✓✓✓
*** -> *y *** 8080, *5432 y 5433 siguen arriba *** ✓
*** -> *y los contenedores son los cuatro de siempre: *
   *`cesta-api-1`, *`cesta-web-1`, *`cesta-db-1` *y *`facylf-postgres` ✓
*** -> *** no queda nada mio levantado *** ✓✓✓
```

## 7.14 *Y la `BARRA` estaba mal en DOS sitios, *no en uno (ronda 27)*

```
*** `BARRA = {"Cesta": "/cesta", "Avisos": "/avisos", "Panel": "/panel", *
   *** "Buscar": "/", "Escáner": "/escaner"}` *** ✓
*** -> *y las rutas de `App.tsx` ***: *
   *-- *`/cesta` *** EXISTE *** *pero es *** `<Navigate to="/compra/listas">`***, *
      *o sea una *** redireccion ***: *el nav *** no puede *** llevar `href='/cesta'` ✓
   *-- *`/avisos` y `/panel` y `/escaner` *** si existen *** *y no se han movido ✓
   *-- *** `/` NO es Buscar: *es el LANZADOR *** ⚠️ *-- *y la ruta de Buscar es `/compra` ✓
*** -> *** DOS valores malos ***: *«Cesta» *y *** «Buscar» *** ✓
```

*** Se corrigieron los dos, *con el motivo escrito en el codigo ***: *

```
*** antes ***: *"Cesta": "/cesta",  "Buscar": "/"*
*** ahora ***: *"Cesta": "/compra/listas",  "Buscar": "/compra"*
*** -> *y se cita que `/cesta` es una redireccion y que `/` es el Lanzador ✓
*** -> *LF conservado *(-- *2152 lineas, *CRLF=0 --)*, *y el diff acumulado *** 8/2 *** ✓
```

### 7.15 *Y LO QUE NO SE HA HECHO, *y se dice*

```
*** NO se ha vuelto a correr la puerta con estos dos arreglos *** ⚠️
*** -> *porque exige levantar otra vez base, *API *y frontend, *
   *y *** esta sesion ya no tiene margen para ese ciclo *** ✓
*** -> *** los dos arreglos estan RAZONADOS, *no VERIFICADOS *** ✓✓✓
*** -> *y el que los lea sabe exactamente que falta: *
   *** volver a correr `prueba_navegador.py` y ver la seccion de los toques *** ✓
```

## 7.16 *Y SE VOLVIO A CORRER LA PUERTA: *EL ARREGLO DE LA FRASE FUNCIONA (ronda 28)*

```
*** *** 19 ok ***, *** 0 FALLO *** ✓✓✓
*** -> *y pasa *** «sin sesion sale la tarjeta de la primera vez (no un esqueleto)» *** *
   *** -- *que era EL fallo -- *** ✓✓✓
*** -> *y pasa los cuatro ejemplos, *y «la cuenta prueba-navegador entra» ✓
*** -> *** EL ARREGLO DE LA FRASE ESTA VERIFICADO *** ✓
```

## 7.17 *Y DONDE SE CORTA AHORA, *que es un TERCER sitio del mismo patron*

```
*** `pagina.wait_for_url("**/grupo/**", timeout=15000)` *** ⚠️
*** -> *y `/grupo/:id` *** es una REDIRECCION a `/compra/comparar/:id` *** ✓
*** -> *o sea que la URL final *** no contiene `/grupo/` ***, *y la espera caduca ✓
```

*** Y AL CONTAR LOS SITIOS, *el asunto es mucho mayor ***: *

```
*** `a[href^='/grupo/']` *** aparece en *** MAS DE VEINTE PUNTOS *** del fichero: *
   *572, *580, *583, *677, *680, *683, *758, *782, *800, *804, *810, *812, *
   *1438, *1439, *1440, *1456, *1477, *1574, *1917, *1972, *1976, *2070 ✓
*** -> *y `App.tsx` *** NO tiene ninguna ruta `/grupo` *** ✓
*** -> *** `/grupo/...` ya no es una URL: *el frontend genera `/compra/comparar/...` *** ✓
*** -> *** la prueba esta vieja en mas de veinte sitios, *no en uno *** ✓✓✓
```

### 7.18 *Y por eso NO se toca mas*

```
*** arreglar esto *** no es una linea ***: *es revisar el fichero entero ✓
*** -> *y hacerlo a trozos, *con el margen que queda, *seria *** exactamente *** *
   *el error que llevo *** SEIS VECES *** cometiendo en este encargo ✓
*** -> *** se para, *y se deja escrito *** ✓✓✓
```

## 7.19 *Y el desmontaje, *otra vez verificado*

```
*** `job_kill` a los dos jobs propios *** ✓ · *** `docker rm -f cesta-prueba-db` *** ✓
*** -> *** 5173: cerrado *** · *** 8099: cerrado *** · *** 5434: cerrado *** ✓
*** -> *y *** 8080, *5432 y 5433 siguen arriba ***, *y los contenedores son los cuatro ✓
*** -> *** no queda nada mio levantado *** ✓✓✓
```

## 7.20 *Y EL BALANCE DE LA PUERTA, *con lo que se sabe ahora*

*** Lo que se ha visto con datos, *y es mucho ***: *

```
*** 86 comprobaciones *** pasaron en la ronda 25 *** *(-- *la puerta llego al final --)* ✓
*** -> *y entre ellas, *lo del punto 5: *unidad, *periodo, *cobertura, *
   *datos desconocidos *y comparacion exacta ✓✓✓
*** -> *** y eso NO se ha perdido: *fue una pasada real, *con su log *** ✓
*** Y lo que queda por hacer en el fichero ***: *
   *-- *** sustituir `/grupo/` por `/compra/comparar/` en los veintitantos sitios *** ⚠️
   *-- *y volver a correr, *que entonces deberia llegar al final ✓
*** -> *** y el arreglo de `BARRA` de la ronda 27 sigue SIN VERIFICAR ***, *
   *porque el script se corta antes de llegar a los toques ✓
```

## 7.21 *Y LAS 22 REFERENCIAS SUSTITUIDAS, *Y UNA CORRECCION MIA (ronda 29)*

*** Dije que arreglar `/grupo/` «no es una linea, es revisar el fichero entero», ***
*** y era MAS DRAMATICO QUE EL PROBLEMA ***: *los veintidos sitios usan el mismo
prefijo y el destino es siempre el mismo, *asi que es una sustitucion literal. *

```
*** `/grupo/` *** antes 22 *** -> *** despues 0 *** ✓
*** `/compra/comparar/` *** antes 0 *** -> *** despues 22 *** ✓
*** -> *ninguno sin barra final; *diff *** 22/22 ***; *LF conservado *(-- 2152, *CRLF=0 --)* ✓
```

## 7.22 *Y AL CORRERLA CON LOS TRES ARREGLOS, *SE CORTA EN EL MISMO SITIO*

```
*** *** 17 ok ***, *0 FALLO *** ✓
*** -> *y para en «esto que tengo en la mano, *esta caro?» ⚠️
*** -> *y el error *** cita MI sustitucion ***: *
   *** `waiting for locator("a[href^='/compra/comparar/']").first to be visible` *** ✓
*** -> *** o sea que la sustitucion se aplico *y el test sigue sin encontrar el enlace *** ⚠️
```

*** Y LO QUE HACE ESA SECCION ***: *`carga("/compra")`, *escribe *** «leche entera» *** *en
el buscador, *y espera *** quince segundos *** *a que salga un resultado. *Y *** no sale.*** *

## 7.23 *Y NO SE POR QUE, *Y NO LO VOY A AFIRMAR*

```
*** el catalogo *** SI esta ***: *`gold` apunta por defecto a *** `data/gold` ***, *
   *que existe *(-- *vi `v20261015-123403` *y `resumen.parquet` --)* ✓
*** -> *y la cuenta *** se creo ***, *y el buscador *** se rellena *** ✓
*** -> *y la pasada de *** 86 ok *** *(-- ronda 25 --)* *** llego al final *** ✓
*** -> *** y con base nueva, *dos veces, *se corta aqui *** ⚠️
*** -> *** NO SE LA CAUSA ***, *y no la voy a inventar: *diria «es el gold» *
   *o «es el estado de la base» *** sin haberlo medido *** ✓✓✓
```

*** LO QUE SI SE SABE ***: *la sustitucion esta *** hecha y aplicada*** *(-- *el error
la cita --)*, *y *** lo que falta por saber es por que no salen resultados con una base
recien migrada***, *cuando con la base de la ronda 25 si salian.* *

## 7.24 *Y EL DESMONTAJE, *verificado otra vez*

```
*** 5173: cerrado *** · *** 8099: cerrado *** · *** 5434: cerrado *** ✓
*** -> *y *** 8080, *5432 y 5433 siguen arriba *** ✓
*** -> *** no queda nada mio levantado *** ✓✓✓
```

## 7.25 *Y LA API RESPONDE PERFECTAMENTE: *EL PROBLEMA NO ES EL CATALOGO (ronda 30)*

```
*** `gold` *** existe *** *y trae los parquet: *`actual.json`, *`grupos.parquet`, *
   *`enlaces.parquet`, *`embedding.parquet` ✓
*** -> *y preguntandole a la API *** directamente ***, *sin navegador: *
   *** `/api/buscar?q=leche+entera&limite=40` *** -> *** HTTP 200 ***, *** 20.719 bytes *** ✓
   *** -> *primer resultado: *`grupo_id` *** 47808 ***, *«Leche entera», *
      *MILSANI, *aldi, *** 96 *** centimos ✓✓✓
*** -> *y `/api/buscar?q=leche` -> *** 200 ***, *20.281 bytes, *«Leche desnatada» ✓
*** -> *** la API da los datos, *y el `grupo_id` de «Leche entera» es 47808 *** *
   *-- *el *** MISMO *** que salio en la ronda 10, *y el que el test busca ✓
```

## 7.26 *Y con eso, *el problema queda acotado al frontend*

```
*** la API *** funciona ***; *el `gold` *** esta ***; *la ruta `/compra/comparar/:grupoId` *
   *** existe *** *(`App.tsx:201`); *y `/grupo/:grupoId` *** redirige *** ahi *(`:277`) ✓
*** -> *y el frontend *** conoce las dos ***: *`App.tsx:144` hace *
   *`startsWith('/grupo/') || startsWith('/compra/comparar/')` ✓
*** -> *** y aun asi el enlace no aparece en la pantalla *** ⚠️
```

## 7.27 *Y LA HIPOTESIS, *que es fuerte y NO esta medida*

```
*** `/api/salud` *** POR EL 5173 FALLO ***, *y *** DOS VECES *** *
   *(-- *rondas 28 *y *29 --)* ⚠️⚠️⚠️
*** -> *y lo achaque a *** IPv6 *** *y lo deje pasar ✓
*** -> *** y quiza NO era IPv6: *quiza el dev server NO proxya `/api` a mi 8099 *** ✓
*** -> *y eso explicaria *** todo ***: *
   *-- *la API del 8099 *** responde 20 KB *** *si le preguntas directo ✓
   *-- *y el NAVEGADOR le pide `/api/buscar` al *** 5173 *** ✓
   *-- *si el 5173 *** no proxya ***, *la pantalla *** no recibe nada *** ✓
   *-- *** y por eso no hay resultados, *ni enlaces, *ni la tarjeta *** ✓✓✓
*** -> *** ES UNA HIPOTESIS, *NO UNA CONCLUSION *** *
   *-- *y por eso *** NO se toca nada *** *ni se declara el punto 4 por bueno ✓
```

*** Y LA LECCION ***: *vi ese `/api/salud` fallando *** dos veces *** *y las dos lo
explique con una causa comoda *(-- IPv6 --)* *** sin medirla.*** *Es la *** septima vez ***
en este encargo que una suposicion comoda tapa el dato.* *
