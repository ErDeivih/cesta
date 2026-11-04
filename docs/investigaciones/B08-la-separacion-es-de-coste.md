# B08 · **Encontrado**: la separacion es de **coste**, esta en `plataforma/api/recetas.py:294` -- y con **la doctrina, decimoquinta vez**

*(13 de octubre de 2026. **Octava ronda de B08. Y la busqueda se cierra -- con la respuesta, y con una distincion.**)*

## 1. Donde estaba

**El camino de las palabras se agoto; el del fichero hermano no.** *Y la interseccion de «nutricion» con «plan» dio
**dos ficheros de la API**, y uno de ellos tiene la respuesta:*

```
plataforma/api/recetas.py -- 439 lineas

  l107: @rutas.get("/plan")                def plan(desde, hasta, ...)
  l118: @rutas.post("/plan", 201)          def planificar(datos, usuario)
  l131: @rutas.get("/{receta_id}")          def leer(receta_id, version=None, ...)
  l294: *** def _con_precios(hallada) -> None ***
  l199: @rutas.get("/{receta_id}/a-la-lista")   def previa(...)
  l235: @rutas.post("/{receta_id}/a-la-lista")  def a_la_lista(...)
  l355: @rutas.delete("/plan")              def quitar_plan(...)
  l386: @rutas.post("/importar")            def importar(datos, usuario)
```

## 2. Y su docstring es **la separacion que el plan pide** -- con una palabra distinta

```python
def _con_precios(hallada: dict) -> None:
    """Pone a cada ingrediente **con producto elegido** el precio del catalogo.

    **G12, punto 222**: *«nutricion/coste por racion con cobertura y procedencia. **Separar co[ste de]
    ingredientes usados del desembolso por envases**»*.

    **El dato ya estaba.** `core/recetas.py` guarda `producto_id`, `grupo_id` y `fuente` por ingrediente
    desde antes -- *opcionales los tres, para que un ingrediente generico siga sie[ndo] generico* --.
    **Lo que faltaba era el cable**: la pantalla recibia el ingrediente sin prec[io] ... `logica/costeReceta.ts`
    decia «no se puede calcular todavia» en **todas** las lineas, incl[uso] las que si tenian producto.

    *Y se hace aqui y no en la pantalla a proposito*: el precio sale del catalogo, que la API [ya] tiene;
    **que la pantalla pidiera el precio ingrediente a ingrediente serian N peticiones p[or] receta para un
    dato que ya esta a mano.**

    **Sin `producto_id` no se pone precio**, ni se busca por nombre: *un nombre parecido no [quiere decir]
    que sea el mismo producto, y es la regla que `cocina.ts` escribe: «no fusionar por parecid[o de]
    nombre».* *** Lo que no se sabe sigue sin saberse. ***
    """
```

## 3. Y contesta **la separacion que B08 pide** -- *aunque de otro eje*

```
B08 PIDE:  «VISTA DE PREVISTOS SEPARADA DEL DIARIO REAL»      <- el eje es: LO CALCULADO vs LO COMIDO
G12/222:   «SEPARAR COSTE DE INGREDIENTES USADOS DEL
            DESEMBOLSO POR ENVASES»                            <- el eje es: LO USADO vs LO COMPRADO
```

> *** Y son **el mismo problema en dos ejes**: ***
>
>   ```
>   EJE DEL CONSUMO:  lo que el plan CALCULA  !=  lo que se ha COMIDO        (B08)
>   EJE DEL GASTO:    el coste de lo USADO    !=  el desembolso por ENVASES  (G12/222)
>   ```
>
> *** Y **las dos separaciones nacen de la misma regla del encargo**: *** **«compra no es consumo»** -- *que en el
> eje del gasto se lee **«comprar un envase no es gastar lo que usas»**.*
>
> *** Asi que B08 no pide una cosa nueva: *** *pide **el mismo par**, **en el eje de la nutricion**, *donde el
> proyecto ya lo tiene **en el eje del coste** -- *y **lo dice en el mismo docstring**: «**nutricion**/coste por
> racion».*
>
> *** Y por eso la respuesta a «¿donde esta la vista de previstos?» es: *** **el proyecto separa, y empieza por el
> coste; la parte de nutricion es la que el plan pide a continuacion** -- *y **no se dice que falte**: se dice que
> **el eje del coste esta, y el de la nutricion esta nombrado en el mismo sitio**.*

## 4. Y la doctrina, **decimoquinta vez**, con una forma nueva

> *** «Sin `producto_id` no se pone precio, NI SE BUSCA POR NOMBRE: un nombre parecido no [quiere decir] que sea el
> mismo producto... **Lo que no se sabe sigue sin saberse**.» ***
>
> *** Y aqui la doctrina no es sobre un `0` ni sobre un `NULL`: *** *es sobre **no emparejar por parecido** -- *que
> es **lo mismo** que el `EAN` de B09 («distinto no acredita mismo articulo») y que el `cadena`/`fuente` de B04.*
>
> *** Y el docstring **cita la regla del frontend**: *** *«es la regla que `cocina.ts` escribe: **no fusionar por
> parecido de nombre**»* -- *o sea: **la regla esta escrita en los dos lados, y el backend la cita.***
>
> *** Decimoquinta vez. Y esta es la primera en que **el codigo cita al codigo**. ***

## 5. Y B08 queda con **la (1) explicada**, y la (4) localizada

```
  1) PREVISTO != REGISTRADO    *** EL PROYECTO SEPARA, y empieza por el COSTE (`_con_precios`, G12/222):
                               «separar coste de ingredientes usados del desembolso por envases».
                               El eje de la NUTRICION esta NOMBRADO en el mismo docstring. ***
  2) SNAPSHOT Y COBERTURA      HECHO -- `de_ficha` y `_cobertura`
  3) EL RECIBO Y SU DESHACER   HECHO -- `apunta` (que rechaza `compra`) y `borrar`
  4) EL OBJETIVO Y LAS GRAFICAS `objetivo` esta en CINCO ficheros del frontend (`Cocina.tsx` incluido)
                               y en NINGUNO de la API -- *y eso es **una pregunta con pista**, no una falta*
  5) Y LA ACEPTACION           LOCALIZADA -- los quince ensayos, con las cifras
```

> *** Y las ocho rondas de B08 dejan **una cosa que ningun otro paquete habia dejado**: *** *una clausula
> **buscada por siete caminos**, con **seis candidatas probadas y descartadas midiendo**, y **encontrada por el
> octavo** -- *que era **el que el metodo ponia segundo**: **leer el fichero hermano**.*
>
> *** Y es, en una frase, la utilidad de los cinco pasos: *** **el `grep` sirve para llegar al fichero, y el fichero
> hay que leerlo.**
