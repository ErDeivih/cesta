# Los ficheros muertos de `src/`, *y cómo se cuentan bien* -- 15/10/2026

*Existe porque **he migrado codigo muerto dos veces**: *`Nav.tsx` y `Cabecera.tsx` en la
FASE 3, *y `Inicio.tsx` en la FASE 5.* *Y las dos veces me entere **despues**, *porque
el navegador no cambia.* *

---

## 1. *** El censo, *y el error que hay que no repetir ***

```
*** VIVOS: 79 *** *de 82 ficheros en `src/`.*
*** MUERTOS: 3 *** *
   *** `componentes/Cabecera.tsx` *** *
      *-- *y *** `Nav.tsx` lo es **de rebote** ***: *solo lo importa `Cabecera`, *que
         esta muerto.* *Un censo de **un salto** no lo ve.* ⚠️
   *** `paginas/Inicio.tsx` *** *
   *** `logica/pagina.ts` *** *
      *-- *y **tiene ensayos**: *`pagina.test.mjs`.* *O sea que **se prueba codigo que
         no se usa.*** ⚠️
```

*** Y el censo hay que hacerlo contando las DOS formas de importar. *** *El primer
intento dio **80 muertos de 160** *-- *con `Cesta`, `Buscar`, `ui` y `Suite` dentro, *que
se ven en pantalla --, *y el fallo era **mio**: *

```
*** la app carga las pantallas con *** `lazy(() => import('./paginas/X'))` *** *
*** y **esa forma no lleva `from`** *** ⚠️
   *-- *una expresion que busque solo `from '...'` **no la ve** *
   *-- *y entonces **todo lo que se carga con `lazy` parece muerto** ✓
*** -> *el patron tiene que ser `(?:from|import)\s*\(?\s*['"]…['"]` ✓✓✓
```

## 2. *** Por que esto importa para el rediseno ***

*El plan de la FASE 5 nombra las pantallas **por el nombre del fichero**: *«Inicio,
Listas/Cesta, Buscar, Producto, Recetario, RecetaDetalle, Plan, Diario y Panel».* *
*Y **`Inicio` no se pinta en ningun sitio** *-- *lo que se ve en `/` es el `Lanzador` de
`App.tsx`, *y en `/compra` es `Buscar`.* *

*** Asi que la lista de la FASE 5 se corrige con lo que de verdad tiene ruta: ***

| ruta | componente | estado |
|---|---|---|
| `/` | `Lanzador` *(-- en `App.tsx` --)* | *** hecho *** |
| `/compra` | `Buscar` | pendiente |
| `/compra/listas` | `Cesta` | pendiente |
| `/compra/despensa` | `Despensa` | pendiente |
| `/compra/favoritos` | `Favoritos` | pendiente |
| `/compra/analisis` | `Tendencias` | pendiente |
| `/recetas` | `Recetario` | pendiente |
| `/recetas/plan` | `PlanSemanal` | pendiente |
| `/calorias` | `Diario` | pendiente |
| `/panel` | `Panel` | pendiente |

*Y **`Inicio.tsx` no esta en la tabla** porque **no tiene ruta.** *
*Lo que si se ha hecho en el suyo: *sus **64 clases** de paleta de fabrica, *que
**cuentan para el trinquete igual** *(-- *el trinquete mira el fichero, *no la pantalla --), *
*y por eso el censo bajo de 468 a 426.* *

## 3. *** Y lo que NO se hace con ellos ***

```
*** NO SE BORRAN *** *en esta fase: *borrar un fichero es **una decision de producto**, *
   *y `Cabecera` y `Nav` podrian volver si el layout cambia otra vez.* *
*** PERO QUEDA DICHO ***, *y por eso existe este documento: *para que **la proxima
   ronda no los migre** *creyendo que son pantallas.* ✓
*** Y `logica/pagina.ts` *** *es el mas raro de los tres: *tiene ensayos y **no se usa**.
   *O esta a punto de usarse, *o hay que quitarlo **con su ensayo**.* *
```
