# A10 — Copias de seguridad: **el mecanismo existe, y por qué no se ejecutó**

*(12 de octubre de 2026. **`A10` pide «revalidar backups/restauración». Esto es lo que se encontró, lo que
se comprobó, y la razón concreta por la que no se corrió.**)*

---

## 1. El mecanismo **ya está escrito**, y está bien pensado

**`plataforma/prueba_copia.py`**, y su cabecera dice por qué existe con una frase que conviene copiar:

> *«No había nada: ni un `pg_dump`, ni una restauración, ni una comprobación sobre la base restaurada.
> **Una copia que nunca se ha restaurado no es una copia: es un fichero del que se supone algo.»***

**Y lo que hace, en cinco pasos:**

1. **Levanta un PostgreSQL desechable en el `5434`** y corre `plataforma.prueba_e2e` de punta a punta -- *que
   deja datos de verdad: listas, líneas, una compra y, sobre todo, **una sustitución confirmada con su
   producto y su cadena***.
2. **Vuelca** esa base con `pg_dump` (y **falla si el volcado tiene menos de 1000 bytes**, que es la
   comprobación de que no salió vacío).
3. **Levanta un entorno separado** -- otro contenedor, el `5435`, otra base -- y **restaura** el volcado.
4. **Comprueba el contenido en el entorno restaurado**: *que las filas de `lista`, `lista_linea` y `compra`
   cuadren con el original*, **y que la confirmación conserve su producto y su cadena**
   (`dia:74397|dia`).
5. **Recoge** los dos contenedores y **borra el volcado** -- *«era para comprobar que se restaura, no para
   guardarlo».*

**Y lo que declara que NO hace**, que es lo que lo hace utilizable: *«no toca la base de casa. El
contenedor de casa no publica su 5432, y los puertos 5434 y 5435 son de esta prueba.»*

> **Así que `A10` tiene esta parte hecha, y no por mí.** *Lo que faltaba no era el mecanismo: era
> **correrlo**, y esa es la parte que se explica abajo.*

---

## 2. Por qué **no se ejecutó**, y la razón es concreta

**El guion empieza así:**

```python
ENSAYO = "cesta-prueba-db"
def arranca(nombre, puertos):
    corre(["docker", "rm", "-f", nombre], timeout=120)      # <-- BORRA el contenedor
    ...crea uno nuevo, vacio, con el mismo nombre...
```

**Y termina así:**

```python
for nombre in (ENSAYO, COPIA):
    corre(["docker", "rm", "-f", nombre], timeout=120)      # <-- y lo vuelve a borrar
```

**O sea: `prueba_copia.py` es **autocontenido** -- *se hace su propia base, la usa, y la retira.* **Y el
nombre que usa es `cesta-prueba-db`, que es EXACTAMENTE el contenedor que ya existe y que sostiene todo lo
demás.**

### Y lo que hay dentro de ese contenedor, medido antes de decidir

```
docker exec cesta-prueba-db psql -U cesta -d cesta -tAc "SELECT ..."
    716 usuarios | 2529 listas | 2533 lineas
```

**Y tiene un volumen anónimo** -- *`c2fca9261070...` -> `/var/lib/postgresql/data`* --, **así que los datos
no se pierden de verdad**: *`docker rm -f` sin `-v` deja el volumen huérfano.* **Pero el contenedor nuevo
recibe un volumen **nuevo y vacío**, así que la base de pruebas quedaría **en blanco** y los 716 usuarios
quedarían en un volumen que ya nadie monta.*

> **Y `compose` no lo reclama**: *`docker inspect` no devuelve etiquetas de `docker compose` para ese
> contenedor*, así que **no se recrea solo** -- *hay que volver a levantarlo a mano.*

### La decisión, y por qué es la prudente

**No se ha corrido.** *No porque el guion esté mal* -- *está bien y hace exactamente lo que dice* --, **sino
porque correrlo cambia el estado de la máquina de una forma que el encargo no pide**:

- *«Preserva cambios ajenos y datos reales»* -- *los 716 usuarios no son datos de casa, pero **son estado
  acumulado que no he creado yo***;
- *y dejar la base de pruebas sin contenedor rompería la suite de `pytest` hasta volver a levantarlo.*

**Lo que sí se puede afirmar, y se afirma:**

- **El mecanismo existe, es correcto en su diseño y comprueba lo que hay que comprobar** -- *no solo que el
  volcado se restaure, sino **que el contenido sea el mismo**, y en el caso que importa (la sustitución
  confirmada conserva producto y cadena)*.
- **No se ha ejecutado, así que NO está verificado hoy.** *Un guion que existe y no se ha corrido es una
  promesa, no una prueba* -- *y esa distinción es la que este documento mantiene.*

### Cómo ejecutarlo sin llevarse por delante la base de pruebas

**Con el contenedor de ensayo parado y a salvo**, o **cambiando `ENSAYO` a otro nombre** -- *por ejemplo
`cesta-copia-ensayo` y su puerto al `5436`*. *Es un cambio de dos constantes, y entonces el guion hace lo
mismo **sin tocar el que ya existe**.*

