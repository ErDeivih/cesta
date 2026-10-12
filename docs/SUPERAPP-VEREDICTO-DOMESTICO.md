# Veredicto: ¿sirve para uso doméstico local?

*(13 de octubre de 2026. **El encargo pide «un veredicto honesto sobre uso doméstico local», y esto es lo
único que puede ser: lo que las mediciones sostienen y lo que no.**)*

**La pregunta, en una línea**: *¿puede una casa usar esto para decidir su compra semanal, sabiendo lo que
sabe y no sabiendo lo que no sabe?*

**Y la respuesta corta, para quien no lea más**: **sí, para lo que está medido; y no, para lo que la
columna izquierda de la [matriz de aceptación](MATRIZ-DE-ACEPTACION.md) deja en blanco.** *Las dos partes
están abajo, y la segunda es más larga a propósito.*

---

## 1. Lo que se puede decir que funciona, con su prueba

*Nada de esto es una impresión: cada línea tiene una medición detrás.*

| capacidad | **prueba** |
|---|---|
| **Compra: el recorrido entero** | *dos personas del mismo hogar comparten una lista, las dos añaden, las dos ven, se cierra y queda el histórico* -- 7 pruebas contra el Postgres de verdad |
| **Compra: aceptar una alternativa** | *se acepta, se guarda **qué** se aceptó, se revoca, y revocar no toca la línea de al lado* -- 5 pruebas |
| **Compra: el descuento de cesta** | *el 3×2 repartido entre las líneas sin perder un céntimo*, con descuentos **no divisibles** a propósito |
| **Envío de envases** | *1,4 kg con envases de 1 kg → **2 envases y 600 g***, por el recorrido entero, del ingrediente al número |
| **Búsqueda y paginación** | *el desplazamiento en la URL, y no se puede ordenar la página* -- con una prueba que lee el fuente y lo exige |
| **Frescura** | *la fecha del **producto**, no la de la cadena*, con reloj inyectable |
| **Identidad entre cadenas** | *las 5 fichas reales del grupo 11627, y **ninguno de los 10 pares sale exacto*** -- el motor y la revisión dicen lo mismo |
| **La interfaz** | *390/768/1440 px, claro y oscuro, zoom al 200 %*: las doce combinaciones sin desbordar |
| **La copia** | *volcado de 30 515 bytes, **restaurado**, contenido 2/2 · 10/10 · 2/2, y la sustitución conservada* |
| **El conjunto** | **1 989 pruebas de Python, 74 de interfaz, 0 fallan, 0 se saltan, 0 `xfail`**; `ruff`, `tsc` y el build limpios |

**Y las cinco `xfail` que la fase 2 arrastraba están las cinco arregladas.** *Ninguna se dejó marcada.*

---

## 2. Y lo que **no** se puede decir, que es lo que decide

### 2.1 **El catálogo está parado, y eso lo cambia todo**

```
/api/estado -> version 20261007-103000 · fecha_datos 2026-10-11
               vigencia_precio.coherente = false
/api/estado/publicacion -> coherente: None · no_cuadran: [] · seis sin_huella
```

**La versión servida se llama «7 de octubre» y sus precios son del 11.** *Y la ingesta de hoy **empezó y se
interrumpió*** -- *bronze lo prueba: Aldi 12:26, Mercadona 12:26, DIA 12:37; **Alcampo y Carrefour siguen
con datos del 11**.*

> **Qué significa para una casa**: *los precios que ves pueden ser de hace días, y **la aplicación no puede
> saber si están desajustados** porque el puntero es anterior a las huellas.* **`coherente: None` no es un
> aprobado: es un «no se sabe».**

**Y esto no es un defecto del código**: *es que **el catálogo no se ha vuelto a publicar bien**.* *El
defecto que sí había -- el enlace duro que hacía cambiar una versión publicada -- está arreglado y con
prueba.* **Pero arreglarlo no publica nada.**

### 2.2 **La nutrición: 28–30 % de la comida, y una cadena que no aporta nada**

```
sobre la comida (36 989 de 52 087 filas, el 71 %):
    energia    techo 29,8 %   suelo 28,0 %
por FUENTE:  alcampo 23 128 filas -> 0 kcal, 0 ingredientes
             aldi     2 768 filas -> 0 kcal, 0 ingredientes
             carrefour 16 195 -> 6 512 kcal, 0 ingredientes
             dia 5 783 / mercadona 4 213  <- las DOS UNICAS con ingredientes
```

