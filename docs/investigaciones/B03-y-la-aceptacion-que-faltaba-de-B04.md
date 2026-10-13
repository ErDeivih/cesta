# B03 · Lidl — el criterio del plan, tal cual. Y **la aceptación de B04 que no complete**

*(13 de octubre de 2026. **Esto no es trabajo hecho: es el plan leido y una correccion que me debo.**)*

## 1. **B04 NO esta cerrado**, y lo digo yo

*En la ronda anterior escribi «con esto, B04 queda cerrado».* **Y al leer el plan entero, su aceptacion pide
mas de lo que probe** -- *textualmente:*

> *«Aceptacion: escenario de cinco recetas, **DOS LISTAS, DOS MARCAS** y plan de otra semana;
> **preview=confirmacion=persistencia**, **cambios/versiones y reintentos incluidos**.»*

**Lo que hay probado** (17 comprobaciones, todas OK): *cinco recetas, escalado, consolidacion, despensa,
envases, ingrediente sin destino, destino elegido, idempotencia y persistencia con cliente nuevo.*

**Lo que NO:**

  - **DOS LISTAS.** *Se uso una para el plan y otra para la despensa, pero **no se probo el mismo plan
    traido a dos listas distintas** -- que es lo que comprueba que el destino es una eleccion y no un
    descuido.*
  - **DOS MARCAS.** *Todos los ingredientes van con `grupo_id`, y **ninguno con `producto_id` de marca**.*
    *La consolidacion por identidad cuando hay producto exacto no se ha ejercitado.*
  - **PLAN DE OTRA SEMANA.** *Todas las fechas son del 19 al 25 de octubre.* **«Repetir no duplica; otra
    semana/operacion legitima si»** es la frase que `traspaso` cita, **y la segunda mitad no se ha probado
    en el puente del plan.**
  - **CAMBIOS Y VERSIONES.** *Una receta editada despues de planificarse: el plan guarda la version del dia
    que se puso, y eso no se ha ejercitado.*
  - **REINTENTOS.** *Una caida a mitad y volver a llamar.*

> **Y la leccion es de metodo, no de codigo**: *lei el plan cuando empece B04 para saber que habia que
> arreglar, y **no volvi a leer su aceptacion cuando lo declare cerrado**.* **«Un documento se lee como un
> relato y se comprueba como un inventario»** -- *y la aceptacion es el inventario.*

## 2. B03, el criterio del plan **tal cual**

*Copiado del plan, sin resumir, porque resumirlo es como se pierden los criterios:*

> **B03 · Lidl como sexta fuente diaria y candidatos por articulo**
>
> Leer `collectors/lidl.py`, `descubrir_lidl.py`, `fichas_lidl.py`, `ficha_lidl.py`, `sondear_lidl.py`,
> `run.py` y `docs/LIDL.md`. **Adaptador explicito de CLI/config; validar tienda/region y no convertir CP en
> id de region sin correspondencia.** Usar preferencia existente si acredita ambito; si no, **capturar
> descubrimiento sin inventar precios regionales** y pedir SOLO ese dato al propietario cuando sea
> necesario. **Reconciliar productos de campana con productos descubiertos, no confundir IAN con EAN ni
> promocion semanal con catalogo total.** Entrada diaria con cobertura por campo. **Eliminar veto global a
> precios validos de Lidl**: permitir candidatos observados, vigentes y de identidad acreditada, y **marcar
> los no observados como desconocidos**. **Lidl no gana una cesta completa si faltan lineas; si puede
> ofrecer una linea exacta con precio valido o una alternativa que la persona acepte.**
>
> **Aceptacion**: ejecucion desde el mismo runner diario, **bronze -> silver -> gold -> API -> UI**;
> **region/club/fechas/nutricion/ausencias probadas**, captura acotada y contador visible.

### Y las cuatro frases que deciden el diseno

  1. **«no convertir CP en id de region sin correspondencia»** -- *un codigo postal no es una region: la
     correspondencia hay que acreditarla, no suponerla.* **Es la misma regla del `0.0.0.0` y del `de_dondo`:
     lo que no consta no se rellena.**
  2. **«no confundir IAN con EAN»** -- *el IAN es el identificador interno de Lidl; el EAN es el del
     fabricante.* **Tomar uno por otro daria por emparejados dos productos que no lo estan.**
  3. **«promocion semanal no es catalogo total»** -- *es la razon por la que `CADENAS` y
     `CADENAS_QUE_SE_CAPTURAN` son listas distintas desde A05.* **Lidl publica ofertas parciales, y
     presentar eso como catalogo haria parecer que no tiene el resto.**
  4. **«marcar los no observados como desconocidos»** -- **no como ausentes.** *No haberlo visto no es que no
     exista*, que es la distincion de toda la fase.

## 3. Lo que hay que leer antes de tocar B03

*El propio plan lo dice, y son siete ficheros:*

```
collectors/lidl.py      descubrir_lidl.py      fichas_lidl.py      ficha_lidl.py
sondear_lidl.py         run.py                 docs/LIDL.md
```

**Y ninguno se ha leido todavia.** *Asi que B03 empieza por leer, no por escribir* -- *que es lo que este
encargo lleva quince rondas demostrando que hay que hacer primero.*
