# B09 · **El «completo» del titulo no es una carencia: es una NEGATIVA RAZONADA** -- y con una discrepancia medida

*(13 de octubre de 2026. **Segunda ronda de B09. Y el fichero contesta la palabra que preocupaba.**)*

## 1. Lo que hay: 164 lineas

```
core/oraculo_reparto.py -- 164 lineas

l46: class Oferta
l80: SIN_OFERTA = Oferta()
l84: class Linea
l92: def coste_del_conjunto(lineas: list[tuple[Linea, int, Oferta]]) -> int
l111: def oraculo(peticiones, oferta) -> ...
```

## 2. Y su docstring, entero, es **la respuesta a «oraculo COMPLETO»**

```python
"""**El oraculo de asignaciones**: el minimo de verdad, enumerando todas, para cestas peque[ñas].

Por que existe: la revision de fase 2 lo pidio: «oraculo exhaustivo independiente de asi[gnaciones] ...
promociones condicionadas al conjunto». Y el criterio de F06: «Aplicar promociones a cada conjunto
**realmente asignado** [...] No elegir partes de un [total] calculado sobre una cesta que al final no se
compra en esa tienda.» «Aceptacion: casos combinatorios con contraejemplos, **discrepancias cero** para
esc[enarios] cubiertos, **suma de partes igual al total**; garantias y **limites** del algoritmo publica[dos]»

**Independiente quiere decir independiente.** Este modulo **no importa nada de `plataforma/api/cesta.py`**:
ni el optimizador, ni la aritmetica de promociones, ni la agrupac[ion]. [La] mecanica de la oferta **entra ya
leida** (`Oferta`), asi que el oraculo no depende ni del pa[rser] castellano de folleto. *Si los dos coinciden,
es porque los dos calculan bien, no porque com[partan el] mismo codigo.*

Que cubre y que no
------------------
**Cubre** las mecanicas cuyo alcance no esta en duda: sin oferta, `nxm` (3x2), `enesima` (2a [unidad] -50 %),
`porcentaje`, `precio_fijo`, `lote` y `descuento_fijo`.

**No cubre `umbral`** («5 EUR dto comprando 20 EUR»), **y a proposito**: el texto del folleto n[o dice si el]
umbral es del producto o del ticket entero, y el motor ha elegido una lectura **sin publicarla**.
13 de octubre de 2026: dos lineas **distintas** de 12 EUR con esa oferta dan **2400** centim[os] con la
lectura del motor y **1900** con la del ticket. **Mientras eso no se decida, un oraculo que [lo cubriera]
estaria eligiendo una de las dos lecturas y llamandola verdad.**
"""
```

## 3. Y contesta **las cuatro cosas** de B09

```
B09 PIDE                                        Y AQUI ESTA
  1) «REUTILIZAR motor y pruebas existentes»       *** y ademas: «INDEPENDIENTE QUIERE DECIR INDEPENDIENTE:
                                                   este modulo NO IMPORTA NADA de `plataforma/api/cesta.py`» ***
                                                   *-- o sea: **el oraculo es un SEGUNDO calculo, no una copia** *
  2) «banco de pares REAL/SINTETICO»               *-> `tests/test_banco_de_pares.py` (y `core/banco_de_pares.py`)*
  3) «exacto/familia/alternativa/desconocido»      *-> seis ficheros de ensayo, y POR MIRAR cuales*
  4) «EAN coincidente no neutraliza formato
      incompatible; distinto no acredita mismo
      articulo»                                     *** es `identidad.py`, y POR MIRAR ***
  5) «no modificar grupos de listas historicas
      por ordinal»                                  *** POR MIRAR -- y el plan lo pide POR ESCRITO ***
```

> *** Y la (1) es **la mas fuerte de todas**, y no la esperaba: *** **no basta con «reutilizar»: el oraculo tiene
> que ser **INDEPENDIENTE** -- *«si los dos coinciden, es porque **los dos calculan bien**, no porque **compartan el
> mismo codigo**».*
>
> *** Que es **la respuesta metodologica a la pregunta de siempre**: *** *¿como se sabe que un calculo esta bien?
> **Con un segundo calculo que no comparte nada con el primero.***
>
> *** Y eso **es lo que esta sesion ha estado haciendo a mano** -- *comparar los seis colectores, comparar los ocho
> fabricantes, comparar `despensa` con `cocina` -- **y el proyecto lo tiene escrito como criterio**: **«oraculo
> exhaustivo INDEPENDIENTE»**. ***

## 4. Y la discrepancia del `umbral` es **lo mas valioso del fichero**

> *** Dos lineas distintas de 12 EUR con la misma oferta de umbral: *** **2400 con la lectura del motor, 1900 con la
> del ticket.** *Y el oraculo **no lo cubre**, con esta razon:* *** «mientras eso no se decida, un oraculo que [lo
> cubriera] estaria **eligiendo una de las dos lecturas y llamandola verdad**». ***
>
> *** O sea: **el oraculo prefiere estar incompleto antes que mentir** *** -- *y **eso es la doctrina, decimosexta
> vez**, en su forma mas limpia: **un dato que no se puede decidir no se decide**.*
>
> *** Y «COMPLETO» en el titulo del paquete **no significa que el oraculo cubra todo**: *** *significa que
> **el conjunto de lo cubierto esta DICHO, y lo no cubierto tambien, con su razon y con su numero**.*
>
> *** Que es, exactamente, lo que el plan pide cuando dice «garantias y **limites** del algoritmo publicados». ***

## 5. Y lo que queda por mirar, dicho

```
POR MIRAR, y con nombre de fichero:
  - `core/identidad.py` -- *** los cuatro veredictos y las dos reglas del EAN ***
  - `core/banco_de_pares.py` y `tests/test_banco_de_pares.py` -- *** el banco de pares real/sintetico ***
  - `tests/test_g11_oraculo.py` (y `test_fase2_f06_oraculo_asignaciones.py`) -- *** los nombres ***
  - y el cuerpo de `oraculo()` (l111-164), que **no se ha leido**
```

> *** Y el siguiente, por el paso (3) del metodo: **los nombres de los ensayos**, *** *que es donde los cuatro
> veredictos (`exacto/familia/alternativa/desconocido`) tienen que aparecer **como palabras**.*
