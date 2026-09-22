# Sellos y certificados

Escrito el 17 de septiembre de 2026, despues de encontrar que Aldi publica 32
certificaciones oficiales y llevabamos once dias tirandolas.

Este documento explica **dos vocabularios distintos que la gente confunde** y que
aqui viven en columnas separadas a proposito.

---

## 1. La diferencia entre un sello y un certificado

| | **sello** (`core/sellos.py`) | **certificado** (`core/certificados.py`) |
|---|---|---|
| responde a | ¿puedo comerlo? | ¿de donde sale y como se hizo? |
| para que sirve | **filtrar** una compra | **ordenar** una comparacion |
| ejemplos | sin gluten, sin lactosa, vegano, ecologico | DOP, IGP, MSC, Fairtrade, bienestar animal, FSC |
| quien lo dice | la cadena, en su ficha o en el nombre | un organismo de tercero, con auditoria |
| si te equivocas | alguien celiaco come gluten | el producto sale mal ordenado |

Mezclarlos tiene una consecuencia concreta y fea: el filtro "ecologico"
devolveria **camisetas de algodon organico** entre los alimentos. Ese es
exactamente el error que la OCU le reprocha a Yuka y a El CoCo (ver
`docs/COMPETENCIA.md`, punto 3): proponer alternativas de otra categoria.

Por eso Natrue (cosmetica natural), Oeko-Tex (tejidos), FSC y PEFC (papel y
madera) y Ecolabel entran como **certificado** y **nunca** ponen el sello
`ecologico`. Ecologico de verdad, en el sentido del Reglamento (UE) 2018/848,
solo lo pone la eurohoja.

---

## 2. El vocabulario de sellos

    sin-gluten   sin-lactosa   vegano   vegetariano   ecologico
    sin-azucar   sin-sal       halal    kosher        sin-aceite-palma

Se guardan en una sola columna de texto, **ordenados alfabeticamente y separados
por comas**, para que dos productos con los mismos sellos tengan exactamente el
mismo texto y se pueda filtrar con un `LIKE` sin montar otra tabla.

El filtro se escribe siempre con las comas puestas:

```sql
',' || coalesce(sellos, '') || ',' LIKE '%,sin-sal,%'
```

Sin las comas, `sin-sal` casaria dentro de `sin-salsa`.

### 2.1 De donde sale cada sello: `sellos_origen`

No todos valen lo mismo, y la ficha lo dice en pantalla:

| valor | significa | fiabilidad |
|---|---|---|
| `certificado` | logotipo de un organismo con auditoria detras | alta |
| `etiqueta` | la cadena lo marca en su ficha | alta |
| `nombre` | solo lo dice el nombre del producto | es marketing |
| `mixto` | las dos cosas | alta |

Lo rellena **silver**, no los colectores, porque el nombre del producto es la
unica columna que publican las cinco cadenas al 100 %.

Medido el 17 de septiembre sobre 52.575 productos:

| cadena | con sellos | certificado | etiqueta | nombre | mixto |
|---|---:|---:|---:|---:|---:|
| alcampo | 6.202 | 0 | 5.750 | 255 | 197 |
| carrefour | 3.863 | 0 | 3.272 | 320 | 271 |
| dia | 1.225 | 0 | 1.155 | 48 | 22 |
| aldi | 394 | 346 | 35 | 6 | 7 |
| mercadona | 155 | 0 | 0 | 155 | 0 |
| **total** | **11.910 (22,8 %)** | | | | |

    sin-gluten 7.355 · vegano 2.874 · sin-lactosa 2.346 · ecologico 1.966
    sin-azucar 1.021 · sin-aceite-palma 67 · sin-sal 60 · vegetariano 10

DIA aparece con 1.225 desde el 17 de septiembre por la tarde, y antes tenia 147.
Los tenia guardados desde el primer dia en dos campos con el nombre enganoso:
`allergens` (que no son alergenos, son 1.177 productos etiquetados "Sin gluten",
"Sin lactosa" o "BIO") y `product_info` (336 mas). Lo encontro
`projects/cesta/auditar_crudo.py`, no una persona.

`sin-azucar` (1.021) es interesante porque **practicamente ninguna cadena lo
etiqueta**: 990 de los 1.021 salen de leer el nombre del producto.

---

## 3. Los 32 certificados de Aldi

`assets` trae tres tipos de imagen y durante once dias solo se leia `primary`
(la foto). `certificate` aparece en **1.106 de 2.065 productos (53,6 %)** y no es
texto libre: es un catalogo cerrado de logotipos con nombre de fichero estable.

