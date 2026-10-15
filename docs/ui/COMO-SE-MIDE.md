# *** Cómo se mide aquí, *y las cuatro veces que medí mal *** *

*Existe porque en **una sola sesión** me salieron **cuatro falsos negativos**, *y los
cuatro eran **de medir**, no de que algo estuviera roto.* *Un falso negativo es **peor que
un fallo**: *un fallo te hace mirar, *y un falso negativo te hace **concluir**.*

---

## 1. *** Pipeline en PowerShell *-> el código de salida se pierde ***

```
*** MAL ***: *`uv run python -m plataforma.prueba_e2e 2>&1 | Select-Object -Last 25` *
   *-- *el `2>&1` mete el **stderr** de `uv` *(-- un `StarletteDeprecationWarning` --)*
      *en la tuberia, *PowerShell lo marca **`NativeCommandError`** *y **el codigo sale 1**
      *aunque el programa haya salido 0 ⚠️
*** BIEN ***: *redirigir a un fichero, *y **preguntar `$LASTEXITCODE`**: *
   `uv run ... > $env:TEMP\x.txt 2>&1; $LASTEXITCODE` ✓
*** -> *y asi se supo: *** el E2E sale 0 y dice `== TODO BIEN` *** ✓
```

## 2. *** `lazy(() => import(...))` *no lleva `from` ***

```
*** MAL ***: *buscar los ficheros vivos con `from '...nombre'` *
   *-- *la app carga las pantallas con `lazy(() => import('./paginas/X'))`, *y **esa
      *forma no lleva `from`** ⚠️
   *-- *resultado: *** 80 muertos de 160 ***, *con `Cesta`, `Buscar`, `ui` y `Suite`
      *dentro, *que **se ven en pantalla** ✓
*** BIEN ***: *`(?:from|import)\s*\(?\s*['"]…['"]` *
   *-- *y el censo bueno: *** 3 muertos de 82 *** ✓✓✓
```

## 3. *** El CSS construido no se escribe como el fuente ***

```
*** MAL ***: *buscar `translateX(-100%)` en el CSS que se sirve, *y ver **NO**, *
   *y concluir que la animacion estaba rota ⚠️
*** BIEN ***: *el minificador lo reescribe a `translate(-100%)`, *que es **equivalente**
   *-- *`translate()` con un argumento **es el eje X** ✓
*** -> *lo mismo paso con `tinta-suave` al principio: *se buscaba donde no era ✓✓✓
```

## 4. *** `newline` en Windows *no conserva: *impone ***

```
*** MAL ***: *`Path.write_text(...)` a secas, *y un fichero *** LF *** pasa a *** CRLF *** ⚠️
*** MAL TAMBIEN ***: *`write_text(..., newline="\n")`, *y un fichero *** CRLF *** pasa
   *a *** LF *** ⚠️
*** -> *las dos veces mal, *y las dos veces el diff salio **del tamano del fichero
   *entero** *en vez del tamano del cambio* ✓
*** BIEN ***: *leer los **bytes**, *mirar que final tenian, *y devolverlos **con ese
   *mismo** ✓✓✓
*** -> *y hacia falta: *en `src/` hay *** LF y CRLF mezclados *** *-- *`Panel` y `Producto`
   *en LF, *`Grupo` y `RepartoEnTiendas` en CRLF, *y asi -- ✓
```

---

## *** Y la regla que sale de las cuatro ***

```
*** un resultado ROTUNDO es sospechoso ***: *
   *-- *«80 muertos de 160» *-- *y los cuatro ficheros clave estaban a la vista ✓
   *-- *«TOTAL: 0 clases» en ficheros que **tenian** clases ✓
   *-- *«`translateX` NO» en una animacion que **funciona** ✓
*** -> *cuando el numero cuadra demasiado, *o sale **cero**, *o sale **todo**, *
   *lo que hay que revisar es *** la medida ***, *no el sistema ✓✓✓
```

*Y una comprobacion mas, *que es la misma idea: *** comprobar en el sitio equivocado
da un falso negativo ***, *y el sitio equivocado casi siempre es **el fuente cuando hay
que mirar lo construido** *-- *o al reves.* *
