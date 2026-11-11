# Caso Cesta: comparar la cesta entre seis supermercados

Mini-informe del cálculo que sostiene la pantalla de comparación. Cifras del catálogo publicado
el **11 de noviembre de 2026** (gold `20261111-140508`), no de una simulación.

**Las tres cifras del caso:** **6 cadenas** · **2,8 M de filas de precio** (2.866.370) ·
**91,1 % de precisión** de emparejamiento sobre **4.804 pares** con verdad de EAN.

## 1. El problema

Una compra semanal se decide entre seis cadenas con precios que cambian a diario. Tres cosas
hacen que la decisión no sea una simple resta:

1. **Los formatos no son comparables**: un brick de 1 l y una lata de 33 cl no se comparan por
   precio, sino por €/l.
2. **Las cadenas no tienen los mismos productos**: dos listas de la compra rara vez están
   completas en las seis, y el total de una cadena incompleta no es comparable con el de una
   completa.
3. **Hay ofertas que no son un descuento real**: las que piden tarjeta, cupón o compra por
   internet no bajan lo que se paga en caja, así que no se restan.

El objetivo es contestar **«esta lista, ¿dónde sale mejor y cuánto me ahorro?»** con una cifra
que se pueda explicar y comprobar, y un desglose que permita ver de dónde sale.

## Portada: el caso en una tabla (recalculable a mano)

**Producto:** café molido Hacendado. **Pack:** 500 g (8,19 € en Carrefour → 16,38 €/kg).
**Cantidad pedida:** **1 kg**.

1. El pack trae 0,5 kg: `1 kg / 0,5 kg = 2 packs`.
2. Se paga el envase entero: `2 × 8,19 € = 16,38 €` donde el pack cuesta 8,19 €; en Mercadona,
   `2 × 4,40 € = 8,80 €`.
3. La variación por el mismo kilo: `16,38 € − 4,76 € = 11,62 €`.

| Cadena | Pack | 2 packs para 1 kg | €/kg | Variación |
|---|---:|---:|---:|---:|
| Alcampo | 2,38 € | **4,76 €** | 4,76 | — |
| Mercadona | 4,40 € | 8,80 € | 8,80 | +4,04 € |
| Carrefour | 8,19 € | 16,38 € | 16,38 | +11,62 € |
| DIA | 8,19 € | 16,38 € | 16,38 | +11,62 € |
| Aldi | — | sin equivalente | — | no se pinta 0 € |

**La misma cuenta con un multipack:** 6 × 125 g = 750 g a 2,40 € → 3,20 €/kg; para 1 kg,
`techo(1 / 0,75) = 2` packs, **4,80 €** y **0,50 kg de sobrante**.

Con la lista de demo (8 productos), la comparativa resume **9,15 € de ahorro posible (−38 %)**;
y la **cesta óptima** muestra el ahorro frente a una sola tienda: todo en Alcampo **17,46 €** o
repartido entre Alcampo y Aldi **15,00 €**, **2,46 € menos**. Capturas de la portada en
`docs/portfolio/`: `390/1280-comparativa.png`, `...-optima.png` y `...-totales.png`.

## 2. Datos

| Qué | Cuánto |
|---|---:|
| Cadenas con captura | **6** |
| Días de histórico | **65** |
| Filas de precio acumuladas | **2.866.370** |
| Productos en catálogo | **53.072** |
| Grupos comparables | **8.891** |
| Productos con medida (kg/l/ud) | **43.321** |
| Productos con código de barras | **25.573** (48,5 %) |
| Comparables con precio hoy | **39.164** |
| Comparables en 2+ cadenas | **8.846** |

Cobertura de la última captura, por cadena:

| Cadena | Filas | Errores | Duración |
|---|---:|---:|---:|
| Alcampo | 23.572 | 0 | 6.569 s |
| Carrefour | 16.684 | 1 | 2.711 s |
| DIA | 5.681 | 0 | 691 s |
| Mercadona | 4.284 | 0 | 101 s |
| Aldi | 2.769 | 0 | 90 s |
| Lidl | 82 | 0 | 5 s |

La ingesta del día terminó en **aviso** por una captura corta de Alcampo (WAF): el dato que falta
no se rellena con ceros; se declara. La publicación de referencia es `20261110-111521`.

### Fuentes de precios

No hay API de consumidor en ninguna de las seis cadenas, así que el dato sale de su **catálogo
público**, no de una integración privilegiada:

- **Captura diaria programada** a las 06:00 (Programador de tareas de Windows). Cada pasada
  descarga el catálogo de cada cadena con `httpx`/`curl-cffi`; **Alcampo** se captura con
  **Patchright + Chrome real** porque su WAF rechaza clientes HTTP simples.
