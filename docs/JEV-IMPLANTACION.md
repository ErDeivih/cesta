# Jev: se puede implantar, y la parte que vale no necesita a Jev

Estudio hecho el 23 de septiembre de 2026, **en paralelo** al trabajo del
emparejador, para decidir si merece la pena meter un modelo de los de salida
forzada en esta cadena. El catalogo de Jev y sus dos sitios naturales estan en
`docs/JEV.md`; esto es **la parte de implantacion**, y la conclusion va arriba.

## 0. La conclusion, en tres lineas

1. **El sitio bueno es el clasificador de ejes**, no el juez de pares. El 64 % de
   nuestros fallos son dato numerico -- formato, unidad, cantidad -- y Jev dice por
   escrito que no cuenta de forma fiable y que lee las fechas como texto. Ponerlo a
   juzgar pares es ponerlo justo donde su propia documentacion dice que no sirve.
2. **Ese sitio no necesita a Jev para probarse.** Ya tenemos un modelo local
   (Ollama) y un arnes que **fuerza el esquema JSON** (`projects/cesta/banco_de_pares.py`,
   `pregunta()`), que es lo mismo que ofrece Jev. La espera de acceso no tiene por
   que parar el experimento: se construye el banco de pruebas y se mide con el
   modelo local, y el dia que abran la lista se cambia **una funcion**.
3. **Lo que cuesta es menos de un euro y lo que bloquea es una lista de espera.** Un
   plan que dependa del acceso no es un plan. El que no depende de el, si.

## 1. Lo que he verificado yo, sobre nuestro codigo

| Dato | Dice el informe | Mido yo | |
|---|---|---|---|
| Ejes en `core/atributos.py` | 12 | **12** | ✓ |
| Opciones de pasillo (`core/secciones.ORDEN`) | 19 | **19** | ✓ |
| Pares (valor, patrones) | 34 | **28** (y 71 patrones sueltos) | ✗ |
| `docs/JEV.md` | 337 lineas | **337** | ✓ |

El de los pares no cuadra: `sum(len(v) for v in EJES.values())` da **28**, y los
patrones sueltos son **71**. No cambia la conclusion -- lo que manda el tamano del
`state` son los **12 ejes**, que si cuadran -- pero el numero hay que decirlo bien,
porque es la clase de cifra que se copia de un informe a otro sin comprobar.

## 2. El sitio que vale: clasificar los ejes

Hoy `core/atributos.py` son **listas a mano**: 12 ejes, 28 opciones, 71 patrones de
subcadena. Funciona, y ya dio un fallo clasico -- `desnatad` casando dentro de
`semidesnatad`, y la leche semidesnatada leida como "sin grasa". Cada eje nuevo es
trabajo manual y otra oportunidad del mismo fallo.

Es un `Choice` de manual: el nombre del producto es el `state`, los valores del eje
mas **"no lo dice"** son la salida, y la regla del dueno -- **el que calla no
bloquea** -- se implementa con la confianza que el modelo ya devuelve.

**Y aqui esta la trampa del banco gratis, medida por el investigador y que hay que
respetar.** Las listas a mano son la verdad de referencia, si, pero son
**subcadenas sueltas aplicadas a todo el catalogo**, y en los tres peores casos hay
**935 declaraciones fuera de sitio**:

    cafeina · natural   1.598 fichas, 19 pasillos   el mayor: lacteos-huevos 411
                        (es "yogur natural", no cafe)
    integral · blanco   1.155 fichas, 20 pasillos   el mayor: bebidas 508
                        (es "vino blanco", no harina)
    aceite · orujo         bebidas 16 por delante de despensa 12
                        (es orujo de hierbas, no aceite)

Asi que **el banco no se usa entero**: se usa lo del pasillo coherente, y los
desacuerdos se auditan uno a uno. Ahi no hay ruido: hay listas que sobre-disparan,
que es un hallazgo sobre nuestro codigo, no sobre el modelo.

## 3. Como se implanta, sin depender de la lista de espera

    core/clasificador_ejes.py

        clasifica(nombres: list[str], respaldo: str = "local") -> list[dict[str, str | None]]

Dos implementaciones detras de la misma firma:

    respaldo="local"    Ollama, con el esquema forzado que ya usa el banco de pares
    respaldo="jev"      el Choice de Jev, el dia que haya acceso

La firma no cambia, y eso es lo que hace que el experimento se pueda hacer **hoy**:
si el modelo local reproduce las listas a mano en el pasillo coherente, el sitio es
bueno y Jev solo lo mejora; si no las reproduce, Jev tampoco se mete a ciegas.

**Una peticion por producto**, y los 12 ejes del mismo producto juntos. El
investigador corrige aqui a Claude y tiene razon: meter cien nombres en un `state`
es el modo de fallo numero 5 de la documentacion de Jev -- para la pregunta del
producto 37, los otros 99 nombres son "content unrelated to the decision" y la
precision cae.

**La barra de aceptacion del experimento**, antes de tocar `core/atributos.py`:

1. Sobre las declaraciones del **pasillo coherente**, el clasificador tiene que
   reproducir lo que ya dicen las listas a mano. Si no lo reproduce, no se usa para
   lo que no sabemos.
2. Los tres casos que sobre-disparan tienen que salir **mejor** que hoy: `yogur
   natural` no es cafeina, `vino blanco` no es harina integral, `orujo de hierbas`
   no es aceite.
3. Y el numero que manda: los ejes contradictorios del catalogo
   (`uv run python -m projects.cesta.ejes`), que hoy son **52** y no pueden subir.

## 4. El segundo sitio: las categorias sin pasillo

Es **el unico paso de la cadena diaria que todavia dice "A MANO"**. Son **19
opciones** exactas (`core/secciones.ORDEN`), y hay **881 claves ya mapeadas** que
sirven de banco gratis (alcampo 206, aldi 101, carrefour 294, dia 254, mercadona 26).
Hoy hay **9 sin mapear**.

Un `Choice` de 19 opciones es lo mas facil que se le puede pedir a un modelo de
estos, y el banco de 881 ya mapeadas es una prueba gratis de si acierta. Coste:
centimos al dia.

## 5. Lo que NO se hace con esto

- **Juez de pares.** Es el 20 % del problema, va detras de los vectores, y el 64 %
  de lo que se nos escapa es justo lo que Jev documenta que no sabe hacer.
- **Las ofertas.** El investigador lo cerro sin gastar nada: las 1.260 fichas en
  `SIN_REGLA` son **20 textos distintos** y los cuatro primeros suman 977. Eso es
  una lista de veinte cadenas, no un modelo.
- **Nada que toque la tarea de las 06:00** hasta que el experimento pase su barra.

## 6. El coste, con los supuestos a la vista

Con 12 ejes y una peticion por producto: **$0,29** la pasada del catalogo entero
(52.567) y **$0,09** la validacion sobre las 16.605 declaraciones, a $0,042/Mtok con
la salida gratis. La cifra de Claude (0,09 $) es exacta **para la validacion**, no
para todo: son dos numeros distintos y conviene no mezclarlos.

El experimento entero -- banco, clasificador local, medida y comparacion -- cuesta
**menos de un euro** y no depende del acceso. El bloqueo real, hoy, es la lista de
espera de Jev; y la unica forma de que eso no pare el trabajo es que la primera
version no lo necesite.
