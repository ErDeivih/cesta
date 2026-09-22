"""Crear una cuenta desde la aplicacion, con el registro abierto.

Abrir el registro cambia quien puede tocar la base de datos: hasta hoy hacia
falta una consola dentro del contenedor, y a partir de ahora basta con llegar a
la pagina. Hoy a esa pagina solo se llega desde Tailscale, y esa es la razon por
la que se puede abrir -- pero la razon vive fuera del codigo, asi que lo que
tiene que estar bien atado es todo lo demas.

Lo que se vigila aqui no es que funcione: es lo que **no** puede pasar.

    · que entre un nombre que se parece al de otra persona
    · que alguien coja `admin` y sus lineas pongan "anadido por admin"
    · que se guarde algo distinto de lo que se comprobo
    · que el tope por hora no frene nada
    · que `CESTA_REGISTRO=cerrado` no cierre de verdad

Y una que no es de seguridad y es la que motivo todo esto: **quien abre un
enlace de invitacion sin tener cuenta tiene que poder acabar dentro de la
lista**. Antes se quedaba mirando la pantalla de entrar.
"""
from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, main, registro

# ----------------------------------------------------------- las reglas ----

def test_un_usuario_normal_pasa():
    assert registro.revisa("david", "David", "unaclavelarga") is None


@pytest.mark.parametrize("usuario", ["", "ab", "a" * 25])
def test_el_largo_del_usuario(usuario):
    assert registro.revisa(usuario, "David", "unaclavelarga") is not None


@pytest.mark.parametrize("usuario", [
    "dav id",          # un espacio en medio
    "david!",          # signos
    "_david",          # tiene que empezar por letra o numero
    "davíd",           # tilde
])
def test_lo_que_no_vale_de_usuario(usuario):
    assert registro.revisa(usuario, "David", "unaclavelarga") is not None


def test_la_a_cirilica_no_cuela():
    """`dаvid` con la `а` de otro alfabeto se lee igual y es otra persona.

    Con listas compartidas eso deja una linea que pone "anadido por david" y no
    la anadio david. Es la suplantacion mas barata que hay y se corta en el
    unico sitio donde se puede cortar: al elegir el nombre.
    """
    cirilica = "dаvid"
    assert cirilica != "david"
    assert registro.revisa(cirilica, "David", "unaclavelarga") is not None


@pytest.mark.parametrize("usuario", ["admin", "ADMIN", "cesta", "sistema", "soporte"])
def test_los_nombres_reservados(usuario):
    assert registro.revisa(usuario, "David", "unaclavelarga") is not None


def test_la_clave_corta_no_pasa():
    assert "8 caracteres" in registro.revisa("david", "David", "corta12")


def test_la_clave_no_puede_ser_el_usuario():
    assert registro.revisa("davidpeve", "David", "DavidPeve") is not None


def test_hace_falta_un_nombre_para_ensenar():
    assert registro.revisa("david", "", "unaclavelarga") is not None


def test_se_comprueba_lo_mismo_que_se_guarda():
    """Normalizar despues de comprobar es como se cuelan los nombres raros."""
    assert registro.normaliza("  DaViD  ") .strip() == "david"
    assert registro.normaliza("  DAVID  ") == "david"
    assert registro.revisa("  DAVID  ", "David", "unaclavelarga") is None


def test_el_nombre_pierde_los_saltos_de_linea():
    assert registro.limpia_nombre("  David   Perez\n") == "David Perez"


# ------------------------------------------------------------- la ruta ----

class _Almacen:
    """Un almacen de mentira: recuerda a quien dio de alta y nada mas."""

    def __init__(self, ya_hay=(), altas_ultima_hora=0):
        self.cuentas = {u: {"id": "1", "usuario": u, "nombre": u} for u in ya_hay}
        self.altas = altas_ultima_hora
        self.creados: list[tuple[str, str]] = []

    def crea_usuario(self, usuario, nombre, clave):
        if usuario in self.cuentas:
            raise almacen.UsuarioRepetido(usuario)
        self.creados.append((usuario, nombre))
        self.cuentas[usuario] = {"id": "1", "usuario": usuario, "nombre": nombre}
        return self.cuentas[usuario]

    def entra(self, usuario, clave, dispositivo=None):
        yo = self.cuentas.get(registro.normaliza(usuario))
        return ("un-token", yo) if yo else None

    def altas_en_la_ultima_hora(self):
        return self.altas


