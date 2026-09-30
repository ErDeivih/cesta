"""La tercera puerta se vigila a si misma: que mida todo lo que dice, que no deje basura y que
un `FALLO` se pueda citar.

`plataforma/prueba_funciones.py` es la puerta que hace **cada funcion de la aplicacion** en un
navegador de verdad (las otras dos miran lo que el encargo pide: las cuatro preguntas y lo que se
sirve). Una puerta que se cae a trozos es peor que no tenerla, porque su `TODO BIEN` se cree; asi
que aqui se guarda lo que a esta le costo aprender, medido el 27 de septiembre de 2026:

**Los numeros se repitieron.** Cada comprobacion traia su numero escrito a mano y, al anadir
comprobaciones nuevas, salieron dos «13.» y cuatro «35.»: un `FALLO 13` no señalaba nada. Ahora
el numero lo pone un contador, y hay una prueba que impide volver a escribirlos a mano.

**El desplegable de listas se queda sin opciones un momento.** Al borrar la lista seleccionada
la pantalla vuelve a pedir la lista de listas, y en ese hueco el `select` esta vacio. Medir ahi
daba un fallo que no era de la aplicacion (**en ese mismo instante la API ya contestaba
`[('Casa', 1)]`**, comprobado con `data/debug/borrar_lista.py`). Por eso la puerta recarga antes
de mirar, y eso tambien se guarda: el dia que alguien quite esa recarga, el fallo fantasma
vuelve.

**Cuatro de los primeros cinco fallos eran de la puerta, no de la aplicacion**: un favorito no
se puede pasar a una lista que no existe, «LO QUE HAS BUSCADO» se pinta en mayusculas desde el
estilo, el interruptor de cadenas cercanas guarda lo contrario de lo que uno supone, y el
escaner dice «No tengo ese codigo» con otras palabras. Es la leccion de esta puerta, y esta
escrita en `docs/OPERACION.md` para que la siguiente no tropiece igual.

**Y la cuenta es desechable**: se borra al terminar para que la base de casa no se llene de
cuentas de prueba (`DELETE /api/yo`), y si una pasada se corta a mitad se borra la que quedo
antes de empezar (una pasada cortada dejaba la cuenta con su lista y la siguiente fallaba por el
estado que habia dejado ella misma).
"""
from __future__ import annotations

import ast
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
PUERTA = RAIZ / "plataforma" / "prueba_funciones.py"
OPERACION = RAIZ / "docs" / "OPERACION.md"
DISENO = RAIZ / ".stitch" / "DESIGN.md"

FUENTE = PUERTA.read_text(encoding="utf-8")


def _quejas() -> list[str]:
    """Las etiquetas de cada comprobacion, tal y como las escribe el codigo.

    De una `f"texto {variable}"` se queda el texto fijo: es lo que hace falta para saber si dos
    comprobaciones dicen lo mismo.
    """
    arbol = ast.parse(FUENTE)
    dichas: list[str] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call) or len(nodo.args) < 2:
            continue
        nombre = nodo.func
        if not (isinstance(nombre, ast.Name) and nombre.id == "comprueba"):
            continue
        etiqueta = nodo.args[1]
        if isinstance(etiqueta, ast.Constant) and isinstance(etiqueta.value, str):
            dichas.append(etiqueta.value)
        elif isinstance(etiqueta, ast.JoinedStr):
            fijo = "".join(v.value for v in etiqueta.values
                           if isinstance(v, ast.Constant) and isinstance(v.value, str))
            dichas.append(fijo)
        else:  # una queja variable: no se puede comparar, pero se cuenta
            dichas.append(f"<variable en la linea {etiqueta.lineno}>")
    return dichas


def test_la_puerta_existe_y_dice_por_que():
    """Sin el «por que» no se sabe si hay que correrla al tocar la interfaz."""
    assert PUERTA.exists(), "no esta la puerta de las funciones"
    assert "prueba_funciones" in FUENTE
    assert "uv run python -m plataforma.prueba_funciones" in FUENTE, (
        "la puerta no dice como se corre")
    assert "prueba_navegador" in FUENTE and "prueba_produccion" in FUENTE, (
        "la puerta no dice de que se diferencia de las otras dos")


def test_hace_el_recorrido_entero_y_no_solo_las_pantallas():
    """Lo que quedo sin tocar hasta que existio esta puerta, uno por uno."""
    funciones = {
        "el alta": "Crear cuenta",
        "volver a entrar": 'name="Entrar"',
        "la baja de la cuenta": "method: 'DELETE'",
        "varias listas": "Lista nueva",
        "el desplegable de listas": "select[aria-label='Lista']",
        "los favoritos": "/favoritos",
        "los avisos": "/avisos",
        "las cadenas cercanas": "cercana",
        "los pesos del grupo": "input[type=range]",
        "elegir tienda": "elegir tienda",
        "las vistas guardadas": "vista guardada",
        "las busquedas recientes": "recientes",
        "el escaner": "/escaner",
        "la cara sin sesion": "sin sesion",
        "lo que se despliega": "que se note que se despliega",
    }
    faltan = [que for que, aguja in funciones.items() if aguja not in FUENTE]
    assert not faltan, f"la puerta no ejercita: {faltan}"


