# Cesta — donde vive cada cosa y como se entra desde fuera

Escrito el 15 de septiembre de 2026. Sustituye a la parte de arquitectura de
`APP.md`, que daba por hecha una PWA con los datos dentro del movil.

---

## 1. La decision, en una frase

**Los datos no salen del PC.** El movil es una pantalla: pide, dibuja, y no
guarda nada que no sea lo que estas mirando ahora mismo.

Esto cambia lo que habia escrito. La version anterior descargaba al movil un
paquete diario de 7 MB con el catalogo entero. Funcionaba sin red, pero:

- eran 7 MB al dia por telefono, y dijiste que no
- con dos personas, cada movil tendria su propia copia de las listas y los
  favoritos, sin forma de compartirlos
- el cuadro de mando que pides ahora no cabe en un movil: son 400.000 filas de
  historico creciendo a 52.575 al dia

Asi que el reparto es este:

    tu PC, fuera de Docker     los colectores (Windows + Chrome para el WAF
                               de Alcampo) y el pipeline. Lo que ya funciona.
    tu PC, dentro de Docker    la API, la base de datos de usuarios, el motor
                               analitico y el cuadro de mando
    el movil                   una web. Sin base de datos, sin descarga diaria.

---

## 2. Por que el scraper se queda fuera del contenedor

Alcampo esta detras de AWS WAF y hace falta Patchright con un Chrome real. Meter
eso en Docker en Windows significa Chrome dentro de un contenedor Linux dentro de
WSL2, con el WAF viendo un navegador que no se parece a ninguno normal. Lo que
hoy funciona tres dias seguidos sin un corte dejaria de funcionar.

