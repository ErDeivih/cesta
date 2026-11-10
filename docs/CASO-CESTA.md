# Caso Cesta: comparar la cesta entre seis supermercados

Mini-informe del cálculo que sostiene la pantalla de comparación. Cifras del catálogo publicado
el **10 de noviembre de 2026** (gold `20261110-111521`), no de una simulación.

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

## 2. Datos

| Qué | Cuánto (10/11/2026) |
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
| Café molido Hacendado | 4,40 € (Mercadona) | 8,19 € (Carrefour) | **3,79 €** |
| Tomate triturado All Seasons | 0,94 € (Aldi) | 2,45 € (Carrefour) | **1,51 €** |
| Perlitas VAHINÉ 100 g | 3,87 € (Alcampo) | 4,65 € (Carrefour) | **0,78 €** |
| Detergente Esselt | 1,09 € (Aldi) | 1,50 € (Alcampo) | 0,41 € |
| Yogur natural Milsani | 1,29 € (Aldi) | 1,45 € (Carrefour) | 0,16 € |
| Caldo casero Gallina Blanca | 2,29 € (Carrefour/Aldi) | 2,36 € (Alcampo) | 0,07 € |
| Tarrito HERO | 1,75 € (Alcampo) | 1,80 € (Carrefour) | 0,05 € |
| Picos sin gluten | 1,39 € (DIA/Aldi) | 1,40 € (Carrefour) | 0,01 € |
| **Total** | | | **6,78 €** |

Base de la suma de máximos: **23,80 €** → **28,5 %** de ahorro posible; la tarjeta redondea a
**6,78 € / −28 %**. El €/unidad enseña la misma diferencia en la unidad correcta: el café está a
**16,38 €/kg** en Carrefour y **8,80 €/kg** en Mercadona; el detergente a **0,58 €/l** frente a
**0,55 €/l**. Y el producto que vuelve a su mínimo lleva su marca: «En su mínimo · 3,87 €».

## 5. Resultado

- **La cifra grande existe y es explicable**: 6,78 € de ahorro posible (−28 %) en una cesta de
  8 productos, con el desglose que la produce y las fórmulas a un toque («¿Cómo se calcula?»).
- **Los totales por cadena** dicen lo que cada una tiene hoy: Carrefour, 18,73 € con 7 de 8
  productos; las demás, sin precio para esta lista. Una cadena incompleta no se presenta como
  ganadora.
- **El gráfico de barras** enseña la diferencia de cada producto en el mismo orden que el desglose: la barra más larga es donde más hay que decidir.
- **El €/kg y el €/l** hacen la comparación honesta: el mismo producto, no dos formatos distintos.
- **La app se puede usar de punta a punta** con estos datos: lista → comparativa → sugerencias
  (repetir la compra semanal, con lo que falta en casa) → exportar CSV.

**Lo que el informe no afirma**: no es una predicción de la compra real en varias tiendas (no
descuenta desplazamiento), no incluye ofertas que no se pueden aplicar sin tarjeta o cupón, y no
supone que un producto esté disponible si la captura no lo trae. Esas tres cosas están dichas en
la propia pantalla.

## 6. Dónde comprobarlo

- Capturas: [`390-comparativa.png`](portfolio/390-comparativa.png),
  [`1280-comparativa.png`](portfolio/1280-comparativa.png) y
  [`1280-comparativa-calculo.png`](portfolio/1280-comparativa-calculo.png) (explicación abierta).
- Cifras de catálogo: [`CIFRAS.md`](CIFRAS.md); calidad: [`CALIDAD-DEL-EMPAREJAMIENTO.md`](CALIDAD-DEL-EMPAREJAMIENTO.md).
- Código: `plataforma/web/app/src/paginas/CompararCesta.tsx` (fórmulas y estados) y
  `plataforma/api/cesta.py` (reparto, €/unidad y ofertas).
- Datos: `data/gold/actual.json` apunta a la publicación del día.
