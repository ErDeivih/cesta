# B02 · **Los dos sitios, leidos** -- y sin conclusion

*(13 de octubre de 2026. **Se hizo lo que la ronda 107 dijo: leer antes de concluir. Y esta vez no se concluye.**)*

## 1. `RetoWAF`, medido

```
projects/cesta/collectors/alcampo.py:100:  class RetoWAF(Exception):
projects/cesta/collectors/alcampo.py:94:            raise RetoWAF(ruta) from None
projects/cesta/collectors/alcampo.py:241:                raise RetoWAF(clave) from None
projects/cesta/collectors/alcampo.py:247:        raise RetoWAF("api-categories")
projects/cesta/collectors/alcampo.py:290:                raise RetoWAF(str(cat_id)) from None
projects/cesta/collectors/alcampo.py:296:        raise RetoWAF(str(cat_id))
projects/cesta/collectors/alcampo.py:315:            raise RetoWAF("terminos") from None
projects/cesta/collectors/alcampo.py:319:        raise RetoWAF("terminos")
```

**Lo que esto dice, y nada mas:**

  - **es una excepcion propia de Alcampo**, *no del `core`* -- **no se comparte con los otros cinco**;
  - **y se lanza desde sitios distintos** *-- la ruta, una clave, `api-categories`, una categoria concreta,
    `terminos` --*, **y cada uno con su nombre**;
  - *o sea: **Alcampo sabe donde le cortaron**, y **lo dice**.*

## 2. `ESTADOS_DE_BLOQUEO`, medido

```
projects/cesta/collectors/carrefour.py:69:   ESTADOS_DE_BLOQUEO = (403, 429)
projects/cesta/collectors/carrefour.py:528:  if ultimo_fallo.get(c) in ESTADOS_DE_BLOQUEO)
```

**Y aqui hay que corregir la ronda 107, que dijo «una linea y nada mas»:** *se **usa**, en la 528, sobre
`ultimo_fallo`.* **Asi que Carrefour **si** hace algo con el bloqueo** -- *no solo lo nombra.*

> **Lo que no se sabe todavia, y no se va a suponer**: *que hay **alrededor** de la 528.* *Una linea no dice si
> eso **evita pedir**, **reintenta**, **marca** o **deja de guardar** -- y **las cuatro cosas son distintas**.*

## 3. Y esta ronda no concluye, a proposito

*Las rondas 105, 106 y 107 dieron **tres conclusiones falsas seguidas**, y las tres por escribir antes de leer.*
**Asi que esta deja los dos hechos y se para.**

> **Lo que hay, dicho sin adornos:**
>
>   - **Alcampo tiene una excepcion propia de desafio** *(`RetoWAF`, 13 usos)*, **un avance minimo**
>     *(`AVANCE_MINIMO`)*, **limites con nombre** *(`CORTES_PARA_RENDIRSE`, `MAX_RENOVACIONES`)* **y un
>     `detener`** *-- con un mensaje que dice «hoy el WAF nos tiene fichados».*
>   - **Carrefour tiene una tupla de estados de bloqueo** *-- 403 y 429 --* **y la usa en un sitio.**
>   - **y los otros cuatro colectores**: *no se ha mirado, y **no se dice nada de ellos**.*
>
> **Eso es todo lo que se sabe.** *Y es mas de lo que se sabia hace tres rondas, porque ahora esta **leido**.*

## 4. Y lo que hace falta para poder concluir algo

**Tres lecturas, y ninguna es un `grep`:**

```
  1) alcampo.py 700-830 ENTERO      -- el bucle de categorias y donde encaja RetoWAF
  2) carrefour.py 500-545 ENTERO    -- que hay alrededor de la 528
  3) y los ENSAYOS de colectores que ya existan -- porque dicen que se considera
     comportamiento correcto hoy, que es la mitad de lo que B02 pide probar
```

> *Y la tercera es la que mas informa y la que menos se ha mirado.* **Un paquete que pide «aceptar fixtures» no se
> diseña sin ver **que ensayos hay ya** -- *porque si ya hay fixtures, B02 es ampliarlos; y si no hay ninguno,
> B02 es crearlos, que es otra cosa.*
>
> **Eso no se sabe. Y se puede saber leyendo.**
