"""A01 — La publicacion por versiones tiene que ser **inmutable por si misma**.

**El defecto que estas pruebas fijan, medido el 12 de octubre de 2026.**

`publicar()` adoptaba el catalogo suelto con `os.link` -- *«para no duplicar un fichero de 195 MB»*.
Dos cosas estaban mal en esa frase:

1. **La cifra.** El fichero mayor de una publicacion es `precio_diario.parquet`, de **19,2 MB**.
2. **Y lo importante**: *un enlace duro **no aisla la version de lo que le pase al fichero suelto**.*

Y lo que le pasa es que **el pipeline lo reescribe in situ**. Con un enlace, esa escritura **cambia el
contenido de una version ya publicada**. *Asi se llego a una version llamada `20261007-103000` cuyo
`precio_diario.parquet` era del 11 de octubre.*

**La prueba que lo demuestra sin depender del disco del proyecto**: *se publica, se reescribe el suelto
**encima**, y se mira si la version se entero.* *Con `os.link` se enteraba; con copia, no.*
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from core import publicacion


@pytest.fixture()
def gold(tmp_path, monkeypatch):
    """Un `data/gold` de mentira, para no tocar el catalogo real ni sus enlaces."""
    carpeta = tmp_path / "gold"
    carpeta.mkdir()
    monkeypatch.setattr(publicacion, "GOLD", carpeta)
    monkeypatch.setattr(publicacion, "PUNTERO", carpeta / "actual.json")
    return carpeta


def _escribe(carpeta: Path, nombre: str, valor: int) -> None:
    pl.DataFrame({"n": [valor]}).write_parquet(carpeta / nombre)


def _lee(carpeta: Path, nombre: str) -> int:
    return int(pl.read_parquet(carpeta / nombre)["n"][0])


def _suelto_completo(carpeta: Path, valor: int = 1) -> None:
    for nombre in publicacion.FICHEROS:
        _escribe(carpeta, nombre, valor)


# --------------------------------------------------------------- el defecto ---

def test_reescribir_el_suelto_no_cambia_una_version_publicada(gold):
    """**La prueba del defecto.** *Es la que fallaba con `os.link`.*

    Se publica con el suelto en `1`, y despues **se reescribe el suelto encima** con `2` -- *que es lo
    que hace el pipeline*. La version publicada **tiene que seguir diciendo `1`**.
    """
    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    assert _lee(publicacion.carpeta_de(version), "grupos.parquet") == 1

    _suelto_completo(gold, 2)  # *el pipeline reescribe in situ*

    assert _lee(publicacion.carpeta_de(version), "grupos.parquet") == 1, (
        "la version publicada cambio por debajo: es el defecto del enlace duro"
    )
    assert _lee(gold, "grupos.parquet") == 2, "el suelto si cambio: eso es lo esperado"


def test_la_version_no_comparte_fichero_fisico_con_el_suelto(gold):
    """*Y por el camino corto*: publicado y suelto **no son el mismo fichero**.

    *Un enlace duro da el mismo inodo; una copia, no.* Es la comprobacion que se hizo con
    `fsutil hardlink list` sobre el catalogo real, aqui sin depender de Windows.
    """
    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    publicado = publicacion.carpeta_de(version) / "grupos.parquet"
    suelto = gold / "grupos.parquet"
    if not hasattr(publicado.stat(), "st_ino"):  # pragma: no cover
        pytest.skip("este sistema de ficheros no da numero de inodo")
    assert publicado.stat().st_ino != suelto.stat().st_ino, "siguen siendo el mismo fichero fisico"


# ------------------------------------------------------ la coherencia, por bytes ---

def test_el_puntero_guarda_la_huella_de_lo_publicado(gold):
    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    datos = json.loads((gold / "actual.json").read_text(encoding="utf-8"))
    assert set(datos["huellas"]) == set(publicacion.FICHEROS)
    assert all(len(h) == 64 for h in datos["huellas"].values())
    assert datos["huellas"] == publicacion.huellas(version)


def test_comprueba_dice_que_esta_bien_cuando_esta_bien(gold):
    _suelto_completo(gold, 1)
    publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    assert publicacion.comprueba() == {"cambiados": [], "ausentes": [], "sin_huella": []}


def test_comprueba_delata_una_version_alterada_por_debajo(gold):
    """**Lo que `/api/estado` no podia hacer con fechas.** *El nombre puede estar bien y el contenido no.*

    Se publica y despues se **escribe a mano** dentro de la carpeta de la version -- *que es
    exactamente el efecto que tenia un enlace duro con una escritura in situ*. La huella lo caza.
    """
    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    _escribe(publicacion.carpeta_de(version), "grupos.parquet", 99)  # *alteracion por debajo*

    r = publicacion.comprueba()
    assert r["cambiados"] == ["grupos.parquet"], r
    assert r["ausentes"] == [] and r["sin_huella"] == []


def test_comprueba_delata_un_fichero_que_falta(gold):
    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    (publicacion.carpeta_de(version) / "enlaces.parquet").unlink()
    r = publicacion.comprueba()
    assert r["ausentes"] == ["enlaces.parquet"] and r["cambiados"] == []


def test_una_version_de_antes_sin_huellas_se_dice_no_se_lo_que_paso(gold):
    """*Y una version publicada antes de que existieran las huellas no se da por buena.*

    **No se puede afirmar que sea coherente ni que no lo sea** -- *y decir «sin_huella» es la unica
    respuesta honesta.* *Es la regla de toda la fase: lo que no se sabe se dice, y no se deja que se
    confunda con un cero.*
    """
    _suelto_completo(gold, 1)
    publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    datos = json.loads((gold / "actual.json").read_text(encoding="utf-8"))
    datos.pop("huellas")  # *como quedaria un puntero escrito por la version anterior*
    (gold / "actual.json").write_text(json.dumps(datos), encoding="utf-8")

    r = publicacion.comprueba()
    assert r["sin_huella"] == publicacion.FICHEROS
    assert r["cambiados"] == [] and r["ausentes"] == []


# ------------------------------------------------------------ el rollback ---

def test_volver_a_una_version_anterior_no_toca_ninguna_carpeta(gold):
    """Publicar **no borra**, y volver atras **no reescribe**: solo mueve el puntero."""
    _suelto_completo(gold, 1)
    primera = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))
    _suelto_completo(gold, 2)
    segunda = publicacion.adoptar(momento=datetime(2026, 10, 11, 12, 45))
    assert publicacion.version_actual() == segunda

    publicacion.fijar(primera)
    assert publicacion.version_actual() == primera
    assert _lee(publicacion.carpeta_de(primera), "grupos.parquet") == 1
    assert _lee(publicacion.carpeta_de(segunda), "grupos.parquet") == 2, "la otra sigue intacta"


def test_publicar_dos_veces_el_mismo_instante_no_sobrescribe(gold):
    _suelto_completo(gold, 1)
    momento = datetime(2026, 10, 7, 10, 30)
    publicacion.adoptar(momento=momento)
    with pytest.raises(ValueError):
        publicacion.adoptar(momento=momento)


# ------------------------------------------- la ruta que lo cuenta en la API ---

def test_la_ruta_de_publicacion_distingue_no_saber_de_estar_mal(gold, monkeypatch):
    """**La distincion que importa en la respuesta HTTP**, y la que costo el §6 de `F14`.

    *Tres estados, y no dos*: **bien**, **cambiado** y **sin_huella**. *El tercero **no es** el
    primero*: un puntero sin huellas -- *como el del catalogo real el 12 de octubre de 2026* -- no
    permite afirmar coherencia, y `coherente` tiene que salir **`None`**, no `True`.

    Y `no_cuadran` **no** cuenta los `sin_huella`: *si los contara, un catalogo que no se puede
    verificar pareceria un catalogo roto, que es la conclusion contraria a la verdad.*
    """
    from types import SimpleNamespace

    from plataforma.api import main as api

    # *Un `SimpleNamespace`, no una clase: dentro de un cuerpo de clase, `gold = gold` no resuelve al
    # valor de la fixture.* Es un rincon del lenguaje que costo una corrida, y se deja dicho.
    monkeypatch.setattr(api, "AJUSTES", SimpleNamespace(gold=gold))

    _suelto_completo(gold, 1)
    version = publicacion.adoptar(momento=datetime(2026, 10, 7, 10, 30))

    # *1) Con huellas y sin tocar: bien, y coherente de verdad.*
    r = api._comprueba_publicacion()
    assert r["version"] == version
    assert r["coherente"] is True and r["no_cuadran"] == [], r

    # *2) Sin huellas en el puntero: no se sabe -- y NO se dice que este bien.*
    datos = json.loads((gold / "actual.json").read_text(encoding="utf-8"))
    datos.pop("huellas")
    (gold / "actual.json").write_text(json.dumps(datos), encoding="utf-8")
    r = api._comprueba_publicacion()
    assert r["coherente"] is None, "un puntero sin huellas no acredita coherencia"
    assert r["no_cuadran"] == [], "«no se sabe» no es «esta mal»"
    assert set(r["por_fichero"].values()) == {"sin_huella"}

    # *3) Y con la huella puesta y el contenido cambiado: mal, y se dice cual.*
    datos["huellas"] = publicacion.huellas(version)
    datos["huellas"]["grupos.parquet"] = "0" * 64  # *una huella que no es la del fichero*
    (gold / "actual.json").write_text(json.dumps(datos), encoding="utf-8")
    r = api._comprueba_publicacion()
    assert r["coherente"] is False
    assert r["no_cuadran"] == ["grupos.parquet"], r
