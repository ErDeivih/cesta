"""**Las guardas del ensayo de restauracion se niegan cuando tienen que negarse.**

*Y esta es la prueba que hace que el ensayo se pueda ejecutar despues: *no se comprueba que **restaura
bien**, se comprueba que **se niega a restaurar donde no debe** -- *que es la mitad que puede destruir
algo.* *

*Todo aqui corre **sin Docker y sin bases**: *si estas guardas necesitaran un contenedor para probarse,
**no se probarian**, y una guarda que no se prueba es una intencion.* *
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
_ESPECIFICA = importlib.util.spec_from_file_location(
    "ensayo_de_restauracion", RAIZ / "scripts" / "ensayo_de_restauracion.py")
assert _ESPECIFICA and _ESPECIFICA.loader
ensayo = importlib.util.module_from_spec(_ESPECIFICA)
_ESPECIFICA.loader.exec_module(ensayo)


# ===================== los puertos: casa, facylf y las pruebas compartidas =====================

@pytest.mark.parametrize("puerto", [5432, 5433, 5434])
def test_los_tres_puertos_prohibidos_se_rechazan(puerto):
    """*** 5432 es casa, 5433 es facylf (ajeno) y 5434 son las pruebas compartidas. *** *

    *Y se comprueba **por numero**: *el sistema no sabe que 5432 es casa, asi que «un puerto efimero no
    sera 5432» es confiar en una coincidencia.*
    """
    with pytest.raises(ensayo.DestinoNoSeguro) as fallo:
        ensayo.comprueba_puerto(puerto)
    assert str(puerto) in str(fallo.value), "y el mensaje dice CUAL"


def test_un_puerto_libre_nunca_es_de_los_prohibidos():
    """*Y no se confia: **se comprueba en el bucle**, cincuenta veces.*"""
    for _ in range(50):
        assert ensayo.puerto_libre() not in ensayo.PUERTOS_PROHIBIDOS


def test_un_puerto_normal_pasa():
    ensayo.comprueba_puerto(55001)  # *no levanta: es lo que se espera*


# ===================== el nombre: propio, unico, y no el de otro trabajo =====================

def test_un_nombre_de_otro_trabajo_se_rechaza():
    """*** Un contenedor que no es de este ensayo no se toca, aunque se llame parecido. ***"""
    for nombre in ensayo.NOMBRES_PROHIBIDOS:
        with pytest.raises(ensayo.DestinoNoSeguro) as fallo:
            ensayo.comprueba_nombre(nombre)
        assert nombre in str(fallo.value)


def test_un_nombre_SIN_prefijo_se_rechaza():
    """*Un nombre sin prefijo **podria pertenecer a otro trabajo**: *y con un nombre constante, **podria
    ser el de otro**.*"""
    with pytest.raises(ensayo.DestinoNoSeguro):
        ensayo.comprueba_nombre("cesta-db-ensayo")


def test_el_nombre_del_ensayo_lleva_prefijo_y_es_unico():
    """*Ni constante ni previsible: **dos ensayos a la vez no pueden pisarse.**"""
    nombres = {ensayo.nombre_unico() for _ in range(20)}
    assert len(nombres) == 20, "los nombres tienen que ser unicos"
    for uno in nombres:
        assert uno.startswith(ensayo.PREFIJO)
        ensayo.comprueba_nombre(uno)  # *y pasan la guarda*


# ===================== el DSN: loopback, con base, y fuera de los prohibidos =====================

def test_un_dsn_al_puerto_de_casa_se_rechaza():
    with pytest.raises(ensayo.DestinoNoSeguro):
        ensayo.comprueba_dsn("postgresql://cesta:x@127.0.0.1:5432/cesta")


def test_un_dsn_que_no_es_loopback_se_rechaza():
    """*** El encargo prohibe publicar nada: el destino tiene que ser loopback. ***"""
    for host in ("10.0.0.5", "192.168.1.20", "example.test"):
        with pytest.raises(ensayo.DestinoNoSeguro) as fallo:
            ensayo.comprueba_dsn(f"postgresql://cesta:x@{host}:55001/cesta_ensayo")
        assert "loopback" in str(fallo.value)


def test_un_dsn_sin_base_se_rechaza():
    """*Una base sin nombre **no es un destino**: es una conexion a la nada.*"""
    for dsn in ("postgresql://cesta:x@127.0.0.1:55001", "postgresql://cesta:x@127.0.0.1:55001/"):
        with pytest.raises(ensayo.DestinoNoSeguro):
            ensayo.comprueba_dsn(dsn)


def test_un_dsn_sin_puerto_se_rechaza():
    """*Sin puerto explicito, PostgreSQL usa **5432** -- *y **5432 es casa**.*"""
    with pytest.raises(ensayo.DestinoNoSeguro):
        ensayo.comprueba_dsn("postgresql://cesta:x@127.0.0.1/cesta_ensayo")


def test_un_dsn_correcto_pasa():
    ensayo.comprueba_dsn("postgresql://cesta:ensayo@127.0.0.1:55001/cesta_ensayo")


# ===================== la limpieza: solo lo que lleva LA etiqueta =====================

def test_no_se_borra_un_contenedor_que_no_lleva_la_etiqueta(monkeypatch):
    """*** Lo que no se pueda acreditar como propio, NO SE TOCA. *** *

    *Y se acredita con **la etiqueta**, no con el nombre: *el prefijo **lo puede escribir cualquiera**;
    *la etiqueta **la pone este ensayo al crear**.* *Asi que un contenedor con el prefijo pero **sin**
    etiqueta **no se borra**, y el ensayo lo dice.*
    """
    monkeypatch.setattr(ensayo, "contenedores_con_etiqueta", lambda: ["cesta-restauro-otro"])
    with pytest.raises(ensayo.DestinoNoSeguro) as fallo:
        ensayo.limpia_lo_propio("cesta-restauro-impostor")
    assert "etiqueta" in str(fallo.value)


def test_la_limpieza_solo_mira_los_etiquetados(monkeypatch):
    """*Y borra **los suyos**: ni uno mas.*"""
    vistos: list[list[str]] = []

    def falso_run(orden, **k):
        vistos.append(list(orden))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(ensayo.subprocess, "run", falso_run)
    monkeypatch.setattr(ensayo, "contenedores_con_etiqueta",
                        lambda: ["cesta-restauro-a", "cesta-restauro-b"])
    borrados = ensayo.limpia_lo_propio()
    assert borrados == ["cesta-restauro-a", "cesta-restauro-b"]
    # *Y cada borrado lleva `-v`, para llevarse tambien su volumen: **es suyo, y lo creo el mismo.** *
    for orden in vistos:
        if orden[:2] == ["docker", "rm"]:
            assert "-v" in orden, orden


# ===================== y el plan dice el destino sin tocar nada =====================

def test_el_plan_no_toca_docker(capsys, monkeypatch):
    """*`--plan` **decide el destino y pasa las guardas**, y **no crea nada**: *es lo que permite revisarlo
    antes de que exista.*"""
    def no_llames(*a, **k):  # pragma: no cover - *si se llama, el ensayo falla abajo*
        raise AssertionError("el plan ha llamado a Docker")

    monkeypatch.setattr(ensayo.subprocess, "run", no_llames)
    monkeypatch.setattr(ensayo.sys, "argv", ["ensayo", "--plan"])
    assert ensayo._cli() == 0
    salida = capsys.readouterr().out
    assert "cesta-restauro-" in salida, salida
    assert "5432" in salida and "5433" in salida and "5434" in salida, salida


# ===================== la base: tiene que estar VACIA =====================

class _CursorFalso:
    """*Un cursor de mentira que contesta lo que se le diga.* *Sin base y sin Docker.*"""

    def __init__(self, cuantas):
        self.cuantas = cuantas
        self.pregunta = None

    def execute(self, sql):
        self.pregunta = sql

    def fetchone(self):
        return (self.cuantas,)


def test_una_base_con_tablas_se_rechaza():
    """*** Una base con datos de alguien NO es un destino desechable. *** *

    *Y esta guarda existia **solo como regla escrita** hasta que se implemento: *es la septima vez en esta
    sesion que **una afirmacion sobrevive al codigo que la describia** -- *y la primera en que la escribo
    yo en el mismo commit que la declara.*
    """
    with pytest.raises(ensayo.DestinoNoSeguro) as fallo:
        ensayo.comprueba_base_vacia(_CursorFalso(7))
    assert "7 tablas" in str(fallo.value), "y el mensaje dice CUANTAS"


def test_una_base_vacia_pasa():
    ensayo.comprueba_base_vacia(_CursorFalso(0))


def test_la_guarda_pregunta_por_el_esquema_public():
    """*Y por `public`, que es **el que el guion viejo borraba**: *es el que hay que saber si tiene algo.*"""
    cur = _CursorFalso(0)
    ensayo.comprueba_base_vacia(cur)
    assert "information_schema.tables" in cur.pregunta, cur.pregunta
    assert "public" in cur.pregunta, cur.pregunta
