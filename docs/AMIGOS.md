# Cesta — que cambia si un dia la usan tus amigos

Escrito el 17 de septiembre de 2026. Hasta ahora todo el proyecto asumia **dos
personas**: David y su madre. Varias decisiones se tomaron con esa frase encima
de la mesa, y unas cuantas hay que revisarlas si algun dia entran diez o quince
personas.

**Esto no es "hazlo ahora".** Es saber **cual de las decisiones de hoy se
convierte en un problema manana**, para no cerrarse puertas por descuido. Las
que hay que hacer ya son tres, y son baratas.

---

## 0. Lo que se resolvio el 21 de septiembre de 2026

**Como entra alguien nuevo.** Este documento se escribio suponiendo que las
cuentas las creaba David desde la consola, y eso dejaba un callejon sin salida
que no se vio al escribirlo: quien recibia un enlace de invitacion a una lista
**sin tener cuenta** llegaba a la pantalla de entrar y ahi se acababa. El enlace
funcionaba, el codigo sobrevivia al login, y no habia forma de hacerse el login.

Ya hay `POST /api/registrarse` y su pantalla: cada uno se hace su cuenta, y al
registrarse entra y se aplica la invitacion en el mismo paso.

**El registro esta abierto, y eso se apoya en una sola cosa**: que a la pagina
solo se llega desde Tailscale. Es la decision que hay que revisar si el servicio
sale a internet -- `CESTA_REGISTRO=cerrado`, y las cuentas vuelven a la consola.
`GET /api/personas` dice quien ha entrado y cuando.

**Lo que sigue sin existir**: quitarle la cuenta a otro. Cada uno se borra la
suya; echar a alguien pide un papel de duenno que hoy no hay, y de momento se
hace con una consulta (`docs/DESPLIEGUE.md` punto 5).

