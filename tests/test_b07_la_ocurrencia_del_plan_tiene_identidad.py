"""**La ocurrencia del plan tiene identidad: `(fecha, comida, receta_id)`, y `raciones` propias.**

*Antes la clave era `(fecha, receta_id)`, *y con ella **no se podia**: *poner la misma receta **dos veces
el mismo dia**, *decir **en cual de las comidas** va, *decir **cuantas raciones** se cocinan ahi,
*ni **copiar una semana** *(-- *que exige saber **que** copiar --).* *

*El plan **modelaba bien** «esta receta, este dia, para esta gente», *y **no modelaba la ocurrencia.** *
*Estos ensayos son **la prueba equivalente** de que ahora si.* *
"""
from __future__ import annotations

import sqlite3

import pytest

from core import recetas


@pytest.fixture
def con(tmp_path):
    c = recetas.conecta(tmp_path / "recetas.sqlite")
    yield c
    c.close()


def _una_receta(con, nombre="Tortilla", raciones=4) -> int:
    return recetas.crear(con, "yo", nombre, raciones=raciones, ingredientes=[{"texto": "4 huevos"}])


def test_la_misma_receta_dos_veces_el_mismo_dia_son_dos_ocurrencias(con):
    """*** Lo que la clave vieja impedia. *** *

    *Con `PRIMARY KEY (fecha, receta_id)`, *poner la tortilla **a la comida y a la cena** era
    **una sola fila** *(-- *`INSERT OR REPLACE` se pisaba --).* *Ahora son **dos**, *y **las dos se leen.** *
    """
    r = _una_receta(con)
    recetas.planificar(con, "yo", "2026-10-20", r, comida="comida")
    recetas.planificar(con, "yo", "2026-10-20", r, comida="cena")

    puestas = recetas.plan(con, "yo", "2026-10-20", "2026-10-20")
    assert [x["comida"] for x in puestas] == ["cena", "comida"], puestas
    assert len(puestas) == 2, puestas


def test_las_raciones_son_de_la_ocurrencia_y_no_de_la_receta(con):
    """*** Una receta de 4, *cocinada **para 2** un dia. *** *

    *Y **`None` quiere decir «las de la receta»** *-- *y **no se copian**, *porque **el dia que la receta
    cambie**, *lo que se cocino **aquel dia no cambia.*** *
    """
    r = _una_receta(con, raciones=4)
    recetas.planificar(con, "yo", "2026-10-21", r, comida="comida", raciones=2)
    recetas.planificar(con, "yo", "2026-10-22", r, comida="comida")

    por_dia = {x["fecha"]: x for x in recetas.plan(con, "yo", "2026-10-21", "2026-10-22")}
    assert por_dia["2026-10-21"]["raciones"] == 2, por_dia
    assert por_dia["2026-10-22"]["raciones"] is None, por_dia

    # *Y si la receta cambia de raciones, **lo ya cocinado no se toca.** *
    recetas.actualizar(con, "yo", r, raciones=6, ingredientes=[{"texto": "6 huevos"}])
    despues = {x["fecha"]: x for x in recetas.plan(con, "yo", "2026-10-21", "2026-10-22")}
    assert despues["2026-10-21"]["raciones"] == 2, despues
    assert despues["2026-10-22"]["raciones"] is None, despues


def test_la_comida_tiene_que_ser_una_de_las_del_diario(con):
    """*** Y **el vocabulario no se inventa**: *es el de `diario.COMIDAS`.** *** *

    *Dos modulos que hablan de lo mismo **tienen que llamarlo igual** *-- *y si no, **se dice cual es
    el problema**, *y **cuales valen.** *
    """
    from core.diario import COMIDAS

    r = _una_receta(con)
    with pytest.raises(ValueError, match="esa comida no existe"):
        recetas.planificar(con, "yo", "2026-10-23", r, comida="almuerzo")
    for buena in COMIDAS:
        recetas.planificar(con, "yo", "2026-10-23", r, comida=buena)


