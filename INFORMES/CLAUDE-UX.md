# Revisión UX de la demo de Avío a 390×844 (16/11/2026)

**Qué es este documento.** La revisión de usabilidad que se pidió a **Claude** y a **Codex** sobre
la demo de Avío, y lo que se ha aplicado de ella. No es una lista de deseos: cada cambio aplicado
está en el código y verificado en la demo publicada.

**Cómo se pidió.** Dos revisiones independientes, sin acceso a editar nada:

- **Claude Code 2.1.302**, en modo plan y solo lectura, con la captura de la entrada y el código
  de `plataforma/web/app/src`. Revisó además las capturas de `capturas/` (lista llena, fila
  desplegada, buscador, comparar, vacío y error).
- **Codex CLI 0.165.0**, en sandbox de solo lectura, con la captura de la entrada adjunta y el
  mismo código.

**Material principal:** `capturas/avio-completa-390x844.png` y el código de las pantallas
`Buscar`, `Cesta`, `TablaResultados`, `OfertasDelProducto`, `Typeahead` y `Suite`.

## Lo que coincidieron los dos

1. **Demasiado cromo antes del primer producto.** El nombre de la lista se repite, el precio
   ocupa una tarjeta de ~132 px y las acciones de renombrar/quitar tienen su propia línea. En la
   captura, el primer producto empezaba hacia el píxel 630–640 y solo se veía uno y medio.
2. **El precio y la cantidad de la fila no se entendían solos.** «2 × en Carrefour» y «1,88 €»
   no decían si 1,88 € era la unidad o el total.
3. **La fila era demasiado alta y la casilla demasiado pequeña.** El `⋯` en una línea aparte
   sumaba altura; la casilla visible medía 22 px.

## Claude: los tres cambios que consideró urgentes

1. **La pantalla «Comparar» se contradecía** en las capturas revisadas: un ahorro grande
   («10,57 € · −48 %») convivía con «ninguna cadena tiene los productos confirmados» y con
   totales a cero. Su propuesta: si no hay precios confirmados, no enseñar la cifra grande y
   poner un estado que lleve a confirmarlos; cuando haya datos, una sola cifra y una línea de
   dónde sale.
2. **Subir la lista y fijar el total abajo.** Un solo título-selector («La semana ▾»), las
   acciones de nombre en el menú `⋯`, y el total como barra fija encima de la barra de pestañas.
3. **Separar «Quitar» del «+»** en el menú desplegado: a 8 px es fácil borrar sin querer con una
   mano en el pasillo.

Además señaló: dos sistemas de navegación (☰ y barra inferior), casillas de 22 px, filas de
~115 px, «PVP» como jerga, «Lo de siempre» como orden ambiguo, la acción principal del buscador
poco visible en su captura, textos de error repetidos y el vacío con la misma frase dos veces.

## Codex: los tres cambios que consideró urgentes

1. **Recuperar espacio para la compra.** Un único selector como cabecera y
   «Cambiar el nombre»/«Quitar la lista» dentro de un menú; «Lista nueva» dentro del selector.
2. **Compactar el precio** a una franja («Estimado · 17,06 €»), con la letra pequeña accesible al
   desplegar; el total debe verse sin ser el bloque principal.
3. **Aclarar qué representa cada precio**: «2 × 0,94 €» y «1,88 €» como subtotal, separando
   cantidad, precio y supermercado.

Su criterio concreto de aceptación: **ver al menos tres productos completos, el total y el acceso
a añadir en la misma pantalla**.

## Lo que se ha aplicado

| Cambio | Antes | Después |
|---|---|---|
| Antetítulo «Avío · Compra · de casa» | Visible, repetía la cabecera | Solo para lector de pantalla (`sr-only`) |
| Precio estimado | Tarjeta de ~132 px | Franja de ~70 px: cifra grande a la izquierda, productos/fecha a la derecha |
| «Cambiar el nombre» y «Quitar la lista» | Línea fija encima de los productos | Dentro del menú `⋯` junto al selector de lista |
| Fila de producto | Nombre + precio, y debajo otra línea con `⋯` | Nombre, precio y `⋯` en la misma línea; debajo, cantidad · precio unitario · cadena |
| Cantidad y precio | «2 × en Carrefour» + «1,88 €» | «2 × 0,94 € · en Carrefour» + «1,88 €» de subtotal |
| Casilla | 22 px | 24 px visibles, con la fila-label de 44 px como zona táctil |
| Cabecera del buscador | «PVP» | «Precio» |
| Orden por defecto | «Lo de siempre» | «Relevancia» |
| Vacío de la lista | La frase «se crea sola» salía dos veces | Una sola vez, en la ayuda del typeahead |

**Resultado medido a 390×844:** el primer producto sube de ~630 px a ~430 px y pasan de **2 a 4
filas visibles** en el primer pantallazo (**3 completas y la cuarta asomando**), con el total y el
buscador aún a la vista. El criterio de Codex (tres productos completos + total + añadir) se
cumple. Captura final de la demo publicada: `capturas/avio-final-390x844.png`.

**Lo que ya estaba y la captura de Claude no reflejaba:** el botón **«Añadir»** en cada resultado
del buscador se había añadido en el commit `9c8b9c2`; la captura del buscador que revisó Claude era
anterior. El flujo publicado de buscar → añadir → comparar → lista está probado y pasa.

## Lo que no se ha aplicado, y por qué

- **Quitar la barra inferior o el menú ☰.** Es una decisión de producto ya tomada (la barra es la
  navegación principal en móvil). Se ha reducido la ambigüedad de la cabecera, pero no se ha
  eliminado ninguna de las dos.
- **Estado «Comparar» con aviso bloqueante.** Se ha comprobado la pantalla con la muestra actual:
  cuando solo una cadena tiene la lista entera, el ahorro sale «—» y cada total dice qué le falta;
  no se ha visto la contradicción de las capturas antiguas. Queda pendiente revisarlo con listas
  confirmadas y no confirmadas mezcladas.
- **Filtros con chips siempre visibles.** Los chips ya aparecen cuando hay filtros puestos; el
  texto «cadena, pasillo, dieta, ofertas…» describe lo disponible. Cambiarlo a «Filtros (2)» es
  una iteración aparte.
- **Estado de error con texto neutro y sin repetir el título.** Pendiente.
- **Imágenes de reserva y nombres a dos líneas en «Lo de siempre».** Pendiente.
- **Deslizar para borrar.** Pendiente; ahora borrar está dentro del `⋯`, que ya lo aleja del «+».

## Verificación

- `tsc --noEmit`: limpio.
- `npm test`: **404/404**.
- `vitest run`: **361/361**.
- Captura después de los cambios: `capturas/avio-ux-390x844.png` y, ya publicada,
  `capturas/avio-final-390x844.png`.
- Commit de los cambios de UX: `982e8e6`.

**Cómo se reprodujo la revisión** (por si hay que repetirla):

```bash
claude -p "$(cat .tmp-demo/prompt-claude.txt)" --permission-mode plan \
  --allowedTools "Read" --output-format text

codex exec -s read-only -i capturas/avio-completa-390x844.png \
  -o .tmp-demo/codex-ux.txt "$(cat .tmp-demo/prompt-codex.txt)"
```
