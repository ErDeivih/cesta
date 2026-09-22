"""El envase, dicho igual venga de donde venga.

DIA dice "frasco" y Mercadona dice "Tarro" para lo mismo, y Mercadona ademas
mete la cantidad en el mismo campo ("Pack-6"), que no es un envase.
"""
from core.envases import _TRADUCCION, ENVASES, lee


def test_las_dos_cadenas_acaban_en_la_misma_palabra():
    assert lee("frasco")[0] == lee("Tarro")[0] == "tarro"
    assert lee("bolsa")[0] == lee("Bolsa")[0] == "bolsa"


def test_un_pack_no_es_un_envase_pero_si_una_cantidad():
    assert lee("Pack-6") == (None, 6)
    assert lee("Pack-4") == (None, 4)
    # "Pack" a secas no dice cuantos.
    assert lee("Pack") == (None, None)


def test_el_material_no_cambia_el_envase():
    assert lee("Botella de cristal")[0] == "botella"
    assert lee("Caja de cartón")[0] == "caja"


def test_normalizar_dos_veces_da_lo_mismo():
    # a_registro puede recibir un maestro viejo que ya guardara el valor
    # normalizado; volver a pasarlo no debe perderlo.
    for bruto in ("frasco", "Pieza", "sin envase", "Brik"):
        una = lee(bruto)[0]
        assert lee(una)[0] == una, bruto


def test_todo_lo_que_produce_esta_declarado():
    assert set(_TRADUCCION.values()) <= set(ENVASES)


def test_lo_desconocido_es_none_y_no_revienta():
    assert lee("caja registradora sorpresa") == (None, None) or lee("caja registradora sorpresa")[0] == "caja"
    assert lee(None) == (None, None)
    assert lee("") == (None, None)
