"""Orquestador local. Lo que lanza el Programador de tareas de Windows.

Corre los colectores, no se detiene si uno falla, y al final ejecuta el pipeline
con lo que haya conseguido. Degradacion honesta: si una cadena cae, el resto del
dia sigue adelante y queda registrado en data/runs.csv.

En paralelo, no en fila. Cada cadena tiene su propio limitador de ritmo contra su
propio dominio, asi que lanzarlas a la vez NO pide mas deprisa a nadie: pide a
cinco sitios distintos al mismo tiempo. Y el tiempo de una pasada deja de ser la
suma para pasar a ser el maximo. Medido el 8 sep:

    en fila     carrefour 44 + alcampo 37 + mercadona 3 + dia 2 + aldi 1 = 87 min
    a la vez    max(44, 37, 3, 2, 1)                                     = 44 min

Casi todo ese tiempo es esperar a que pase el segundo siguiente, no calcular, asi
que los hilos se pasan la mayor parte del rato dormidos y no se estorban.
"""
from __future__ import annotations

import argparse
import importlib
import io
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core import cobertura, config
from core.runlock import ejecucion_exclusiva

# Orden a proposito para el modo en fila: primero los lentos. En paralelo el orden
# solo decide quien arranca antes, pero se conserva porque tambien es el orden en
# que se leen los resultados.
ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo"]

_QUIEN = threading.local()


class SalidaEtiquetada(io.TextIOBase):
    """Pone delante de cada linea la cadena que la escribio.

    Cinco colectores hablando a la vez sin esto dejan un log donde no se sabe
    quien dice que, y el log es lo unico que queda cuando la ejecucion corre de
    madrugada. Se acumula por hilo hasta el salto de linea, porque `print` escribe
    el texto y el salto en dos llamadas y si no saldrian partidas.
    """

    def __init__(self, real):
        self.real = real
        self.trozos: dict[int, list[str]] = {}
        self.candado = threading.Lock()

    def write(self, texto: str) -> int:
        etiqueta = getattr(_QUIEN, "nombre", None)
        if etiqueta is None:
            self.real.write(texto)
            return len(texto)
        clave = threading.get_ident()
        with self.candado:
            pendiente = self.trozos.setdefault(clave, [])
            pendiente.append(texto)
            if "\n" not in texto:
                return len(texto)
            entero = "".join(pendiente)
            pendiente.clear()
            cola = ""
            if not entero.endswith("\n"):
                entero, _, cola = entero.rpartition("\n")
                entero += "\n"
            for linea in entero.splitlines():
                self.real.write(f"[{etiqueta}] {linea}\n")
            if cola:
                pendiente.append(cola)
            self.real.flush()
        return len(texto)

    def flush(self) -> None:
        self.real.flush()


# Alcampo se queda en el hilo principal. Su renovacion de cookie abre un Chrome
# de verdad con Patchright, y la API sincrona de Playwright es delicada fuera del
# hilo principal. No cuesta nada respetarlo: Alcampo y Carrefour son los dos
# largos, asi que corran donde corran el reloj lo marca el mas lento de los dos.
EN_HILO_PRINCIPAL = "alcampo"


def _una_cadena(nombre: str) -> tuple[str, bool, float]:
    anterior = getattr(_QUIEN, "nombre", None)
    _QUIEN.nombre = nombre
    t0 = time.monotonic()
    bien = False
    try:
        mod = importlib.import_module(f"projects.cesta.collectors.{nombre}")
        if not hasattr(mod, "main"):
            print("colector incompleto: tiene parser pero no main()")
        else:
            bien = mod.main() == 0
    except Exception as exc:  # noqa: BLE001
        print(f"FALLO: {type(exc).__name__}: {exc}")
    segundos = time.monotonic() - t0
    print(f"terminado en {segundos:.0f}s")
    # Devolver la etiqueta a como estaba: si no, todo lo que imprima despues el
    # hilo principal (pipeline, emparejador, resumen) saldria firmado por Alcampo.
    _QUIEN.nombre = anterior
    return nombre, bien, segundos


def _en_paralelo(fuentes: list[str]) -> list[tuple[str, bool, float]]:
    resto = [n for n in fuentes if n != EN_HILO_PRINCIPAL]
    resultados: list[tuple[str, bool, float]] = []
    with ThreadPoolExecutor(max_workers=max(len(resto), 1)) as pool:
        futuros = {n: pool.submit(_una_cadena, n) for n in resto}
        if EN_HILO_PRINCIPAL in fuentes:
            resultados.append(_una_cadena(EN_HILO_PRINCIPAL))
        for nombre in resto:
            resultados.append(futuros[nombre].result())
    orden = {n: i for i, n in enumerate(fuentes)}
    return sorted(resultados, key=lambda r: orden[r[0]])


