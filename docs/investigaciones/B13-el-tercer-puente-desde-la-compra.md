# B13 · **El tercer puente**: `desde-la-compra`, y **«comprar no es comer»** con su motivo escrito

*(13 de octubre de 2026. **Y su ultima frase es la mejor del proyecto, y es la doctrina entera.**)*

## 1. El docstring, literal -- y dice **la clausula central del encargo**

```python
# plataforma/api/main.py:1679
@app.get("/api/listas/{lista_id}/desde-la-compra")
def previa_de_la_compra(lista_id: str, compra_id: str | None = None,
                        usuario: dict = Depends(usuario_actual)) -> dict:
    """**La vista previa de consumir**: que lineas de la ultima compra se podrian anotar y con que datos.

    No escribe nada: el diario rechaza el tipo `compra` a proposito -- comprar no es comer --, asi que esto
    **propone** y la persona confirma.

    **Y dice la cobertura, que es lo que hace que esto no mienta**: las lineas cuyo producto **no** declara
    nutricion en el catalogo se devuelven aparte, con su nombre. Anotar las que se puede y callar las demas
    convertiria un dato que falta en una comida que parece completa.
    """
    ...
    return {"compra_id": None, "anotarian": [], "sin_dato": [],
            "cobertura": {"con_dato": 0, "total": 0}}
```

## 2. *** Y contesta la clausula del encargo, y la mejora ***

> *** El encargo dice: ***
> > *** «*** *** COMPRA NO ES CONSUMO: *** *** el plan calcula nutricion prevista; *** *** EL DIARIO SOLO REGISTRA LAS
> > PORCIONES CONFIRMADAS *** *** por cada persona, *** *** con receta/version/snapshot Y COBERTURA. *** ***» ***
>
> *** Y **el docstring dice las cuatro cosas, una por una**: ***
> ```
> *** «el diario RECHAZA el tipo `compra` A PROPOSITO» ***  -> *** «compra no es consumo», COMPROBADO (B07) *** *
> *** «esto PROPONE y LA PERSONA CONFIRMA» ***               -> *** «solo registra las porciones CONFIRMADAS» *** *
> *** «Y DICE LA COBERTURA» ***                              -> *** «con... COBERTURA» *** *
> *** y «SIN_DATO: list[str]» ***                            -> *** «las que no declaran nutricion, APARTE Y CON SU
>                                                              NOMBRE» *** *
> ```
>
> *** O sea: **el encargo no pide nada que este docstring no diga** *** -- *y **lo dice mejor**, *porque **explica
> por que.** *

## 3. *** Y su ultima frase es LA MEJOR DEL PROYECTO, y es la doctrina entera ***

> *** «Anotar las que se puede y CALLAR LAS DEMAS *** *** CONVERTIRIA UN DATO QUE FALTA EN UNA COMIDA QUE PARECE
> COMPLETA. *** ***» *
>
> *** Y **ahi estan las veintitres formas, en una frase**: ***
> ```
> *** «un dato que falta» ***     -> *`null` · `NO_LO_SE` · `sin_precio` · `DESCONOCIDO` · `ABSTIENE` *
> *** «una comida que parece completa» *** -> *** y eso es LO QUE HAY QUE EVITAR: *el hueco RELLENADO CON APARIENCIA
>                                    DE PLENITUD *** *
> *** y «CONVERTIRIA» ***           -> *y **la conversion es el fallo**: *no **omitir**, *sino *** TRANSFORMAR** *
> ```
>
> *** Y **es la misma frase que el encargo usa para Lidl**: *** *«no presentes **ausencias de captura** como
> **indisponibilidad**» -- *o sea: *no **conviertas un dato que falta** en **una conclusion que parece firme.** *
>
> *** Y **la misma que `formato.ts`**: *** *«**un dato que no tenemos es "no lo se", nunca un cero**. *Un **0,00 €** se
> lee como **"gratis"** y **una letra vacía** como **"malo"**; *las dos cosas serian **mentira**.» *
>
> *** O sea: **la misma doctrina, dicha para el dinero, para el catalogo, y para la nutricion** *** -- *y **las tres
> veces con la misma palabra: MENTIRA.** *

## 4. Y **los tres puentes, juntos, son el ciclo entero del encargo**

```
*** RECETA -> LISTA ***  `GET/POST /api/recetas/{id}/a-la-lista`
   *la lista es **de texto**: `300 g tomate` entra como linea (o **se dice** en `sin_cantidad`)*

*** PLAN -> LISTA ***    `GET/POST /api/listas/{id}/desde-el-plan`
   *y aqui **se busca el producto en el catalogo**: si no esta -> *** `sin_catalogo: ["tomate"]` ***

*** COMPRA -> DIARIO *** `GET/POST /api/listas/{id}/desde-la-compra`   *<- *** y este es el de CONSUMIR *** *
   *** «el diario rechaza `compra` a proposito -- comprar no es comer --, asi que esto PROPONE y LA PERSONA
   CONFIRMA» *** *y *** `sin_dato` *** *con las lineas sin nutricion, **aparte y con su nombre** *
```

> *** O sea: *** *** **el ciclo entero esta montado, y cada puente dice lo que no sabe** ***:
> *`sin_cantidad` · `sin_catalogo` · `sin_consolidar` · `sin_dato` · `cobertura`. *
>
> *** Y **los tres son `GET` de vista previa + `POST` de accion** *** -- *o sea: *** *** **siempre se puede mirar antes
> de escribir**, *y **eso es lo que permite medir sin inventar.** *
>
> *** Y **el encargo nombra **dos** puentes** *** -- *y **hay **tres**, y **el tercero es el que cierra el ciclo**:
> *el plan calcula **la prevision**, *y **este propone lo que se ha **consumido** -- *que **es la frontera que el
> encargo dibuja: «compra no es consumo».** *

## 5. Y el estado, con el ciclo entero localizado y **dos puentes medidos**

```
*** RECETA -> LISTA ***   -> *** MEDIDO ***: `300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"`
*** PLAN -> LISTA ***     -> *** MEDIDO ***: POST 201, `anadidos: 0`, `sin_catalogo: ["tomate"]`, persiste
*** COMPRA -> DIARIO ***  -> *** LOCALIZADO *** (`main.py:1679/1719`), *y **su docstring dice el contrato entero** *
   *** y NO se ha ejecutado *** -- *porque **necesita una compra cerrada con lineas**, *y **la lista de ensayo
   tiene 0 lineas** (el tomate no tiene catalogo). *
   *** -> o sea: **el tercer puente no se puede probar sin un catalogo**, *y **el catalogo es la fuente de B01/B02**,
   *y **el contenedor no lo tiene** (`/datos:ro` tiene el crudo, y **el catalogo vive en la API**). *
```

> *** Y **no se declara un fallo** *** -- *se declara **que el tercer puente tiene su contrato escrito, y que
> probarlo necesita una compra real.** *
