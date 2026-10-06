import polars as pl
import pytest

from projects.cesta.laboratorio_comparacion import evaluar, gtin, medir


def producto(**cambios):
    return {"fuente": "dia", "id_fuente": "a", "nombre": "Leche entera marca",
            "marca": "marca", "ean": "4006381333931", "cantidad": 1.0,
            "unidad_canon": "l", "cantidad_fiable": True, "grupo_id": 1, **cambios}


@pytest.mark.parametrize("codigo", [None, 4006381333931, "4006381333932", "x4006381333931",
                                     "00000000", "１２３４５６７８", "12345"])
def test_rechaza_gtin_invalido(codigo):
    assert gtin(codigo) is None


def test_ceros_de_representacion_no_crean_otro_gtin():
    assert gtin("4006381333931") == gtin("04006381333931")


@pytest.mark.parametrize("cambio", [{"marca": "otra"}, {"cantidad": 6},
                                   {"nombre": "Leche desnatada marca"}])
def test_mismo_ean_no_anula_contradicciones(cambio):
    assert evaluar(producto(), producto(**cambio))["estado"] == "conflicto"


def test_sin_prueba_no_es_identico_aunque_nombre_coincida():
    assert evaluar(producto(ean=None), producto(ean=None))["estado"] == "evidencia_insuficiente"
    assert evaluar(producto(), producto(cantidad_fiable=False))["estado"] == "gtin_sin_formato_verificado"
    assert evaluar(producto(), producto())["estado"] == "candidato_exacto_gtin"


def test_medicion_no_escribe_y_descubre_gtin_fuera_del_grupo(tmp_path):
    ruta = tmp_path / "catalogo.parquet"
    pl.DataFrame([producto(nutricion="{}", nutricion_por="100g"),
                  producto(fuente="otra", grupo_id=2, nutricion='{"kcal":0}',
                           nutricion_por="100g")]).write_parquet(ruta)
    antes = ruta.read_bytes()
    r = medir(ruta)
    assert r["pares_evaluados"] == 1
    assert r["fuentes"]["dia"]["nutricion_numerica_con_base"] == 0
    assert r["fuentes"]["otra"]["nutricion_numerica_con_base"] == 1
    assert ruta.read_bytes() == antes
    assert len(list(tmp_path.iterdir())) == 1


def test_datos_ausentes_no_aprueban(tmp_path):
    ruta = tmp_path / "vacio.parquet"
    pl.DataFrame({"fuente": []}).write_parquet(ruta)
    with pytest.raises(ValueError):
        medir(ruta)
