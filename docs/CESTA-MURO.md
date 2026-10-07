# El muro: todo lo que hay que hacer, en orden

> Encargo ampliado del 7 de octubre: empezar por
> [SUPERAPP-00-EMPEZAR-AQUI.md](SUPERAPP-00-EMPEZAR-AQUI.md).
> Define tres aplicaciones separadas, nueva dirección visual, renovación de
> fichas de todas las cadenas y ampliación de descubrimiento Lidl. Es un plan de
> ejecución con criterios, no una declaración de paquetes terminados.

> Revisión adicional del 6 de octubre: [superapp, correcciones y siguiente entrega](CESTA-REVISION-SUPERAPP-2026-10-06.md).
> Incluye prueba real de Lidl, alcance v3 para reutilizables y prototipo local de
> recetas/calorías. No cierra T02, T03 ni T11, ni autoriza despliegue público.

Este es el tablero de trabajo del encargo **Cesta familiar**. Se actualiza **en cada entrega**: un
paquete no se marca hecho por escribir la propuesta, sino cuando pasa sus pruebas de aceptación y
el documento de resultado va en el mismo commit que el código.

- **Contrato completo:** `docs/CESTA-PLAN-DE-IMPLEMENTACION.md` (decisiones cerradas y flujo).
- **Cómo se hace:** `docs/CESTA-DATOS-Y-COMPARACION.md` (dato) y
  `docs/CESTA-APLICACION-Y-GRAFICAS.md` (pantallas).
- **Detalle y aceptación de cada paquete:** `docs/CESTA-TAREAS-Y-ACEPTACION.md` (T01–T10).
- **De dónde sale todo esto:** `docs/AUDITORIA-CESTA-2026-10-05.md`.
- **Reglas de la casa:** `docs/TRASPASO-CHATGPT.md` §6 (todo número medido y con fecha, documentos
  en el mismo commit que el código, un instrumento que no puede medir tiene que decirlo).

Leyenda: `PENDIENTE` · `EN CURSO` · `HECHO` (código + pruebas + resultado medido) · `BLOQUEADO`.

---

## Lo que ya está comprobado y de dónde partimos

Medido el 5 de octubre de 2026 con `uv run python -m projects.cesta.auditar_identidad` (instrumento
de solo lectura, con prueba propia en `tests/test_auditar_identidad.py`):

| hecho | número |
|---|---:|
| productos en el catalogo | 53.139 |
| grupos multicadena | 8.812 |
| grupos multicadena con **varios EAN** | 2.276 |
| grupos multicadena con **varios formatos fiables** | 593 |
| productos de Alcampo en ramas excluidas (bazar, juguetes...) | 245 |
| columnas que faltan en gold para trazabilidad | `disponible`, `capturado_en`, `tienda_id` |

**Lo que esto significa, dicho claro: «grupo comparable» hoy no quiere decir «producto idéntico».**
La app puede presentar como ahorro el cambio de una marca por otra, y el plan existe para que deje
de hacerlo. Los fallos concretos que se vieron: Asturiana entera 6×1 l comparada con Celta entera
6×1 l; al añadir desde una ficha se guarda el grupo de alternativas y no el artículo exacto; el
optimizador admite precios de Alcampo del 1 de octubre estando configurado un límite de tres días;
el gasto archivado es estimado y se presenta como compra; las ventanas «30/90 días» cuentan
observaciones y no días; una caída de «Hogar y Decoración» puede bloquear la aceptación de
alimentarios nuevos.

---

## El muro

### Entrega E1 — Catálogo familiar

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T01** | Alcance de consumibles y presupuesto de extracción | — | el bazar sale del catálogo y del recorrido; se piden menos cosas y con motivo | **HECHO (2026-10-06)**: política v2 con la frontera del dueño, clasificador por frases contiguas, **banco de verdad** con 0 falsos descartes y 0 bazar aceptado sobre 37 etiquetas, y las cuatro cadenas que saben la categoría antes de pedir dejan de pedir bazar (Alcampo, Carrefour, DIA, Mercadona). Catálogo: 50.642 entran · 303 salen · 714 a revisar. **Aldi no se toca, y está medido**: saltarse su bazar ahorra 1 petición de 2.536 |

