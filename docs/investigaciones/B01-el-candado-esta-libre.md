# B01 · **Resuelto**: el `ejecucion.lock` esta **LIBRE**, y el `"0"` no significa nada

*(13 de octubre de 2026. **La duda de la ronda 129, resuelta leyendo `core/runlock.py`. Y no habia nada roto.**)*

## 1. Lo que hace el candado, literal

```python
core/runlock.py
  l12:  def ejecucion_exclusiva(path: Path | None = None):
  l13:      path = path or config.DATA / "ejecucion.lock"
  l16:      if path.stat().st_size == 0:
  l17:          fh.write(b"0")                                     # <- el byte que se bloquea
  l19:      fh.seek(0)
  l25:      msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)          # Windows
  l32:      fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # Linux
  l40:      msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)          # se suelta
  l42:      fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
```

> **Es un bloqueo del SISTEMA OPERATIVO sobre un byte del fichero** -- `msvcrt.locking` en Windows, `fcntl.flock`
> en Linux -- **no una bandera escrita en el contenido.**
>
>   - **el `"0"` se escribe UNA VEZ**, *si el fichero esta vacio (l16-17), **y solo para tener un byte que
>     bloquear**;*
>   - **`LK_NBLCK` y `LOCK_NB` son NO BLOQUEANTES**: *si ya estuviera tomado, el segundo proceso **falla**, no
>     espera;*
>   - **y el fichero NO SE BORRA al soltar** *-- por eso sigue en disco con su fecha del 7 de septiembre.*

## 2. Y entonces la respuesta es la LECTURA B

```
el candado esta LIBRE.
y la fecha del 7 de septiembre es la de su CREACION, no la de su ultimo uso.
```

> *** Y el `"0"` no significa «tomado» ni «libre»: significa «aqui hay un byte que bloquear». ***
>
> *Asi que **no hay candado viejo, ni ingesta bloqueada durante 36 dias**.* *Y el indicio que apuntaba a esto
> -- **tres versiones publicadas hoy** -- **queda confirmado por el codigo**, que es como se confirman las cosas.*

## 3. Y esto es lo contrario de una alarma, pero es exactamente la conducta correcta

**Lo que se hizo en la ronda 129 fue:** *ver el fichero, ver que tenia 36 dias, **y no concluir nada** -- *escribir
**las dos lecturas contrarias**, decir **cual era el indicio y que era un indicio**, y **dejar dicho que se
resolvia leyendo `core/runlock.py`**.*

> *Y **en una ronda se resolvio**: el candado es del sistema operativo, esta libre, y **no hay nada roto**.*
>
> *** Las dos lecturas eran posibles, y solo una era cierta. Si se hubiera escrito la A -- «la ingesta lleva 36
> dias sin arrancar» -- habria sido la NOVENA conclusion falsa de esta sesion, y la mas alarmante: habria
> justificado tocar el candado, o peor, **revivir la ingesta a mano sobre una base que ya tenia los datos**. ***
>
> **Y lo que la evito fue lo mismo de siempre: decir lo que no se sabia, en vez de elegir.**

## 4. Y el estado operativo queda afirmado, sin nada pendiente

```
AFIRMADO:
  - la tarea `Cesta diaria` existe, esta Ready, y su proxima es el 14/10/2026 a las 06:00
  - hay tres versiones publicadas de hoy, la mas nueva v20261013-155356 (15:53)
  - data/runs.csv: 226 pasadas de cinco cadenas, la ultima de hoy 10:48 (alcampo)
  - el candado esta LIBRE, y el fichero que queda es el byte que se bloquea
  - los 8 procesos python son de los `uv run` de esta tarde (parejas, 4 MB + grande)

Y NO HAY NADA PENDIENTE DE ESTA COMPROBACION.
```

> *** La ingesta esta sana: la tarea esta lista, la version de hoy esta publicada, el registro tiene las pasadas
> de hoy, y el candado esta suelto. ***
