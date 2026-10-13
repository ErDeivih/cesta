# Traspaso — 12 de octubre de 2026, al parar la sesión

**Por qué existe.** *El dueño para la sesión.* **Esto dice qué quedó hecho, qué quedó a medias, y la
acción siguiente exacta** -- *para que retomarlo no exija leer nueve documentos ni fiarse de la memoria.*

---

## 1. Lo primero: cómo está la máquina ahora

**Se pararon dos trabajos que estaban corriendo al parar:**

- **`pwsh-9853`** -- *la ingesta de `carrefour` y `alcampo`.* **Estaba corriendo sin haber escrito nada
  todavía** (*bronze seguía con dato del 11*). *Se paró **a propósito**: dejar un scraper de horas corriendo
  sin nadie delante no tiene sentido, y Alcampo pide un clic humano cuando su WAF se pone.*
- **`pwsh-7684`** -- *un `uvicorn` viejo en el **8100**, de una ronda muy anterior.*

**Y lo que sigue en pie, que es lo que se usa:**

| | |
|---|---|
| `cesta-web-1` | **`127.0.0.1:8080`** -- *la web, ya en loopback* |
| `cesta-api-1` | **imagen reconstruida**, con las correcciones de A01 |
| `cesta-db-1` | **`127.0.0.1:5432`**, la base de casa -- **intacta** |
| `cesta-prueba-db` | **`127.0.0.1:5434`**, la de las pruebas |
| `facylf-postgres` | **`127.0.0.1:5433`** -- **de otro encargo, no se ha tocado** |

---

## 2. El estado del catálogo, que es lo que más importa

```
/api/estado             -> version 20261012-162023 · fecha_datos 2026-10-11
                           vigencia_precio.coherente = TRUE · huellas_en_el_puntero = 6
/api/estado/publicacion -> coherente = TRUE · no_cuadran = []
```

**Se publicó una versión nueva con huellas, y `coherente` dejó de ser `None`.** *La versión nueva está
**aislada** -- un solo nombre en `fsutil hardlink list`.*

**Y lo que sigue faltando**: *los datos son del **11 de octubre**.* **La publicación arregló que se pueda
**comprobar** la coherencia; no trajo datos nuevos.**

```
alcampo     10-11 12:45    <- AYER
carrefour   10-11 12:38    <- AYER
aldi        10-12 12:26    <- HOY
mercadona   10-12 12:26    <- HOY
dia         10-12 12:37    <- HOY
```

---

## 3. Las puertas, y cómo se corren

```powershell
uv run ruff check .                                     # All checks passed!
$env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
uv run pytest -q                                        # 1999 passed, 0 failed, 0 skipped
cd plataforma/web/app ; npm test                        # 74 passed
npx --no-install tsc --noEmit                           # 0
npm run build                                           # built
```

**Y cero `xfail` en todo el proyecto.** *Las cinco que arrastraba la fase 2 están las cinco arregladas.*

---

## 4. **La acción siguiente exacta**

**Terminar la ingesta de las dos cadenas que faltan**, y **sin** el error que cometí:

```powershell
cd F:\aprendizaje\scrap
$env:PYTHONPATH = 'F:\aprendizaje\scrap'
# SIN `Select-Object`, que bufferiza y no deja ver avanzar.
uv run python -m projects.cesta.run --solo carrefour alcampo *>&1 |
    Tee-Object -FilePath data\debug\ingesta-dos.log
```

**Por qué así**: *la vez anterior le puse `Select-Object -Last 40` y **no se vio nada hasta el final*** --
*y encima me quejé de no poder verlo avanzar.*

**Cuánto tarda**: *una pasada de las dos son **horas** -- Carrefour tiene 16 195 filas y Alcampo 23 128, y
Alcampo va a **una petición cada 6,7 s**.*

**El límite que hay que esperar**: *Alcampo usa AWS WAF y **puede pedir un clic humano**.* **Si lo pide y
no hay nadie, Alcampo no se completa** -- *y Carrefour, que no necesita navegador, sí debería.*

**Cuando termine**, republicar y comprobar:

```powershell
uv run python -c "from core import publicacion as P; print(P.publicar()); print(P.version_actual())"
# y entonces /api/estado debe decir fecha_datos de hoy
```

---

## 5. Lo que queda, por peso

1. **La ingesta de las dos cadenas** -- *el punto 4, y es la única condición del veredicto que falta.*
2. **Una copia de la base fuera de la máquina.** *`plataforma/respaldar.bat` ya comprime, rechaza el
   vacío, tiene `restaurar` y retiene 30 días* -- **y no está dado de alta como tarea.**
   *Se dio de alta **por error** un `registrar-copia.ps1` mío, que **se retiró** al descubrir que
   `respaldar.bat` ya existía y era mejor.* **Lo que falta es una línea, y es una decisión:**
   ```powershell
   schtasks /create /tn "Cesta respaldo" /tr "F:\aprendizaje\scrap\plataforma\respaldar.bat" /sc daily /st 03:30
   ```
3. **El presupuesto de la cola de fichas**: *72 319 pendientes, **88 horas**, y **43 603 son de Alcampo**
   -- el 91,7 % del tiempo.* *Medido en `core/presupuesto.py`.* **Y el hallazgo**: *las 88 horas **no
   arreglarían** el hueco de nutrición, porque Alcampo no publica nutrición.*
4. **El universo de alimentos** está en `core/alimentos.py`, **con la cobertura medida** (28–30 % sobre
   comida, no 21,6 % sobre el catálogo). *Lo que falta de `A06` es el **inventario por campo y cadena**.*
5. **Los tres puntos que el veredicto deja sin medir**: *la caducidad de sesiones ya se midió; quedan
   **los logs con un log que crezca**, y **el recorrido de A09 con capturas versionadas** -- las capturas
   están, pero `data/` está ignorado en git.*

---

## 6. Lo que **no** hay que hacer, y por qué

- **No tocar `facylf-postgres` (el 5433)**: *es de otro encargo.*
- **No commitear** `core/datos/secciones.yml`, `docs/CIFRAS.md` ni
  `docs/SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`: *son cambios del dueño, y siguen sin commitear.*
- **No publicar nada hacia fuera**, ni abrir puertos: *la web está en loopback **porque A10 lo arregló**.*
- **No republicar `v20261007-103000` ni `v20261011-124542`**: *siguen compartiendo inodo con el gold
  suelto -- **es el daño que no se puede deshacer** --, y **republicarlas con el contenido de hoy sería
  mentir sobre lo que se publicó aquel día.**
- **Y no copiar cifras de un documento**: *en esta fase, la cifra de cobertura heredada hablaba de **48 606
  filas** cuando el universo tiene **52 087**; y la de la cola de fichas **sí cuadraba**.* **Hay que medir
  las dos.**

---

## 7. Los documentos, por si se quiere el detalle

| | |
|---|---|
| `docs/SUPERAPP-CIERRE-A01-A10.md` | *los diez paquetes, uno a uno, con lo hecho y lo que no* |
| `docs/MATRIZ-DE-ACEPTACION.md` | *doméstico local contra publicar, **con seis celdas medidas el 12 y el 13 de octubre*** |
| `docs/SUPERAPP-VEREDICTO-DOMESTICO.md` | *el veredicto: sirve con dos condiciones, y ninguna es del programa* |
| `docs/investigaciones/A10-despliegue.md` | *§1 a §7: puertos, bundle, copias, sesiones, logs, la cola* |
| `docs/investigaciones/A10-copias.md` | *la copia, con el daño que causé y lo que se arregló* |
| `docs/investigaciones/A01-publicacion-hecha.md` | *la publicación, y por qué las versiones viejas siguen contaminadas* |
| `docs/aprende/17-fallos-reales.md` | *seis fallos reales, con su reproducción* |
| `docs/aprende/18-cobertura-real.md` | *la cobertura medida, y el universo de alimentos* |

---

## 8. Y una cosa que hay que decir al retomar

**En esta fase me equivoqué nueve veces, y las nueve veces el código o el instrumento tenían razón:**

