# F07 -- Compra rapida, familiar y clara (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:121`:**

> Investigar C01-C05 con Bring!/AnyList/Listonic. Mejorar solo lo que falte: lista por pasillos y orden por
> pasillo...
> Dos usuarios concurrentes del mismo hogar **no pisan cantidades ni tachados**; conflictos claros, sin
> empujar[se]...
> **Aceptacion:** tarea movil con una mano, recorrido de cuenta vacia, recarga y **dos sesiones**; medir pasos

*Y el encargo pone esto **despues** de los cierres*, asi que se empieza por lo que se puede comprobar.

---

## 1. Lo que hay que comprobar primero: **la concurrencia**, y ya tiene mecanismo

*Antes de «mejorar solo lo que falte» hay que saber **que falta**, y la parte verificable del criterio es la
concurrencia:* **dos usuarios del mismo hogar no pisan cantidades ni tachados.**

**Y el mecanismo existe**, en `plataforma/api/main.py`:

```
870  @app.post("/api/listas/{lista_id}/sincronizar")
871  def sincronizar(lista_id: str, cambios: list[dict], usuario: dict = Depends(usuario_actual)):
872      """Lo que se hizo sin cobertura, todo de golpe.
874      Cada cambio lleva su hora del movil. Como anadir y tachar son idempotentes,
875      subir dos veces lo mismo no rompe nada: es justo lo que pasa cuando la red
876      va y viene en el pasillo del supermercado.
877      """
```

**Asi que esta disenado para el caso real**: *cambios hechos **sin cobertura** en el pasillo, subidos **de
golpe** al recuperarla, **cada uno con su hora del movil**, y con **anadir y tachar idempotentes** -- *subir
dos veces lo mismo no rompe nada.*

### Y lo que queda por comprobar, con precision

**El endpoint resuelve el caso de UN usuario que pierde la red.** *Lo que el criterio pide ademas es **DOS
usuarios a la vez***, y ahi hay una pregunta abierta y concreta:

> **¿`momento` se usa para resolver conflictos, o solo viaja?**

*El parametro esta ahi (`c.get("momento")`, linea 888) y se pasa a `almacen.cambia_linea`. **Si `cambia_linea`
lo usa para decidir quien gana, la afirmacion del criterio es cierta; si lo ignora y escribe el ultimo que
llega, entonces dos usuarios si se pisan** -- *y la ultima linea escrita gana por orden de llegada, no por hora
del movil.*

**Es una pregunta de una funcion**, y *es lo primero que hay que mirar en F07: **leer `almacen.cambia_linea` y
ver si `momento` decide algo.***

### Y lo demas del criterio, para no perderlo

| lo que pide | estado |
|---|---|
| **dos sesiones, sin pisarse** | **mecanismo existe**; *falta comprobar si `momento` resuelve* |
| **lista por pasillos y orden por pasillo** | *por medir* -- *¿hay `categoria` en las lineas de la lista?* |
| C01-C05 con Bring!/AnyList/Listonic | **estudio de competencia**: *`docs/SUPERAPP-COMPETENCIA-Y-REA.md`* |
| **tarea movil con una mano** | *por medir* |
| **recorrido de cuenta vacia** | *por medir* |
| **medir pasos** | *por hacer, y es un numero* |

**Y el orden correcto es el que ya funciona en esta fase**: *primero **medir que falta** -- `momento`, los
pasillos, y los pasos --, y despues mejorar.* **No al reves.**
