"""Reproduce tres contratos abiertos sin red ni operaciones contra bases.

Las dependencias del cierre se sustituyen antes de invocar el endpoint. No es
una aceptación HTTP ni un ensayo de PostgreSQL: es un diagnóstico controlado.
Ejecutar: uv run python -m scripts.auditar_cierre_y_banco_20261018
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from unittest.mock import patch

from core import banco_identidad, identidad
from plataforma.api import cesta, main


def audita() -> dict:
    linea = {
        "id": "linea-ensayo", "grupo_id": 7, "producto_id": None,
        "nombre_visto": "Arroz", "cantidad": 1, "en_carrito": True,
        "cadena_elegida": "dia", "producto_movido": False,
    }
    estimacion_vista = 100
    precio_nuevo = 120
    eventos: list[str] = []

    def guarda(*_args):
        eventos.append("guarda_compra")
        return {"compra_id": "ensayo", "total_cent": precio_nuevo}

    def estima(*_args):
        eventos.append("recalcula_estimacion_actual")
        return {"total_cent": precio_nuevo}

    with ExitStack() as stack:
        stack.enter_context(patch.object(main, "_acceso"))
        stack.enter_context(patch.object(main.almacen, "lineas_de", return_value=[linea]))
        stack.enter_context(patch.object(main.catalogo, "con_pasillos", side_effect=lambda x: x))
        stack.enter_context(patch.object(main.catalogo, "lineas_movidas", return_value={}))
        stack.enter_context(patch.object(main, "_con_autorizacion", side_effect=lambda x, _: x))
        stack.enter_context(patch.object(main.cesta, "coste_por_linea", return_value={}))
        stack.enter_context(patch.object(main.almacen, "cierra_compra", side_effect=guarda))
        stack.enter_context(patch.object(main.cesta, "estimacion", side_effect=estima))
        respuesta = main.cerrar_compra("lista-ensayo", {"id": "usuario-ensayo"})

    def candidatos(peticiones, _fecha):
        return {
            cesta._llave_candidato(p.grupo_id, p.producto_id, "aldi"):
                ("aldi:P1", 90, "Arroz", None, None, None, None, 90, True)
            for p in peticiones
        }

    with patch.object(cesta, "_candidatos", side_effect=candidatos), patch.object(
        cesta, "_promos_vigentes", return_value={}
    ):
        sin_tienda = cesta.coste_por_linea([linea])[linea["id"]]

    producto = identidad.Producto(
        fuente="ensayo", id_fuente="uno", nombre="Arroz 1 kg",
        marca="Ensayo", gtin="8412345678905",
    )
    sin_etiqueta = banco_identidad.mide([
        {"a": producto, "b": producto, "cierto": None,
         "estrato": "ensayo", "quien": "diagnostico"},
    ])["global"]
    mixto = banco_identidad.mide([
        {"a": producto, "b": producto, "cierto": valor,
         "estrato": "ensayo", "quien": "diagnostico"}
        for valor in (True, None)
    ])["global"]

    pendientes = [dict(linea, id="carro"), dict(linea, id="pendiente", en_carrito=False)]
    with patch.object(cesta, "estimacion", side_effect=lambda x: {"total_cent": 100 * len(x)}), patch.object(
        cesta, "coste_por_linea",
        side_effect=lambda x: {
            ln["id"]: {"cadena": "dia", "precio_cent": 100, "producto_id": "dia:P1"}
            for ln in x
        },
    ):
        cotizacion_lista = cesta.cotiza(pendientes)
        cotizacion_carro = cesta.cotiza([pendientes[0]])

    return {
        "alcance": "diagnostico con dobles; sin red ni escrituras en bases",
        "precio_cambiado": {
            "estimacion_vista": estimacion_vista,
            "precio_actual": precio_nuevo,
            "diferencia_esperada_con_lo_visto": precio_nuevo - estimacion_vista,
            "respuesta_endpoint": respuesta,
            "orden": eventos,
        },
        "tienda_elegida_ausente": {
            "elegida": linea["cadena_elegida"], "resultado_cierre": sin_tienda,
        },
        "etiqueta_desconocida": {
            "entrada_cierto": None, "exactos_mal_contados": sin_etiqueta["exactos_mal"],
        },
        "precision_con_etiquetas_mixtas": {
            "caso": "un exacto correcto etiquetado y otro exacto sin etiqueta",
            "precision_esperada_sobre_evaluables": 1.0,
            "precision_observada": mixto["precision"],
            "exactos_sin_etiqueta": mixto.get("exactos_sin_etiqueta"),
        },
        "alcance_cotizacion": {
            "sello_lista_entera": cotizacion_lista["sello"],
            "sello_carrito": cotizacion_carro["sello"],
            "mismos_precios_distinto_sello": cotizacion_lista["sello"] != cotizacion_carro["sello"],
        },
        "viaje_fijo_cent": getattr(cesta, "VIAJE_CENT", None),
    }


if __name__ == "__main__":
    print(json.dumps(audita(), ensure_ascii=True, indent=2))
