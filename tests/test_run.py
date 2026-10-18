"""El orquestador: cinco cadenas a la vez sin que el log se vuelva ilegible."""
import re
import threading
import time
from unittest import mock

from projects.cesta import run


def _capturado(escrituras, etiqueta=None):
    real = mock.Mock()
    real.write = lambda t: escrituras.append(t)
    real.flush = lambda: None
    salida = run.SalidaEtiquetada(real)
    if etiqueta:
        run._QUIEN.nombre = etiqueta
    return salida


def test_cada_linea_lleva_delante_su_cadena():
    escrituras = []
    salida = _capturado(escrituras, "carrefour")
    try:
        salida.write("651 categorias\n")
    finally:
        run._QUIEN.nombre = None
    assert escrituras == ["[carrefour] 651 categorias\n"]


def test_print_escribe_texto_y_salto_por_separado_y_no_parte_la_linea():
    # print() hace dos write(): el texto y el "\n". Sin acumular por hilo, cada
    # linea salia partida en dos con la etiqueta repetida.
    escrituras = []
    salida = _capturado(escrituras, "dia")
    try:
        salida.write("508 paginas")
        assert escrituras == []          # todavia no hay linea entera
        salida.write("\n")
    finally:
        run._QUIEN.nombre = None
    assert escrituras == ["[dia] 508 paginas\n"]


def test_sin_cadena_asignada_la_salida_pasa_tal_cual():
    escrituras = []
    salida = _capturado(escrituras)
    salida.write("pipeline: hecho\n")
    assert escrituras == ["pipeline: hecho\n"]


def test_dos_hilos_no_se_mezclan_las_lineas():
    escrituras = []
    real = mock.Mock()
    real.write = lambda t: escrituras.append(t)
    real.flush = lambda: None
    salida = run.SalidaEtiquetada(real)

    def escribe(nombre, veces):
        run._QUIEN.nombre = nombre
        for n in range(veces):
            salida.write(f"linea {n}")
            time.sleep(0)
            salida.write("\n")

    hilos = [threading.Thread(target=escribe, args=(n, 20))
             for n in ("carrefour", "alcampo")]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert len(escrituras) == 40
    for linea in escrituras:
        assert linea.startswith(("[carrefour] linea ", "[alcampo] linea "))
        assert linea.endswith("\n")
        assert linea.count("\n") == 1


def test_una_cadena_que_revienta_no_tumba_a_las_demas():
    def falso(nombre):
        modulo = mock.Mock()
        if nombre == "aldi":
            modulo.main.side_effect = RuntimeError("se cayo la web")
        else:
            modulo.main.return_value = 0
        return modulo

    with mock.patch.object(run.importlib, "import_module", side_effect=lambda r: falso(r.split(".")[-1])):
        resultados = [run._una_cadena(n) for n in ("dia", "aldi", "mercadona")]
    assert [(n, ok) for n, ok, _ in resultados] == [
        ("dia", True), ("aldi", False), ("mercadona", True)]


def test_la_cadena_que_revienta_DEJA_SU_ERROR_ESCRITO(monkeypatch, tmp_path):
    """*** El 18/10/2026 Carrefour fallo y su error no quedo en ningun sitio. ***

    *Se imprimia por pantalla y nada mas, y esa pantalla no la guarda nadie.* *Asi que la causa
    de un fallo de **5,2 segundos con cero filas** no se pudo investigar.*

    *Esta prueba fija lo que ahora pasa: la cadena que revienta llama a `log_error` con **su
    nombre** y con **el texto y la traza** del fallo.*
    """
    llamadas = []
    monkeypatch.setattr(run, "log_error", lambda fuente, texto: llamadas.append((fuente, texto)))

    def falso(nombre):
        modulo = mock.Mock()
        if nombre == "carrefour":
            modulo.main.side_effect = RuntimeError("la web devolvio un desafio")
        else:
            modulo.main.return_value = 0
        return modulo

    with mock.patch.object(run.importlib, "import_module", side_effect=lambda r: falso(r.split(".")[-1])):
        run._una_cadena("carrefour")

    assert len(llamadas) == 1, "un fallo, una entrada"
    fuente, texto = llamadas[0]
    assert fuente == "carrefour"
    assert "RuntimeError" in texto, "el tipo, para saber que clase de fallo fue"
    assert "desafio" in texto, "el mensaje del servidor, que es el que dice POR QUE"
    assert "Traceback" in texto, "y la traza, que dice DONDE"


