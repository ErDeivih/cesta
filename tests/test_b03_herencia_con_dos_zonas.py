"""B03 · **La herencia de `grupo_id` cuando un grupo se parte** -- medido, y NO es un defecto.

**Que se creyo, y que es de verdad.** *El 13 de octubre de 2026 se midio `estabiliza` con «dos zonas» y se
concluyo que habia un fallo: **uno de los dos grupos recibia un id nuevo**.* *Al escribir esta prueba, el caso
**normal** -- dos productos que ayer estaban juntos -- **hizo exactamente lo mismo**.*

```
ayer:  grupo_id 7 = {lidl:1, lidl:2}
hoy:   grupo 10 = {lidl:1}   grupo 11 = {lidl:2}
       -> 10 hereda el 7  ·  11 recibe el 8
```

**Y eso NO es un fallo: es un grupo que se PARTE.** *Dos productos que ayer se emparejaron y hoy no -- porque
cambio un formato, un nombre o una zona -- **dejan de ser un grupo**.* *Uno conserva el numero de ayer y el otro
empieza.* **Que es lo unico que se puede hacer: no hay dos numeros de ayer que repartir.**

**Y LO IMPORTANTE, que es lo que la medida del 13 de octubre no miro:** *el desempate **es determinista**
(`sort(["miembros", "grupo_viejo", "grupo_nuevo"], descending=[True, False, False])`, y su comentario dice
justamente que es para que salga igual en el PC y en el contenedor).* *Asi que **con las mismas entradas, sale
el mismo resultado todos los dias** -- y `grupo_id` **no oscila**.*

**Lo que si queda dicho, y es lo unico que hay que respetar cuando la zona entre en `grupos_de`:** *con dos
zonas, `tabla_de` guardara **dos filas con la misma `clave`**, y el `join` de `estabiliza` tendra **un empate
cada dia**.* *Determinista, si -- pero **un empate**, y **conviene que la clave de esa tabla lleve la zona para
que no haya que desempatar**.* *Que es una mejora, no un arreglo.*
"""
from __future__ import annotations

import polars as pl

from core import grupos_ids


def _ayer(juntos: bool = True) -> pl.DataFrame:
    """*La tabla que la pasada de ayer dejo en disco.* **Y `juntos` dice si ayer eran un grupo o dos.**"""
    return pl.DataFrame({
        "clave": ["lidl:1", "lidl:2", "dia:9"],
        "grupo_id": [7, 7, 3] if juntos else [7, 8, 3],
    })


def test_lo_que_no_cambia_conserva_su_numero():
    """**El caso que importa de verdad**: *lo que era un grupo y sigue siendo el mismo, conserva su numero.*

    *Es para lo que existe `estabiliza`, y es lo que hay que proteger.*
    """
    hoy = pl.DataFrame({"clave": ["lidl:1", "lidl:2", "dia:9"], "grupo": [10, 10, 20]})
    salida = grupos_ids.estabiliza(hoy, _ayer())
    heredado = dict(zip(salida["clave"].to_list(), salida["grupo_id"].to_list(), strict=True))
    assert heredado == {"lidl:1": 7, "lidl:2": 7, "dia:9": 3}, (
        "un grupo que no cambia tiene que conservar su numero")


def test_un_grupo_que_se_parte_reparte_el_numero():
    """**Y cuando un grupo se parte, uno conserva el numero y el otro empieza.** *No hay otra cosa que hacer.*

    *Se creyo que esto era el defecto de las dos zonas, y se vio al escribir la prueba que **pasa igual sin
    zonas** -- con dos productos que dejan de emparejarse.* **Es el comportamiento correcto, y queda fijado para
    que no se «arregle» por error.**
    """
    hoy = pl.DataFrame({"clave": ["lidl:1", "lidl:2"], "grupo": [10, 11]})
    salida = grupos_ids.estabiliza(hoy, _ayer())
    ids = dict(zip(salida["grupo"].to_list(), salida["grupo_id"].to_list(), strict=True))
    assert ids[10] == 7, "uno de los dos tiene que conservar el 7 de ayer"
    assert ids[11] != 7, "y el otro no puede tener tambien el 7: seria el mismo numero para dos grupos"


def test_el_desempate_no_oscila_entre_dias():
    """**Y lo que de verdad habia que comprobar: que dos corridas den lo mismo.** *Que es lo que impide que
    `grupo_id` cambie de un dia para otro.*

    *Es la unica forma de que un historico no se parta* -- *y por eso el desempate esta escrito y ordenado en
    vez de dejarse «como salga».*
    """
    hoy = pl.DataFrame({"clave": ["lidl:1", "lidl:1", "lidl:2"], "grupo": [10, 11, 11]})
    primera = grupos_ids.estabiliza(hoy, _ayer())
    segunda = grupos_ids.estabiliza(hoy, _ayer())
    assert primera.equals(segunda), "las mismas entradas tienen que dar el mismo resultado"
