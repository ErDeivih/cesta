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
