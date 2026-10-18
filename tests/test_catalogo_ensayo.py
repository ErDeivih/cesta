"""*** EL CATALOGO DE ENSAYO TIENE QUE CUADRAR CONSIGO MISMO. ***

*M00 pide «catalogo de ensayo pequeno y versionado», y el apartado 8 fija las cifras del escenario
obligatorio.* *Si el catalogo dice una cosa y los resultados esperados otra, el escenario no sirve
para aceptar nada: la prueba pasaria por comparar el banco consigo mismo.*

*Aqui se comprueba **aritmetica**, no buena voluntad.*

*Y las cifras no se inventan: son las del apartado 8 de la especificacion maestra.*
"""

import json
from pathlib import Path

CATALOGO = Path(__file__).resolve().parent.parent / "plataforma" / "ensayo" / "catalogo.json"


def lee() -> dict:
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def test_el_catalogo_es_versionado_y_se_declara_sintetico() -> None:
    d = lee()
    assert d["version"] == "ensayo-1", "la version tiene que estar escrita"
    assert d["sintetico"] is True, "un catalogo de ensayo no puede decir que es real"
    # *Y dice lo que NO es, para que nadie lo cite como catalogo de una cadena.*
    assert d["no_es"], "tiene que declarar lo que no es"
    assert any("precios observados" in x for x in d["no_es"])


def test_las_cantidades_del_escenario_cuadran() -> None:
    d = lee()
    e = d["escenario"]["resultados_esperados"]
    r = {x["id"]: x for x in d["escenario"]["recetas"]}

    # *Arroz: 150 de R1 + 200 de R2.*
    arroz = r["R1"]["necesita"]["cantidad"] + r["R2"]["necesita"]["cantidad"]
    assert arroz == e["arroz_total_g"] == 350

    # *Y con 100 g de despensa confirmada, el deficit es 250 y hace falta UN envase de 1 kg.*
    assert arroz - e["arroz_despensa_confirmada_g"] == e["arroz_deficit_g"] == 250
    # *Del envase de 1 kg quedan 750 g.*
    assert 1000 - e["arroz_deficit_g"] == e["arroz_restante_del_envase_g"] == 750

    # *Leche: 500 de R3 + 500 de R4 = 1 l, una botella.*
    leche = r["R3"]["necesita"]["cantidad"] + r["R4"]["necesita"]["cantidad"]
    assert leche == e["leche_total_ml"] == 1000
    assert e["leche_botellas"] == 1

    # *Huevos: 3 de R5, pack de 6, sobran 3.*
    assert r["R5"]["necesita"]["cantidad"] == e["huevos_total_ud"] == 3
    assert e["huevos_pack"] - e["huevos_total_ud"] == e["huevos_sobrantes_ud"] == 3

    # *Y si R1 pasa a cuatro raciones, necesita 300 g ella sola.*
    assert r["R1"]["necesita"]["cantidad"] * (4 / r["R1"]["raciones"]) == e["r1_a_cuatro_raciones_g"] == 300


def test_la_energia_no_se_confunde_con_la_ingesta() -> None:
    d = lee()
    e = d["escenario"]["resultados_esperados"]
    r = {x["id"]: x for x in d["escenario"]["recetas"]}
    # *2100 kcal son las CINCO preparaciones; 1050 es UNA racion de cada una.*
    assert e["energia_cinco_preparaciones_kcal"] == 2100
    assert e["una_racion_de_cada_kcal"] == 1050
    # *Y 1050 es la mitad de 2100: cinco recetas de dos raciones son diez raciones, y sumar una de
    # cada una es la mitad del total.* *Es una comprobacion que afirma algo; la version anterior
    # llevaba un `or True` al final y **no comprobaba nada**, que es peor que no tenerla.*
    assert e["una_racion_de_cada_kcal"] * 2 == e["energia_cinco_preparaciones_kcal"]
    # *R1: una racion 270, media 135.*
    assert r["R1"]["kcal_racion"] == 270
    assert r["R1"]["kcal_media_racion"] == 135
    assert r["R1"]["kcal_media_racion"] * 2 == r["R1"]["kcal_racion"]
    # *Y el catalogo avisa de que no es una ingesta total: la nota tiene que estar.*
    assert "NO una ingesta total" in d["escenario"]["nota_resultados"]


def test_gastar_y_comprar_no_son_la_misma_magnitud() -> None:
    d = lee()
    e = d["escenario"]["resultados_esperados"]
    # *42 centimos de arroz USADO no son 120 del envase que hay que COMPRAR.*
    assert e["coste_ingrediente_usado_cent"] == 42
    assert e["compra_necesaria_arroz_cent"] == 120
    assert e["coste_ingrediente_usado_cent"] != e["compra_necesaria_arroz_cent"]
    # *Y los tres envases suman 400 (120 + 100 + 180).*
    assert e["gasto_tres_envases_cent"] == 120 + 100 + 180
    assert "despensa no convierte en gratis" in d["escenario"]["nota_resultados"]


def test_dos_marcas_de_arroz_no_se_fusionan() -> None:
    d = lee()
    arroz = next(g for g in d["grupos"] if g["grupo_id"] == 900001)
    marcas = [p["marca"] for p in arroz["productos"]]
    eans = [p["ean"] for p in arroz["productos"]]
    # *Mismo grupo -- para poder compararlos -- y EAN distintos: NO son el mismo articulo.*
    assert len(marcas) == 2 and len(set(marcas)) == 2
    assert len(set(eans)) == 2, "dos marcas no pueden compartir EAN"
    # *Y el escenario no autoriza anadir otra marca de leche.*
    leche = next(g for g in d["grupos"] if g["grupo_id"] == 900002)
    assert len(leche["productos"]) == 1
