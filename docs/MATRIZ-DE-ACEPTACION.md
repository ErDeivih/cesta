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
| **Doméstico local** | **No hace falta, y no está.** *Se sirve por `http://localhost:8080` en la misma máquina; no hay tráfico que salga de casa ni nada que escuchar en el cable.* **Y el 13 de octubre de 2026 se comprobó que es de verdad sólo local**: *de los cinco contenedores, **la web era el único en `0.0.0.0`** -- todas las interfaces -- y ahora está en `127.0.0.1`.* *Los otros cuatro ya estaban en loopback o sin publicar.* |
| **Antes de publicar** | **Hace falta.** *Certificado, renovación y redirección de http a https.* **Y no basta con «hay TLS»: hay que decidir qué se hace con las cookies al pasar a `Secure` -- y esa decisión ya se sabe cuál es, porque el estado de hoy está medido.** |

## 2. Cookies y CSRF

| | |
|---|---|
| **Doméstico local** | **Implementado**: hay sesión con cookie (`POST /api/entrar`) y cada mutación comprueba el dueño en el servidor (`_acceso(lista_id, usuario, hace_falta_escribir=True)`, `usuario_actual`). *El endpoint del 221 comprueba el dueño con `almacen.listas_de` y no con lo que manda el cliente.* **Y el 13 de octubre se midieron tres cosas más:** *la cookie lleva `httponly` y `samesite="lax"` y **no lleva `secure`** -- *correcto en HTTP local, obligatorio en HTTPS* --; **el token de sesión se guarda como huella SHA-256, no en claro** (`almacen._huella`), *así que un volcado de la base no entrega sesiones vivas*; y **se comprobó que la caducidad se aplica de verdad**, *poniendo `expira_en` en el pasado: `almacen.quien(token)` devuelve `None`.* |
| **Antes de publicar** | **Medido el 12 de octubre de 2026, y la respuesta no es la que la celda suponía: NO HAY TOKEN CSRF, y no hace falta uno con esta cookie.** *Lo que hay, comprobado contra la API servida:* la cookie sale con **`SameSite=lax`** -- *leído de su `Set-Cookie`* --, y **una mutación sin cookie devuelve `401`**. *Las dos cosas juntas son la defensa entera*: **un POST desde `evil.com` no lleva la cookie, porque `Lax` no la manda en peticiones de otro sitio, así que llega sin sesión y se rechaza.** *El navegador y el servidor se bastan sin token.*
| | **Lo que `SameSite=Lax` NO cubre, y hay que decirlo al publicar**: *un subdominio del mismo sitio* -- *`evil.ejemplo.com` contra `ejemplo.com` es «same-site», y ahí `Lax` no protege* --, **y los navegadores que no lo implementan.** *Lo primero se resuelve no compartiendo dominio con nadie; lo segundo, con un token de verdad.* **Y el `Max-Age` de la cookie son 30 días** (*`2592000` segundos*), *que coincide con `dias_sesion`: las dos mitades de la caducidad están puestas.* |

## 3. Secretos

| | |
|---|---|
| **Doméstico local** | **Implementado y verificado por búsqueda** (598 ficheros versionados, 19 coincidencias, todas revisadas): `.env` **está ignorado**, `docker-compose.yml` toma la clave de `${CESTA_CLAVE_DB}`, `prueba_e2e.py` y `avisos.py` usan plantillas (`{clave}`), y **nueve ficheros de pruebas apuntan a la base desechable del 5434**. |
| **Antes de publicar** | **Un hallazgo que conviene nombrar**: `plataforma/api/ajustes.py:30` trae `postgresql://cesta:cesta@` **como valor por defecto**. *Es un valor de conveniencia para un contenedor de la máquina de casa, y el compose lo sustituye por la variable* — **no es un incidente, pero el 231 avisa de que «rotación requiere coordinación, no reutilización en documentación»**: *un secreto repetido en muchos sitios es un secreto que cuesta rotar.* |

## 4. Copias de seguridad