def test_quitar_sin_comida_quita_todas_las_del_dia_y_con_comida_solo_esa(con):
    """*** La pregunta que el modelo viejo **no tenia**. *** *

    *`comida=None` -> **todas las ocurrencias de esa receta ese dia**, *que es **el sentido viejo**
    *y **el defecto**; *`comida="cena"` -> **solo esa.** *
    """
    r = _una_receta(con)
    recetas.planificar(con, "yo", "2026-10-24", r, comida="comida")
    recetas.planificar(con, "yo", "2026-10-24", r, comida="cena")

    assert recetas.quitar_del_plan(con, "yo", "2026-10-24", r, comida="cena") is True
    quedan = recetas.plan(con, "yo", "2026-10-24", "2026-10-24")
    assert [x["comida"] for x in quedan] == ["comida"], quedan

    assert recetas.quitar_del_plan(con, "yo", "2026-10-24", r) is True
    assert recetas.plan(con, "yo", "2026-10-24", "2026-10-24") == []
    # *Y quitar lo que ya no esta **no es un error**: dice que no habia nada.*
    assert recetas.quitar_del_plan(con, "yo", "2026-10-24", r) is False


def test_una_base_con_la_clave_vieja_se_migra_y_no_pierde_lo_planeado(tmp_path):
    """*** La migracion, que es **la parte delicada.** *** *

    *SQLite **no permite `ALTER TABLE` sobre una clave primaria**, *asi que hay que **rehacer la tabla**.
    *Y **se conservan los datos**: *cada fila vieja pasa a `comida = 'comida'` *-- *que es **lo que
    significaba** *--, *y `raciones = NULL` *-- *las de la receta, *que es **lo que se cocinaba.*** *

    *Y **el esquema viejo se construye a mano SOLO para `plan`**, *sobre una base **hecha por el
    codigo**: *duplicar el esquema entero a mano fue **el error de la primera version de este ensayo**,
    *y **lo que probaba entonces era mi copia, no la migracion.** *
    """
    ruta = tmp_path / "vieja.sqlite"
    # *1) Una base de verdad, con el codigo, y una receta planeada.*
    con = recetas.conecta(ruta)
    r = recetas.crear(con, "yo", "Tortilla", raciones=4, ingredientes=[{"texto": "4 huevos"}])
    recetas.planificar(con, "yo", "2026-01-02", r, comensales=3)
    con.close()

    # *2) Y se le pone la clave VIEJA a `plan`, copiando lo que hay.*
    vieja = sqlite3.connect(ruta)
    vieja.executescript("""
        CREATE TABLE plan_viejo (
            fecha TEXT NOT NULL, receta_id INTEGER NOT NULL REFERENCES receta(id),
            version INTEGER NOT NULL, comensales INTEGER NOT NULL, PRIMARY KEY (fecha, receta_id));
        INSERT INTO plan_viejo (fecha, receta_id, version, comensales)
             SELECT fecha, receta_id, version, comensales FROM plan;
        DROP TABLE plan;
        ALTER TABLE plan_viejo RENAME TO plan;
    """)
    vieja.commit()
    columnas = {f[1] for f in vieja.execute("PRAGMA table_info(plan)").fetchall()}
    assert "comida" not in columnas, columnas
    vieja.close()

    # *3) Y al abrirla otra vez, `_migra` la arregla **sin perder lo planeado.** *
    con = recetas.conecta(ruta)
    try:
        puestas = recetas.plan(con, "yo", "2026-01-02", "2026-01-02")
        assert len(puestas) == 1, puestas
        assert puestas[0]["comida"] == "comida", puestas
        assert puestas[0]["raciones"] is None, puestas
        assert puestas[0]["comensales"] == 3, puestas
        # *Y **la clave nueva funciona** ya en la base migrada: la misma receta, otra comida.*
        recetas.planificar(con, "yo", "2026-01-02", r, comida="cena")
        assert len(recetas.plan(con, "yo", "2026-01-02", "2026-01-02")) == 2
    finally:
        con.close()


def test_duplicar_la_semana_copia_las_ocurrencias_con_su_comida_y_sus_raciones(con):
    """*** La tercera frase de B07, *y la que **no se podia escribir antes.** *** *

    *Mientras la ocurrencia **no tuvo identidad**, *«duplicar» **no tenia sobre que actuar**: *
    *no se sabia **que** copiar. *Ahora se copia **cada ocurrencia**, *con **su comida**, *
    *sus comensales y *** sus raciones *** *-- *que **es lo que se cocino**, *y es lo que hay que
    repetir.* *
    """
    r = _una_receta(con)
    recetas.planificar(con, "yo", "2026-11-02", r, comida="comida", comensales=3, raciones=2)
    recetas.planificar(con, "yo", "2026-11-03", r, comida="cena", comensales=5)

    recibo = recetas.duplicar_semana(con, "yo", "2026-11-02", "2026-11-09")
    assert recibo["creadas"] == 2, recibo
    assert recibo["ya_estaban"] == 0, recibo

    copiadas = {x["fecha"]: x for x in recetas.plan(con, "yo", "2026-11-09", "2026-11-15")}
    assert set(copiadas) == {"2026-11-09", "2026-11-10"}, copiadas
    assert copiadas["2026-11-09"]["comida"] == "comida", copiadas
    assert copiadas["2026-11-09"]["comensales"] == 3, copiadas
    assert copiadas["2026-11-09"]["raciones"] == 2, copiadas
    assert copiadas["2026-11-10"]["comida"] == "cena", copiadas
    assert copiadas["2026-11-10"]["raciones"] is None, copiadas


