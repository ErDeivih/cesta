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


---

## 2. `R04`: **el escalado esta hecho y no suma nada** -- y la suma esta en F10

*(Ronda 116.)* El `SELECT` sobre `core/recetas.py`, que era lo primero que habia que mirar.

### El escalado, entero, en veinte lineas

```python
134  def escala(ingredientes: list[dict], de_raciones: int, a_raciones: int) -> list[dict]:
135      """Los ingredientes para `a_raciones` en vez de para `de_raciones`.
137      **Lo que no tiene cantidad, no la gana.** Un ingrediente anotado como "sal" sigue sin cantidad: la
138      regla de tres no se puede aplicar a lo que no se sabe, e inventarle un cero seria convertir un dato
139      que falta en un dato falso.
141      Se redondea a dos decimales, y sin miedo: media unidad de huevo es raro de leer pero es la verdad.
142      Redondear a 2 seria comodo y mentira; quien cocina decide, con el numero delante.
143      """
144      if de_raciones < 1 or a_raciones < 1:
145          raise ValueError("las raciones son al menos una")
146      factor = a_raciones / de_raciones
148      for uno in ingredientes:
150          cantidad = copia.get("cantidad")
151          if isinstance(cantidad, (int, float)):
152              copia["cantidad"] = round(cantidad * factor, 2)
```

**Las dos mitades del criterio, una por una:**

| lo que pide `R04` | **estado** |
|---|---|
| **«escalado reproducible»** | **si**: *una multiplicacion por el factor, redondeada a dos decimales -- **determinista**, y sin depender de nada mas* |
| **«lo que no tiene cantidad, no la gana»** | **si, y dicho**: *la sal sigue sin cantidad, porque **inventarle un cero seria convertir un dato que falta en un dato falso*** |
| **«g/ml/ud no sumados por apariencia»** | **aqui se cumple por no haber suma** -- *ver abajo* |

### Y el hallazgo que importa: **`escala` no suma, multiplica**

**«No sumados por apariencia» presupone que hay una suma.** *Y en `escala` **no la hay**: recorre los
ingredientes **de uno en uno** y multiplica cada cantidad por el factor.* **Asi que no puede sumar g con ml
porque no suma nada con nada.**

**La suma aparece **en otro sitio**: cuando el plan semanal se convierte en lista de la compra** -- *«Plan→lista:
seleccionar lo necesario, **consolidar compatibles** y mantener trazabilidad ingrediente-receta»*, que es
**F10** (`SUPERAPP-FASE2-EMPEZAR-AQUI.md:149`).*

> **Ahi es donde 100 g de harina de una receta y 200 g de harina de otra tienen que ser 300 g** -- *y donde
> 100 ml de leche y 100 g de mantequilla **no pueden ser 200 de nada**.*

**Asi que `R04` queda medido -- el escalado esta y esta bien --, y **la mitad que da miedo no es de este
paquete**: es de F10, y conviene decirlo para no darla por buena desde aqui.** *Es la misma trampa que F08 me
enseno a evitar: **la pieza existe en un sitio y el criterio se cumple en otro.***

### Y `R03` empieza a aparecer solo, y es fuerte

**El docstring del modulo, en sus tres primeras lineas:**

```
:3    **Privacidad, implementada.** Cada receta tiene propietario, y **todas** las operaciones lo exig[en]...
:11   **Lo historico, sin dueno, queda conservado e inaccesible.** La migracion anade la columna y dej[a]...
:15   **Cada version es autocontenida**: guarda sus raciones, su preparacion y sus ingredientes **copi[ados]**...
```

**Y las tres son `R03` y el aislamiento de la aceptacion:**

| lo que dice el modulo | **que criterio toca** |
|---|---|
| **«Privacidad, implementada. Cada receta tiene propietario, y todas las operaciones lo exigen»** | **`R03`/aislamiento** -- *el septimo caso de la aceptacion* |
| **«Lo historico, sin dueno, queda conservado e inaccesible»** | *una decision de migracion: **no se borra y no se ve*** |
| **«Cada version es autocontenida: guarda sus raciones, su preparacion y sus ingredientes copiados»** | **`R03`: «version persistente»** -- *una version no cambia porque cambie la receta* |

**Y hay funciones que lo dicen en su nombre**: `versiones()`, `actualizar()`, `archivar()`, y **`_de_quien(con,
propietario, receta_id)`** -- *que es el guardian de `R03`, y es una funcion de tres argumentos que **devuelve
`None` si no es tuya**.*

**Asi que `R03` tiene modulo, docstring y guardian.** *Falta **medirlo** -- el aislamiento de verdad, con dos
propietarios --, que es exactamente la prueba que F07 ya hizo para las listas (`test_fase2_f07_otro_hogar.py`) y
que aqui se puede copiar entera.*
