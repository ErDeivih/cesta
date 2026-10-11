# Fase 2 de Cesta · matriz de capacidades y veredicto

Fecha: 13 de octubre de 2026. **Todo lo que hay aquí está medido y commiteado**, con el comando al lado.
*Lo que no se ha hecho se dice como no hecho; los números salen de las ejecuciones, no de la intención.*

---

## 1. Qué se puede hacer hoy, de verdad

| capacidad | estado | con qué se comprueba |
|---|---|---|
| Buscar un producto y ver su precio por cadena | **funciona** | `/api/buscar?q=leche` → 200, 40 resultados |
| Estimar la lista, por tienda y repartida | **funciona** | 1.714 pruebas; oráculo exhaustivo de asignaciones |
| Repartir entre tiendas **eligiendo el óptimo** | **funciona** (≤200.000 asignaciones) | 200 escenarios al azar con **cero discrepancias** |
| Aceptar una alternativa y que el histórico guarde **la comprada** | **funciona** | prueba HTTP que **discrimina** (simulando lo anterior, falla) |
| Cerrar la compra y ver el importe final | **funciona** | 1.714 pruebas, base desechable y PostgreSQL |
| Apuntar una comida, reintentar y **no duplicar** | **funciona** | navegador de verdad: **1→1** con arreglo, **1→3** sin él |
| Reintentar dos veces **a la vez** | **funciona** | dos conexiones y barrera; antes: `IntegrityError` |
| Publicar una versión y que **la API la sirva** | **funciona** | HTTP con el código de hoy; V2 publicada cambia lo servido |
| Reanudar una captura **sin volver a pedirla** | **funciona** | `alcampo._cache_limpia` rechaza un reto cacheado |
| Saber **qué se ha capturado, procesado y publicado** | **funciona** | el resumen, corriendo |
| Fichas de producto (kcal, ingredientes, Nutri-Score…) | **no, en la práctica** | **79.887 en cola, 28 hechas (0,04 %)** |
| Usar Cesta con la API caída | **no medido** | — |
| Defensa CSRF | **no ensayado** | — |

---

## 2. Matriz por paquete

| paquete | estado | lo que falta, concreto |
|---|---|---|
| **F00** reconciliar | **en curso** | Matriz hecha. **8 de los 10 hallazgos siguen sin contrastar uno a uno.** |
| **F01** producto efectivo | **en curso** | Motor, cierre y **HTTP verificado**. Falta navegador, estabilidad ante reordenación, «comprar A otra vez» y migrar consumidores del ordinal. |
| **F02** diario | **en curso** | Reintento **verificado en la UX** y carrera arreglada. Falta **unidades** (g/ml/raciones) y vista previa congelada. |
| **F03** publicación | **en curso** | Todo hecho y probado **salvo los dos recorridos de navegador** que su aceptación pide. |
| **F04** privacidad/CSRF | **sin empezar** | — |
| **F05** fichas | **medido** | 79.887 pendientes. Falta **ejecutar**, medir **por campo** separando «no lo publica» de «no lo hemos pedido», y el parser. |
| **F06** matching y optimizador | **en curso** | Optimizador **cerrado** (oráculo, 9 discrepancias, garantía y límites publicados, `umbral` decidido con los folletos). Falta el **banco de matching**. |
| **F07–F16** | **sin empezar** | Mejoras funcionales y visuales: *van después de los cierres, según el encargo.* |

---

## 3. Pruebas reproducibles

**Las puertas**, y lo que dan hoy:

```
uv run ruff check . --output-format=concise          limpio
uv run pytest -q                                     1714 pasan, 0 fallan  (~2 min 50 s)
npm test          (cliente)                          42 pasan
npx tsc --noEmit                                     0
npm run build                                        154 modulos
```

**Los ensayos que existen y qué demuestran**, por si hay que volver a ellos:

