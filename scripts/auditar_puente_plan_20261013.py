"""Diagnostico sin red ni bases reales; imprime el contrato del puente semanal.

No es una prueba de aceptacion verde: los numeros permiten contrastar el
comportamiento actual con la necesidad esperada de 300 g.
"""
import json
from contextlib import ExitStack
from unittest.mock import Mock, patch

from core import recetas
from plataforma.api import main


def main_auditoria():
    planes = [
        {"receta_id": 1, "version": 1, "fecha": "2026-10-19", "comensales": 4},
        {"receta_id": 2, "version": 1, "fecha": "2026-10-20", "comensales": 2},
    ]

    def leer(*args, **kwargs):
        return {
            "nombre": f"Receta {args[2]}", "version": 1, "raciones": 2,
            "ingredientes": [{"texto": "harina", "cantidad": 100, "unidad": "g",
                              "producto_id": "dia:fixture", "grupo_id": 1}],
        }

    insertar = Mock()
    with ExitStack() as pila:
        pila.enter_context(patch.object(main, "_acceso", return_value=None))
        pila.enter_context(patch.object(main.almacen, "lineas_de", return_value=[]))
        pila.enter_context(patch.object(main.almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(recetas, "conecta", return_value=Mock()))
        pila.enter_context(patch.object(recetas, "plan", return_value=planes))
        pila.enter_context(patch.object(recetas, "leer", side_effect=leer))
        usuario = {"id": "fixture"}
        previa = main.previa_del_plan("lista-fixture", "2026-10-19", "2026-10-25", usuario)
        recibo = main.traer_del_plan("lista-fixture", "2026-10-19", "2026-10-25", usuario)
    print(json.dumps({
        "naturaleza": "diagnostico controlado, sin persistencia real",
        "necesidad_correcta_g": 100 * 4 / 2 + 100 * 2 / 2,
        "cantidades_de_la_previa": [x["cantidad"] for x in previa["entrarian"]],
        "recibo": recibo,
        "unidades_de_compra_insertadas": [x.args[6] for x in insertar.call_args_list],
        "notas_insertadas": [x.args[7] for x in insertar.call_args_list],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main_auditoria()
