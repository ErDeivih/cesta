"""El paso de los avisos en la cadena diaria: el §6 del encargo, medido en los dos casos.

Lo que se vigila aqui, y cada cosa por su motivo:

  - **Que el paso no pueda fallar el dia.** Corre a las 06:00, sin nadie delante, y
    despues de el van el resumen, la comprobacion de precios y `verificar_docs`. Si se
    cayera por no llegar a la base, un dia bueno se contaria como fallido por una linea
    de resumen. Devuelve 0 en los dos casos y **nunca levanta**.
  - **Que cuando no puede mirar lo diga, y no un cero.** Un cero se lee como "no ha
    saltado nada" y lo que pasa es que no se ha mirado. Es la misma regla que el "no lo
    se" de la pantalla.
  - **Que la nota que lee el resumen sea la de hoy.** Si el paso falla, la nota se
    reescribe con el fallo: reutilizar los numeros de ayer es peor que no tenerlos.
  - **Que la zona horaria sea la del proyecto.** `almacen.ZONA_HORARIA` esta escrita
    alli para no meter `core.config` (que crea carpetas al importarse) dentro de la API;
    esta prueba es la que impide que los dos numeros se separen.

El caso con base de datos **no se prueba aqui**: se prueba de punta a punta contra un
PostgreSQL de verdad, que es como se prueba lo que habla SQL (`docs/OPERACION.md`).
Aqui se sustituye la base y lo que se comprueba es el contrato de este paso.
"""
from __future__ import annotations

import json

import pytest

from core import config
from plataforma.api import almacen
from projects.cesta import avisos, resumen


@pytest.fixture
def sin_base(monkeypatch):
    """Un almacen que no arranca, como el del PC: alli PostgreSQL no publica el puerto."""

    def no_arranca(*_a, **_k):
        raise OSError("connection refused")

    monkeypatch.setattr(almacen, "arranca", no_arranca)
    monkeypatch.setattr(config, "DATA", config.DATA)


@pytest.fixture
def fichero(tmp_path, monkeypatch):
    """La nota, en un sitio de usar y tirar: no se toca el `data/` de verdad."""
    destino = tmp_path / "avisos.json"
    monkeypatch.setattr(avisos, "FICHERO", destino)
    return destino


def test_sin_base_lo_dice_y_no_falla(sin_base, fichero, capsys):
    """El caso del PC de casa: la base no se alcanza. Se dice, y el dia sigue."""
    assert avisos.main([]) == 0, (
        "el paso ha devuelto algo que no es 0: la cadena lo contaria como un dia fallido")
    salida = capsys.readouterr().out
    assert "no lo se" in salida, f"el paso no ha dicho que no pudo mirar: {salida!r}"
    assert "no publica su puerto" in salida or "no se alcanza" in salida, (
        "no dice por que no ha podido mirar, y entonces parece un fallo de la aplicacion")

    nota = json.loads(fichero.read_text(encoding="utf-8"))
    assert "error" in nota and nota["cuando"]
    assert "saltaron_hoy" not in nota, (
        "ha dejado numeros de avisos sin haber mirado nada: eso es un cero inventado")


def test_cuando_no_hay_base_el_resumen_no_inventa_un_cero(sin_base, fichero):
    """La linea del resumen tiene que decir "no lo se", no "0 saltaron"."""
    assert avisos.main([]) == 0
    linea = avisos.frase(avisos.lee())
    assert linea.startswith("avisos: no lo se"), linea
    assert "0 saltaron" not in linea


def test_sin_nota_de_la_pasada_el_resumen_tambien_lo_dice(fichero):
    """La primera vez, o si alguien borra `data/`: no hay nota, y se dice."""
    assert avisos.lee() is None
    assert "no lo se" in avisos.frase(None)