| ensayo | qué demuestra |
|---|---|
| `tests/test_fase2_f01_sustitucion.py` | A pedido, B aceptado, 3 unidades y 3×2 → **500**, no 900 |
| `tests/test_g03_cierre.py` | el cierre archiva **lo que puso el precio**, por HTTP |
| `tests/test_fase2_f02_concurrencia.py` | misma clave a la vez → **una** entrada; choque → **400** |
| `plataforma/prueba_reintento.py` | el reintento **en un navegador**: 1→1 contra 1→3 |
| `core/oraculo_reparto.py` + su prueba | **cero discrepancias** en 200 escenarios al azar |
| `tests/test_fase2_f03_publicacion.py` | publicar tarde, fallo en el veredicto, e invariantes |
| `tests/test_fase2_f03_version_vigente.py` | la versión vigente **sin arrastrar polars** |

**Y el estado del dato, hoy**: `/api/estado` dice **`coherente: False`** —*los precios son del 11 y el
puntero del 7*—, y el resumen lo dice con las cuatro patas.

---

## 4. Veredicto honesto sobre uso doméstico local

**Lo que está listo para usarse en casa, hoy:**

**La compra.** *Buscar, estimar, repartir entre tiendas, aceptar alternativas, cerrar y consultar el
histórico.* **Es la parte más madura y la que tiene las pruebas más duras**: un oráculo independiente que
enumera asignaciones, un cierre que guarda el producto efectivo, y **1.714 pruebas** que pasan. *Si algo
de esto se rompe, hay una prueba que lo dice.*

**El diario.** *Apuntar comidas, reintentar sin duplicar, y que dos envíos a la vez no dupliquen.*
**Verificado en un navegador de verdad, no sólo en el motor**: *el ensayo reproduce el defecto (1→3) y
confirma el arreglo (1→1).*

**Lo que NO está listo, y conviene decir por qué:**

- **Las fichas de producto.** *79.887 en cola y 28 hechas.* **Cualquier cifra de nutrición o de
  ingredientes que se enseñe hoy cubre el 0,04 % del catálogo**, y *la ausencia no es una limitación de
  fuente: es trabajo sin ejecutar.*
- **Usar la app con la API caída.** *No medido.*
- **La publicación**: funciona y está probada por API, pero **falta el recorrido de navegador**, y
  **`/api/estado` lleva desde el 7 de octubre declarando el catálogo incoherente** porque el puntero no
  se ha movido. *Publicar lo arregla y es reversible; es una decisión de operación, no de código.*

**El veredicto, en una frase**: **para hacer la compra y llevar el diario, esto sirve hoy y está
probado; para mirar nutrición, todavía no, y la razón es que no se ha ejecutado el trabajo, no que no se
pueda saber.**

---

## 5. Lo que hay que hacer a continuación, en orden

1. **Ejecutar la cola de fichas de una cadena pequeña** (`aldi`, 3.206) **con presupuesto acotado**, y
   **medir por campo separando «no lo publica» de «no lo hemos pedido»**. *Primer trozo verificable de
   F05, y el que convierte la cifra en algo que no miente.*
2. **Los dos recorridos de navegador de F03** —*la receta está en
   `docs/investigaciones/F03-publicacion.md` §15: `CESTA_GOLD` a un sandbox, API en el 8101*—.
3. **Decidir sobre el puntero** (`20261007-103000` contra un gold del 11): publicar o dejarlo. *Es de
   operación.*
4. **Las unidades del diario** (g/ml/raciones) y la vista previa congelada —*lo que queda de F02*—.
5. **Los ocho hallazgos de F00** que siguen sin contrastar, y **F04** (CSRF) —*que el informe anterior
   aplazó con una inferencia que el encargo no acepta*—.
6. **El banco de matching de F06**, y después **F07–F16**.

*Los puntos 1, 3 y 4 son pequeños y concretos. El 6 y los paquetes F07–F16 son el grueso que queda.*
