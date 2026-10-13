# B13 · **La estructura del ingrediente**: `texto` obligatorio, y **`cantidad`/`unidad` OPCIONALES**

*(13 de octubre de 2026. **Y es la pieza que explica el fallo del propietario, y por que el formulario de la web no lo tiene.**)*

## 1. Las dos formas, literales

```python
# plataforma/api/recetas.py:43
class IngredienteIn(BaseModel):
    *** texto: str = Field(min_length=1) ***     <- *** OBLIGATORIO ***
    *** cantidad: float | None = None ***         <- *** y OPCIONAL ***
    *** unidad: str | None = None ***             <- *** y OPCIONAL ***
    producto_id: str | None = None
    grupo_id: 
    fuente: str | None = None

class RecetaIn(BaseModel):
    nombre: str = Field(min_length=1)
    *** raciones: int = Field(default=2, ge=1) ***
    preparacion: str = ""
    ingredientes: *** list[IngredienteIn] *** = []
    minutos: int | None = Field(default=None, ge=0)
    etiquetas: str = ""
```

> *** O sea: *** *** **un ingrediente puede venir de DOS maneras**: ***
> ```
> *** A) SOLO TEXTO ***     -> *`{"texto": "300 g tomate"}`* *-- *y **la cantidad y la unidad se INTERPRETAN** *
> *** B) ESTRUCTURADO ***   -> *`{"texto": "tomate", "cantidad": 300, "unidad": "g"}`* *-- *y **se saben** *
> ```
>
> *** Y **es `identidad.RE_CANTIDAD` y `RE_PACK` (B12)** *** -- *o sea: **hay un parser** que lee «300 g tomate»
> *y **saca 300 y `g`.** *
>
> *** Y **cuando el parser acierta, da lo mismo por donde se metio**: *por eso **la previa dio `300.0 g`**
> *-- *porque **el `texto` se interpretó bien.** *
>
> *** Y **cuando el parser NO puede**, *es **`sin_cantidad`** -- *y el puente **lo dice** en vez de inventar. *

## 2. *** Y el formulario de la WEB manda **la forma A**, y por eso el parser es el que decide ***

```
*** EL FORMULARIO DE LA WEB *** (`/recetas`, ronda 237):
  *** text «Ingredientes, uno por linea» ***  ·  *** textbox «Ingredientes, uno por linea» ***
  *** /placeholder: «600 g patatas \n 5 ud huevos» ***
   -> *o sea: **UNA LINEA = UN INGREDIENTE**, *y **cada linea es TEXTO** *
   -> *** y la web manda `IngredienteIn` con SOLO `texto` *** -- *porque **no tiene campos de cantidad ni unidad.** *
```

> *** O sea: *** *** **cuando se crea una receta por la web, el ingrediente va como TEXTO, y el parser decide.** *
>
> *** Y **eso es lo que hace que el fallo del propietario sea posible**: *** *si el parser **lee «300 g» como
> «1 unidad»**, *entonces **el puente pide una unidad** *-- *y **es exactamente lo que el describio.** *
>
> *** Y **tambien explica por que el fallo NO aparece ahora**: *** *** el parser **lo lee bien** -- *y **esta medido**:
> *`"cantidad": 300.0, "unidad": "g"` (ronda 241). *
>
> *** O sea: *** *** **la restriccion del propietario vivia en el PARSER, y el parser esta bien.** *
> *Y **la prueba esta donde tenia que estar**: *en **una receta creada por la web**, *con **el texto**
> `300 g tomate`, *y **el puente saca 300 gramos.** *

## 3. Y **la forma B existe, y la web no la usa** -- y eso es un dato, no un fallo

```
*** LA API ACEPTA `cantidad` y `unidad` ESTRUCTURADOS ***
   -> *y **el formulario de la web NO los pide** *
   -> *** y eso es coherente con `Cesta.tsx:136-139`: *«LAS REGLAS VIVEN EN LA API... *** COPIAR AQUI EL MINIMO DE LA
      CLAVE SERIA UNA SEGUNDA COPIA QUE SE QUEDA VIEJA ***» *
   -> *o sea: **la web manda lo minimo** (el texto), *y **el parser -- que es del nucleo -- decide.** *
```

> *** Y **por eso el ingrediente tiene `texto` obligatorio y lo demas opcional**: *** *** es **la forma comoda para
> escribir** (una linea por ingrediente), *y **la estructurada para cuando se sabe.** *
>
> *** Y **es la misma doctrina que `producto_id`**: *** *si se sabe **de que producto es**, se pone; *y **si no,
> se deja `None`** -- *y **el puente lo dice** en `sin_catalogo`. *

## 4. Y **la prueba que cierra el circulo**, y que se puede hacer en una llamada

```
*** CREAR UNA RECETA CON LA FORMA B ***  *-- *o sea: *`{"nombre": ..., "ingredientes": [{"texto": "tomate",
"cantidad": 300, "unidad": "g"}], "raciones": 2}`*
   *** -> y su previa deberia dar `cantidad: 300.0, unidad: "g"` SIN PASAR POR EL PARSER *** *
   *** -> y si da lo mismo que la forma A, entonces las dos vias coinciden, y eso es lo que hay que saber. *** *
```

> *** Y **`_como_filas(ingredientes)`** (`recetas.py:78`) *es **la que convierte** `IngredienteIn` **en fila**,
> *y **`recetas.crear`** la guarda. *Asi que **las dos formas llegan al mismo sitio.** *

## 5. Y el estado, con una pieza mas del mapa

```
*** LA RESTRICCION DEL PROPIETARIO ***  -> *** medida por los dos puentes, y CORRECTA ***
   *** y ahora se sabe DONDE vivia: en el PARSER (`identidad.RE_CANTIDAD`), que lee el `texto`. *** *
*** y `300 g tomate` creado POR LA WEB dio `300.0 g` -> EL PARSER ACIERTA. ***
```

> *** Y **lo que queda de esta ronda**: *** *el `POST /api/recetas` **funciona** (201 para las 5 planificadas
> estaban 2; *y **las 3 nuevas no se crearon** porque **el `ingredientes` iba mal**, *y ahora se sabe como.) *
>
> *** y **el plan semanal** *** -- *que es **lo que la aceptacion pide**: *** *** «cinco recetas semanales» *** --
> *tiene **4 entradas**: *`Ensalada` el 12, *`Sopa` el 13, *y **las dos el 14.**
> *** -> o sea: **hay que crear tres mas y repartirlas**, *y **ya se sabe la forma exacta del ingrediente.** *