**Y desde el 23 de septiembre de 2026 el enlace lo abre un navegador, con dos
personas.** Lo hace la puerta mecanica de la interfaz
(`plataforma/prueba_navegador.py`, seccion "el enlace de invitacion, abierto por
otra persona"): la cuenta de siempre crea el enlace desde su cesta, y **una
segunda sesion** -- otro contexto del navegador, sin cookies ni nada en comun --
lo abre tal como lo abre quien lo recibe, entra (o se crea la cuenta) **en la
propia pantalla del enlace**, aterriza en la lista con las lineas que ya estaban
dentro, y **no le sale el boton de invitar, porque la lista no es suya**. Hasta
ese dia se probaba el endpoint, no la pantalla: el mismo hueco que tenia el
escaner. La seccion **anula antes los enlaces que haya**, que es lo que hace falta
para poder correrla mas de tres veces (la API admite tres vivos por lista) y de
paso comprueba el otro camino, el de apagar un enlace que ya no vale.

---

## 1. Lo que ya aguanta, sin tocar nada

    cuentas             `usuario` es unica y la clave va con Argon2id. Diez
                        cuentas o dos, da igual.
    listas compartidas  `lista_acceso` ya tiene papel ('dueno', 'escribe',
                        'mira') y no asume dos filas. El papel 'mira' se creo
                        justo para "ensenarsela a alguien sin que la cambie",
                        y con amigos por fin sirve.
    invitar por enlace  caduca a los 7 dias y sirve para 3 personas, y los dos
                        numeros son parametros.
    sin cobertura       el identificador de linea lo genera el movil y cada
                        cambio viaja con su hora. Eso escala solo.
    el catalogo         es el mismo para todos y no se copia por usuario. Diez
                        personas leen el mismo parquet.

---

## 2. Lo que hay que hacer YA, porque despues es caro

### 2.1 Que la lista de casa deje de ser unica en el sistema

    hoy      `CREATE UNIQUE INDEX lista_de_casa_unica ON lista((es_de_casa))
              WHERE es_de_casa`
    problema **hay UNA lista de casa en toda la base de datos.** Con dos
             personas que viven juntas tiene sentido. Con amigos, cada uno
             querra la suya y el segundo que lo intente se llevara un error de
             clave duplicada que no entendera nadie.
    arreglo  el indice pasa a ser por dueno:
             `CREATE UNIQUE INDEX ... ON lista(dueno_id) WHERE es_de_casa`
    coste    una linea de SQL en una migracion nueva
    si no    el dia que entre la tercera persona, la app falla al crear su
             primera lista, y el error no dira por que

### 2.2 Guardar quien invito a quien

    hoy      `invitacion.creada_por` existe, pero cuando alguien acepta solo se
             guarda su fila en `lista_acceso`
    problema con quince personas, quien invito a quien importa: para saber a
             quien echar si alguien se pasa, y para entender como crecio
    arreglo  `lista_acceso.invitado_por` ya existe en el esquema. Solo hay que
             rellenarlo al aceptar una invitacion.
    coste    una linea en `acepta_invitacion()`

### 2.3 Un limite de invitaciones por persona

    hoy      cualquiera con una lista puede generar enlaces sin limite
    problema no es un ataque: es que un enlace reenviado sin querer mete a
             gente que no sabes que esta
    arreglo  un maximo de invitaciones vivas por lista (tres, por ejemplo) y
             que crear una nueva revoque las anteriores si se pasa
    coste    una comprobacion en `crea_invitacion()`

---

## 3. Lo que hay que decidir antes de dar la primera cuenta a un amigo

### 3.1 Los datos de tus amigos son tuyos, y eso es una responsabilidad

Mientras sois dos, la lista de la compra es un asunto de familia. En cuanto
entra un amigo, **estas guardando en tu ordenador lo que compra otra persona**:
que come, cuanto gasta, cuando hace la compra. Eso no es grave, pero tampoco es
nada.

Lo minimo, y no cuesta casi:

    - decirselo. Una linea al crear la cuenta: "esto vive en el ordenador de
      David, y David puede ver tus listas si mira la base de datos".
    - poder borrarse. `DELETE FROM usuario` ya arrastra sus listas, favoritos y
      sesiones por las claves ajenas. Falta el boton.
    - no guardar lo que no hace falta. Hoy no se guarda ningun dato de pago ni
      ninguna direccion, y eso debe seguir asi.

### 3.2 El PC apagado deja de ser una molestia y pasa a ser un problema

Con dos personas que viven en la misma casa, "el ordenador esta apagado" se
resuelve encendiendolo. Con un amigo en otra ciudad, la app **simplemente no
funciona** y no puede hacer nada.

Tres opciones, por orden de lo que cuestan:

    1. asumirlo y decirlo    la app ya guarda la lista abierta en el movil. Lo
                             unico que falta es que el aviso sea claro:
                             "el ordenador de David esta apagado".
    2. encenderlo solo       Wake-on-LAN desde Tailscale. Es un proyecto
                             pequeno y resuelve el 90 % de los casos.
    3. un servidor           se descarto a proposito, y con amigos vuelve a la
                             mesa. Un VPS de 5 EUR al mes lo resuelve entero.

**No hay que decidirlo hoy.** Hay que saber que el dia que entre el primer amigo,
esta es la primera pregunta que hara.

### 3.3 Tailscale aguanta seis personas gratis

El plan Personal cubre **hasta 6 usuarios** con dispositivos ilimitados. Tu, tu
madre y cuatro amigos. El septimo ya no entra.

A partir de ahi:

    - o se pasa a Cloudflare Tunnel con Access, que llega a 50 usuarios gratis
      pero **publica el servicio en internet** (docs/DESPLIEGUE.md punto 4.2)
    - o se paga Tailscale
    - o se comparte la maquina en vez de la red (`node sharing`), que obliga a
      que cada amigo tenga su propia red de Tailscale: mas lio para ellos

Con amigos, **Cloudflare pasa a ser la opcion sensata** y Tailscale la de dos
personas. Merece la pena tenerlo escrito antes de invitar al quinto.

---

## 4. Lo que habia descartado "porque sois dos" y con amigos vuelve

En `docs/FUNCIONALIDADES.md` seccion G hay ocho cosas descartadas. **Tres de
ellas cambian de veredicto** con mas gente:

    amigos por @usuario      descartado por burocracia. Con diez personas,
                             buscar a alguien por su nombre de usuario deja de
                             ser burocracia y pasa a ser lo normal.
                             -> revisar a partir de 5 usuarios
    varios carritos activos  descartado porque "con una lista de casa basta".
                             Con amigos hay lista de casa, lista del piso, lista
                             de la barbacoa del sabado. QueFalta lo resuelve con
                             grupos y un carrito activo.
                             -> revisar cuando alguien tenga mas de 3 listas
    pantalla de actividad    descartada porque `anadido_por` en cada linea
                             basta. Con cinco personas en una lista, deja de
                             bastar.
                             -> revisar a partir de 4 personas en una lista

Las otras cinco (colores de acento, tarjetas de fidelizacion, inventario a mano,
escaneo de tickets, "enviar al supermercado") siguen descartadas por sus propios
motivos, que no tienen que ver con cuanta gente haya.

---

## 5. Lo que hay que mirar cuando entre gente

Numeros que hoy no importan y entonces si:

    consultas por segundo   DuckDB abre una conexion POR HILO y cada una hace
                            una copia del catalogo en memoria (~4,5 MB). Con
                            cuatro hilos son 18 MB: nada. Con veinte, 90 MB.
                            **Vigilar si se sube el pool de uvicorn.**
    tamano de PostgreSQL    con dos personas son unos pocos MB. Con quince y un
                            ano de historial de compra, decenas. Sigue siendo
                            nada, pero el respaldo deja de ser instantaneo.
    el calculo de la cesta  `donde_comprar` mira diez combinaciones de tienda
                            por lista. Si veinte personas lo piden a la vez, son
                            doscientas. Hoy tarda milisegundos; conviene medirlo
                            antes de que pase.

---

## 6. Resumen: que hacer y cuando

    AHORA, y son tres lineas de codigo
      - el indice de "lista de casa" pasa a ser por dueno
      - rellenar `invitado_por` al aceptar una invitacion
      - un limite de invitaciones vivas por lista

    ANTES DE DAR LA PRIMERA CUENTA A UN AMIGO
      - decirle donde viven sus datos, y darle un boton para borrarse
      - decidir que pasa cuando el PC esta apagado
      - si van a ser mas de seis, mirar Cloudflare en vez de Tailscale

    CUANDO SEAN CINCO O MAS
      - buscar gente por @usuario
      - varias listas con una activa
      - pantalla de actividad en las listas compartidas