| | |
|---|---|
| **Doméstico local** | **El ensayo existe y es de verdad**: `plataforma/prueba_copia.py` levanta un PostgreSQL desechable, corre el ensayo de punta a punta con datos reales, **vuelca** con `pg_dump`, levanta un entorno **separado**, **restaura**, **comprueba el contenido** -- incluida una sustitución confirmada con su producto y su cadena -- y recoge. *«Una copia que nunca se ha restaurado no es una copia: es un fichero del que se supone que lo es.»* Y `plataforma/respaldar.bat` hace el volcado diario: **comprime** (`.sql.gz`), **rechaza el volcado vacío** (*«un fichero de cero bytes es un respaldo que no lo es»*), **tiene `restaurar` con confirmación**, y **borra los de más de 30 días**. **Y el 13 de octubre el ensayo se ejecutó entero y pasó**: *volcado de 30 515 bytes, restaurado sin error, contenido 2/2 · 10/10 · 2/2, y `dia:74397\\|dia` conservado.* |
| **Antes de publicar** | **Sacar la copia de la máquina.** *Hoy el volcado se queda en `data/respaldos`, que vive en el mismo disco que la base.* **Una copia en el mismo disco no protege de lo que más pasa: que el disco falle.** *Y `respaldar.bat` **ya se puede dar de alta como tarea diaria** -- lo dice su propia cabecera --, así que eso no es trabajo pendiente: es una decisión.* |

## 5. Acceso y cuentas

| | |
|---|---|
| **Doméstico local** | **Implementado**: cada consulta lleva `propietario` en la firma (`_de_quien`, `listar(con, propietario, …)`) y **el aislamiento entre cuentas se prueba**. *«Una receta necesita dueño: el recetario es personal.»* **Y el 13 de octubre se midió el reparto de responsabilidad de la sustitución**: *`almacen.autoriza_linea` **no comprueba que el usuario sea de la lista** -- lo comprueba la ruta, con `_acceso` --, así que **la función de almacén confía en quien la llama y el permiso se comprueba en la puerta**.* *Está escrito y con prueba, porque un reparto no documentado es el que se rompe al añadir la siguiente ruta.* |
| **Antes de publicar** | **No verificado**: *recuperación de contraseña, límite de intentos y bloqueo.* **El límite de altas sí está y se midió**: `ALTAS_POR_HORA = 10`, comprobado en `/api/registrarse` -- *y se notó de verdad, porque al vaciarse la base de pruebas 17 ensayos empezaron a saltarse con «el alta tiene límite por hora agotado».* **Un límite que no se puede agotar no es un límite: es un adorno**, y éste se agota. |

## 6. Límites de uso

| | |
|---|---|
| **Doméstico local** | **Implementado**: `config.RITMO` declara una espera por cadena (*Lidl a 1,0; Alcampo a 0,15 por el corte medido*), `core/runlock.py` impide dos ejecuciones a la vez, y **`fichas_lidl.LIMITE_POR_EJECUCION` tiene un presupuesto con plazo**. **Y el 13 de octubre se midió la cola entera**, que es lo que le da escala a esos límites: *`data/inventario.sqlite`, **72 319 pendientes y 7 593 correctas** -- *y de las pendientes, **43 603 son de Alcampo, el 60 %**, y 5 026 de Lidl con sólo 28 hechas.* **La cola y la cobertura de nutrición cuentan la misma historia**: *las dos cadenas con la cola más parada son las dos que no aportan ni una caloría.* |
| **Antes de publicar** | **Límites por usuario y no por proceso**, y una política escrita de qué se hace cuando una fuente bloquea. *Hoy el límite protege a la fuente de nosotros; al publicar habría que proteger también la máquina de los usuarios.* **Y falta el presupuesto de la cola**: *cuánto cuesta una pasada de 72 319 fichas y cuántas caben por día* -- **no se ha estimado**, y sin eso «pendiente» no dice cuánto falta. |

## 7. Observabilidad

