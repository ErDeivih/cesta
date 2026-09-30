"""El control que vigila que las cifras de los documentos sigan siendo verdad.

Y, sobre todo, que no diga "ok" cuando no ha comparado nada. El 18 de septiembre
de 2026, en un ensayo con un catalogo de mentira de 123 productos, las nueve
comprobaciones salieron en verde y el control termino diciendo "los numeros de
los documentos cuadran con los datos de hoy". No cuadraban: "123" estaba dentro
de "1.234" en algun documento, y el "0" de las capas que no habian corrido estaba
en todas partes.
"""
from projects.cesta.verificar_docs import (
    RAIZ,
    _candidatos,
    _cita_viva,
    _citado,
    _citas,
    _comando_existe,
    _comandos,
    _como_se_escribe,
    _existe_fichero,
    _existe_modulo,
    _miles,
)


def test_una_cifra_que_esta_de_verdad_cuenta():
    assert _citado("52.575", ["hoy el catalogo son 52.575 productos"])


def test_un_trozo_de_otra_cifra_no_cuenta():
    # "123" dentro de "1.234" era el falso positivo original.
    assert not _citado("123", ["el emparejador hizo 1.234 enlaces"])
    assert not _citado("575", ["hoy el catalogo son 52.575 productos"])


def test_dentro_de_una_fecha_tampoco():
    assert not _citado("18", ["medido el 2026-09-18 por la manana"])


def test_el_cero_nunca_se_da_por_citado():
    # "0 productos con Nutri-Score" no es una cifra que verificar: es una capa
    # que no ha corrido.
    assert not _citado("0", ["0 productos con Nutri-Score", "cero de cero"])


def test_la_cifra_pegada_a_puntuacion_normal_si_cuenta():
    assert _citado("6.448", ["comparables 6.448."])
    assert _citado("6.448", ["(6.448)"])


def test_los_miles_se_escriben_con_punto():
    assert _miles(52575) == "52.575"
    assert _miles(123) == "123"


def test_un_numero_de_dos_cifras_no_vale_como_vigilancia():
    # En un ensayo con 60 productos, "60" aparecia en algun documento por
    # casualidad y la comprobacion salia en verde sin haber vigilado nada.
    assert not _citado("60", ["hay 60 categorias en el menu"])
    assert _citado("761", ["761 productos con certificado"])


# --- Las citas de codigo (`almacen.py:287`) ----------------------------------
# Una cita que se puede leer es una prueba; una que apunta a un fichero que no
# esta o a una linea 1200 de un fichero de 900 es una promesa vacia, y suena
# igual de bien que la buena.


def _buscar_de_mentira(mapa):
    def buscar(citado):
        return mapa.get(citado, [])

    return buscar


def test_se_sacan_las_citas_con_su_tramo():
    assert _citas("ver `almacen.py:287` y `app.js:1413-1418`") == [
        ("almacen.py", 287, 0),
        ("app.js", 1413, 1418),
    ]


def test_una_cita_normal_esta_viva():
    buscar = _buscar_de_mentira({"almacen.py": [("plataforma/api/almacen.py", 1083, True)]})
    assert _cita_viva("almacen.py", 287, 0, buscar)[0] == "ok"


def test_la_ultima_linea_del_fichero_cuenta():
    buscar = _buscar_de_mentira({"almacen.py": [("almacen.py", 1083, True)]})
    assert _cita_viva("almacen.py", 1083, 0, buscar)[0] == "ok"


def test_una_linea_que_no_llega_avisa():
    buscar = _buscar_de_mentira({"almacen.py": [("almacen.py", 1083, True)]})
    estado, detalle = _cita_viva("almacen.py", 999999, 0, buscar)
    assert estado == "fuera"
    assert "1083" in detalle


def test_un_fichero_que_no_esta_avisa():
    assert _cita_viva("no_existe.py", 12, 0, _buscar_de_mentira({}))[0] == "no esta"


def test_un_tramo_manda_por_su_final():
    # `app.js:1413-1418` necesita que exista la 1418, no solo la 1413.
    buscar = _buscar_de_mentira({"app.js": [("app.js", 1415, True)]})
    assert _cita_viva("app.js", 1413, 1418, buscar)[0] == "fuera"
    assert _cita_viva("app.js", 1413, 0, buscar)[0] == "ok"


def test_el_fichero_en_otra_ruta_no_es_lo_mismo():
    # El lector no puede abrir `plataforma/web/almacen.py` si el fichero vive en
    # `plataforma/api/`: la cita esta movida y hay que arreglarla.
    buscar = _buscar_de_mentira({"almacen.py": [("plataforma/api/almacen.py", 1083, False)]})
    assert _cita_viva("almacen.py", 287, 0, buscar)[0] == "movida"


