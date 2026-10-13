# B03 · **La zona es del usuario, y no es solo Lidl** -- la respuesta a la pregunta del propietario

*(13 de octubre de 2026. **Se pregunto por la region de Lidl, y la respuesta fue un diseno mejor que el que
iba a implementar**: «que dependa de la region que elija el usuario, o en la que se encuentre en ese
momento. Verifica si esto le pasa a mas supermercados o solo a Lidl, para mejorar la experiencia del
usuario.»)*

## 1. La respuesta, medida: **no es solo Lidl**

*Menciones de region/tienda y de codigo postal en cada colector:*

```
mercadona    region/tienda: 10    codigo postal:  6
aldi         region/tienda: 12    codigo postal: 11
alcampo      region/tienda:  4    codigo postal:  0
lidl         region/tienda: 25    codigo postal:  1
carrefour    region/tienda:  2    codigo postal:  0
dia          region/tienda:  1    codigo postal:  1
```

**Cuatro de seis tienen el concepto.** *Y los dos que mas lo usan -- Aldi y Mercadona -- son los que mas
mencionan el codigo postal.*

### Y en Mercadona esta explicito, con su motivo

`projects/cesta/collectors/mercadona.py`:

> *«`PUT /api/postal-codes/actions/change-pc/` fija el almacen. **Los precios varian por almacen, asi que se
> fija el CP antes de recorrer nada.**»*

```python
json={"new_postal_code": config.CODIGO_POSTAL},
```

### Y en Aldi tambien

*«...las tiendas ubicadas en las Islas Baleares» en el 99,3 % de los casos* -- *de ahi `ALDI_SCOPE`.*

## 2. **Y la zona del usuario YA EXISTE, y ya es configurable**

`core/config.py`:

```python
# tu zona: fija el almacen de Mercadona y el ambito de Aldi
CODIGO_POSTAL = os.environ.get("SCRAP_CP", "28001")
ALDI_SCOPE = os.environ.get("SCRAP_ALDI_SCOPE", "es_pen")   # es_pen | es_bal | es_can
```

> **«Tu zona».** *Con esas dos palabras.* **Y son dos variables de entorno, o sea que se cambian sin tocar
> codigo.** *El patron que el propietario pide **ya esta inventado en este proyecto**, y **lo usan dos de los
> seis colectores**.*

**Lo que NO existe es que Lidl lo use.** *Y no es un olvido: es que **la correspondencia no esta acreditada**
-- *el `--region` de Lidl es un identificador de `regionsV2` (un numero), y **un codigo postal no es ese
numero**.* **Que es exactamente lo que el plan prohibe suponer.**

## 3. Y la correspondencia **se puede acreditar**, que es lo que faltaba saber

*La captura viva trae **55 regiones con nombre**, dentro del propio dato:*

```
 1 A Coruña     26 Barcelona    42 Cadiz       53 Fuerteventura   59 Ibiza
 5 Asturias     27 Girona       43 Cordoba     51 Ceuta           57 Cat 2
13 Burgos       29 Caceres      46 Granada     35 Albacete        ...
```

> **Asi que la correspondencia no hay que inventarla: hay que CONSTRUIRLA con los nombres que la propia
> fuente publica.** *Un CP -> provincia es un dato administrativo conocido; provincia -> `regionPriceId` sale
> **de esta tabla, que la publica Lidl**.* **Y asi la eleccion queda acreditada por el dato, no por un
> codigo postal supuesto.**

**Y `REGION_POR_DEFECTO = "28"`** -- *que el propio colector comenta asi:* **«la unica observada; NO ES LA
ZONA DEL HOGAR DE NADIE»**. *Es un valor tecnico para poder ejecutar, y el colector se niega a publicar con
el.*

## 4. El diseno que sale de esto, y es el que el propietario pide

**Hoy**: *Mercadona y Aldi leen `config.CODIGO_POSTAL`; **Lidl tiene una constante «28» que no es de nadie**;
Carrefour, DIA y Alcampo no miran la zona.*

**Lo que corresponde**:

  1. **La zona es UNA, del usuario, y ya esta en `config`.** *No se anade otra variable: se usa la que hay.*
  2. **Lidl deriva su `--region` del CP**, *por la tabla de nombres que la propia captura publica* -- **y si un
     CP no se puede mapear, se dice `region_desconocida` y no se publica**, *como ya hace el piloto.*
  3. **Y las otras tres** (*Carrefour, DIA, Alcampo*): **comprobar si publican precio por zona** -- *y si lo
     publican y hoy no se usa, es una mejora de la experiencia, no un detalle.*
  4. **Y se dice en la interfaz**: *que precio es de que zona, y cuando no se sabe.* *Es la regla de toda la
     fase: un precio sin su zona es un precio que no se puede comparar.*

## 5. Lo que **no** se ha hecho, y por que

**No se ha escrito el bronze de Lidl.** *Y ahora se sabe que era correcto no escribirlo: **elegir «28» habria
publicado precios de una zona que no es la del usuario*** -- *y ese es exactamente el dato que hay que
acreditar, no suponer.*

**No se ha tocado `config`.** *El diseno esta escrito y medido; **el cambio de codigo es el paso siguiente**, y
tiene que llevar su prueba: *que la region salga del CP, que un CP no mapeable diga `region_desconocida`, y
que no se publique bronze sin region acreditada.*