*Los cinco contratos de `almacen` · la vía de lectura de la autorización · el formato del descuento ·
`almacen.sesion` · `_dsn` · las claves del cursor · `write_parquet` · mi detector de texto · y `parents[1]`
contra `parents[2]`.*

**Y una de las nueve costó algo que no se recupera**: *al lanzar `prueba_copia.py` le pasé un
`CESTA_POSTGRES` que apuntaba a la base de pruebas, el ensayo rehízo el esquema, y **se perdieron 716
usuarios, 2 529 listas y 2 533 líneas**.*

> **La regla que sale de las nueve, y con la que conviene empezar la próxima vez**: *un documento se lee
> como un relato y **se comprueba como un inventario**.* **Y «no se nota» es una afirmación que hay que
> medir como cualquier otra** -- *la hice sobre el daño, y era falsa por diecisiete ensayos.*


---

## 9. Al retomar: **la tarea programada estaba corriendo sola**

*(13 de octubre de 2026, 11:14. **Y esto cambia la acción siguiente: no hay que lanzar nada.**)*

**Lo primero que pasó al retomar** fue lanzar la ingesta de `carrefour` y `alcampo` **como decía el punto
4**. *Y se negó a arrancar:*

```
[ejecucion] ya hay otra ejecucion de cesta en marcha
```

**Y no era un cerrojo viejo de la ejecución que yo había matado.** *Lo que había era esto:*

```
Cesta diaria:  estado = RUNNING   ·   ultima = 10/13/2026 10:59:53
python pid=33740  inicio 10-13 10:55     uv pid=36624  inicio 10-13 10:55
python pid=43424  inicio 10-13 10:55     python pid=30960  inicio 10-13 10:59
```

### Lo que había hecho la tarea por su cuenta, mientras la sesión estaba parada

```
aldi        10-13 10:57    <- HOY
dia         10-13 11:08    <- HOY
mercadona   10-13 10:57    <- HOY
carrefour   10-11 12:38    <- 11 de octubre, sin tocar
alcampo     10-11 12:45    <- 11 de octubre, sin tocar
```

**La tarea corrió a las 10:59:53 y **volvió a hacer las tres cadenas que ya había hecho**.** *Y a las 11:22
-- veintitrés minutos después -- **`carrefour` y `alcampo` seguían con dato del 11** y la tarea seguía
`Running`.*

> **Así que la acción siguiente del punto 4 está **mal planteada**, y conviene decirlo**: *no hay que lanzar
> la ingesta.* **Ya está lanzada, por la tarea programada, y `runlock` impide lanzar una segunda** -- *que
> es exactamente lo que debe hacer.*

### Lo que hay que hacer entonces, y es distinto

**Mirar, no lanzar.** *Y lo que hay que mirar es si la tarea llega a `carrefour` y `alcampo` o se queda por
el camino:*

```powershell
# 1. ¿sigue corriendo?
Get-ScheduledTask -TaskName "Cesta diaria" | Get-ScheduledTaskInfo

# 2. ¿ha escrito bronze?
Get-ChildItem dataronzeuente=carrefour,dataronzeuente=alcampo -Recurse -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 2

# 3. y si termino, republicar:
uv run python -c "from core import publicacion as P; print(P.publicar()); print(P.version_actual())"
```

### Y dos cosas que se aprendieron de esto

1. **`runlock` funcionó.** *Mi intento de lanzar una segunda ingesta se paró solo, y el mensaje decía por
   qué.* **Si no hubiera cerrojo, dos pasadas simultáneas sobre las mismas cadenas habrían escrito bronze a
   la vez** -- *y el WAF de Alcampo, que ya pide un clic humano, habría visto el doble de presión.*
2. **Y la tarea se dispara sola a las 06:00, al arrancar y al iniciar sesión.** *O sea que **el trabajo que
   el punto 4 mandaba lanzar ya estaba en marcha**, y yo iba a lanzarlo por segunda vez.*
   **Antes de lanzar una tarea programada, se mira si está corriendo** -- *que es la misma lección de
   `respaldar.bat` y de esta misma tarea, en otro sitio.*