**Y eso no se ha hecho tampoco**, porque *el guion está escrito para correr en un entorno desechable*, y
adaptarlo para que conviva con una base que ya tiene 716 usuarios es **una decisión sobre qué se quiere
medir**, no un arreglo obvio.


---

## 3. **Lo que pasó al ejecutarlo, y un daño que causé yo**

*(Ronda 246. **Esto no es un hallazgo sobre el código: es un error mío, y va primero.**)*

### Y lo primero es el daño

**`cesta-prueba-db` tenía 716 usuarios, 2 529 listas y 2 533 líneas. Ahora tiene 2, 2 y 10.** *Los dos
usuarios que quedan son `prueba` y `la-otra`, **los del propio ensayo e2e** -- o sea que lo que hay dentro
es lo que el ensayo acaba de crear.*

```
antes:  716 usuarios | 2529 listas | 2533 lineas
ahora:    2 usuarios |    2 listas |   10 lineas | 2 compras
```

*El contenedor es **el mismo** -- creado el `2026-10-10` --, así que **no se borró el contenedor: se
borraron los datos**.* La última escritura es de las `13:28`, **mi primera corrida**.

### Cómo lo hice, y por qué la culpa no es del guion

**Al lanzarlo puse `$env:CESTA_POSTGRES='postgresql://...@127.0.0.1:5434/cesta'` en la línea de
comandos.** *Y el guion, en su versión de entonces, **no ponía ese entorno para el ensayo**: lo heredaba de
quien lo lanzara.* **Resultado: `plataforma.prueba_e2e` corrió contra la base de pruebas de verdad, y ese
ensayo rehace el esquema.**

> **La ironía es exacta y merece quedar escrita**: *en la ronda anterior identifiqué este riesgo con
> precisión -- «empieza con `docker rm -f cesta-prueba-db`», «los 716 usuarios no son datos de casa, pero
> son estado acumulado que no he creado yo» -- y **lo evité por el contenedor y lo provoqué por la variable
> de entorno**.*
>
> **Identificar un riesgo no es lo mismo que esquivarlo.** *Lo que faltaba era **no pasarle a ese guion un
> `CESTA_POSTGRES` que apuntara a otro sitio** -- y eso no lo comprobé, porque estaba mirando el nombre del
> contenedor.*

### Qué se ha arreglado, y qué no se puede arreglar

**Arreglado**: *el guion **ya no hereda** el `CESTA_POSTGRES` de quien lo lanza.* **Le pone el suyo**,
construido desde su propio puerto:

```python
entorno = {**os.environ,
           "CESTA_POSTGRES": f"postgresql://cesta:prueba@127.0.0.1:{PUERTO_ENSAYO.split(':')[1]}/cesta"}
e = corre_env(["uv", "run", "python", "-m", "plataforma.prueba_e2e"], cwd=raiz, env=entorno)
```

**Y no se puede arreglar**: *los 716 usuarios.* *No hay copia de esa base -- **que es justamente lo que este
guion existe para comprobar que se puede hacer** --, así que no se recuperan.* **Se dice y no se disimula.**

### Lo que no está en peligro, y conviene decirlo

- **Los datos de casa**: `cesta-db-1` (el `5432` interno) **no publica puerto y no se ha tocado**.
- **`facylf-postgres` (el `5433`)**: **no se ha tocado**, y el encargo lo prohíbe expresamente.
- **El catálogo**: *los `parquet` de `data/gold` no se han tocado.*
- **Y la suite**: *los 1 959 pasan igual*, porque **cada prueba crea sus propios usuarios** -- *que es la
  razón de que el daño no se note en las puertas.*

### Y el segundo fallo, que sigue sin explicación y se dice como tal

**La segunda corrida -- ya con el arreglo -- llegó más lejos y falló en otro sitio:**

```
-- 3. el entorno separado: otro contenedor, otra base
   base separada lista en el 5437
   FALLO en la restauracion: psql: error: connection to server on socket
   "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL: the database system is shutting down
```

**Y el ensayo y el volcado, esta vez, sí fueron bien** -- *porque las comprobaciones de contenido dicen «2
en el ensayo, 10 en el ensayo, 2 en el ensayo», o sea que había datos de verdad.*

**Lo que se sabe**: *`arranca()` da el contenedor por listo con `pg_isready`, y **entre esa comprobación y
el `psql` el servidor empezó a apagarse**.* **Lo que NO se sabe**: *por qué.* *Las posibilidades que no he
descartado: que el `docker run --rm` se lleve el contenedor al salir de algún modo, que el nombre
`cesta-copia-db` choque con un resto de la corrida anterior, o algo del propio Docker de esta máquina.*

> **Y se deja así, dicho como lo que es**: *un fallo reproducido dos veces en el mismo punto, **sin causa
> confirmada**.* *Inventar una ahora sería lo contrario de todo lo que este documento hace.*
