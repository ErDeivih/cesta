"""Da de alta una cuenta desde la consola.

    docker compose exec api python -m plataforma.cuenta david "David"

Desde que existe `POST /api/registrarse` esto **ya no es la puerta principal**:
cualquiera se hace la cuenta desde la propia aplicacion. Sigue aqui para dos
casos en los que la aplicacion no sirve: crear la primera cuenta antes de que
nadie haya entrado, y dar de alta a alguien con el registro cerrado
(`CESTA_REGISTRO=cerrado`).

Las reglas son las mismas que las del formulario, y estan escritas una sola vez
en `plataforma/api/registro.py`. Si se copiaran aqui, acabarian siendo dos
reglas distintas: la consola aceptaria nombres que la web rechaza, y nadie
sabria cual de las dos manda.

Pide la contrasena por teclado y no la guarda en ningun sitio: en la base solo
queda su hash con Argon2id, que no se puede deshacer.
"""
from __future__ import annotations

import getpass
import sys

from plataforma.api import almacen, registro


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 2:
        print(__doc__)
        return 2
    usuario, nombre = registro.normaliza(args[0]), registro.limpia_nombre(args[1])

    clave = getpass.getpass(f"Contrasena para {usuario}: ")
    if clave != getpass.getpass("Otra vez, para estar seguros: "):
        print("no coinciden")
        return 2

    # Despues de teclearla, y no antes: preguntar dos veces la contrasena para
    # decir luego "el usuario es demasiado corto" es hacer trabajar en balde.
    if problema := registro.revisa(usuario, nombre, clave):
        print(problema)
        return 2

    almacen.arranca()
    try:
        creado = almacen.crea_usuario(usuario, nombre, clave)
    except almacen.UsuarioRepetido:
        print(f"ya hay una cuenta que se llama '{usuario}'")
        return 1
    finally:
        almacen.para()

    print(f"Creada la cuenta de {creado['nombre']} ({creado['usuario']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