@pytest.fixture
def api(monkeypatch):
    """El cliente, con el almacen sustituido. No hay PostgreSQL en las pruebas."""
    def montar(ya_hay=(), altas=0, abierto=True):
        falso = _Almacen(ya_hay, altas)
        for nombre in ("crea_usuario", "entra", "altas_en_la_ultima_hora"):
            monkeypatch.setattr(almacen, nombre, getattr(falso, nombre))
        monkeypatch.setattr(main, "AJUSTES",
                            replace(main.AJUSTES, registro_abierto=abierto))
        return TestClient(main.app), falso
    return montar


def test_se_crea_la_cuenta_y_se_entra_de_una_vez(api):
    """Sin esto haria falta escribir usuario y clave dos veces seguidas, y ademas
    la invitacion de una lista solo se aplica cuando ya hay sesion."""
    c, falso = api()
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "unaclavelarga"})
    assert r.status_code == 201
    assert r.json()["usuario"]["usuario"] == "ana"
    assert main.COOKIE in r.cookies
    assert falso.creados == [("ana", "Ana")]


def test_se_guarda_normalizado(api):
    c, falso = api()
    c.post("/api/registrarse", json={
        "usuario": "  ANA  ", "nombre": "  Ana   Lopez ", "clave": "unaclavelarga"})
    assert falso.creados == [("ana", "Ana Lopez")]


def test_el_usuario_cogido_lo_dice_con_su_nombre(api):
    c, _ = api(ya_hay=["ana"])
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "unaclavelarga"})
    assert r.status_code == 409
    assert "cogido" in r.json()["detail"]


def test_una_clave_corta_no_llega_a_crear_nada(api):
    c, falso = api()
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "corta"})
    assert r.status_code == 422
    assert falso.creados == []


def test_con_el_registro_cerrado_no_se_crea_nadie(api):
    """El ajuste existe para el dia que el servicio salga a internet. Si no
    cerrara de verdad, seria peor que no tenerlo: daria por resuelto algo que no
    lo esta."""
    c, falso = api(abierto=False)
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "unaclavelarga"})
    assert r.status_code == 403
    assert falso.creados == []


def test_el_tope_por_hora_frena(api):
    c, falso = api(altas=almacen.ALTAS_POR_HORA)
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "unaclavelarga"})
    assert r.status_code == 429
    assert falso.creados == []


def test_justo_por_debajo_del_tope_todavia_se_puede(api):
    """Un freno que se pasa de frenado es un fallo que parece una medida."""
    c, falso = api(altas=almacen.ALTAS_POR_HORA - 1)
    r = c.post("/api/registrarse", json={
        "usuario": "ana", "nombre": "Ana", "clave": "unaclavelarga"})
    assert r.status_code == 201
    assert falso.creados == [("ana", "Ana")]


def test_quien_hay_pide_sesion(api):
    """La lista de personas es la ventana que hace vigilable la puerta abierta,
    pero no tiene por que verla quien todavia no ha entrado."""
    c, _ = api()
    assert c.get("/api/personas").status_code == 401


# --------------------------------------------------- la web lo acompana ----

def test_la_pantalla_de_entrar_ofrece_crear_cuenta():
    """Quien llega con un enlace de invitacion casi nunca tiene cuenta. Si el
    camino de crearla no esta a la vista, el enlace sigue sin servir de nada."""
    from pathlib import Path
    web = Path(__file__).resolve().parents[1] / "plataforma" / "web"
    html = (web / "index.html").read_text(encoding="utf-8")
    js = (web / "app.js").read_text(encoding="utf-8")
    assert 'id="f-registro"' in html
    assert 'id="b-a-registro"' in html
    assert "/registrarse" in js
    # Y que justo despues de registrarse se aplique la invitacion, que es el
    # motivo entero de que esta pantalla exista.
    despues = js.split("/registrarse", 1)[1][:1200]
    assert "aplicaInvitacion" in despues


def test_la_consola_usa_las_mismas_reglas_que_el_formulario():
    """Dos sitios que dan de alta cuentas no pueden tener dos listas de reglas:
    la consola aceptaria nombres que la web rechaza y nadie sabria cual manda."""
    from pathlib import Path
    fuente = (Path(__file__).resolve().parents[1] / "plataforma" / "cuenta.py"
              ).read_text(encoding="utf-8")
    assert "registro.revisa" in fuente
    assert "registro.normaliza" in fuente
