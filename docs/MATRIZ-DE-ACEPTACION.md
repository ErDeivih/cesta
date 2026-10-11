# Matriz de aceptación: uso doméstico local contra despliegue público

**G13, punto 232**, que lo pide con estas palabras: *«Diferenciar limitaciones de uso doméstico de
requisitos pendientes de despliegue público: TLS, cookies/CSRF según entorno, secretos, backups
automatizados, acceso, límites, observabilidad y obligaciones de fuentes. **No publicar nada en este
encargo.**»*

**Y la regla que se sigue al escribirla**: *cada celda dice **implementado** o **verificado**, que no
es lo mismo, y cuando no se ha comprobado se escribe **no verificado** en vez de suponerlo.* **Una
matriz que declara verde lo que nadie ha ejercitado no es una aceptación: es una promesa.**

---

## Las dos columnas

**«Doméstico local»** quiere decir: *se usa desde la casa, en la red de casa, con la base de casa, y lo
que se rompe se arregla el mismo día.* **«Antes de publicar»** quiere decir: *lo que habría que
resolver para que lo usara alguien de fuera, o para que un fallo no cueste datos.* *Son dos listas
distintas, y mezclarlas es lo que hace que un proyecto doméstico parezca inseguro y uno publicado
parezca terminado.*

---

## 1. TLS

| | |
|---|---|
| **Doméstico local** | **No hace falta, y no está.** *Se sirve por `http://localhost:5175` en la misma máquina; no hay tráfico que salga de casa ni nada que escuchar en el cable.* |
| **Antes de publicar** | **Hace falta.** *Certificado, renovación y redirección de http a https.* **Y no basta con «hay TLS»: hay que decidir qué se hace con las cookies al pasar a `Secure`.** |

## 2. Cookies y CSRF

| | |
|---|---|
| **Doméstico local** | **Implementado**: hay sesión con cookie (`POST /api/entrar`) y cada mutación comprueba el dueño en el servidor (`_acceso(lista_id, usuario, hace_falta_escribir=True)`, `usuario_actual`). *El endpoint del 221 comprueba el dueño con `almacen.listas_de` y no con lo que manda el cliente.* |
| **Antes de publicar** | **CSRF: no verificado.** *No he comprobado si las mutaciones exigen un token o si se apoyan sólo en `SameSite`; con el navegador y el servidor en el mismo origen da igual, **y con un dominio de verdad deja de dar igual**.* **Es la casilla que no se puede cerrar por lectura: hay que probarla.** |

## 3. Secretos

| | |
|---|---|
| **Doméstico local** | **Implementado y verificado por búsqueda** (598 ficheros versionados, 19 coincidencias, todas revisadas): `.env` **está ignorado**, `docker-compose.yml` toma la clave de `${CESTA_CLAVE_DB}`, `prueba_e2e.py` y `avisos.py` usan plantillas (`{clave}`), y **nueve ficheros de pruebas apuntan a la base desechable del 5434**. |
| **Antes de publicar** | **Un hallazgo que conviene nombrar**: `plataforma/api/ajustes.py:30` trae `postgresql://cesta:cesta@` **como valor por defecto**. *Es un valor de conveniencia para un contenedor de la máquina de casa, y el compose lo sustituye por la variable* — **no es un incidente, pero el 231 avisa de que «rotación requiere coordinación, no reutilización en documentación»**: *un secreto repetido en muchos sitios es un secreto que cuesta rotar.* |

## 4. Copias de seguridad

| | |
|---|---|
| **Doméstico local** | **El ensayo existe y es de verdad**: `plataforma/prueba_copia.py` levanta un PostgreSQL desechable (**5434**), corre el ensayo de punta a punta con datos reales, **vuelca** con `pg_dump`, levanta un entorno **separado** (**5435**), **restaura**, **comprueba el contenido** -- incluida una sustitución confirmada con su producto y su cadena -- y recoge. *«Una copia que nunca se ha restaurado no es una copia: es un fichero del que se supone que lo es.»* Y `plataforma/respaldar.bat` hace el volcado diario. |
| **Antes de publicar** | **Automatizar, retener y sacar de la máquina.** *Hoy el ensayo se lanza a mano y el volcado se queda en `data/`, que está ignorado por git pero vive en el mismo disco que la base.* **Una copia en el mismo disco no protege de lo que más pasa: que el disco falle.** |

