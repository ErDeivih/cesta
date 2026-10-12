---
seccion: Algoritmos y evaluación
resumen: Seis fallos que pasaron de verdad, con el código donde viven y cómo se reproducen. Ninguno dio error.
en_una_frase: Los fallos que duran no fallan: devuelven None, un cero o un True por defecto.
---

# 17 — Fallos reales de este proyecto, con su reproducción

**Por qué este documento existe, y por qué es distinto de los demás.**

*Los dieciséis anteriores explican **cómo se hace** cada cosa: la extracción, la ingeniería del dato, las
unidades, el emparejador, los índices.* **Este explica cómo se rompió.**

**Y la razón está escrita en la revisión del 12 de octubre de 2026, con estas palabras:**

> *«Hay material educativo en `docs/aprende` [...] **Debe completarse con ejemplos reales de estas
> carencias, no con una descripción ideal que afirme cobertura conseguida.**»*

*Un material que enseña el método y no los fallos enseña una versión del trabajo que no existe.* **Todos
los casos de aquí pasaron de verdad**, y cada uno lleva **el código donde vive**, **la medición que lo
detectó** y **cómo se reproduce**.

**Y ninguno se cuenta como una anécdota.** *Cada uno tiene una lección que se puede aplicar a otro
problema, y esa lección está dicha al final de su caso.*

---

## 1. El enlace duro que hacía que una versión publicada cambiara sola

**Dónde**: `core/publicacion.py`, `publicar()`.

**Qué pasaba.** *El catálogo se publica «por versiones»: cada publicación escribe sus ficheros en una
carpeta propia y luego mueve un puntero.* **Y para no duplicar los ficheros, los publicaba con
`os.link`** -- *un enlace duro* --, con este comentario:

```python
# Enlace duro: no se duplica un fichero de 195 MB para versionar.
```

**Lo que se midió**, con una orden de Windows:

```
fsutil hardlink list data\gold\precio_diario.parquet
    \aprendizaje\scrap\data\gold\v20261007-103000\precio_diario.parquet
    \aprendizaje\scrap\data\gold\v20261011-124542\precio_diario.parquet
    \aprendizaje\scrap\data\gold\precio_diario.parquet
```

**Tres nombres, un fichero.** *Y el enlace seguía **intacto*** -- *lo que prueba que el proceso que
reescribe el catálogo lo hace **in situ**, no escribiendo un fichero nuevo y renombrando.*

> **La consecuencia**: *la versión `v20261007-103000` se **llama** 7 de octubre y su contenido **es** del
> 11.* **Una versión publicada dejó de ser inmutable**, porque compartía almacenamiento con el fichero
> vivo.

**La lección, que vale para cualquier sistema de versiones**: *una versión publicada tiene que ser
**inmutable por sí misma**, no por la buena conducta de quien escriba el original.* **Ahorrarse una copia
con un enlace duro es ahorrarse la garantía.**

**Y una segunda lección, sobre la frase**: *«195 MB» era falso* -- *el fichero mayor son 19,2 MB.* **Un
número inventado en un comentario justificó una decisión equivocada durante meses.**

---

## 2. El detector que funcionaba y no bastaba

**Dónde**: `plataforma/api/main.py`, `_vigencia()`.

**Qué pasaba, y es lo interesante de este caso: el detector estaba BIEN.**

```python
coherente = fecha_precio <= dia_publicacion
```

*Con el precio del 11 y la publicación del 7, `11 > 7`, y devolvía `false`.* **`/api/estado` lo decía.**

**Y no bastaba**, por una razón que se ve mirando el caso anterior: *sólo lo delató **porque el día del
precio iba por delante**.* **Al revés no se habría notado** -- *una versión con contenido ajeno y fecha
compatible habría pasado por buena.*

**Lo que se añadió**: *la **huella SHA-256** de cada fichero en el puntero, y una ruta que la comprueba*
-- `/api/estado/publicacion`.* **Y con ella, la respuesta distingue tres estados y no dos:**