def test_los_numeros_los_pone_ella_y_no_la_queja():
    """Dos «13.» y cuatro «35.» hacian que un FALLO no se pudiera citar."""
    assert "{HECHAS:>3}" in FUENTE, "la puerta no numera las comprobaciones con su contador"
    a_mano = re.findall(r'\bf?"\d+\. ', FUENTE)
    assert not a_mano, (
        f"hay {len(a_mano)} quejas con el numero escrito a mano: el contador es el que numera")


def test_cada_comprobacion_dice_una_cosa_distinta():
    """Si dos comprobaciones dicen lo mismo, un `FALLO` señala a las dos."""
    dichas = _quejas()
    assert len(dichas) >= 40, f"la puerta se ha quedado corta: {len(dichas)} comprobaciones"
    repetidas = sorted({q for q in dichas if dichas.count(q) > 1})
    assert not repetidas, f"hay comprobaciones que dicen lo mismo: {repetidas}"


def test_la_cuenta_es_desechable_y_no_deja_basura():
    """La base de casa no se queda con cuentas de prueba."""
    assert 'USUARIO = "prueba-funciones"' in FUENTE
    assert "'/api/yo'" in FUENTE and "'DELETE'" in FUENTE, (
        "la puerta no borra su cuenta al terminar")
    # **Y al empezar, si la pasada anterior se cayo.** El 30 de septiembre de 2026 esta
    # comprobacion se quedo corta pidiendo solo «una cuenta con lista **y lineas**»: una pasada
    # que se corta despues de vaciar la lista dejaba la cuenta viva, el alta no volvia a pasar
    # (la pantalla ya no ofrecia «Créala») y la lista nueva salia con un «(1)» porque el nombre
    # estaba cogido. Dos comprobaciones rojas por la basura de antes y no por el codigo.
    assert "la cuenta de la pasada anterior seguia ahi" in FUENTE, (
        "una pasada cortada deja la cuenta viva y la siguiente falla por ese estado")
    assert 'pagina.get_by_label("Clave").count() == 0' in FUENTE, (
        "la limpieza del principio tiene que ser «hay sesion», no «hay lista con lineas»")


def test_mide_lo_que_se_sirve_y_en_un_movil():
    """La puerta mide la aplicacion servida (como `prueba_produccion`), no el Vite de casa."""
    assert 'os.environ.get("CESTA_UI", "http://127.0.0.1:8080")' in FUENTE, (
        "por defecto no mide lo servido")
    assert '"width": 390, "height": 844' in FUENTE and "is_mobile=True" in FUENTE, (
        "no mide en el movil del encargo")


def test_la_leccion_del_desplegable_esta_escrita():
    """Al borrar la lista seleccionada el `select` pasa por estar vacio: se mira despues."""
    assert "Se recarga antes de mirar el desplegable" in FUENTE, (
        "falta la explicacion: dentro de nada alguien quita esa recarga y vuelve el fallo fantasma")
    assert "borrar_lista" in FUENTE, "no dice con que se comprobo cual era la verdad"
    trozo = FUENTE.split("quitar la lista la quita del desplegable")[0]
    assert 'carga("/cesta")' in trozo.rsplit("if otra:", 1)[-1], (
        "se quito la recarga: se esta midiendo el hueco en el que el desplegable esta vacio")


def test_la_operacion_documenta_la_puerta():
    """Una puerta que no esta en la operacion no se corre."""
    operacion = OPERACION.read_text(encoding="utf-8")
    assert "plataforma.prueba_funciones" in operacion, (
        "docs/OPERACION.md no dice que existe esta puerta")
    assert "TODAS LAS FUNCIONES CONTESTAN." in operacion, (
        "la operacion no dice que salida se espera")
    # El numero sale de **una sola constante**, y la pasada la comprueba al final: si se anade
    # una comprobacion, la puerta lo dice en vez de dejar los documentos mintiendo. Aqui se
    # vigila que los documentos digan lo mismo que la constante.
    constante = re.search(r"^COMPROBACIONES = (\d+)$", FUENTE, re.M)
    assert constante, "la puerta no tiene el numero de comprobaciones en una constante"
    puesto = [int(n) for n in re.findall(r"\*\*(\d+) comprobaciones\*\*", operacion)]
    assert puesto, "la operacion no dice cuantas comprobaciones son"
    assert puesto[0] == int(constante.group(1)), (
        f"la operacion dice {puesto[0]} comprobaciones y la puerta dice "
        f"{constante.group(1)}: se han separado")
    assert "HECHAS != COMPROBACIONES" in FUENTE, (
        "la puerta ya no comprueba que el numero de la pasada sea el que esta escrito")
    diseno = DISENO.read_text(encoding="utf-8")
    assert "plataforma.prueba_funciones" in diseno, (
        ".stitch/DESIGN.md no la cuenta entre las barras automaticas")
    assert f"{constante.group(1)} comprobaciones" in diseno, (
        ".stitch/DESIGN.md dice otro numero que la puerta")
