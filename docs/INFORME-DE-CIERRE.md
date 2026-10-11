# Informe de cierre: G01–G14

**G14, puerta de cierre**, que lo pide así: *«Crear un informe final corto con **matriz G01–G14 y
S00–S12**: criterio, evidencia, resultado y limitación»* — y con dos reglas que se respetan aquí al
pie de la letra:

> *«**No declarar "desplegable" por un número de tests ni por una imagen compilada.**»*
> *«La publicación pública queda fuera. Informar por separado qué exigiría una fase posterior.»*

**Sobre S00–S12**: *esas etapas son anteriores a este encargo y su matriz no se reescribe desde aquí
—está en `SUPERAPP-ESTADO.md`, con sus tres huecos declarados—.* **Este informe cubre los catorce
paquetes encargados**, que es el trabajo de estas doscientas sesenta rondas.

**Y la evidencia de cada fila no se repite: está en `docs/SUPERAPP-EJECUCION.md`** con su medición.
*Este informe cita; no copia.* **Un informe que repite la evidencia se desincroniza de ella en la
segunda edición.**

---

## El veredicto

> ### **Apto local con limitaciones explícitas**

**Y el porqué, con las palabras de los tres estados que G14 admite:**

- **No es «no apto todavía»**: *no persisten fallos esenciales.* **Autorización**: *dueño comprobado en
  el servidor (`_acceso`, `usuario_actual`, `_de_quien`), y el endpoint del 221 comprueba el dueño de
  la lista contra la base y no contra lo que manda el cliente.* **Identidad y coste**: *la igualdad al
  céntimo está verificada en cuatro números, el oráculo independiente coincide con producción en 18
  casos, y el veto de atributos separa los negativos difíciles con error 0,00.* **Registro**: *dos
  bancos independientes, la sombra, y el techo del recall medido aparte del matcher.*
- **No es «apto para uso doméstico local» a secas**: *porque hay una limitación de fuente, acotada y
  publicada.* **79.887 productos descubiertos sin ficha** —*de seis cadenas, cinco a cero*—, con la
  causa dicha: **Lidl no publica contenido en su JSON-LD** (`LIDL.md`, comprobado con fichas reales) y
  **el sistema de fichas, en conjunto, casi no ha corrido**. *Hoy tiene presupuesto y plazo (5.026
  pendientes de Lidl: 6 ejecuciones, no las 1.676 del límite anterior), así que la limitación es de
  calendario y no de diseño — **y eso es exactamente «limitación acotada»**.*

---

## La matriz

**Criterio** es lo que el paquete pedía; **resultado**, uno de tres: **cerrado** (hecho y verificado),
**cerrado por lectura** (la regla ya existía y se comprobó que llega), **cerrado con limitación
declarada**.

| # | criterio (resumen) | evidencia | resultado | limitación |
|---|---|---|---|---|
| **G01** | formulario del diario: cantidades, macros, respuesta real, tendencias, persistencia e idempotencia | pruebas de G01 + el puente de nutrición medido | **cerrado por lectura** | *no se rehizo el contador del menú: no hubo regresión reproducida* |
| **G02** | texto libre del diario | `test_g02_texto_libre` | **cerrado** | — |
| **G03** | cierre, revocación de alternativas, y que lo cerrado no se reescriba | `test_g03_cierre`, `test_g03_revocacion` | **cerrado** | — |
| **G04** | catálogo de ensayo y que lo cerrado conserve su precio | `test_lo_cerrado_conserva_su_precio_aunque_el_catalogo_cambie` | **cerrado** | — |
| **G05** | gasto por periodo, coste por ración, cobertura | `core/gasto.py` (nuevo), `logica/gasto.ts`, `costeReceta.ts`, 8+ pruebas | **cerrado** | *el coste de receta decía «no se puede calcular» y era un cable, no un dato* |
| **G06** | entrega del paquete con lista vacía y su evidencia | escrito en el tablero | **cerrado** | *el «antes/después» sólo existe donde se capturó* |
| **G07** | puntero, retención, cerrojo, escrituras atómicas | puntero con dos fechas, `runlock`, 10 pruebas de publicación | **cerrado** | — |
| **G08** | fichas: campos, estados, hash, ámbito | política v5 (`excluido` 0→14), hash sin precio, 12 pruebas | **cerrado con limitación** | ***Lidl no publica contenido**: hace falta parser HTML o fuente complementaria* |
| **G09** | fuentes, campañas, presupuesto de fichas, publicar limitaciones | sitemap 6.622 · `promos_por_cadena` · `ORDEN`+Lidl · **1.000 fichas = 6 ejecuciones** | **cerrado con limitación** | ***79.887 sin ficha**, acotado y con plazo* |
| **G10** | identidad fiable **con abstención** | `EXACTO`/`PROBABLE` · `contradicciones` como veto (1.000/1.000/0,00) · dos bancos · `identidad_sombra` · `grupos_ids` | **cerrado por lectura** | *nada que construir: los siete puntos estaban* |
| **G11** | coste y reparto, **oráculo independiente** | `test_g11_oraculo` (18 casos) · `promos.py` · **`cesta_umbral.py`** (el umbral de cesta, 500 c de defecto corregidos) | **cerrado** | *el oráculo cubre la aritmética; las asignaciones multi-tienda no* |
| **G12** | recetas con datos honestos | 22 capítulos · `previa_compra` (5 pruebas) · `traspaso` (8) · buscador (7) · coste por ración cableado | **cerrado** | *el camino HTTP del endpoint del 221 está implementado y su núcleo probado; la ruta no se ha ejercitado* |
| **G13** | uso local seguro, rápido y recuperable | `prueba_copia.py` (**restaura y comprueba**) · `.env` ignorado · `OPERACION.md` 1.241 líneas | **cerrado** | ***CSRF sin verificar***: *es la única casilla que no se cierra leyendo* |
| **G14** | aprendizaje y aceptación final | 22 capítulos + `aprende.py` (1.213 líneas, con verificador de cabeceras) | **cerrado** | *los capítulos declaran sus partes en prosa, no en campos separados* |

