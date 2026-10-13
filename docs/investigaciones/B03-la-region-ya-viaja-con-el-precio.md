# B03 · **La region ya viaja con el precio** -- en bronze, y se pierde en silver

*(13 de octubre de 2026. **Lo unico que le faltaba a B03, y el paso donde se corta.**)*

## 1. Lo que se anadio, y por que

*El bronze de Lidl tenia 54 columnas y **ninguna decia de que zona era el precio** -- aunque su colector
acreditaba `28` desde el codigo postal **para resolverlo**.* *Asi que 79 precios de Madrid estaban en bronze
**sin decir que lo eran**, y **dos precios de zonas distintas se podian comparar como si fueran el mismo**.*

*Dos cambios:*

```python
# core/schemas.py  -- en ESQUEMA_BRONZE, que comparten las seis fuentes
"region": pl.Utf8,

# projects/cesta/collectors/lidl.py  -- y Lidl la rellena
"region": str(region),
```

**Y comprobado:**

```
columna region: con valor = 79 de 79 · distintas = 1 · valor = 28
```

> **Las 79 filas dicen su zona.** *Y las otras cinco fuentes la dejan vacia, que es lo correcto:*
> *Mercadona y Aldi **ya fijan la zona al pedir**, y las demas no la publican por fila.* **Vacio quiere decir
> «no se declara», no «no tiene zona»** -- *la distincion de siempre.*

## 2. Y **el esquema es compartido**, asi que la suite entera era obligatoria

*`ESQUEMA_BRONZE` lo usan los seis colectores.* **Asi que no bastaba con probar Lidl:**

```
ruff check .        ->  All checks passed!
pytest -q           ->  2012 PASAN, 0 FALLAN, 0 SE SALTAN
```

> **Y el pipeline tambien, que es el que escribe:**

```
  1651966 filas, 6 cadenas
    lidl       2026-10-13
  silver: 51725 filas de 6 cadenas
  gold: 1652509 filas de historico, 37 dias acumulados
```

**Seis cadenas, y `lidl` entre ellas.** *Anadir una columna al esquema compartido no ha roto a ninguna.*

## 3. Y donde se corta: **`silver` la descarta**

```
diario (gold) tiene region: False
```

> **La region esta en bronze (79 de 79) y **no llega a gold**.** *Y no es un fallo de la captura: es que
> `a_silver` **selecciona las columnas que le interesan**, y `region` no esta entre ellas.*
>
> *Asi que el recorrido de la region es:* **bronze SI -> silver NO -> gold NO -> API NO -> pantalla NO.**

## 4. Y lo que eso significa, dicho sin adornos

**El dato esta capturado y no llega a ninguna parte util.** *Que es **exactamente** la clase de cosa que este
paquete lleva trece rondas encontrando* -- *el `grupo_id` que se nombraba y no se leia, el
`por_que_no_se_compara` que se probaba y no se llamaba, y ahora la region que se escribe y no se propaga.*

> **Y decirlo asi es lo que impide contarlo como hecho.** *«La region viaja con el precio» es cierto **en
> bronze** y falso **de bronze en adelante**.* **Y la aceptacion de B03 pide el ambito regional
> *demostrado*** -- no escrito en el primer fichero.

## 5. Asi que lo que queda es **una linea en `a_silver`**

*Y tiene su forma exacta:* **`silver` tiene que llevarse `region` de bronze**, *y `gold` **decidir si la
guarda*** -- *que no es lo mismo: la tabla `diario` es de precios por dia, y una columna mas cambia lo que
significa una fila.*

> *Y ahi esta la pregunta que hay que contestar antes de tocarlo*: **si `diario` guarda un precio por producto
> y dia, y ahora hay zonas, entonces «un precio por producto y dia» ya no es cierto** -- *hay uno por zona.*
> **Y eso no es una columna: es un cambio en lo que la tabla dice.**

## 6. Estado de B03, con esto

```
captura acotada                          HECHO
bronze con la zona acreditada            HECHO (y ahora EN CADA FILA: 79 de 79)
cobertura por campo y contador visible   HECHO
bronze -> silver -> gold                 HECHO (6 cadenas, sin romper nada)
/api/estado como sexta fuente            HECHO (HTTP)
la pantalla la ensena                    HECHO
Y CORRE EN LA PASADA DIARIA              HECHO
club capturado como condicion            PROBADO
fechas                                   PROBADO
nutricion ausente y dicha                PROBADO
ausencias dichas                         PROBADO
LA REGION, DE BRONZE EN ADELANTE         PENDIENTE -- y es una decision, no solo una columna
```
