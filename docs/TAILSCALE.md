# Cesta — Tailscale explicado y configurado

Escrito el 15 de septiembre de 2026. Es la pieza que falta entre "los datos
viven en mi PC" y "mi madre puede usar la app desde su movil".

---

## 1. Que es, sin metaforas

El problema: tu PC esta en tu casa, detras de un router que no deja entrar a
nadie. Eso es bueno. El movil de tu madre esta en su casa, detras de otro router
igual de cerrado. Para que su movil hable con tu PC, normalmente hay que abrir un
agujero en tu router, y ese agujero lo ve internet entero.

Tailscale hace otra cosa: **instala una tarjeta de red mas** en cada dispositivo.
No una tarjeta fisica: una que existe solo para tu red. Cada dispositivo recibe
una direccion que solo tiene sentido dentro de ella (algo como `100.x.y.z`), y
todo lo que pasa entre ellos va cifrado de punta a punta con WireGuard.

Lo que importa de verdad:

- **No se abre ningun puerto en tu router.** Los dos extremos salen hacia fuera y
  se encuentran a medio camino. Un router no distingue eso de que alguien este
  viendo un video.
- **El servicio no tiene direccion publica.** No hay una URL de Cesta que alguien
  pueda encontrar. Si no estas en la red, para ti no existe.
- **Tailscale no ve tus datos.** Coordina el encuentro y reparte las llaves; el
  trafico va directo entre los dos dispositivos y cifrado.
- **Va desde cualquier sitio.** No hace falta estar en tu wifi. Su movil con
  datos moviles en mitad de la calle entra igual.

Lo que hay que aceptar: tu madre instala una app mas y entra con una cuenta
(Google le vale). Una vez. Despues no vuelve a tocarla.

---

## 2. Lo que cuesta

El plan Personal es **gratis y cubre hasta 6 usuarios con dispositivos
ilimitados**. Vosotros sois dos. Incluye lo que hace falta: MagicDNS, listas de
acceso y HTTPS dentro de la red.

Es para uso no comercial, que es exactamente este caso.

---

## 3. Montarlo: cuatro pasos

### Paso 1 — Tu cuenta y tu PC

1. Entra en `tailscale.com` y crea la cuenta con tu Google. Eso crea **tu red**
   (ellos la llaman *tailnet*).
2. Descarga el cliente de Windows e instalalo en el PC donde corre todo.
3. Al arrancar, entra con la misma cuenta. El PC aparece en la lista de maquinas.
4. En la consola de administracion, **renombra esa maquina a `cesta`**. No es
   estetica: con MagicDNS activado, el nombre es la direccion.
5. Comprueba que Tailscale **arranca con Windows**. Si no, el dia que el PC se
   reinicie solo, la app deja de existir sin que nadie sepa por que.

Con esto ya puedes abrir `http://cesta:8080` desde tu propio movil, en cuanto
instales la app ahi tambien.

### Paso 2 — Tu movil

Instala Tailscale del Play Store o del App Store, entra con tu cuenta, y activa
el interruptor. Ya esta.

### Paso 3 — Tu madre

En la consola de administracion, pestana **Users**, `Invite external users`.
Escribes su correo y le llega una invitacion.

Ella: instala la app, abre el correo, pulsa el enlace, entra con su Google, y
activa el interruptor. Fin.

Es **invitarla como usuaria de tu red**, no compartirle una maquina suelta.
Compartir maquinas (*node sharing*) existe, pero obliga a que ella tenga su
propia red de Tailscale y sea administradora de ella, que es mucho mas lio para
lo mismo.

### Paso 4 — Cerrarle el paso a todo lo demas

Este paso se salta mucha gente y es el que convierte "funciona" en "esta bien
hecho". Por defecto, quien entra en tu red **ve toda tu red**: el movil de tu
madre podria alcanzar cualquier servicio de tu PC, no solo Cesta.

En `Access controls` de la consola se escribe quien llega a que. La idea, en
castellano: **ella solo llega a la maquina `cesta`, y solo al puerto de la app.**
El resto de tu PC, y cualquier otro cacharro que metas en la red algun dia,
queda fuera de su alcance.

No es desconfianza. Es que si un dia su movil se pierde o se infecta, lo que
alcanza ese movil es una web de precios de supermercado y nada mas.

---

## 4. Como se ve desde el movil

    http://cesta:8080

Eso es todo. `cesta` funciona como direccion gracias a MagicDNS, que viene
activado de serie. Se guarda en la pantalla de inicio del movil como si fuera una
app y ya no se escribe mas.

Tailscale se queda de fondo consumiendo practicamente nada. No es una VPN de las
que enrutan todo tu trafico: solo se activa cuando hablas con una maquina de tu
red. Navegar por internet sigue yendo directo.

---

## 5. Lo que va a pasar y conviene saber de antemano

**El PC apagado.** Abrir `http://cesta:8080` da un error de conexion. Es el
comportamiento correcto y esperado, pero conviene decirselo a tu madre antes de
que pase, porque si no va a pensar que la app esta rota. La app guarda la lista
de la compra abierta en el movil justo para este caso.

**El primer arranque tras reiniciar.** Tailscale tarda unos segundos en
reconectar. Si abres la app en ese momento, falla y al insistir funciona.

**La sesion de la app.** Dura 30 dias a proposito, porque tu madre no va a entrar
todas las semanas y no tiene gracia pedirle la contrasena cada vez. El riesgo de
una sesion larga es pequeno cuando lo unico que puede alcanzarla es un movil que
ya esta dentro de tu red.

**Si algun dia no va.** En la consola de administracion se ve que maquinas estan
conectadas y cuando se vio cada una por ultima vez. Casi siempre la respuesta
esta ahi: el PC dormido, o Tailscale que no arranco.

---

## 6. Y si tu madre no se apana con la app

Entonces el otro camino es **Cloudflare Tunnel con Access delante**: ella abre un
enlace normal, mete el codigo que le llega al correo, y dentro. Gratis hasta 50
usuarios, pero hace falta un dominio propio gestionado en Cloudflare y, sobre
todo, **el servicio pasa a ser alcanzable desde internet**. Access es lo unico que
hay delante: una regla mal puesta y queda abierto.

Merece la pena intentar Tailscale primero. Instalar una app y pulsar un enlace del
correo es una sola tarde, y despues no se vuelve a tocar.

---

## 7. Lo que no se hace, nunca

**Abrir un puerto en el router.** Ni con contrasena, ni con un puerto raro, ni
"solo un rato para probar". Un PC de casa con un puerto abierto recibe intentos
automaticos desde el primer minuto, y detras de este hay un PostgreSQL con
vuestras cuentas.

**Meter la app en un servicio de tuneles rapidos** (ngrok y parecidos) para salir
del paso. Son direcciones publicas, cambian cada vez, y acaban quedandose.
