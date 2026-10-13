# B01 · **La cola, medida**: 79.915 fichas, y **72.319 pendientes (el 90,5 %)**

*(2026-10-14, ~01:00. **Y es el «progreso» que B01 pide, medido por primera vez en muchas rondas.**)*

## 1. El estado, literal

```
`data/inventario.sqlite` · tabla *** `fichas` *** (*** 79.915 filas ***)

*** ESTADOS: ***
  *** pendiente       72.319 ***   *-- *y es *** el 90,5 % *** *
  *** correcto          7.593 ***
  *** no_publicado          2 ***
  *** error_temporal        1 ***
```

> *** Y **una nota de nombre, porque costo un intento**: *** *la tabla **no se llama `inventario`**, *se llama
> *** `fichas` *** -- *y **el fichero si se llama `inventario.sqlite`.** *
>
> *** Y **los nueve estados** que B02 vio en `core/inventario.py` (`PENDIENTE · EN_CURSO · CORRECTO · PARCIAL ·
> NO_PUBLICADO · BLOQUEADO · ERROR_TEMPORAL · NO_ENCONTRADO · EXCLUIDO`) *-- *y **aqui solo hay cuatro con filas.** *
> *** -> o sea: **no hay nada EN_CURSO ni BLOQUEADO**, *y **el `lease` de 30 minutos no tiene a nadie esperando.** *

## 2. *** Y el desglose por fuente, que es lo util ***

```
*** alcampo    pendiente  43.603 ***   *-- *el mayor de todos, y con diferencia*
*** carrefour  pendiente  17.280 ***
*** lidl       pendiente   5.026 ***   *** <- y confirma lo que B02 midio *** *
    dia       correcto    4.655
    aldi      pendiente   3.206
    mercadona correcto    2.910
    dia       pendiente   1.637
    mercadona pendiente   1.567
```

> *** Y **3.206 + 1.637 + 1.567 + ... suman los 72.319**, *y **las tres grandes son Alcampo, Carrefour y Lidl.** *
>
> *** Y **el 5.026 de Lidl es el dato que cierra el circulo de B02**: *** *«5.026 fichas pendientes = 1.676 pasadas
> con `--limite = 3`»* -- *y **por eso se subio `LIMITE_POR_EJECUCION` a 1000 en `fichas_lidl.py`.** *
>
> *** -> o sea: *** *** **Lidl no entra a «hacer bulto»: entra con 5.026 fichas detras**, *y **con un presupuesto
> que las hace posibles.** *

## 3. Y **lo que esta cola dice del encargo**, sin adornos

```
*** LO QUE SE PUEDE DECIR, MEDIDO: ***
  *el trabajo **esta vivo y por delante**: *72.319 fichas pendientes, *y **nada atascado** -- *
  *** sin `EN_CURSO` colgadas, *sin `BLOQUEADO`, *y con **una sola `error_temporal`** *y **dos `no_publicado`.** *
  *** -> y esa es la senal de que **la cola funciona**: *lo que falla **vuelve a la cola**, *
  *** y lo que no se publica se marca aparte.** *

*** LO QUE NO SE DECLARA: ***
  *** no se declara «va lento» ni «va rapido» *** *-- *serian **juicios sin linea base**; *
  *** y lo que hay es **un numero**, *y **su desglose por fuente.** *
```

> *** Y **es la primera vez que se mide esta cola en toda la sesion**, *y **por eso vale la pena**: *
> *porque **B01 pide «ingesta activa, progreso y recuperacion»**, *y **el progreso es esto** -- *
> *y **nadie lo habia mirado.** *
