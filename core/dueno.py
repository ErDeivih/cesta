"""**El dueno de lo privado, siempre como texto.** *Una vez, y para los dos nucleos.*

**Por que existe este fichero.** *`core/recetas.py` y `core/diario.py` **declaran el mismo contrato con
las mismas palabras**:*

    *** «**Privacidad, implementada** … *Cada receta/entrada tiene **propietario**, y *** todas ***
    las operaciones lo exigen.» ***

*-- *y **ninguno de los dos lo comprobaba.** *Los dos reciben `propietario: str` *y **se lo dan a SQLite
tal cual**, *que **no acepta un `UUID`.** *

*** Y se encontro midiendo ***, *el 14 de octubre de 2026, **al abrir `plataforma/prueba_e2e.py` a
Recetas**: *

    `sqlite3.ProgrammingError: Error binding parameter 3: type 'UUID' is not supported`

*Y **no era un modulo ni una funcion**: *era **la convencion**, *repetida en **quince funciones** entre
los dos ficheros* *(-- diez en el recetario, *cinco en el diario --), *y **no comprobada en ninguna.** *

**Y el criterio lo tenia escrito el proyecto** *, donde este error aparecio la primera vez
(`tests/test_revision_a09_compra_hogar.py:34-42`): *

    *** «El id, siempre como texto… *Es el mismo error de siempre: dar por hecho el tipo de un dato en
    vez de leerlo. *** Aqui se lee, y se convierte.» ***

*Asi que **se lee, y se convierte** -- *y **no se rechaza**: *un `UUID` de dueno **es el mismo dueno con
otro tipo**, *y rechazarlo romperia el uso legitimo de un ensayo que inyecta el usuario.* *

**Y por que aqui y no en cada nucleo.** *El encargo pide **no copiar**, *y el proyecto **ya decidio** en
un caso igual* *(-- `plataforma/api/cesta.py`, *donde **se nombro la distincion en las tres listas en vez
de unificarlas**, *y **se dejo escrito por que** --).* *Aqui **si se unifica**, *porque es **el mismo
contrato literal** *y **un tercer nucleo SQLite tendria que hacer lo mismo**: *una sola copia, *y **el
motivo escrito una vez.** *

**Por que no se ve por HTTP**: *el `id` de la sesion **ya es cadena** al leerlo de la base; *el `UUID`
solo aparece cuando lo inyecta un ensayo con `dependency_overrides[usuario_actual]`
*-- *que es **justo lo que hizo `prueba_e2e.py`**, *y **por eso lo encontro.*** *
"""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def dueno_como_texto(fn: F) -> F:
    """**Envuelve una funcion cuyo segundo argumento es el dueno**, *y lo convierte a texto.*

    *Se aplica a las funciones de los dos nucleos que declaran `propietario: str` como segundo
    parametro* *(-- `(con, propietario, ...)` --), *que es **la forma que los dos usan.** *

    *`None` **se deja pasar**: *las funciones ya lo rechazan con su propio `ValueError` *(-- «una receta
    necesita dueno» --), *y **ahogarlo aqui** seria **cambiar el mensaje de error de otro.** *
    """
    @functools.wraps(fn)
    def envuelto(con: Any, propietario: Any, *args: Any, **kwargs: Any) -> Any:
        if propietario is not None:
            propietario = str(propietario)
        return fn(con, propietario, *args, **kwargs)

    return envuelto  # type: ignore[return-value]