```
coherente: None     <- NO SE SABE. El puntero es anterior a las huellas.
no_cuadran: []      <- y nada esta desajustado.
```

> **La lección**: *«no se sabe» y «está bien» se escriben casi igual en un informe, y son lo contrario.*
> **Y `None` es la única respuesta honesta cuando no hay con qué comprobarlo** -- *devolver `True` habría
> sido afirmar lo que no consta.*

**Reproducción**: `uv run pytest tests/test_revision_a01_publicacion.py -q` -- *10 pruebas, y ninguna toca
el catálogo real.*

---

## 3. El cálculo que estaba escrito y nunca se ejecutaba

**Dónde**: `core/previa_compra.py`, `_tamano_del_envase()`.

**Qué pasaba.** *La previa de la compra calcula cuántos envases enteros hay que comprar y cuánto sobra.*
**Y para saber el tamaño del envase, le preguntaba a `core/envases.py`:**

```python
cantidad = leido.get("cantidad") if isinstance(leido, dict) else getattr(leido, "cantidad", None)
```

**Y `envases.lee` no devuelve un diccionario: devuelve una tupla.**

```python
def lee(bruto) -> tuple[str | None, int | None]:
    """Lo que escribe la cadena -> (envase nuestro, unidades del pack)."""
```

**Resultado**: *`isinstance(leido, dict)` es falso, `getattr(tupla, "cantidad", None)` da `None`, y el
`if tamano and tamano > 0` **nunca entra**.* **Ni `envases` ni `sobrante` se calculaban jamás.**

> **Y aquí está la parte que importa**: *ninguna prueba lo notaba, porque **la función no fallaba**:
> devolvía `None`, que es un resultado válido.* **Una regla que existe, se ejecuta y no hace nada es la
> clase de defecto que sólo se caza mirándola.**

**La segunda capa del mismo error**: *aunque se hubiera arreglado el `dict`, seguiría dando `None`* --
*`envases.lee` **nunca devolvió un tamaño**: lee «botella», «malla», «Pack-6», que son **el tipo de envase y
cuántas unidades van dentro**.* **El dato no estaba donde se le pedía.**

**La lección**: *antes de arreglar una conversión de tipos, comprobar que **el dato exista al otro lado**.*
*Y sacar la regla a una función propia -- `core/envases_enteros.py`, con 20 pruebas -- porque **el fallo
duró precisamente porque no había forma de mirarlo**.*

---

## 4. El temporizador que se reiniciaba justo cuando debía dispararse

**Dónde**: `plataforma/web/app/src/api/cliente.ts`, `useSeAtasca()`.

**Qué pasaba.** *Las pantallas que esperan datos tienen un tope: si a los diez segundos no ha llegado
nada, dejan de decir «Cargando» y dicen que no se ha podido preguntar.* **Y no se disparaba nunca.**

```ts
useEffect(() => {
  if (!estaAtascada(cargando, 0, segundos)) { setAtascada(false); return }
  const reloj = setTimeout(() => setAtascada(true), segundos * 1000)
  return () => clearInterval(reloj)
}, [cargando, segundos])          // <-- AQUI ESTA EL FALLO
```

**El efecto depende de `cargando`.** *Así que **cada vez que `cargando` cambia de valor, el `setTimeout`
se cancela y empieza de cero**.* **Y `isLoading` de React Query no es estable**: *vuelve a intentar, y
entre intento e intento **oscila**.* **Si oscila, el reloj nunca llega a los diez segundos.**

> **El tope existía, la regla tenía sus pruebas... y el temporizador que la dispara no llegaba a
> dispararse** -- *porque **dependía de la misma señal que vigilaba**.*

**La lección, y es la misma que la del caso 3 en otro lenguaje**: *un temporizador que depende del estado
que vigila se reinicia justo cuando debería sonar.* **Lo que hay que guardar no es un contador: es
**cuándo empezó**.**