def test_duplicar_no_pisa_lo_que_ya_hay_y_lo_dice_en_el_recibo(con):
    """*** «*Misma clave con contenido distinto produce *** conflicto, no exito ficticio ***». *** *

    *Lo dice B05, *y por eso aqui **no se usa `INSERT OR REPLACE`**: *si en el dia destino ya hay algo
    *(-- *esa comida y esa receta --)*, **se respeta**, *se cuenta aparte, *y **se devuelve el recibo.** *
    *Que es **lo contrario** de decir «duplicado» cuando **no se duplico nada.** *
    """
    r = _una_receta(con)
    otra = recetas.crear(con, "yo", "Ensalada", raciones=2, ingredientes=[{"texto": "1 lechuga"}])
    recetas.planificar(con, "yo", "2026-11-02", r, comida="comida", comensales=3, raciones=2)
    # *Y **dos** en el origen: *la Ensalada **si** se copiara, *y la tortilla **no**, *porque en el
    # destino **ya hay** esa misma receta, esa misma comida, **con otros numeros.** *
    recetas.planificar(con, "yo", "2026-11-03", otra, comida="cena")
    recetas.planificar(con, "yo", "2026-11-09", r, comida="comida", comensales=9, raciones=9)

    recibo = recetas.duplicar_semana(con, "yo", "2026-11-02", "2026-11-09")
    assert recibo["creadas"] == 1, recibo
    assert recibo["ya_estaban"] == 1, recibo
    assert recetas.plan(con, "yo", "2026-11-10", "2026-11-10")[0]["nombre"] == "Ensalada"

    # *Y **lo que ya estaba sigue como estaba**: *9 comensales y 9 raciones, *no 3 y 2.* *
    destino = {x["receta_id"]: x for x in recetas.plan(con, "yo", "2026-11-09", "2026-11-09")}
    assert destino[r]["comensales"] == 9, destino
    assert destino[r]["raciones"] == 9, destino


def test_duplicar_a_la_misma_semana_es_un_error_dicho(con):
    """*Y **decir a cual**, *porque copiar una semana **sobre si misma** no quiere decir nada.*"""
    r = _una_receta(con)
    recetas.planificar(con, "yo", "2026-11-02", r)
    with pytest.raises(ValueError, match="a cual"):
        recetas.duplicar_semana(con, "yo", "2026-11-02", "2026-11-02")


def test_duplicar_no_toca_el_plan_de_otro(con):
    """*** Y **el permiso, que es lo de siempre**: *solo se copia **lo tuyo.** *** *

    *La lectura del origen ya va con `propietario` *(-- *`plan` hace el JOIN con `receta` --)*, *
    *asi que **lo de otro no entra en el origen**, *y **duplicar no es una puerta de atras.** *
    """
    mio = recetas.crear(con, "yo", "Mia", raciones=2, ingredientes=[{"texto": "1 x"}])
    ajeno = recetas.crear(con, "otro", "Ajena", raciones=2, ingredientes=[{"texto": "1 y"}])
    recetas.planificar(con, "yo", "2026-11-02", mio)
    recetas.planificar(con, "otro", "2026-11-03", ajeno)

    recibo = recetas.duplicar_semana(con, "yo", "2026-11-02", "2026-11-09")
    assert recibo["creadas"] == 1, recibo
    # *Y **lo de `otro` no aparece** en el destino de `yo`.* *
    assert [x["nombre"] for x in recetas.plan(con, "yo", "2026-11-09", "2026-11-15")] == ["Mia"]
    # *Y **lo de `otro` sigue donde estaba**, *y **no se ha duplicado a la semana siguiente**.* *
    suyo = recetas.plan(con, "otro", "2026-11-02", "2026-11-15")
    assert [x["fecha"] for x in suyo] == ["2026-11-03"], suyo
