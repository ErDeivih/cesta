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
*** BLOQUEO 1 ***. *** Falta API con datos controlados *** *
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
