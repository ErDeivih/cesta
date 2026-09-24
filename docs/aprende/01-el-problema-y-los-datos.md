---
seccion: Fundamentos
resumen: Que publica cada cadena, cuanto ocupa cada capa y que NO se puede concluir.
---

# 01 · El problema, los datos y lo que NO se puede concluir

Todo curso de datos debería empezar por aquí, y casi ninguno lo hace: **qué datos hay de
verdad**, con sus huecos, y qué preguntas se pueden contestar con ellos. La mitad de los
errores caros de un proyecto salen de saltarse este capítulo.

## 1. La pregunta

La aplicación existe para contestar cuatro preguntas, y las cuatro se hacen **de pie en un
pasillo**, con una mano y sin tiempo:

1. ¿Qué me falta comprar y dónde lo compro?
2. Esto que tengo en la mano, ¿está caro?
3. ¿Voy tachando bien?
4. ¿Ha bajado algo de lo mío?

Fíjate en que ninguna es «enséñame un gráfico». Eso no es una casualidad de este proyecto: es
la diferencia entre **enseñar datos** y **contestar preguntas**, y en un portfolio se nota
muchísimo. La pregunta manda sobre la arquitectura: si la respuesta tiene que caber en la
primera pantalla de un móvil, no vale «descárgate el CSV».

## 2. De dónde salen los datos

Cinco cadenas españolas, cada una con su web pública y su manera de publicarla:

    alcampo     catálogo con navegación por categorías; WAF que a veces pide navegador real
    aldi        listado por categorías, sin código de barras
    carrefour   catálogo con API interna y URL por producto
    dia         el más completo: código de barras, cantidad declarada, ingredientes
    mercadona   la única que publica promociones con fecha de fin

De la tabla completa de qué publica cada una (campo a campo, con porcentajes medidos) está
`docs/CADENAS.md`, y es el documento que hay que leer antes de escribir una línea. Tres
consecuencias que ordenan todo el diseño:

- **La mitad del catálogo no tiene código de barras.** Alcampo y Aldi no lo publican: medido
  el 15 de septiembre de 2026 sobre el catálogo de entonces, **25.638 de 51.781 productos, el
  50 %**. El EAN es la única llave que dice «este producto es *exactamente* este otro» sin
  dudar, y sin él solo se puede emparejar por nombre, formato y cantidad. No es un fallo que
  se arregle programando mejor: es lo que hay en la fuente.
- **La información nutricional solo existe en tres cadenas, y a medias** (ingredientes: DIA
  76 %, Mercadona 57 %, el resto 0 %).
- **Las promociones casi nadie las declara**: `promo_txt` lo trae el 12 % de Alcampo y el 8 %
  de Aldi, y nada en las otras tres. Lo que se sabe de ofertas hay que **deducirlo del
  precio**, no leerlo.

## 3. Cuánto ocupa esto, de verdad

Medido hoy con `Get-ChildItem` sobre `data/` (el comando está en el pie):

    data/raw        72.426 ficheros   2.874,6 MB   lo que devolvio la web, tal cual
    data/bronze         86 ficheros      65,6 MB   parquet sin tocar
    data/silver         86 ficheros      84,0 MB   limpio y tipado
    data/gold           67 ficheros     219,5 MB   lo que consume la aplicacion

Dos lecciones de esta tabla:

1. **El 96 % del peso es el crudo** (2.874 MB de 3.243 MB). Es HTML y JSON con todo el ruido
   de la web —menús, scripts, textos legales— del que se aprovecha un puñado de campos.
2. **`gold` (219 MB) pesa más que `silver` (84 MB)**, y eso sorprende hasta que se mira qué
   hay dentro: 190 MB son un `embedding.parquet` con los vectores de los 52.567 productos.
   Un fichero de 4 bytes por producto por 384 dimensiones es más grande que el catálogo
   entero, y es el ejemplo perfecto de que **el coste de un dato no se mide en filas**.

```powershell
Get-ChildItem -Recurse -File data\raw, data\bronze, data\silver, data\gold |
    Group-Object { $_.Directory.FullName -replace '.*\\data\\','data\' } |
    ForEach-Object { "{0,-14} {1,7} ficheros  {2,8:N1} MB" -f $_.Name, $_.Count,
                     (($_.Group | Measure-Object Length -Sum).Sum / 1MB) }
```

## 4. Qué preguntas se pueden contestar, y cuáles no

Aquí está lo que separa un proyecto honesto de una demo: **decir lo que no se puede hacer con
estos datos**, antes de que alguien lo dé por hecho. Con precios diarios, catálogo y listas de
la compra, y **sin ventas ni tickets**, la frontera es esta:

| Lo que se quiere saber | ¿Se puede? | Por qué |
|---|---|---|
| Cuánto cuesta lo mismo en cada cadena | **Sí** | Catálogo emparejado + precio diario |
| Si una oferta anunciada es real | **Sí** | El histórico propio dice cuál es su precio normal |
| Cuánto ha subido *mi* compra | **Sí**, con matices | Cesta fija: sin cantidades no hay ponderaciones por gasto |
| Qué productos se compran juntos | **No** | Una lista de la compra es una *intención*, no la cesta: no se observa lo que no se apuntó |
| Elasticidad de la demanda | **No** | Sin cantidades vendidas, correlación precio-cantidad no es elasticidad |
| Cuota de mercado por cadena | **No** | No hay ventas. El catálogo no dice cuota |
| Cuánto subirán los precios | **Casi** | Previsión de un índice agregado a pocos días; de un producto suelto, no |
| Estacionalidad anual | **No** | Con 19 días de histórico no hay un solo ciclo anual |

Esa tabla es material de portfolio por sí sola: demuestra que sabes **acotar** un problema.
El detalle de cada fila, con las fuentes y los métodos, está en el capítulo 09.

> **Trampa:** el error caro de un proyecto de datos casi nunca es un número mal calculado: es
> **contestar una pregunta que los datos no pueden contestar**. Si alguien pide «la cuota de
> mercado» o «la elasticidad» y no hay ventas, la respuesta profesional es esta tabla, no un
> modelo con supuestos heroicos.

## 5. El vocabulario mínimo

Para no perderse en los capítulos siguientes:

    producto     una ficha de una cadena: "Leche entera MILSANI 1 l" en Alcampo. Tiene
                 `fuente` (la cadena) e `id_fuente` (su identificador). Junto: `producto_id`.
    grupo        el mismo producto de verdad en varias cadenas, emparejado. Es lo que
                 permite comparar precios. `grupo_id` los une.
    EAN          el código de barras. Cuando dos fichas lo comparten, son **el mismo**
                 producto: es la verdad de referencia del proyecto.
    comparable   una ficha cuyo precio por unidad se puede comparar (unidad canónica, tamaño
                 fiable). Sin esto, un precio por kilo se compara con uno por unidad y sale
                 un disparate.
    gold         la capa que lee la aplicación, ya con grupos, calidades y precios por unidad.
    banco        los pares ciertos por EAN, que sirven para medir el emparejador sin
                 trampas. Es el equivalente a un *test set*, y no se toca al programar.

## 6. Lo que se aprende en este capítulo

- Un proyecto de datos empieza por **inventariar la fuente**, campo a campo, y por escribir
  lo que falta. `docs/CADENAS.md` es ese inventario, y se lee antes que el código.
- El tamaño de un dato no son las filas: 190 MB de vectores pesan más que 57.000 productos.
- La lista de **lo que no se puede concluir** es parte del entregable. Es lo que evita que
  alguien lea «dispersión de precios» como «poder de mercado», o una lista de la compra como
  una cesta de verdad.