- **Lidl** publica sobre todo folletos de ofertas: entran 82 filas de promo, no el catálogo entero;
  por eso no se usa como cadena completa en las comparaciones.
- Cada precio guarda **fecha de captura, cadena, producto, precio, unidad y promoción**, y se
  publica como un `gold` inmutable con huellas (`data/gold/actual.json`). Nada se sobrescribe: la
  foto de un día queda para el histórico.
- **Garantías de la pasada**: recuento de filas por cadena, referencia contra la captura anterior,
  presupuesto de tiempo y avisos si una captura sale corta. Un hueco se dice, no se rellena.


## 3. Normalización

Antes de comparar hay que dejar los datos en el mismo idioma:

- **Unidades**: kg/g y l/ml se convierten a una unidad canónica; `ud` solo se compara con `ud`.
  El €/kg o €/l se calcula desde el formato (peso o volumen) y **no se enseña si no está medido**.
- **Identidad**: primero el **código de barras (EAN)**, que es la prueba dura; si no está, marca +
  formato declarado, y por último el nombre con umbral de similitud. El código lo trae el 48,5 %
  del catálogo, y Alcampo y Aldi no publican ninguno.
- **Calidad del emparejamiento**: sobre 22.772 enlaces, 73,3 % son equivalentes (misma categoría y
  formato, marca distinta), 12,5 % misma marca, 7,7 % mismo EAN y 6,4 % sin formato comprobado.
  Medida contra 4.804 pares con verdad de EAN: **precisión 91,1 %**; por el nombre solo, 61,4 %.
  El EAN es lo que sostiene la calidad; el nombre, no.
- **Ofertas**: se aplica la oferta al precio de la cadena solo cuando el propio dato muestra la
  diferencia (`coste_sin_oferta_cent > coste_cent`); las condicionadas se muestran como condición,
  no como descuento.
- **Datos que faltan**: un producto sin precio en una cadena no cuenta en esa cadena; no se
  convierte en 0. Un producto sin formato medido no entra en la comparación por unidad.



### Buscar una alternativa desde la fila

Cuando una cadena no tiene el producto, la fila puede ofrecer **«Buscar alternativa»**. El
criterio es explícito:

- **Aceptar** cambia a qué producto apunta la línea y su grupo, para que el reparto lo encuentre
  en esa cadena: la cobertura y el total cambian.
- **Rechazar** no escribe nada: la fila se queda en «Sin equivalente» y el precio de la rechazada
  no suma en ningún total.
- Si no hay candidato, se dice, en vez de inventar uno.

### Las tres etiquetas de cada precio

En el desglose, cada cadena lleva su precio y una etiqueta que dice **qué** es ese precio:

- **Mismo producto**: mismo GTIN válido y presentación compatible. Es el único caso en que se
  puede decir «el mismo artículo»; cuenta en el total sin preguntar.
- **Alternativa**: un equivalente (misma categoría y formato, marca distinta, o nombre parecido
  sin GTIN). Se puede elegir, pero no es el mismo producto; **no suma en el total** hasta que se
  confirma, y el €/kg permite compararlo con el original.
- **Sin equivalente**: esa cadena no tiene hoy un producto que cubra lo pedido. No es un cero: no entra en su total, y no se pinta 0 €.

El **€/kg o €/L** va pegado al precio de cada fila; si el formato no trae medida, se dice «sin
medida» en vez de inventar una unidad. Así, dos precios solo se comparan cuando hablan de lo mismo.

## 4. Cómo se calcula el ahorro

La pantalla usa dos fórmulas, y **dice cuál está usando**:

### Caso A — dos o más cadenas completas

El ahorro es la diferencia entre el total de la cadena más barata y el de la más cara:

```
ahorro = total(cadena más cara) − total(cadena más barata)
porcentaje = ahorro / total(cadena más cara)
```

Solo entran cadenas con **la lista entera**; una incompleta no se compara, porque su total sería
más bajo por tener menos productos.

### Caso B — cada cosa donde está más barata (el normal)

Con la autorización por línea, rara vez hay dos cadenas completas. Entonces el ahorro es la suma,
producto a producto, de lo que separa el precio más caro del más barato de los que hoy tienen ese
producto:

```
ahorro = Σ_lineas ( max(precio en cadenas con precio) − min(precio) )
porcentaje = ahorro / Σ_lineas max(precio)
```

Los **equivalentes sin confirmar** cuentan en esta suma (son una estimación del ahorro posible),
pero no en los totales por cadena de abajo; la nota de la tarjeta lo dice. Las ofertas
condicionadas no se restan en ninguno de los dos casos.

### Ejemplo real (cesta de demo, 8 productos)