| logotipo | nuestro certificado | sello que implica | productos |
|---|---|---|---:|
| `01_A_Origen_nacional` | origen-espana | — (pone `origen = España`) | 186 |
| `07_Sin_gluten` | feacab | sin-gluten | 181 |
| `V-Label_Vegano_Color` | v-label | vegano | 109 |
| `48_Adilac` | adilac | sin-lactosa | 108 |
| `51_A_Rainforest_Alliance_*` | rainforest-alliance | — | 124 |
| `12_ALDI_Nord_Logo_2021` | — (pone `es_marca_propia`) | — | 63 |
| `52_Fairtrade_Cocoa`, `60_A_Fairtrade` | comercio-justo | — | 59 |
| `EU_Organic_Logo_*` | eurohoja | ecologico | 52 |
| `MSC_0626` | msc | — | 26 |
| `Bienestar_animal_AENOR_*`, `welfair` | bienestar-animal | — | 25 |
| `VeganTM-Palette1-LeafyGreen` | vegan-trademark | vegano | 20 |
| `01_B_Carne_nacional` | origen-espana | — | 19 |
| `FSC-R-logobackground_green` | fsc | — | 19 |
| `Standard_Oekotex` | oeko-tex | — | 18 |
| `63_Natrue` | natrue | — | 17 |
| `V-Label_Vegetariano_Color` | v-label | vegetariano | 8 |
| `43_DOP` / `44_IGP` / `45_ETG` | dop / igp / etg | — | 19 |
| `64_Ecolabel` | ecolabel | — | 7 |
| `OrganicCotton_Oekotex` | algodon-organico | — | 4 |
| `66_GGN_certified_farming` | ggn | — | 3 |
| `62_PEFC` | pefc | — | 2 |
| `42_ASC_16_mm_de_alto` | asc | — | 1 |

Resultado: **729 productos con certificado (35,3 %)**, 342 con sellos de dieta
que antes no teniamos y **205 con pais de origen**.

En el catalogo entero son **761 productos con certificado**: casi todos vienen de
Aldi, porque es la unica cadena que publica los logotipos. Esa cifra la vigila
`verificar_docs`; hasta el 18 de septiembre de 2026 creia vigilarla y no lo hacia
-- buscaba "761" con `in` y lo encontraba dentro del "10.761" de
`PARIDAD-CAMPOS.md`.

### 3.1 Los que no sabemos leer

Cuatro nombres de fichero son el nombre por defecto de Illustrator, en 36
productos:

    "Mesa de trabajo 1"   "Mesa de trabajo 3"   "ES Portrait (1)"   "ES Landscape (1)"

Alguien en Aldi subio el logo sin renombrarlo. **No se adivinan**: se cuentan con
`certificados.sin_traducir()` para que salgan en la auditoria el dia que los
arreglen o aparezca uno nuevo.

---

## 4. Lo que esto cambia sobre el origen

El 5 de septiembre se midio que el `origen` tenia un techo del **3,7 %** del
catalogo (~1.900 de 51.781) y se dio por imposible el filtro "producto espanol"
(ver `docs/PARIDAD.md`). Esa medicion era correcta con los campos que se miraban,
y estaba incompleta:

- Aldi **no publica el origen en ningun campo de texto**. Lo publica en un
  logotipo (205 productos) y dentro de su descripcion, con forma de `Origen:
  España, Francia, Italia` (212 productos). Entre los dos: **306 productos de
  2.065 (14,8 %)**, donde antes habia cero.
- El techo global sigue siendo bajo (3 %), pero la conclusion "es imposible" era
  falsa: el dato existe, estaba donde no lo buscabamos.

Queda pendiente mirar lo mismo en Carrefour y Alcampo, que hoy dan 0 %.

---

## 5. Como se anade una cadena nueva a este sistema

1. Buscar en su crudo cualquier lista de etiquetas, tags o iconos. En Alcampo es
   `iconAttributes`, en Carrefour `info_tags[].message`, en Aldi
   `assets[type=certificate]`.
2. Si son **textos**, pasarlos por `sellos.de_etiquetas(lista)`. Si hay palabras
   nuevas, anadir un patron a `_PATRONES` con limites de palabra `\b`.
3. Si son **logotipos**, anadir la clave al `_CATALOGO` de `core/certificados.py`
   **en su forma ya limpia** (sin `_Color`, sin `_rgb`, sin ano ni milimetros).
   El test `test_las_claves_del_catalogo_sobreviven_a_la_limpieza` lo comprueba.
4. Si la cadena escribe **prosa** (una descripcion), usar `sellos.de_prosa()`,
   que es mas estricto a proposito: "con extracto de arroz ecologico" describe un
   ingrediente, no el producto.
5. Medir sobre el crudo antes y despues, y apuntar el numero en este documento.

---

## 6. La trampa que costo encontrar

Hasta el 17 de septiembre, `de_etiquetas` buscaba con `subcadena in texto` y el
comentario de al lado prometia que exigia palabra entera. El comentario mentia.
Con `eco` y `bio` en el diccionario, esto devolvia el sello **ecologico** para:

    "Seco"        "Recambios"        "Marruecos"        "economico"        "Ecopack"

Con etiquetas cortas y controladas nunca llego a fallar. Salto al leer texto
libre: en la descripcion de Aldi, `Origen: Marruecos` marcaba el producto como
ecologico. Ahora cada sello es una expresion regular con `\b`, y hay un test
(`test_una_palabra_que_contiene_el_sello_no_es_el_sello`) con esas cinco trampas.