def descarta_sin_bronze(resultados: list[tuple[str, bool, float]],
                        dia: str) -> list[tuple[str, bool, float]]:
    """Una cadena que dice haber ido bien y no dejo bronze no ha ido bien.

    El 18 de septiembre de 2026 Alcampo termino con 20.571 productos y cero
    errores a las 08:26, y a las 08:52 su carpeta
    `bronze/fuente=alcampo/fecha=2026-09-18` ya no estaba. Nunca se supo quien la
    borro. Lo grave no fue perderla: fue que **nada se entero**. El pipeline
    siguio con la instantanea del dia anterior, el resumen dijo trece dias
    acumulados tan tranquilo, y en gold quedaron 20.559 filas que ya no se podian
    recalcular desde nada.

    Se mira **antes** del pipeline, que es cuando todavia tiene arreglo barato:
    el crudo del dia sigue en disco y `reprocesar` lo rehace en un minuto.

    Una cadena que se nego a escribir a proposito -- porque el control de
    cobertura vio media tienda desaparecida -- ya devuelve error, asi que nunca
    llega aqui.
    """
    dicen_que_bien = [n for n, bien, _ in resultados if bien]
    if not dicen_que_bien:
        return resultados
    perdidas = cobertura.sin_bronze(dicen_que_bien, dia)
    fuera = cobertura.apartados()
    for nombre in perdidas:
        motivo = fuera.get((nombre, dia))
        if motivo:
            print(f"[{nombre}] termino bien pero su bronze de hoy esta apartado "
                  f"en data/debug/descartados ({motivo}).")
        else:
            print(f"[{nombre}] TERMINO BIEN PERO NO HAY BRONZE DE HOY ({dia}), "
                  f"ni en su sitio ni entre los descartados.")
        print(f"[{nombre}]   arreglo:  uv run python -m projects.cesta."
              f"reprocesar --fuente {nombre} --fecha {dia}")
    if not perdidas:
        return resultados
    return [(n, bien and n not in perdidas, s) for n, bien, s in resultados]


def _veredicto(resultados: list[tuple[str, bool, float]], fallos: list[str]) -> int:
    """0 = el dia esta hecho. 1 = hay que reintentarlo en el proximo arranque.

    Que una cadena no colabore NO es un dia perdido. Alcampo lleva dias cortando,
    y con la regla anterior el dia nunca se marcaba como hecho: la tarea
    programada lo reintentaba en cada inicio de sesion, todas las veces, para
    acabar igual. El dia esta hecho cuando el pipeline ha corrido con algo fresco
    dentro; que falte una cadena se ve en el resumen, que para eso dice cuales no
    han refrescado hoy.
    """
    cadenas_ok = [n for n, bien, _ in resultados if bien]
    if fallos:
        print(f"=== fallaron: {', '.join(fallos)} ===")
    if "pipeline" in fallos or not cadenas_ok:
        print("=== dia NO completado: se reintentara en el proximo arranque ===")
        return 1
    if fallos:
        print(f"=== dia completado con {len(cadenas_ok)} de {len(resultados)} "
              f"cadenas ===")
        return 0
    print("=== todo correcto ===")
    return 0


