"""El banco de pruebas de Laya: lo que se puede fijar sin cargar el modelo.

Estas pruebas **no cargan Laya, ni lo necesitan**: comprueban las tres cosas que
tienen que seguir siendo verdad para que el experimento de `docs/LAYA.md` siga
significando lo mismo cuando alguien lo repita.

1. **`laya` no es una dependencia de este proyecto.** El paquete arrastra torch y 2,2 GB
   de pesos, y la cadena de las 06:00 no puede depender de el. Se importa **dentro** de
   la funcion que mide, y aqui se comprueba que importar el modulo no lo arrastra.
2. **La pregunta la escribe una persona.** Cada (eje, valor) de `core/atributos.py`
   tiene que tener su explicacion en castellano escrita a mano en `laya_ejes.py`. Si
   alguien anade un eje al catalogo y no lo explica aqui, la prueba se pone roja: es
   la unica forma de que el enunciado no se quede atras en silencio. Y como las
   explicaciones estan escritas como las escribiria una persona, parte de ellas
   **copian el patron** de la lista: eso no se prohibe, se cuenta y se fija, porque el
   informe tiene que decir cuanto del acierto puede ser copia.
3. **El banco es deterministico.** Dos ejecuciones con la misma semilla preguntan por
   los mismos nombres; con otra semilla, no. Sin eso, la cifra de `docs/LAYA.md` no
   se puede volver a medir ni comparar.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from core.atributos import EJES, valores
from projects.cesta import laya_ejes

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold" / "grupos.parquet"


def test_importar_el_modulo_no_trae_laya():
    """El paquete vive en un entorno aparte, y esto lo fija."""
    assert "laya" not in sys.modules, (
        "importar `projects.cesta.laya_ejes` ha arrastrado el paquete de Laya: tiene "
        "que importarse dentro de `mide()`, nunca arriba. Si no, el proyecto pasa a "
        "depender de torch.")
    assert "torch" not in sys.modules


def test_cada_valor_del_catalogo_tiene_su_explicacion_a_mano():
    """El trinquete del enunciado: un eje nuevo obliga a escribir como se pregunta."""
    faltan = [(eje, valor) for eje, opciones in EJES.items()
              for valor, _patrones in opciones
              if (eje, valor) not in laya_ejes.EXPLICACION]
    assert not faltan, (
        f"estos valores de `core/atributos.py` no tienen explicacion en "
        f"`laya_ejes.EXPLICACION`: {faltan}. Escribela a mano: es el enunciado que "
        f"recibe el modelo, y copiar los patrones de la lista haria el experimento "
        f"circular.")


def test_la_generosidad_del_enunciado_esta_medida_y_fijada():
    """Cuantos valores del enunciado llevan dentro un patron de la lista.

    No se prohibe -- las explicaciones estan escritas como las escribiria una persona
    --, pero **hay que decirlo**, porque el acierto de esos valores puede ser copia y
    no lectura. Si alguien escribe mas explicaciones copiando el patron, este numero
    sube y la prueba avisa: el experimento se vuelve mas generoso y el informe tiene
    que enterarse.
    """
    copian = laya_ejes.valores_que_copian_el_patron()
    assert len(copian) == 12, (
        f"hoy son 12 de 27 valores; ahora son {len(copian)}: "
        f"{[(e, v) for e, v, _p in copian]}. Si sube, el experimento es mas generoso "
        f"con el modelo y `docs/LAYA.md` tiene que decirlo en el mismo commit")
    assert all(copiados for _eje, _valor, copiados in copian)


def test_la_generosidad_parte_el_banco_en_dos():
    """`generosidad()` separa los pares de los valores que copian y los que no."""
    from collections import Counter

    copiado = next(iter(laya_ejes.valores_que_copian_el_patron()))[:2]
    # Un valor de los que NO copian, buscado y no escrito a mano: si manana se anade
    # una explicacion que copie, esto seguiria midiendo lo mismo.
    limpio = next((eje, valor) for eje, opciones in EJES.items()
                  for valor, _p in opciones
                  if (eje, valor) != copiado and not laya_ejes.copia_del_patron(eje, valor))
    por_par = {
        copiado: Counter({"acuerdo": 3, "abstencion": 1}),
        limpio: Counter({"acuerdo": 1, "abstencion": 3}),
    }
    g = laya_ejes.generosidad(por_par)
    assert g["copia"] == {"pares": 4, "acuerdo": 3, "acuerdo_pct": 75.0}
    assert g["limpio"] == {"pares": 4, "acuerdo": 1, "acuerdo_pct": 25.0}


def test_las_preguntas_son_las_doces_con_su_no_lo_dice():
    """Una `Choice` por eje, con los valores del eje **y** la opcion de callar."""
    preguntas = laya_ejes.preguntas_de("Leche entera semidesnatada MILSANI 1 l")
    assert set(preguntas) == set(EJES)
    for eje, pregunta in preguntas.items():
        assert pregunta["type"] == "choice"
        criterios = pregunta["criteria"]
        assert list(criterios)[-1] == laya_ejes.SILENCIO, (
            "la opcion de silencio va la ultima: es la respuesta de la casa cuando el "
            "nombre no dice nada")
        assert set(criterios) == {v for v, _p in EJES[eje]} | {laya_ejes.SILENCIO}


@pytest.mark.skipif(not GOLD.exists(), reason="esta copia no trae gold")
def test_el_banco_es_deterministico_y_solo_pregunta_por_lo_que_ya_sabemos():
    """Dos veces lo mismo da lo mismo, y nadie entra en el banco por casualidad."""
    nombres, verdad = laya_ejes.banco(3, 23)
    otros, _ = laya_ejes.banco(3, 23)
    distintos, _ = laya_ejes.banco(3, 24)
    assert nombres == otros, "el banco no es determinista: la cifra no se puede repetir"
    assert nombres != distintos, "la semilla no cambia la muestra: no muestrea nada"
    # Solo entra quien declara algo: un nombre del que no sabemos nada no prueba nada.
    assert nombres
    assert all(verdad[n] for n in nombres)
    for nombre in nombres:
        assert verdad[nombre] == valores(nombre)