### T01 en detalle, cadena por cadena (lo que pide el contrato)

| cadena | qué hay que hacer | estado |
|---|---|---|
| **Alcampo** | filtrar árbol, categorías hijas y términos de búsqueda; volver a clasificar antes de bronze | **HECHO** (ramas que no se piden) · falta el filtro de producto |
| **Aldi** | separar surtido de consumo y bazar temporal; **no consultar los detalles del bazar solo porque estén en el sitemap** (es donde más peticiones se ahorran) | PENDIENTE |
| **Carrefour** | sitemap de supermercado, ramas permitidas y validación final de cada ficha: `supermercado` en la URL no garantiza consumible | PENDIENTE |
| **DIA** | categorías permitidas y filtro de producto, manteniendo alimentación animal y hogar | PENDIENTE |
| **Mercadona** | recorrer el surtido habitual y clasificar producto a producto, sin asumir que todo lo que publique un día pertenece al alcance | PENDIENTE |

Y en las cinco, lo mismo: **una rama excluida nunca veta una captura incluida**, y el producto se
clasifica otra vez antes de escribir bronze para no colar cruces de categoría.

### Entrega E2 — Identidad y ofertas

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T02** | Oferta trazable y publicación por versiones | E1 | cada catálogo dice con qué capturas y con qué reglas se publicó | **PRIMERA VERSIÓN HECHA (2026-10-06)**: `core/manifiesto.py` escribe `data/gold/manifiesto.json` al final de la pasada, con la versión y la **huella sha256 de la política**, la captura y las filas de cada cadena, la huella de cada fichero publicado, la cobertura declarada y avisos. Escritura atómica y no puede tumbar el día. Falta que la aplicación lo enseñe |
| **T03** | Identidad exacta (artículo / familia / alternativa) | T02 | dos cadenas solo se comparan cuando son el mismo producto o cuando alguien eligió la alternativa | **SIN EMPEZAR**. El laboratorio de comparación que dejó la ampliación (17.549 pares evaluados: 10.999 con contradicción, 1.014 candidatos por GTIN) es **diagnóstico**, no el algoritmo de producción. Es el corazón de que las comparaciones sean correctas |

### Entrega E3 — Lista fiel a la elección

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T04** | Migración de listas, favoritos y alertas (migración nueva después de la 010, `almacen.py`, `main.py`, `alertas.py`, `vigilante.py`, `catalogo.py`) | T03 | añadir desde una ficha guarda **ese** artículo; las alternativas se piden; ninguna alerta dispara por una bajada de otra marca; listas, favoritos y compras se conservan | **PENDIENTE** |

### Entrega E4 — Presupuesto correcto

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T05** | Selector único de ofertas elegibles (`cesta.py`, `catalogo.py`, `movimientos.py`, alertas) | T02–T04 | una oferta del día 1 no decide una cesta del día 5; fuera lo retirado, sin stock o sin zona; cada descarte explicado | **PENDIENTE** |
| **T06** | Cantidades, promociones y optimización (`core/promos.py`, `api/cesta.py`, preferencias) | T05 | los 11 casos de la tabla del contrato dan el resultado exacto; paquetes y unidades comparados por desembolso real; nada de dobles descuentos | **PENDIENTE** |

### Entrega E5 — Compra y gastos

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T07** | Compra confirmada e histórico familiar (migración nueva, `almacen.cierra_compra`, `main.cerrar_compra`, `cesta.coste_por_linea`, interfaz de cierre) | T04 y T06 | el importe confirmado y el estimado son series distintas; lo antiguo queda etiquetado como estimado; cierre idempotente | **PENDIENTE** |

