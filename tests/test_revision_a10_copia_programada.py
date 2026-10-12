"""La copia programada: **que no se guarde una copia vacia, y que la retencion se lleve las viejas.**

**Lo que estas pruebas fijan, y por que cada una.**

 1. **Un volcado vacio NO se guarda.** *Un fichero con nombre de copia y cero bytes es **peor que no tener
    copia**: el dia que se necesite, parecera que la hay.*
 2. **La retencion se lleva las VIEJAS.** *Al reves seria absurdo -- y hay que probarlo, porque un `sorted`
    mal puesto lo hace al reves sin quejarse.*
 3. **Hacer una copia no toca ningun contenedor de nadie.** *Es la leccion de los 716 usuarios: `docker
    exec` para leer, y escribir en un fichero.*
 4. **Dos copias en el mismo segundo no se pisan.** *Mejor un error claro que una copia sobrescrita.*

*Y nada de esto necesita Docker ni la base de casa:* **el volcado se sustituye**, que es lo que permite
probar la guarda del volcado vacio sin tener que romper una base de verdad.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timedelta

import pytest

from plataforma import copia_programada as C


@pytest.fixture()
def destino(tmp_path, monkeypatch):
    """Un `data/copias` de mentira, para no tocar las copias de verdad."""
    carpeta = tmp_path / "copias"
    monkeypatch.setattr(C, "DESTINO", carpeta)
    return carpeta


@pytest.fixture()
def sin_docker(monkeypatch):
    """*Da el contenedor por vivo y el volcado por bueno*, para no necesitar Docker."""
    monkeypatch.setattr(C, "esta_el_contenedor", lambda: True)
    monkeypatch.setattr(C, "volcado", lambda: b"-- un volcado de mentira\n" * 100)


# ================================================== lo que NO se guarda, nunca ===

def test_un_volcado_vacio_no_se_guarda(destino, monkeypatch):
    """**La guarda que impide la peor de las copias: la que parece una copia.**

    *Un `pg_dump` que falla a medias deja un fichero con la cabecera y nada mas* -- **y es exactamente lo
    que paso el 12 de octubre de 2026**: *643 bytes, que son la cabecera y ni una fila.* **Si eso se
    guardara con nombre de copia, el dia que hiciera falta se restauraria una base vacia.**
    """
    monkeypatch.setattr(C, "esta_el_contenedor", lambda: True)
    monkeypatch.setattr(C, "volcado", lambda: b"cabecera y nada mas\n")
    with pytest.raises(RuntimeError) as fallo:
        C.hace()
    assert "NO se guarda" in str(fallo.value)
    # *Y no ha dejado NADA escrito.* **Ni un fichero a medias.**
    assert not destino.exists() or list(destino.glob("*.sql")) == []


def test_si_el_contenedor_no_esta_se_dice_y_no_se_copia(destino, monkeypatch):
    """*Y sin base no hay copia que hacer.* **Se dice cual falta**, en vez de fallar por dentro."""
    monkeypatch.setattr(C, "esta_el_contenedor", lambda: False)
    with pytest.raises(RuntimeError) as fallo:
        C.hace()
    assert "no esta corriendo" in str(fallo.value)
    assert "cesta-db-1" in str(fallo.value), "el mensaje tiene que decir QUE contenedor falta"


def test_el_volcado_de_verdad_se_guarda_con_su_tamano(destino, sin_docker):
    """*Y cuando el volcado trae datos, se guarda entero.* **Sin recortarlo ni resumirlo.**"""
    camino = C.hace(momento=datetime(2026, 10, 12, 16, 0, 0))
    assert camino.name == "cesta-20261012-160000.sql"
    assert camino.read_bytes() == C.volcado()
    assert camino.stat().st_size > C.MINIMO_BYTES


def test_dos_copias_en_el_mismo_segundo_no_se_pisan(destino, sin_docker):
    """**Mejor un error claro que una copia sobrescrita.** *Y pasa: si algo llama dos veces seguidas, el
    sello tiene el mismo segundo.*"""
    momento = datetime(2026, 10, 12, 16, 0, 0)
    C.hace(momento=momento)
    with pytest.raises(ValueError):
        C.hace(momento=momento)


# ======================================================== la retencion, y su orden ===

def test_la_retencion_se_lleva_las_viejas_y_deja_las_nuevas(destino, sin_docker):
    """**El orden es lo unico que importa aqui, y al reves seria absurdo.**

    *Si algo va mal, la copia que se quiere es **la mas reciente**.* **Un `sorted` sin `reverse` se lleva
    justo las que hacen falta**, y no se queja: *borra ficheros y devuelve una lista.*
    """
    base = datetime(2026, 10, 12, 16, 0, 0)
    for i in range(5):
        C.hace(momento=base + timedelta(minutes=i))

    fuera = C.aplica_retencion(2)
    nombres = {x.name for x in fuera}
    # *Se van las tres primeras -- las de las 16:00, 16:01 y 16:02.*
    assert nombres == {"cesta-20261012-160000.sql", "cesta-20261012-160100.sql",
                       "cesta-20261012-160200.sql"}, nombres
    quedan = {x.name for x in C.copias()}
    assert quedan == {"cesta-20261012-160400.sql", "cesta-20261012-160300.sql"}, quedan


def test_con_retencion_de_una_solo_queda_la_ultima(destino, sin_docker):
    """*Y el caso extremo*: **una copia, la de ahora.**"""
    base = datetime(2026, 10, 12, 16, 0, 0)
    for i in range(3):
        C.hace(momento=base + timedelta(minutes=i))
    C.aplica_retencion(1)
    assert [x.name for x in C.copias()] == ["cesta-20261012-160200.sql"]


def test_si_hay_menos_copias_que_la_retencion_no_se_borra_ninguna(destino, sin_docker):
    """*Y no se borra por borrar.* **Con dos copias y retencion de siete, no se va ninguna.**"""
    base = datetime(2026, 10, 12, 16, 0, 0)
    C.hace(momento=base)
    C.hace(momento=base + timedelta(minutes=1))
    assert C.aplica_retencion(7) == []
    assert len(C.copias()) == 2


def test_sin_copias_la_retencion_no_falla(destino):
    """*Y sin nada que retener, tampoco revienta.*"""
    assert C.copias() == []
    assert C.aplica_retencion(3) == []


def test_listar_no_copia_nada(destino, sin_docker):
    """**`--listar` solo mira.** *Que una orden de consulta haga una copia seria una sorpresa cara.*"""
    C.hace(momento=datetime(2026, 10, 12, 16, 0, 0))
    antes = len(C.copias())
    assert C.main(["--listar"]) == 0
    assert len(C.copias()) == antes


# ============================================== y lo que NO se toca, que es la leccion ===

def test_hacer_una_copia_no_ejecuta_ningun_rm_ni_toca_otros_contenedores(destino, monkeypatch):
    """**La leccion de los 716 usuarios, escrita como prueba.**

    *La copia lee de `cesta-db-1` con `docker exec` y escribe en un fichero.* **No borra contenedores, ni
    toca el `5433`, ni toca la base de pruebas.** *Y se comprueba mirando **todo** lo que se ejecuta*,
    porque lo que se ejecuta es lo unico que puede hacer dano.
    """
    monkeypatch.setattr(C, "esta_el_contenedor", lambda: True)
    # *Y el volcado de mentira tiene que pasar el minimo de verdad*: con 900 bytes, la propia guarda
    # lo para -- **que es como se descubrio que 100 repeticiones se quedaban cortas.**
    monkeypatch.setattr(C, "volcado", lambda: b"-- datos\n" * 1000)

    ordenes: list[list[str]] = []
    de_verdad = subprocess.run

    def espia(args, **kw):
        ordenes.append(list(args))
        return de_verdad(args, **kw) if False else subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(C.subprocess, "run", espia)
    C.hace(momento=datetime(2026, 10, 12, 16, 0, 0))

    # *Y aqui esta lo que se afirma:* **ninguna orden lleva `rm`, ni `-f`, ni otro contenedor.**
    for orden in ordenes:
        assert "rm" not in orden, f"la copia no puede borrar nada: {orden}"
        assert "-f" not in orden, f"y menos a la fuerza: {orden}"
    # *Si se ejecuto algo, solo puede ser para leer o para mirar si esta vivo.*
    for orden in ordenes:
        assert orden[0] == "docker", orden
        assert orden[1] in ("exec", "inspect"), f"solo se lee: {orden}"
        if orden[1] == "exec":
            assert orden[2] == C.CONTENEDOR, f"solo se lee de {C.CONTENEDOR}: {orden}"
