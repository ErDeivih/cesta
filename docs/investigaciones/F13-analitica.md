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
