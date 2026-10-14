"""**La auditoria de `GET` sin cambios, contra casos que yo controlo.**

*Una herramienta que encuentra una cosa de verdad **necesita su propio ensayo**, *o **el dia que deje
de encontrar** nadie se enterara: *es **el mismo problema que los cinco ensayos de envases** que
parchaban `main._del_plan` *y por eso **pasaban con y sin arreglo.*** *

*Aqui se le dan ficheros **escritos a mano**, *con lo que tiene que encontrar y con lo que NO*:
  *-- *un `GET` que llama a una funcion de escritura  -> **tiene que salir***
  *-- *un `GET` que ejecuta un `INSERT`               -> **tiene que salir***
  *-- *un `GET` que **solo lee**                      -> **NO tiene que salir***
  *-- *y un `GET` cuyo **comentario** dice «apunta»   -> **NO tiene que salir***
     *(-- que es el fallo que tenia el `grep`, *y **el que mas facil es volver a cometer** --)*
  *-- *y un `POST` que escribe **justo debajo** de un `GET` -> **NO tiene que salir por el GET***
     *(-- la ventana de lineas cruzaba la frontera, *y **por eso salio `crea_lista` --)*
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "auditar_gets_que_escriben.py"


def _herramienta():
    """*Se carga por ruta: `scripts/` no es un paquete.*"""
    spec = importlib.util.spec_from_file_location("auditar_gets", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _un_modulo(tmp_path, nombre: str, cuerpo: str):
    (tmp_path / nombre).write_text(cuerpo, encoding="utf-8")
    return tmp_path


def test_encuentra_un_get_que_llama_a_algo_que_escribe(tmp_path):
    _un_modulo(tmp_path, "a.py", '''
@app.get("/api/cosas")
def ver():
    almacen.marca_visita("x", "y")
    return {}
''')
    halladas = _herramienta().sospechosas(tmp_path)
    assert len(halladas) == 1, halladas
    assert halladas[0][2] == "ver" and "marca_visita" in halladas[0][3]


def test_encuentra_un_get_con_un_insert(tmp_path):
    _un_modulo(tmp_path, "b.py", '''
@app.get("/api/cosas")
def ver():
    cur.execute("INSERT INTO visita (a) VALUES (%s)", (1,))
    return {}
''')
    halladas = _herramienta().sospechosas(tmp_path)
    assert len(halladas) == 1, halladas
    assert "SQL" in halladas[0][3]


def test_un_get_que_solo_lee_no_sale(tmp_path):
    """*Y **el que solo lee, no sale** -- si saliera, la herramienta no valdria nada.*"""
    _un_modulo(tmp_path, "c.py", '''
@app.get("/api/cosas")
def ver():
    cur.execute("SELECT a FROM cosas WHERE id = %s", (1,))
    return {}
''')
    assert _herramienta().sospechosas(tmp_path) == []


def test_un_comentario_que_dice_apunta_NO_cuenta(tmp_path):
    """*** Y este es EL fallo del `grep`: **la prosa no es codigo.** ***

    *La primera version buscaba la palabra `apunta` en 30 lineas, *y **salio siete veces** -- *todas en
    comentarios.* *Si esto vuelve a pasar, **la herramienta se vuelve ruido** *y nadie la mira.*
    """
    _un_modulo(tmp_path, "d.py", '''
@app.get("/api/cosas")
def ver():
    # Aqui se apunta lo que hay, y el que apunta es el vigilante.
    # Y esto apunta a otra cosa: no se reordena nada.
    return {}
''')
    assert _herramienta().sospechosas(tmp_path) == []


def test_el_POST_de_debajo_de_un_GET_no_cuenta_para_el_GET(tmp_path):
    """*** Y este es el otro fallo: LA VENTANA DE LINEAS CRUZABA LA FRONTERA. ***

    *`GET /api/listas` parecia llamar a `crea_lista`, *que esta **30 lineas mas abajo** -- *en el
    `POST`.* *Con el AST, cada funcion tiene **su** cuerpo, *y lo de abajo **no es suyo.** *
    """
    _un_modulo(tmp_path, "e.py", '''
@app.get("/api/cosas")
def ver():
    return {}


@app.post("/api/cosas")
def crear():
    almacen.crea_lista("x", "y")
    return {}
''')
    assert _herramienta().sospechosas(tmp_path) == []


def test_una_ruta_sin_decorador_no_se_mira(tmp_path):
    """*Y una funcion que **no es una ruta** no entra: *si entrara, *cualquier ayudante de escritura
    dentro del modulo **saldria.***"""
    _un_modulo(tmp_path, "f.py", '''
def ayudante():
    almacen.crea_usuario("x", "y", "z")
''')
    assert _herramienta().sospechosas(tmp_path) == []


def test_y_contra_LA_API_DE_VERDAD(tmp_path):
    """**Y el caso real, que es el que importa**: *hoy sale **una**, *y es la que se midio.*

    *Si un dia sale **cero**, *es que alguien movio la marca a un `POST` -- *y entonces **este ensayo
    esta diciendo que el hallazgo se cerro*** *; *y si sale **dos**, *hay **una nueva.*** *
    """
    halladas = _herramienta().sospechosas()
    assert len(halladas) <= 1, f"hay mas de una: {halladas}"
    if halladas:
        assert halladas[0][0] == "main.py" and halladas[0][2] == "ver_lista", halladas
