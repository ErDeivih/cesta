# B03 · **Las tres, comprobadas por HTTP.** La API reconstruida, y lo que eso significa

*(13 de octubre de 2026. **Se reconstruyo la imagen y se volvio a preguntar. Las tres salen.**)*

## 1. Y primero: el codigo esta dentro

```
$ docker compose build api   ->  Service api  Built
$ docker compose up -d api
$ docker exec cesta-api-1 grep -c '_cobertura' /app/plataforma/api/main.py
2
```

> **De `0` a `2`.** *Antes el contenedor no tenia la funcion; ahora si.* **Y eso es lo que hace que lo demas
> signifique algo.**

## 2. Las tres comprobaciones, por HTTP

### (1) y (2) -- `/api/estado`: Lidl esta, y con su cobertura

```
  alcampo    22816  (cataloga entero)
  aldi        2476  (cataloga entero)
  carrefour  16149  (cataloga entero)
  dia         5760  (cataloga entero)
  LIDL          77  <- ofertas_semanales_parcial · con_precio 77/79
                 aviso: «ofertas conocidas de Lidl, no su catalogo completo: no certifica stock, ni
                         identidad de producto, ni que un producto ausente se haya retirado»
  mercadona   4168  (cataloga entero)
```

> **Y ahi esta la diferencia que se buscaba desde hace ocho rondas**: *`77` **ya no esta solo***. *Lleva al lado
> `ofertas_semanales_parcial` y `con_precio 77 de 79`, **y su aviso**.*
>
> **Un `77` con eso es un dato; un `77` solo seria un catalogo pequeno.** *Y las otras cinco dicen
> `(cataloga entero)` -- **por ausencia de cobertura**, que es lo correcto: no se les inventa una.*

### (3) -- `en_tienda` admite `lidl`, de verdad

```
$ POST /api/listas/no-existe/tienda  {"cadena": "lidl"}
HTTP 401: {"detail":"Hay que entrar primero."}
```

> **Y ese `401` es la prueba.** *Antes de la ronda 31, esa misma peticion daba **`422`** -- «'lidl' no es una
> de las cadenas» --, **que es el veto.** *Ahora la puerta pasa y lo unico que falta es entrar.*
>
> **No es un `200`, y no se dice que lo sea**: *la lista no existe y no hay sesion.* **Pero lo que se estaba
> comprobando -- si el veto seguia puesto -- tiene respuesta: no.**

## 3. Y esto cierra el paso de API de B03

```
captura acotada                          HECHO
bronze con la zona acreditada            HECHO
cobertura por campo y contador visible   HECHO
bronze -> silver -> gold                 HECHO
en /api/estado como sexta fuente         HECHO, y con su cobertura
en_tienda la admite                      HECHO, comprobado por HTTP
```

## 4. Y la leccion de metodo, que es la de esta ronda

**Los tres cambios de este paquete se dieron por probados antes de estarlo:**

  - **el `aviso` en `en_tienda`** *-- en el repo, con pruebas verdes, y **no servido**;*
  - **la cobertura** *-- escrita, y **no servida**;*
  - **y los dos se dieron por buenos** *hasta que `grep` dijo `0`.*

> **`grep -c '_cobertura' /app/...` = `0` fue el dato que lo destapo.** *Una linea, en el sitio donde corre
> el codigo, y no donde se escribe.*
>
> **Y la regla que sale de esto vale para el resto del plan**: *«pasa las pruebas» y «el usuario lo ve» son
> dos afirmaciones distintas, y **la segunda necesita una peticion, no un commit**.* **Ni lo uno es lo otro,
> ni vale dar por hecho que un reinicio recarga un codigo que va dentro de una imagen.**

## 5. Y lo que queda de B03

  - **el horario de las 06:00** -- *que es la segunda mitad del punto 189 de G09, y donde el bronze ya haria
    entrar al colector.*
  - **region/club/fechas/nutricion/ausencias probadas EN EL RECORRIDO** *-- el bronze trae la region y las
    condiciones; falta comprobar que llegan a la UI.*
  - **y la parte de UI**: *`/api/estado` ya trae la cobertura; **la pantalla tiene que ensenarla**.*