def _main() -> int:
    ap = argparse.ArgumentParser()
    # nargs="+" a proposito: con "*", escribir `--solo` sin nombres devolvia una
    # lista vacia, que es falsa, y acababa lanzando las CINCO cadenas creyendo que
    # no lanzabas ninguna. Ahora eso es un error explicito.
    ap.add_argument("--solo", nargs="+", metavar="CADENA",
                    help="cadenas concretas; sin esto se ejecutan todas")
    ap.add_argument("--sin-pipeline", action="store_true")
    ap.add_argument("--sin-comprobar-precios", action="store_true",
                    help="salta la comprobacion contra la web de las cadenas")
    ap.add_argument("--sin-emparejar", action="store_true",
                    help="no reconstruir grupos entre cadenas ni calidades")
    ap.add_argument("--secuencial", action="store_true",
                    help="una cadena detras de otra, como antes; para depurar")
    args = ap.parse_args()

    fuentes = args.solo or ORDEN
    modo = "en fila" if args.secuencial or len(fuentes) == 1 else "a la vez"
    print(f"=== {config.ahora_local():%Y-%m-%d %H:%M} | {len(fuentes)} cadenas, {modo} ===")
    avisa_si_la_anterior_no_termino()
    marca_en_curso()
    t0 = time.monotonic()
    fallos = []

    original = sys.stdout
    sys.stdout = SalidaEtiquetada(original)
    try:
        if args.secuencial or len(fuentes) == 1:
            resultados = [_una_cadena(n) for n in fuentes]
        else:
            resultados = _en_paralelo(fuentes)
    finally:
        sys.stdout = original

    resultados = descarta_sin_bronze(resultados, str(config.hoy_local()))

    for nombre, bien, _ in resultados:
        if not bien:
            fallos.append(nombre)
    print(f"=== cadenas: {time.monotonic() - t0:.0f}s en total "
          f"({', '.join(f'{n} {s:.0f}s' for n, _, s in resultados)}) ===")

    if not args.sin_pipeline:
        try:
            importlib.import_module("projects.cesta.pipeline").main()
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] FALLO: {exc}")
            fallos.append("pipeline")

    # Los grupos se reconstruyen enteros cada dia, no se acumulan: son producto
    # del catalogo de hoy, y un catalogo distinto da grupos distintos. Cuesta
    # segundos y no toca la red, asi que no hay razon para conservar los de ayer.
    if not (args.sin_pipeline or args.sin_emparejar):
        try:
            importlib.import_module("projects.cesta.emparejar").main([])
            # **El manifiesto de publicacion** (T02): que se publica, con que capturas, con que
            # reglas y con que cobertura. Va despues del emparejador, que es lo ultimo que toca
            # gold. Y no puede tumbar el dia: si falla, se avisa y se sigue.
            try:
                importlib.import_module("core.manifiesto").escribe()
            except Exception as exc:  # noqa: BLE001
                print(f"[manifiesto] no se pudo escribir: {type(exc).__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"[emparejar] FALLO: {exc}")
            fallos.append("emparejar")

    # Tirar el crudo viejo antes del resumen. Va aqui y no en una tarea aparte
    # porque una limpieza que hay que acordarse de lanzar no se lanza nunca, y el
    # disco se llena igual.
    try:
        importlib.import_module("projects.cesta.limpiar").main([])
    except Exception as exc:  # noqa: BLE001
        print(f"[limpiar] no se pudo limpiar el crudo viejo: {exc}")

    # Los avisos: el §6 del encargo dice *"evaluarlas en la cadena diaria, despues del
    # pipeline"*, porque un aviso que solo salta cuando alguien abre la pantalla no es
    # un aviso. Va aqui, con gold ya entero y antes del resumen, que es quien lo cuenta.
    #
    # La base de datos de casa no publica su puerto, asi que desde el PC este paso no
    # la alcanza: lo dice, deja el resumen diciendo "no lo se" y el dia sigue. Un paso
    # que se cayera por eso convertiria un dia bueno en un dia fallido por una linea.
    if not args.sin_pipeline:
        try:
            importlib.import_module("projects.cesta.avisos").main([])
        except Exception as exc:  # noqa: BLE001
            print(f"[avisos] no se pudieron mirar: {exc}")

    # El resumen se imprime siempre, tambien cuando algo ha fallado: saber que
    # quedo en disco importa mas cuando el dia ha ido mal que cuando ha ido bien.
    if not args.sin_pipeline:
        try:
            importlib.import_module("projects.cesta.resumen").main([])
        except Exception as exc:  # noqa: BLE001
            print(f"[resumen] no se pudo imprimir: {exc}")

        # La unica comprobacion que mira hacia fuera: coger unos cuantos
        # productos al azar, abrir su pagina en la web de la cadena y ver si el
        # precio que publicamos es el que pone ahi. Todo lo demas comprueba que
        # somos coherentes con nosotros mismos, que es otra cosa.
        if not args.sin_comprobar_precios:
            try:
                importlib.import_module(
                    "projects.cesta.verificar_precios").main([])
            except Exception as exc:  # noqa: BLE001
                print(f"[precios] no se pudo comprobar contra la web: {exc}")

        # Primero se escriben las cifras de hoy, y despues se comprueba.
        #
        # El orden importa y llego tarde. `docs/CIFRAS.md` decia de si mismo que
        # "se reescribe entero despues de cada pasada" desde el 19 de septiembre
        # de 2026, y no lo reescribia nadie: se escribio a mano aquel dia. Asi
        # que el verificador cerraba todos los dias con "8 cifras posiblemente
        # caducadas", y las ocho eran las del 19 esperando en un fichero que se
        # suponia automatico. Un aviso que hay que descartar a mano todos los
        # dias deja de leerse, y el dia que avise de algo de verdad tampoco.
        try:
            importlib.import_module("projects.cesta.cifras").main()
        except Exception as exc:  # noqa: BLE001
            print(f"[cifras] no se pudo reescribir CIFRAS.md: {exc}")

        # Los documentos de este proyecto estan llenos de cifras medidas, y esa
        # es su virtud. Pero una cifra que fue cierta en septiembre y ya no lo
        # es resulta peor que no poner ninguna, porque nadie la vuelve a
        # comprobar. Esto avisa; no toca nada, y no hace fallar el dia.
        try:
            importlib.import_module("projects.cesta.verificar_docs").main()
        except Exception as exc:  # noqa: BLE001
            print(f"[documentos] no se pudieron verificar: {exc}")

        # **Cuanto trajo cada cadena, comparado con lo que esa cadena sabe traer.**
        #
        # Esto falta desde siempre y se noto el 5 de octubre de 2026: Alcampo llevaba **cuatro
        # dias sin traer una sola captura** y ningun control lo decia. `verificar_ingesta`
        # comprueba coherencia --lo que la cadena declaro, lo guardamos-- y una cadena que no
        # llega a declarar nada es coherente consigo misma; y el control de cobertura que ya
        # habia (`core/cobertura.py`) compara rama por rama contra el bronze **anterior**, asi
        # que desde que una captura viene corta, la corta es la vara de medir. Alcampo bajo de
        # 37.019 filas a 24.120 en dos dias sin que saltara nada.
        #
        # Avisa y no hace fallar el dia, como el de los documentos: una cadena corta no es
        # motivo para no recoger las otras cuatro.
        try:
            # Con `[]` a proposito: sin argumentos, `argparse` leeria el `sys.argv` de esta
            # pasada, y un argumento que no conociera lanzaria `SystemExit` -- que no es una
            # `Exception` y el `except` de aqui abajo no lo coge. Un aviso que puede tumbar el
            # dia deja de ser un aviso.
            importlib.import_module("projects.cesta.cobertura_diaria").main([])
        except Exception as exc:  # noqa: BLE001
            print(f"[cobertura] no se pudo mirar cuanto trajo cada cadena: {exc}")

        # Las cadenas abren ramas nuevas cada semana y nadie se entera. El 21 de
        # septiembre de 2026 Carrefour trajo 24 productos en 16 categorias que
        # el dia anterior no existian -- sandias y melones, fiambre de pavo,
        # bolleria tradicional -- y se quedaron sin pasillo: al final de la
        # lista y fuera de la pantalla de secciones.
        #
        # Se aplican solo las que heredan la seccion de su propio padre, que es
        # la misma regla con la que se auditan las que ya estan; las dudosas
        # salen por pantalla para que las ponga una persona. Una seccion puesta
        # a ojo es lo que mando los pañales a la panaderia.
        try:
            importlib.import_module(
                "projects.cesta.auditar_secciones").main(["--aplicar"])
        except Exception as exc:  # noqa: BLE001
            print(f"[secciones] no se pudieron auditar: {exc}")

    # Solo aqui, con todo hecho. Si el proceso muere antes, la marca se queda y
    # la siguiente ejecucion lo cuenta.
    quita_la_marca()
    return _veredicto(resultados, fallos)


EN_CURSO = config.DATA / "ejecucion_en_curso.txt"


def avisa_si_la_anterior_no_termino(marca: Path | None = None) -> str | None:
    """¿La ejecucion anterior llego al final, o la mataron por el camino?

    El 21 de septiembre de 2026 la de las 6:18 se corto a las 9:31 con Carrefour
    por la categoria 525 de 651 y Alcampo por la 250. Sin pipeline, sin gold y
    sin una sola linea que lo dijera: el log simplemente **se acaba a media
    frase** y empieza otro encabezado. El dia se salvo de casualidad, porque a
    las 9:32 David encendio el ordenador y el disparador de inicio de sesion
    lanzo otra.

    El bloqueo de fichero no sirve para esto: lo suelta el sistema operativo
    cuando el proceso muere, asi que una ejecucion matada no deja rastro. Esta
    marca si: se escribe al empezar y solo se borra al terminar entero.

    No hace fallar el dia -- lo de ayer ya no tiene arreglo -- pero se dice en
    voz alta, que es lo unico que convierte "no me entere" en "lo sabia".
    """
    marca = marca or EN_CURSO
    if not marca.exists():
        return None
    try:
        cuando = marca.read_text(encoding="utf-8").strip()
    except OSError:
        cuando = "?"
    aviso = (f"[ejecucion] AVISO: la ejecucion que empezo el {cuando} no llego a "
             f"terminar. Se quedo a medias y nadie lo conto; revisa el log de "
             f"ese dia antes de fiarte de sus datos.")
    print(aviso)
    return aviso


def marca_en_curso(marca: Path | None = None) -> None:
    marca = marca or EN_CURSO
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(f"{config.ahora_local():%Y-%m-%d %H:%M}", encoding="utf-8")


def quita_la_marca(marca: Path | None = None) -> None:
    (marca or EN_CURSO).unlink(missing_ok=True)


def main() -> int:
    try:
        with ejecucion_exclusiva():
            return _main()
    except RuntimeError as exc:
        print(f"[ejecucion] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