| Producto | Más barato | Más caro | Diferencia |
|---|---:|---:|---:|
| Café molido Hacendado | 2,38 € (Alcampo) | 8,19 € (Carrefour) | **5,81 €** |
| Tomate triturado All Seasons | 0,94 € (Aldi) | 2,80 € (Alcampo) | **1,86 €** |
| Perlitas VAHINÉ 100 g | 3,87 € (Alcampo) | 4,65 € (Carrefour) | **0,78 €** |
| Detergente Esselt | 1,09 € (Aldi) | 1,50 € (Alcampo) | 0,41 € |
| Yogur natural Milsani | 1,29 € (Aldi) | 1,45 € (Carrefour) | 0,16 € |
| Caldo casero Gallina Blanca | 2,29 € (Carrefour/Aldi) | 2,36 € (Alcampo) | 0,07 € |
| Tarrito HERO | 1,75 € (Alcampo) | 1,80 € (Carrefour) | 0,05 € |
| Picos sin gluten | 1,39 € (DIA/Aldi) | 1,40 € (Carrefour) | 0,01 € |
| **Total** | | | **9,15 €** |

**Comprobación del total, a mano:** `5,81 + 1,86 + 0,78 + 0,41 + 0,16 + 0,07 + 0,05 + 0,01 = 9,15 €`.
La base (suma de los precios máximos) es `8,19 + 2,80 + 4,65 + 1,50 + 1,45 + 2,36 + 1,80 + 1,40 = 24,15 €`,
y `9,15 / 24,15 = 37,9 %` → la tarjeta lo redondea a **−38 %**.

Base de la suma de máximos: **24,15 €** → **37,9 %** de ahorro posible; la tarjeta redondea a
**9,15 € / −38 %**. El €/unidad enseña la misma diferencia en la unidad correcta: el café está a
**16,38 €/kg** en Carrefour y **8,80 €/kg** en Mercadona; el detergente a **0,58 €/l** frente a
**0,55 €/l**. Y el producto que vuelve a su mínimo lleva su marca: «En su mínimo · 3,87 €».


## 4 bis. Multipack y envases enteros

Un pack de **6 × 125 g** no se vende por kilos. El paquete trae **750 g** y cuesta **2,40 €**, así
que su precio normalizado es:

`
2,40 € / 0,750 kg = 3,20 €/kg
`

Y si se necesitan **1 kg**, no se compra «1,33 packs»: los envases se compran enteros.

`
envases = techo(1 kg / 0,750 kg) = 2
coste   = 2 × 2,40 € = 4,80 €
sobra   = 2 × 0,750 kg − 1 kg = 0,50 kg
`

La comparativa enseña el €/kg o €/L **al lado del precio** y, al abrir un producto, una
**calculadora de envases**: se escribe la cantidad que se necesita y cada cadena dice cuántos
envases enteros hacen falta, lo que se paga y lo que sobra. Si la cantidad y el envase no son de
la misma magnitud (kg contra l) o falta el tamaño, **no se calcula**: se dice, en vez de inventar
una compra fraccionaria.

Y una cadena que no tiene el producto **no se pinta como 0 €**: su fila dice «Sin equivalente» y
no entra en ningún total. El cero se reserva para lo que de verdad cuesta cero, que no es el caso.


## 4 ter. La cesta en una o dos tiendas

El algoritmo es simple y se puede explicar sin caja negra: **se prueban todas las tiendas y todas
las parejas de tiendas, se exige que cubran toda la lista y se queda la más barata.** Una tienda
sin un producto **no entra como 0 €**: esa opción no se propone. Y si repartir no ahorra, no se
anuncia un ahorro: se dice que no compensa partir la compra.

Con la cesta de demo (8 productos, precios del 10/11, incluidas alternativas sin confirmar):

- **Una tienda:** Alcampo, **17,46 €** (la única completa junto con Carrefour).
- **Dos tiendas:** Alcampo + Aldi, **15,00 €** (3 productos en Alcampo y 5 en Aldi).
- **Ahorro:** **2,46 €** frente a comprarlo todo en una.

La frase que sale en pantalla: «Comprando todo en Alcampo: 17,46 €. Repartiendo entre Alcampo y Aldi: 15,00 €. Te ahorras 2,46 €.»

### Ejemplo numerado: producto, pack, cantidad pedida, coste por cadena

Producto: **café molido Hacendado**. Pack: **500 g** (8,19 € a 16,38 €/kg en Carrefour). Cantidad
pedida: **1 kg**. Como el pack trae 0,5 kg, hacen falta **2 packs**:

| Cadena | Precio del pack | 2 packs para 1 kg | €/kg | Variación frente a la más barata |
|---|---:|---:|---:|---:|
| Alcampo | 2,38 € | **4,76 €** | 4,76 €/kg | — |
| Mercadona | 4,40 € | 8,80 € | 8,80 €/kg | +4,04 € |
| Carrefour | 8,19 € | 16,38 € | 16,38 €/kg | +11,62 € |
| DIA | 8,19 € | 16,38 € | 16,38 €/kg | +11,62 € |
| Aldi | — | **sin equivalente** | — | no se pinta 0 € |

