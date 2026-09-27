# Encargo: que Cesta sea de verdad una ayuda

23 de septiembre de 2026. El encargo anterior (`TAREAS-22SEP.md`) iba de que el
dato fuera cierto. Éste va de lo siguiente: **que sirva para algo a la persona
que la abre**. Son cosas distintas y la segunda no sale sola de la primera.

---

## 0. El cambio de marco

Cesta hoy **enseña datos**. Lo que hace falta es que **conteste preguntas**.

Nadie abre una aplicación de precios pensando «quiero ver el índice de Jevons
encadenado». Se abre con una de estas cuatro preguntas en la cabeza, y **todas
las pantallas existen para contestar una de ellas**:

```
1  ¿Qué me falta y dónde lo compro?         en casa, antes de salir
2  ¿Esto que tengo en la mano está caro?    en el pasillo, con el carro
3  ¿Voy tachando bien?                      en el pasillo, una mano ocupada
4  ¿Ha bajado algo de lo mío?               entre compras, sin abrir nada
```

La prueba de aceptación de todo este encargo es una sola, y no es un número de
cobertura: **coger el móvil, abrir Cesta y contestar cada una de las cuatro en
menos de quince segundos, sin saber de antemano dónde está el botón.** Si hace
falta explicárselo a alguien, no está hecho.

Y hay una quinta persona a tener en cuenta que no es David: **su madre**. No va a
leer ninguna ayuda, no va a explorar menús, y si algo no se entiende a la primera
no lo va a preguntar: va a dejar de usarlo. Todo lo de abajo se juzga contra
ella, no contra quien escribió el código.

---

## 1. Lo que ya está bien y no hay que tocar

Para que nadie lo deshaga buscando mejorar:

- **El contraste y los límites de los campos**, con las fórmulas dentro de las
  pruebas. Eso es accesibilidad de verdad y está medida.
- **La privacidad**: ninguna interfaz carga nada de un tercero, y hay prueba.
- **La fecha del dato en la cabecera**. No es decoración: es la regla que
  atraviesa la aplicación entera.
- **La explicación del emparejamiento** en la ficha de grupo.
- **Las cifras tabulares** en las columnas de precio.
- **El tema por `prefers-color-scheme`, sin interruptor.** Un botón de tema es
  una cosa más que mantener y que nadie pulsa dos veces.

---

## 2. Lo primero: la primera vez

**Esto no lo ha mirado nadie y decide si alguien vuelve.**

Hoy, cuando una persona nueva se registra, entra y ve: un buscador vacío, una
cesta vacía, unos favoritos vacíos y un panel de índices que no significa nada
sin contexto. Ese es el peor momento posible de la aplicación y es el único que
todo el mundo ve.

**Qué hacer.** En la primera sesión —y sólo en la primera— la pantalla de inicio
tiene que enseñar de qué va esto con **datos reales**, no con texto:

- tres o cuatro productos de los que todo el mundo compra (leche, aceite, papel
  de cocina, huevos) con **su diferencia real entre cadenas de hoy**;
- un botón grande de **«empieza tu lista»**;
- y una línea, una sola, diciendo qué es Cesta: *«los precios de cinco
  supermercados, actualizados esta mañana en el ordenador de casa»*.

**Cómo se acepta.** Una persona que nunca la ha visto añade su primer producto a
una lista **sin que nadie le diga dónde pulsar**. Si hace falta decírselo, se
rehace.

**Qué no.** Nada de visita guiada con flechas ni de pantallas de bienvenida que
hay que pasar. Se enseña la aplicación funcionando, no un folleto sobre la
aplicación.

---

## 3. La lista, que es la pantalla que de verdad se usa

Todo lo demás se mira de vez en cuando. **La lista se usa cada semana, de pie, en
movimiento y con una mano.** Merece más cuidado que el resto junto.

### 3.1 Separar «por coger» de «en el carro»

Ya está en la lista de pendientes y es lo más valioso de esta pantalla. Con nueve
líneas y cuatro cogidas hay que leer nueve nombres para saber qué falta. La
columna `en_carrito` existe en la base desde `002_invitaciones.sql` y se creó
justo para esto.

- Lo que falta, arriba y grande.
- Lo cogido, abajo, encogido y en gris, con un contador: *«4 en el carro»*.
- Y **se puede volver a sacar** de un toque, porque todo el mundo se equivoca.

**Se acepta** cuando, con la lista a medias, se sabe qué queda **sin leer ningún
nombre**: se ve por la forma.

### 3.2 El orden por pasillos, hasta el final

El orden por pasillo ya existe en el dato (19 secciones). En la pantalla tiene
que verse como lo que es: **el recorrido de la tienda**, con el nombre del
pasillo como separador pegajoso mientras se recorre. Quien va por «Lácteos» tiene
que saber que va por lácteos sin buscarlo.

### 3.3 La zona del pulgar

Lo que se toca con el carro en marcha —tachar, sumar uno, quitar uno, meter en el
carro— va **abajo y grande**. Las siete zonas por debajo de 44 px que están
medidas son sólo el mínimo legal: en la lista, el objetivo no es 44, es que se
acierte **sin mirar**.

