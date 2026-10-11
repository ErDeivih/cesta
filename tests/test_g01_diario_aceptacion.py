"""G01: la aceptación del diario, tal como la fija `docs/SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`.

Tres cosas que **no** cubre `test_de_la_ficha_al_diario.py`, y que son las que el documento pide:

1. **Los números exactos del caso de aceptación**, para que el día que alguien toque la cuenta se
   vea que cambió: *ficha de 200 kcal / 10 g proteína / 5 g grasa / 20 g hidratos por 100 g, 150 g
   consumidos → 300 kcal, 15 g, 7,5 g y 30 g.*
2. **La cobertura por nutriente**, que es lo que impide leer el subtotal como el día entero: con una
   segunda entrada de energía desconocida y 12 g de proteína, la energía sigue en 300 y la proteína
   pasa a 27, **con cobertura 1/2 y 2/2**. Sin esto, «300 kcal» parece el día y no lo es.
3. **Que dos comidas legítimas del mismo alimento se registren las dos.** El documento lo dice al
   revés de como se escribe una deduplicación por descuido: *«no deduplicar solo por nombre, fecha y
   nutrientes»*. Lo que hay que impedir es que un **reintento de la misma operación** duplique, no
   que dos meriendas iguales existan.
"""
from __future__ import annotations

import pytest

from core import diario

FICHA = {"kcal_100g": 200.0, "proteinas_100g": 10.0,
         "grasas_100g": 5.0, "hidratos_100g": 20.0}


# --- 1. los números del caso de aceptación ---------------------------------

def test_los_numeros_exactos_del_caso_de_aceptacion():
    """150 g de una ficha de 200/10/5/20 por 100 g: 300, 15, 7,5 y 30."""
    valores = diario.de_ficha(FICHA, 150)
    assert valores["kcal"] == pytest.approx(300.0)
    assert valores["proteinas_g"] == pytest.approx(15.0)
    assert valores["grasas_g"] == pytest.approx(7.5)
    assert valores["hidratos_g"] == pytest.approx(30.0)


def test_la_mitad_de_la_porcion_es_la_mitad_de_todo():
    """Y no se multiplica dos veces: 50 g son un tercio de 150, en los cuatro."""
    valores = diario.de_ficha(FICHA, 50)
    assert valores["kcal"] == pytest.approx(100.0)
    assert valores["proteinas_g"] == pytest.approx(5.0)
    assert valores["grasas_g"] == pytest.approx(2.5)
    assert valores["hidratos_g"] == pytest.approx(10.0)


# --- 2. la cobertura por nutriente -----------------------------------------

def test_energia_conocida_y_proteina_con_cobertura_distinta(tmp_path):
    """La segunda entrada no trae energía y sí proteína: 300 kcal, 27 g, y coberturas 1/2 y 2/2.

    **Éste es el caso que impide leer «300 kcal» como el día entero.** La energía se sabe de una de
    las dos entradas y la proteína de las dos, y el día tiene que decirlo con esos dos números, no
    con un total que parece completo.
    """
    con = diario.conecta(tmp_path / "diario.db")
    diario.apunta_de_ficha(con, "david", "2026-10-11", "comida", producto=FICHA,
                           gramos=150, referencia="dia:1")
    diario.apunta(con, "david", "2026-10-11", "merienda",
                  kcal=None, proteinas_g=12.0, fuente_dato=diario.DESCONOCIDO)

    dia = diario.dia(con, "david", "2026-10-11")
    conocido = dia["conocido"]
    assert conocido["kcal"] == pytest.approx(300.0), "la energía conocida no se toca"
    assert conocido["proteinas_g"] == pytest.approx(27.0), "15 + 12"

    cobertura = dia["cobertura"]
    assert cobertura["kcal"]["con_dato"] == 1 and cobertura["kcal"]["total"] == 2
    assert cobertura["kcal"]["completa"] is False
    assert cobertura["proteinas_g"]["con_dato"] == 2 and cobertura["proteinas_g"]["total"] == 2
    assert cobertura["proteinas_g"]["completa"] is True

    assert dia["completo"] is False, "el día no está completo: falta la energía de una entrada"
    assert len(dia["sin_dato"]) == 1, "y se dice cuál falta"


def test_un_nutriente_que_no_trae_nadie_se_dice_sin_dato_y_no_cero(tmp_path):
    """La grasa no la trae ninguna de las dos: `None`, no 0."""
    con = diario.conecta(tmp_path / "diario.db")
    diario.apunta(con, "david", "2026-10-11", "comida", kcal=300.0, proteinas_g=15.0)
    dia = diario.dia(con, "david", "2026-10-11")
    assert dia["conocido"]["grasas_g"] is None
    assert dia["cobertura"]["grasas_g"]["con_dato"] == 0


def test_un_cero_publicado_es_un_dato_y_cuenta_como_conocido(tmp_path):
    """«Sin grasas» es una afirmación legítima: 0 con dato es distinto de 0 por ausencia."""
    con = diario.conecta(tmp_path / "diario.db")
    diario.apunta(con, "david", "2026-10-11", "comida", grasas_g=0.0)
    dia = diario.dia(con, "david", "2026-10-11")
    assert dia["conocido"]["grasas_g"] == pytest.approx(0.0)
    assert dia["cobertura"]["grasas_g"]["con_dato"] == 1


# --- 3. dos comidas legítimas, y el reintento ------------------------------

