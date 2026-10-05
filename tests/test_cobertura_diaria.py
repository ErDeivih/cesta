"""El aviso de cobertura diaria: la cadena que trae menos de lo que esa cadena sabe traer.

Lo que se fija aqui es la decision que costo cuatro dias de no enterarse: **la referencia es el
maximo de una ventana larga, no la captura de ayer ni la mediana**. Alcampo bajo de 37.019 filas
de bronze a 24.120 en dos dias, y despues a cero durante cuatro, sin que saltara ningun control:

  - `core.cobertura.revisa` compara rama por rama contra el bronze anterior, asi que una bajada
    lenta se mide contra si misma;
  - `core.cobertura.sin_bronze` mira las cadenas que dijeron haber ido bien, y Alcampo dijo que
    habia fallado.

Y la otra cosa que se fija: **los dias sin fichero no estan en la serie**. La primera version
contaba los huecos mirando las fechas que habia, asi que una cadena con cuatro dias sin traer nada
salia con cero huecos -- justo el caso que esto existe para cazar.
"""
import datetime as dt

from projects.cesta import cobertura_diaria


def _serie(filas_por_dia: dict[str, int], hasta: str = "2026-10-05") -> dict[str, int]:
    """Una serie de dias hacia atras, terminando en `hasta`."""
    fin = dt.date.fromisoformat(hasta)
    return {(fin - dt.timedelta(days=i)).isoformat(): n
            for i, n in enumerate(filas_por_dia.values())}


def test_una_captura_normal_no_levanta_la_voz():
    serie = _serie({"2026-10-05": 24_000, "2026-10-04": 24_100, "2026-10-03": 23_900})
    v = cobertura_diaria.veredicto(serie, "2026-10-05", dias=3)
    assert v["veredicto"] == "ok"
    assert v["referencia"] == 24_100
    assert v["pct"] == 99.6


def test_una_cadena_que_no_trae_nada_lo_dice():
    serie = _serie({"2026-10-01": 24_000}, hasta="2026-10-01")
    v = cobertura_diaria.veredicto(serie, "2026-10-05", dias=5)
    assert v["veredicto"] == "sin datos"
    assert v["filas"] == 0
    assert v["pct"] == 0.0


def test_los_dias_sin_fichero_cuentan_como_hueco():
    """El caso de Alcampo: cuatro dias seguidos sin escribir ni una captura.

    La serie solo tiene los dias que hay, asi que contar los huecos por la serie daba cero.
    """
    serie = {"2026-10-01": 24_000, "2026-09-30": 23_900}
    v = cobertura_diaria.veredicto(serie, "2026-10-05", dias=5)
    assert v["dias_en_la_ventana"] == 5
    assert v["dias_sin_datos"] == 3, (
        "los dias 2, 3 y 4 no tienen fichero y tienen que contar como huecos")
    assert v["referencia"] == 24_000


def test_la_referencia_es_el_maximo_de_la_ventana_y_no_la_mediana():
    """Un dia bueno viejo sostiene la vara: es lo que esa cadena sabe traer.

    Es el caso real: con la mediana, la captura corta de Alcampo se daba por buena.
    """
    serie = _serie({"2026-10-05": 24_000, "2026-10-04": 24_000, "2026-10-03": 24_000,
                    "2026-10-02": 24_000, "2026-10-01": 37_019})
    v = cobertura_diaria.veredicto(serie, "2026-10-05", dias=4)
    assert v["referencia"] == 37_019, "con la mediana, la captura corta se daria por buena"
    assert v["veredicto"] == "corta"
    assert v["pct"] == 64.8


def test_hoy_no_sube_su_propia_vara():
    """Una captura buena no puede ser su propia referencia."""
    serie = _serie({"2026-10-05": 37_019, "2026-10-04": 10_000})
    v = cobertura_diaria.veredicto(serie, "2026-10-05", dias=1)
    assert v["referencia"] == 10_000
    assert v["veredicto"] == "ok"


def test_sin_referencia_no_se_puede_decir_nada():
    """El primer dia de una cadena no se puede juzgar: no hay con que comparar."""
    v = cobertura_diaria.veredicto({}, "2026-10-05", dias=7)
    assert v["referencia"] == 0
    assert v["dias_sin_datos"] == 7
    assert v["veredicto"] == "sin datos"


def test_la_cadena_diaria_lo_llama_sin_leer_sus_argumentos():
    """`main([])` y no `main()`: si leyera el `sys.argv` de la pasada, un argumento que no
    conociera lanzaria `SystemExit` --que no es una `Exception`-- y se llevaria por delante el
    dia entero. Un aviso que puede tumbar la pasada deja de ser un aviso."""
    import inspect

    from projects.cesta import run

    firma = inspect.signature(cobertura_diaria.main)
    assert "argv" in firma.parameters, (
        "main() no acepta una lista de argumentos, asi que lee el sys.argv de quien lo llame")
    fuente = inspect.getsource(run)
    assert '.main([])' in fuente, (
        "la cadena diaria lo llama con main() a secas: cualquier argumento suyo mata la pasada")