### Entrega E6 — Experiencia final

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T08** | Interfaz cotidiana (`App.tsx`, Inicio, Buscar, Producto, Grupo, Favoritos, Cesta, `BotonAnadirACesta`...) | T04–T07 | cuatro rutas y los recorridos del contrato; etiquetas que no prometen identidad sin prueba; capturas en móvil y escritorio de todos los estados; probado por una persona ajena | **PENDIENTE** |
| **T09** | Gráficas correctas (`derive.py`, `api/analisis.py`, movimientos, consultas de gasto, componentes) | T02, T03, T07 | ventanas de calendario de verdad, series por identidad, episodios; gasto confirmado ≠ estimado ≠ contrafactual; cada céntimo rastreable | **PENDIENTE** |
| **T10** | Verificación diaria y entrega operativa (`run.py`, `ejecutar.bat`, verificadores, documentación) | todas | métricas por fuente, inyección de fallos (bloqueo, categoría vacía, corte de publicación), y una fuente sin dato aceptado **no** se llama correcta | **PENDIENTE** |

---

## Reglas de ejecución (del contrato, y no se saltan)

1. Comprobar Git y procesos activos antes de tocar nada; preservar los cambios del dueño
   (`core/datos/secciones.yml` y `docs/CIFRAS.md` están modificados a propósito y no entran en
   commits de tareas).
2. Línea base de pruebas primero. Desarrollar contra **copia** de datos y base de pruebas: no se
   lanza la pasada de horas para probar una regla de identidad.
3. Una entrega es código + migración (si toca) + pruebas + resultado **medido**. Nada de marcar un
   paquete por escribir la propuesta.
4. No publicar gold con otro esquema sin probar todos sus consumidores y el adaptador antiguo.
5. Probar rollback y compatibilidad de listas y compras antes de cualquier corte de versión.
6. Cerrar cada paquete con la plantilla de `CESTA-TAREAS-Y-ACEPTACION.md` §«Plantilla obligatoria»:
   estado, archivos, qué cambia para la persona, pruebas y resultado, métricas antes/después **con
   fecha**, compatibilidad y recuperación, y pendientes con condición concreta.

---

## Preguntas al dueño (contestadas antes de empezar a fondo)

1. **Dónde está la frontera del «consumible».** El contrato incluye alimentación, frescos, bebidas,
   limpieza, higiene, bebé, mascotas y consumibles domésticos, y excluye el bazar duradero. Los
   casos que quiero que confirmes, porque deciden qué se deja de pedir el primer día: **bombillas,
   pilas, bolsas de basura, papel de cocina, papel higiénico, servilletas, insecticidas, ambientadores,
   cubos y bayetas, menaje barato (vasos, fiambreras), juguetes de mascota, arena de gato, comida de
   mascota**.
2. **Qué va primero dentro de E2**: infraestructura (T02: trazabilidad y publicación por versiones)
   o identidad (T03: que la comparación sea del mismo producto). El plan los pone en ese orden; si
   prefieres ver antes el arreglo de las comparaciones, se cambia el orden y T02 pasa después.
3. **Cuánto puedo cambiar el aspecto.** T08 pide una navegación y unos recorridos nuevos. ¿Mantengo
   el lenguaje visual actual y sólo arreglo flujos y etiquetas, o puedo rediseñar pantallas? Y si
   rediseño, ¿sigo usando Stitch para las pantallas nuevas (la clave nunca entra en el repositorio)?

---

## Por dónde seguir, en orden

1. **T02 — Oferta trazable y publicación consistente** (lo siguiente, y antes que T03 por decisión
   del dueño: corregir identidad sin conservar fechas, procedencia y versiones dejaría comparaciones
   aparentemente exactas pero desactualizadas). Archivos: `schemas.py`, `storage.py`, `pipeline.py`,
   `emparejar.py`, `catalogo.py`, `cifras.py`, `cobertura_diaria.py`. Y en paralelo, preparar reglas
   y pruebas de identidad **sin** regenerar identificadores ni migrar listas.
2. **T01, lo que falta**: DIA y Mercadona (mismo patrón que Carrefour; 2,0 % y 2,4 % fuera), la
   decisión de Aldi (su sitemap no lleva categoría), el informe de peticiones realizadas, y la
   verificación en vivo con la captura de Alcampo.
3. Después, T03 a T10 en el orden del muro.

**Lo que no se puede saltar** (está en el contrato y en las reglas de la casa): cada paquete cierra
con sus pruebas de aceptación pasando, su plantilla rellenada, el muro actualizado y los documentos
en el mismo commit que el código. Y la regla central: **elegir un producto concreto no autoriza
sustituirlo por otro más barato.**

