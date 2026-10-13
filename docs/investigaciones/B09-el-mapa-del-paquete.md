# B09 · **El mapa del paquete** -- el criterio, y donde mirar

*(13 de octubre de 2026. **Lo siguiente por el plan. Y las piezas tienen los nombres del propio criterio.**)*

## 1. El criterio, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:301`:

> **B09 · Identidad y coste con oraculo completo**
>
> *«**Reutilizar motor y pruebas existentes**; **banco de pares real/sintetico con EAN, marca/variante/neto/pack y
> contradicciones**. **Exacto/familia/alternativa/desconocido visibles**. **EAN coincidente no neutraliza formato
> incompatible; distinto no acredita mismo articulo**. **No modificar grupos de listas historicas por ordinal**.»*

## 2. Y desglosado, son cuatro cosas -- y las cuatro son **reglas**, no tareas

```
1) REUTILIZAR                 -- «motor y pruebas EXISTENTES»   <- *y no escribir un motor nuevo*
2) EL BANCO DE PARES          -- real Y sintetico · con EAN · marca/variante/neto/pack · Y CONTRADICCIONES
3) LOS CUATRO VEREDICTOS      -- EXACTO / FAMILIA / ALTERNATIVA / DESCONOCIDO, *** visibles ***
4) Y DOS REGLAS DE IDENTIDAD  -- *** «EAN coincidente NO NEUTRALIZA formato incompatible;
                                  DISTINTO NO ACREDITA mismo articulo» ***
5) Y UNA PROHIBICION          -- *** «NO MODIFICAR grupos de listas historicas POR ORDINAL» ***
```

> *** Y hay **dos frases que son, literalmente, las lecciones de esta sesion puestas en el plan**: ***
>
>   - *** «EAN coincidente no neutraliza formato incompatible; distinto no acredita mismo articulo» *** *-- *que es
>     **la doctrina de las quince caras, en su forma de IDENTIDAD**: **que dos cosas se parezcan no las hace la
>     misma, y que se diferencien no las hace distintas.*** *Y es **lo mismo** que `_con_precios` escribe en su
>     docstring: «un nombre parecido no [quiere decir] que sea el mismo producto».*
>   - *** «No modificar grupos de listas historicas POR ORDINAL» *** *-- *que es **exactamente el fallo latente de
>     B03**: *«la consulta devolvia 11 columnas y el codigo esperaba 10»* -- *o sea, **depender de la POSICION**.*
>     *** El plan lo **prohibe por escrito**, en el paquete que va de identidad. ***

## 3. Y donde mirar, medido -- **con los nombres del criterio**

```
$ git grep -ln "oraculo|identidad|banco_de_pares|EAN" -- core/

  core/cesta_umbral.py    core/config.py        core/fetch.py       core/grupos_ids.py
  core/identidad.py       core/matching.py      core/off.py         core/oraculo_reparto.py
  core/previa_compra.py   core/schemas.py

Y LOS ENSAYOS, que es donde mas informa:

  tests/test_banco_de_pares.py                    <- *** «banco de pares»: EL NOMBRE DEL CRITERIO ***
  tests/test_g11_oraculo.py                       <- «G11»: un punto del encargo, como `g12` en B05
  tests/test_fase2_f06_oraculo_asignaciones.py    <- «oraculo de asignaciones»: el titulo del paquete
  tests/test_identidad.py                         · test_identidad_sombra.py
  tests/test_auditar_identidad.py                 · test_marca_en_identidad.py
  tests/test_revision_a02_identidad.py            · test_serializa_identidad.py
  tests/test_fase2_f01_alerta_identidad.py
```

> *** Y fijate en que **el criterio nombra dos cosas y las dos tienen fichero**: ***
>
>   - **«banco de pares»** *-> **`tests/test_banco_de_pares.py`** -- *y **`core/banco_de_pares.py`**, que ya salio
>     citado en B07 por la «cobertura de EAN»;*
>   - **«oraculo»** *-> **`core/oraculo_reparto.py`**, **`test_g11_oraculo.py`** y
>     **`test_fase2_f06_oraculo_asignaciones.py`**.*
>
> *** O sea: **igual que en B05, B06 y B07**, el paquete **no hay que construirlo**: hay que **leerlo y ver si esta
> entero**. ***

## 4. Y el orden de trabajo, el de los tres paquetes anteriores

```
  1) ls de la zona                          (hecho: los diez modulos y los nueve ensayos)
  2) LEER el fichero que el titulo nombra:  *** `core/oraculo_reparto.py` ***
     -- «oraculo» esta en el TITULO del paquete, y `oraculo_reparto` es su nombre
  3) LOS NOMBRES DE LOS ENSAYOS             -- y aqui hay NUEVE, con `test_banco_de_pares.py` entre ellos
  4) COMPARAR los que hacen lo mismo
  5) y grep al final, con las palabras del codigo

  Y NO DECIR NUNCA: «no existe», «y nada mas», «hay que construirlo», «ya esta» sin su cita
```

> *** Y el paso (3) tiene **una ventaja concreta en B09**: *** *el criterio pide
> **«exacto/familia/alternativa/desconocido visibles»** -- *y **esos cuatro nombres son los que hay que buscar en
> los ensayos**, porque **los nombres de los ensayos son el contrato**.*
>
> *** Y el paso (2) tiene **la pista del titulo**: *** *«oraculo **COMPLETO**» -- *y **`completo` es la palabra que
> hay que probar**: *si el oraculo esta **a medias**, el paquete pide **acabarlo**, y **eso si seria trabajo**.*