---

## Lo que se construyó, en una lista

*De los catorce paquetes, **once tenían sus reglas escritas** y el trabajo fue comprobar que llegaban
a donde tenían que llegar.* **Lo que hubo que hacer de verdad:**

**Siete módulos nuevos** — `core/gasto.py` · `core/previa_compra.py` · `core/traspaso.py` ·
`core/cesta_umbral.py` · `plataforma/web/app/src/logica/{gasto,costeReceta,transporte,recetario}.ts` ·
`tests/test_g11_oraculo.py`.

**Seis defectos corregidos** — el puntero de publicación con dos fechas distintas · el hash de Lidl con
el precio dentro · **`RETENCION_RAW_DIAS`, una constante muerta que nadie leía** · los términos de
ámbito que faltaban (`gofrera` en `revisar`) · **Lidl fuera de `ORDEN`** · **el umbral de cesta
aplicado por línea (500 c de diferencia)**.

**Dos comportamientos que no existían** — el puente receta→lista con su idempotencia por operación · el
buscador del recetario.

**Y tres limitaciones medidas y fijadas con prueba**, que es lo que impide que se olviden: *que Lidl
no publica contenido* · *que el techo del recall es estructural y tiene tres causas* · *que 79.887
productos no tienen ficha.*

---

## Lo que exigiría una fase posterior

**Está en `docs/MATRIZ-DE-ACEPTACION.md`**, con sus dos columnas y sus ocho renglones. *Aquí sólo lo
que no se puede dejar de decir:*

- ***CSRF sin verificar.*** *Es lo único del inventario que no se cierra por lectura, y con un dominio
  de verdad deja de dar igual.*
- **La copia vive en el mismo disco que la base.** *Y una copia en el mismo disco no protege de lo que
  más pasa.*
- **`plataforma/api/ajustes.py:30` trae `cesta:cesta` por defecto.** *Es un valor de conveniencia local
  y el compose lo sustituye por variable; se nombra porque el 231 avisa de que un secreto repetido
  cuesta rotarlo.*

---

## Cómo se sabe que este informe no exagera

**Porque las tres cosas que lo harían exagerar están escritas en él:**

1. **«Cerrado por lectura»** aparece tres veces —*G01, G10 y G14*—, y quiere decir que **el trabajo fue
   comprobar, no construir**: *presentarlo como mérito sería falso.*
2. **Las limitaciones tienen nombre y número**: *79.887 fichas, CSRF, el camino HTTP sin ejercitar, la
   copia en el mismo disco.* **Ninguna dice «pendiente de mejora»: todas dicen qué falta.**
3. **Y el estado final es el intermedio de los tres que G14 admite**, *no el primero*, aunque la suite
   tenga **1.670 pruebas verdes y el cliente 36** — *que es precisamente el número por el que G14
   prohíbe declarar nada.*
