# Cesta — la plataforma

Lo que hay aqui es el servicio que consulta los datos: la API, la base de
usuarios y la interfaz. **El scraper no esta aqui**, sigue siendo `ejecutar.bat`
en la raiz del proyecto.

Las dos mitades solo se hablan por el disco:

    el scraper escribe   data/gold/*.parquet
    la plataforma lee    /datos/gold   (montado en SOLO LECTURA)

Eso significa que se pueden parar, arreglar y arrancar por separado, y que si un
dia la recoleccion falla, la app sigue sirviendo lo de ayer y lo dice en
pantalla.

---

## Arrancarla, la primera vez

1. **Docker Desktop** instalado y funcionando.
2. Copia `.env.ejemplo` a `.env` y cambia `CESTA_CLAVE_DB` por algo largo. No la
   vas a escribir nunca: la usa el contenedor de la API para hablar con
   PostgreSQL.
3. `.\arrancar.bat`
4. Abre `http://localhost:8080` y **crea tu cuenta desde la propia pagina**:
   «¿No tienes cuenta? Crearla». El registro esta abierto, asi que las demas
   personas se hacen la suya igual, sin que tengas que darlas de alta tu.

   El usuario admite letras sin tilde, numeros, punto y guiones. La contrasena,
   ocho caracteres como minimo. En la base solo queda su hash de Argon2id.

   Sigue existiendo la via de la consola, y hace falta si algun dia cierras el
   registro con `CESTA_REGISTRO=cerrado`:

       .\arrancar.bat cuenta david "David"

5. Abre `http://localhost:8080` en este PC.
6. Para entrar desde el movil, monta Tailscale (`docs/TAILSCALE.md`) y entra en
   `http://cesta:8080`.

### El registro esta abierto, y de que depende que eso este bien

Cualquiera que llegue a `http://cesta:8080` puede crearse una cuenta. Eso es
razonable **solo mientras llegar ahi signifique estar dentro de Tailscale**, que
es una red privada a la que se entra por invitacion. El dia que publiques el
servicio con Cloudflare Tunnel (`docs/DESPLIEGUE.md` 4.2), la pagina de registro
queda en internet: entonces hay que poner `CESTA_REGISTRO=cerrado` en el `.env`.

Para ver quien ha entrado, `GET /api/personas` da la lista con la fecha de alta.
Echar a alguien todavia se hace por consola; esta el comando en `DESPLIEGUE.md`.

El resto de dias: `.\arrancar.bat` y ya. O nada, porque los contenedores se
levantan solos cuando arranca Docker.

**El `.\` de delante no sobra.** PowerShell, que es lo que abre Windows por
defecto, no ejecuta nada del directorio actual si no se lo dices con una ruta:
escribir `arrancar.bat` a secas da *«no se reconoce como nombre de un cmdlet»* y
parece que falta el fichero cuando lo que falta son dos caracteres. En `cmd`
funcionan las dos formas, asi que aqui se escribe siempre con `.\`.

---

## Que hay dentro

    api/ajustes.py    lo que cambia entre tu portatil y el contenedor
    api/catalogo.py   DuckDB sobre los parquet de gold. Solo lee.
    api/cesta.py      donde sale mas barata la lista, con las ofertas puestas
    api/almacen.py    PostgreSQL: cuentas, listas, favoritos
    api/panel.py      las consultas del cuadro de mando
    api/main.py       las rutas
    sql/              el esquema, que se aplica solo al arrancar
    web/              la interfaz: tres ficheros, sin framework
    cuenta.py         dar de alta a una persona

### Dos motores de datos, a proposito

**DuckDB** para lo que se lee: consulta los parquet donde estan, sin copiarlos.
560.640 filas hoy, unos 19 millones en un ano, y las agregaciones del panel
salen en milisegundos.

**PostgreSQL** para lo que se escribe: cuentas, listas y favoritos. Son pocos
miles de filas pero con dos personas escribiendo a la vez, y eso DuckDB lo hace
mal.

El unico volumen que hay que respaldar es el de PostgreSQL. Gold se regenera
solo desde raw.

---

## Las reglas que estan metidas en el codigo

Tres cosas que no son detalles y conviene no deshacer sin pensarlo:

**Una letra de calidad sacada del precio no se llama calidad.** El 77 % de ellas
salen de ordenar por precio, no de leer una etiqueta. La API devuelve `calidad`
solo cuando viene de ingredientes, y `gama` cuando viene del precio. Mezclarlas
produce la conclusion falsa de que lo barato es peor
(`docs/DASHBOARD.md` estudio 3.2).

**Una oferta es una regla, no un precio.** "2a unidad -50%" no abarata el
producto, abarata el par. `core/promos.py` lo traduce y `api/cesta.py` lo usa
para elegir tienda. Y los descuentos de tarjeta **no bajan el total**: ese dinero
no se descuenta en caja.

**Cada precio lleva su fecha cuando no es de hoy**, y uno de mas de tres dias se
ensena pero no decide en que tienda comprar. `/api/estado` es lo que sostiene
esta regla: la interfaz la pide al abrir.

---

## Sin cobertura

El supermercado es donde peor va la red, y es donde se usa la lista. Tres cosas
lo resuelven:

1. **El identificador de cada linea lo genera el movil**, no el servidor. Asi se
   puede anadir sin red y subirlo despues con la identidad con la que nacio.
2. **Cada cambio viaja con la hora del movil**, no con la de llegada. Tachar a
   las 18:04 y subirlo a las 18:20 cuenta como las 18:04.
3. **La lista abierta se guarda entera en el movil.** Unos pocos KB, y es lo
   unico que la app guarda.

Tachar es idempotente: si los dos tachais lo mismo a la vez, gana quien lo hizo
antes y el otro ve lo que queria ver. La cantidad es el unico caso con conflicto
real, y ahi gana el ultimo y se avisa de quien fue.

---

## Si algo va mal

    .\arrancar.bat logs      que dice cada contenedor
    docker compose ps        cuales estan vivos
    docker compose logs --tail 80 api    solo la API, y sin quedarse mirando

**La API no arranca**: casi siempre es que `CESTA_GOLD` apunta a una carpeta sin
parquet. Comprueba que `data/gold/grupos.parquet` existe.

**Entra pero no hay datos**: el pipeline no ha corrido. `.\ejecutar.bat` en la raiz.

**`cesta-api` se reinicia sin parar** y `docker compose exec` contesta *«Container
is restarting»*: la API se esta muriendo al importarse, antes de servir nada.
`docker compose logs --tail 80 api` lo dice en la ultima linea. El 21 de
septiembre de 2026 fue un `import polars` que llego de rebote desde
`core/comparacion.py`, y polars no esta en la imagen de la API. Lo vigila
`tests/test_imagen_api.py`, que compara el grafo de importaciones con el
`pip install` del Dockerfile sin levantar Docker.

**Desde el movil no se abre**: es Tailscale, no la plataforma. Comprueba primero
`http://localhost:8080` en el PC.

**El PC estaba apagado**: la app no funciona salvo la lista que te llevaste. Es
la consecuencia de no querer un servidor de pago, y esta decidido a proposito
(`docs/DESPLIEGUE.md` punto 6).