La **variación** entre la cadena más barata y la más cara es **11,62 € por el mismo kilo de café**.
Ese es el tipo de diferencia que la comparativa pone en unidades comparables y que la cesta óptima
convierte en una decisión: llevarlo en Mercadona o repartir la compra.

## 5. Resultado

- **La cifra grande existe y es explicable**: 9,15 € de ahorro posible (−38 %) en una cesta de
  8 productos, con el desglose que la produce y las fórmulas a un toque («¿Cómo se calcula?»).
- **Los totales por cadena** dicen lo que cada una tiene hoy: Carrefour, 18,73 € con **Encontrados 7/8**; las demás, sin precio para esta lista. Una cadena incompleta no se presenta como
  ganadora.
- **El gráfico de barras** enseña la diferencia de cada producto en el mismo orden que el desglose: la barra más larga es donde más hay que decidir.
- **El €/kg y el €/l** hacen la comparación honesta: el mismo producto, no dos formatos distintos; y la calculadora de envases dice cuántos packs hay que comprar para una cantidad (6 × 125 g a 2,40 € son 3,20 €/kg; para 1 kg, 2 packs y 4,80 €).
- **La app se puede usar de punta a punta** con estos datos: lista → comparativa → sugerencias
  (repetir la compra semanal, con lo que falta en casa) → exportar CSV, y la comparativa propone
  la **cesta en 1 o 2 tiendas** con su ahorro en una frase.

**Lo que el informe no afirma**: no es una predicción de la compra real en varias tiendas (no
descuenta desplazamiento), no incluye ofertas que no se pueden aplicar sin tarjeta o cupón, y no
supone que un producto esté disponible si la captura no lo trae. Esas tres cosas están dichas en
la propia pantalla.


## 6. Criterios de la revisión (CE-*)

| ID | Criterio | Dónde se cumple |
|---|---|---|
| **CE-U3 / CE-I1** | Separa «Subtotal · faltan N» de «Cesta completa»; «Más barata» solo entre cestas comparables. Una cadena con 7 de 8 no gana a una con 8 de 8. | CadenaEnLaLista: la etiqueta verde solo la lleva la ganadora entre las completas; las incompletas dicen «Subtotal · faltan N» y no se coronan. |
| **CE-F1** | Coste de la cantidad pedida con envases completos, separado del precio normalizado. 1 kg de un pack de 750 g a 2,40 € → 2 packs (1,5 kg) por 4,80 €. | Calculadora de envases (logica/envases.ts) y §4 bis: 	echo(1/0,75)=2, 2×2,40=4,80, sobra 0,50 kg. |
| **CE-F2** | Exacto / Alternativa / Sin equivalente, con motivo. Cada fila dice cómo se decidió. | Cada fila enseña la etiqueta y el motivo de la API («GTIN distinto…», «coincidencia parcial sin GTIN…»); sin producto, «Sin equivalente» y nunca 0 €. |
| **CE-I2** | Coste de compra primero y €/kg o €/L debajo, con el formato del pack. «6×125 g · 2,40 €» muestra 3,20 €/kg. | La fila pinta primero el precio, debajo «6 × 125 g · 3,20 €/kg»; el formato sale del nombre o del coste ÷ €/kg. |
| **CE-U1** | La cesta se conserva al cambiar de cadena: 8 artículos se mantienen al ir y volver. | POST /api/listas/{id}/tienda cambia cadena_elegida, no las líneas: comprobado con 8 líneas antes, 8 durante y 8 después (mismos ids). |

## 7. Dónde comprobarlo

- Capturas: [`390-comparativa.png`](portfolio/390-comparativa.png),
  [`1280-comparativa.png`](portfolio/1280-comparativa.png) y
  [`1280-comparativa-calculo.png`](portfolio/1280-comparativa-calculo.png) (explicación abierta).
- Cifras de catálogo: [`CIFRAS.md`](CIFRAS.md); calidad: [`CALIDAD-DEL-EMPAREJAMIENTO.md`](CALIDAD-DEL-EMPAREJAMIENTO.md).
- Código: `plataforma/web/app/src/paginas/CompararCesta.tsx` (fórmulas y estados) y
  `plataforma/api/cesta.py` (reparto, €/unidad y ofertas).
- Datos: `data/gold/actual.json` apunta a la publicación del día.
- **Publicado en el portfolio:** [cesta-caso.html](https://erdeivih.github.io/cesta-caso.html),
  enlazado desde la sección Cesta de [casos.html](https://erdeivih.github.io/casos.html#cesta).
