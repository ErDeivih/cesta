# F14 -- Sistema visual propio aplicado (P1/P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:177`:**

> **Hacer inventario de pantallas servidas y componentes, no rediseñar solo una portada.** Adoptar la direccion...
> **Crear antes/despues con mismos fixtures.** Simplificar jerarquia, numeros/unidades, textos y estados; dens[idad]...
> **Aceptacion:** **360/390/768/1440**, **zoom 200 %**, **teclado/cajon/foco**, **reduccion de movimiento**,
> **contraste y c[olor]**...

---

## 1. Punto de partida: **nada medido**, y el inventario ya esta hecho por F13

**De F14 no se ha medido nada** -- *pero **la primera cosa que pide ya esta contada**, porque F13 la necesitaba:*

> *«**Hacer inventario de pantallas servidas y componentes, no rediseñar solo una portada.**»*

**Y el inventario existe** (ronda 138): **18 paginas** -- `Ajustes`, `Avisos`, `Buscar`, `Cesta`, `Cocina`,
`Diario`, `Escaner`, `Favoritos`, `Grupo`, `Inicio`, `Panel`, `PanelMatching`, `PlanSemanal`, `Producto`,
`RecetaDetalle`, `Recetario`, `Tendencias`, `Unirse` -- **y sus componentes**.

**Y el criterio dice «no rediseñar solo una portada», que es una advertencia sobre el trabajo, no sobre el
resultado**: *es facil hacer bonita `Inicio` y dejar `Ajustes` como estaba.* **Tener las 18 contadas es lo que
permite comprobar que se aplico a todas** -- *y es **la razon de que el encargo pida «inventario» antes de
«direccion»**.*

### Y la aceptacion es **accesibilidad**, entera

**Los cinco casos, y los cinco son de accesibilidad:**

| caso | **que es** |
|---|---|
| **360 / 390 / 768 / 1440** | *las cuatro anchuras: movil pequeno, movil, tableta, escritorio* |
| **zoom 200 %** | *y a 200 % **no se puede perder nada** -- es el criterio de reflow* |
| **teclado / cajon / foco** | *navegar sin raton, y **saber donde estas*** |
| **reduccion de movimiento** | *respetar `prefers-reduced-motion`* |
| **contraste y color** | *el minimo, y **no depender solo del color*** |

**Y ninguna de las cinco se puede comprobar leyendo el codigo**: *todas son **de pantalla**, y tres de ellas
**necesitan un navegador de verdad** (`zoom`, `foco`, `movimiento`).* **Es el paquete mas «de pantalla» de la
fase hasta ahora.**

### Y ya hay **dos** datos de contraste en esta fase, sin buscarlos

**El criterio de F13 trajo uno, y es del propio proyecto:**

> *«Y **la tabla de debajo no es un extra**: cinco colores no se distinguen ni con buena vista, y **tres de los
> que usaba la interfaz vieja no llegaban a 3:1 de contraste contra el fondo claro**.»* (`GraficoIndice.tsx:8-9`)

**Asi que el proyecto **ya encontro** un fallo de contraste, **ya lo escribio**, y **ya lo arreglo poniendo una
tabla** -- *lo cual es exactamente el criterio «no depender solo del color», resuelto **en un sitio**.*

**Y la pregunta de F14 empieza por ahi, y es concreta**: *¿se arreglo **en ese sitio**, o **hay una regla**?* *Es
decir: **¿hay una paleta con sus contrastes comprobados, o cada componente se arregla cuando alguien lo mira?***

**Eso es un `SELECT` sobre `estilos.css` y los tokens.** *Y va antes que cualquier captura de pantalla, porque
si **hay** una paleta con sus minimos, la mitad del criterio ya esta; y si no, **el trabajo es otro**.*

### Y una nota de metodo que este paquete exige

**Los cuatro casos de anchura y el zoom no se pueden medir «leyendo».** *En `F03` y `F07` hicieron falta
`prueba_f03_publicacion.py` y `prueba_f07_pasos.py`, con `patchright` y **navegador de verdad** -- y **`F14`
necesita lo mismo**, mas capturas a cuatro anchuras y a 200 %.*

**Y el criterio pide «antes/despues con **mismos fixtures**»** -- *o sea, que las capturas se puedan comparar.*
*Eso es `compare_web_screenshots` del laboratorio auxiliar, o el mismo `navegador.py` con dos juegos de tokens.*
**Es trabajo de ensayo, no de lectura.**
