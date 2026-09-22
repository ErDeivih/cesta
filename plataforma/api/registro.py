"""Crear una cuenta desde la propia aplicacion, sin pasar por la consola.

Hasta hoy las cuentas solo nacian con `plataforma/cuenta.py`, desde la linea de
comandos del contenedor. Eso tenia sentido mientras la frase que sostenia el
diseno era "sois dos y no hay nadie mas a quien dar de alta". Ya no lo es, y
ademas dejaba un callejon sin salida que si era un fallo de verdad: **a quien
recibia un enlace de invitacion a una lista sin tener cuenta, la aplicacion le
ensenaba la pantalla de entrar y ahi se acababa el viaje.** El enlace
funcionaba, el codigo sobrevivia al login, y no habia forma de hacerse el login.

Este modulo es solo las reglas. No toca la base de datos ni sabe de HTTP: asi se
pueden probar una a una, que es lo que importa cuando lo que hay detras es
"cualquiera que llegue a esta pagina puede crearse una cuenta".

Por que el registro esta ABIERTO
--------------------------------
Es una decision tomada a sabiendas, no un descuido. Hoy Cesta solo se alcanza
desde Tailscale, que es una red privada entre dispositivos invitados uno a uno:
quien llega a la pagina de registro ya ha pasado un control, y pedirle ademas un
codigo era un trasto para nada.

Lo que hay que saber es **cuando deja de ser cierto**: el dia que el servicio se
publique con Cloudflare Tunnel (`docs/DESPLIEGUE.md` 4.2), la pagina de registro
queda en internet y este parrafo pasa a ser un problema. Por eso existe
`CESTA_REGISTRO=cerrado`, que se cambia en el `.env` y no toca codigo. Esta
escrito aqui para que el dia que alguien abra el tunel se encuentre el aviso.

Las reglas, y por que cada una
------------------------------
    solo ASCII en el usuario   con registro abierto y listas compartidas, un
                               nombre con letras que se parecen (la `a` cirilica
                               de `dаvid`) deja una linea que pone "anadido por
                               david" y no la anadio david. Es suplantacion
                               barata y se corta aqui.
    nombres reservados         quien coja `admin` o `cesta` pasa por el sistema
                               en una lista compartida.
    ocho caracteres de clave   lo mismo que ya pedia `cuenta.py`. Se comprueba
                               en un solo sitio para que no se separen.
    la clave no es el usuario  es la contrasena que mas se pone cuando se pide
                               una deprisa.
"""
from __future__ import annotations

import re
import unicodedata

# Tres a veinticuatro, empezando por letra o numero. El resto admite punto,
# guion y guion bajo, que es lo que la gente escribe sin pensar.
USUARIO_VALIDO = re.compile(r"^[a-z0-9][a-z0-9._-]{2,23}$")

MINIMO_CLAVE = 8
# Argon2 hashea lo que le eches, pero no hay ninguna razon para aceptar un
# megabyte de contrasena y si para no hacerlo.
MAXIMO_CLAVE = 200

MINIMO_NOMBRE = 2
MAXIMO_NOMBRE = 60

# Nombres con los que alguien pasaria por el sistema o por otra persona.
RESERVADOS = frozenset({
    "admin", "administrador", "administrator", "root", "sistema", "system",
    "cesta", "soporte", "support", "ayuda", "help", "api", "www", "correo",
    "mail", "nadie", "null", "undefined", "none", "anonimo", "anonymous",
    "todos", "everyone", "oficial", "official",
})


def normaliza(usuario: str) -> str:
    """Lo que de verdad se va a guardar: sin espacios alrededor y en minusculas.

    Se normaliza **antes** de comprobar nada, para que la comprobacion mire
    exactamente lo mismo que acabara en la base de datos. Comprobar una cosa y
    guardar otra es como se cuelan los nombres que no deberian existir.
    """
    return unicodedata.normalize("NFKC", usuario or "").strip().lower()


def limpia_nombre(nombre: str) -> str:
    """El nombre que se ensena. Se le quitan los saltos de linea y poco mas."""
    return " ".join((nombre or "").split())


def revisa(usuario: str, nombre: str, clave: str) -> str | None:
    """El problema que tiene esta alta, en una frase, o None si no tiene ninguno.

    Devuelve texto y no un codigo a proposito: es lo que va a leer una persona
    delante del formulario, y una frase que explica que hacer vale mas que un
    identificador que hay que traducir en otra capa.
    """
    usuario = normaliza(usuario)
    nombre = limpia_nombre(nombre)

    if not usuario:
        return "Hace falta un nombre de usuario."
    if len(usuario) < 3:
        return "El usuario necesita al menos tres caracteres."
    if len(usuario) > 24:
        return "El usuario no puede pasar de veinticuatro caracteres."
    if not USUARIO_VALIDO.match(usuario):
        return ("El usuario solo puede llevar letras sin tilde, números, punto, "
                "guión y guión bajo, y tiene que empezar por letra o número.")
    if usuario in RESERVADOS:
        return "Ese nombre de usuario está reservado. Elige otro."

    if len(nombre) < MINIMO_NOMBRE:
        return "Hace falta un nombre para enseñar en las listas."
    if len(nombre) > MAXIMO_NOMBRE:
        return "El nombre es demasiado largo."

    if len(clave or "") < MINIMO_CLAVE:
        return f"La contraseña necesita al menos {MINIMO_CLAVE} caracteres."
    if len(clave) > MAXIMO_CLAVE:
        return "Esa contraseña es absurdamente larga."
    if clave.strip().lower() == usuario:
        return "La contraseña no puede ser el propio usuario."

    return None