| | |
|---|---|
| **Doméstico local** | **Implementado**: `docs/OPERACION.md` (1.241 líneas) documenta el arranque, la escalera de ejecución por fases, **«la marca del día: qué quiere decir "ha ido bien"»**, el runbook (*«qué hago yo cuando algo se rompe»*) y **los fallos que siguen sin arreglar** (*«Fallo 2: el motor de Docker Desktop (sin arreglar)»*). Y `/api/estado` declara la vigencia del catálogo comparando dos fechas. **Y desde el 13 de octubre hay una segunda ruta que dice lo que las fechas no pueden**: `/api/estado/publicacion` compara **huellas SHA-256** y distingue **`bien`**, **`cambiado`** y **`sin_huella`** -- *con `coherente: None` cuando no hay con qué comprobarlo, en vez de un `True` que afirmaría lo que no consta.* *Hoy responde: `coherente: None`, `no_cuadran: []`, seis ficheros `sin_huella`.* |
| **Antes de publicar** | **Métricas y avisos que no dependan de que alguien mire.** *Hoy la observabilidad es un documento y una pantalla: sirve si alguien la abre.* **Y los logs se midieron**: *140 líneas de la API, buscando la contraseña de los ensayos, la de la base, la variable del entorno y una cadena de conexión entera -- **ninguna credencial**. Pero 140 líneas son las de un contenedor que acaba de arrancar: lo que se afirma es sobre esas, no sobre un log que crece.* |

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

---

## Lo que cambió esta matriz el 12 y el 13 de octubre de 2026

*Se recorrieron los diez paquetes de la revisión del dueño (`A01`–`A10`), **y seis celdas de la izquierda
pasaron de «implementado» a «medido», que no es lo mismo**.*

| celda | **qué se midió** |
|---|---|
| **§1 TLS / exposición** | *la web era el único de cinco contenedores en `0.0.0.0`* -- **todas las interfaces** -- y ahora está en `127.0.0.1`. *No era una decisión: era un valor por defecto, y estaba en dos sitios.* |
| **§2 Cookies** | *la cookie no lleva `secure` (correcto en HTTP local); **el token se guarda como huella SHA-256**, así que un volcado no entrega sesiones vivas; y **la caducidad se aplica de verdad** -- comprobado poniendo `expira_en` en el pasado.* |
| **§4 Copias** | *el ensayo **se ejecutó entero y pasó**: 30 515 bytes, restaurado, contenido 2/2 · 10/10 · 2/2, y la sustitución conservada. Y `respaldar.bat` ya comprime, rechaza el vacío, tiene `restaurar` y retiene 30 días.* |
| **§5 Acceso** | *el límite de altas es 10 por hora **y se agota de verdad** -- se notó al vaciarse la base de pruebas; y `autoriza_linea` **no comprueba pertenencia**: lo hace la ruta.* |
| **§6 Límites** | *la cola entera: **72 319 pendientes y 7 593 correctas**, con **43 603 de Alcampo** -- el 60 % -- y 5 026 de Lidl con 28 hechas.* |
| **§7 Observabilidad** | *`/api/estado/publicacion` con huellas; y **140 líneas de log sin ninguna credencial**.* |

### Y una celda que **NO** cambió, y se dice

**`§3 Secretos` sigue como estaba** -- *medido por búsqueda en 598 ficheros versionados, con las 19
coincidencias revisadas.* **No se ha vuelto a hacer esa búsqueda**, así que la celda sigue diciendo lo que
decía y **no se le añade una fecha nueva**. *Una celda no se revalida por haber leído el documento: se
revalida midiendo.*

### Y lo que se aprendió midiendo, que conviene dejar aquí

*De los diez paquetes, **el trabajo de esta fase no encontró un solo defecto leyendo; los encontró todos
ejecutando**.* **Y los tres más caros fueron tres suposiciones mías**:

1. **Un guion de copia que heredaba `CESTA_POSTGRES` del entorno** -- *y al apuntarlo a la base de pruebas
   de verdad, su ensayo rehízo el esquema: **716 usuarios, 2 529 listas y 2 533 líneas, perdidos**.*
2. **Una copia programada escrita entera** (310 líneas) **sin comprobar que `respaldar.bat` ya existía** --
   *y era mejor: comprime, rechaza el vacío, tiene `restaurar` y retiene 30 días.* **Lo habría dicho esta
   misma matriz, que lo nombraba en su §4, y que se leyó por primera vez ese día.**
3. **Cinco contratos de `almacen`** -- *y el código tenía razón en los cinco.*

> **La regla que sale de las tres, y es la que esta matriz ya practicaba sin decirlo**: *un documento se
> lee como un relato y **se comprueba como un inventario**.* **Y «no se nota» es una afirmación que hay que
> medir como cualquier otra** -- *yo la hice sobre el daño a la base de pruebas, y era falsa por diecisiete
> ensayos que empezaron a saltarse.*
