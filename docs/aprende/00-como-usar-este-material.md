# 00 · Cómo usar este material

Esto no es la documentación de una aplicación. Es **el material de un curso** que usa un
proyecto real como caso práctico: comparar los precios de cinco supermercados españoles,
todos los días, en un PC de casa, y contestar con esos datos preguntas que la gente se hace
de verdad en el pasillo.

Se lee de arriba abajo, y cada capítulo hace lo mismo:

1. **La teoría**, en corto y con las fuentes donde está mejor contada.
2. **El caso**: qué hace este proyecto, con **los números medidos** y el comando que los
   reproduce. No hay ni un número de ejemplo.
3. **Lo que no se sabe** o no se puede hacer con estos datos, dicho antes de que alguien lo
   dé por hecho.

## Dónde se lee esto

De dos maneras, y las dos valen:

- **En el PC, sin servidor**: `plataforma/web/aprende/index.html`, con doble clic. El buscador
  lleva su índice embebido, así que funciona sin conexión.
- **Desde el móvil o cualquier cacharro de casa**: `http://<el-PC>:8080/aprende/`.

El sitio se genera a partir de estos documentos, que son la fuente:

```bash
uv run --extra docs python -m plataforma.aprende
```

## Lo que hay que saber antes de empezar

No hace falta ser ninguna de estas tres cosas, pero ayuda tener idea de:

    Python          leer un script y ejecutarlo. Nada mas.
    SQL             SELECT, JOIN, GROUP BY. Es lo que se usa aqui el 80 % del tiempo.
    estadistica     saber que una mediana no es una media. El resto se explica.

Y **no hace falta**: ni saber de Docker, ni de AWS, ni de machine learning. Cuando algo de
eso aparece, se explica por qué está ahí y qué costaría quitarlo.

## Las reglas de la casa

Estas cuatro reglas son el 80 % de lo que se aprende aquí, y están metidas en el código, no
en un manual:

1. **Un dato que no tenemos es «no lo sé»**, nunca un cero. Un `0,00 €` se lee como «gratis»
   y una letra vacía como «malo»; las dos cosas serían mentira.
2. **Se mide antes y después, sobre el mismo dato.** Si el dato de entrada cambia entre las
   dos medidas, no sabes qué causó la diferencia. Esto es lo que separa un cambio de una
   opinión.
3. **Comparar solo dentro de la misma unidad.** Un precio por kilo y un precio por unidad no
   se comparan: compararlos da «te ahorras 6.872 €» en la ficha de un azafrán.
4. **El que calla no bloquea.** Si un dato no dice nada de un atributo, no está afirmando que
   sea igual: es que no lo sabemos. Eso no es tolerancia, es ausencia de prueba.

## Cómo se ejecuta cada cosa

Todo lo de este material se puede reproducir en este PC. Los cuatro comandos que aparecen una
y otra vez:

```bash
uv run python -m projects.cesta.verificar_docs    # las cifras de los documentos, contra el dato de hoy
uv run python -m projects.cesta.ejes              # las condiciones de dato (ejes, grupos, packs)
uv run python -m projects.cesta.emparejar --medir # el recall del emparejador sobre el banco de pares
uv run pytest -q                                  # las pruebas del proyecto
```

Y para mirar los datos a mano, que es de donde salen casi todos los hallazgos:

```bash
uv run python -c "import duckdb; print(duckdb.sql(\"select count(*) from 'data/gold/grupos.parquet'\"))"
```

## El mapa

    El problema y los datos           01  que hay, de donde sale y que NO se puede concluir
    Ingenieria de datos               02  capas, formatos, motores, idempotencia, la cadena diaria
    Unidades y comparabilidad         03  por que un catalogo de envases no se puede comparar sin normalizar
    Emparejar productos               04  resolucion de entidades: bloqueo, similitud, hungaro, ejes
    Medir el emparejador              05  el banco de pares, el techo del bloqueo, invariantes y fugas
    Estadistica del catalogo          06  medianas frente a medias, percentiles, muestra, recortes
    Indices de precios                07  Jevons encadenado, formulas oficiales, y el sesgo de
                                           encadenamiento medido (y descartado) aqui
    Promociones y anomalias           08  que se anuncia, que sostiene el historico, y por que
                                           la mayoria de las ofertas NO se pueden juzgar
    Que mas se puede hacer            09  el catalogo de analisis, con lo que se puede y lo que no
    Cuando NO usar machine learning   10  tres intentos medidos y descartados, con su numero

    Anexo 90   la investigacion sobre emparejamiento, entera y con sus fuentes
    Anexo 91   la investigacion sobre indices de precios con datos de escaner, y la auditoria
    Anexo 92   como se hizo esta investigacion (metodo, fechas y lo que no se pudo verificar)

Los capitulos que faltan (servir los datos y medir sin engañarse) están en camino: cada uno
necesita sus números medidos y reproducibles, y se escriben en ese orden. **El temario del índice
es la lista completa**; aquí solo están los que ya se pueden leer.

Los documentos largos del proyecto (el registro del día a día, los informes, la operación)
están en **la referencia**, que es donde se comprueba de dónde sale cada cosa. Este curso los
cita continuamente con la forma `docs/BACKLOG.md`, y esos nombres se pueden abrir en el mismo
sitio: son las páginas de la sección *Referencia*.

## Lo que este material NO es

- **No es un tutorial de herramientas.** DuckDB, Polars o FastAPI aparecen porque hacen falta
  para algo concreto, no como temario.
- **No es un caso de éxito.** La mitad de los capítulos cuentan cosas que se intentaron, se
  midieron y **no se adoptaron** (el canal de vectores, el medoide, dos modelos de decisión
  de los que se habla hoy). Un proyecto de datos de verdad es eso.
- **No tiene los números inventados.** Si un dato no se ha medido, pone «no lo sé». Y eso es
  una respuesta, no un hueco.
