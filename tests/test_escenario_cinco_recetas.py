"""*** EL ESCENARIO OBLIGATORIO DEL APARTADO 8, CON SUS NUMEROS. ***

*Cinco recetas, dos personas y dos listas.* *Este fichero cubre la parte que se puede comprobar
**sin base de datos ni contenedor**: las cinco recetas y la aritmetica de raciones.*

    R1  Arroz con leche de la casa  150 g de arroz + 500 ml de leche
    R2  Arroz al horno              200 g de arroz
    R3  Bechamel                    500 ml de leche
    R4  Salsa de leche              500 ml de leche
    R5  Tortilla de tres huevos     3 huevos

*Y las cifras que la especificacion da como buenas:*

    arroz para el plan ......... 150 + 200 = **350 g**, menos 100 de despensa = **250 g de deficit**
    leche ...................... 500 + 500 = **1 000 ml** (R1 y R3; R4 es otra salsa)
    huevos ..................... **3** de un envase de 6, sobran 3
    R1 a 4 raciones ............ 150 g x (4/2) = **300 g**

*No se inventan densidades, calorias ni equivalencias: solo se comprueba la regla de tres y las
sumas que la especificacion ya da.*
"""

import sqlite3
from pathlib import Path

import pytest

from core import recetas

# *Las cinco del apartado 8, con lo que cada una lleva. Las cantidades son las de la
# especificacion; las raciones de partida, las de la receta tal como se guarda.*
LAS_CINCO = [
    ("R1", "Arroz con leche de la casa", 2,
     [{"texto": "arroz", "cantidad": 150, "unidad": "g"},
      {"texto": "leche", "cantidad": 500, "unidad": "ml"}]),
    ("R2", "Arroz al horno", 2,
     [{"texto": "arroz", "cantidad": 200, "unidad": "g"}]),
    ("R3", "Bechamel", 2,
     [{"texto": "leche", "cantidad": 500, "unidad": "ml"}]),
    ("R4", "Salsa de leche", 2,
     [{"texto": "leche", "cantidad": 500, "unidad": "ml"}]),
    ("R5", "Tortilla de tres huevos", 2,
     [{"texto": "huevo", "cantidad": 3, "unidad": "ud"}]),
]


@pytest.fixture()
def libro(tmp_path: Path) -> sqlite3.Connection:
    con = recetas.conecta(tmp_path / "recetas.sqlite3")
    for _clave, nombre, raciones, ingredientes in LAS_CINCO:
        recetas.crear(con, "ana", nombre, raciones=raciones, ingredientes=ingredientes)
    return con


def test_las_cinco_recetas_son_cinco_y_de_su_dueno(libro: sqlite3.Connection) -> None:
    de_ana = recetas.listar(libro, "ana")
    assert len(de_ana) == 5
    assert {r["nombre"] for r in de_ana} == {n for _, n, _, _ in LAS_CINCO}


def test_b_no_ve_las_recetas_de_ana(libro: sqlite3.Connection) -> None:
    """*** Dos personas. *** *`listar` es «el recetario de quien pregunta».*"""
    assert recetas.listar(libro, "bea") == []


def test_el_arroz_del_plan_suma_350_g(libro: sqlite3.Connection) -> None:
    """*R1 lleva 150 y R2 lleva 200: **350 g**. Y la despensa tiene 100 confirmados.*"""
    total = 0.0
    for r in recetas.listar(libro, "ana"):
        if r["nombre"] not in ("Arroz con leche de la casa", "Arroz al horno"):
            continue
        detalle = recetas.leer(libro, "ana", r["id"])
        for ing in detalle["ingredientes"]:
            if ing["texto"] == "arroz":
                total += ing["cantidad"]
    assert total == 350.0
    assert total - 100.0 == 250.0, "el deficit del apartado 8, con los 100 g de despensa"


def test_la_leche_suma_mil_ml(libro: sqlite3.Connection) -> None:
    """*R1 y R3 llevan 500 ml cada una: **1 000 ml**.*"""
    total = 0.0
    for r in recetas.listar(libro, "ana"):
        if r["nombre"] not in ("Arroz con leche de la casa", "Bechamel"):
            continue
        for ing in recetas.leer(libro, "ana", r["id"])["ingredientes"]:
            if ing["texto"] == "leche":
                total += ing["cantidad"]
    assert total == 1000.0


def test_los_huevos_son_tres_de_un_envase_de_seis(libro: sqlite3.Connection) -> None:
    """*3 de 6: **sobran 3**.* *Y la receta se llama «Tortilla de tres huevos», no «media
    tortilla»: el nombre y la cantidad tienen que decir lo mismo.*"""
    tortilla = next(r for r in recetas.listar(libro, "ana")
                    if r["nombre"] == "Tortilla de tres huevos")
    huevos = [i for i in recetas.leer(libro, "ana", tortilla["id"])["ingredientes"]
              if i["texto"] == "huevo"]
    assert len(huevos) == 1
    assert huevos[0]["cantidad"] == 3
    assert 6 - huevos[0]["cantidad"] == 3, "sobran tres del envase"


def test_r1_a_cuatro_raciones_son_300_g_de_arroz(libro: sqlite3.Connection) -> None:
    """*** La regla de tres, con el numero que da la especificacion. ***"""
    r1 = next(r for r in recetas.listar(libro, "ana")
              if r["nombre"] == "Arroz con leche de la casa")
    detalle = recetas.leer(libro, "ana", r1["id"])
    escalados = recetas.escala(detalle["ingredientes"], detalle["raciones"], 4)
    arroz = next(i for i in escalados if i["texto"] == "arroz")
    assert arroz["cantidad"] == 300.0
    leche = next(i for i in escalados if i["texto"] == "leche")
    assert leche["cantidad"] == 1000.0


def test_lo_que_no_tiene_cantidad_no_la_gana() -> None:
    """*** `null` no es cero, y aqui se ve. ***
    *Un ingrediente anotado como «sal» sigue sin cantidad al escalar: la regla de tres no se
    puede aplicar a lo que no se sabe, e inventarle un cero seria convertir un dato que falta en
    un dato falso.*"""
    escalados = recetas.escala(
        [{"texto": "sal"}, {"texto": "arroz", "cantidad": 150, "unidad": "g"}], 2, 4)
    sal = next(i for i in escalados if i["texto"] == "sal")
    assert "cantidad" not in sal or sal["cantidad"] is None
    assert sal.get("cantidad") != 0, "un cero aqui seria mentira"