> **Qué significa para una casa**: *siete de cada diez productos de alimentación **no tienen ni una
> caloría** en el catálogo.* **Y la cadena más grande no aporta ninguna.**
>
> *Las calorías y las recetas funcionan para DIA y Mercadona, y para poco más.* **Decir «hay nutrición» sin
> decir esto sería vender lo que no hay.**

### 2.3 **La cola: 72 319 fichas pendientes, y 43 603 son de Alcampo**

*Y 5 026 de Lidl con 28 hechas.* **La cola y la cobertura cuentan la misma historia**: *las dos cadenas con
la cola más parada son las dos que no aportan ni una caloría.*

**Y no hay presupuesto**: *no se ha estimado cuánto cuesta una pasada ni cuántas caben por día.* *Así que
«pendiente» no dice cuánto falta.*

### 2.4 **Lidl: capturada y no comparable** -- *y está bien que lo esté*

*A05 lo dejó escrito con su motivo*: **Lidl publica ofertas semanales parciales**, y meterlo en las
comparaciones haría que pareciera tener precio para cosas que no cataloga. **La decisión es correcta y está
en el código** (`CADENAS_QUE_SE_CAPTURAN` frente a `CADENAS`). **Pero es una cadena menos de la que se
puede comparar.**

### 2.5 Y las tres cosas que **no se han medido**, dichas como tales

- **CSRF**: *la matriz lo dice desde antes de esta fase y **sigue sin verificarse**.* *En local, mismo
  origen, da igual; **al publicar deja de dar igual**.*
- **La copia no está programada.** *`respaldar.bat` **se puede** dar de alta como tarea diaria -- lo dice su
  cabecera --, y **no se ha dado de alta**.* *Y en el mismo disco.*
- **El recorrido de A09 con «controles, textos y errores reales, no sólo conteo de píxeles»**, y las
  capturas con commit/imagen/versión. *Tampoco.*

---

## 3. El veredicto

> **Sirve para uso doméstico local, con dos condiciones que no son del programa sino del catálogo, y con
> tres cosas sin medir que no impiden usarlo pero sí impiden confiar en él a ciegas.**

**Lo que sí, y con prueba**: *la lista de la compra -- compartida, con alternativas aceptadas y
revertidas, con el descuento repartido al céntimo y con los envases enteros calculados -- funciona y está
probada. La interfaz se lee en un móvil y a doble zoom. La copia se restaura.*

**Lo que hay que saber antes de fiarse**:

1. **Los precios pueden estar viejos y la aplicación no puede saberlo.** *Hoy lo dice: `coherente: None`.*
   **Lo dice, que es lo importante** -- *una aplicación que dijera «todo bien» aquí sería peor que una que
   no dijera nada.*
2. **La nutrición y las calorías valen para lo que valen**: *dos cadenas de cinco para los ingredientes,
   tres para la energía, y **Alcampo y Aldi para nada**.*
3. **Y las recetas y el diario se apoyan en eso**, así que heredan el límite.

**Y lo que no se puede afirmar de ninguna manera**: **que esté listo para que lo use alguien de fuera.**
*La matriz lo dice con su propia regla: la mitad de la columna derecha son cosas sin hacer y una -- CSRF --
sin verificar.* **Y el catálogo parado lo empeora**: *un usuario de fuera no tiene forma de saber que los
precios son de hace días.*

---

## 4. Lo que haría falta para cambiar este veredicto

*Por orden de lo que más pesa, y no por lo que más fácil sería:*

1. **Publicar el catálogo**, y que `coherente` deje de ser `None` -- *o sea: que la ingesta termine y se
   publique, y que el puntero lleve huellas.* **Sin esto, todo lo demás se apoya en precios que no se sabe
   de cuándo son.**
2. **El presupuesto de la cola**: *cuántas de las 72 319 fichas caben por día y cuánto se tarda.* **Sin
   esto, «pendiente» no tiene fecha.**
3. **Dar de alta `respaldar.bat` como tarea diaria** -- *que es una decisión, no un trabajo.*
4. **Y las tres sin medir**: *CSRF, el recorrido de A09 con errores reales, y las capturas.*

**Ninguna de las cuatro es un defecto encontrado: son las cuatro cosas que las mediciones de esta fase
dejaron a la vista.** *Que es exactamente lo que una matriz y un veredicto tienen que hacer.*
