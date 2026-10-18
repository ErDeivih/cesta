"""Una fila por ejecucion + deteccion de deriva. Vale mas que el propio scraper."""
from __future__ import annotations

import csv
import threading
from datetime import datetime, timezone

from core import config

LOG = config.DATA / "runs.csv"
FIELDS = ["ts", "fuente", "filas", "errores", "segundos", "ok"]

# *** EL TEXTO DEL ERROR VA APARTE, *y no es un detalle*. ***
#
# *El 18/10/2026 Carrefour fallo en **5,2 segundos** con **cero** filas, despues de haber
# traido 16 561 el dia anterior.* *`runs.csv` guardo `errores=1` -- **cuantos**, no **cuales**
# --, y en disco no quedo **nada**: ni raw, ni bronze, ni un mensaje.*
# *Asi que la causa no se pudo investigar, y el siguiente fallo habria sido igual de invisible.*
#
# *`runs.csv` sigue teniendo seis columnas: **las pruebas y `check_drift` dependen de ellas**, y
# meter aqui un texto libre con saltos de linea rompe el CSV.* *El detalle va a su propio
# fichero, **rotado por tamano**, que es lo que pide M18.*
LOG_ERRORES = config.DATA / "errores.log"

#: *Cuando el log de errores pasa de este tamano, se rota a `.1`.* *No crece sin fin y no
#: necesita un servicio de logs para hacerlo.*
MAXIMO_LOG_ERRORES = 1_000_000


# Con las cadenas en paralelo, cinco hilos terminan y escriben aqui casi a la vez.
# Dos filas a medio escribir en el mismo renglon dejan el fichero ilegible, y este
# fichero es el unico sitio donde consta que una ejecucion paso.
_CANDADO = threading.Lock()


def log_run(fuente: str, filas: int, errores: int, segundos: float,
            completa: bool | None = None) -> None:
    """Apunta la ejecucion. `completa` es el veredicto del colector.

    La columna `ok` decide dos cosas: si esta captura sirve de referencia para
    `check_drift` y si cuenta como "la ultima vez que salio bien". Durante
    diecinueve ejecuciones se calculo aqui dentro como `errores == 0`, que **no
    es lo que el colector entiende por buena**.

    Carrefour tiene siempre cuatro o cinco categorias que fallan -- papeleria
    rota, alguna difunta -- y las da por buenas porque entran en su tolerancia
    (4 de 653 el 20 de septiembre de 2026, con tolerancia 13). Su bronze se
    escribe, su dia es correcto, y sin embargo **ni una sola de sus 19
    ejecuciones tiene `ok=True`**.

    Consecuencia: `check_drift` busca la ultima fila buena de carrefour, no
    encuentra ninguna y devuelve None. El aviso de deriva de Carrefour **nunca
    ha estado armado**. El 18 de septiembre su catalogo se hundio de 16.416 a
    11.613 filas, un 29 % menos, y no salto: no tenia con que comparar.

    Asi que `ok` pasa a ser lo que el colector decide. Si no se le dice nada se
    mantiene la regla vieja, para no romper a quien llame con cuatro argumentos.
    """
    with _CANDADO:
        _escribe(fuente, filas, errores, segundos, completa)


def _escribe(fuente: str, filas: int, errores: int, segundos: float,
             completa: bool | None = None) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if nuevo:
            w.writeheader()
        w.writerow({
            "ts": datetime.now(timezone.utc).isoformat(),
            "fuente": fuente, "filas": filas, "errores": errores,
            "segundos": round(segundos, 1),
            "ok": (errores == 0 if completa is None else completa) and filas > 0,
        })


def log_error(fuente: str, texto: str) -> None:
    """*** El texto de un fallo, *para que se pueda investigar despues*. ***

    *Se separa de `runs.csv` a proposito: el CSV apunta **cuantas** cosas fallaron y este
    fichero **que** fallo.* *Un texto con saltos de linea dentro de una columna CSV rompe el
    CSV, y el CSV es la unica prueba de que una pasada ocurrio.*

    *Se rota por tamano: cuando pasa de `MAXIMO_LOG_ERRORES`, el anterior se queda como `.1`.*
    *No se borra historia sin dejar rastro: se conserva la ultima pasada.*
    """
    with _CANDADO:
        LOG_ERRORES.parent.mkdir(parents=True, exist_ok=True)
        try:
            if LOG_ERRORES.exists() and LOG_ERRORES.stat().st_size > MAXIMO_LOG_ERRORES:
                anterior = LOG_ERRORES.with_suffix(LOG_ERRORES.suffix + '.1')
                anterior.unlink(missing_ok=True)
                LOG_ERRORES.rename(anterior)
        except OSError:
            # *Si no se puede rotar, se sigue escribiendo: perder el mensaje es peor que un
            # log grande.*
            pass
        with LOG_ERRORES.open('a', encoding='utf-8') as fh:
            fh.write(datetime.now(timezone.utc).isoformat() + '\t' + fuente + '\t' +
                     texto.replace('\n', ' | ')[:4000] + '\n')


def check_drift(fuente: str, filas_hoy: int, tolerancia: float = 0.10) -> str | None:
    """Compara con la ultima ejecucion buena. Devuelve mensaje de alerta o None.

    Callar cuando no hay con que comparar era el fallo de fondo. Carrefour no
    tenia ni una fila `ok=True` en 19 ejecuciones (ver `log_run`), asi que este
    control devolvia None todos los dias: no avisaba de deriva **y tampoco
    avisaba de que no estaba mirando nada**. Un control que aprueba en silencio
    cuando no tiene referencia es peor que no tener control, porque ademas
    tranquiliza.

    Ahora, si la cadena ya ha corrido antes pero ninguna de sus ejecuciones
    consta como buena, eso se dice en voz alta.
    """
    if not LOG.exists():
        return None
    todas = [r for r in csv.DictReader(LOG.open(encoding="utf-8"))
             if r["fuente"] == fuente]
    rows = [r for r in todas if r["ok"] == "True"]
    if not rows:
        if todas:
            return (f"[SIN REFERENCIA] {fuente}: {filas_hoy} filas hoy y "
                    f"{len(todas)} ejecuciones anteriores, ninguna marcada como "
                    f"buena. No hay con que comparar, asi que la deriva no se "
                    f"esta vigilando.")
        return None
    prev = int(rows[-1]["filas"])
    if prev and abs(filas_hoy - prev) / prev > tolerancia:
        return f"[DERIVA] {fuente}: {filas_hoy} filas hoy vs {prev} la ultima vez"
    return None
