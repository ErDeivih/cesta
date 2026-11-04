"""El manifiesto de publicacion decia «0 filas» y «cobertura: solo Lidl».

Dos mentiras del documento que se lee como contrato de lo publicado, medidas el 4 de
noviembre de 2026 sobre el manifiesto real de las 13:09:

    "precio_diario.parquet": {"sha256": "85e3d256aad0", "filas": 0, "bytes": 33873856}
    "alcampo": {"captura": "2026-11-03", "filas": 0, "de_hoy": false}
    "cobertura_declarada": {"lidl-2026-10-13": ..., "lidl-2026-10-14": ...}

El fichero tenia 2.527.902 filas; `_fuentes` contaba las de Alcampo como 0. La causa es
`pl.read_parquet(ruta, columns=[]).height`, que en polars devuelve **0** -- se pide el
recuento pidiendo cero columnas, y sin columnas no hay filas que contar.

Y la tercera: `cobertura_declarada` solo lleva lo que escriben los colectores en
`data/cobertura/`, que hoy es **solo Lidl**. De ahi salio el «solo Lidl tiene cobertura,
21 dias» que se lee en la ficha del agente: los otros cinco no declaran nada ahi, y el
manifiesto no tenia donde decir que trajeron 16.782 o 23.416 filas.

Lo que se fija aqui: el manifiesto cuenta las filas que hay de verdad y declara la
cobertura de **todas** las cadenas, con la fecha de la referencia.
"""
from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from core import config, manifiesto


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Un gold, un bronze y una politica de mentira, con el mismo formato que los de verdad."""
    gold = tmp_path / "gold"
    bronze = tmp_path / "bronze"
    cobertura = tmp_path / "cobertura"
    for carpeta in (gold, bronze, cobertura):
        carpeta.mkdir(parents=True, exist_ok=True)
    politica = tmp_path / "alcance.yml"
    politica.write_text("version: 5\n", encoding="utf-8")

    monkeypatch.setattr(manifiesto, "GOLD", gold)
    monkeypatch.setattr(manifiesto, "BRONZE", bronze)
    monkeypatch.setattr(manifiesto, "COBERTURA", cobertura)
    monkeypatch.setattr(manifiesto, "POLITICA", politica)
    monkeypatch.setattr(manifiesto, "MANIFIESTO", gold / "manifiesto.json")
    # La cobertura medida se calcula sobre `config.DATA`, que es la raiz de data/.
    monkeypatch.setattr(config, "DATA", tmp_path)

    def bronze_de(fuente: str, fecha: str, n: int) -> None:
        d = bronze / f"fuente={fuente}" / f"fecha={fecha}"
        d.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({"id_fuente": [f"{fuente}-{i}" for i in range(n)]}).write_parquet(
            d / "part.parquet")

    return {"gold": gold, "bronze": bronze, "cobertura": cobertura, "bronze_de": bronze_de}


def test_las_filas_del_manifiesto_son_las_que_tiene_el_fichero(entorno):
    """2.527.902 filas declaradas como 0 no es un redondeo: es un contrato que miente."""
    n = 1234
    pl.DataFrame({"fuente": ["alcampo"] * n}).write_parquet(
        entorno["gold"] / "precio_diario.parquet")

    datos = manifiesto.construye(date(2026, 11, 4))
    assert datos["ficheros"]["precio_diario.parquet"]["filas"] == n


def test_las_filas_de_cada_cadena_son_las_de_su_captura(entorno):
    entorno["bronze_de"]("alcampo", "2026-11-04", 23416)
    entorno["bronze_de"]("dia", "2026-11-04", 5712)

    datos = manifiesto.construye(date(2026, 11, 4))
    assert datos["fuentes"]["alcampo"]["filas"] == 23416
    assert datos["fuentes"]["dia"]["filas"] == 5712


def test_la_cobertura_no_es_solo_lo_que_declara_lidl(entorno):
    """El manifiesto tiene que poder decir cuantas filas trajo cada cadena.

    `cobertura_declarada` sigue siendo lo que cada colector declara de su propio alcance
    (Lidl: ofertas conocidas); lo que faltaba es la cobertura **medida** de las cinco
    cadenas de catalogo.
    """
    entorno["bronze_de"]("alcampo", "2026-11-03", 22776)
    entorno["bronze_de"]("alcampo", "2026-11-04", 23416)
    entorno["bronze_de"]("dia", "2026-11-04", 5712)
    (entorno["cobertura"] / "lidl-2026-11-04.json").write_text(
        '{"fuente": "lidl", "cobertura": "ofertas_semanales_parcial"}', encoding="utf-8")

    datos = manifiesto.construye(date(2026, 11, 4))
    por_cadena = datos["cobertura_medida"]
    assert set(por_cadena) >= {"alcampo", "dia"}, "las cadenas de catalogo tienen que estar"
    assert por_cadena["alcampo"]["filas"] == 23416
    assert por_cadena["alcampo"]["veredicto"] == "ok"
    assert por_cadena["alcampo"]["referencia_fecha"] == "2026-11-03"
    # Y lo que declara el colector sigue estando, sin mezclarse con lo medido.
    assert "lidl-2026-11-04" in datos["cobertura_declarada"]


def test_una_cadena_que_no_trajo_nada_hoy_se_ve_en_la_cobertura(entorno):
    """El 4/11/2026 Alcampo no trajo nada y esto tiene que leerse, no deducirse."""
    entorno["bronze_de"]("alcampo", "2026-11-03", 22776)
    entorno["bronze_de"]("dia", "2026-11-04", 5712)

    datos = manifiesto.construye(date(2026, 11, 4))
    assert datos["cobertura_medida"]["alcampo"]["veredicto"] == "sin datos"
    assert datos["cobertura_medida"]["alcampo"]["filas"] == 0
    assert any("alcampo" in a for a in datos["avisos"])


def test_el_manifiesto_sigue_saliendo_sin_bronze(entorno):
    """Nunca lanza: sin nada que medir, cada cadena sale «sin datos» y el aviso lo dice."""
    datos = manifiesto.construye(date(2026, 11, 4))
    assert datos["cobertura_medida"], "el manifiesto sale igual, sin reventar"
    assert all(v["veredicto"] == "sin datos" for v in datos["cobertura_medida"].values())
    assert datos["avisos"]
