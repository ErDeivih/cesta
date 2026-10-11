# F01 · Identidad estable: el consumidor que quedaba ligado al ordinal

Estado: **encontrado y localizado; sin arreglar**. Fecha: 13 de octubre de 2026.
Origen: hallazgo #9 de la revisión (*«Riesgo de identidad estable»*) y la mitad pendiente de F01.

> *«Tablero describe grupos ordinales renumerados y migración a producto estable; informe da G10 cerrado
> por lectura. → **Prueba lista/favorito/receta sobreviviendo a reordenación** y separación de grupos.
> **Resolver cualquier consumidor aún ligado a ordinal.**»*

---

## 1. La mitad «resolver consumidores»: **encontrada, y hay uno**

**Primero se comprobó que no hubiera consumidores _de código_**, con `git grep`: las tres menciones del
ordinal del grupo son **comentarios** (`catalogo.py:777`, `cesta.py:908`, `main.py:671`), y dos de ellos
dicen justo lo que el hallazgo avisa. *Ningún código trata el ordinal como identidad.*

**Pero el esquema sí distingue, y ahí está el hallazgo:**

```
plataforma/sql/001_esquema.sql:98    linea:    grupo_id bigint,  producto_id text
plataforma/sql/001_esquema.sql:109   CONSTRAINT linea_con_destino  CHECK (grupo_id IS NOT NULL OR producto_id IS NOT NULL)
plataforma/sql/001_esquema.sql:126   favorito: grupo_id bigint,  producto_id text
plataforma/sql/001_esquema.sql:129   CONSTRAINT favorito_con_destino
plataforma/sql/001_esquema.sql:136   alerta:
plataforma/sql/001_esquema.sql:139       grupo_id  bigint NOT NULL      <- SOLO el ordinal
```

**`linea` y `favorito` guardan las dos referencias** -- *y por eso pueden apuntar a un producto estable
(la migración 015 y el trabajo de F01 van por ahí)* --. **`alerta` guarda `grupo_id` y nada más, y encima
`NOT NULL`.**

## 2. Y por qué eso importa, medido

**`grupo_id` es un ordinal que el emparejador renumera en cada pasada.** *No es una interpretación: lo dice
el propio código, en tres sitios, y uno de ellos lo explica como advertencia:*

```
plataforma/api/main.py:671    # `grupo_id` es un ordinal que el emparejador renumera en cada pasada, asi...
plataforma/api/cesta.py:908   # ordinal que se renumera en cada pasada, asi que esta linea puede e...
plataforma/api/catalogo.py:777 **Esto es el sintoma de que `grupo_id` es un ordinal, no una identidad...
```

**Así que una alerta creada para «el grupo 5000» puede, tras una reordenación, estar vigilando otro
producto.** *Y como las alertas son de bajada de precio, el fallo es silencioso y del peor tipo:* **la
persona recibe un aviso de un producto que no pidió, o deja de recibirlo del que sí, y nada se lo dice.**

**`favorito` y `linea` no tienen ese problema porque tienen `producto_id`.** *`alerta` no.*

## 3. Lo que NO se ha hecho

1. **El arreglo.** *La dirección es la misma que ya se siguió con `linea` y `favorito`: dar a `alerta` una
   referencia al producto estable, con su `CHECK` de «una u otra».* **No se ha escrito la migración.**
2. **La prueba** de lista/favorito/receta sobreviviendo a una reordenación, que es la otra mitad del
   hallazgo. *Y ojo: **la lista y el favorito sí pueden pasar esa prueba hoy** -- tienen `producto_id` --,
   pero **no se ha demostrado**, y **la alerta no podría**.*
3. **Y una pregunta que hay que contestar antes de tocar `alerta`**: *una alerta «de este grupo» ¿es
   legítimamente del grupo -- «vigila este producto, se llame como se llame» -- o siempre debería ser de un
   producto?* **De la respuesta depende si `alerta` necesita las dos columnas o sólo cambiar de una a
   otra.** *No la contesto yo.*

## 4. Lo que se puede afirmar hoy

**El hallazgo #9 tenía razón, y su mitad «resolver consumidores» da un caso concreto**: *`alerta` está
ligada al ordinal, `linea` y `favorito` no, y el ordinal se renumera.* **No es una hipótesis del tablero:
está en el esquema y lo avisa el propio código.**

*Y es el único caso de los nueve hallazgos de F00 que ha resultado ser **un defecto localizado y no
arreglado**, en vez de un cierre insuficiente ya cubierto.*
