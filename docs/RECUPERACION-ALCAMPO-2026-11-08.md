# Alcampo: segunda caída y recuperación automática (8/11/2026)

**Hecho el 2026-11-08.** La pasada de la mañana no llegó a arrancar; al relanzarla por la tarde,
Alcampo volvió a caer. Se recuperó desde el crudo y se dejó automatizado el camino.

## 1. Qué pasó

- A las 6:00 no había datos del día: `Cesta diaria` no llegó a correr (su última ejecución era del
  7/11). Se lanzó la recolección completa a las **15:12** con `ejecutar.bat --forzar`.
- Las otras cadenas fueron bien: Lidl 91, Aldi 2.824, Mercadona 4.286, DIA 5.686, Carrefour
  16.816 (1 error de catálogo, tolerable).
- **Alcampo cayó otra vez** a los 486 s: `TargetClosedError: Page.wait_for_timeout: Target page,
  context or browser has been closed`. No fue el selector: se cerró el navegador que resolvía el
  reto del WAF. Quedó crudo parcial (25 ficheros) y ningún bronce.
- El pipeline corrió con 5 de 6 cadenas y publicó `20261108-160601`, pero **sin Alcampo**: el
  vigilante marcó `sin_pasada` y fallo.

## 2. Recuperación desde el crudo

- `scripts/recuperar_alcampo.py` detectó: sin bronce del 8/11, última pasada de Alcampo no es de
  hoy, crudo presente y ninguna pasada en curso. Lanzó
  `projects.cesta.run --solo alcampo --sin-comprobar-precios` a las **16:08**.
- Tardó **6.676 s (1 h 51 min)** porque el crudo de la caída era incompleto y tuvo que volver a
  pedir categorías, con el WAF de por medio. Terminó con **23.313 productos y 0 errores**.
- Se escribió el bronce del 8/11 (1,46 MB) y el pipeline publicó **`20261108-175843`**:
  `precio_diario` hasta el **2026-11-08**, **2.760.653** filas, 63 días acumulados.
- El script retiró `data/INGESTA-DETENIDA.txt` y dejó
  `data/recuperacion-alcampo-2026-11-08.txt`.

## 3. Resultado por cadena (datos publicados del 8/11)

| Cadena | Productos | Errores | Estado | Nota |
|---|---:|---:|---|---|
| Carrefour | 16.816 | 1 | `ok` | error de catálogo conocido (HTTP 520) |
| DIA | 5.686 | 0 | `ok` | |
| Mercadona | 4.286 | 0 | `ok` | |
| Aldi | 2.824 | 0 | `ok` | |
| **Alcampo** | **23.313** | **0** | **`ok`** (recuperado) | 83,2 % de la vara del 17/10; aviso de captura corta, no fallo |
| Lidl | 91 | 0 | `ok` | alcance parcial |

Gold publicado: `20261108-175843`; 52.5xx productos en silver; cobertura declarada para las cinco
cadenas de catálogo. Vigilante: **1 aviso, 0 fallos** (captura corta de Alcampo).

## 4. Automatización (lo que queda montado)

- **`scripts/recuperar_alcampo.py`**: decide si hay que recuperar (sin bronce hoy, última pasada
  no es de hoy, crudo presente, sin ejecución en curso), evita repetir el intento
  (`data/recuperacion-alcampo-<fecha>.txt`), lanza solo Alcampo y devuelve códigos claros
  (0 recuperado/nada, 1 fallo, 2 en curso, 3 sin crudo, 4 ya intentado).
- **`ejecutar-vigilante.bat`**: tras el primer fallo llama al recuperador; si recupera, vuelve a
  mirar y termina en 0, sin dejar el aviso viejo. Si no, sigue con la segunda mirada y el aviso.
- **Pruebas**: `tests/test_recuperar_alcampo.py` (6 casos: sin bronce con crudo, sin crudo, bronce
  presente, pasada en curso, ya intentado, pasada buena de ayer). No lanza `run.py` en las pruebas.
- **Límite**: si el navegador se cierra durante el reto del WAF (lo de hoy), la recuperación puede
  tardar horas y volver a la red. El crudo se conserva para que la siguiente pasada sea más barata.
  El WAF sigue siendo el punto débil; la propuesta de subir la espera (60 → 120–180 s) queda en el
  diagnóstico del 7/11.
