# B00 — Verificación del estado al empezar el encargo del 13 de octubre

*(13 de octubre de 2026, ~11:50. **Lo primero que manda el GOAL: «verifica la ingesta activa, runlock,
estado publicado, Docker, git y guardas de los ensayos».**)*

## 1. La ingesta: **sigue corriendo, y las dos cadenas siguen sin hacerse**

```
tarea «Cesta diaria»: estado=RUNNING · ultima=10/13/2026 10:59:53 · resultado=2147946720
carrefour: 10-11 12:38    <- 11 de octubre
alcampo:   10-11 12:45    <- 11 de octubre
```

*Cincuenta minutos corriendo y las dos cadenas que faltan siguen con dato del 11.* **No se ha duplicado ni
detenido**, como pide el encargo.

## 2. Runlock: **el fichero es viejo, y eso no quiere decir nada**

```
data/ejecucion.lock: modificado 09-07 12:19
```

> *Ojo con la conclusión fácil*: **`runlock` usa un cerrojo del sistema operativo, no la fecha del
> fichero.** *La prueba es que mi intento de lanzar una segunda ingesta **se rechazó** hace un rato* — *o
> sea que el cerrojo **está tomado**, aunque el fichero tenga meses.*
>
> **La fecha no es la señal; el rechazo lo es.**

## 3. Estado publicado: **no se puede comprobar**

```
/api/estado             -> URLError
/api/estado/publicacion -> URLError
```

## 4. Docker: **caído**

```
docker info -> error during connect: ... The system cannot find the file specified
8080: NADA · 5432: NADA · 5434: NADA
```

**Docker Desktop no está corriendo.** *Y eso tiene tres consecuencias concretas:*

- **la API y la web están caídas**, así que **el estado publicado no se puede verificar**;
- **la base de pruebas (5434) está caída**, así que **`pytest` no puede correr**;
- la base de casa (5432) también.

**Y una cosa que NO se sigue de ahí**: *el scraper **no necesita Docker*** — *escribe ficheros en bronze* —,
**así que la tarea puede estar corriendo con Docker caído.** *Que es justo lo que se ve.* **No es una
contradicción: son dos cosas distintas.**

## 5. Git: los ficheros del dueño, y los nuevos

```
M  core/datos/secciones.yml
M  docs/CIFRAS.md
M  docs/SUPERAPP-EJECUCION.md          <- tocado por el dueño ahora
M  docs/SUPERAPP-ESTADO.md             <- tocado por el dueño ahora
M  docs/SUPERAPP-GOAL-CONTINUACION-2026-10-11.md
?? docs/SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md
```

*No se tocan: son suyos.*

## Lo que esto dice para el plan

**El paso 3 de B00 —verificar el estado publicado— no se puede hacer sin levantar Docker.** **Y el paso 4
—las guardas de los ensayos— tampoco**, porque la base de pruebas está en el 5434.

**Pero el encargo dice: «Continúa trabajo independiente si falta una fuente o una decisión puntual».** *Y
hay un trabajo independiente de todo esto, que además es **la prioridad declarada***:

> **El fallo de los dos puentes.** *«300 g necesarios terminan como una unidad y una nota de 100 g,
> descartando la segunda receta como repetida.»*
>
> **Eso es código puro** — *en `core/previa_compra.py` y en el puente del plan* — **y no necesita ni Docker
> ni la ingesta.**

**Así que la continuación es: levantar Docker para poder medir, y mientras, ir al fallo de los puentes.**


---

## 6. Docker, levantado — **y las cuatro puertas, por primera vez**

*(13 de octubre de 2026. **La ronda 1 dejo dicho que Docker estaba caido y que los pasos 3 y 4 de B00 no se
podian hacer. Ya se pueden.**)*

### Lo que estaba parado, y como se levanto

```
Docker Desktop.exe            -> existe (C:\Program Files\Docker\Docker\Docker Desktop.exe)
proceso de Docker Desktop     -> NO estaba corriendo
servicio com.docker.service   -> Stopped
```

**Se arranco `Docker Desktop.exe`** -- *accion de usuario normal, sin elevacion* -- **y el motor respondio en
el primer intento.** *Los contenedores del compose volvieron solos: `cesta-web-1`, `cesta-api-1`,
`cesta-db-1` y `facylf-postgres`, los cuatro sanos.*

### Y faltaba uno: **el de pruebas, que se lo habia llevado el reinicio**

```
8080: en pie · 5432: en pie · 5433: en pie · 5434: NADA
```

**`cesta-prueba-db` no existia.** *Y la causa esta escrita en `docs/OPERACION.md:13`*: la orden con la que
se crea lleva **`--rm`**:

```
docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
    -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
```

> **`--rm` quiere decir que el contenedor se retira cuando para** -- *asi que al apagar Docker Desktop se
> fue, y con el su base.* **No es un fallo: es lo que la orden pide.** *Pero conviene saberlo, porque
> `pytest` no puede correr sin el.*

### Y las cuentas de los ensayos, que hay que volver a crear

*La base nueva nace vacia, asi que los ensayos que buscan una cuenta por su nombre se saltan* -- **17, con
este motivo:**

```
no hay cuenta de prueba y el alta tiene limite por hora agotado
```

**Se recrearon `prueba-navegador` y `recibo-de-prueba` con `almacen.crea_usuario`** -- *que no pasa por la
ruta HTTP y por tanto no toca el limite de altas.* *Es el mismo arreglo de la sesion anterior, y por el
mismo motivo.*

### Y ahora si: **las cuatro puertas, y sin nada saltado**

```
uv run ruff check .                    ->  All checks passed!                    (0)
uv run pytest -q                       ->  2012 passed, 0 skipped, 0 failed
cd plataforma/web/app ; npm test       ->  74 passed, 0 failed
npx --no-install tsc --noEmit          ->  0
```

**Y el estado publicado, que en la ronda 1 no se pudo comprobar:**

```
/api/estado             -> version 20261012-162023 · fecha_datos 2026-10-11
                           coherente TRUE · huellas_en_el_puntero 6
/api/estado/publicacion -> coherente TRUE · no_cuadran []
```

> **Y esto es lo que acredita que el trabajo de B04 no ha roto nada fuera de los puentes.** *Las 59 pruebas
> del puente decian que los puentes estaban bien; **las 2012 dicen que el resto sigue bien tambien** --
> *que es una afirmacion distinta, y sin Docker no se podia hacer.*

### Y lo que sigue igual, que no hay que confundir

**La ingesta.** *La tarea `Cesta diaria` seguia corriendo al levantar Docker, y **`carrefour` y `alcampo`
siguen con dato del 11 de octubre**.* **Eso no lo arregla Docker.** *Sigue pendiente, y sin duplicar ni
detener nada.*