def test_una_cadena_que_sale_por_su_CLI_tambien_deja_constancia(monkeypatch):
    """*Lidl tiene CLI propia y puede cerrarse sola. Ese camino tambien es un fallo.*"""
    llamadas = []
    monkeypatch.setattr(run, "log_error", lambda fuente, texto: llamadas.append((fuente, texto)))

    def falso(nombre):
        modulo = mock.Mock()
        if nombre == "lidl":
            modulo.main.side_effect = SystemExit(2)
        else:
            modulo.main.return_value = 0
        return modulo

    with mock.patch.object(run.importlib, "import_module", side_effect=lambda r: falso(r.split(".")[-1])):
        _, bien, _ = run._una_cadena("lidl")

    assert bien is False
    assert len(llamadas) == 1
    assert llamadas[0][0] == "lidl"
    assert "codigo" in llamadas[0][1].lower()


def test_el_registro_de_ejecuciones_aguanta_varios_hilos(tmp_path):
    import csv

    from core import runlog

    with mock.patch.object(runlog, "LOG", tmp_path / "runs.csv"):
        hilos = [threading.Thread(target=runlog.log_run, args=(f"cadena{n}", n, 0, 1.0))
                 for n in range(25)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        filas = list(csv.DictReader((tmp_path / "runs.csv").open(encoding="utf-8")))
    assert len(filas) == 25
    assert all(f["fuente"].startswith("cadena") for f in filas)


def test_alcampo_se_queda_en_el_hilo_principal():
    """Su renovacion de cookie abre un Chrome de verdad, y la API sincrona de
    Playwright es delicada fuera del hilo principal. Como Alcampo y Carrefour son
    los dos largos, el reloj lo marca el mas lento de los dos corran donde corran.
    """
    hilos = {}

    def falso(ruta):
        nombre = ruta.split(".")[-1]
        modulo = mock.Mock()

        def registra():
            hilos[nombre] = threading.current_thread() is threading.main_thread()
            return 0

        modulo.main.side_effect = registra
        return modulo

    with mock.patch.object(run.importlib, "import_module", side_effect=falso):
        resultados = run._en_paralelo(["carrefour", "dia", "alcampo"])

    assert hilos["alcampo"] is True
    assert hilos["carrefour"] is False
    assert [n for n, _, _ in resultados] == ["carrefour", "dia", "alcampo"]


def test_despues_de_una_cadena_la_etiqueta_vuelve_a_estar_limpia():
    # Si no, el pipeline y el resumen saldrian firmados por la ultima cadena.
    with mock.patch.object(run.importlib, "import_module",
                           side_effect=lambda r: mock.Mock(main=lambda: 0)):
        run._una_cadena("alcampo")
    assert getattr(run._QUIEN, "nombre", None) is None


def _resultado(bien_por_cadena):
    return [(n, bien, 1.0) for n, bien in bien_por_cadena.items()]


def test_una_cadena_caida_no_convierte_el_dia_en_perdido():
    """Alcampo lleva dias cortando. Con la regla anterior el dia nunca se marcaba
    como hecho y la tarea lo reintentaba en cada inicio de sesion, todas las
    veces, para acabar igual. Que falte una cadena se ve en el resumen.
    """
    codigo = run._veredicto(
        _resultado({"carrefour": True, "dia": True, "mercadona": True,
                    "aldi": True, "alcampo": False}),
        ["alcampo"])
    assert codigo == 0


def test_si_no_refresca_ninguna_cadena_el_dia_se_reintenta():
    codigo = run._veredicto(
        _resultado({"carrefour": False, "alcampo": False}),
        ["carrefour", "alcampo"])
    assert codigo == 1


def test_si_falla_el_pipeline_el_dia_se_reintenta():
    # Sin pipeline no hay silver ni gold: da igual que las cadenas fueran bien.
    codigo = run._veredicto(_resultado({"dia": True}), ["pipeline"])
    assert codigo == 1


def test_un_dia_limpio_devuelve_cero():
    assert run._veredicto(_resultado({"dia": True, "aldi": True}), []) == 0


# --- la cadena que dijo "bien" y no dejo bronze -----------------------------

def _bronze(raiz, fuente, fecha):
    import polars as pl
    d = raiz / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
    d.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"x": [1]}).write_parquet(d / "part.parquet")


