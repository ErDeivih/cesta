# B02 · **Los fixtures no son de una clase**: el reto se simula con una funcion, y el HTML con un fabricante

*(13 de octubre de 2026. **Antes de crear `tests/fixtures/`, se miro como se prueba hoy.**)*

## 1. Las dos formas que ya existen, y son distintas

```
FORMA 1 -- EL RETO, SIMULADO CON UNA FUNCION  (tests/test_waf_alcampo.py:47-50)

    def obtener(dominio, url, headless=None):
        raise RuntimeError("no pasa el reto sin ventana")

  -> NO HAY HTML. El desafio se simula **cambiando `obtener`**, que es la funcion que
     pide la pagina. *** Es un fixture de COMPORTAMIENTO, no de bytes. ***

FORMA 2 -- EL HTML, FABRICADO POR UNA FUNCION DEL ENSAYO

  tests/test_banco_de_pares.py · test_carrefour.py · test_g07_manifiesto.py
  test_lidl_colector.py · test_lidl_regresiones_reales.py · test_marca_en_identidad.py
  test_revision_a02_identidad.py · test_sondear_lidl.py        (ocho ficheros)

  -> cada uno tiene su `def ficha(...)` / `def oferta(...)` / `def html(...)` que **construye
     el HTML minimo que el parser entiende**. *** Es un fixture de BYTES, y vive en el ensayo. ***
```

> **Y esto importa porque el plan pide seis casos -- «desafio · esquema cambiado · pagina vacia · corte a mitad
> · reanudar · publicacion final» -- y no son de la misma clase:**
>
>   - **«desafio»** *-- **forma 1**: se prueba **que hace el colector cuando `obtener` falla**, y **ya esta
>     probado** en `test_waf_alcampo.py` (13 ensayos).*
>   - **«esquema cambiado», «pagina vacia»** *-- **forma 2**: HTML que el parser no entiende, o que viene sin
>     productos.*
>   - **«corte a mitad», «reanudar»** *-- **forma 1 tambien**: *que pasa cuando la primera pagina va bien y la
>     segunda falla.* **Carrefour ya lo tiene**: `VUELTAS_DE_RESCATE` y `VUELTAS_SIN_BLOQUEO` existen para eso.*
>   - **«publicacion final»** *-- *que el bronze y la cobertura salgan **solo si la pasada fue completa**.* *Que es
>     `guardar = completa`.*
>
> *** O sea: tres de los seis casos NO son ficheros de HTML, y uno de ellos YA ESTA PROBADO. ***

## 2. Y entonces `tests/fixtures/` puede que no sea el sitio

**La carpeta existe y esta vacia.** *Y lo que se prueba hoy **no vive ahi**: vive **dentro de cada ensayo**, en su
`def ficha(...)`.*

> *Asi que **antes de meter seis ficheros en `tests/fixtures/`**, hay que contestar: **¿por que una carpeta, si el
> proyecto hasta ahora fabrica el HTML en el ensayo?***
>
> *Y hay dos respuestas posibles, y **ninguna se sabe todavia**:*
>
>   - **si los fabricantes de HTML de los ocho ensayos son parecidos**, *entonces **hay duplicacion** y la carpeta
>     -- o un modulo de fabricantes -- **une lo que ya esta repetido**;*
>   - **y si cada uno fabrica algo distinto para su parser**, *entonces **la carpeta sobra** y lo que falta son
>     **casos nuevos en los ensayos que ya existen**.*

## 3. Y lo que se deja dicho, sin escribirlo

**Nada de codigo.** *Y una pregunta que hay que contestar **leyendo los ocho fabricantes** antes de crear un solo
fichero:*

> ***¿Se repiten?*** *Porque `tests/fixtures/` **vacio y con ocho fabricantes dentro de los ensayos** es la senal
> de que **alguien penso en la carpeta y no la uso** -- *y **puede ser a proposito**: un fixture de bytes que solo
> entiende un parser **vive mejor al lado del parser que lo prueba**.*
>
> *** Y es la novena vez que la respuesta es «hay que mirar antes de decidir»: la carpeta vacia parecia una tarea
> pendiente, y puede ser una decision. ***
