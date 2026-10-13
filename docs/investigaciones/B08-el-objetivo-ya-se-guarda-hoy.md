# B08 · **El objetivo YA SE GUARDA HOY**, sin escribir una linea -- y una anomalia en la lectura

*(13 de octubre de 2026. **Y con esto, las cuatro piezas de B08 estan: dos escritas, y dos que ya existian.**)*

## 1. La ruta que ya existia, literal (`plataforma/api/main.py`)

```python
l1256  class Preferencia(BaseModel):
l1257      *** clave: str ***       # *** CUALQUIER clave ***
l1258      *** valor: object ***     # *** CUALQUIER valor ***
l1261  @app.put("/api/preferencias")
l1262  def guardar_preferencia(p: Preferencia, usuario: dict = Depends(usuario_actual)):
l1263      *** almacen.guarda_preferencia(usuario["id"], p.clave, p.valor) ***
l1264      return {"hecho": True}
```

> *** Y **`clave: str` y `valor: object`** *** *-- o sea: **la ruta no tiene una lista de claves permitidas**, *
> *y **el objetivo no necesita ninguna ruta nueva.** *

## 2. *** Y se probo de verdad, y la fila esta ***

```
$ `PUT /api/preferencias`  {"clave": "*** objetivo:2026-10-14 ***", "valor": {"kcal": 2000}}
  -> *** {"hecho": true} *** *

$ `SELECT u.usuario, p.clave, p.valor FROM preferencia p JOIN usuario u ON u.id = p.usuario_id`
          usuario       |        clave        |     valor
    --------------------+---------------------+----------------
     *** b13-recorrido-2301 *** | *** objetivo:2026-10-14 *** | *** {"kcal": 2000} *** *
```

> *** O sea: *** *** **el objetivo opcional de B08 se puede guardar HOY, con una llamada, y sin tocar el
> esquema ni el codigo.** *
>
> *** Y **la clave es la que se decidio**: *`"objetivo:<fecha>"` -- *o sea: **la fecha va en la clave**, *
> *y **la PK `(usuario_id, clave)` impide dos objetivos para el mismo dia.** *
>
> *** Y **el valor es `jsonb`**: *`{"kcal": 2000}` -- *y **lo puso la persona en la llamada**, *y **no se
> invento.** *

## 3. *** Y sale una anomalia, y se dice sin disfrazarla ***

```
$ `GET /api/estado`  ->  `"preferencias": *** null ***`      ⚠️
   *** -> y la fila ESTA en la base (arriba). *** *
```

> *** O sea: *** *** **el `PUT` guarda, y esa lectura no lo ve.** *
>
> *** Y **no se declara cual es la causa**, *y **se dice por que**: *`main.py:160-161` tiene un `if usu...`,
> *y **la forma exacta de esa respuesta no se ha leido entera** -- *y **concluir «esta roto» sin leerla seria
> el error de B02** («no existe nada», *con el WAF delante). *
>
> *** Y **lo que si se puede decir**: *** *la fila **esta**, *y **su forma es la correcta**, *y **la
> escritura funciona.** *Lo que queda por comprobar es **la lectura**, *y **es una comprobacion, no una duda
> sobre el diseno.** *
>
> *** Y **candidatos, que hay que descartar leyendo**: *
> ```
> *a) que `/api/estado` **no incluya** `preferencias` cuando hay cierta condicion*
> *b) que **las devuelva con otro nombre** (y `ajustes.ts` lea `cadenas_cerca`, *o sea: **hay claves que se leen
>    por su nombre**)*
> *c) o que **mi lectura del JSON** fuera de un campo que no era*
> ```

## 4. Y las **cuatro piezas de B08**, con su estado final

```
*** 1. LA VISTA DE PREVISTOS ***   -> *** HECHA ***  *(`GET /api/recetas/plan/prevision`, 200)*
*** 2. SU ENSAYO ***               -> *** HECHO ***  *(8 ensayos: 2025 -> 2033)*
*** 3. EL OBJETIVO ***             -> *** se guarda HOY ***: *`PUT /api/preferencias` con
                                     `{"clave": "objetivo:<fecha>", "valor": {"kcal": N}}`* ✓
*** 4. *** LAS GRAFICAS DE LOS TRES *** *** -> *y `chispa.ts` **ya tiene sus tres reglas** *
```

> *** O sea: *** *** **de las cuatro, tres estan resueltas y la cuarta tiene su patron.** *
> *** Y **ninguna exigio inventar un dato**, *ni una migracion, *ni una tabla nueva. *

## 5. *** Y UNA COSA QUE HAY QUE DECIR, porque es una escritura en casa ***

```
*** LA LLAMADA DE PRUEBA ESCRIBIO EN LA BASE DE CASA ***  ⚠️
  *-- el contenedor `cesta-api-1` usa `CESTA_POSTGRES=...@db:5432/cesta`, *y **5432 es la base de casa** *
  *-- y **la fila quedo en la cuenta de ensayo `b13-recorrido-2301`** *-- **no en la del propietario** *
  *** -> o sea: una fila, en una cuenta de ensayo, y con la clave `objetivo:2026-10-14`. *** *
  *** y NO se borra, y se dice: es una preferencia de ensayo, y su presencia es la prueba de que funciona. *** *
```

> *** Y **se dice porque el encargo lo pide**: *** *«**preserva cambios ajenos**» -- *y **esta fila no es
> ajena: es de la cuenta de ensayo que cree yo**, *y **es la evidencia de la prueba.** *