### 3.4 Deshacer, siempre

Tachar sin querer pasa. Borrar una línea sin querer pasa. **Cada acción
destructiva deja un «deshacer» durante unos segundos**, y ninguna pide
confirmación: confirmar cada toque es peor que deshacer el que sobra.

### 3.5 Que no se note cuando no hay cobertura

El supermercado es donde peor va la red y es donde se usa la lista. La mecánica
ya está resuelta —el identificador de línea lo genera el móvil, cada cambio viaja
con su hora—, pero **en la pantalla no se ve**. Hace falta:

- que tachar funcione igual sin red, sin ruedecita ni error;
- una línea discreta cuando hay cambios sin subir: *«3 cambios se subirán al
  volver la cobertura»*;
- y que al volver, se suba solo y se diga en una frase.

**Qué no:** un aviso rojo de error. Estar sin cobertura en un supermercado no es
un fallo de la aplicación.

---

## 4. Contestar «¿esto está caro?» en un vistazo

Es la pregunta 2 y hoy la aplicación la contesta **con una tabla**. Una tabla no
es una respuesta.

**Lo que hace falta** en la ficha de un producto, en este orden y de arriba
abajo:

1. **Una frase**, no un número: *«Es el más barato de las cinco»* / *«Cuesta un
   18 % más que en DIA»* / *«No puedo compararlo: no lo encuentro en otras
   cadenas»*.
2. **Dónde está más barato** y cuánto se ahorra en euros por unidad de uso, no
   en porcentaje abstracto.
3. **La curva**, que ya existe, con una frase debajo: *«lleva 14 días a este
   precio»* o *«está más barato que en los últimos 90 días»*.
4. Y sólo después, la tabla para quien quiera mirar.

**La regla que no se puede saltar:** si el grupo no es de fiar, la frase no se
inventa. Se dice: *«aquí hay productos que no estoy seguro de que sean lo
mismo»*, y se enseña la tabla sin recomendación. **Callarse con una explicación
es una respuesta; adivinar no.**

---

## 5. El mosaico de lo habitual, y `/api/habituales`

El agente dice, y tiene razón, que esto está bloqueado por la API. Va la
especificación completa para que no haya que diseñarla:

```
GET /api/habituales?limite=24
    pide sesion
```

**Qué devuelve.** Los productos que esta persona ha puesto más veces en sus
listas, con lo justo para pintar una tarjeta y añadirla de un toque:

```json
{ "habituales": [
    { "grupo_id": 4125, "nombre": "Leche entera 1 l",
      "imagen": "...", "veces": 9, "ultima_vez": "2026-09-16",
      "precio_unidad_cent": 98, "unidad": "l",
      "cadena_mas_barata": "dia", "fiable": true } ] }
```

**De dónde sale.** De `lista_linea` en PostgreSQL, no de gold: es historial de
esta persona. La consulta es un `count(*)` por `grupo_id` sobre las líneas de sus
listas, con dos cuidados:

- **Se cuentan las veces que se añadió, no las líneas vivas.** Una lista se
  vacía; el hábito no.
- **Pesa más lo reciente.** Algo comprado nueve veces hace tres meses no es
  habitual. Un decaimiento sencillo —contar sólo los últimos 90 días, o pesar por
  recencia— y escrito en el docstring por qué.

**Qué hace cuando no hay historial**, que es el caso del primer día y el que
suele quedar sin pensar: devuelve **lo más comprado por todos** (no hay datos
personales ahí: es un recuento agregado) o, si tampoco hay, una lista fija de la
compra básica. Y lo dice en un campo `origen: "tuyo" | "de todos" | "basico"`,
para que la pantalla pueda ser honesta: *«todavía no sé lo que sueles comprar»*.

**Cómo se acepta.** Añadir un producto habitual pasa de *escribir + elegir +
añadir* a **un toque**. Y con historial vacío la pantalla **no se ve vacía**.

---

## 6. Los avisos, que hoy no avisan

Sigue sin arreglarse y es mío: `alertas.evalua()` sólo corre cuando alguien abre
`GET /api/alertas`. La alerta salta **si entras a mirar**, que es lo contrario de
para lo que existe.

- Evaluarlas **en la cadena diaria**, después del pipeline.
- Dejar el resultado guardado, para que abrir la aplicación sea instantáneo.
- Que el resumen diario diga cuántas saltaron.
- Y en la pantalla: un punto en el icono, y al abrirlo **la frase entera** —*«el
  aceite que sigues está a 3,89 €/l en Alcampo, el más barato en 90 días»*—, no
  un número rojo sin contexto.

Y la regla que ya está escrita en el módulo: **una alerta se dispara una vez**.
Un aviso que se repite todos los días deja de leerse.

---

## 7. La honestidad, que es lo que nos diferencia

Esto no es una sección de diseño, es la identidad del producto, y en la pantalla
se juega entera:

- **Un precio sin fecha es una afirmación falsa.** Lo que no sea de hoy lleva su
  día; lo de más de tres días se ve pero **no decide dónde comprar**.