def test_una_cita_por_nombre_suelto_no_afirma_donde_esta():
    # Las 521 citas por nombre del BACKLOG (`Producto.tsx:352`, `almacen.py:287`)
    # estaban todas bien; la primera version las dio por movidas por resolverlas
    # por nombre.
    indice = {"zzz_almacen.py": [RAIZ / "plataforma/api/zzz_almacen.py"]}
    assert [c[2] for c in _candidatos("zzz_almacen.py", indice)] == [True]


def test_una_ruta_parcial_vale_si_acaba_igual():
    # `src/tipos.ts:173` esta escrito desde la carpeta de la aplicacion: el
    # lector lo encuentra igual, asi que la cita vale.
    indice = {"zzz_tipos.ts": [RAIZ / "plataforma/web/app/src/zzz_tipos.ts"]}
    assert [c[2] for c in _candidatos("src/zzz_tipos.ts", indice)] == [True]


def test_una_ruta_que_no_acaba_igual_esta_movida():
    # El fichero existe, pero no donde la cita dice.
    buscar = _buscar_de_mentira({
        "plataforma/web/zzz_almacen.py": [
            (RAIZ / "plataforma/api/zzz_almacen.py", 100, False)
        ]
    })
    assert _cita_viva("plataforma/web/zzz_almacen.py", 1, 0, buscar)[0] == "movida"


# --- Los comandos que los documentos mandan ejecutar -------------------------


def test_se_sacan_los_comandos_de_una_linea():
    assert _comandos("uv run python -m projects.cesta.pipeline") == [
        ("modulo", "projects.cesta.pipeline")
    ]
    assert _comandos("cd app; npm run build") == [("npm", "build")]


def test_el_comando_de_uvicorn_se_guarda_sin_adorno():
    # El fallo: se guardaba `"uvicorn plataforma.api.main:app"` y luego se partia
    # por `:` para sacar el modulo, con lo que le llegaba
    # `"uvicorn plataforma.api.main"`, contestaba "no es de casa" y **saltaba el
    # comando sin medirlo**. El dato que se busca va pelado.
    assert _comandos("uv run uvicorn plataforma.api.main:app --port 8099") == [
        ("uvicorn", "plataforma.api.main:app")
    ]


def test_el_comando_de_uvicorn_se_mira_de_verdad():
    propias = {"projects", "plataforma", "core"}
    assert _comando_existe("uvicorn", "plataforma.api.main:app", propias, {}, set()) is True
    assert _comando_existe("uvicorn", "plataforma.api.zzz:app", propias, {}, set()) is False
    # Y uno que no es de casa sigue sin mirarse.
    assert _comando_existe("uvicorn", "algo.de.fuera:app", propias, {}, set()) is None


def test_el_texto_del_aviso_se_compone_al_final():
    assert _como_se_escribe("npm", "build") == "npm run build"
    assert _como_se_escribe("uvicorn", "plataforma.api.main:app") == (
        "uvicorn plataforma.api.main:app"
    )
    assert _como_se_escribe("modulo", "projects.cesta.pipeline") == "projects.cesta.pipeline"


def test_un_comando_de_mentira_no_es_un_comando():
    # `python -m projects.cesta.<lo-que-sea>` y `...` son plantillas.
    assert _comandos("uv run python -m projects.cesta.<modulo>") == []
    assert _comandos("uv run python -m projects.cesta... ") == []


def test_los_modulos_de_casa_se_miran():
    propias = {"projects", "plataforma", "core"}
    assert _existe_modulo("projects.cesta.pipeline", propias) is True
    assert _existe_modulo("projects.cesta.zzz_no_existe", propias) is False


def test_lo_que_no_es_de_casa_no_se_mira():
    # `pytest`, `uvicorn`, `http.server`: avisar de esto seria avisar de todo el
    # rato y ninguno de los avisos seria un fallo del repositorio.
    propias = {"projects", "plataforma", "core"}
    assert _existe_modulo("pytest", propias) is None
    assert _existe_modulo("http.server", propias) is None
    assert _existe_modulo("uvicorn", propias) is None


def test_una_ruta_de_contenedor_no_se_mira():
    assert _existe_fichero("/app/plataforma/api/main.py", {}) is None
    assert _existe_fichero("$CARPETA/lo.py", {}) is None


def test_un_fichero_citado_por_su_final_vale():
    indice = {"zzz_pipeline.py": [RAIZ / "projects/cesta/zzz_pipeline.py"]}
    assert _existe_fichero("zzz_pipeline.py", indice) is True
    assert _existe_fichero("cesta/zzz_pipeline.py", indice) is True
    assert _existe_fichero("otra_carpeta/zzz_pipeline.py", indice) is False
