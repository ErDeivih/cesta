# La auditoria que faltaba: las fichas de producto

Hasta el 19 de septiembre de 2026, `auditar_crudo.py` miraba el crudo de los
**listados** -- la rejilla de una categoria -- y nunca el de las **fichas**. Y la
ficha es donde esta lo bueno: la de DIA tiene **unas 200 claves**.

El resultado de mirarla: dos campos que marcaban **0 % en gold** llevaban semanas
ahi, y para uno de los dos el motor de lectura ya estaba escrito.

---

## 1. DIA: `conservacion` estaba al 0 % y el dato llevaba semanas en disco

`storage_instructions`, en el **44 %** de las fichas:

    "Mantengase en lugar fresco, seco y alejado de la luz"
    "Conservar a -18 ºC"
    "Conservar refrigerado entre 0 y 4 ºC"

Son **las mismas palabras que escribe Mercadona**, y
`sellos.conservacion_de_prosa` lleva semanas sabiendo leerlas: se escribio para
Mercadona, que tampoco tiene campo de conservacion. El dato estaba, el motor
estaba, y nadie los habia juntado.

Medido sobre 460 fichas reales de DIA:

| | antes | despues |
|---|---:|---:|
| conservacion | **0 %** | **34 %** (131 ambiente, 13 congelado, 11 refrigerado) |

De paso aparecio un fallo del propio lector: el patron era `lugar fresco y seco`
y DIA escribe `lugar fresco, seco y...` **con coma**. Ampliado a `lugar fresco` a
secas, que en unas instrucciones de conservacion es siempre la despensa -- la
nevera se dice con "refrigerado", "nevera" o "frio", y esos tres se comprueban
antes. Eso solo subio del 30 % al 34 %.

## 2. DIA: `origen` estaba al 0 %

    manufacturer_contact_country   29 %   "Union Europea"
    manufacturer_name              41 %   "Freudenberg Home and Cleaning Solutions"

Juntos, **69 %**. Se prefiere el pais y, si no lo dice, el fabricante.

**La direccion postal NO se usa**, y esta escrito como prueba: un domicilio
social no dice de donde viene un producto, y ponerlo en `origen` seria vender por
procedencia lo que solo es una oficina.

## 3. DIA: codigos de barras de mas, guardados y **sin usar a proposito**

`secondary_eans`, en el **22 %** de las fichas: 187 codigos en 460 productos.

La tentacion es evidente -- mas codigos, mas emparejamientos, y el emparejamiento
es donde estamos por delante de la competencia. **No se hace**, y la razon es la
de siempre: entre esos secundarios esta el codigo **del pack**. Emparejar por ahi
haria que un pack de seis y una unidad suelta fueran "el mismo producto", que es
exactamente el error que este proyecto se dedica a evitar.

Para usarlos hay que saber antes cual es de unidad y cual de pack, y la ficha no
lo dice. Se guardan; se usaran el dia que se sepa distinguirlos.

## 4. Lo que queda en la ficha de DIA, con su numero

Medido sobre las mismas 460 fichas. Nada de esto se lee todavia:

| campo | cobertura | para que |
|---|---:|---|
| `days_to_expiration` | 100 % | ya se lee |
| `drained_weight` | 100 % | peso de lo que hay dentro |
| `category_description` / `family_description` / `section_description` | 100 % | **el arbol de categorias de DIA en palabras** (backlog N3) |
| `item_vat_code` | 100 % | 920, 910, 905: tipo de IVA |
| `net_contents` | 48 % | contenido neto declarado |
| `nuts_free` / `caffeine_free` / `salt_free` | 26-53 % | **ojo**: el valor es "No Aplica"/"NO"/"SI". Solo "SI" vale |
| `manufacturer_warnings` | 22 % | advertencias |
| `serving_size` | 17 % | la base de la tabla nutricional |
| `alcohol_content` | 7 % | grado alcoholico |
| `nutritional_claim` | 5 % | "0 % azucares anadidos..." |
| `health_claim` | 3 % | declaraciones de salud |
| `nutri_score` | 2 % | el suyo, distinto del de Open Food Facts |
| `hazard_info` | 2 % | codigos CLP estructurados (`H319` + descripcion) |
| `stamp_description` | 2 % | **lo que significan los `stamp_code`** del listado |
| micronutrientes (calcio, hierro, vitaminas...) | 1-2 % | mas alla de la tabla basica |

Dos avisos para quien los implemente:

- **Los "free" son trampa.** `gluten_free` vale "No Aplica" en el 72 % de las
  fichas, y "No Aplica" **no significa sin gluten**. Solo cuenta un "SI"
  explicito. Es la asimetria de siempre: en un filtro de inclusion, pasarse
  marcando es peligroso.
- **`stamp_description` desbloquea los `stamp_code`.** En la auditoria de
  listados del 18 de septiembre quedaron 1.096 productos con `stamp_code` 1, 2, 3
  o 4 y la nota "no se tocan hasta saber que significan". La ficha lo dice.

## 5. Mercadona: poco, y ya conocido

Solo hay 11 fichas en el crudo del dia -- el maestro es incremental, 100 al dia,
y el crudo viejo se limpia --, asi que la muestra es corta:

    extra_info      100 %   ['Nota olfativa floral']
    main_feature     73 %   ya apuntado (backlog N19)
    is_bulk         100 %   a granel
    details.is_prepared_by_mercadona

Nada del tamano de lo de DIA.

## 6. La leccion

Es la tercera vez este mes que el hallazgo tiene la misma forma: **el dato estaba
descargado y el codigo para leerlo tambien, y lo que faltaba era la linea que los
une.** Paso con `promo_club` (1.244 ofertas de tarjeta contadas como rebajas),
paso con los `iconAttributes` de Alcampo, y pasa aqui con la conservacion de DIA.

Por eso `auditar_crudo.py` existe. Lo que faltaba era apuntarlo tambien a las
fichas, no solo a los listados.