- **Nunca «antes 3,00 / ahora 2,50» con aspecto de oferta.** El movimiento se
  enseña como movimiento: *«lleva 14 días a 3,00 y hoy está a 2,50; el mínimo de
  los últimos 90 días fue 2,45»*. Lo primero es vender, lo segundo es informar.
- **Un descuento de tarjeta no baja lo que se paga en caja**, y por eso no baja el
  precio. Cuando exista, se enseña aparte y etiquetado.
- **Un grupo del que no estamos seguros no recomienda tienda.** Con la invariante
  de cadena repetida esto ya es barato de saber.
- **Cuando la aplicación se calla, dice por qué.** Un hueco sin explicación se
  lee como un fallo; una frase corta se lee como honestidad.

---

## 8. Los detalles que hacen que parezca terminada

Ninguno es grande. Juntos son la diferencia entre «un proyecto» y «una
aplicación»:

- **Los estados vacíos**, todos, con una frase que diga qué falta y qué hacer.
  El «Nada con «».» de un pasillo vacío fue un fallo real.
- **Los estados de carga**: nada de saltos de maquetación. Un hueco del tamaño de
  lo que va a venir.
- **Los errores**: *«no llego a casa»* en vez de *«Network error»*, y un botón de
  reintentar.
- **El buscador**: que encuentre con faltas de ortografía y sin tildes (ya se
  normaliza en el dato), que recuerde las últimas búsquedas y que no exija pulsar
  una lupa.
- **Los números**: euros con dos decimales y coma, cantidades sin decimales
  inútiles, y **siempre la unidad al lado**. Un `1.5` suelto no es un dato.
- **El título de cada pantalla** en la pestaña, para quien la tenga abierta entre
  otras diez.
- **Volver atrás** funciona siempre, y `/favoritos` y `/ajustes` ya tienen enlace
  — bien.

---

## 9. Lo que me pedís, contestado

**(a) El barrido de las 28 mejoras restantes del estudio.** De acuerdo en que es
mecánico, pero **no lo voy a hacer en paralelo en el front**: ya nos mezcló el
árbol una vez y tenéis razón en no querer repetirlo. Lo que sí puedo hacer sin
tocaros nada: revisarlas en el navegador y devolver los defectos con su medida,
como hice con los grupos, para que el arreglo lo hagáis vosotros en un solo sitio.

**(b) `/api/habituales`.** Especificada entera en el punto 5, incluido lo que
suele quedar sin pensar: qué devuelve cuando no hay historial.

**(c) La cohesión contra el medoide.** Sigue valiendo como **segunda red**, y
ahora con un papel más claro: la invariante de cadena repetida caza lo que se
funde *entre* cadenas, y no ve lo que se funde *dentro* de un grupo legítimo de
cinco. Spec corta:

> Para cada grupo, el medoide es el miembro con mayor parecido medio al resto.
> Un miembro cuyo parecido al medoide esté por debajo de `UMBRAL_COHESION` sale
> del grupo. Se itera hasta que nadie se mueva.
>
> **El umbral no se elige a ojo**: se calibra sobre el banco de pares, buscando
> el valor que no expulse a ningún par con EAN compartido. Si expulsa a alguno,
> está mal puesto.

Con grupos de seis productos como mucho, esto ya no es lo urgente. Es la red por
si el bloqueo se afloja algún día.

---

## 10. Lo que he tocado yo hoy, para que no se busque

**`extension/contenido.js` y `tests/test_extension.py`.** La prueba de Alcampo
estaba en rojo y **no era del `secciones.yml` de nadie: era mía**.

Con el primer bronze bueno de Alcampo se ha visto una segunda forma de URL que no
existía en los datos viejos: **lo que se corta en el mostrador lleva el corte
pegado al identificador**.

```
products/39529-TROZO
products/90012-TAPEO-3-A-5-MM
products/94846-LONCHA-NORMAL-2-A-3-MM
```

Y ese sufijo **es parte del `id_fuente`**, no un adorno de la dirección. Son 335
de 23.842 productos (1,4 %): todo el mostrador de quesos y embutidos, que es
justo donde alguien se para a comparar. El patrón pedía dígitos hasta el final
del segmento, así que en esas 335 fichas la extensión se quedaba muda.

Arreglado admitiendo un sufijo en MAYÚSCULAS dentro de lo capturado. Comprobado
sobre las 23.842 URL de hoy: **las reconoce todas y el identificador que saca es
exactamente el `id_fuente` en las 23.842**. La URL vieja con UUID sigue
rechazada, que era el punto del patrón original.

`pytest tests/test_extension.py` → 14 pasan, ninguna se salta.

---

## 11. Y la buena noticia del día

**Las cinco cadenas han escrito bronze el mismo día**, por primera vez desde el
21 de septiembre:

```
aldi 2.066 · mercadona 4.325 · dia 5.809 · carrefour · alcampo 23.842
```

Es la quinta condición de la barra, y estaba en «por comprobar». Ya no.
