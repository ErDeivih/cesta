"""El control que faltaba: ¿falta media tienda?

El 18 de septiembre de 2026 Alcampo entrego 20.571 productos en vez de 23.573 y
la ejecucion se dio por **completa, con cero errores**. Faltaba la rama Frescos
entera -- 2.646 productos el dia anterior, 91 ese dia --, se escribio el bronze y
el catalogo salio a la app sin fruta, verdura, carne ni pescado.

Los tres controles que ya habia miran el TOTAL, y un total puede bajar un 13 %
por mil razones normales. Lo que no es normal es que una rama se quede en el 3 %
de lo que tenia mientras las demas siguen igual.
"""
import polars as pl
import pytest

from core import cobertura


def _frame(ramas: dict[str, int]) -> pl.DataFrame:
    filas = []
    for rama, n in ramas.items():
        for i in range(n):
            filas.append({"fuente": "alcampo", "id_fuente": f"{rama}-{i}",
                          "nombre": "x", "categoria": f"{rama} > sub"})
    return pl.DataFrame(filas)


@pytest.fixture
def bronze(tmp_path, monkeypatch):
    def escribe(ramas):
        d = tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-17"
        d.mkdir(parents=True, exist_ok=True)
        _frame(ramas).write_parquet(d / "part.parquet")
    monkeypatch.setattr(cobertura.config, "DATA", tmp_path)
    return escribe


def test_una_rama_de_bazar_hundida_no_veta_la_captura(bronze):
    """El caso real de Alcampo del 5 de octubre de 2026.

    La captura del dia traia 23.859 productos con 0 errores y se rechazo porque "Hogar y
    Decoracion" caia de 133 a 31. Esa rama es bazar: con la politica de alcance ni se pide, y
    **una rama excluida no puede vetar una captura incluida mejores alimentos**.
    """
    bronze({"Frescos": 2646, "Alimentacion": 3647, "Hogar y Decoracion": 133})
    hoy = _frame({"Frescos": 2600, "Alimentacion": 3600, "Hogar y Decoracion": 31})

    assert cobertura.revisa(hoy, "alcampo") == [], (
        "el bazar hundido no puede rechazar la captura: es justo lo que dejo a Alcampo sin datos")

    # Y el contraste, que es lo que demuestra que el filtro es lo que cambia el resultado: sin
    # filtrar, el control **si** protesta.
    sin_filtrar = cobertura.por_rama(hoy, "alcampo", solo_alcance=False)
    antes_sin_filtrar = cobertura.por_rama(
        _frame({"Frescos": 2646, "Alimentacion": 3647, "Hogar y Decoracion": 133}),
        "alcampo", solo_alcance=False)
    assert sin_filtrar["Hogar y Decoracion"] < antes_sin_filtrar["Hogar y Decoracion"] * 0.5


def test_una_rama_de_comida_hundida_si_avisa(bronze):
    """Lo otro: si lo que se hunde es comida, el control tiene que seguir protestando."""
    bronze({"Frescos": 2646, "Alimentacion": 3647})
    hoy = _frame({"Frescos": 91, "Alimentacion": 3600})
    caidas = cobertura.revisa(hoy, "alcampo")
    assert caidas, "una rama de frescos hundida tiene que seguir dando la voz"


def test_el_caso_real_de_frescos(bronze):
    bronze({"Frescos": 2646, "Alimentacion": 3647, "Bebidas": 2394})
    hoy = _frame({"Frescos": 91, "Alimentacion": 3433, "Bebidas": 2419})
    caidas = cobertura.revisa(hoy, "alcampo")
    assert len(caidas) == 1
    assert caidas[0].startswith("Frescos: 2646 -> 91")
    assert "97% menos" in caidas[0]


def test_un_dia_normal_no_da_falsa_alarma(bronze):
    # Un 10 % arriba o abajo en cada rama es el ruido de todos los dias.
    bronze({"Frescos": 2646, "Alimentacion": 3647})
    hoy = _frame({"Frescos": 2400, "Alimentacion": 3800})
    assert cobertura.revisa(hoy, "alcampo") == []


def test_una_rama_pequena_no_cuenta(bronze):
    # Que una rama de 30 productos no salga un dia es normal; no vale la pena
    # tirar una captura entera por eso.
    bronze({"Frescos": 2646, "Rarezas": 30})
    hoy = _frame({"Frescos": 2646})
    assert cobertura.revisa(hoy, "alcampo") == []


def test_el_minimo_es_relativo_al_tamano_del_catalogo():
    """Con un minimo fijo de 100 el control era inerte en las cadenas pequenas.

    Aldi tiene 2.065 productos en 100 categorias y ninguna llega a 100, asi que
    el control no podia saltar nunca. Se descubrio probando con un catalogo de
    mentira de 60 productos al que se le quitaba una rama de 24 -- el 40 % -- sin
    que nadie dijera nada.
    """
    assert cobertura.minimo_para_vigilar(60) == 20        # suelo
    assert cobertura.minimo_para_vigilar(2065) == 41      # el 2 %
    assert cobertura.minimo_para_vigilar(52575) == 100    # techo


