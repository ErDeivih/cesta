# B05 · **El fichero entero, por sus nombres**: y tiene **ensayo propio**

*(13 de octubre de 2026. **Segunda ronda de B05. Y con los nombres ya se puede decir casi todo.**)*

## 1. Lo que hay en `core/traspaso.py`, por sus nombres

```
l33:  class Operacion                    -- la identidad: propietario + receta_id + version + semana
l41:      def clave(self) -> str         -- y su clave, que es lo que se guarda
l45:  def semana_de(hoy=None) -> str      -- *** la semana la calcula el SERVIDOR ***
l56:  def id_de_linea(lista_id, clave) -> str   -- *** LA IDEMPOTENCIA DE LA LINEA DE LISTA ***
l73:  def _migra(con) -> None             -- y hay migracion (o sea: hay tabla)
l89:  def pasar_a_lista(...)              -- el traspaso
```

> *** Y `id_de_linea(lista_id, clave)` es exactamente lo que B05 pide: ***
>
> *una linea de lista **no se identifica por su contenido** (que seria «200 g de harina»), **sino por
> `(lista, clave-de-operacion)`**.* *Asi que **repetir la operacion produce el mismo `id`, y la segunda vez se
> pisa** -- *que es «repetir no duplica» -- y **otra semana tiene otra clave, asi que produce otro `id`, y se
> anade** -- *que es «otra semana si».*
>
> *** Las dos mitades del criterio de G12, resueltas con una funcion de tres palabras. ***

## 2. Y tiene dos ensayos

```
tests/test_g12_traspaso.py          <- EL SUYO
tests/test_b04_los_dos_puentes.py   <- y el de B04, porque el traspaso es uno de los dos puentes
```

> **Un fichero de core con su ensayo dedicado y con nombre de punto del encargo (`g12`).** *No es codigo suelto: es
> **una pieza del contrato, con su prueba**.*

## 3. Y `_migra(con)` dice algo que hay que anotar

**`_migra(con: sqlite3.Connection)`** *-- o sea: **el traspaso tiene su propia tabla**, y **se migra**.*

> *Que es lo que hace posible la idempotencia: **la operacion se apunta en algun sitio**, no se deduce de las lineas.*
>
> *** Y eso contesta la pregunta dificil del criterio -- «misma clave con contenido distinto» -- sin comparar
> contenido: **si la operacion ya esta apuntada, no se vuelve a hacer; y si el contenido que se iba a escribir es
> distinto, es que la operacion se repitio con otros datos, y eso hay que decirlo, no ignorarlo**.*
>
> *Que es **justo** «conflicto, no exito ficticio» -- *y **no se ha leido el cuerpo**, asi que **no se dice que lo
> haga**: se dice que **la tabla y la migracion estan, y que eso es lo que las hace posibles**.*

## 4. Y el balance honesto de las dos rondas de B05

```
RONDA 131:  el criterio desglosado, doce ficheros localizados, el orden escrito   -- sin abrir ninguno
RONDA 132:  `core/traspaso.py` abierto: su docstring entero, y sus seis nombres  -- y DOS ensayos
```

> **Y en dos rondas se ha establecido lo que en B02 costo diez**: *que **el nucleo del paquete ya esta**, **con su
> razonamiento escrito**, **con su ensayo**, y **con la parte dificil resuelta por diseño** -- *no usando el
> contenido como clave.*
>
> *** La diferencia no es que B05 sea mas facil: es que **se empezo mirando**, y **el docstring del proyecto
> contesta las preguntas que uno iba a hacerse.**

## 5. Y lo que queda por leer, dicho, sin concluir

```
POR LEER:
  - el CUERPO de `pasar_a_lista` y de `_migra` (105 lineas menos los nombres)
  - `tests/test_g12_traspaso.py` -- que dice QUE SE CONSIDERA CORRECTO HOY (y es lo que mas informa)
  - `plataforma/api/almacen.py` (58,4 KB) -- el almacen, donde vive la idempotencia de las LISTAS
  - `core/manifiesto.py` y `core/publicacion.py` -- el recibo de una publicacion
  - y los otros cuatro ficheros de la lista de doce
```

> *** Y el siguiente, por lo que informa: `tests/test_g12_traspaso.py`. *** *Porque **los nombres de los ensayos
> son la documentacion que no miente** -- *y es lo que encontro, en B02, que Lidl era el unico de los seis sin
> registro.*
