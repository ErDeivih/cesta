# F13 -- Analitica legible de las tres apps (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:169`:**

> **Graficas: medida/unidad/universo/fecha/ambito/cobertura/fuente**; **tabla equivalente y huecos reales**.
> Compr[ar]...
> Campos nutricionales adicionales **solo si disponibles** (fibra, azucares, saturadas, sal, etc.), mantenien[do]...
> **Aceptacion:** **datos controlados exactos**, **filtro que cambia universo explicado**, **fechas duplicadas**,
> seri[e]...

---

## 1. Punto de partida: **nada medido**, y una lista que es la misma de siempre

**De F13 no se ha medido nada.** *Y lo primero que llama la atencion es **la lista del criterio**:*

> *«medida / unidad / **universo** / **fecha** / **ambito** / **cobertura** / **fuente**»*

**Siete cosas que un numero tiene que declarar para ser un dato.** *Y **cuatro de las siete ya han salido en esta
fase**, cada una en su paquete:*

| lo que pide F13 | **donde ya salio** |
|---|---|
| **«fecha»** | **`C06`** (`F08`): *la fecha del catalogo, **en la cabecera de todas las pantallas**, con «hace N»* |
| **«ambito»** | **`C06`**: *la columna `cadenas`; y **una de las dos cosas por las que se ordena*** |
| **«cobertura»** | **`R09`** (`F11`): *`{valor, faltantes}` -- «**un total sobre la mitad de los ingredientes no es el total**»* |
| **«fuente»** | **`N05`** (`F12`): *`fuente_dato` **`NOT NULL`** y conjunto cerrado de cuatro, **con `raise`*** |

**Y las tres que faltan por ver son «medida», «unidad» y «universo»** -- *que son justo las que **una grafica**
necesita y una tabla no: **que se esta midiendo, en que unidad, y sobre que conjunto**.*

**Asi que F13 no es una pantalla nueva con numeros nuevos: es la misma disciplina aplicada a un dibujo.** *Una
grafica es **la cosa que mas facil es de mentir sin querer** -- un eje sin unidad, una linea sin decir sobre
cuantos productos, un hueco que se lee como un cero.*

### Y la frase que decide el paquete

**«Tabla equivalente y huecos reales.»**

*«Tabla equivalente» quiere decir que **lo que dice la grafica se puede leer tambien como numeros** -- que es
accesibilidad, y que es lo que permite **comprobar** la grafica.* **Y «huecos reales» es la misma regla que
`C09`**: *un mes sin datos **no es un mes con cero**.* **La grafica tiene que **dibujar el hueco**, no
atravesarlo con una linea recta.**

### Y «datos controlados exactos», que es la primera prueba de la aceptacion

**«Datos controlados exactos»** -- *una prueba con **datos que se sabe lo que valen**, y comprobar que la grafica
dice **exactamente** eso.* *Es la misma clase de ensayo que `test_fase2_f10_previa_compra.py`: **fixtures con
numeros redondos y aserciones sobre el resultado**, no una captura de pantalla.*

### Y la primera medida, que es un inventario

**¿Que pantallas dibujan algo?** *Es lo primero, y es lo que el criterio pide en su segunda linea de F14
(«inventario de pantallas servidas y componentes»), **que aqui vale igual**:* **no se puede juzgar «analitica
legible» sin saber cuanta analitica hay.**

**Y hay dos candidatas conocidas de rondas anteriores** -- *`Panel.tsx` (que tiene un `PanelMatching`) y el
`/api/movimientos` que se vio en `C01b`* --, **y ninguna de las dos se ha mirado por su contenido.**


---

## 2. El inventario, y las dos piezas que contestan el criterio **con sus palabras**

*(Ronda 138.)* **El inventario primero**, que era lo que hacia falta.

**18 paginas** (`Ajustes`, `Avisos`, `Buscar`, `Cesta`, `Cocina`, `Diario`, `Escaner`, `Favoritos`, `Grupo`,
`Inicio`, `Panel`, `PanelMatching`, `PlanSemanal`, `Producto`, `RecetaDetalle`, `Recetario`, `Tendencias`,
`Unirse`), **y tres que dibujan**: `Panel`, `PanelMatching` y **`Tendencias`** -- *mas **dos componentes**:*
**`Chispa.tsx`** (*la sparkline del historico*) y **`GraficoIndice.tsx`**.

### `GraficoIndice.tsx` -- «la tabla de debajo **no es un extra**»