## Bitácora

| fecha | qué se hizo |
|---|---|
| 2026-10-06 | **T01 cerrado de verdad**: banco de verdad con 37 etiquetas (4 falsos descartes a 0 y 0 bazar aceptado), hueco de vocabulario de los plurales corregido, y las cuatro cadenas que saben la categoría antes de pedir dejan de pedir bazar. **Aldi medido y descartado**: 1 petición de 2.536 |
| 2026-10-06 | **Contador de peticiones**: enviadas, de caché y evitadas, contadas donde ocurren; y una prueba que impide que una ejecución de prueba ensucie el recuento del día |
| 2026-10-06 | **T02**: manifiesto de publicación con la huella de la política, las capturas, las huellas de gold y la cobertura declarada |
| 2026-10-06 | **T11 medido**: la ficha ya llega en Carrefour, DIA y Aldi y se tira al parsear; en Alcampo no llega. La primera medición contaba respuestas y su corrección está escrita al lado |
| 2026-10-06 | **T12**: colector de Lidl con cobertura parcial explícita, 11 pruebas sin red y el escribir bronze detrás de una bandera, porque la pasada descubre las cadenas |
| 2026-10-05 | **T01 completo en su parte verificable**: política v2 (frontera del dueño: menaje de un solo uso y bayetas dentro; bombillas, cubos, vasos reutilizables y juguetes de mascota fuera), clasificador con prioridad y palabras enteras, ejecución seca con informe por cadena y rama, y **comprobación de seguridad de comida excluida a cero** |
| 2026-10-05 | **La política, dentro de los colectores**: Alcampo deja de pedir las ramas sin producto de cesta (Hogar y Decoración, la que tumbó su captura) y clasifica el producto antes de bronze; Carrefour no pide sus categorías de bazar |
| 2026-10-05 | **Apagada y vuelta a enganchar**, en ese orden: la comprobación de seguridad encontró 561 alimentos excluidos, se desenganchó hasta arreglarlo, y se volvió a enganchar con el número a cero. Política y comprobación en el mismo commit que el código |
| 2026-10-05 | Cierre parcial de T01 con su plantilla (`docs/CESTA-CIERRE-T01.md`), con lo que falta dicho con nombre y su condición |
| 2026-10-05 | De paso: el aviso de cobertura diaria, el ratchet del barrido de Alcampo (de 7 a 30 días de ventana) y la regla de que una rama excluida no veta una captura incluida |


| fecha | qué se hizo |
|---|---|
| 2026-10-05 | **T01, primera mitad**: politica de alcance, clasificador y ejecucion seca. Tres rondas de medicion (11,8 % -> 9,0 % -> **6,0 % fuera**), con un fallo del emparejador encontrado por el camino (los terminos con guion no casaban). Y la regla "una rama excluida no veta una captura incluida", que es lo que desbloquea Alcampo |
| 2026-10-05 | **T01 en Alcampo**: el colector deja de pedir las ramas sin producto de cesta (Hogar y Decoración, que fue la que tumbó la captura del día). Cuatro pruebas, con las dos cautelas: solo se salta lo excluido y ante la duda se pide |
| 2026-10-05 | informe de ramas: 5 ramas sin un solo producto de cesta, la primera la de Alcampo con sus 133 |
| 2026-10-05 | muro creado; auditoría de ChatGPT verificada en esta máquina (los 6 números y el instrumento, con su prueba) |

| **T11** | Ficha de producto completa e incremental | T02 | ingredientes, alérgenos, nutrientes con su base, pesos, origen y envase, con evidencia por campo | **MEDIDO, NO EXTRAÍDO (2026-10-06)**: `matriz_fichas.py` dice qué llega y qué se tira. Carrefour trae peso neto y origen en el 100 % de las fichas, DIA alérgenos en el 52 %, Aldi bases nutricionales en el 48 %, Alcampo ingredientes en el 0 % de sus 2.582 productos (solo escaparate). Lo que hay que hacer es **dejar de tirarlo**, no pedirlo otra vez |

