"""B08: **la prevision no inventa.** Lo que no se sabe se dice, y no se rellena.

El criterio de B08 dice, literal:

> *«Vista de previstos separada del diario real. [...] Aceptar R1=270, media=135, **ausencia de energia con
> proteina conocida**, idempotencia, recarga y aislamiento A/B; **compra nunca genera consumo por si sola**.»*

*Estas pruebas fijan las **reglas de honestidad** de la vista de previstos -- que es lo que la hace distinta de
un formulario comodo -- **sin base de datos y sin red**, leyendo el codigo que las impone.* **No sustituyen a un
recorrido con datos reales**, y se dice: lo que fijan es que la **regla esta escrita donde se decide**, no que
el numero salga bien con un catalogo lleno.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RECETAS = RAIZ / "plataforma" / "api" / "recetas.py"
DIARIO = RAIZ / "core" / "diario.py"


def _fuente():
    return RECETAS.read_text(encoding="utf-8")


def test_la_vista_de_previstos_existe_y_pide_el_rango():
    """***La ruta esta, y pide `desde` y `hasta`*** -- *como `desde-el-plan`, que da 422 sin ellos.*"""
    fuente = _fuente()
    assert '@rutas.get("/plan/prevision")' in fuente
    assert "def prevision_del_plan(desde: str = Query(...), hasta: str = Query(...)" in fuente


def test_la_vista_va_antes_del_identificador():
    """*Y **antes** que `/{receta_id}`*: *si no, FastAPI leeria "plan" como un identificador.*

    *Es la misma trampa que ya documenta la ruta del plan, y se comprueba por posicion.*
    """
    fuente = _fuente()
    assert fuente.index('@rutas.get("/plan/prevision")') < fuente.index('@rutas.get("/{receta_id}")')


def test_solo_se_convierten_las_dos_unidades_de_peso():
    """***`ml` y `ud` NO se convierten a gramos, y no es un olvido.***

    `ml` necesitaria **la densidad**, y `ud` **el peso de una unidad**: los dos son datos que no tenemos, y
    **el encargo prohibe inventarlos**. Se comprueba la tabla entera, y no solo que exista.
    """
    fuente = _fuente()
    bloque = fuente[fuente.index("_GRAMOS_POR_UNIDAD"):fuente.index("\n\n", fuente.index("_GRAMOS_POR_UNIDAD"))]
    unidades = set(re.findall(r'"([a-z]+)":', bloque))
    assert unidades == {"g", "kg"}, f"la tabla de pesos cambio: {unidades}"
    for prohibida in ("ml", "l", "ud", "unidad", "cl"):
        assert f'"{prohibida}":' not in bloque, f"{prohibida} no se puede convertir sin inventar un dato"


def test_el_docstring_dice_por_que_no_se_convierte():
    """*Y **el motivo queda escrito al lado de la tabla**, no en un commit.*

    *Una regla sin su motivo se borra en el primer arreglo apresurado.*

    *Las palabras se buscan sueltas y no en frases: el docstring lleva marcas de enfasis (`**densidad**`) que
    parten las frases, y un ensayo que dependa del marcado se rompe al reescribir el comentario.*
    """
    fuente = _fuente()
    for palabra in ("densidad", "peso de una unidad", "prohibe inventarla"):
        assert palabra in fuente, f"el motivo se perdio: {palabra}"


def test_lo_que_no_tiene_producto_va_a_sin_dato_con_su_nombre():
    """***`sin_dato` recibe el `texto` de la linea, y no un id.***

    *Si llevara un id, la lista de lo que falta no se podria leer; y **el encargo pide que se conserve el
    ingrediente sin catalogo**, con su nombre.*
    """
    fuente = _fuente()
    assert "sin_dato.append(texto)" in fuente
    assert "sin_cantidad.append(texto)" in fuente
    assert '"sin_catalogo"' in fuente and '"sin_cantidad"' in fuente


def test_la_suma_es_la_del_diario_y_no_una_copia():
    """***La prevision llama a `diario.resumen`; no se escribe su propia aritmetica.***

    *Es lo que hace que los dos numeros sean comparables: si cada uno sumara a su manera, la grafica que los
    pone juntos seria una mentira, y la mentira no estaria en los datos sino en el codigo.*
    """
    fuente = _fuente()
    assert "diario.resumen(" in fuente
    # *Y `resumen` existe de verdad, y con ese nombre, en el diario.*
    assert re.search(r"^def resumen\(", DIARIO.read_text(encoding="utf-8"), re.M)
    # *Y la prevision no se define su propia cobertura.*
    assert "_cobertura(" not in fuente
    assert "def resumen(" not in fuente


def test_el_diario_calcula_los_nutrientes_uno_a_uno():
    """***`de_ficha` calcula nutriente a nutriente, y deja `None` en lo que no sabe.***

    *Es el caso que el criterio de B08 pide aceptar -- «ausencia de energia con proteina conocida» -- y su
    motivo esta escrito: **rellenar con ceros seria afirmar que no lleva proteina**.*
    """
    diario = DIARIO.read_text(encoding="utf-8").lower()
    assert "nutriente a nutriente, no en bloque" in diario
    assert "rellenar con ceros" in diario


def test_la_prevision_no_escribe_nada():
    """***Compra no es consumo, y esta ruta no apunta en el diario.***

    *Se comprueba sobre el arbol sintactico: **ni una llamada a `apunta`**, ni `INSERT`, ni `commit`.*
    """
    fuente = _fuente()
    arbol = ast.parse(fuente)
    cuerpo = None
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "prevision_del_plan":
            cuerpo = ast.get_source_segment(fuente, nodo) or ""
    assert cuerpo, "no se encontro la funcion"
    for escritura in ("apunta(", "apunta_de_ficha(", "INSERT", "UPDATE", "DELETE", "commit("):
        assert escritura not in cuerpo, f"la prevision no puede escribir: {escritura}"