**Y es la misma decisión que se tomó en `core/cocina.py`**: *«un temporizador **no es una cuenta atrás, es
una hora de fin**».* **Dos sitios, un solo principio.**

---

## 5. Los cinco contratos que supuse y el código tenía razón

*Este caso no es de un fallo del programa: es de un fallo de método, y por eso va el último.*

**Al escribir las pruebas de los recorridos reales, asumí cinco veces cómo funcionaba una función sin
leerla. Las cinco veces, el código estaba bien.**

| lo que supuse | lo que era |
|---|---|
| `almacen.comparte(lista, id_de_B, id_de_A)` | **`comparte` busca por NOMBRE de usuario**, no por id. *Con el id no da error: **devuelve `None` sin compartir nada*** |
| `comparte(lista, nombre, nombre)` | *`quien_invita` sí va por **id** -- acaba en `invitado_por`, que es un `uuid`* |
| `cierra_compra` vacía la lista | **cierra sólo lo que está en el carro**: *«lo que no se cogió se queda en la lista, que es la mitad que importa: quien no encuentra el pan no quiere volver a apuntarlo»* |
| una línea de lista puede no tener cantidad | **`lista_linea.cantidad` es NOT NULL**: *apuntar es decidir cuánto* |
| `descuento_de_cesta` entiende «Compra 20 EUR y te descontamos 5» | el formato es **«5 EUR dto comprando 20 EUR»** -- *y con el mío devolvía **cero las cuatro veces, sin fallar*** |

> **La lección, que es la de todo este documento**: *ante un rojo, lo primero no es arreglar el código: es
> comprobar si **uno entendió lo que la función hace**.*
>
> *Y el caso del descuento es el más peligroso de los cinco*: **un texto que la función no reconoce no es
> un error, es una promoción que no aplica.** *Silencio, y un cero con aspecto de resultado.*

---

## 6. Y dos más, cortos, del mismo tipo

**El `0.0.0.0` que nadie había decidido.** *La web escuchaba en **todas** las interfaces de la máquina, y
los otros cuatro contenedores estaban en `127.0.0.1`.* **No era una decisión: era un valor por defecto**
-- *y estaba **en dos sitios**, así que cambiar el que se ve no cambiaba nada.* **Lección**: *lo que se
abre, se abre queriendo; y un valor por defecto que expone es una decisión que alguien tomó por ti.*

**El desbordamiento que sólo aparecía al doble de zoom.** *A 390 px la pantalla se salía **sólo** con el
zoom al 200%, y sólo en un elemento.* **El arreglo no era un número más pequeño: era `min-w-0`**, porque
*dentro de un `flex`, un hijo no encoge por debajo de su mínimo salvo que se le diga.* **Lección**: *once
combinaciones bien y una mal se ven **recorriéndolas**; y para arreglar un desbordamiento, **preguntarle al
navegador qué elemento se sale**, no leer el CSS.*

---

## Cómo se reproduce todo esto

```powershell
# Las pruebas de los casos 1, 2 y 6:
$env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
uv run pytest tests/test_revision_a01_publicacion.py -q      # el enlace duro y las huellas
uv run pytest tests/test_revision_a08_envases.py -q          # los envases enteros
uv run pytest tests/test_revision_a09_sustitucion.py -q      # el reparto de responsabilidad

# Y la de la interfaz:
cd plataforma/web/app ; npm test                             # estaAtascada, frescura, pagina
```

**Y la medición de los enlaces duros, que necesita Windows:**

```powershell
fsutil hardlink list data\gold\precio_diario.parquet
```

**Lo que estos casos tienen en común, y es la razón de que estén juntos**: *en **ninguno** el programa
falló.* *Devolvieron `None`, un cero, un `True` por defecto o un silencio* -- **y ninguno de esos es un
error, que es exactamente por qué duraron.**