def test_la_cadena_sin_bronze_deja_de_contar_como_buena(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run.cobertura.config, "DATA", tmp_path)
    _bronze(tmp_path, "aldi", "2026-09-18")
    _bronze(tmp_path, "alcampo", "2026-09-17")      # la de ayer, no la de hoy

    salida = run.descarta_sin_bronze(
        [("aldi", True, 78.0), ("alcampo", True, 3770.0)], "2026-09-18")

    assert salida == [("aldi", True, 78.0), ("alcampo", False, 3770.0)]
    dicho = capsys.readouterr().out
    assert "NO HAY BRONZE DE HOY" in dicho
    assert "reprocesar --fuente alcampo --fecha 2026-09-18" in dicho


def test_con_todo_el_bronze_en_su_sitio_no_se_toca_nada(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run.cobertura.config, "DATA", tmp_path)
    _bronze(tmp_path, "aldi", "2026-09-18")
    entrada = [("aldi", True, 78.0), ("carrefour", False, 2271.0)]
    assert run.descarta_sin_bronze(entrada, "2026-09-18") == entrada
    assert capsys.readouterr().out == ""


def test_una_cadena_que_ya_habia_fallado_no_se_acusa_de_nada(tmp_path, monkeypatch, capsys):
    # Carrefour fallo y no escribio bronze: eso ya se sabia, no es un borrado
    # misterioso. Acusarla otra vez solo anade ruido al log.
    monkeypatch.setattr(run.cobertura.config, "DATA", tmp_path)
    _bronze(tmp_path, "aldi", "2026-09-18")
    run.descarta_sin_bronze([("aldi", True, 78.0), ("carrefour", False, 1.0)],
                            "2026-09-18")
    assert "carrefour" not in capsys.readouterr().out


def test_un_dia_en_que_no_fue_bien_ninguna_no_mira_el_disco(tmp_path, monkeypatch):
    monkeypatch.setattr(run.cobertura.config, "DATA", tmp_path / "no_existe")
    entrada = [("aldi", False, 1.0)]
    assert run.descarta_sin_bronze(entrada, "2026-09-18") == entrada


# --- una ejecucion que muere a medias tiene que dejar rastro -----------------

def test_una_ejecucion_matada_se_cuenta_en_la_siguiente(tmp_path, capsys):
    """El 21 de septiembre de 2026 la de las 6:18 se cortó a las 9:31.

    Carrefour por la categoría 525 de 651, Alcampo por la 250, sin pipeline y
    sin gold. El log **se acaba a media frase** y empieza otro encabezado: ni
    una línea decía que aquello se había quedado a medias. El día se salvó de
    casualidad, porque un minuto después el disparador de inicio de sesión lanzó
    otra ejecución.

    El bloqueo de fichero no sirve para esto: lo suelta el sistema operativo
    cuando el proceso muere, así que no deja rastro ninguno.
    """
    marca = tmp_path / "en_curso.txt"
    run.marca_en_curso(marca)
    assert marca.exists()

    aviso = run.avisa_si_la_anterior_no_termino(marca)
    assert aviso is not None
    assert "no llego a terminar" in aviso
    assert "AVISO" in capsys.readouterr().out


def test_una_ejecucion_que_termina_no_deja_marca(tmp_path):
    marca = tmp_path / "en_curso.txt"
    run.marca_en_curso(marca)
    run.quita_la_marca(marca)
    assert not marca.exists()
    assert run.avisa_si_la_anterior_no_termino(marca) is None


def test_quitar_una_marca_que_no_esta_no_revienta(tmp_path):
    run.quita_la_marca(tmp_path / "no-existe.txt")


def test_la_marca_lleva_cuando_empezo(tmp_path):
    """Sin la hora, el aviso no dice qué día hay que ir a mirar."""
    marca = tmp_path / "en_curso.txt"
    run.marca_en_curso(marca)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
                        marca.read_text(encoding="utf-8"))