La frontera entre las dos mitades es el disco:

    el scraper escribe   F:\aprendizaje\scrap\data\gold\*.parquet
    el contenedor lee    /datos/gold/*.parquet   (el mismo sitio, montado)

El contenedor **nunca escribe** en gold. Si un dia el scraper falla, la app sigue
sirviendo lo de ayer y lo dice en pantalla. Son dos piezas que solo se hablan por
ficheros, y eso significa que se pueden parar, arreglar y arrancar por separado.

---

## 3. Los cuatro contenedores

    cesta-api        FastAPI. La unica puerta. Autentica, consulta y responde
                     JSON. No sirve HTML.
    cesta-db         PostgreSQL 16. Usuarios, listas, favoritos, alertas,
                     historial. Todo lo que se escribe.
    cesta-web        La interfaz. Ficheros estaticos servidos por Caddy.
    cesta-panel      El cuadro de mando. Ver DASHBOARD.md.

**Dos motores de datos, a proposito:**

    PostgreSQL   lo que escriben las personas. Poco volumen, muchas escrituras
                 a la vez, y hace falta que dos moviles no se pisen. Unas pocas
                 miles de filas.
    DuckDB       lo que lee todo el mundo. Consulta los parquet de gold sin
                 copiarlos. 560.640 filas hoy, unos 19 millones en un ano.
                 Cero escrituras: si se rompe, se reinicia y ya esta.

Meter el historico en Postgres seria un error caro: 19 millones de filas al ano
con consultas de agregacion es justo lo que DuckDB hace en milisegundos leyendo
parquet y lo que Postgres hace mal sin un trabajo de indices que no quieres
mantener.

El unico volumen que hay que respaldar es el de Postgres. Gold se regenera
solo desde raw.

---

## 4. Como entra tu madre

Dos caminos. Recomiendo el primero.

### 4.1 Tailscale (recomendado)

Una red privada entre tus dispositivos. Tu PC, tu movil y el de tu madre se ven
entre ellos como si estuvieran en la misma casa. **El servicio nunca tiene una
direccion publica: no hay nada en internet que atacar.**

    coste        gratis. El plan Personal cubre hasta 6 usuarios y
                 dispositivos ilimitados
    lo que hace  instalar la app en el movil de tu madre y aceptar una
                 invitacion. Una vez.
    la direccion http://cesta:8080 desde cualquiera de los dos moviles
    dominio      no hace falta ninguno

Lo que hay que aceptar: tu madre tiene que instalar una app mas y entrar con una
cuenta (Google le vale). Si eso es un problema, el segundo camino.

### 4.2 Cloudflare Tunnel + Access (alternativa)

El PC abre una conexion hacia fuera y Cloudflare publica una direccion. Tu madre
entra con un enlace normal y un codigo que le llega al correo.

    coste        gratis hasta 50 usuarios en el plan Zero Trust
    lo que hace  abrir un enlace y meter el codigo del correo
    dominio      hace falta uno propio, gestionado en Cloudflare
    el riesgo    **el servicio SI es alcanzable desde internet.** Access es lo
                 unico que hay delante. Una regla mal puesta y queda abierto.

**Si se abre este tunel hay que cerrar el registro.** Desde el 21 de septiembre
de 2026 cualquiera que llegue a la pagina puede crearse una cuenta, y eso solo es
razonable mientras "llegar a la pagina" signifique estar dentro de Tailscale. Con
el tunel abierto, la pagina de registro esta en internet. Se cierra poniendo
`CESTA_REGISTRO=cerrado` en el `.env` y levantando otra vez.

### 4.3 Lo que no se hace

Abrir un puerto en el router. Ni con contrasena, ni con un puerto raro, ni "solo
un rato". Un PC de casa expuesto a internet recibe intentos automaticos desde el
primer minuto, y aqui hay un Postgres detras.

---

## 5. Usuarios: tu y tu madre

Dos personas, dos formas de usar la misma cosa. El modelo tiene que separar lo
que es de cada uno de lo que es de los dos.

    de cada uno       favoritos, alertas, historial de busquedas,
                      que cadenas tiene cerca
    compartido        las listas de la compra, si se marcan como compartidas
    de nadie          el catalogo, los grupos, los precios: es el mismo para
                      todos y no se copia por usuario

Una lista compartida se edita a la vez desde los dos moviles. Cuando tu madre
tacha la leche, a ti se te tacha. Eso pide que el estado viva en el servidor,
que es exactamente lo que estamos montando.

**Identidad**: usuario y contrasena propios de la app, guardados con Argon2id.
La sesion dura mucho (30 dias) porque tu madre no va a entrar cada semana; y
cuando expira, Tailscale ya la ha identificado como tu red, asi que el riesgo de
una sesion larga es pequeno.

**El registro esta abierto** desde el 21 de septiembre de 2026: cada uno se hace
su cuenta desde la propia pagina, sin que tu tengas que darla de alta a mano. La
decision se apoya enteramente en **quien puede llegar a la pagina**, y hoy eso es
Tailscale, que ya es una red de invitados uno a uno. Por eso el aviso del punto
4.2: el dia que el servicio salga a internet, esta frase deja de ser cierta y hay
que poner `CESTA_REGISTRO=cerrado`.

Lo que lo hace vigilable es `GET /api/personas`: quien tiene cuenta y desde
cuando. Una puerta abierta sin una ventana por la que ver quien ha entrado no es
una decision, es un descuido.

**Lo que todavia no hay**: una forma de echar a alguien desde la aplicacion. Cada
uno puede borrarse su propia cuenta, pero quitarle la suya a otro pide decidir
quien manda aqui, y eso es un papel de duenno que hoy no existe a proposito. De
momento se hace por consola:

    docker compose exec db psql -U cesta -d cesta \
        -c "SELECT borrar_usuario(id) FROM usuario WHERE usuario = 'quien';"

**Lo que no se guarda**: ningun dato de pago, ninguna direccion, ningun correo
que no sea el de recuperacion. La app no compra nada.

---

## 6. Cuando el PC esta apagado

Esta es la unica pega real de esta arquitectura, y no tiene solucion elegante:
**si el PC esta apagado, la app no funciona.**

Lo que se puede hacer para que duela menos:

- El movil guarda en memoria lo ultimo que se vio (la lista de la compra, sobre
  todo) y lo ensena marcado como "de hace X horas, sin conexion con casa".
- Lo que se escribe sin conexion (tachar un producto de la lista) se guarda en
  el movil y se sube cuando vuelve. Es un cambio pequeno y hay que hacerlo,
  porque el supermercado es justo donde peor cobertura hay.
- Encender el PC por Wake-on-LAN desde Tailscale es posible pero es un
  proyecto en si mismo. No para la primera version.

La alternativa seria un servidor siempre encendido, y dijiste que no querias VPS.
Es una decision coherente: lo importante es saber que se ha decidido.

---

## 7. Orden de montaje

    1  cesta-api con solo dos consultas (buscar, ficha de grupo) leyendo
       gold con DuckDB. Sin usuarios todavia. Se prueba desde el propio PC.
    2  Tailscale. Comprobar que se abre desde tu movil.
    3  cesta-db y las cuentas. Tu primero, tu madre despues.
    4  Listas y favoritos.
    5  cesta-web: las cinco pantallas de APP.md.
    6  cesta-panel: el cuadro de mando de DASHBOARD.md.
    7  Escritura sin conexion en el movil.

Los pasos 1 a 3 son lo que hay que tener antes de ensenarselo a nadie.

---

## 8. Estado del montaje (24 de septiembre de 2026)

Lo que hay montado de verdad, y lo que falta. El detalle de cada cosa, con sus numeros y su
comprobacion, esta en `docs/BACKLOG.md` (§0) y en `docs/CIERRE-ENCARGO-UX.md`.

    cesta-db    **Publica su puerto en 127.0.0.1:5432, y solo ahi** (ni wifi ni Tailscale).
                No es para nadie de fuera: es para la **cadena diaria**, que corre en el
                PC y tiene que mirar las alertas para que el resumen de las 06:00 diga
                cuantas saltaron (`projects/cesta/avisos.py`, que lee la clave de
                `plataforma/.env` y asi no necesita una segunda copia). Antes decia
                "no lo se"; desde el 24 sep dice el numero.
    cesta-api   Imagen **reconstruida** el 24 sep: la que corria llevaba dos dias sin la
                correccion de faltas, sin `/api/habituales` y sin el vigilante de los
                avisos. Al arrancar se aplicaron solas las migraciones 006 y 007.
                El `.dockerignore` esta **en la raiz**, no en `plataforma/`: el contexto de
                construccion es la raiz (`context: ..`), asi que el de `plataforma/` no se
                usaba para nada y el daemon recibia los 11 GB de `data/` y los 96 MB de
                `node_modules`.
    cesta-web   Sirve la interfaz **vieja** (`./web:/srv:ro`). Cambiar el montaje a
                `./web/dist:/srv:ro` es la ultima cosa que queda, y no es un paso
                automatico: **antes hay que medir la paridad que falta**, porque lo que la
                vieja hace y la nueva no desaparece de la mano de quien la usa.
    cesta-panel Sigue siendo el cuadro de mando de `DASHBOARD.md`.
