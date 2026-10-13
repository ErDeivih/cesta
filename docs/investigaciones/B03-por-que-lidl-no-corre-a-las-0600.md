# B03 · **Por que Lidl no corre a las 06:00** -- y no es «a proposito», es un argumento que falta

*(13 de octubre de 2026. **Se iba a anadir el horario y resulta que el problema es otro: la tarea SI llama a
Lidl, y Lidl se sale.**)*

## 1. La tarea si lo llama

*La tarea programada, leida:*

```
Cesta diaria   estado: Ready
  disparador: 2026-09-08T06:00:00+02:00
  accion:     F:\aprendizaje\scrap\ejecutar.bat   (en F:\aprendizaje\scrap)
```

*Y `run.py:40` tiene a Lidl en la lista:*

```python
ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl"]
```

> **Asi que la pasada diaria **si intenta** lanzar Lidl.** *No hay que anadirlo a ninguna lista: **ya esta**.*

## 2. Y lo que pasa es que se sale

`run.py:100`:

```python
mod = importlib.import_module(f"projects.cesta.collectors.{nombre}")
if not hasattr(mod, "main"):
    print("colector incompleto: tiene parser pero no main()")
else:
    bien = mod.main() == 0          # <-- SIN ARGUMENTOS
```

*Y el `main` de Lidl:*

```python
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(...)
    entrada = ap.add_mutually_exclusive_group(required=True)   # <-- REQUIRED
    entrada.add_argument("--html", ...)
    entrada.add_argument("--web", action="store_true", ...)
```

> **`run.py` llama `main()` sin argumentos, y el CLI de Lidl **exige** uno.** *Asi que `argparse` sale con
> `SystemExit`, y lo recoge la linea 105:*

```python
except SystemExit as exc:
    # Un colector con CLI propia (Lidl exige origen y region) no puede
    # terminar el proceso diario ni impedir publicar las otras cadenas.
    print(f"FALLO: el colector termino su CLI (codigo {exc.code}); revisa su configuracion")
```

**Que es una precaucion buena** -- *que un colector no tumbe el dia* -- **y a la vez, para Lidl, es la razon
por la que nunca recoge: **se sale por arriba, se imprime un aviso, y el dia sigue sin el**.*

## 3. Y esto **corrige lo que yo habia leido del colector**

*El docstring de `collectors/lidl.py` dice:*

> *«**No esta en la tarea de las 06:00, a proposito.** La ampliacion lo pide asi: "pasar una captura acotada
> antes de anadirlo a la tarea diaria". Se ejecuta a mano y no puede romper la pasada diaria.»*

**Y eso describe una intencion, no el mecanismo.** *Lo que hay medido es:* **la tarea lo llama, su `main`
necesita un argumento que `run.py` no le da, y por eso se sale.** *Asi que «no esta en las 06:00» es cierto
**por accidente de interfaz**, no por una puerta que alguien cerro.*

> **Y la diferencia importa para arreglarlo**: *si fuera una puerta, habria que abrirla; **como es un argumento
> que falta, hay que pasarselo**.*

## 4. Y lo que hace falta, entonces, es **una linea**

**`run.py` tiene que saber que hay colectores con CLI propia, y darles sus argumentos.** *Y hoy ya reconoce que
existen* -- *el comentario de la linea 106 lo dice con esas palabras* --, **pero no los trata distinto.**

*Lo que corresponde, y que hay que decidir con cuidado:*

  1. **Una tabla de argumentos por colector** *-- y para Lidl, `["--web", "--escribir"]`.*
  2. **Y la region**: *`--region` ya no hace falta pasarselo, porque **el colector la acredita desde
     `config.CODIGO_POSTAL`*** -- *que es lo que se arreglo en la ronda 25.* *Asi que basta `--web --escribir`.*
  3. **Y si no hay region acreditada, el colector sale con 1 y un motivo** *-- **y entonces la precaucion de
     `run.py` es la correcta**: se avisa y el dia sigue.*

> **Y el orden que el colector pedia ya se ha respetado**: *«pasar una captura acotada antes de anadirlo a la
> tarea diaria».* **La captura se hizo, el bronze se publico, y el recorrido hasta la pantalla esta
> comprobado.** *Ahora si toca el horario.*

## 5. Y lo que **no** se ha hecho en esta ronda

**No se ha tocado `run.py`.** *Y no por prudencia mal entendida, sino porque **esto es el camino diario de las
seis cadenas**: un cambio aqui que salga mal no rompe una pantalla, **rompe la ingesta de la casa**.*

*Asi que queda dicho, medido, con la linea exacta que hay que cambiar y los argumentos que hay que pasar* --
*y se hace con su prueba, que en este caso es **una ejecucion de verdad del runner**, no un mock.*
