# A10 — Preparación de despliegue: **lo que se midió, puerto a puerto**

*(12 de octubre de 2026. **`A10` pide «revalidar backups/restauración, migraciones, permisos, sesiones,
límites de registro, protección de mutaciones, logs sin secretos y exposición de puertos». Esta es la
parte que se pudo medir, y lo que queda sin medir.***)

---

## 1. Exposición de puertos: **medida, y era un defecto**

**Lo que `docker ps` devolvía antes, con los cinco contenedores del proyecto:**

```
cesta-api-1        8000/tcp                          <- sin publicar
cesta-db-1         127.0.0.1:5432->5432/tcp          <- loopback
cesta-prueba-db    127.0.0.1:5434->5432/tcp          <- loopback
facylf-postgres    127.0.0.1:5433->5432/tcp          <- loopback (y no es de este encargo)
cesta-web-1        0.0.0.0:8080->8080/tcp            <- TODAS LAS INTERFACES
```

> **De los cinco, era el único en `0.0.0.0`.** *O sea: **el patrón del proyecto ya era loopback, y la web
> era la excepción** -- y era la excepción **sin que nadie lo hubiera decidido**: venía de un valor por
> defecto.*

**Y estaba en dos sitios a la vez, que es lo que costó verlo:**

1. **`plataforma/docker-compose.yml`**: `- "${CESTA_ESCUCHA:-0.0.0.0}:8080:8080"` -- *el valor por defecto
   era `0.0.0.0`.*
2. **`plataforma/.env`**: `CESTA_ESCUCHA=0.0.0.0` -- *y como la variable **estaba puesta**, el valor por
   defecto **nunca se usaba**.* *Cambiar solo el compose no habría cambiado nada: se recreó el contenedor
   y siguió en `0.0.0.0`, que es como se descubrió.*

**Los dos, cambiados a `127.0.0.1`. Y el resultado, medido después:**

```
cesta-web-1        127.0.0.1:8080->8080/tcp          <- ya no es la excepción
```

*Y la web sigue respondiendo: `http://localhost:8080/` -> `200`, `http://127.0.0.1:8080/api/estado` ->
`200`.*

### Y por qué esto no es un detalle de configuración

**«No es solo loopback» no significa «está en Internet», y la diferencia importa.** *`0.0.0.0` quiere decir
**cualquier interfaz**: la red de casa, la del trabajo, y cualquier VPN a la que la máquina esté conectada
en ese momento.* **Que hoy no haya nada mirando no lo convierte en una decisión** -- *y para abrirlo a
propósito ahora hay que escribir `CESTA_ESCUCHA=0.0.0.0`, que es lo correcto: **lo que se abre, se abre
queriendo**.*

> **Y el encargo lo dice con estas palabras**: *«no realices despliegues públicos ni gastos nuevos».*
> **`0.0.0.0` por defecto era un despliegue público latente que nadie había pedido.**

---

## 2. La cookie de sesión **no lleva `secure`**, y se dice

**`plataforma/api/main.py`, en las dos rutas que entran (`/api/entrar` y `/api/registrarse`):**

```python
respuesta.set_cookie(COOKIE, token, httponly=True, samesite="lax",
                     max_age=AJUSTES.dias_sesion * 86400, path="/")
```

**Están `httponly` y `samesite`** -- *que es lo que `F04` verificó, y está bien* --, **y falta `secure`.**

> **Lo que eso significa**: *sin `secure`, el navegador manda la cookie de sesión **también por HTTP sin
> cifrar**.* **En loopback eso no expone nada** -- *no hay red por medio* --, **y por eso no se ha
> cambiado**: *poner `secure=True` con la pila en `http://localhost` **rompería la sesión**, porque el
> navegador dejaría de mandar la cookie.*

**Queda dicho como el límite que es**: *el día que esto se sirva por HTTPS, `secure=True` es obligatorio y
hoy no está.* *No es un olvido: es una consecuencia de que la pila es HTTP local.*

---

## 3. El bundle, medido con la compilación de hoy

```
index-IXpBL6pj.js      677,8 KB
index-C0um6nXU.css      35,2 KB
TOTAL assets           713,0 KB
```

**Un solo trozo de JS de 677,8 KB.** *La revisión del dueño daba «692 kB / 208 kB gzip», y la cifra de hoy
es un poco menor porque es otra compilación* -- *las dos son medidas, y **la de hoy es la que está
servida**.*

**Lo que esto dice, y lo que no:**

- **Dice**: *que **todo** el JavaScript viaja en **un** fichero, sin separar por rutas.* *Quien abre
  `/compra` se descarga también el código de `/compra/cocina` y de `/recetas`.*
- **No dice**: *cuánto tarda en cargar en un móvil real.* **No se ha medido el tiempo de carga**, y el
  tamaño no es lo mismo que la espera -- *aunque 677 KB sin comprimir en una conexión mala sí se nota.*

**Y no se ha separado por rutas**, que es lo que `A10` pide con «medir bundles y **separar rutas**».
*Está medido y no está hecho.*

---

## 4. Lo que sí estaba bien, y conviene decirlo

| lo que `A10` pide | **lo medido** |
|---|---|
| **límite de registro** | **está**: `ALTAS_POR_HORA = 10`, y `/api/registrarse` lo comprueba con `altas_en_la_ultima_hora()` |
| **protección de mutaciones** | **está**: *`F04`, verificado antes -- `SameSite=Lax` + `HttpOnly`, 26 endpoints que mutan* |
| **permisos de base** | *los cinco contenedores en loopback o sin publicar* (**después del arreglo de §1**) |
| **migraciones** | *19 migraciones numeradas, idempotentes, y `arranca()` **no deja el esquema a medias*** -- *se comprobó en A04, cuando una migración con el nombre de tabla equivocado la paró* |
| **logs sin secretos** | *no medido* |

