"""La cobertura diaria, medida sin mentir: el dia que se tiraba por una rama de folleto.

**El 4 de noviembre de 2026 Alcampo trajo 23.416 productos con cero errores y su bronze
del dia no se escribio.** El control de cobertura vio una rama hundida:

    Folletos y Promociones: 1472 -> 727 (51% menos)

y, como la regla era «una rama hundida veta la captura entera», se conservo la de ayer.
Pero esa rama **no es una estanteria: es el folleto de la campana**, y su contenido lo
pone la campana de la semana. Las otras quince ramas de comida **subieron** ese dia
(Frescos +6%, Perfumeria +10%, Drogueria +15%, Bebe +38%). Se tiraron 23.416 precios
frescos -- y con ellos el dia, que es el que hace once de treinta que falta.

Lo que se fija aqui:

  1. una rama de folleto hundida **no veta** la captura, pero **se sigue diciendo**;
  2. una rama de estanteria hundida **sigue vetando** (el caso Frescos del 18/09/2026,
     que es para lo que existe el control);
  3. la excepcion es de la cadena que la tiene, no universal;
  4. el informe dice **contra que fecha** mide: hoy decia «corta» sin decir que la vara
     era un dia atipico del 17/10/2026 (28.022 cuando lo normal era 22.800-24.300), y
     «corta» sin eso se lee como «Alcampo esta roto», que no es lo mismo.
"""
from __future__ import annotations

import polars as pl
import pytest

from core import cobertura
from projects.cesta import cobertura_diaria


def _frame(ramas: dict[str, int], fuente: str = "alcampo") -> pl.DataFrame:
    filas = []
    for rama, n in ramas.items():
        for i in range(n):
            filas.append({"fuente": fuente, "id_fuente": f"{rama}-{i}",
                          "nombre": "x", "categoria": f"{rama} > sub"})
    return pl.DataFrame(filas)


@pytest.fixture
def bronze(tmp_path, monkeypatch):
    def escribe(ramas, fuente="alcampo", fecha="2026-11-03"):
        d = tmp_path / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
        d.mkdir(parents=True, exist_ok=True)
        _frame(ramas, fuente).write_parquet(d / "part.parquet")
    monkeypatch.setattr(cobertura.config, "DATA", tmp_path)
    return escribe


# --- 1. la rama de folleto: no veta, pero se dice ---------------------------

def test_la_rama_de_folletos_no_tira_la_captura(bronze):
    bronze({"Frescos": 2657, "Folletos y Promociones": 1472, "Alimentacion": 3320})
    hoy = _frame({"Frescos": 2812, "Folletos y Promociones": 727, "Alimentacion": 3379})

    assert cobertura.que_vetan(hoy, "alcampo") == [], (
        "el folleto de la campana no puede costar el dia entero de precios frescos")


def test_pero_el_folleto_hundido_se_sigue_diciendo(bronze):
    bronze({"Frescos": 2657, "Folletos y Promociones": 1472})
    hoy = _frame({"Frescos": 2812, "Folletos y Promociones": 727})

    caidas = cobertura.revisa(hoy, "alcampo")
    assert any(c.startswith("Folletos y Promociones: 1472 -> 727") for c in caidas), (
        "silenciar la caida seria el defecto contrario: se guarda, pero se cuenta")


# --- 2. una rama de estanteria sigue vetando ------------------------------

def test_una_rama_de_estanteria_hundida_sigue_vetando(bronze):
    bronze({"Frescos": 2657, "Folletos y Promociones": 1472, "Alimentacion": 3320})
    hoy = _frame({"Frescos": 91, "Folletos y Promociones": 1472, "Alimentacion": 3379})

    vetan = cobertura.que_vetan(hoy, "alcampo")
    assert any(c.startswith("Frescos: 2657 -> 91") for c in vetan), (
        "el caso del 18/09/2026 (Frescos entera perdida) no puede dejar de vetar")


