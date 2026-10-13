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
