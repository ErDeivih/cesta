# B08 (y B09) · **El mapa** -- y B08 trae **tres numeros de aceptacion**

*(13 de octubre de 2026. **Lo siguiente por el plan. Y el criterio viene con cifras.**)*

## 1. El criterio de B08, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:291`:

> **B08 · Calorias integradas pero personales**
>
> *Vista de **previstos** separada del diario real. Elegir **receta versionada, porciones efectivas y comida**;
> consultar **snapshot nutricional y cobertura antes de confirmar**. Acceso rapido desde **plan/cocina** con
> **recibo de consumo** y **correccion/borrado propios**. **Objetivo opcional por persona y fecha**; **grafias de
> registrado versus previsto versus objetivo**, **sin totalizar un dia no completo ni colorear diagnosticos
> medicos**. Aceptar **R1=270, media=135, ausencia de energia con proteina conocida, idempotencia, recarga y
> aislamiento A/B**; **compra nunca genera consumo por si sola**.*

## 2. Y desglosado, son cinco cosas -- y la ultima trae NUMEROS

```
1) PREVISTO != REGISTRADO    -- «vista de previstos SEPARADA del diario real»
2) QUE SE CONFIRMA Y CON QUE -- receta VERSIONADA · porciones EFECTIVAS · comida
                                · *** y consultar SNAPSHOT NUTRICIONAL Y COBERTURA ANTES DE CONFIRMAR ***
3) EL RECIBO Y SU DESHACER   -- «recibo de consumo y correccion/borrado PROPIOS», desde plan/cocina
4) EL OBJETIVO Y SUS GRAFICAS -- opcional · por persona Y FECHA · «registrado vs previsto vs objetivo»
                                · *** «sin totalizar un dia NO COMPLETO» ***
                                · *** «ni colorear diagnosticos medicos» ***
5) Y LA ACEPTACION, CON CIFRAS:
   *** R1 = 270 · media = 135 · ausencia de energia con proteina conocida ***
   + idempotencia · recarga · aislamiento A/B
   + *** «compra NUNCA genera consumo por si sola» ***
```

> *** Y dos cosas hay que subrayar, porque son la restriccion del propietario otra vez: ***
>
>   - *** «Consultar snapshot nutricional Y COBERTURA antes de confirmar» *** *-- *o sea: **antes de apuntar que
>     alguien ha comido algo, hay que poder decir **de donde sale la cifra y cuanto del plato esta cubierto**.* *Es
>     **`fuente_dato` y `cobertura`** (B06) **aplicados al acto de comer**.*
>   - *** «Ni colorear diagnosticos medicos» *** *-- *que es **la prohibicion de inventar objetivos de salud**,
>     *que el encargo pide: «no inventes ... **objetivos de salud**».* *** Y aqui esta dicho como prohibicion de
>     **pintar**: **el color es la opinion, y no se pone.** ***
>
> *** Y la aceptacion **da los tres numeros**, que son **los de las cinco recetas del propietario**: *** *R1 = 270,
> media = 135, y el caso de **un dia sin energia pero con proteina conocida** -- *que es **el caso en que la
> cobertura importa**: *hay proteina, no hay kcal, **y hay que decirlo sin inventar las kcal**.*

## 3. Y de propina, el criterio de B09 -- que es la continuacion natural

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:301`:

> **B09 · Identidad y coste con oraculo completo**
>
> *Reutilizar **motor y pruebas existentes**; **banco de pares real/sintetico con EAN, marca/variante/neto/pack y
> contradicciones**. **Exacto/familia/alternativa/desconocido visibles**. **EAN coincidente no neutraliza formato
> incompatible; distinto no acredita mismo articulo**. **No modificar grupos de listas historicas por ordinal**.*

> *** Y sus dos ultimas frases son **las dos lecciones de esta sesion**, puestas por el plan: ***
>
>   - *** «EAN coincidente no neutraliza formato incompatible; DISTINTO NO ACREDITA MISMO ARTICULO» *** *-- *que es
>     **la doctrina de las doce caras**, aplicada a la identidad: **que dos cosas se parezcan no las hace la
>     misma, y que se diferencien no las hace distintas.***
>   - *** «No modificar grupos de listas historicas por ordinal» *** *-- *que es **exactamente el fallo latente de
>     B03**: *«la consulta devolvia 11 columnas y el codigo esperaba 10»* -- *o sea: **depender de la POSICION de
>     las columnas**.* *** El plan lo prohibe por escrito, en el paquete que va de identidad. ***
>
> *** Y «reutilizar motor y pruebas existentes» es **el metodo de esta sesion, escrito en el plan**. ***

## 4. Y el orden de trabajo, el mismo

```
  1) ls de la zona                    -- `core/diario.py` (17,5 KB, ya localizado en B06), `core/alimentos.py`
                                         (leido), `plataforma/api/diario.py`, y `core/nutricion*` si existe
  2) LEER el fichero que el titulo nombra: *** el titulo es «Calorias», y el modulo es `core/diario.py` ***
     -- *que ya se leyo **su cabecera** en B06 (la columna `fuente_dato`), y **no su cuerpo***
  3) LOS NOMBRES DE LOS ENSAYOS        -- `test_de_la_ficha_al_diario.py`, `test_dia_nutricion.py`, `test_diario.py`
  4) COMPARAR los que hacen lo mismo
  5) y grep al final, con las palabras del codigo
```

> *** Y el paso (2) tiene una ventaja: `core/diario.py` **ya se abrio una vez** en B06 -- *pero **solo su cabecera**,
> para la columna `fuente_dato`.* *** Ahora toca **el cuerpo**: **como se apunta una porcion**, **que se guarda del
> snapshot**, y **si toca la compra**. ***
