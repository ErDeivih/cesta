# F09 -- Recetario completo y recuperacion de borradores (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:137`:**

> Investigar R01-R04 con Paprika/Samsung Food. Busqueda y filtros utiles, favoritos/colecciones, editor, v[ersiones]...
> Raciones y cantidades reproducibles; **unidades incompatibles sin conversiones inventadas**. Recetas gener[icas]...
> **Aceptacion:** normal/error/**URL invalida**/**duplicado**/**borrador**/**versiones**/**aislamiento**; recetas de fixture p[ara pruebas]

**Y los cuatro criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:101-104`:**

| ID | lo que pide |
|---|---|
| **R01** | *biblioteca/filtros* -- recetas propias, etiquetas, favoritos, busqueda y **vacio con filtros explicados** |
| **R02** | *importar receta* -- **URL/archivo de fuente permitida**; previa, **fuente, unidades y edicion antes de guardar** |
| **R03** | *editor/versiones* -- **borrador recuperable y version persistente**; diario antiguo permanece estable |
| **R04** | *raciones/unidades* -- **escalado reproducible**; **g/ml/ud no sumados por apariencia** |

---

## 1. Punto de partida: lo que hay, y lo que **no** se ha medido

**De R01-R04 no se ha medido nada en esta fase** -- *y lo digo antes de empezar, porque en esta fase he dado por
hecho lo contrario ocho veces.* **Lo que si se ha visto de pasada, y conviene anotar sin confundirlo con una
medicion:**

- **`core/recetas.py` existe**, y `plataforma/api/recetas.py` tiene una ruta base -- *`recetas.ruta_base()`, que
  aparece en `diario.py:78` al comprobar que una receta anotada existe de verdad.*
- **El diario comprueba la receta antes de guardarla** -- *`diario.py:75-94`: «la receta se comprueba ANTES de
  guardarla. Una version que no existe, o de otra persona, no se anota»* --, **y eso es `R03` visto desde el
  diario: la version importa**.
- **`cocina.ts:36` prohibe algo** -- *lo nombra `RecetaDetalle.tsx:228`: «identidad de G10*, y `cocina.ts:36`
  prohibe...»* -- *sin leer.*

**Asi que hay modulo, hay ruta base, y hay una comprobacion de version ya usada por el diario.** *Nada de eso es
una medicion de R01-R04: es **saber donde mirar**.*

### Y los siete casos de la aceptacion, que son lo que hay que probar

**La aceptacion no pide funciones: pide **siete casos**, y son los que hay que ejercer:**

1. **normal** -- *el camino que funciona*
2. **error** -- *algo que sale mal y se dice*
3. **URL invalida** -- *importar de una direccion que no vale*
4. **duplicado** -- *la misma receta dos veces*
5. **borrador** -- *lo que se empieza y no se termina*
6. **versiones** -- *editar una receta y que lo viejo siga*
7. **aislamiento** -- *que una receta de otra persona no se vea ni se pueda anotar*

**Y hay una octava linea que dice algo mas de lo que parece**: *«recetas de **fixture** para pruebas»*. *Es
decir: **la aceptacion pide que las pruebas no dependan de recetas de verdad de nadie** -- *que es la misma
regla que el encargo pone al principio, «preserva datos reales», y que en esta fase ha costado un incidente
(F03, ronda 50).*

### Y `R04` es el criterio que mas me interesa de los cuatro

**«Escalado reproducible; **g/ml/ud no sumados por apariencia**.»**

*«No sumados por apariencia» es una frase muy concreta: **100 g de harina y 100 ml de leche no son 200 de
nada**.* **Y es el mismo problema que F01 y F08 ya trataron con los formatos** -- *`parse_formato` normaliza
packs, unidades y pesos a una cantidad canonica* --, **pero al reves**: *alli habia que convertir para comparar
precios; **aqui hay que negarse a convertir cuando no se puede**.*

**Asi que `R04` se mide con la misma pregunta que F08**: *¿hay una funcion que decida si dos unidades se pueden
sumar, **y que se niegue cuando no**?* *Y en F08 la respuesta fue que **si**, con `_UNIDADES` y un factor
explicito. **Aqui hay que ver si la receta usa la misma** -- *o si suma por apariencia.*

**Es un `SELECT` sobre `core/recetas.py` y `core/normalize.py`, y va antes que cualquier pantalla.**
