"""El vigilante tiene que poder avisar aunque la recoleccion no llegue a arrancar.

El 6/11/2026 el vigilante vivia al final de `ejecutar.bat`: si el Programador no
lanzaba ese .bat, el vigilante tampoco corria y el fallo se quedaba callado. Esta
prueba no arranca tareas de Windows (eso no cabe en pytest): vigila el cableado
que hace posible el aviso independiente.

Lo que se comprueba:
  - hay un .bat propio del vigilante, y llama al script con `--solo-fallos`;
  - deja un aviso visible y refresca las metricas del panel;
  - espera y reintenta antes de dar el fallo (evita el falso positivo del arranque);
  - hay un registrador con el nombre y la hora de la tarea, y su accion es el .bat.
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _texto(nombre: str) -> str:
    return (RAIZ / nombre).read_text(encoding="utf-8")


def test_el_vigilante_tiene_su_propio_bat_y_usa_solo_fallos():
    bat = _texto("ejecutar-vigilante.bat")

    assert "scripts.vigilar_ingesta" in bat
    assert "--solo-fallos" in bat, (
        "sin --solo-fallos un aviso conocido convertiria un dia bueno en fallido"
    )
    assert "projects.cesta.metricas" in bat, "el panel no se enteraria del estado"
    assert "Start-Sleep -Seconds 300" in bat, (
        "sin segunda mirada, el arranque del PC puede dar un falso «no arranco»"
    )
    assert "INGESTA-DETENIDA.txt" in bat, "el aviso tiene que quedar a la vista"
    assert "avisos_ingesta.log" in bat


def test_el_registrador_declara_la_tarea_con_su_hora_y_su_accion():
    ps = _texto("registrar-vigilante.ps1")

    assert "Cesta vigilante" in ps
    assert "ejecutar-vigilante.bat" in ps
    assert "New-ScheduledTaskAction" in ps
    assert "New-ScheduledTaskTrigger -Daily -At 2:00pm" in ps
    assert "AtLogOn" in ps, "un dia con el PC apagado a las 14:00 tambien se mira"
    assert "StartWhenAvailable" in ps


def test_el_vigilante_no_depende_del_bat_de_la_recoleccion():
    """El .bat del dia puede seguir llamandolo, pero el aviso no depende de eso."""
    diario = _texto("ejecutar.bat")
    assert "scripts.vigilar_ingesta" in diario
    # El propio, en cambio, no *llama* a la recoleccion: solo la nombra en el aviso.
    propio = _texto("ejecutar-vigilante.bat")
    assert "call ejecutar.bat" not in propio
    assert "scripts.vigilar_ingesta --solo-fallos" in propio
