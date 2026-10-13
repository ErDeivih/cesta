# B02 · **Las dos medidas, y ya se puede decir que le falta a B02** -- con lo leido, no con lo supuesto

*(13 de octubre de 2026. **Cuatro rondas y tres correcciones despues, por fin hay una conclusion que se sostiene.**)*

## 1. Las dos medidas

```
tests/fixtures/         EXISTE Y ESTA VACIA
test_waf_alcampo.py     9,3 KB
```

> **La carpeta existe y esta vacia.** *Y eso contesta las dos preguntas de golpe:*
>
>   - **¿donde van los fixtures?** *-- *ahi, que es lo que el proyecto ya eligio;*
>   - **¿hay que crearlos o ampliarlos?** *-- *crearlos, porque no hay ninguno.*

**Y `test_waf_alcampo.py` son 9,3 KB** *-- no un apunte: **un ensayo de verdad**, que dice **que se considera
comportamiento correcto hoy** en Alcampo.*

## 2. Y entonces B02, con lo leido, es esto

```
LO QUE HAY (leido, no buscado):
  ALCAMPO    RetoWAF (13 usos) · AVANCE_MINIMO · CORTES_PARA_RENDIRSE · MAX_RENOVACIONES
             · `detener` · mensaje que dice «hoy el WAF nos tiene fichados»
             Y SU ENSAYO: test_waf_alcampo.py (9,3 KB)
  CARREFOUR  ESTADOS_DE_BLOQUEO = (403, 429), USADO en la 528
  FIXTURES   tests/fixtures/ EXISTE Y ESTA VACIA
  OTROS      los otros cuatro colectores: sin mirar, y no se dice nada

LO QUE FALTA, Y SE PUEDE DECIR:
  1) FIXTURES -- la carpeta esta y el material no. Y el plan pide SEIS casos:
     desafio · esquema cambiado · pagina vacia · corte a mitad · reanudar · publicacion final
  2) LLEVAR A CARREFOUR lo que Alcampo tiene -- empezando por leer la 528 y su alrededor,
     que NO se ha leido
  3) MEDIR -- las cuatro cosas del plan. Y ALCAMPO YA CUENTA errores, renovaciones, truncadas
     y reintentos: lo que falta es SACARLO a donde se pueda leer
  4) Y UNA CAPTURA ACOTADA REAL -- la segunda mitad de la aceptacion, que es facil saltarse
```

> **Y ahora si: esto es una conclusion que se sostiene**, *porque cada linea de arriba viene de **un fichero que
> se ha mirado o de un `ls`** -- *no de un `grep` con mis palabras, ni de una lectura de dos lineas, ni de una
> correccion sin abrir.*

## 3. Y las cinco rondas que costo, dichas en orden

```
105  grep con MIS palabras          -> «no existe nada»         FALSO
106  correccion sin abrir            -> «falta la distincion»   FALSO
107  leer 20 lineas                  -> «tiene una linea y nada mas»  FALSO
108  no mirar el directorio          -> «no se sabe si hay fixtures»  FALSO (la carpeta estaba)
109  ls de fixtures + mirar el WAF   -> y por fin algo que se sostiene
```

**Cinco rondas, cuatro conclusiones falsas, y el arreglo de todas era el mismo:** ***empezar por lo mas barato y
mirar antes de escribir.*** *`ls tests/` habria contestado en la ronda 105 lo que se ha tardado cinco en saber.*

> **Y hay una razon por la que no se hizo**: *`grep` **parece** mas listo que `ls`.* *Buscar parece investigar, y
> mirar parece no hacer nada.* **Pero `grep` responde a la pregunta que le haces, y `ls` te dice que preguntas
> hay.**
>
> ***En un paquete nuevo, la primera pregunta no es «que le falta»: es «que hay».*** **Y se contesta mirando.**

## 4. Y el estado de B02, sin adornos

**No empezado en codigo, y con el mapa hecho a base de correcciones.** *Que es peor que haberlo hecho bien a la
primera, y **mucho mejor que haber empezado a escribir en la ronda 105** -- *cuando la conclusion era que había
que construirlo entero.*

> *Si se hubiera hecho caso a la ronda 105, **se habria escrito un colector de cero al lado de uno que ya
> funciona**.* **Que es la clase de daño que estas cinco rondas han evitado, a costa de cinco rondas.**
