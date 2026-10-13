# B03 · **El recorrido entero, medido por HTTP** -- despues de rehacer gold, el emparejamiento y publicar

*(13 de octubre de 2026. **La comprobacion de que dos reconstrucciones y tres publicaciones no rompieron nada.**)*

## 1. Lo que se midio

```
GET /api/estado    HTTP 200 · version 20261013-155356 · fecha_datos 2026-10-13

  alcampo       22816  (cataloga entero)
  aldi           2476  (cataloga entero)
  carrefour     16149  (cataloga entero)
  dia            5760  (cataloga entero)
  LIDL             77  ofertas_semanales_parcial      <- con su cobertura
  mercadona      4168  (cataloga entero)

GET /api/secciones  HTTP 200  (2 elementos)
GET /api/recetas    HTTP 401  (hay que entrar primero)
GET /api/listas     HTTP 401  (hay que entrar primero)
```

> **Las seis cadenas, con sus cifras, y la cobertura de Lidl** -- *despues de:*
>
>   - **el historico de gold rehecho** (ronda 46: *1643898 filas, 38 dias*);
>   - **el emparejamiento rehecho dos veces** (rondas 97 y 99: *443 s, 51725 productos, 22873 enlaces*);
>   - **y tres publicaciones** (`v20261013-134352`, `-135533`, `-155356`).
>
> **Y los numeros son los mismos de antes de todo eso** -- *que es lo que la ronda 46 se propuso comprobar y
> ahora se ha comprobado **en la API, no en el fichero**.*

## 2. Y las dos respuestas que parecen fallos y no lo son

**`/api/recetas` y `/api/listas` dan 401** -- *«hay que entrar primero».* **Que es lo correcto**: *son las rutas
con datos de una persona, y sin sesion no se sirven.* *No es una pantalla vacia: es una puerta.*

> *Y conviene decirlo, porque el objetivo pide «no considerar terminado lo que solo abrio una pantalla vacia»*:
> **un 401 no es una pantalla vacia** -- *es una ruta que existe y que pide lo que tiene que pedir.* *Lo que
> delataria una pantalla vacia seria un 200 con una lista de cero elementos.*

**Y `/api/donde?q=leche` dio 404** -- *porque **esa no es la ruta**: el nombre se invento al probar.* *Lo cual es,
en si, una comprobacion util: **el servidor no responde 200 a una ruta que no existe.***

## 3. Y lo que esto cierra de B03, que es su criterio de aceptacion entero

*El objetivo pide, para Lidl:*

> *«Integra Lidl en el MISMO ciclo diario y en API/UI como sexta fuente, con **ambito regional y cobertura
> demostrados**.»*

**Y esta medido:**

```
MISMO CICLO DIARIO   run.py, con su tabla de argumentos -- ya corre en la pasada
SEXTA FUENTE         /api/estado, con las seis y con las cifras cuadrando
AMBITO REGIONAL      la zona, de la web a la API: bronze 79/79 · silver 79/79 · gold 77/77
                     · grupos 79/79 · y 38961 grupos sin ninguno con dos zonas
COBERTURA            ofertas_semanales_parcial, dicha en la API y en la pantalla
```

*Y no «acreditado en el colector»: **medido en cada parada y comprobado por HTTP.***

## 4. Y lo unico que queda, que es una decision de presentacion

```
QUE `donde_comprar` HAGA ALGO CON LA ZONA -- Y `grupos` YA LA TIENE, Y LA API YA LA SIRVE.
  Decision escrita: que el precio que se elija sea de la zona del usuario,
  y decir cuando no haya con quien comparar.
  *Y hoy no cambia nada: solo Lidl declara zona, y es una sola.*
```

*O sea: **el dato esta donde hace falta y llega a quien lo necesita**; lo que falta es **que alguien lo mire**.*
*Que es la forma de hueco que este paquete lleva encontrando toda la sesion -- el `grupo_id`, el
`por_que_no_se_compara`, y ahora la zona --, y por eso se deja dicho con nombre.*