## 5. Acceso y cuentas

| | |
|---|---|
| **Doméstico local** | **Implementado**: cada consulta lleva `propietario` en la firma (`_de_quien`, `listar(con, propietario, …)`) y **el aislamiento entre cuentas se prueba**. *«Una receta necesita dueño: el recetario es personal.»* |
| **Antes de publicar** | **No verificado**: *alta de usuarios, recuperación de contraseña, límite de intentos y bloqueo.* **Y hay una regla del encargo que no se puede relajar al publicar**: *«registros legado conservados sin propietario no se asignan por conveniencia»* — **un dato huérfano se queda huérfano, no se le da un dueño para que la consulta cuadre.** |

## 6. Límites de uso

| | |
|---|---|
| **Doméstico local** | **Implementado**: `config.RITMO` declara una espera por cadena (*Lidl a 1,0; Alcampo a 0,15 por el corte medido*), `core/runlock.py` impide dos ejecuciones a la vez, y **`fichas_lidl.LIMITE_POR_EJECUCION` tiene un presupuesto con plazo** (5.026 pendientes, 6 ejecuciones). |
| **Antes de publicar** | **Límites por usuario y no por proceso**, y una política escrita de qué se hace cuando una fuente bloquea. *Hoy el límite protege a la fuente de nosotros; al publicar habría que proteger también la máquina de los usuarios.* |

## 7. Observabilidad

| | |
|---|---|
| **Doméstico local** | **Implementado**: `docs/OPERACION.md` (1.241 líneas) documenta el arranque, la escalera de ejecución por fases, **«la marca del día: qué quiere decir "ha ido bien"»**, el runbook (*«qué hago yo cuando algo se rompe»*) y **los fallos que siguen sin arreglar** (*«Fallo 2: el motor de Docker Desktop (sin arreglar)»*). Y `/api/estado` declara la vigencia del catálogo comparando dos fechas. |
| **Antes de publicar** | **Métricas y avisos que no dependan de que alguien mire.** *Hoy la observabilidad es un documento y una pantalla: sirve si alguien la abre.* |

## 8. Obligaciones con las fuentes

| | |
|---|---|
| **Doméstico local** | **Registrado y verificado**: `docs/LIDL.md` dice en una línea que **«lidl.es no publica precios de alimentación»**, y `COMPETENCIA.md` añade que se **comprobó con fichas reales**; el respeto a `robots` está escrito; y **`Mecanica.SIN_REGLA` trata lo que no entiende como si no hubiera oferta**, que es «el error seguro». *No se elude un bloqueo ni se inventa un dato para cumplir una cifra.* |
| **Antes de publicar** | **Nada de esto cambia al publicar, y por eso conviene decirlo**: *las obligaciones son las mismas con un usuario o con cien.* **Lo que cambia es la escala del daño si se incumplen** — *y ahí sí hace falta una decisión explícita, no una costumbre.* |

---

## Lo que esta matriz NO dice

**No dice que la aplicación esté lista para publicar**, porque no lo está: *la mitad de la columna
derecha son cosas sin hacer y una —CSRF— sin verificar.*

**Y no dice que sea insegura para uso doméstico**, porque las casillas de la izquierda que importan
—dueño comprobado en el servidor, secretos fuera del repositorio, copia que se restaura y se
comprueba— **están implementadas y con evidencia**.

**Lo que dice es lo que el 232 pide**: *que las dos listas sean dos listas.* **Un proyecto doméstico
con TLS y alta de usuarios sería tiempo perdido; uno publicado sin CSRF verificado y con la copia en el
mismo disco sería un problema esperando.** *Y confundir las dos columnas es cómo se acaba sin ninguna
de las dos.*