def test_en_un_catalogo_pequeno_tambien_salta(bronze):
    # 24 de 60 productos es el 40 % del catalogo: eso se tiene que ver.
    bronze({"frescos": 24, "bebidas": 15, "limpieza": 12, "congelados": 9})
    hoy = _frame({"bebidas": 15, "limpieza": 12, "congelados": 9})
    caidas = cobertura.revisa(hoy, "alcampo")
    assert len(caidas) == 1 and caidas[0].startswith("frescos: 24 -> 0")


def test_una_rama_que_desaparece_del_todo(bronze):
    bronze({"Frescos": 2646, "Alimentacion": 3647})
    hoy = _frame({"Alimentacion": 3647})
    caidas = cobertura.revisa(hoy, "alcampo")
    assert len(caidas) == 1 and "-> 0" in caidas[0]


def test_sin_bronze_anterior_no_hay_con_que_comparar(tmp_path, monkeypatch):
    monkeypatch.setattr(cobertura.config, "DATA", tmp_path)
    assert cobertura.revisa(_frame({"Frescos": 10}), "alcampo") == []


def test_la_rama_de_dia_sale_de_su_url():
    # DIA guarda la categoria como URL completa, no como arbol.
    assert cobertura._rama(
        "https://www.dia.es/congelados-y-helados/helados-y-hielo/c/L2130",
        "dia") == "congelados-y-helados"


# --- la cadena dijo que bien y no dejo bronze ------------------------------
#
# 18 de septiembre de 2026, 08:26: alcampo termina con 20.571 productos y cero
# errores. 08:52: su carpeta de bronze de ese dia ya no esta. Nunca se supo quien
# la borro; lo grave fue que nada se entero. El pipeline tiro con la instantanea
# del dia anterior y en gold quedaron 20.559 filas imposibles de recalcular.

def _particion(raiz, fuente, fecha):
    d = raiz / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
    d.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"x": [1]}).write_parquet(d / "part.parquet")


@pytest.fixture
def disco(tmp_path, monkeypatch):
    monkeypatch.setattr(cobertura.config, "DATA", tmp_path)
    return tmp_path


def test_se_denuncia_la_cadena_que_no_dejo_bronze(disco):
    _particion(disco, "aldi", "2026-09-18")
    _particion(disco, "alcampo", "2026-09-17")     # la de ayer si esta
    assert cobertura.sin_bronze(["aldi", "alcampo"], "2026-09-18") == ["alcampo"]


def test_si_todas_dejaron_bronze_no_se_dice_nada(disco):
    _particion(disco, "aldi", "2026-09-18")
    _particion(disco, "dia", "2026-09-18")
    assert cobertura.sin_bronze(["aldi", "dia"], "2026-09-18") == []


def test_las_particiones_se_leen_como_pares_de_cadena_y_fecha(disco):
    _particion(disco, "dia", "2026-09-17")
    _particion(disco, "dia", "2026-09-18")
    assert cobertura.particiones_bronze() == {("dia", "2026-09-17"),
                                              ("dia", "2026-09-18")}


def test_sin_bronze_ninguno_todas_estan_perdidas(disco):
    # El primer dia de la vida del proyecto no pasa por aqui: el orquestador solo
    # pregunta por las cadenas que dicen haber terminado bien.
    assert cobertura.sin_bronze(["aldi"], "2026-09-18") == ["aldi"]


# --- bronze apartado a mano, que no es lo mismo que bronze perdido ---------
#
# `docs/OPERACION.md`: un bronze malo se aparta, no se borra. El 18 de septiembre
# de 2026 se estuvo un dia entero dando por perdida una particion de alcampo que
# estaba enterita en data/debug/descartados, apartada esa misma manana por venir
# sin la rama Frescos.

def test_se_lee_el_motivo_del_nombre_de_la_carpeta(disco):
    (disco / "debug" / "descartados" /
     "alcampo-2026-09-18-sin-frescos").mkdir(parents=True)
    assert cobertura.apartados() == {("alcampo", "2026-09-18"): "sin frescos"}


def test_un_apartado_sin_motivo_tambien_se_lee(disco):
    (disco / "debug" / "descartados" / "dia-2026-09-11-").mkdir(parents=True)
    assert cobertura.apartados() == {("dia", "2026-09-11"): "sin motivo apuntado"}


def test_una_carpeta_con_nombre_raro_no_se_interpreta(disco):
    (disco / "debug" / "descartados" / "notas").mkdir(parents=True)
    (disco / "debug" / "descartados" / "alcampo-no-es-fecha-x").mkdir(parents=True)
    assert cobertura.apartados() == {}


def test_sin_carpeta_de_descartados_no_falla(disco):
    assert cobertura.apartados() == {}