def test_dos_comidas_legitimas_del_mismo_alimento_son_dos(tmp_path):
    """Comer dos veces lo mismo es normal. Deduplicar por nombre y fecha lo prohibiría."""
    con = diario.conecta(tmp_path / "diario.db")
    for _ in range(2):
        diario.apunta(con, "david", "2026-10-11", "merienda", kcal=100.0, proteinas_g=1.0)
    dia = diario.dia(con, "david", "2026-10-11")
    assert len(dia["entradas"]) == 2, "dos operaciones distintas son dos entradas"
    assert dia["conocido"]["kcal"] == pytest.approx(200.0)


def test_la_identidad_de_la_entrada_es_su_id_no_su_contenido(tmp_path):
    """Lo que impide duplicar un reintento es la **clave de la operación**, no el parecido."""
    con = diario.conecta(tmp_path / "diario.db")
    primera = diario.apunta(con, "david", "2026-10-11", "comida", kcal=300.0)
    segunda = diario.apunta(con, "david", "2026-10-11", "comida", kcal=300.0)
    assert primera != segunda, "cada alta devuelve su identificador"


# --- 4. lo que no se puede anotar ------------------------------------------

def test_una_compra_no_es_consumo(tmp_path):
    """Comprar no registra nada en el diario: lo dice el propio almacén."""
    con = diario.conecta(tmp_path / "diario.db")
    with pytest.raises(ValueError):
        diario.apunta(con, "david", "2026-10-11", "comida", tipo="compra")


def test_los_valores_negativos_y_no_finitos_no_entran(tmp_path):
    con = diario.conecta(tmp_path / "diario.db")
    for malo in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            diario.apunta(con, "david", "2026-10-11", "comida", kcal=malo)


def test_la_comida_tiene_que_ser_una_de_las_suyas(tmp_path):
    """`comida` es el hueco del día, y se valida: no vale cualquier texto."""
    con = diario.conecta(tmp_path / "diario.db")
    with pytest.raises(ValueError):
        diario.apunta(con, "david", "2026-10-11", "almuerzo de empresa", kcal=100.0)


# --- 5. el aislamiento entre dos personas, en el almacén -------------------

def test_el_dia_de_una_persona_no_ve_el_de_otra(tmp_path):
    """La misma fecha, dos propietarios: cada uno ve lo suyo y el borrado no cruza."""
    con = diario.conecta(tmp_path / "diario.db")
    de_a = diario.apunta(con, "ana", "2026-10-11", "comida", kcal=300.0)
    diario.apunta(con, "luis", "2026-10-11", "comida", kcal=900.0)

    assert len(diario.dia(con, "ana", "2026-10-11")["entradas"]) == 1
    assert diario.dia(con, "ana", "2026-10-11")["conocido"]["kcal"] == pytest.approx(300.0)
    assert diario.dia(con, "luis", "2026-10-11")["conocido"]["kcal"] == pytest.approx(900.0)

    # **Y no se puede borrar lo de otra persona ni sabiendo su identificador.**
    assert diario.borrar(con, "luis", de_a) is False
    assert len(diario.dia(con, "ana", "2026-10-11")["entradas"]) == 1

# --- 6. la idempotencia por operacion --------------------------------------

def test_la_misma_operacion_dos_veces_no_duplica(tmp_path):
    """Un doble clic, o un reintento con la respuesta perdida, **no** crean otra entrada.

    Y no se consigue mirando si se parece a otra: se consigue con **la clave que manda quien
    envia**. Es la unica que distingue un reintento de una comida nueva.
    """
    con = diario.conecta(tmp_path / "diario.db")
    primera = diario.apunta(con, "david", "2026-10-11", "comida", kcal=300.0,
                            clave_operacion="op-abc")
    segunda = diario.apunta(con, "david", "2026-10-11", "comida", kcal=300.0,
                            clave_operacion="op-abc")
    assert primera == segunda, "la segunda devuelve la entrada que ya habia, no una nueva"
    assert len(diario.dia(con, "david", "2026-10-11")["entradas"]) == 1
    assert diario.dia(con, "david", "2026-10-11")["conocido"]["kcal"] == pytest.approx(300.0)


def test_dos_operaciones_distintas_con_lo_mismo_son_dos(tmp_path):
    """Dos meriendas iguales de verdad: el documento pide que **se puedan** registrar."""
    con = diario.conecta(tmp_path / "diario.db")
    a = diario.apunta(con, "david", "2026-10-11", "merienda", kcal=100.0, clave_operacion="op-1")
    b = diario.apunta(con, "david", "2026-10-11", "merienda", kcal=100.0, clave_operacion="op-2")
    assert a != b
    assert len(diario.dia(con, "david", "2026-10-11")["entradas"]) == 2


def test_sin_clave_sigue_funcionando_como_antes(tmp_path):
    """La clave es opcional: quien no la mande se comporta como siempre. Los registros viejos,
    que no la tienen, no pueden chocar entre si."""
    con = diario.conecta(tmp_path / "diario.db")
    diario.apunta(con, "david", "2026-10-11", "comida", kcal=100.0)
    diario.apunta(con, "david", "2026-10-11", "comida", kcal=100.0)
    assert len(diario.dia(con, "david", "2026-10-11")["entradas"]) == 2


def test_la_clave_no_cruza_entre_personas(tmp_path):
    """Cada uno con su clave: la de uno no devuelve la entrada del otro."""
    con = diario.conecta(tmp_path / "diario.db")
    de_ana = diario.apunta(con, "ana", "2026-10-11", "comida", kcal=300.0, clave_operacion="op-x")
    de_luis = diario.apunta(con, "luis", "2026-10-11", "comida", kcal=900.0, clave_operacion="op-x")
    assert de_ana != de_luis
    assert diario.dia(con, "ana", "2026-10-11")["conocido"]["kcal"] == pytest.approx(300.0)
    assert diario.dia(con, "luis", "2026-10-11")["conocido"]["kcal"] == pytest.approx(900.0)
