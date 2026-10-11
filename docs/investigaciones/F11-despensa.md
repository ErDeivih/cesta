# F11 -- Despensa y aprovechamiento (P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:153`:**

> Investigar R08-R10; **construir version local pequeña, no inventario logistico**. Stock declarado con unidad...
> Sugerir recetas por ingredientes **disponibles, faltantes, fecha conocida y coste parcial**. Descontar exist[encias]...
> **Aceptacion:** **consumo parcial** / **stock desconocido** / **unidades incompatibles** / **fecha ausente**,
> filtros y privac[idad]

**Y los tres criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:108-110`:**

| ID | lo que pide |
|---|---|
| **R08** | *despensa/sobrantes* -- **existencias declaradas**, ubicacion/caducidad **opcional**; **compra no acredita consumo ni stock restante** |
| **R09** | *coste por racion* -- **coste usado distinto de envases por comprar**; cobertura/ambito/version |
| **R10** | *buscar por lo disponible* -- explicar **disponibles/faltantes**, coste y restricciones; **sugerencia, no sustitucion automatica** |

---

## 1. Punto de partida: **nada medido, y una pista que vale mucho**

**De R08-R10 no se ha medido nada** -- *y lo digo antes de empezar.* **Lo que si hay, y es una pista mejor que un
modulo:**

**`core/diario.py:140` ya tiene escrita la regla central de `R08`:**

> *«**Rechaza `compra` a proposito.** **Comprar no es comer**: si una compra entrara aqui...»*

**Y `R08` dice, con otras palabras, exactamente lo mismo**: *«**compra no acredita consumo ni stock
restante**»* -- *comprar algo **no quiere decir** que se haya consumido, ni que quede, ni que no.*

**Es la misma disciplina que atraviesa toda la fase**: *`sin_precio` (un cero afirmaria que salio gratis),
`nombre_visto` (lo que no se sabe se dice), y ahora **una compra no es un consumo**.* **Y ya esta escrita, en
el diario, desde antes.**

### Y lo que NO hay, por lo que se ve

**Una busqueda de «despensa» y «stock» en `core`, `plataforma/api` y la pantalla devuelve ficheros que no son de
esto** -- *`alcance`, `cobertura`, `secciones`, `previa_compra`, `sellos`, `traspaso`* --, **y ninguno se llama
`despensa`.** *Pero **no lo cuento como «no existe» todavia**: eso exige mirarlo en las tres capas, y aqui solo
he mirado una.*

### Y los cuatro casos de la aceptacion, que son los que hay que ejercer

1. **consumo parcial** -- *se gasto parte de lo que habia*
2. **stock desconocido** -- *no se sabe cuanto queda, y hay que poder decirlo*
3. **unidades incompatibles** -- **el mismo problema que el `kg/g` de F10**, *y aqui vuelve*
4. **fecha ausente** -- *un producto sin caducidad conocida*

**Y el tercero es el que mas importa de los cuatro**, porque **ya se midio en F10 y esta fijado con
`xfail`**: *`previa_compra._unidad_canon` no usa `normalize._UNIDADES`, asi que `1 kg` y `500 g` no se suman.*
**Si la despensa descuenta existencias, va a necesitar exactamente la misma conversion** -- *y **la decision que
esta esperando el dueno** (guardar en la unidad que vino o en la canonica) **la necesita tambien este paquete**.*

**Asi que F11 no empieza de cero: empieza con una regla ya escrita (`diario.py:140`), un defecto ya medido
(`kg/g`), y una decision ya planteada -- que resulta que ** no era solo de F10.***

### Y la primera medida, que es un `SELECT`

**¿Existe una tabla de despensa?** *Es lo primero, y contesta `R08` entero: «existencias declaradas» **o no
existen**.* *Y despues, si existe: **¿la compra escribe en ella?*** -- *que es la pregunta de `R08`: «compra no
acredita consumo», **y hay que ver si la compra la toca.**
