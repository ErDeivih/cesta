"""El resumen diario: lo que se lee al terminar la ejecucion.

Una ejecucion que solo dice "hecho" no sirve para saber si el dia ha ido bien.
"""
import polars as pl

from projects.cesta import resumen
from projects.cesta.resumen import TOPE_CREIBLE, ahorro


def _catalogo(filas):
    return pl.DataFrame(filas, schema={
        "grupo_id": pl.Int32, "fuente": pl.Utf8, "nombre": pl.Utf8,
        "unidad_canon": pl.Utf8, "precio_unidad_cent": pl.Float64})


def test_un_grupo_de_una_sola_cadena_no_es_comparable():
    # "mas barato" no significa nada si solo lo vende un supermercado.
    d = _catalogo([
        {"grupo_id": 1, "fuente": "a", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 100.0},
        {"grupo_id": 1, "fuente": "a", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 200.0},
    ])
    assert len(ahorro(d)) == 0


def test_calcula_la_diferencia_entre_la_mas_barata_y_la_mas_cara():
    d = _catalogo([
        {"grupo_id": 1, "fuente": "a", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 100.0},
        {"grupo_id": 1, "fuente": "b", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 150.0},
    ])
    assert ahorro(d)["dif_pct"].item() == 50.0


def test_un_precio_a_cero_no_puede_dividir():
    d = _catalogo([
        {"grupo_id": 1, "fuente": "a", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 0.0},
        {"grupo_id": 1, "fuente": "b", "nombre": "Leche", "unidad_canon": "l",
         "precio_unidad_cent": 150.0},
    ])
    assert len(ahorro(d)) == 0


def test_las_diferencias_imposibles_se_pueden_separar():
    # 229.000% no es una ganga: es una unidad mal leida, y se avisa aparte.
    d = _catalogo([
        {"grupo_id": 1, "fuente": "a", "nombre": "Azafran", "unidad_canon": "ud",
         "precio_unidad_cent": 299.0},
        {"grupo_id": 1, "fuente": "b", "nombre": "Azafran", "unidad_canon": "ud",
         "precio_unidad_cent": 687500.0},
    ])
    assert ahorro(d)["dif_pct"].item() > TOPE_CREIBLE


# --- dias del historico que se quedaron sin bronze -------------------------
#
# El 18 de septiembre de 2026, probando la cadena entera sobre una copia limpia,
# el historico tenia 20.559 filas de alcampo fechadas ese dia y en bronze la
# ultima carpeta de alcampo era la del 17. El colector habia ido bien esa manana.
# Nada en el sistema lo decia.

def _monta(tmp_path, monkeypatch, historico, particiones_bronze, apartadas=()):
    gold = tmp_path / "gold"
    gold.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(historico, schema={"fuente": pl.Utf8, "fecha": pl.Utf8}) \
      .write_parquet(gold / "precio_diario.parquet")
    for fuente, fecha in particiones_bronze:
        d = tmp_path / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
        d.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({"x": [1]}).write_parquet(d / "part.parquet")
    for nombre in apartadas:
        (tmp_path / "debug" / "descartados" / nombre).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(resumen.config, "DATA", tmp_path)
    monkeypatch.setattr(resumen.cobertura.config, "DATA", tmp_path)


def test_un_dia_del_historico_sin_rastro_se_denuncia(tmp_path, monkeypatch):
    _monta(tmp_path, monkeypatch,
           [{"fuente": "alcampo", "fecha": "2026-09-17"},
            {"fuente": "alcampo", "fecha": "2026-09-18"},
            {"fuente": "alcampo", "fecha": "2026-09-18"}],
           [("alcampo", "2026-09-17")])
    assert resumen.dias_huerfanos() == [("alcampo", "2026-09-18", 2, "SIN RASTRO")]


def test_un_bronze_apartado_a_proposito_se_distingue_de_uno_perdido(tmp_path, monkeypatch):
    # El caso real del 18 de septiembre de 2026: no lo borro nadie, lo apartaron
    # esa manana por venir sin la rama Frescos, y estaba entero en descartados.
    _monta(tmp_path, monkeypatch,
           [{"fuente": "alcampo", "fecha": "2026-09-18"}],
           [("alcampo", "2026-09-17")],
           apartadas=["alcampo-2026-09-18-sin-frescos"])
    assert resumen.dias_huerfanos() == [("alcampo", "2026-09-18", 1, "sin frescos")]


def test_si_todo_el_historico_tiene_bronze_no_se_dice_nada(tmp_path, monkeypatch):
    _monta(tmp_path, monkeypatch,
           [{"fuente": "aldi", "fecha": "2026-09-17"},
            {"fuente": "dia", "fecha": "2026-09-18"}],
           [("aldi", "2026-09-17"), ("dia", "2026-09-18")])
    assert resumen.dias_huerfanos() == []


def test_sin_bronze_ninguno_no_se_acusa_a_todo_el_historico(tmp_path, monkeypatch):
    # Una copia de solo-gold (la plataforma monta gold sin bronze) no puede
    # ponerse a gritar que le faltan trece dias: no tiene con que compararlos.
    _monta(tmp_path, monkeypatch,
           [{"fuente": "aldi", "fecha": "2026-09-17"}], [])
    assert resumen.dias_huerfanos() == []