| **T12** | Lidl con cobertura parcial explícita | T02 | «ofertas conocidas de Lidl», nunca «catálogo completo» | **COLECTOR HECHO, SIN ACTIVAR (2026-10-06)**: `collectors/lidl.py` lee su página pública de ofertas (robots.txt primero, una página), no inventa EAN, no confunde el precio tachado y no finge stock. 11 pruebas sin red. Escribir bronze está detrás de `--escribir` porque la pasada **descubre** las cadenas. La primera captura real, pendiente de hacer a mano |


## Traspaso: qué está hecho, qué está medido y qué falta (6 de octubre de 2026)

### Hecho y probado

| pieza | qué hace | dónde |
|---|---|---|
| Política de alcance v2 | la frontera que fijó el dueño, versionada con el código | `core/datos/alcance.yml`, `core/alcance.py` |
| Banco de verdad | 37 etiquetas humanas, muestra ciega y reproducible; mide falsos descartes y bazar aceptado **por separado** | `projects/cesta/banco_verdad.py`, `docs/banco-verdad/` |
| Contador de peticiones | enviadas, servidas de caché y **evitadas por política**, contadas donde ocurren | `core/peticiones.py`, `projects/cesta/peticiones.py` |
| Manifiesto de publicación (T02) | con qué capturas, con qué reglas y con qué cobertura se publicó | `core/manifiesto.py` |
| Colector de Lidl (T12) | ofertas conocidas, cobertura parcial declarada | `projects/cesta/collectors/lidl.py` |
| Matriz de fichas (T11) | qué campos llegan, qué se extrae y qué se tira | `projects/cesta/matriz_fichas.py` |
| Cuatro cadenas sin bazar | Alcampo, Carrefour, DIA y Mercadona no piden lo excluido | `projects/cesta/collectors/` |

**El catálogo del 6 de octubre de 2026**: 51.659 productos de 5 cadenas → **50.642 entran, 303 salen (0,6 %), 714 a revisar**. Un día antes eran 2.098 en revisión: la diferencia es el hueco de vocabulario (plurales y pasillos) que destapó el banco.

### Medido, y por eso decidido

- **Aldi no se rediseña**: saltarse su bazar ahorra **1 petición de 2.536** (0,0 %). Su problema real son las 230 fichas en revisión, que es clasificación y no peticiones.
- **T11**: la ficha **ya llega** en Carrefour, DIA y Aldi y se tira al parsear; en Alcampo no llega (solo escaparate). La primera medición contaba respuestas y daba una conclusión falsa; contando productos, la conclusión cambia y está escrita con su corrección al lado.
- **Lidl**: la sonda y el colector funcionan sobre la página pública; falta la primera captura real, que hay que hacer **a mano y a la vista**.

### Lo que falta, en orden

1. **T03 · identidad exacta** — es lo que gobierna que las comparaciones sean correctas. Normalizar sin borrar diferencias, candidatos por GTIN y por marca+familia+formato, veto de contradicciones, decisión con evidencia, sin fusiones transitivas, métricas por familia y **publicación en sombra** antes de tocar listas. El laboratorio es diagnóstico.
2. **T11 · extraer lo que ya llega** — empezando por peso neto y origen de Carrefour (100 %) y alérgenos de DIA (52 %), con procedencia y fecha por campo, y sin sustituir un valor bueno por un fallo temporal.
3. **La primera medición real de peticiones** — el contador ya está dentro; la pasada siguiente dirá cuántas ahorra la política, en lugar de suponerlo.
4. **T12 · la primera captura de Lidl** y, solo después, decidir si entra en la tarea diaria.
5. T04 a T10, en el orden del muro.

### Las reglas que no se saltan

Cada paquete cierra con sus pruebas de aceptación pasando, su plantilla rellenada, el muro actualizado y los documentos **en el mismo commit** que el código. La tarea de las 06:00 no se rompe. Se trabaja contra copia. **Elegir un producto concreto no autoriza sustituirlo por otro más barato.** Y lo que no se sabe se dice: ni un cero donde no hay dato, ni una comprobación que aprueba sin mirar.
