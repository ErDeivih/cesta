# F15 -- Offline, rendimiento y aprendizaje (P1/P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:185`:**

> **Definir que funciona sin red local/servicio: datos cacheados fechados, borradores y acciones pendientes.**
> **Medir busqueda/listas/fichas/graficas con volumen real: paginacion, indices, cargas, tamanos JS y latencia.**
> **Actualizar material educativo** con ejemplos reproducibles crudo -> normalizacion -> identidad -> coste/nutricion.
> **Aceptacion:** **mala conexion / error / recuperacion sin duplicados y cuenta cruzada**; **antes/despues de
> rendimiento**.

---

## 1. Punto de partida: **tres cosas distintas en un paquete**, y una de ellas ya tiene pieza medida

**De F15 no se ha medido nada.** *Pero el criterio son **tres trabajos que no se parecen**:*

| | que es | **como se mide** |
|---|---|---|
| **offline** | *definir **que funciona sin red*** -- datos cacheados fechados, borradores, acciones pendientes | *leyendo el codigo y **con el servidor caido*** |
| **rendimiento** | *medir con **volumen real**: paginacion, indices, cargas, tamanos JS y latencia* | ***midiendo***: `SELECT`, `du`, y tiempos |
| **aprendizaje** | *actualizar el material educativo con **ejemplos reproducibles*** | *leyendo y reescribiendo* |

**Y la aceptacion nombra la parte que **ya tiene una pieza medida en esta fase**:**

> *«mala conexion / error / recuperacion **sin duplicados y cuenta cruzada**»*

**«Sin duplicados y cuenta cruzada» es, palabra por palabra, `N01`/`N04`:** *la **clave de operacion** --
«el cliente la genera al enviar y **la repite si reintenta**… y **dos comidas legitimas llevan claves
distintas**».* **Y «cuenta cruzada» es la carrera que `test_fase2_f02_concurrencia.py` ya prueba**: *«misma
clave a la vez -> **una** entrada; choque -> **400**».*

**Asi que la mitad de la aceptacion de F15 esta **medida y pasando** -- *lo que falta es **lo de offline**: que
pasa cuando la red **no esta**.*

### Y hay dos piezas de offline que ya se han visto, y conviene anotarlas como pistas

1. **`alcampo._cache_limpia`** (`F03`): *«reanudar una captura **sin volver a pedirla**»* -- *y rechaza un reto
   cacheado.* **Es cache, y es del colector, no de la app.**
2. **`F14` acaba de anadir `prefers-reduced-motion`**, y **la app nueva no tiene `service worker`** -- *que es
   **la** pieza de offline en una web*. *Y el laboratorio auxiliar **bloquea los service workers** por defecto en
   sus escenarios (`service_workers: "block"`), **que es una pista de que el proyecto ya se topo con esto**.*

**Lo primero es un `SELECT`**: ***¿hay `service worker`, hay `localStorage` de datos, y hay cola de acciones
pendientes?*** *Tres preguntas, y **las tres son de codigo, no de pantalla** -- asi que se contestan antes de
levantar nada.*

### Y el rendimiento es lo unico de la fase que se mide **con reloj**

**«Antes/despues de rendimiento»** *exige **dos medidas**, y eso es lo que F16 quiere con «evidencia»:*
**paginacion** (¿hay?), **indices** (¿cuales?), **cargas** (¿cuantas peticiones?), **tamanos JS** (*el build ya
avisa: «Some chunks are larger than 500 kB»*) y **latencia**.

**Y el aviso del build no es una hipotesis: es un mensaje que el propio build escupe** -- *y **esta sin
resolver**.*
