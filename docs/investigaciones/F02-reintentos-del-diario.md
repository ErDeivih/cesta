# F02 · Los reintentos del diario, y la clave que no impedía nada

Estado: **arreglado y probado en el cliente; falta el ensayo de navegador**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Reintento manual del diario»*.

> *«`Diario.tsx:Alta` genera UUID en cada submit. Backend deduplica por clave. […] Respuesta perdida
> seguida de pulsar otra vez: reutilizar operación pendiente; doble submit y carga idéntica con clave
> reutilizada. **La prueba de mismo UUID por HTTP no cubre la UX.**»*

---

## 1. El defecto, y por qué era peor de lo que decía el hallazgo

`Diario.tsx` generaba la clave **dentro del `onSubmit`**:

```jsx
const datos: NuevaEntrada = {
  clave_operacion: crypto.randomUUID(),   // ← se ejecuta en CADA envío
  fecha, comida, …
}
```

*El comentario que había encima decía*: *«Una clave por operación, generada al enviar. Va dentro de
`datos`, que es lo que se reintenta: si la respuesta se pierde y se repite, **la clave es la misma**»*.

**Y es falso.** «Va dentro de `datos`» describe un **reintento automático del mismo payload**; pero
**pulsar otra vez ejecuta el `onSubmit` otra vez**, y ahí se genera una clave nueva. *El tipo
`NuevaEntrada`, en `api/diario.ts`, repetía la misma creencia: «es lo que impide que un doble clic
duplique».*

**Y había dos cosas más, medidas:**

| | |
|---|---|
| `Diario.tsx:350` | `<Boton type="submit" disabled={apuntar.isPending}>` — *un doble clic **en vuelo** lo bloquea el `disabled`, **no la clave*** |
| `api/diario.ts` | **ninguna mutación declara `retry`** — *no existe reintento automático* |

**Conclusión, dicha sin adorno**: hoy `clave_operacion` **no impedía nada en la UX real**. *La clave
existía, el índice único existía y el servidor deduplicaba — probado en `tests/test_g01_diario_http.py`
— pero **el cliente nunca reenviaba la misma clave**.*

## 2. Y un segundo defecto en la misma línea, que rompía el formulario

`crypto.randomUUID` **sólo existe en contexto seguro** (https o localhost). *`api/cesta.ts:378` ya lo
documentaba y tenía respaldo con `getRandomValues`, porque **esta aplicación se sirve por http en el
8080, también por la IP de Tailscale**: ahí no está definido.* **El diario llamaba al método a pelo**, así
que por esa IP «Anotar» reventaba.

---

## 3. Lo que se ha hecho

**`logica/operacionPendiente.ts`**, sin dependencias —*como `chispa`, `gasto`, `costeReceta` y
`recetario`, que es lo que permite probarlo con `node --test`*:

    claveNueva()                    un uuid v4, tambien donde `crypto.randomUUID` no existe
    sello(datos)                    la huella estable del payload, con las claves ordenadas
    esReintento(pendiente, datos)   ¿esto es reintentar lo mismo?
    resolver(pendiente, datos)      la clave de esta operacion: la de antes si es lo mismo

**La regla**: *si vuelve a enviarse **lo mismo**, lleva la misma clave; si cambia algo del formulario,
es otra operación y lleva clave nueva — cambiar lo escrito es cancelar lo anterior, y no hace falta un
botón para eso.* **Y al confirmar se olvida**, para que dos meriendas iguales de verdad sigan siendo
dos: *el servidor ya prueba esa mitad por su lado.*

**Y el payload se construye SIN la clave**, que la añade `resolver` al final. *No es cosmético: si la
clave fuera dentro del payload que se compara, el sello daría siempre distinto y la regla nunca
reconocería un reintento.*

**`Diario.tsx`** guarda la operación pendiente en un `useRef` —*no se pinta, sólo tiene que sobrevivir
al repintado*—, y la olvida en `onSuccess`.

---

## 4. Cómo se comprueba

