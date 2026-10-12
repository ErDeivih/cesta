"""A05 — Lidl: capturada y **no** comparable, y que la diferencia este dicha.

**El hallazgo, tal cual lo midio la revision del 12 de octubre de 2026.** *`plataforma/api/cesta.py`
enumeraba **cinco** cadenas, y `projects/cesta/run.py` tenia `ORDEN` con **seis** -- porque Lidl entra en
la captura.* **La diferencia entre las dos listas no estaba escrita en ningun sitio**, asi que se leia
como un descuido.

**Y no es un descuido, son dos cosas distintas:**
- **`CADENAS_QUE_SE_CAPTURAN`** (seis): de las que hay colector y se les pide el catalogo.
- **`CADENAS`** (cinco): de las que se puede **comparar precios**.

*`collectors/lidl.py` publica **ofertas semanales parciales**, no el surtido completo.* Meterlo en las
comparaciones haria que **pareciera tener precio para cosas que no cataloga** -- *y un «Lidl no lo tiene»
que en realidad es «no lo hemos capturado» es la clase de mentira que esta fase lleva cazando.*

**Estas pruebas no capturan nada**: *son de coherencia de las listas y de que el motivo se pueda decir.*
*Lo que NO acreditan -- y se dice -- es que la captura de Lidl funcione: **eso necesita red y una region
declarada**, y es el paso siguiente de A05.*
"""
from __future__ import annotations

from plataforma.api import cesta


def test_lidl_se_captura_pero_no_se_compara():
    """**La distincion, en una linea.** *Estaba en las dos listas y sin decirse.*"""
    assert "lidl" in cesta.CADENAS_QUE_SE_CAPTURAN, "Lidl tiene colector: se captura"
    assert "lidl" not in cesta.CADENAS, "y no entra en las comparaciones"


def test_lo_comparable_esta_dentro_de_lo_capturable():
    """*No se puede comparar lo que no se captura.* **Y esto es lo que la comprobacion de importacion
    vigila**: si alguien anade una cadena a `CADENAS` sin colector, salta al importar y no al comparar.
    """
    sobran = [c for c in cesta.CADENAS if c not in cesta.CADENAS_QUE_SE_CAPTURAN]
    assert sobran == [], f"se comparan y no se capturan: {sobran}"


def test_las_cinco_comparables_siguen_siendo_las_cinco():
    """**Las cinco de siempre, ni una mas.** *Y en orden alfabetico, que es como estaban.*"""
    assert cesta.CADENAS == ("alcampo", "aldi", "carrefour", "dia", "mercadona")


def test_las_seis_capturables_son_las_del_ejecutor():
    """**La lista de captura y el `ORDEN` del ejecutor tienen que decir lo mismo.**

    *Si divergen, se captura algo que la API no conoce -- o al reves, la API cree capturar algo que
    nadie pide.* **Se comprueba contra el ejecutor de verdad, importandolo**, y no contra una copia.
    """
    from projects.cesta import run

    assert set(run.ORDEN) == set(cesta.CADENAS_QUE_SE_CAPTURAN), (
        f"el ejecutor captura {sorted(run.ORDEN)} y la API declara "
        f"{sorted(cesta.CADENAS_QUE_SE_CAPTURAN)}")


def test_el_motivo_de_lidl_se_puede_decir_en_pantalla():
    """*Y no es «no se compara» a secas*: **el motivo nombra la causa** -- ofertas parciales --, para que
    quien lea sepa que **no falta un dato, falta un surtido.** *Es «cobertura parcial visible».*
    """
    motivo = cesta.por_que_no_se_compara("lidl")
    assert motivo is not None
    assert "ofertas semanales parciales" in motivo
    assert "no cubren el catálogo" in motivo


def test_una_cadena_comparable_no_tiene_motivo():
    """*Si se compara, no hay nada que explicar.* **Y decir un motivo donde no lo hay seria ruido.**"""
    for cadena in cesta.CADENAS:
        assert cesta.por_que_no_se_compara(cadena) is None, cadena


def test_una_cadena_desconocida_lo_dice_sin_inventarse_una_razon():
    """*Y aqui esta la distincion que importa*: **«Lidl no se compara porque publica ofertas parciales» y
    «Eroski no se compara porque no lo conocemos» son dos frases distintas.** *La segunda no puede
    disfrazarse de la primera.*
    """
    motivo = cesta.por_que_no_se_compara("eroki")
    assert motivo is not None
    assert "no es una cadena conocida" in motivo
    assert "ofertas" not in motivo, "no se le atribuye a una desconocida una razon que no consta"


def test_los_precios_de_una_cadena_no_comparable_no_entran_aunque_se_pidan():
    """**Lo que de verdad protege la lista.** *Pedir Lidl explicitamente no lo mete en la comparacion.*

    *Es la linea `disponibles = [c for c in (cadenas or CADENAS) if c in CADENAS]`*: **filtra contra
    `CADENAS`, no contra lo que llegue.** *Aunque un cliente liste las seis, solo pasan las cinco.*
    """
    disponibles = [c for c in ("lidl", "mercadona", "alcampo") if c in cesta.CADENAS]
    assert disponibles == ["mercadona", "alcampo"]
    assert "lidl" not in disponibles, "Lidl no puede colarse por pedirlo"
