# B03 · **La zona en la comparacion: intentado, medido, y revertido**

*(13 de octubre de 2026. **Se probo la forma que parecia segura, rompio seis pruebas, y se deshizo.**)*

## 1. Lo que se intento, y por que parecia seguro

*El problema, ya escrito:* **`donde_comprar` compara precios de zonas distintas como si fueran la misma**, *y
elegir «la mas barata» puede dar un ganador que no existe.*

*Y el obstaculo que aparco el intento anterior era*: **la consulta devuelve una tupla posicional, y anadir un
campo desplaza los indices aguas abajo.**

*Asi que se busco la forma que no desplaza nada:* **anadir `region` AL FINAL del `SELECT`.**

```sql
SELECT grupo_id, NULL, fuente, fuente || ':' || id_fuente, nombre,
       precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca,
       region                                    -- <- el once
  FROM grupos ...
```

> **Y el razonamiento era bueno**: *los diez campos de antes no se mueven, asi que **ningun indice de los que
> ya se leen cambia de sitio**.* *Un campo nuevo se anade al final **o** se toca cada lectura: se eligio lo
> primero.*

## 2. Y rompio seis pruebas

```
FAILED tests/test_cantidades_repetidas.py::test_el_candidato_elegido_no_depende_de_como_se_repartan_las_lineas
FAILED tests/test_g01_recibo_del_puente.py::test_el_recibo_dice_lo_que_se_anoto_y_lo_que_no
FAILED tests/test_g01_recibo_del_puente.py::test_una_linea_ajena_se_devuelve_en_vez_de_ignorarse
FAILED tests/test_g01_recibo_del_puente.py::test_una_linea_con_nutricion... (y tres mas)
FAILED tests/test_g03_cierre.py::test_con_la_sustitucion_aceptada_se_archiva_el_precio_de_su_tienda
FAILED tests/test_g03_cierre.py::test_el_cierre_archiva_el_producto_que_puso_el_precio
```

> **Seis, y de tres ficheros distintos** -- `cantidades_repetidas`, `g01_recibo_del_puente` y `g03_cierre`.
> *O sea que **no era una lectura de indice**: era algo mas de fondo.*

## 3. Y se revirtio, que es lo que habia que hacer

**Con el contexto que queda, parchear a ciegas seis fallos en la funcion mas central del paquete seria
temerario.** *Asi que se deshizo el cambio y se comprobo que el arbol volvia a estar bien:*

```
git checkout -- plataforma/api/cesta.py
pytest -q  ->  2019 pasan, 0 fallan
```

> **Y esto es lo que la ronda 48 decia que habia que hacer, hecho de verdad**: *«no empezar lo que no se puede
> terminar bien».* **Solo que esta vez se empezo -- porque la forma parecia segura -- y al ver el resultado se
> deshizo.** *Que es mejor que no haberlo intentado: **ahora se sabe algo que antes no se sabia.***

## 4. Y lo que se sabe ahora, que es nuevo

**Que el problema NO son los indices.** *Eso era la hipotesis de la ronda 48, y **queda refutada**: anadir el
campo al final no mueve ningun indice, y aun asi se rompen seis pruebas.*

> **Asi que la causa esta en otra parte**, y hay tres candidatos que ahora se pueden mirar **sin adivinar**:
>
>   1. **algo hace `zip` con los nombres de las columnas** *y espera diez*;
>   2. **o `region` choca con un nombre que ya existe** *en la vista o en alguna consulta intermedia*;
>   3. **o el numero de columnas del `SELECT` se comprueba en algun sitio** -- *un `assert` o un contrato de
>      forma.*
>
> **Y `tests/test_g01_recibo_del_puente.py` es por donde empezar**: *el recibo del puente es justo lo que
> cuenta **que** se anoto y **que** no, y un fallo ahi apunta a un contrato de forma.*

## 5. Y el valor de esto, que no es cero

**Se ha acotado el problema en dos direcciones:**

  - **la forma segura de anadir el campo existe** *-- al final --*, **y sigue disponible**;
  - **y la causa no es la que se creia**, *que era la unica razon por la que este cambio llevaba tres rondas
    aparcado.*

> *Aparcarlo estaba bien mientras la razon fuera la duda.* **Ahora hay una razon mejor: hay seis pruebas que
> dicen exactamente donde mirar.** *Y eso se puede retomar en una ronda, con el contexto entero, en vez de a
> ciegas al final de esta.*

## 6. Estado de B03

```
LA ZONA EN LA COMPARACION   PENDIENTE
  - la forma segura de anadirla: AL FINAL del SELECT (probado: no mueve indices)
  - y la causa de los seis fallos: NO son los indices -- hay que mirarla
  - por donde empezar: tests/test_g01_recibo_del_puente.py
```

*Todo lo demas de B03 esta hecho: la captura, el bronze con zona, la cobertura, silver, gold, la vista, la
API y la pasada diaria.*