**Seis pruebas de cliente** en `tests/cocina.test.mjs` (42 en total, todas pasan):

    reintentar lo mismo reutiliza la clave, y sube el contador de intentos
    cambiar el formulario es otra operacion, no un reintento
    tras un alta buena, dos meriendas iguales siguen siendo dos
    el sello no depende del orden en que se escriban los campos
    el generador sirve tambien donde `crypto.randomUUID` no existe
    **el diario no genera la clave a mano: la decide la operacion pendiente**

**Y la última se ha comprobado discriminante**, que es lo que faltaba en otros cierres: *reintroduciendo
el defecto **en el código** —no en un comentario— la prueba **falla**; y el fichero se restauró y se
verificó.* **Es una prueba sobre el texto del fichero, y se hace a propósito: lo que hay que impedir es
exactamente esa línea.** *Se le quitan los comentarios antes de mirar, porque el fichero **menciona**
`crypto.randomUUID` para explicar por qué ya no lo usa — y la primera versión de la guarda falló por su
propia documentación.*

---

## 5. Y una cosa que el encargo pedía y no estaba: un comando que ejecute todos los tests del cliente

El encargo avisa: *«añadir/documentar un comando que ejecute **todos** los tests del cliente, no asumir
que cocina ya los recoge»*. **Medido**: hoy hay **un solo** fichero de pruebas del cliente
(`tests/cocina.test.mjs`), así que `test:cocina` **sí** las ejecuta todas. *Pero el nombre engaña y
dejaría de ser verdad con el segundo fichero.*

**Se añade `npm test`**, que las recoge por patrón: `node --test "tests/**/*.test.mjs"`.
*Y hay que decirlo porque **la primera versión no funcionaba**: `node --test tests/` —con la barra— da
`Cannot find module '…\tests'`, porque Node lo trata como módulo y no como carpeta que explorar.
**Lo cazó la ejecución, no la lectura.***

---

## 6. El ensayo de navegador — **y reproduce el defecto**

**Es lo que el encargo reclamaba con esas palabras**: *«la prueba de mismo UUID por HTTP no cubre la
UX»*. Está en `plataforma/prueba_reintento.py`, y **no prueba el módulo: prueba la pantalla**.

*El «servidor que guarda y pierde la respuesta» se monta sin tocar el código*: con
`route.fetch()` la petición **llega** y la entrada **se guarda**; con `route.abort()` el navegador **ve
un fallo**. Después se pulsa otra vez, ya sin interceptar.

**Lo que mide, y son tres cosas distintas:**

```
ok  se interrumpio una respuesta, ni mas ni menos
ok  **el primer envio SI guardo** (la respuesta es lo que se perdio): 0 -> 1
ok  el boton vuelve a estar activo: el reintento es posible
ok  hubo dos envios del alta (2)
ok  **los dos envios llevan la MISMA clave**
ok  **y el dia acaba con UNA entrada, no dos**: 0 -> 1
```

**Y se ha comprobado que discrimina**, que era lo que faltaba en otros cierres: simulando la regla
anterior —`resolver(null, …)`, que da clave nueva en cada envío— **el ensayo falla, y reproduce el
defecto entero**:

```
FALLA **los dos envios llevan la MISMA clave**
FALLA **y el dia acaba con UNA entrada, no dos**: 1 -> 3
```

**Dos entradas de más en una sola pantalla, contadas en el navegador.** *El fichero se restauró y se
verificó.* **Es la primera vez en esta fase que un defecto se reproduce y se arregla en la UX y no sólo
en el motor.**

*Y costó dos intentos:* la primera versión usaba `get_by_role("button", name="Anotar")`, que resolvía a
**dos** botones —«Ver que se puede **anotar**» también contiene «anotar», y la coincidencia por defecto
es por subcadena—. Se arregla con `exact=True`.

---

## 7. La carrera del diario — y **por qué el `UPDATE` de después era el defecto**

El encargo lo dejó escrito como hallazgo: *«clave de diario escrita tras el INSERT»*. **Y era
exactamente eso.** `core/diario.py:apunta` hacía:

```
1. SELECT por (propietario, clave_operacion)   -> si estaba, se devuelve
2. INSERT  ... SIN la clave
3. UPDATE  ... poniendo la clave               <- después
4. commit
```

**Con dos envíos a la vez, los dos pasos 1 no ven nada** —ninguno ha escrito todavía—. Los dos insertan
su fila. Y al poner la clave, el índice único parcial
`(propietario, clave_operacion) WHERE clave_operacion IS NOT NULL` **rechaza al segundo**. *No se
deduplica: **falla**. Y la fila del que falla se queda sin clave, que es peor que fallar: una entrada
que ya no se puede reconocer como repetida.*

**Reproducido, y de forma determinista** (`tests/test_fase2_f02_concurrencia.py`, dos conexiones y una
barrera —*que es lo que hace que sea una carrera y no una cola*—):

```
ANTES   F..   1 failed, 2 passed
        IntegrityError: UNIQUE constraint failed: entrada.propietario, entrada.clave_operacion

DESPUES .....  5 passed
```

**La reproducción fue la prueba de que discrimina**: el ensayo falló antes del arreglo y pasa después,
sin necesidad de simular nada.

**El arreglo: una sola escritura.** La clave va **dentro del `INSERT`**, con
`ON CONFLICT (propietario, clave_operacion) WHERE clave_operacion IS NOT NULL DO NOTHING`. *El
`WHERE` es obligatorio: el índice es parcial, y el destino del conflicto tiene que repetir su
predicado o SQLite no lo reconoce.* **El que no inserta lee la fila del otro y la devuelve.**

---

## 8. Y la misma clave con **otros** datos

Tercer punto de F02: *«misma clave con payload distinto produce conflicto o política explícita, **no
éxito que parece guardar otro dato**»*. **Lo que hacía era lo peor de los dos mundos**: el `SELECT`
encontraba la fila y **devolvía su id en silencio**, así que quien lo pidió creería haber anotado lo
suyo mientras en el diario estaba lo de antes.

**Ahora se compara el contenido**: si es el mismo reintento se devuelve su id —*que es lo que hace que
un envío repetido no duplique*—, y **si la clave se reutilizó con otros datos se dice**.
`plataforma/api/diario.py:103` convierte el `ValueError` en **400 con el motivo**, así que la política
llega al HTTP y no se queda en el motor.

*Dos cuidados que tienen prueba propia:*

- **`None` y `''` no son un cambio** — `referencia` y `nota` pueden llegar de las dos formas.
- **`0` no es lo mismo que `None`** (`test_un_cero_no_es_lo_mismo_que_no_saberlo`): *es la misma regla
  que el resto del diario — dejar un campo en blanco no es anotar cero —, y si se compararan como
  iguales, un reintento que corrigiera un dato a `0` se tomaría por el mismo y la corrección se
  perdería.*

*El cliente no puede llegar a este caso* —su regla, probada en `tests/cocina.test.mjs`, es que un
payload distinto lleva clave nueva—, **pero el servidor no puede depender de que el cliente sea
correcto.**

---

## 9. Lo que queda de F02

1. **Cantidad, unidad y base**: g, ml y raciones con conversiones trazables —*que SQLite tenga columna
   `unidad` no acredita API, cálculo ni interfaz*—, y **consumir parte del envase, no la compra entera
   por defecto**.
2. **La vista previa congelada** a compra/líneas y receta/versiones, con revalidación al cambiar.

*El reintento está hecho, **verificado en la UX** y **con la carrera arreglada**; lo demás está
enumerado arriba.* **No se declara F02 cerrado por tener verdes las tres cuartas partes.**

---

## 10. Y para volver a correrlo

Necesita la API y la interfaz levantadas, **con la interfaz sirviendo el código de hoy**:

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099
    cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev
    $env:CESTA_UI='http://localhost:5173'; uv run python -m plataforma.prueba_reintento

*Los datos son de la base desechable y de la cuenta `prueba-navegador`.* **No toca el diario de casa.**