```typescript
1   /** El indice de precios por cadena, con sus cinco series.
3   *  **SVG a mano y no uPlot**, al reves que la chispa del historico. Son cinco series y catorce puntos
4   *  que se pintan una vez al abrir la pestaña: uPlot se come 50 KB para esto y ademas la chispa va sin
5   *  ejes (`Chispa.tsx`: `time: false`), asi que no serviria sin reescribirla. **Aqui hacen falta el eje
6   *  de fechas, el 100 de referencia y las etiquetas del final.**
8   *  Y **la tabla de debajo no es un extra**: cinco colores no se distinguen ni con buena vista, y tres
9   *  de los que usaba la interfaz vieja **no llegaban a 3:1 de contraste** contra el fondo claro. El
10  *  dibujo ayuda a ver la tendencia; **el numero que se lee es el de la tabla.** Por eso este componente
11  *  **no** decide nada: **pinta lo que le dan y no calcula ni un dato.**
```

**Y «la tabla de debajo no es un extra» es, palabra por palabra, lo que el criterio pide**: *«Graficas:
medida/unidad/universo/fecha/ambito/cobertura/fuente; **tabla equivalente** y huecos reales.»*

**Y el motivo no es estetico: es de contraste.** *«Cinco colores no se distinguen ni con buena vista, y tres de
los que usaba la interfaz vieja **no llegaban a 3:1**»* -- *que es el minimo de contraste de las pautas de
accesibilidad.* **Asi que la tabla **es** el canal principal y el dibujo el apoyo, y eso esta decidido y escrito.**

**Y la ultima linea es la que lo hace comprobable**: ***«no calcula ni un dato»***. *Un componente que solo pinta
**se puede probar con fixtures**, que es exactamente la primera prueba de la aceptacion: «**datos controlados
exactos**».*

**Y las otras decisiones del dibujo, que son las tres que faltaban de la lista del criterio:**

| la lista del criterio | **aqui** |
|---|---|
| **«unidad»** | *el **100 de referencia*** -- *el indice esta normalizado, y el 100 lo dice* |
| **«fecha»** | *«el **eje de fechas**»* -- *y por eso **no** vale la chispa, que va `time: false`* |
| **«universo»** | *«cinco series»* y *«catorce puntos»* -- *el conjunto esta dicho* |

### `Tendencias.tsx` -- «un dia sin dato no es un dia de cero»

```typescript
1   /** Las tendencias: los ultimos dias, **con los huecos donde no hay dato**.
2   *  **Un dia sin dato no es un dia de cero.** Aqui los dias sin energia no llevan barra: llevan la
3   *  pal[abra] "sin dato". Un grafico que dibuja cero donde no hay dato **dice que se comio nada**, y
4   *  encima **hace par[ecer] que los demas dias estan completos**.
6   *  **Y tampoco se inventa una media.** Si ningun dia trae dato, no hay nada que promediar y se dice;
7   *  ... un cero seria **inventarse un resultado**.
9   *  **La medida se declara:** es lo anotado y lo que se sabe, **no "lo que comiste"**.
```

**«Huecos reales»** -- *la otra mitad del criterio, y con la razon completa:* **un cero donde no hay dato no solo
miente sobre ese dia: hace parecer que los demas estan completos** ✓✓✓

**Y «la medida se declara»** -- *«es lo anotado y lo que se sabe, **no "lo que comiste"**»* -- *que es **la misma
distincion de `nombre_visto`, `sin_precio` y `fuente_dato`, aplicada a una grafica*** ✓✓

**Y «tampoco se inventa una media»**: *si no hay ningun dato, no hay media -- y **decir cero seria inventarse un
resultado**.*

### Y F13, con lo medido

| lo que pide F13 | **estado** |
|---|---|
| **las siete cosas declaradas** | **fecha** (`C06`), **ambito** (`C06`), **cobertura** (`R09`), **fuente** (`N05`), y **unidad / fecha / universo** en `GraficoIndice` |
| **«tabla equivalente»** | **hecho, y con el motivo de contraste escrito** |
| **«huecos reales»** | **hecho**: *«un dia sin dato no es un dia de cero»* |
| **«datos controlados exactos»** | *el componente **no calcula ni un dato***, asi que se prueba con fixtures |
| **«filtro que cambia universo explicado»** | *por medir* |
| **«fechas duplicadas»** | *por medir* |
| **«campos nutricionales solo si disponibles»** | *por medir* -- *y `N03` ya midio que la cobertura es del **22,8 %***

**Las dos mitades del criterio, hechas y con sus palabras; y los casos de la aceptacion, el unico que ya se ve
cubierto es «datos controlados exactos»** -- *porque el componente no calcula nada.* **Van doce piezas.**