def test_un_folleto_y_un_fresco_hundidos_a_la_vez_siguen_vetando(bronze):
    """La excepcion no puede tapar una rama de verdad: veta la de estanteria."""
    bronze({"Frescos": 2657, "Folletos y Promociones": 1472})
    hoy = _frame({"Frescos": 91, "Folletos y Promociones": 727})

    vetan = cobertura.que_vetan(hoy, "alcampo")
    assert len(vetan) == 1 and vetan[0].startswith("Frescos:")


# --- 3. la excepcion es de quien la tiene ---------------------------------

def test_la_excepcion_no_se_hereda_a_otra_cadena(bronze):
    """En DIA una rama llamada igual seria una estanteria mas, y hundirse veta."""
    bronze({"Folletos y Promociones": 1472, "Congelados": 900}, fuente="dia")
    hoy = _frame({"Folletos y Promociones": 727, "Congelados": 900}, fuente="dia")

    assert cobertura.que_vetan(hoy, "dia"), (
        "la excepcion del folleto es de Alcampo, no una regla universal")


# --- 4. el caso real, con sus numeros ------------------------------------

def test_el_caso_real_de_alcampo_del_4_de_noviembre(bronze):
    """Las ramas medidas ese dia, en bronze: solo el folleto bajo, todo lo demas subio."""
    bronze({"Alimentacion": 3320, "Perfumeria": 2910, "Frescos": 2657,
            "Desayuno y Merienda": 2656, "Bebidas": 2399, "Drogueria": 1351,
            "Leche, Huevos, Lacteos, Yogures y Bebidas vegetales": 1039,
            "Congelados": 999, "Bebe": 623, "Folletos y Promociones": 1472})
    hoy = _frame({"Alimentacion": 3379, "Perfumeria": 3207, "Frescos": 2812,
                  "Desayuno y Merienda": 2641, "Bebidas": 2464, "Drogueria": 1558,
                  "Leche, Huevos, Lacteos, Yogures y Bebidas vegetales": 1095,
                  "Congelados": 1025, "Bebe": 861, "Folletos y Promociones": 727})

    assert cobertura.que_vetan(hoy, "alcampo") == []
    caidas = cobertura.revisa(hoy, "alcampo")
    assert len(caidas) == 1 and caidas[0].startswith("Folletos y Promociones:")


# --- 5. el informe dice contra que mide -----------------------------------

def test_el_veredicto_dice_de_que_dia_es_la_referencia():
    """«Corta» sin decir contra que no se puede interpretar.

    El 17/10/2026 Alcampo trajo 28.022 cuando lo normal era 22.800-24.300. Ese dia
    es la referencia de todos los dias siguientes, y hasta hoy el informe lo callaba:
    una captura de 23.416 -- que supera a la de ayer -- salia «corta» y punto.
    """
    serie = {"2026-11-03": 22776, "2026-11-02": 22813, "2026-10-31": 22697,
             "2026-10-30": 24297, "2026-10-24": 23460, "2026-10-17": 28022,
             "2026-11-04": 23416}
    v = cobertura_diaria.veredicto(serie, "2026-11-04", dias=19)
    assert v["referencia"] == 28022
    assert v["referencia_fecha"] == "2026-10-17", "hay que poder ver que la vara es un dia suelto"
    assert v["pct"] == 83.6


def test_el_veredicto_dice_cuanto_cambio_contra_la_ultima_captura():
    """La otra mitad de la frase: 23.416 es +2,8 % sobre ayer, no una caida."""
    serie = {"2026-11-03": 22776, "2026-11-04": 23416}
    v = cobertura_diaria.veredicto(serie, "2026-11-04", dias=2)
    assert v["vs_anterior_pct"] == 2.8


def test_sin_captura_anterior_no_se_inventa_una_variacion():
    v = cobertura_diaria.veredicto({"2026-11-04": 23416}, "2026-11-04", dias=1)
    assert v["vs_anterior_pct"] is None, "sin dia anterior, la variacion es desconocida"