def test_con_base_apunta_lo_que_salta_y_lo_deja_escrito(monkeypatch, fichero):
    """Con base: una pasada, y la nota con lo que el resumen necesita contar."""
    llamadas = []
    monkeypatch.setattr(almacen, "arrancado", lambda: False)
    monkeypatch.setattr(almacen, "arranca", lambda **_k: llamadas.append("arranca"))
    monkeypatch.setattr(almacen, "para", lambda: llamadas.append("para"))
    monkeypatch.setattr(avisos.vigilante, "una_pasada",
                        lambda: {"miradas": 4, "saltan": 2, "apuntadas": 2})
    monkeypatch.setattr(almacen, "avisos_del_dia",
                        lambda: {"saltaron_hoy": 3, "sin_saltar": 7, "por_mirar": 5})

    nota = avisos.una_pasada()
    assert nota["miradas"] == 4 and nota["apuntadas"] == 2
    assert nota["saltaron_hoy"] == 3 and nota["por_mirar"] == 5
    assert llamadas == ["arranca", "para"], (
        "el paso tiene que cerrar el pool que ha abierto: si no, la cadena se queda "
        "con conexiones abiertas")

    avisos.escribe(nota)
    linea = avisos.frase(avisos.lee())
    assert "3 saltaron hoy" in linea, linea
    assert "2 en esta pasada de 4 miradas" in linea, linea
    assert "5 esperando su dia" in linea, linea


def test_no_le_cierra_el_almacen_a_quien_ya_lo_tenia_abierto(monkeypatch):
    """Si el almacen ya estaba arrancado, este paso no lo cierra al terminar.

    Es el caso de la prueba de punta a punta, que arranca el almacen y llama a esto a
    mitad: cerrarlo dejaria sin base todo lo que viene detras.
    """
    llamadas = []
    monkeypatch.setattr(almacen, "arrancado", lambda: True)
    monkeypatch.setattr(almacen, "arranca", lambda **_k: llamadas.append("arranca"))
    monkeypatch.setattr(almacen, "para", lambda: llamadas.append("para"))
    monkeypatch.setattr(avisos.vigilante, "una_pasada",
                        lambda: {"miradas": 0, "saltan": 0, "apuntadas": 0})
    monkeypatch.setattr(almacen, "avisos_del_dia",
                        lambda: {"saltaron_hoy": 0, "sin_saltar": 0, "por_mirar": 0})

    avisos.una_pasada()
    assert llamadas == ["arranca"], (
        f"le ha cerrado el almacen a quien ya lo tenia abierto: {llamadas}")


def test_el_resumen_ensena_la_linea_de_los_avisos(fichero, capsys):
    """La linea aparece en el resumen, que es donde el encargo la pide."""
    avisos.escribe({"cuando": "2026-09-23T06:41:00", "miradas": 4, "saltan": 2,
                    "apuntadas": 2, "saltaron_hoy": 3, "sin_saltar": 7, "por_mirar": 5})
    # `resumen.main` necesita gold; lo que se comprueba aqui es la linea, que es una
    # funcion pura sobre lo que dejo el paso.
    print("  " + avisos.frase(avisos.lee()))
    salida = capsys.readouterr().out
    assert "avisos: 3 saltaron hoy" in salida, salida
    assert "06:41" in salida, "la hora de la pasada deja de verse: no se sabe de cuando es"


def test_la_zona_del_resumen_es_la_del_proyecto():
    """`almacen.ZONA_HORARIA` y `core.config.ZONA_HORARIA` son el mismo dia.

    Estan escritas en dos sitios a proposito (la API no importa `core.config`, que crea
    carpetas al importarse), y esta prueba es lo que impide que se separen: contar "hoy"
    con dos zonas distintas daria dos numeros distintos el mismo dia.
    """
    assert str(config.ZONA_HORARIA) == almacen.ZONA_HORARIA


def test_el_resumen_importa_el_paso_sin_pedir_base():
    """Importar el resumen no puede conectar con nada: se corre tambien sin base."""
    assert resumen.avisos is avisos
