# Recolección del 7/11/2026 — relanzada y diagnóstico de Alcampo

**Hecho el 2026-11-07 a las 14:22–14:39.** La pasada de la mañana terminó con Alcampo `ok=False`
y sin publicar el gold. David pidió relanzar las cinco cadenas y no perder datos.

## 1. Resultado por cadena (relanzamiento de 14:22)

| Cadena | Productos | Errores | Estado | Tiempo | Bronze |
|---|---:|---:|---|---:|---|
| Carrefour | 16.811 | 1 | `ok` | 416 s | 1,08 MB |
| DIA | 5.704 | 0 | `ok` | 81 s | 0,75 MB |
| Mercadona | 4.280 | 0 | `ok` | 107 s | 0,62 MB |
| Aldi | 2.826 | 0 | `ok` | 16 s | 0,22 MB |
| Alcampo | **22.834** | **0** | **`ok`** | 272 s | 1,42 MB |
| Lidl (informativo) | 91 | 0 | `ok` | 3,5 s | 0,02 MB |

- **Las seis particiones de bronce del 7/11 están escritas**, incluidas las cinco cadenas de
  catálogo y Lidl.
- **Gold publicado:** versión `20261107-143704`, con el día **2026-11-07**, **2.707.900** filas
  de histórico y 62 días acumulados (52.546 productos en silver).
- **Cobertura declarada** para las 5 cadenas de catálogo (`data/cobertura/*-2026-11-07.json`).
- **Vigilante:** `estado: "aviso"`, **1 aviso y 0 fallos** — Alcampo 22.834 frente a la referencia
  28.022 del 17/10 (81,5 %, «captura corta»). No es un fallo: el día está publicado y las seis
  cadenas tienen datos de hoy.
- **Productos por cadena en el gold publicado:** Carrefour 16.811 · DIA 5.690 · Mercadona 4.234 ·
  Aldi 2.635 · Alcampo 22.823 · Lidl 91 (el gold filtra algún producto fuera de alcance; son datos
  de la misma captura).

## 2. Qué pasó en la pasada de la mañana

- Sobre las **11:03** la tarea «Cesta diaria» arrancó (Windows la recuperó al iniciar sesión).
- Alcampo llegó a **22.897 productos con 1 error** tras **6.327 s**, pero el recorrido quedó
  cortado por el **reto de AWS WAF**: 20 renovaciones/11 intentos en una ventana de 60 s sin pasar
  el reto; el log lo dice literalmente (`tras 11 intentos en 60s ... sigue devolviendo el reto`).
- El colector **rechazó la captura parcial** porque no era completa y estaba «muy por debajo» del
  último bronze (28.977): conservó el anterior y devolvió `ok=False`; por eso no había partición de
  bronce del 7/11 para Alcampo y el día no se publicó.
- No fue un fallo del selector ni de la API de categorías: las categorías y los productos se
  leyeron bien hasta que el WAF cortó el paso. Es **bloqueo anti-bot / tiempo de espera**, no
  selector.

## 3. Por qué el relanzamiento sí funcionó

- El **crudo de la pasada fallida ya estaba en `data/raw/`**. El relanzamiento reutilizó esa caché
  y solo volvió a pedir lo que faltaba; de ahí que Alcampo tardase **272 s** en vez de 6.327 s y
  terminase con **0 errores**.
- Con 0 errores la captura se considera **completa** para el colector (`completa = not detener and
  errores == 0`) y se guarda, aunque su tamaño quede un 18,5 % por debajo de la referencia del
  17/10. Esa diferencia se declara como **captura corta** en la cobertura y en el vigilante.
- El aviso viejo `data/INGESTA-DETENIDA.txt` se ha retirado: la pasada ya está recuperada. A partir
  de ahora, `ejecutar.bat` lo borra cuando el vigilante termina en 0.

## 4. Qué hay que cambiar (decisión)

1. **No tocar selectores.** El fallo no está en el parseo: está en AWS WAF. Cambiar selectores
   habría roto una captura que funciona.
2. **WAF:** `core/waf.obtener()` usa `espera=60` por defecto y `core/waf` encadena 2 reintentos con
   la misma sesión + renovación. Con la IP marcada, 60 s no bastan. Propuesta: subir la espera a
   120–180 s (configurable), y mantener el orden sin ventana → con ventana. No se ha cambiado el
   código en esta ronda porque el relanzamiento ya ha recuperado el día; queda como tarea.
3. **Conservar el crudo siempre** (ya se hace): es lo que ha permitido recuperar el día con una
   pasada de 4,5 minutos. No se debe borrar `data/raw` de una captura fallida.
4. **No aceptar una captura parcial como canónica por tamaño**: se conserva la anterior para no
   mezclar catálogos. Si se quiere conservar el parcial para análisis, que sea un fichero aparte
   (`parcial.parquet`), nunca el bronze del día.
5. **Relanzar con `ejecutar.bat --forzar`** es la vía correcta cuando la pasada falla y el crudo
   está en disco; no hay que esperar al día siguiente.

## 5. Estado del vigilante

- Tarea «Cesta vigilante» restaurada a **08:00, 14:00 y 20:00** + inicio de sesión; próxima
  ejecución 07/11/2026 14:00.
- `data/avisos_ingesta.json`: `2026-11-07`, `estado: "aviso"`, 1 aviso (`captura_corta` de
  Alcampo), 0 fallos.
- `metricas-cesta.json`: `dias_historial: 62`, `ingesta.estado: "aviso"`.