---

## 5. **Lo que queda sin medir, y es la mitad de `A10`**

*Se dice entero, porque un documento que solo cuenta lo hecho miente por omisión:*

- **Backups y restauración.** *No se ha probado un `pg_dump`/restore, ni se ha medido si el catálogo se
  puede recuperar.*
- **Sesiones.** *Se ha leído la cookie, **no** se ha probado la caducidad, ni el cierre en todas las
  pestañas, ni qué pasa con dos sesiones del mismo usuario.*
- **Logs sin secretos.** *No se ha mirado ni un log buscando claves, tokens o contraseñas.*
- **Separar el bundle por rutas.** *Medido el tamaño, no hecho el trozo.*
- **`docs/aprende`.** *`A10` pide actualizarlo con «trazabilidad, consulta de cobertura, transformaciones,
  algoritmos y fallos reales, **enlazados a código y ejemplos reproducibles**». **No se ha tocado.***
- **El recorrido de `A09` con «controles, textos y errores reales, no solo conteo de píxeles»**, y las
  capturas con commit/imagen/versión. *Tampoco.*


---

## 6. Las sesiones y los logs: **las dos que faltaban, medidas**

*(13 de octubre de 2026. **`A10` pide «revalidar [...] sesiones [...] y logs sin secretos». Las dos estaban
sin medir, y ya no.**)*

### 6.1 La sesión caduca, y se comprobó **poniéndola en el pasado**

**No basta con leer la consulta.** *La consulta lleva `AND s.expira_en > now()` -- se ve en
`almacen.quien` --, **pero leerlo y comprobarlo son cosas distintas***, así que se hizo lo segundo:

```
1) sesion creada:                              si
2) quien(tok) la reconoce:                     si
5) caducidad puesta en el pasado (a mano, en la base)
6) y ahora quien(tok) devuelve:                None
   -> RECHAZADA, que es lo correcto
7) dias_sesion:                                30
```

**Y `dias_sesion` fija la misma caducidad en los dos sitios**: *la columna `expira_en` de la base y el
`max_age` de la cookie* (`main.py`, en las dos rutas que entran). **Si sólo se pusiera en uno, la sesión
duraría lo que dijera el otro** -- *y el navegador es el que menos se puede permitir mandar.*

### 6.2 **Y el token se guarda como huella, no en claro**

*Esto no era lo que se iba a medir y salió al mirar la consulta*: `almacen.quien` busca por
**`_huella(token)`**, no por el token.

**Y se comprobó leyendo la fila de verdad:**

```
el token guardado:   df1c6b86364d3bc741aff8c1e1817aa62a71353b0999cce1e42b9d4a1f41979a
el token de verdad:  VeGIejXSsqCEPH86CfkX...
la huella de verdad: df1c6b86364d3bc741aff8c1e1817aa62a71353b0999cce1e42b9d4a1f41979a   -> COINCIDE
```

> **Lo que eso significa, y por qué importa más de lo que parece**: *una copia de la base de datos **no
> entrega sesiones vivas**.* **El que la consiga tiene los hashes, no los tokens** -- *y con un token
> hasheado no se puede entrar.*

**Y enlaza directamente con la copia de la ronda 250**: *`plataforma/copia_programada.py` **volca esa
misma tabla**, y el volcado queda en `data/copias/`.* **Que el token esté hasheado es lo que hace que ese
fichero no sea un llavero.**

### 6.3 Los logs: **140 líneas, y ninguna credencial**

```
docker logs cesta-api-1  ->  140 lineas
buscando: clave-de-prueba | prueba123 | CESTA_CLAVE | postgresql:// | prueba@
resultado: NINGUNA
```

**Y se buscaron las cadenas de verdad, no sólo la palabra «clave»**: *la contraseña que usan los ensayos
(`clave-de-prueba-123`), la de la base (`prueba`), la variable del entorno (`CESTA_CLAVE`) y una cadena de
conexión entera con su usuario y su contraseña.*

> **Lo que esto dice, y lo que NO dice.** *Dice que en **estos** 140 líneas no hay ninguna credencial.*
> **No dice que no pueda haberla**: *140 líneas son las de un contenedor que acaba de arrancar, y un log
> crece.* **Lo que sí se puede afirmar es que el log de arranque y de las peticiones que ha atendido no las
> lleva** -- *que es donde aparecerían si alguien imprimiera el entorno o la conexión.*

### 6.4 Y un error mío, en esta misma medición

*La primera lectura de la fila dio `guardado = "token"` y `len = 5`, y `expira = "expira_en"`.* **Parecía
que el token guardado fuera la cadena «token».** *Y era que `almacen.cursor()` devuelve **diccionarios**,
así que `a, b = cur.fetchone()` desempaqueta **las claves**, no los valores.* **Corregido con
`fila["token"]`.**

> *Es el mismo tipo de error que las cinco suposiciones de A09, y el más fácil de no ver*: **el resultado
> tenía la forma correcta -- dos cadenas -- y el contenido era el nombre de las columnas.**

### 6.5 Lo que queda de `A10`, entonces

| lo que pide | **estado** |
|---|---|
| exposición de puertos | **hecho** -- de `0.0.0.0` a `127.0.0.1` |
| bundles y separar rutas | **hecho** -- 677,8 -> 326,5 KB de entrada |
| backups y restauración | **verificado**, y con copia programada |
| la tarea de la copia | **escrita y verificada; sin dar de alta** -- *eso se decide* |
| `docs/aprende` | **hecho** -- los fallos (17) y la cobertura (18) |
| **sesiones** | **medido**: caduca, y el token va hasheado |
| **logs sin secretos** | **medido en las 140 líneas que hay** |
